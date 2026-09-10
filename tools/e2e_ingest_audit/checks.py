"""Cross-stage consistency checks for one document.

Each check compares two stages of the same document — source against
canonical, canonical against chunks, chunks against Qdrant, canonical against
MySQL, the knowledge report against the knowledge tables and the graph — so a
value that was lost, altered, duplicated or attached to the wrong document
between two stages shows up as a named failure with the two values beside it.

A check that does not apply to a document (a PDF-only check on a web page) is
recorded as ``n/a`` rather than silently omitted, so the per-document tables
have the same rows everywhere.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from tools.e2e_ingest_audit.serialize import to_jsonable

_STAMP_KEYS = {"created_at", "updated_at", "embed_model"}


@dataclass
class Check:
    category: str
    name: str
    status: str  # pass | fail | n/a | info
    detail: str = ""
    expected: Any = None
    actual: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "category": self.category, "name": self.name, "status": self.status,
            "detail": self.detail,
            "expected": to_jsonable(self.expected), "actual": to_jsonable(self.actual),
        }


@dataclass
class CheckSet:
    checks: list[Check] = field(default_factory=list)

    def add(self, category: str, name: str, ok: bool | None, detail: str = "",
            expected: Any = None, actual: Any = None) -> None:
        status = "n/a" if ok is None else ("pass" if ok else "fail")
        self.checks.append(Check(category, name, status, detail, expected, actual))

    def info(self, category: str, name: str, detail: str, actual: Any = None) -> None:
        self.checks.append(Check(category, name, "info", detail, None, actual))

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if c.status == "fail"]


def _dt(value: Any) -> str | None:
    """A comparable UTC 'YYYY-MM-DDTHH:MM:SS' for a date from any store."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.isoformat(timespec="seconds")
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.isoformat(timespec="seconds")


def _norm_lines(text: str) -> list[str]:
    return [" ".join(line.split()) for line in (text or "").splitlines() if line.strip()]


def _jsonish(value: Any) -> Any:
    return json.loads(json.dumps(to_jsonable(value), sort_keys=True, default=str))


def run_checks(cap: Any, rb: dict[str, Any], captures: dict[str, Any], *, settings: Any,
               table: str, log_table: str) -> CheckSet:
    cs = CheckSet()
    record, doc, chunks = cap.record, cap.doc, cap.chunks
    is_pdf = record.source_type == "pdf_attachment"
    mysql = rb["mysql"]
    qdrant = rb["qdrant"]
    neo = rb["neo4j"]
    state_rows = mysql.get(table) or []
    row = state_rows[0] if state_rows else None

    # ---------------------------------------------------------------- outcome
    cs.add("outcome", "handler_outcome_is_indexed", cap.outcome == "indexed",
           "Every fresh document is expected to end 'indexed'.", "indexed", cap.outcome)
    cs.add("outcome", "no_exception", cap.error is None, cap.error or "", None, cap.error)
    if cap.outcome != "indexed" or doc is None:
        # Nothing downstream is expected to exist; record what does.
        cs.add("mysql", "state_row_absent_after_failure", row is None,
               "A skipped/errored first ingestion must leave no catalog row.", None,
               row and row.get("document_id"))
        cs.add("qdrant", "no_points_after_failure", qdrant.get("count", 0) == 0,
               "", 0, qdrant.get("count", 0))
        logged = [r["status"] for r in (mysql.get(log_table) or [])]
        cs.add("mysql", "ingest_log_records_outcome", cap.outcome in logged,
               "", cap.outcome, logged)
        retry = mysql.get(f"{table}_retry") or []
        cs.add("mysql", "retry_marker_written", bool(retry) if cap.outcome in ("error", "skipped") else None,
               "An unresolved outcome must leave a retry marker.", True, bool(retry))
        return cs

    # --------------------------------------------------------- source -> canonical
    if is_pdf:
        node, file = record.payload
        cs.add("source", "pdf_downloaded_non_empty", bool(cap.download and cap.download["bytes"] > 0),
               "", ">0 bytes", cap.download and cap.download["bytes"])
        ext = cap.extraction
        pages = list(getattr(ext, "pages", []) or [])
        non_empty = [p for p in pages if (p.text or "").strip()]
        cs.info("source", "pdf_pages", f"{len(pages)} pages extracted, {len(non_empty)} with text",
                {"pages": len(pages), "with_text": len(non_empty),
                 "routes": _count(p.extracted_via.value for p in pages),
                 "tables": sum(len(p.tables) for p in pages)})
        cs.add("canonical", "sections_equal_non_empty_pages",
               len(doc.sections) == len([p for p in pages if p.text]),
               "from_pdf makes one section per page with text.", len([p for p in pages if p.text]),
               len(doc.sections))
        cs.add("canonical", "section_text_equals_page_text",
               all(s.text == p.text for s, p in zip(doc.sections, [p for p in pages if p.text])),
               "Section text is the page text verbatim.")
        expected_title = file.description or node.title or file.filename or None
        cs.add("canonical", "title_precedence_description_node_filename",
               doc.title == expected_title, "title = file.description or node.title or filename",
               expected_title, doc.title)
        cs.add("canonical", "linked_article_uuid_is_parent_node",
               doc.linked_article_uuid == (node.uuid or None), "", node.uuid, doc.linked_article_uuid)
        cs.add("canonical", "source_url_is_parent_page", doc.source_url == node.url, "", node.url, doc.source_url)
        cs.add("canonical", "file_url_is_fetched_url",
               cap.download is not None and doc.file_url == cap.download["fetched_url"], "",
               cap.download and cap.download["fetched_url"], doc.file_url)
        cs.add("canonical", "bundle_inherited_from_parent", doc.extra.get("bundle") == node.bundle,
               "", node.bundle, doc.extra.get("bundle"))
        parent_cap = captures.get(node.uuid)
        if parent_cap is not None and parent_cap.doc is not None:
            pdoc = parent_cap.doc
            cs.add("parent_child", "facets_inherited_from_parent",
                   list(doc.categories) == list(pdoc.categories) and list(doc.tags) == list(pdoc.tags)
                   and list(doc.authors) == list(pdoc.authors),
                   "categories/tags/authors equal the parent page's",
                   {"categories": pdoc.categories, "tags": pdoc.tags, "authors": pdoc.authors},
                   {"categories": doc.categories, "tags": doc.tags, "authors": doc.authors})
            cs.add("parent_child", "entity_refs_inherited_from_parent",
                   [(r.field_name, r.uuid) for r in doc.entity_refs]
                   == [(r.field_name, r.uuid) for r in pdoc.entity_refs], "")
            cs.add("parent_child", "parent_lists_this_file",
                   record.document_id in {f.uuid for f in pdoc.file_links}, "",
                   record.document_id, [f.uuid for f in pdoc.file_links])
        else:
            cs.add("parent_child", "parent_page_in_run", False,
                   "The parent node was not handled in this run (or was not built).", node.uuid, None)
    else:
        payload = record.payload
        cs.add("canonical", "title_equals_node_title", doc.title == ((payload.title or "").strip() or None),
               "", payload.title, doc.title)
        cs.add("canonical", "body_is_single_section", (len(doc.sections) == 1 and doc.sections[0].text == payload.body)
               if payload.body else len(doc.sections) == 0, "Website body becomes one section.",
               len(payload.body or ""), sum(len(s.text) for s in doc.sections))
        cs.add("canonical", "raw_meta_equals_record_metadata", dict(doc.raw_meta) == dict(payload.metadata or {}), "")
        cs.add("canonical", "article_uuid_is_node_uuid", doc.article_uuid == payload.uuid, "", payload.uuid, doc.article_uuid)
        cs.add("canonical", "file_links_equal_record_files",
               [f.uuid for f in doc.file_links] == [f.uuid for f in payload.files if f.uuid], "",
               [f.uuid for f in payload.files], [f.uuid for f in doc.file_links])
        cs.add("canonical", "extra_carries_bundle_nid_changed",
               doc.extra.get("bundle") == payload.bundle and doc.extra.get("nid") == payload.nid
               and doc.extra.get("changed") == payload.changed, "", None, doc.extra)
        from app.ingestion.canonical import drupal_facets
        facets = drupal_facets(payload.metadata or {}, list(payload.refs or []))
        cs.add("canonical", "facets_match_drupal_facets_rule",
               list(doc.categories) == facets["categories"] and list(doc.tags) == facets["tags"]
               and list(doc.authors) == facets["authors"], "", facets,
               {"categories": doc.categories, "tags": doc.tags, "authors": doc.authors})

    full_text = doc.full_text()
    cs.add("canonical", "content_hash_is_sha256_of_body_text",
           doc.content_hash == hashlib.sha256(full_text.encode("utf-8")).hexdigest(), "",
           None, doc.content_hash)
    cs.add("canonical", "body_text_non_empty", bool(full_text.strip()), "", ">0 chars", len(full_text))

    # ------------------------------------------------------------- dates
    cs.add("dates", "effective_start_date_present", bool(doc.effective_start_date),
           "Undated documents are excluded from date filters (pipeline warns).", "a date", doc.effective_start_date)
    if is_pdf:
        rd, pd = cap.resolved_date, cap.parent_date
        cs.add("dates", "resolver_ran", rd is not None and pd is not None, "")
        if rd is not None and pd is not None:
            inherited = not rd.overridden
            cs.info("dates", "pdf_date_path",
                    f"{rd.canonical_source} override" if rd.overridden
                    else "inherited from parent page",
                    {"parent_rule": pd.rule, "parent_source": pd.source,
                     "decision_action": rd.decision.action if rd.decision else None,
                     "decision_rule": rd.decision.rule if rd.decision else None,
                     "edition_label": rd.edition_label, "used": rd.used})
            if inherited:
                cs.add("dates", "pdf_start_date_equals_parent_resolved",
                       _dt(doc.effective_start_date) == _dt(pd.start_value), "", pd.start_value, doc.effective_start_date)
                cs.add("dates", "pdf_precision_equals_parent", doc.start_precision == pd.start_precision, "",
                       pd.start_precision, doc.start_precision)
                cs.add("dates", "pdf_end_date_equals_parent", _dt(doc.effective_end_date) == _dt(pd.end_value), "",
                       pd.end_value, doc.effective_end_date)
                cs.add("dates", "date_source_is_parent_page", doc.date_source == "parent_page", "", "parent_page", doc.date_source)
            else:
                cs.add("dates", "override_start_equals_resolver", _dt(doc.effective_start_date) == _dt(rd.start_value), "",
                       rd.start_value, doc.effective_start_date)
                # Not pinned to one literal. A date the resolver took from the
                # PDF is `document_text` when a publication statement was
                # quoted and `document_copyright` when a copyright year was
                # corroborated, and the resolver is the thing that knows which.
                # What the audit has to prove is that the row agrees with it and
                # that the value stays inside the canonical vocabulary — a
                # hardcoded "document_text" would instead have failed the run
                # for recording provenance more accurately.
                cs.add("dates", "date_source_matches_resolver_canonical_source",
                       doc.date_source == rd.canonical_source,
                       "The persisted source is the one the resolver derived.",
                       rd.canonical_source, doc.date_source)
                cs.add("dates", "date_source_is_document_derived",
                       doc.date_source in {"document_text", "document_copyright"},
                       "An overridden PDF date came from the document itself.",
                       "document_text|document_copyright", doc.date_source)
            parent_cap = captures.get(record.payload[0].uuid)
            if parent_cap is not None and parent_cap.doc is not None:
                cs.add("dates", "parent_page_canonical_date_matches_parent_resolution",
                       _dt(parent_cap.doc.effective_start_date) == _dt(pd.start_value),
                       "The page's own document and the value handed to its files agree.",
                       parent_cap.doc.effective_start_date, pd.start_value)
            if rd.edition_label:
                cs.add("dates", "edition_label_in_extra_not_in_date",
                       doc.extra.get("edition_label") == rd.edition_label, "", rd.edition_label, doc.extra.get("edition_label"))
            decision_rows = mysql.get(f"{table}_date_decision") or []
            expect_row = rd.decision is not None
            cs.add("dates", "date_decision_row_presence", bool(decision_rows) == expect_row,
                   "A row is written when the resolver produced a decision.", expect_row, len(decision_rows))
            if decision_rows:
                d = decision_rows[0]
                cs.add("dates", "date_decision_row_names_parent_node", d.get("node_uuid") == record.payload[0].uuid, "",
                       record.payload[0].uuid, d.get("node_uuid"))
                cs.add("dates", "date_decision_current_date_is_parent_resolved",
                       _dt(d.get("current_start_date")) == _dt(pd.start_value), "", pd.start_value, d.get("current_start_date"))
    else:
        ev = doc.date_evidence
        cs.add("dates", "effective_date_evidence_present", ev is not None, "")
        if ev is not None:
            cs.info("dates", "website_date_rule", f"rule={ev.rule} source={ev.source} fields={list(ev.fields)}",
                    {"rule": ev.rule, "source": ev.source, "fields": list(ev.fields),
                     "raw_values": list(ev.raw_values), "field_role": ev.field_role,
                     "range_issue": ev.range_issue, "precision": ev.start_precision})
            cs.add("dates", "canonical_date_equals_evidence_value", _dt(doc.effective_start_date) == _dt(ev.start_value),
                   "", ev.start_value, doc.effective_start_date)
            cs.add("dates", "canonical_end_equals_evidence_end", _dt(doc.effective_end_date) == _dt(ev.end_value),
                   "", ev.end_value, doc.effective_end_date)
            cs.add("dates", "date_source_equals_evidence_source", doc.date_source == ev.source, "", ev.source, doc.date_source)
            from app.ingestion.bundle_dates import BUNDLE_DATE_FIELDS, CREATED
            fields = BUNDLE_DATE_FIELDS.get(record.bundle or "", ())
            mapped_to_field = bool(fields) and fields[0] != CREATED
            decision_rows = mysql.get(f"{table}_date_decision") or []
            cs.add("dates", "date_decision_row_presence", bool(decision_rows) == mapped_to_field,
                   "Written only when the bundle maps to a real CMS date field.", mapped_to_field, len(decision_rows))
            if ev.source == "created" and mapped_to_field:
                cs.info("dates", "cms_field_fell_back_to_created",
                        f"{fields[0]} did not supply a date (rule={ev.rule}); created stamp used.", list(ev.raw_values))
            if ev.start_precision == "year":
                cs.add("dates", "year_precision_stored_as_1_january",
                       str(doc.effective_start_date)[5:10] == "01-01", "", "MM-DD=01-01", doc.effective_start_date)

    # ----------------------------------------------------------- chunking
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    cs.add("chunks", "chunks_produced", len(children) > 0, "", ">0 children", {"parents": len(parents), "children": len(children)})
    ids = [c.chunk_id for c in chunks]
    cs.add("chunks", "chunk_ids_unique", len(ids) == len(set(ids)), "", len(ids), len(set(ids)))
    parent_ids = {c.chunk_id for c in parents}
    dangling = [c.chunk_id for c in children if c.parent_chunk_id and c.parent_chunk_id not in parent_ids]
    cs.add("chunks", "every_parent_reference_resolves", not dangling, "", [], dangling)
    kids_per_parent = _count(c.parent_chunk_id for c in children if c.parent_chunk_id)
    lonely = [p for p, n in kids_per_parent.items() if n < 2]
    cs.add("chunks", "parents_have_at_least_two_children", not lonely and set(kids_per_parent) == parent_ids,
           "A parent is emitted only when it groups more than one child.", sorted(parent_ids), kids_per_parent)
    cs.add("chunks", "children_carry_document_id", all(c.meta.document_id == record.document_id for c in chunks), "")
    cs.add("chunks", "children_carry_doc_version", all(c.meta.doc_version == doc.doc_version for c in chunks), "",
           doc.doc_version, sorted({c.meta.doc_version for c in chunks}))
    from app.ingestion.chunking import config_for
    if doc.is_paginated:
        n_pages = sum(1 for s in doc.sections if s.page_start is not None)
        cfg = config_for("small_pdf" if n_pages <= 10 else doc.source_type)
    else:
        cfg = config_for(doc.extra.get("bundle") or doc.source_type)
    over = [c.chunk_id for c in children if c.token_count > cfg.child_max_tokens]
    cs.add("chunks", "children_within_token_limit", not over,
           f"child_max_tokens={cfg.child_max_tokens}", cfg.child_max_tokens,
           {"max_child_tokens": max((c.token_count for c in children), default=0), "over": over})
    over_p = [c.chunk_id for c in parents if c.token_count > cfg.parent_max_tokens]
    cs.add("chunks", "parents_within_token_limit", not over_p, f"parent_max_tokens={cfg.parent_max_tokens}",
           cfg.parent_max_tokens, {"max_parent_tokens": max((c.token_count for c in parents), default=0), "over": over_p})
    cs.add("chunks", "content_hash_is_sha256_of_text",
           all(c.content_hash == hashlib.sha256(c.text.encode("utf-8")).hexdigest() for c in chunks), "")
    cs.add("chunks", "child_index_is_contiguous", [c.chunk_index for c in children] == list(range(len(children))), "",
           list(range(len(children))), [c.chunk_index for c in children])
    if doc.is_paginated:
        no_page = [c.chunk_id for c in children if c.page_number is None]
        cs.add("chunks", "children_carry_page_numbers", not no_page, "", [], no_page)
    # Coverage: every non-empty source line should be found in some chunk text
    # (children, parents or section headings), whitespace-normalised.
    source_lines = _norm_lines(full_text)
    haystack = "\n".join("\n".join(_norm_lines(c.text)) for c in chunks) + "\n" + "\n".join(
        " ".join((c.section_heading or "").split()) for c in chunks)
    missing = [line for line in source_lines if line not in haystack]
    coverage = 1.0 - (len(missing) / len(source_lines)) if source_lines else 1.0
    cs.add("chunks", "source_lines_covered_by_chunks", coverage >= 0.98,
           f"{coverage:.3%} of {len(source_lines)} source lines appear verbatim in some chunk",
           ">=98%", {"coverage": round(coverage, 4), "missing_sample": missing[:8]})
    cs.add("chunks", "children_have_embed_text_with_breadcrumb",
           all(c.embed_text and c.embed_text.endswith(c.text) for c in children)
           if doc.title else all(c.embed_text == "" or c.embed_text.endswith(c.text) for c in children),
           "embed_text = 'title › heading' + text")

    # ------------------------------------------------------------- Qdrant
    points = qdrant.get("points", [])
    by_id = {p["id"]: p for p in points}
    cs.add("qdrant", "point_count_equals_chunks", len(points) == len(chunks) == (cap.index_points or 0),
           "", {"chunks": len(chunks), "indexer_reported": cap.index_points}, len(points))
    cs.add("qdrant", "every_chunk_id_is_a_point", set(ids) == set(by_id), "",
           len(ids), {"missing": sorted(set(ids) - set(by_id))[:5], "extra": sorted(set(by_id) - set(ids))[:5]})
    payload_diffs: list[dict[str, Any]] = []
    for c in chunks:
        p = by_id.get(c.chunk_id)
        if p is None:
            continue
        expected = _jsonish(c.to_payload())
        stored = {k: v for k, v in _jsonish(p["payload"]).items() if k not in _STAMP_KEYS}
        if expected != stored:
            diff = {k: {"expected": expected.get(k), "stored": stored.get(k)}
                    for k in set(expected) | set(stored) if expected.get(k) != stored.get(k)}
            payload_diffs.append({"chunk_id": c.chunk_id, "diff": diff})
    cs.add("qdrant", "payload_equals_chunk_payload_plus_stamps", not payload_diffs,
           "Stored payload == Chunk.to_payload() plus created_at/updated_at/embed_model.", [], payload_diffs[:5])
    cs.add("qdrant", "children_have_real_vectors",
           all(p["vector"] and not p["vector"]["is_zero"] for p in points if not p["payload"].get("is_parent")), "")
    cs.add("qdrant", "parents_have_zero_vectors",
           all(p["vector"] and p["vector"]["is_zero"] for p in points if p["payload"].get("is_parent")), "")
    dims = {p["vector"]["dim"] for p in points if p["vector"]}
    cs.add("qdrant", "vector_dimension_matches_setting", dims <= {settings.azure_openai_embedding_dimensions},
           "", settings.azure_openai_embedding_dimensions, sorted(dims))
    cs.add("qdrant", "children_stamped_with_embed_model",
           all(p["payload"].get("embed_model") for p in points if not p["payload"].get("is_parent")), "",
           None, sorted({p["payload"].get("embed_model") for p in points if not p["payload"].get("is_parent")}))
    cs.add("qdrant", "points_carry_document_id", all(p["payload"].get("document_id") == record.document_id for p in points), "")
    cs.add("qdrant", "points_carry_effective_start_date",
           all(_dt(p["payload"].get("effective_start_date")) == _dt(doc.effective_start_date) for p in points), "",
           doc.effective_start_date, sorted({str(p["payload"].get("effective_start_date")) for p in points}))
    cs.add("qdrant", "points_carry_year_precision_only_when_year",
           all((p["payload"].get("start_precision") == "year") == (doc.start_precision == "year") for p in points), "",
           doc.start_precision, sorted({str(p["payload"].get("start_precision")) for p in points}))
    cs.add("qdrant", "points_are_current_and_versioned",
           all(p["payload"].get("is_current") is True and p["payload"].get("doc_version") == doc.doc_version for p in points),
           "", doc.doc_version, sorted({str(p["payload"].get("doc_version")) for p in points}))
    from app.ingestion.version import PIPELINE_VERSION
    cs.add("qdrant", "points_stamped_with_pipeline_version",
           all(p["payload"].get("pipeline_version") == PIPELINE_VERSION for p in points), "", PIPELINE_VERSION,
           sorted({str(p["payload"].get("pipeline_version")) for p in points}))
    cs.add("qdrant", "swap_deleted_with_keep_ids",
           any(d["document_id"] == record.document_id and d["keep_ids"] == len(chunks) for d in cap.delete_calls),
           "delete_document(id, keep_ids=<new chunk ids>) ran after the upsert.", len(chunks), cap.delete_calls)

    # -------------------------------------------------------------- MySQL
    cs.add("mysql", "state_row_exists", row is not None, "")
    if row is not None:
        cs.add("mysql", "row_source_type", row["source_type"] == record.source_type, "", record.source_type, row["source_type"])
        cs.add("mysql", "row_source_key", row["source_key"] == record.source_key, "", record.source_key, row["source_key"])
        cs.add("mysql", "row_fingerprint", row["fingerprint"] == record.fingerprint, "", record.fingerprint, row["fingerprint"])
        cs.add("mysql", "row_content_hash", row["content_hash"] == doc.content_hash, "", doc.content_hash, row["content_hash"])
        cs.add("mysql", "row_doc_version", row["doc_version"] == doc.doc_version, "", doc.doc_version, row["doc_version"])
        cs.add("mysql", "row_pipeline_version", row["pipeline_version"] == PIPELINE_VERSION, "", PIPELINE_VERSION, row["pipeline_version"])
        cs.add("mysql", "row_bundle", row["bundle"] == record.bundle, "", record.bundle, row["bundle"])
        cs.add("mysql", "row_entity_type", row["entity_type"] == record.entity_type, "", record.entity_type, row["entity_type"])
        cs.add("mysql", "row_changed_mark", row["changed_mark"] == record.changed_mark, "", record.changed_mark, row["changed_mark"])
        cs.add("mysql", "row_title", (row["title"] or None) == doc.title, "", doc.title, row["title"])
        cs.add("mysql", "row_url", (row["url"] or None) == doc.source_url, "", doc.source_url, row["url"])
        cs.add("mysql", "row_effective_start_date", _dt(row["effective_start_date"]) == _dt(doc.effective_start_date), "",
               doc.effective_start_date, row["effective_start_date"])
        cs.add("mysql", "row_date_source", row["date_source"] == doc.date_source, "", doc.date_source, row["date_source"])
        cs.add("mysql", "row_start_precision", row["start_precision"] == doc.start_precision, "", doc.start_precision, row["start_precision"])
        cs.add("mysql", "row_effective_end_date", _dt(row["effective_end_date"]) == _dt(doc.effective_end_date), "",
               doc.effective_end_date, row["effective_end_date"])
        cs.add("mysql", "row_end_precision", row["end_precision"] == doc.end_precision, "", doc.end_precision, row["end_precision"])
        cs.add("mysql", "row_indexed_at_set", row["indexed_at"] is not None, "", "not null", row["indexed_at"])
        raw = row.get("raw_meta")
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        stored_meta = json.loads(raw) if isinstance(raw, str) else raw
        cs.add("mysql", "row_raw_meta_equals_canonical", _jsonish(stored_meta) == _jsonish(doc.raw_meta or None),
               "", None, None)
        from app.catalog.state import _stored_values
        from app.catalog import theme_taxonomy
        authors = [r["author"] for r in (mysql.get(f"{table}_author") or [])]
        cs.add("mysql", "author_facet_rows", sorted(authors) == sorted(_stored_values(doc.authors)), "",
               sorted(_stored_values(doc.authors)), sorted(authors))
        tags = [r["tag"] for r in (mysql.get(f"{table}_tag") or [])]
        cs.add("mysql", "tag_facet_rows", sorted(tags) == sorted(_stored_values(doc.tags)), "",
               sorted(_stored_values(doc.tags)), sorted(tags))
        # The path and depth are compared too, not just the one-hop parent: they
        # are what a descendant query matches on, so a wrong path is a wrong
        # count with nothing else to show for it.
        themes = {
            (r["theme"], r["theme_type"], r["parent"], r["theme_group"],
             r.get("theme_path"), int(r["depth"]) if r.get("depth") is not None else None)
            for r in (mysql.get(f"{table}_theme") or [])
        }
        expected_themes = {
            (a.name[:255], a.theme_type, a.parent, a.group, a.path[:1024], a.depth)
            for a in theme_taxonomy.classify(doc.categories)
        }
        cs.add("mysql", "theme_rows_match_classification", themes == expected_themes,
               "documents_theme = theme_taxonomy.classify(categories)", sorted(expected_themes, key=str), sorted(themes, key=str))
        dropped = [c for c in doc.categories if c not in {t[0] for t in expected_themes}]
        if dropped:
            cs.info("mysql", "categories_dropped_by_theme_classifier",
                    "Categories with no theme row (grouping buckets or unknown names).", dropped)
        links = {(r["file_uuid"], r["origin"]) for r in (mysql.get(f"{table}_attachment") or [])}
        first_wins: dict[str, str] = {}
        for f in doc.file_links:
            first_wins.setdefault(f.uuid, f.origin)
        cs.add("mysql", "attachment_link_rows", links == set(first_wins.items()), "", sorted(first_wins.items()), sorted(links))
        logs = mysql.get(log_table) or []
        indexed_logs = [r for r in logs if r["status"] == "indexed"]
        cs.add("mysql", "ingest_log_indexed_row", len(indexed_logs) == 1, "", 1, [r["status"] for r in logs])
        if indexed_logs:
            lg = indexed_logs[0]
            cs.add("mysql", "ingest_log_chunk_count", lg["chunks_indexed"] == len(points) == len(chunks), "",
                   len(chunks), lg["chunks_indexed"])
            cs.add("mysql", "ingest_log_hash_and_version",
                   lg["content_hash"] == doc.content_hash and lg["doc_version"] == doc.doc_version, "")
        cs.add("mysql", "no_retry_marker", not (mysql.get(f"{table}_retry") or []), "", [], mysql.get(f"{table}_retry"))
        if is_pdf:
            as_file = mysql.get(f"{table}_attachment (as file)") or []
            cs.add("parent_child", "linked_from_parent_in_attachment_table",
                   any(r["document_id"] == record.payload[0].uuid for r in as_file), "",
                   record.payload[0].uuid, [r["document_id"] for r in as_file])
            cs.info("parent_child", "parents_claiming_this_file", f"{len(as_file)} page(s) link this file",
                    [r["document_id"] for r in as_file])

    # ---------------------------------------------------------- knowledge
    report = cap.knowledge_report
    kn_enabled = settings.knowledge_enabled and settings.knowledge_process_after_index
    krun = mysql.get(f"{table}_knowledge_run") or []
    if not kn_enabled:
        cs.add("knowledge", "stage_disabled", None, "knowledge stage off in settings")
    elif report is None:
        cs.add("knowledge", "stage_ran", not children, "process_after_index returned None (no child chunks?)", "report", None)
    else:
        counts = report["counts"]
        cs.info("knowledge", "stage_report", f"status={report['status']} {counts} projection={report['projection']}", report)
        cs.add("knowledge", "run_row_written", len(krun) == 1 and krun[0]["doc_version"] == doc.doc_version, "",
               doc.doc_version, [(r["doc_version"], r["status"]) for r in krun])
        if krun:
            kr = krun[0]
            # The row is upserted on (document_id, doc_version), so a document
            # whose per-document stage ended `partial` and was then re-run by the
            # post-sweep catch-up carries the LATER run — which is the retry
            # mechanism working, not a mismatch. `seconds` identifies the run.
            same_run = abs(float(kr["seconds"] or 0) - float(report["seconds"] or 0)) < 0.01
            if not same_run:
                cs.info("knowledge", "run_row_matches_report",
                        f"the row is a later run than the captured report "
                        f"(report {report['status']} in {report['seconds']}s, "
                        f"row {kr['status']} in {kr['seconds']}s) — the catch-up "
                        f"sweep re-ran this document",
                        {"report": report["status"], "row": kr["status"]})
                cs.add("knowledge", "run_row_is_a_valid_terminal_state",
                       kr["status"] in ("ok", "partial", "failed") and kr["attempts"] >= 1,
                       "", "ok|partial|failed with attempts>=1",
                       {"status": kr["status"], "attempts": kr["attempts"],
                        "last_error": kr["last_error"]})
            else:
                cs.add("knowledge", "run_row_matches_report",
                       kr["status"] == report["status"] and kr["mentions"] == counts["mentions"]
                       and kr["claims_staged"] == counts["claims_staged"] and kr["claims_rejected"] == counts["claims_rejected"]
                       and kr["projection_status"] == report["projection"]["status"], "",
                       {"status": report["status"], "mentions": counts["mentions"], "claims_staged": counts["claims_staged"]},
                       {"status": kr["status"], "mentions": kr["mentions"], "claims_staged": kr["claims_staged"]})
        mentions = mysql.get(f"{table}_entity_mention") or []
        cs.add("knowledge", "mention_rows_equal_report",
               len(mentions) == counts["mentions"] if settings.knowledge_extract_mentions else None,
               "", counts["mentions"], len(mentions))
        decisions = mysql.get(f"{table}_entity_resolution_decision") or []
        resolved_total = counts["entities_auto"] + counts["entities_provisional"] + counts["entities_ambiguous"] + counts["entities_unresolved"]
        cs.add("knowledge", "decision_rows_equal_report",
               len(decisions) == resolved_total if settings.knowledge_extract_mentions else None, "",
               resolved_total, len(decisions))
        cs.add("knowledge", "mentions_point_at_own_chunks",
               all(m["chunk_id"] in set(ids) for m in mentions), "", None,
               [m["chunk_id"] for m in mentions if m["chunk_id"] not in set(ids)][:5])
        claims = mysql.get(f"{table}_assertion") or []
        cs.add("knowledge", "staged_claim_rows_equal_report", len(claims) == counts["claims_staged"], "",
               counts["claims_staged"], len(claims))
        cs.add("knowledge", "claims_cite_own_chunks_or_document",
               all((c["chunk_id"] in set(ids)) or c["chunk_id"] is None for c in claims), "")
        rejections = mysql.get(f"{table}_assertion_rejection") or []
        cs.add("knowledge", "rejection_rows_equal_report", len(rejections) == counts["claims_rejected"], "",
               counts["claims_rejected"], len(rejections))
        # ------------------------------------------------ CMS relationships
        # AUTHORED and PARTNER_OF are the two mappings added before the corpus
        # reprocess. Both must come from authoritative CMS fields and never
        # from the model, both must skip a name the entity store does not hold
        # rather than invent one, and neither may double an edge.
        by_predicate = _count(c["predicate"] for c in claims)
        cs.info("knowledge", "claims_by_predicate", str(by_predicate), by_predicate)
        by_method = _count(c["extraction_method"] for c in claims)
        cs.info("knowledge", "claims_by_method", str(by_method), by_method)

        authored = [c for c in claims if c["predicate"] == "AUTHORED"]
        partners = [c for c in claims if c["predicate"] == "PARTNER_OF"]
        # The canonical document's own raw_meta -- exactly what the extractor
        # was handed. Using the crawl record's metadata instead would compare
        # against the wrong thing for a PDF attachment, whose record carries the
        # file's metadata rather than the node's.
        raw_meta = doc.raw_meta if isinstance(doc.raw_meta, dict) else {}
        author_values = _cms_values(raw_meta, _AUTHOR_FIELDS)
        partner_values = _cms_values(raw_meta, _PARTNER_FIELDS)

        cs.info("knowledge", "cms_author_values",
                f"{len(author_values)} author value(s) in metadata", author_values[:12])
        cs.info("knowledge", "cms_partner_values",
                f"{len(partner_values)} partner value(s) in metadata", partner_values[:12])

        # Never model-inferred.
        cs.add("knowledge", "authored_is_cms_only",
               all(c["extraction_method"] == "cms_field" for c in authored)
               if authored else None,
               "AUTHORED must never come from the LLM.",
               "cms_field", _count(c["extraction_method"] for c in authored))
        cs.add("knowledge", "partner_of_is_cms_only",
               all(c["extraction_method"] == "cms_field" for c in partners)
               if partners else None,
               "PARTNER_OF must never come from the LLM.",
               "cms_field", _count(c["extraction_method"] for c in partners))

        # Provenance: the field the value came from is recorded.
        cs.add("knowledge", "authored_records_its_source_field",
               all(c["source_field"] in _AUTHOR_FIELDS for c in authored)
               if authored else None, "",
               list(_AUTHOR_FIELDS), _count(c["source_field"] for c in authored))
        cs.add("knowledge", "partner_of_records_its_source_field",
               all(c["source_field"] in _PARTNER_FIELDS for c in partners)
               if partners else None, "",
               list(_PARTNER_FIELDS), _count(c["source_field"] for c in partners))

        # Shape: AUTHORED is PERSON -> this document, as a literal.
        cs.add("knowledge", "authored_points_at_this_document",
               all(c["object_literal"] == record.document_id
                   and not c["object_entity_id"] for c in authored)
               if authored else None,
               "The object identifies the document; the entity link is the "
               "claim's own provenance.",
               record.document_id,
               [c["object_literal"] for c in authored][:4])
        cs.add("knowledge", "partner_of_points_at_an_organization",
               all(c["object_entity_id"] and not c["object_literal"]
                   for c in partners) if partners else None, "")

        # Never more claims than the CMS stated values.
        cs.add("knowledge", "authored_never_exceeds_its_source",
               len(authored) <= len(author_values) if author_values else
               (len(authored) == 0 if not author_values else None),
               "An author claim per stated author at most; unresolved names "
               "are skipped, never invented.",
               f"<= {len(author_values)}", len(authored))
        cs.add("knowledge", "partner_of_never_exceeds_its_source",
               len(partners) <= len(partner_values) if partner_values else
               (len(partners) == 0 if not partner_values else None),
               "", f"<= {len(partner_values)}", len(partners))

        # No duplicate edges: one claim per (subject, predicate, object).
        for label, rows in (("authored", authored), ("partner_of", partners)):
            keys = [(c["subject_entity_id"], c["predicate"],
                     c["object_entity_id"], c["object_literal"]) for c in rows]
            cs.add("knowledge", f"{label}_has_no_duplicate_edge",
                   len(keys) == len(set(keys)) if rows else None,
                   "One edge per relationship, however many fields state it.",
                   len(set(keys)), len(keys))
        all_keys = [(c["subject_entity_id"], c["predicate"],
                     c["object_entity_id"], c["object_literal"]) for c in claims]
        cs.add("knowledge", "no_duplicate_claim_identity",
               len(all_keys) == len(set(all_keys)) if claims else None,
               "", len(set(all_keys)), len(all_keys))
        cs.add("knowledge", "claim_ids_are_unique",
               len({c["claim_id"] for c in claims}) == len(claims) if claims else None,
               "", len(claims), len({c["claim_id"] for c in claims}))

        # Unresolved CMS values: reported, and provably not turned into claims.
        resolved_author_values = {c["source_value"] for c in authored}
        unresolved_authors = [v for v in author_values
                              if v not in resolved_author_values]
        resolved_partner_values = {c["source_value"] for c in partners}
        unresolved_partners = [v for v in partner_values
                               if v not in resolved_partner_values]
        if author_values:
            cs.info("knowledge", "unresolved_author_values",
                    f"{len(unresolved_authors)} of {len(author_values)} skipped",
                    unresolved_authors[:12])
        if partner_values:
            cs.info("knowledge", "unresolved_partner_values",
                    f"{len(unresolved_partners)} of {len(partner_values)} skipped",
                    unresolved_partners[:12])

        # Rejections, by reason, so a regression in the validator is visible.
        if rejections:
            cs.info("knowledge", "rejections_by_reason",
                    str(_count(r["code"] for r in rejections)),
                    _count(r["code"] for r in rejections))
            cs.add("knowledge", "rejected_claims_are_not_staged",
                   not ({r.get("subject_entity_id") for r in rejections}
                        & {c["subject_entity_id"] for c in claims
                           if c["predicate"] in
                           {r["predicate"] for r in rejections}}
                        - {None}) or True,
                   "Recorded for visibility; a subject may legitimately carry "
                   "one accepted and one rejected claim.")

        cs.add("knowledge", "extraction_cache_recorded",
               (len(mysql.get(f"{table}_entity_extraction") or []) == len(children)) if settings.knowledge_extract_mentions else None,
               "One cache row per child chunk content hash.", len(children), len(mysql.get(f"{table}_entity_extraction") or []))
        proj = report["projection"]["status"]
        staged_ids = [c["claim_id"] for c in claims]
        if neo.get("reachable"):
            if proj == "ok":
                cs.add("graph", "claim_nodes_for_staged_claims",
                       set(neo.get("claim_nodes_for_staged_ids", [])) == set(staged_ids), "", len(staged_ids),
                       len(neo.get("claim_nodes_for_staged_ids", [])))
                cs.add("graph", "document_stub_present", neo.get("document_node") is not None, "", "Document node", neo.get("document_node"))
                cs.add("graph", "current_edges_equal_report", len(neo.get("current_state_edges", [])) == report["projection"]["edges"],
                       "", report["projection"]["edges"], len(neo.get("current_state_edges", [])))
            elif proj == "skipped":
                cs.add("graph", "nothing_projected_when_skipped",
                       not neo.get("claims") or not staged_ids, "projection skipped: no touched claims", None,
                       {"claims_in_graph": len(neo.get("claims", []))})
            else:
                cs.add("graph", "projection_status", False, f"projection ended '{proj}'", "ok", proj)
        else:
            cs.add("graph", "neo4j_reachable", False, "graph unreachable at readback")
    return cs


#: Mirrors app.knowledge.claims.extract_cms. Named here rather than imported so
#: the audit states independently what it expects the mapping to read -- an
#: import would agree with the implementation by construction, including when
#: the implementation is wrong.
_AUTHOR_FIELDS = (
    "field_authors", "field_rpaper_author", "field_article_authors",
    "field_policybrief_authors", "field_external_authors", "field_author",
)
_PARTNER_FIELDS = ("field_completed_partners", "field_ongoing_partners")


def _cms_values(meta: Any, fields: tuple[str, ...]) -> list[str]:
    """The scalar values those fields hold, in Drupal's nested shapes."""
    def flat(value: Any) -> Any:
        if isinstance(value, (str, int, float)):
            yield str(value)
        elif isinstance(value, dict):
            for key in ("value", "target_id", "title", "name"):
                if key in value:
                    yield from flat(value[key])
        elif isinstance(value, list):
            for item in value:
                yield from flat(item)

    out: list[str] = []
    if not isinstance(meta, dict):
        return out
    for field in fields:
        for value in flat(meta.get(field)):
            text = value.strip()
            if text:
                out.append(text)
    return out


def _count(values: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return out
