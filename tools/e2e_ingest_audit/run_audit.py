"""Run the real ingestion pipeline on 30 freshly fetched documents and write
one evidence folder per document plus a run report.

    python -m tools.e2e_ingest_audit.run_audit --out reports/e2e_ingest_audit/<run>

Isolation (nothing here touches the production catalog, collection or graph):

* MySQL   — every table the pipeline writes derives its name from
            ``INGEST_STATE_TABLE`` / ``INGEST_LOG_TABLE``; both are pointed at
            ``e2e_audit_*`` before the app is imported.
* Qdrant  — ``QDRANT_COLLECTION=e2e_audit_documents``, recreated per run.
* Neo4j   — a throwaway container (same pinned image as docker-compose) on a
            different port; ``NEO4J_URI`` points at it. Removed at the end
            unless ``--keep-neo4j``.
* Crawl   — the real change detection runs, but its bundle enumeration is
            replaced by the freshly fetched selection (see select_docs.py), so
            the run does not start in 2017.

One runtime dependency is snapshotted from production rather than left empty:
the canonical entity store (``documents_entity`` / ``_alias`` / ``_identifier``)
is copied into the isolated prefix, because the per-document knowledge stage
resolves mentions against it and a deployment always has one. Nothing else is
copied, and no assertion in the checks reads production data.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PREFIX = "e2e_audit"
NEO4J_CONTAINER = "e2e-audit-neo4j"
NEO4J_IMAGE = "neo4j:2026.07.1-community"
NEO4J_BOLT_PORT = 7688
NEO4J_HTTP_PORT = 7475

_ENV = {
    "INGEST_STATE_TABLE": f"{PREFIX}_documents",
    "INGEST_LOG_TABLE": f"{PREFIX}_ingest_log",
    "QDRANT_COLLECTION": f"{PREFIX}_documents",
    "NEO4J_URI": f"bolt://localhost:{NEO4J_BOLT_PORT}",
    # Sequential so every nested observation can be attributed to one document.
    "INGEST_WORKERS": "1",
    "INGEST_LOG_UNCHANGED": "true",
    "IS_RETRIEVAL_LOG": "false",
    "SEMANTIC_CACHE_ENABLED": "false",
}


def _apply_env(use_container: bool) -> None:
    env = dict(_ENV)
    if not use_container:
        env.pop("NEO4J_URI")
    os.environ.update(env)


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


# --------------------------------------------------------------------------- #
# Neo4j container
# --------------------------------------------------------------------------- #

def _start_neo4j(password: str) -> None:
    subprocess.run(["docker", "rm", "-f", NEO4J_CONTAINER], capture_output=True)
    cmd = [
        "docker", "run", "-d", "--rm", "--name", NEO4J_CONTAINER,
        "-p", f"{NEO4J_BOLT_PORT}:7687", "-p", f"{NEO4J_HTTP_PORT}:7474",
        "-e", f"NEO4J_AUTH=neo4j/{password}",
        NEO4J_IMAGE,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"could not start the Neo4j container: {result.stderr.strip()}")
    from app.core.clients import graph_available, reset_graph_driver

    deadline = time.time() + 180
    while time.time() < deadline:
        reset_graph_driver()
        if graph_available():
            return
        time.sleep(3)
    raise RuntimeError("the Neo4j container did not accept connections within 180s")


def _stop_neo4j() -> None:
    subprocess.run(["docker", "rm", "-f", NEO4J_CONTAINER], capture_output=True)


# --------------------------------------------------------------------------- #
# Stores
# --------------------------------------------------------------------------- #

def _drop_isolated_tables(prefix: str) -> list[str]:
    from app.core.clients import mysql_connection
    from tools.e2e_ingest_audit.readback import existing_tables

    tables = existing_tables(prefix)
    for name in tables:
        assert name.startswith(prefix), name
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for name in tables:
            cur.execute(f"DROP TABLE IF EXISTS `{name}`")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
    return tables


def _ensure_isolated_tables() -> None:
    from app.catalog import schema

    schema.ensure_state_table()
    schema.ensure_log_table()
    schema.ensure_retry_table()
    schema.ensure_dead_link_table()
    schema.ensure_date_decision_table()
    schema.ensure_entity_tables()
    schema.ensure_resolution_tables()
    schema.ensure_assertion_tables()
    schema.ensure_predicate_candidate_table()
    schema.ensure_knowledge_run_table()


def _snapshot_entities(prefix_table: str, production_table: str) -> dict[str, int]:
    """Copy the canonical entity store into the isolated prefix (columns by name)."""
    from app.core.clients import mysql_connection

    copied: dict[str, int] = {}
    with mysql_connection() as conn, conn.cursor() as cur:
        for suffix in ("_entity", "_entity_alias", "_entity_identifier"):
            src, dst = f"{production_table}{suffix}", f"{prefix_table}{suffix}"
            cur.execute(
                "SELECT table_name AS t, column_name AS c FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name IN (%s, %s)", (src, dst),
            )
            cols: dict[str, set[str]] = {}
            for r in cur.fetchall():
                cols.setdefault(r["t"], set()).add(r["c"])
            if src not in cols or dst not in cols:
                copied[dst] = -1
                continue
            shared = sorted(cols[src] & cols[dst])
            col_list = ", ".join(f"`{c}`" for c in shared)
            cur.execute(f"INSERT IGNORE INTO `{dst}` ({col_list}) SELECT {col_list} FROM `{src}`")
            copied[dst] = cur.rowcount
        conn.commit()
    return copied


def _reset_collection() -> None:
    from app.config import get_settings
    from app.core.clients import ensure_collection, get_qdrant_client
    from app.core.clients import vector_store

    name = get_settings().qdrant_collection
    assert name.startswith(PREFIX), name
    client = get_qdrant_client()
    if client.collection_exists(name):
        client.delete_collection(name)
    vector_store._ensured_collections.discard(name)
    ensure_collection()


# --------------------------------------------------------------------------- #
# Per-document artifacts
# --------------------------------------------------------------------------- #

def _website_extraction(raw: dict[str, Any] | None, record: Any) -> dict[str, Any]:
    from app.ingestion.extractors.drupal_extractor import LONG_TEXT_THRESHOLD, _html_to_text

    fields: list[dict[str, Any]] = []
    attributes = ((raw or {}).get("jsonapi_resource") or {}).get("attributes") or {}
    for key, value in attributes.items():
        if isinstance(value, dict) and ("processed" in value or "value" in value):
            html = value.get("processed") or value.get("value") or ""
            fields.append({"field": key, "kind": "formatted_text", "html_chars": len(html),
                           "html": html, "text": _html_to_text(html)})
        elif isinstance(value, str) and len(value) > LONG_TEXT_THRESHOLD and key.startswith("field_"):
            fields.append({"field": key, "kind": "long_string", "html_chars": len(value),
                           "html": value, "text": _html_to_text(value)})
    return {
        "rich_text_fields": fields,
        "record_body": record.body,
        "record_body_chars": len(record.body),
        "files_discovered": [vars(f) for f in record.files],
        "entity_refs": [vars(r) for r in record.refs],
        "scalar_metadata": record.metadata,
    }


def _write_document_folder(run_dir: Path, index: int, cap: Any, selection: Any, settings: Any,
                           table: str, log_table: str, captures_by_id: dict[str, Any]) -> dict[str, Any]:
    from tools.e2e_ingest_audit import checks as chk
    from tools.e2e_ingest_audit import readback, render
    from tools.e2e_ingest_audit.serialize import dump_json, to_jsonable

    record = cap.record
    is_pdf = record.source_type == "pdf_attachment"
    folder_name = f"{index:02d}_{'pdf' if is_pdf else 'web'}_{_safe(record.bundle or 'none')}_{_safe(record.document_id)[:40]}"
    folder = run_dir / "documents" / folder_name
    (folder / "00_source").mkdir(parents=True, exist_ok=True)
    files: list[tuple[str, str]] = []

    # 00 source
    if is_pdf:
        node, file = record.payload
        dump_json(folder / "00_source" / "parent_record.json", selection.raw_by_uuid.get(node.uuid))
        files.append(("00_source/parent_record.json", "raw JSON:API resource of the parent page (plus included entities)"))
        dump_json(folder / "00_source" / "file_link.json", {"drupal_file": vars(file), "download": cap.download})
        files.append(("00_source/file_link.json", "the file reference as discovered on the page, and the download result"))
        if cap.pdf_bytes:
            pdf_name = _safe(file.filename or "document.pdf")[:80]
            if not pdf_name.lower().endswith(".pdf"):
                pdf_name += ".pdf"
            (folder / "00_source" / pdf_name).write_bytes(cap.pdf_bytes)
            files.append((f"00_source/{pdf_name}", "the freshly downloaded PDF bytes"))
    else:
        dump_json(folder / "00_source" / "record.json", {
            "raw": selection.raw_by_uuid.get(record.document_id),
            "parsed_drupal_record": to_jsonable(record.payload),
        })
        files.append(("00_source/record.json", "raw JSON:API resource (with included entities) and the parsed DrupalRecord"))

    # 01 change record
    dump_json(folder / "01_change_record.json", {
        "status": record.status.value, "document_id": record.document_id,
        "source_type": record.source_type, "source_key": record.source_key,
        "fingerprint": record.fingerprint, "bundle": record.bundle,
        "entity_type": record.entity_type, "changed_mark": record.changed_mark,
        "filename": record.filename, "prior": to_jsonable(record.prior),
        "outcome": cap.outcome, "error": cap.error, "traceback": cap.traceback,
        "started_at": cap.started_at, "finished_at": cap.finished_at,
        "elapsed_seconds": cap.elapsed_seconds,
        "stage_seconds": {"build_doc": cap.build_seconds, "pdf_extraction": cap.extraction_seconds,
                          "chunk": cap.chunk_seconds, "embed_and_upsert": cap.index_seconds,
                          "knowledge": cap.knowledge_seconds},
    })
    files.append(("01_change_record.json", "the ChangeRecord as yielded by detect_drupal_changes, and the handler outcome"))

    # 02 extraction
    html_fields = None
    if is_pdf:
        dump_json(folder / "02_extraction.json", cap.extraction)
        files.append(("02_extraction.json", "ExtractionResult: every page's text, route (text/ocr/empty), tables, PDF metadata"))
    else:
        ext = _website_extraction(selection.raw_by_uuid.get(record.document_id), record.payload)
        html_fields = len(ext["rich_text_fields"])
        dump_json(folder / "02_extraction.json", ext)
        files.append(("02_extraction.json", "HTML→text per rich-text field, discovered PDF links, entity refs, scalar metadata"))

    # 03 canonical
    doc = cap.doc
    if doc is not None:
        canonical = to_jsonable(doc)
        canonical.pop("date_evidence", None)
        dump_json(folder / "03_canonical.json", canonical)
        (folder / "03_canonical_text.txt").write_text(doc.full_text(), encoding="utf-8")
        files.append(("03_canonical.json", "CanonicalDocument (all fields, all sections)"))
        files.append(("03_canonical_text.txt", "full_text(): the exact string content_hash covers"))

    # 04 dates
    parent_cap = captures_by_id.get(record.payload[0].uuid) if is_pdf else None
    dump_json(folder / "04_dates.json", {
        "canonical": None if doc is None else {
            "effective_start_date": doc.effective_start_date, "start_precision": doc.start_precision,
            "date_source": doc.date_source, "effective_end_date": doc.effective_end_date,
            "end_precision": doc.end_precision, "edition_label": doc.extra.get("edition_label"),
        },
        "website_evidence": None if (is_pdf or doc is None) else to_jsonable(doc.date_evidence),
        "record_created": None if is_pdf else record.payload.created,
        "record_changed": None if is_pdf else record.payload.changed,
        "parent_page_resolution": to_jsonable(cap.parent_date),
        "file_resolution": to_jsonable(cap.resolved_date),
        "parent_page_canonical_date": None if parent_cap is None or parent_cap.doc is None else {
            "effective_start_date": parent_cap.doc.effective_start_date,
            "start_precision": parent_cap.doc.start_precision,
            "effective_end_date": parent_cap.doc.effective_end_date,
        },
    })
    files.append(("04_dates.json", "EffectiveDate evidence (page) / ResolvedDate (file), raw CMS values, what was applied"))

    # 05 chunks
    chunks_out = []
    for c in cap.chunks:
        d = to_jsonable(c)
        d["payload"] = c.to_payload()
        d["embed_hash"] = c.embed_hash
        chunks_out.append(d)
    dump_json(folder / "05_chunks.json", {"parents": sum(1 for c in cap.chunks if c.is_parent),
                                          "children": sum(1 for c in cap.chunks if not c.is_parent),
                                          "chunks": chunks_out})
    (folder / "05_chunks.md").write_text(render.chunk_tree(cap.chunks), encoding="utf-8")
    files.append(("05_chunks.json", "every Chunk: text, embed_text, ids, parent link, pages, tokens, the payload it was indexed with"))
    files.append(("05_chunks.md", "the parent/child tree in readable form"))

    # 06-09 read-back
    chunk_ids = [c.chunk_id for c in cap.chunks]
    hashes = sorted({c.content_hash for c in cap.chunks if not c.is_parent})
    mysql = readback.mysql_document(record.document_id, chunk_ids=chunk_ids, content_hashes=hashes)
    qdrant = readback.qdrant_document(record.document_id)
    claim_ids = [r["claim_id"] for r in (mysql.get(f"{table}_assertion") or [])]
    neo = readback.neo4j_document(record.document_id, claim_ids)
    dump_json(folder / "06_qdrant.json", qdrant)
    dump_json(folder / "07_mysql.json", mysql)
    dump_json(folder / "08_knowledge.json", {
        "stage_report": cap.knowledge_report,
        "knowledge_run_rows": mysql.get(f"{table}_knowledge_run"),
        "mentions": mysql.get(f"{table}_entity_mention"),
        "resolution_decisions": mysql.get(f"{table}_entity_resolution_decision"),
        "extraction_cache": mysql.get(f"{table}_entity_extraction"),
        "assertions": mysql.get(f"{table}_assertion"),
        "assertion_rejections": mysql.get(f"{table}_assertion_rejection"),
        "assertion_links": mysql.get(f"{table}_assertion_link"),
        "predicate_candidates": mysql.get(f"{table}_predicate_candidate"),
        "entities_referenced": mysql.get(f"{table}_entity (referenced)"),
    })
    dump_json(folder / "09_neo4j.json", neo)
    files.append(("06_qdrant.json", "every point read back from Qdrant: payload + vector summary"))
    files.append(("07_mysql.json", "every row in every catalog/knowledge table that refers to this document"))
    files.append(("08_knowledge.json", "knowledge StageReport + the mention/decision/claim/rejection/candidate rows"))
    files.append(("09_neo4j.json", "Document stub, chunk stubs, Claim nodes and current-state edges in the graph"))

    rb = {"mysql": mysql, "qdrant": qdrant, "neo4j": neo}
    cs = chk.run_checks(cap, rb, captures_by_id, settings=settings, table=table, log_table=log_table)
    dump_json(folder / "10_checks.json", [c.as_dict() for c in cs.checks])
    (folder / "log.txt").write_text("\n".join(cap.log_lines), encoding="utf-8")
    files.append(("10_checks.json", "every cross-stage check with expected/actual"))
    files.append(("log.txt", "the pipeline's own log lines while this document was handled"))

    ctx = {"cap": cap, "checks": cs.checks, "readback": rb, "folder": folder_name, "files": files,
           "table": table, "html_fields": html_fields}
    (folder / "README.md").write_text(render.document_readme(ctx), encoding="utf-8")

    return {"folder": folder_name, "cap": cap, "checks": cs, "readback": rb}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", type=int, default=30, help="documents to ingest (nodes + their PDFs)")
    parser.add_argument("--per-bundle-cap", type=int, default=3, help="soft cap on nodes per bundle")
    parser.add_argument("--per-source-fetch", type=int, default=12, help="newest records sampled per source")
    parser.add_argument("--out", help="results directory (default reports/e2e_ingest_audit/run-<ts>)")
    parser.add_argument("--keep-neo4j", action="store_true", help="leave the throwaway Neo4j container running")
    parser.add_argument("--no-neo4j-container", action="store_true",
                        help="use the configured NEO4J_URI instead of a throwaway container (not isolated!)")
    parser.add_argument("--no-entity-snapshot", action="store_true",
                        help="do not copy the production entity store into the isolated prefix")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    _apply_env(use_container=not args.no_neo4j_container)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    # Server-side "property key does not exist" notices on an empty graph are
    # not evidence of anything; keep the captured log readable.
    logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    started = datetime.now(timezone.utc)
    repo = Path(__file__).resolve().parents[2]
    run_dir = Path(args.out).resolve() if args.out else (
        repo / "reports" / "e2e_ingest_audit" / f"run-{started:%Y%m%d-%H%M%S}")
    run_dir.mkdir(parents=True, exist_ok=True)

    from app.catalog.db import log_table as _log_table
    from app.catalog.db import state_table as _state_table
    from app.config import get_settings
    from app.ingestion.version import PIPELINE_VERSION
    from tools.e2e_ingest_audit import readback, render, select_docs
    from tools.e2e_ingest_audit.capture import Captures, observed_pipeline
    from tools.e2e_ingest_audit.serialize import dump_json, to_jsonable

    get_settings.cache_clear()
    settings = get_settings()
    table, log_table = _state_table(), _log_table()
    assert table.startswith(PREFIX) and log_table.startswith(PREFIX)
    print(f"results -> {run_dir}")
    print(f"isolated MySQL prefix {table!r}, Qdrant collection {settings.qdrant_collection!r}, Neo4j {settings.neo4j_uri}")

    neo4j_started = False
    try:
        if not args.no_neo4j_container:
            print("starting throwaway Neo4j container ...")
            _start_neo4j(settings.neo4j_password)
            neo4j_started = True
            print("neo4j ready")

        dropped = _drop_isolated_tables(PREFIX + "_")
        _ensure_isolated_tables()
        snapshot = {} if args.no_entity_snapshot else _snapshot_entities(table, "documents")
        _reset_collection()
        print(f"stores prepared (dropped {len(dropped)} stale tables; entity snapshot {snapshot})")

        # ---- selection --------------------------------------------------
        from app.ingestion.extractors.drupal_extractor import _build_session

        session = _build_session(settings.drupal_max_retries)
        try:
            print("sampling newest records from every source ...")
            candidates = select_docs.fetch_candidates(session, args.per_source_fetch)
            selection = select_docs.choose(candidates, target=args.target, per_bundle_cap=args.per_bundle_cap)
        finally:
            session.close()
        print(f"selected {len(selection.records)} nodes -> {selection.expected_documents} documents "
              f"({selection.expected_attachments} attachments) from {selection.candidates_seen} candidates")
        dump_json(run_dir / "selection.json", {
            "target": args.target, "per_bundle_cap": args.per_bundle_cap,
            "per_source_fetch": args.per_source_fetch,
            "candidates_seen": selection.candidates_seen,
            "per_source_fetched": selection.per_source_fetched,
            "expected_documents": selection.expected_documents,
            "expected_attachments": selection.expected_attachments,
            "bundle_specs": selection.bundle_specs(),
            "nodes": [{"uuid": r.uuid, "bundle": r.bundle, "entity_type": r.metadata.get("entity_type", "node"),
                       "nid": r.nid, "title": r.title, "url": r.url, "created": r.created, "changed": r.changed,
                       "files": [{"uuid": f.uuid, "origin": f.origin, "filename": f.filename, "url": f.url} for f in r.files]}
                      for r in selection.records],
        })

        # ---- the run ----------------------------------------------------
        from app.ingestion.pipeline import ingest_drupal

        captures = Captures()
        captures.progress = lambda cap: print(
            f"  [{cap.order:02d}] {cap.record.source_type:14} {cap.outcome or '?':17} "
            f"chunks={len(cap.chunks):<4} {cap.elapsed_seconds:>7}s  {cap.record.document_id}"
        )
        print("running ingest_drupal ...")
        t0 = time.perf_counter()
        with observed_pipeline(captures), select_docs.substitute_crawl(selection):
            tally = ingest_drupal(selection.bundle_specs())
        ingest_seconds = round(time.perf_counter() - t0, 1)
        print(f"ingest_drupal finished in {ingest_seconds}s: {dict(tally)}")

        # ---- the sweep tail ---------------------------------------------
        from app.ingestion.graph_sync import project_after_sweep
        from app.ingestion.knowledge_sync import catch_up
        from app.ingestion.reconcile import reconcile_after_sweep
        from app.observability import metrics

        print("post-sweep: knowledge catch-up, graph projection, reconciliation ...")
        post_sweep: dict[str, Any] = {}
        with observed_pipeline(captures):
            post_sweep["knowledge_catch_up"] = catch_up()
            post_sweep["graph_projection"] = project_after_sweep()
            report = reconcile_after_sweep()
            post_sweep["reconciliation"] = report.as_dict() if report is not None else None
        dump_json(run_dir / "post_sweep.json", post_sweep)
        dump_json(run_dir / "timings.json", metrics.snapshot())
        (run_dir / "run.log").write_text("\n".join(captures.run_log), encoding="utf-8")

        # ---- per-document evidence --------------------------------------
        print("reading back stores and writing per-document folders ...")
        results = []
        for cap in captures.ordered():
            try:
                results.append(_write_document_folder(run_dir, cap.order, cap, selection, settings,
                                                      table, log_table, captures.by_id))
            except Exception:
                # A harness defect must not lose the run: record it beside the
                # document and keep going, so the stores can still be read.
                import traceback as _tb
                err_dir = run_dir / "documents"
                err_dir.mkdir(parents=True, exist_ok=True)
                (err_dir / f"{cap.order:02d}_HARNESS_ERROR.txt").write_text(_tb.format_exc(), encoding="utf-8")
                print(f"  !! harness error writing document {cap.order}: see documents/{cap.order:02d}_HARNESS_ERROR.txt")

        # ---- run-level -------------------------------------------------
        tables = readback.existing_tables(PREFIX + "_")
        table_counts = readback.table_counts(tables)
        qdrant_info = readback.qdrant_collection_info()
        neo_stats = readback.neo4j_stats()

        doc_rows, doc_traces, matrix = [], [], {}
        for r in results:
            cap, cs = r["cap"], r["checks"]
            doc = cap.doc
            rep = cap.knowledge_report or {}
            fails = cs.failed
            doc_rows.append({
                "#": cap.order, "type": "pdf" if cap.record.source_type == "pdf_attachment" else "web",
                "bundle": cap.record.bundle, "outcome": cap.outcome,
                "title": (doc.title if doc else None), "date": (doc.effective_start_date or "")[:10] if doc else None,
                "date_source": doc.date_source if doc else None,
                "parents": sum(1 for c in cap.chunks if c.is_parent),
                "children": sum(1 for c in cap.chunks if not c.is_parent),
                "points": r["readback"]["qdrant"].get("count"),
                "claims": (rep.get("counts") or {}).get("claims_staged"),
                "proj": (rep.get("projection") or {}).get("status"),
                "fail": len(fails), "folder": r["folder"],
            })
            for c in cs.checks:
                key = (c.category, c.name)
                m = matrix.setdefault(key, {"category": c.category, "check": c.name, "pass": 0, "fail": 0, "n/a": 0, "failing documents": []})
                if c.status in ("pass", "fail", "n/a"):
                    m[c.status] += 1
                if c.status == "fail":
                    m["failing documents"].append(str(cap.order))
            lines = []
            rec = cap.record
            if rec.source_type == "pdf_attachment":
                node, file = rec.payload
                lines.append(f"source: PDF `{file.filename}` ({file.origin}) on page `{node.uuid}` “{node.title}” · "
                             f"{(cap.download or {}).get('bytes')} bytes")
                if cap.extraction is not None:
                    routes = Counter(p.extracted_via.value for p in cap.extraction.pages)
                    lines.append(f"extraction: {len(cap.extraction.pages)} pages, routes {dict(routes)}, "
                                 f"{sum(len(p.tables) for p in cap.extraction.pages)} tables, "
                                 f"{sum(len(p.text) for p in cap.extraction.pages)} chars")
            else:
                lines.append(f"source: node `{rec.document_id}` ({rec.bundle}) “{rec.payload.title}” · body {len(rec.payload.body)} chars · "
                             f"{len(rec.payload.files)} PDF link(s) · created {rec.payload.created} · changed {rec.payload.changed}")
            lines.append(f"outcome: **{cap.outcome}** in {cap.elapsed_seconds}s" + (f" — {cap.error}" if cap.error else ""))
            if doc is not None:
                lines.append(f"canonical: title “{doc.title}” · {len(doc.sections)} section(s) · {len(doc.full_text())} chars · hash `{doc.content_hash[:12]}…` · "
                             f"authors {doc.authors} · tags {doc.tags} · categories {doc.categories}")
                lines.append(f"dates: start {doc.effective_start_date} ({doc.start_precision}, {doc.date_source}) · end {doc.effective_end_date}"
                             + (f" · page rule `{cap.parent_date.rule}`" if cap.parent_date is not None else
                                (f" · rule `{doc.date_evidence.rule}` fields {list(doc.date_evidence.fields)} raw {list(doc.date_evidence.raw_values)}" if doc.date_evidence is not None else ""))
                             + (f" · file resolver: {'OVERRIDE' if cap.resolved_date.overridden else 'inherit'} ({cap.resolved_date.decision.rule if cap.resolved_date.decision else 'no decision'})" if cap.resolved_date is not None else ""))
            lines.append(f"chunks: {doc_rows[-1]['parents']} parents / {doc_rows[-1]['children']} children · Qdrant points {doc_rows[-1]['points']}")
            m = r["readback"]["mysql"]
            lines.append("mysql: " + ", ".join(f"{k.replace(table + '_', '·').replace(table, 'documents')}={len(v)}"
                                                for k, v in m.items() if v))
            if rep:
                lines.append(f"knowledge: {rep['status']} · mentions {rep['counts']['mentions']} · resolved auto/prov/amb/unres "
                             f"{rep['counts']['entities_auto']}/{rep['counts']['entities_provisional']}/{rep['counts']['entities_ambiguous']}/{rep['counts']['entities_unresolved']} · "
                             f"claims built/staged/rejected {rep['counts']['claims_built']}/{rep['counts']['claims_staged']}/{rep['counts']['claims_rejected']} · "
                             f"projection {rep['projection']['status']} ({rep['projection']['edges']} edges)")
                notes = [n for st in rep["stages"] for n in (st.get("notes") or [])]
                if notes:
                    lines.append(f"knowledge notes: {notes}")
            n = r["readback"]["neo4j"]
            if n.get("reachable"):
                lines.append(f"neo4j: document stub {'yes' if n.get('document_node') else 'no'} · claim nodes {len(n.get('claims', []))} · current edges {len(n.get('current_state_edges', []))}")
            lines.append(f"checks: {sum(1 for c in cs.checks if c.status == 'pass')} pass / {len(fails)} fail · folder `documents/{r['folder']}/`")
            doc_traces.append({"index": cap.order, "folder": r["folder"], "lines": lines,
                               "fails": [c.as_dict() for c in fails]})

        for m in matrix.values():
            m["failing documents"] = ", ".join(m["failing documents"])
        finished = datetime.now(timezone.utc)
        isolation_notes = [
            f"MySQL tables: `{table}*` and `{log_table}` (created fresh; {len(dropped)} stale tables dropped first). Production `documents*` untouched.",
            f"Qdrant collection: `{settings.qdrant_collection}` (recreated). Production `documents` collection untouched.",
            (f"Neo4j: throwaway container `{NEO4J_CONTAINER}` ({NEO4J_IMAGE}) at `{settings.neo4j_uri}`, empty at start."
             if neo4j_started else f"Neo4j: the configured instance at `{settings.neo4j_uri}` (NOT isolated)."),
            (f"Entity store snapshot: production `documents_entity/_alias/_identifier` copied into the isolated prefix "
             f"({snapshot}) so mention resolution runs against the index a deployment has. No check reads production data."
             if snapshot else "Entity store: left empty (no snapshot)."),
            "Gazetteer, author facet and CMS-claim context are built from the isolated catalog, i.e. only from these 30 documents' metadata, "
            "so mention recognition is narrower than in production (see the assessment).",
            f"Workers forced to 1 (production .env has INGEST_WORKERS={os.environ.get('INGEST_WORKERS_ORIG', '2')}); the per-document logic is identical, only concurrency differs.",
            f"Feature flags as in .env: knowledge_enabled={settings.knowledge_enabled}, knowledge_process_after_index={settings.knowledge_process_after_index}, "
            f"knowledge_extract_mentions={settings.knowledge_extract_mentions}, claim_extraction_enabled={settings.claim_extraction_enabled}, "
            f"knowledge_project_per_document={settings.knowledge_project_per_document}, enrichment_enabled={settings.enrichment_enabled}, "
            f"date_resolution_enabled={settings.date_resolution_enabled}, extraction_mode={settings.extraction_mode}, "
            f"verify_corpus_after_sweep={settings.verify_corpus_after_sweep}.",
            "Selection: newest-first sample of every configured source; the real detect_drupal_changes ran with only its bundle enumeration substituted.",
        ]
        ctx = {
            "run_id": f"{started:%Y%m%d-%H%M%S}", "started_at": started.isoformat(timespec="seconds"),
            "finished_at": finished.isoformat(timespec="seconds"), "pipeline_version": PIPELINE_VERSION,
            "run_dir": str(run_dir), "isolation_notes": isolation_notes,
            "selection": {"candidates_seen": selection.candidates_seen, "per_source_fetched": selection.per_source_fetched,
                          "nodes_chosen": len(selection.records), "expected_attachments": selection.expected_attachments,
                          "expected_documents": selection.expected_documents, "bundles": selection.bundle_specs()},
            "handled": len(results), "tally": dict(tally), "ingest_seconds": ingest_seconds,
            "post_sweep": post_sweep, "qdrant_info": qdrant_info, "neo4j_stats": neo_stats,
            "table_counts": table_counts, "doc_rows": doc_rows,
            "check_matrix": sorted(matrix.values(), key=lambda m: (m["category"], m["check"])),
            "doc_traces": doc_traces,
        }
        (run_dir / "REPORT.md").write_text(render.run_report(ctx), encoding="utf-8")
        dump_json(run_dir / "summary.json", {
            **{k: v for k, v in ctx.items() if k not in ("doc_traces",)},
            "settings": {k: v for k, v in to_jsonable(settings).items()
                         if not any(s in k for s in ("key", "password", "secret"))},
            "documents": [{"order": r["cap"].order, "document_id": r["cap"].document_id, "folder": r["folder"],
                           "outcome": r["cap"].outcome, "checks_failed": [c.name for c in r["checks"].failed]}
                          for r in results],
        })
        total_fail = sum(len(r["checks"].failed) for r in results)
        print(f"done: {len(results)} documents, {total_fail} failed checks. Report: {run_dir / 'REPORT.md'}")
        return 0 if total_fail == 0 else 1
    finally:
        if neo4j_started and not args.keep_neo4j:
            _stop_neo4j()
            print("neo4j container removed")


if __name__ == "__main__":
    raise SystemExit(main())
