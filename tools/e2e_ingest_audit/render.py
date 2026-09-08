"""Human-readable renderings: one README per document folder, a chunk tree,
and the run-level REPORT.md skeleton (per-document trace + aggregates)."""
from __future__ import annotations

from typing import Any


def _esc(value: Any) -> str:
    text = "-" if value in (None, "", [], {}) else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _short(value: Any, n: int = 90) -> str:
    text = _esc(value)
    return text if len(text) <= n else text[: n - 1] + "…"


def _table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_none_\n"
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_short(row.get(c)) for c in columns) + " |")
    return "\n".join(out) + "\n"


def chunk_tree(chunks: list[Any]) -> str:
    lines = ["# Chunk tree (parents and their children)", ""]
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    lines.append(f"{len(parents)} parent(s), {len(children)} child(ren)")
    lines.append("")
    by_parent: dict[str | None, list[Any]] = {}
    for c in children:
        by_parent.setdefault(c.parent_chunk_id, []).append(c)
    for p in parents:
        lines.append(f"## PARENT {p.chunk_id}")
        lines.append(f"- heading: {p.section_heading!r} · type: {p.section_type} · tokens: {p.token_count}"
                     f" · pages: {p.page_range} · has_table: {p.has_table}")
        lines.append("")
        lines.append("```text")
        lines.append(p.text)
        lines.append("```")
        for c in by_parent.get(p.chunk_id, []):
            _child(lines, c, indent="    ")
        lines.append("")
    orphans = by_parent.get(None, [])
    if orphans:
        lines.append("## CHILDREN WITHOUT A PARENT RECORD (single-child windows)")
        for c in orphans:
            _child(lines, c, indent="")
    return "\n".join(lines) + "\n"


def _child(lines: list[str], c: Any, indent: str) -> None:
    lines.append(f"{indent}### CHILD #{c.chunk_index} {c.chunk_id}")
    lines.append(f"{indent}- heading: {c.section_heading!r} · type: {c.section_type} · tokens: {c.token_count}"
                 f" · page: {c.page_number} · pages: {c.page_range} · overlap_pages: {c.overlap_page_range}"
                 f" · has_table: {c.has_table}")
    lines.append(f"{indent}- embed_text prefix: {c.embed_text[: max(0, len(c.embed_text) - len(c.text))].strip()!r}")
    lines.append("")
    lines.append(f"{indent}```text")
    for line in c.text.splitlines():
        lines.append(f"{indent}{line}")
    lines.append(f"{indent}```")


def document_readme(ctx: dict[str, Any]) -> str:
    cap, doc, rec = ctx["cap"], ctx["cap"].doc, ctx["cap"].record
    checks = ctx["checks"]
    rb = ctx["readback"]
    is_pdf = rec.source_type == "pdf_attachment"
    L: list[str] = []
    L.append(f"# {ctx['folder']}")
    L.append("")
    L.append(f"**{rec.source_type}** · bundle `{rec.bundle}` · outcome **{cap.outcome}**"
             + (f" · error `{cap.error}`" if cap.error else ""))
    L.append("")
    L.append(f"- document_id: `{rec.document_id}`")
    L.append(f"- title: {_esc(doc.title if doc else None)}")
    L.append(f"- source_key: {rec.source_key}")
    if is_pdf:
        node, file = rec.payload
        L.append(f"- parent page: `{node.uuid}` — {_esc(node.title)} ({node.url})")
        L.append(f"- file: {file.filename} · origin `{file.origin}` · description {_esc(file.description)}")
    L.append(f"- handled in {cap.elapsed_seconds}s (build {cap.build_seconds}s, extract {cap.extraction_seconds}s, "
             f"chunk {cap.chunk_seconds}s, embed+upsert {cap.index_seconds}s, knowledge {cap.knowledge_seconds}s)")
    L.append("")
    L.append("## Files in this folder")
    L.append("")
    for name, what in ctx["files"]:
        L.append(f"- `{name}` — {what}")
    L.append("")
    L.append("## Stage trace")
    L.append("")
    L.append("### 1. Source (fresh fetch)")
    if is_pdf:
        d = cap.download or {}
        L.append(f"- downloaded {d.get('bytes')} bytes from `{d.get('fetched_url')}` "
                 f"(requested `{d.get('requested_url')}`, https upgrade: {d.get('upgraded_to_https')}) · sha256 `{d.get('sha256')}`")
    else:
        L.append(f"- JSON:API `{rec.entity_type}/{rec.bundle}` uuid `{rec.document_id}` · nid {rec.payload.nid} · "
                 f"created {rec.payload.created} · changed {rec.payload.changed}")
    L.append(f"- change detection: status **{rec.status.value}** · fingerprint `{rec.fingerprint}` · changed_mark {rec.changed_mark} · prior: {rec.prior is not None}")
    L.append("")
    L.append("### 2. Extraction")
    if is_pdf and cap.extraction is not None:
        ext = cap.extraction
        routes: dict[str, int] = {}
        for p in ext.pages:
            routes[p.extracted_via.value] = routes.get(p.extracted_via.value, 0) + 1
        L.append(f"- {len(ext.pages)} page(s) · routes {routes} · tables {sum(len(p.tables) for p in ext.pages)} · "
                 f"PDF metadata keys {sorted(ext.metadata.keys())[:12]}")
        L.append(f"- characters: {sum(len(p.text) for p in ext.pages)} · empty pages: {sum(1 for p in ext.pages if not p.text.strip())}")
    elif not is_pdf:
        L.append(f"- HTML→text: body {len(rec.payload.body)} chars from {ctx.get('html_fields', '?')} rich-text field(s); "
                 f"{len(rec.payload.files)} PDF link(s) discovered ({[f.origin for f in rec.payload.files]})")
    L.append("")
    L.append("### 3. Canonical document")
    if doc is not None:
        L.append(f"- sections {len(doc.sections)} · body chars {len(doc.full_text())} · content_hash `{doc.content_hash}` · doc_version {doc.doc_version}")
        L.append(f"- authors {doc.authors} · tags {doc.tags} · categories {doc.categories}")
        L.append(f"- entity_refs {len(doc.entity_refs)} · file_links {[(f.uuid, f.origin) for f in doc.file_links]}")
        L.append(f"- extra {doc.extra}")
    L.append("")
    L.append("### 4. Dates")
    if doc is not None:
        L.append(f"- effective_start_date **{doc.effective_start_date}** (precision {doc.start_precision}, source {doc.date_source}) · "
                 f"effective_end_date {doc.effective_end_date} (precision {doc.end_precision})")
        if is_pdf and cap.parent_date is not None:
            pd, rd = cap.parent_date, cap.resolved_date
            L.append(f"- parent page resolution: rule `{pd.rule}` source `{pd.source}` fields {list(pd.fields)} raw {list(pd.raw_values)}")
            if rd is not None:
                L.append(f"- file resolver: overridden={rd.overridden} · decision action `{rd.decision.action if rd.decision else None}` "
                         f"rule `{rd.decision.rule if rd.decision else None}` · edition_label {rd.edition_label} · evidence used {rd.used}")
                if rd.decision is not None:
                    L.append(f"- decision evidence: {rd.decision.evidence}")
        elif doc.date_evidence is not None:
            ev = doc.date_evidence
            L.append(f"- rule `{ev.rule}` · source `{ev.source}` · fields {list(ev.fields)} · raw values {list(ev.raw_values)} · role {ev.field_role} · range_issue {ev.range_issue}")
        rows = rb["mysql"].get(ctx["table"] + "_date_decision") or []
        L.append(f"- date_decision rows in MySQL: {len(rows)}" + (f" — action `{rows[0]['action']}` rule `{rows[0]['rule']}` candidate {rows[0]['candidate_start_date']}" if rows else ""))
    L.append("")
    L.append("### 5. Chunks")
    parents = [c for c in cap.chunks if c.is_parent]
    children = [c for c in cap.chunks if not c.is_parent]
    if cap.chunks:
        L.append(f"- {len(parents)} parent(s), {len(children)} child(ren) · child tokens min/avg/max "
                 f"{min(c.token_count for c in children)}/{sum(c.token_count for c in children)//len(children)}/{max(c.token_count for c in children)}"
                 f" · section types {sorted({str(c.section_type) for c in children})}")
    L.append("")
    L.append("### 6. Qdrant")
    q = rb["qdrant"]
    L.append(f"- collection `{q.get('collection')}` · points for this document: {q.get('count', 0)} · indexer reported {cap.index_points}")
    L.append(f"- delete_document calls: {cap.delete_calls}")
    L.append("")
    L.append("### 7. MySQL")
    for name, rows in rb["mysql"].items():
        if rows is None:
            continue
        L.append(f"- `{name}`: {len(rows)} row(s)")
    L.append("")
    L.append("### 8. Knowledge stage")
    if cap.knowledge_report:
        r = cap.knowledge_report
        L.append(f"- status **{r['status']}** in {r['seconds']}s · knowledge_version `{r['knowledge_version']}`")
        L.append(f"- counts {r['counts']}")
        L.append(f"- projection {r['projection']}")
        for st in r["stages"]:
            L.append(f"  - stage `{st.get('stage')}`: {'skipped' if st.get('skipped') else 'ran'} · counts {st.get('counts')} · notes {st.get('notes')} · errors {st.get('errors')}")
    else:
        L.append("- no knowledge report (stage disabled, document not indexed, or no child chunks)")
    L.append("")
    L.append("### 9. Neo4j")
    n = rb["neo4j"]
    if n.get("reachable"):
        L.append(f"- Document node: {n.get('document_node')} · chunk stubs: {len(n.get('chunk_nodes', []))} · "
                 f"Claim nodes: {len(n.get('claims', []))} · current-state edges from this document's claims: {len(n.get('current_state_edges', []))}")
    else:
        L.append("- graph unreachable at readback")
    L.append("")
    L.append("## Checks")
    L.append("")
    fails = [c for c in checks if c.status == "fail"]
    L.append(f"**{sum(1 for c in checks if c.status == 'pass')} pass · {len(fails)} fail · "
             f"{sum(1 for c in checks if c.status == 'n/a')} n/a · {sum(1 for c in checks if c.status == 'info')} info**")
    L.append("")
    L.append(_table(
        [{"status": c.status.upper(), "category": c.category, "check": c.name, "detail": c.detail,
          "expected": _short(c.expected, 70), "actual": _short(c.actual, 70)} for c in checks],
        ["status", "category", "check", "detail", "expected", "actual"],
    ))
    return "\n".join(L) + "\n"


def run_report(ctx: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# End-to-end ingestion audit — 30 freshly fetched documents")
    L.append("")
    L.append(f"Run `{ctx['run_id']}` started {ctx['started_at']} finished {ctx['finished_at']} · "
             f"pipeline version `{ctx['pipeline_version']}` · results in `{ctx['run_dir']}`")
    L.append("")
    L.append("## How to read this")
    L.append("")
    L.append("Part 1 is generated from the run: one row per document, then a per-document trace with links to the "
             "evidence folder (`documents/NN_.../`). Every folder holds the raw source, the extraction, the canonical "
             "document, the date evidence, every chunk, every Qdrant point, every MySQL row, the knowledge report and "
             "the Neo4j subgraph for that document, plus `10_checks.json`. Part 2 is the assessment written from that evidence.")
    L.append("")
    L.append("## Isolation and assumptions")
    L.append("")
    for line in ctx["isolation_notes"]:
        L.append(f"- {line}")
    L.append("")
    L.append("## Part 1 — Run summary")
    L.append("")
    L.append("### Selection")
    L.append("")
    sel = ctx["selection"]
    L.append(f"- candidates sampled from the live JSON:API (newest first): {sel['candidates_seen']} across {len(sel['per_source_fetched'])} sources")
    L.append(f"- nodes chosen: {sel['nodes_chosen']} · attachments they carry: {sel['expected_attachments']} · documents expected: {sel['expected_documents']}")
    L.append(f"- documents actually yielded by change detection and handled: **{ctx['handled']}**")
    L.append(f"- bundles: {sel['bundles']}")
    L.append("")
    L.append("### Outcomes")
    L.append("")
    L.append(f"- pipeline tally: `{ctx['tally']}`")
    L.append(f"- wall clock for `ingest_drupal`: {ctx['ingest_seconds']}s")
    L.append(f"- stage timings (app.observability.metrics): see `timings.json`")
    L.append("")
    L.append("### Post-sweep stages (the same order `workers.tasks.sweep` uses)")
    L.append("")
    ps = ctx["post_sweep"]
    L.append(f"- knowledge catch-up: `{ps.get('knowledge_catch_up')}`")
    proj = ps.get("graph_projection") or {}
    L.append(f"- graph projection: version `{proj.get('projection_version')}` nodes `{proj.get('nodes')}` "
             f"relationships `{proj.get('relationships')}` skipped `{proj.get('skipped')}`")
    rec = ps.get("reconciliation") or {}
    L.append(f"- reconciliation: ok={rec.get('ok')} documents={rec.get('documents')} points={rec.get('points')}")
    if rec.get("checks"):
        L.append("")
        L.append(_table([{"check": c["check"], "count": c["count"], "ok": c["ok"], "skipped": c["skipped"],
                          "samples": ", ".join(c["samples"][:3]), "detail": _short(c["detail"], 110)} for c in rec["checks"]],
                        ["check", "count", "ok", "skipped", "samples", "detail"]))
    L.append("")
    L.append("### Stores after the run")
    L.append("")
    L.append(f"- Qdrant: `{ctx['qdrant_info']}`")
    L.append(f"- Neo4j: `{ctx['neo4j_stats']}`")
    L.append("- MySQL row counts:")
    L.append("")
    L.append(_table([{"table": k, "rows": v} for k, v in ctx["table_counts"].items()], ["table", "rows"]))
    L.append("")
    L.append("### Documents")
    L.append("")
    L.append(_table(ctx["doc_rows"], ["#", "type", "bundle", "outcome", "title", "date", "date_source",
                                      "parents", "children", "points", "claims", "proj", "fail", "folder"]))
    L.append("")
    L.append("### Check results across all documents")
    L.append("")
    L.append(_table(ctx["check_matrix"], ["category", "check", "pass", "fail", "n/a", "failing documents"]))
    L.append("")
    L.append("## Part 1 — Per-document trace")
    L.append("")
    for d in ctx["doc_traces"]:
        L.append(f"### {d['index']}. {d['folder']}")
        L.append("")
        for line in d["lines"]:
            L.append(f"- {line}")
        if d["fails"]:
            L.append("- **failed checks:**")
            for f in d["fails"]:
                L.append(f"  - `{f['name']}` — {f['detail']} (expected {_short(f['expected'], 60)}, actual {_short(f['actual'], 60)})")
        L.append("")
    return "\n".join(L) + "\n"
