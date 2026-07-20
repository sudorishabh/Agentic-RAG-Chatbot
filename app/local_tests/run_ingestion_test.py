"""Run ONLY the ingestion pipeline against a local folder of PDFs and report
every stage per document: change detection, extraction, canonical mapping,
chunking, indexing, and exactly what landed in MySQL.

Isolated by default: all writes go to ``local_test_*`` MySQL tables and a
``local_test_documents`` Qdrant collection, never the real catalog. Documents
are processed through the pipeline's own per-document handler, so this test
exercises the real ingestion code path.

Usage:
    python -m app.local_tests.run_ingestion_test --make-sample --skip-index
    python -m app.local_tests.run_ingestion_test --dir path\\to\\pdfs
    python -m app.local_tests.run_ingestion_test --cleanup

Run it twice to see change detection in action: the second run reports every
document as UNCHANGED straight from the MySQL state table.
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest import mock

# Only stdlib and reporting (which has no app.* dependencies) are imported at
# module level: the test-table env overrides must land before app settings are
# first built, so every app import happens after _apply_test_env() ran.
from app.local_tests import reporting as rep

_PREFIX = "local_test"

_ENV_OVERRIDES = {
    "INGEST_STATE_TABLE": f"{_PREFIX}_ingest_state",
    "INGEST_LOG_TABLE": f"{_PREFIX}_ingest_log",
    "QDRANT_COLLECTION": f"{_PREFIX}_documents",
    # Log UNCHANGED rows too so a second run shows them in the report.
    "INGEST_LOG_UNCHANGED": "true",
}


def _apply_test_env(extraction_mode: str | None) -> None:
    os.environ.update(_ENV_OVERRIDES)
    if extraction_mode:
        os.environ["EXTRACTION_MODE"] = extraction_mode


@dataclass
class DocCapture:
    """Per-document artifacts captured while the pipeline handles one record."""

    record: Any
    extraction: Any | None = None
    doc: Any | None = None
    chunks: list[Any] = field(default_factory=list)
    points: int | None = None
    outcome: str = "error"
    error: str | None = None


# --------------------------------------------------------------------------- #
# Sample data
# --------------------------------------------------------------------------- #

_SAMPLE_PAGES = [
    (
        "Renewable Energy Adoption in India: A Sample Report\n\n"
        "1. Introduction\n\n"
        "The Energy and Resources Institute tracks the adoption of renewable "
        "energy across Indian states. This sample document exists only to "
        "exercise the local ingestion pipeline: extraction, canonical mapping, "
        "chunking, and catalog writes. Every sentence here is synthetic test "
        "content. The report is organised into short numbered sections so the "
        "chunker's heading detection has something realistic to work with.\n\n"
        "2. Solar Capacity Trends\n\n"
        "Installed solar capacity grew steadily between 2015 and 2025, driven "
        "by falling module prices and competitive auctions. Utility-scale "
        "parks contributed the bulk of new additions, while rooftop programs "
        "expanded more slowly in the residential segment. Several states "
        "introduced net metering reforms that improved payback periods for "
        "commercial consumers. Storage-paired tenders emerged as a mechanism "
        "to firm up daytime generation for evening demand."
    ),
    (
        "3. Grid Integration Challenges\n\n"
        "High renewable penetration introduces variability that the grid must "
        "absorb through flexible resources. Thermal plants increasingly "
        "operate in load-following mode, and interstate transmission corridors "
        "carry surplus generation to demand centres. Forecasting errors "
        "shrink as weather models improve, but ramping events around sunset "
        "remain the hardest interval to balance.\n\n"
        "4. Policy Recommendations\n\n"
        "First, align renewable purchase obligations with realistic state-level "
        "resource assessments. Second, expand time-of-day tariffs so demand "
        "shifts toward solar hours. Third, fund distribution-grid upgrades "
        "before rooftop targets are raised further.\n\n"
        "5. Conclusion\n\n"
        "The sample report ends here. If this text appears in your chunk "
        "payloads and MySQL rows, the ingestion pipeline carried it through "
        "every stage intact."
    ),
]


def make_sample_pdf(directory: Path) -> Path:
    """Write a small two-page PDF into the data dir using PyMuPDF."""
    import fitz

    path = directory / "sample_energy_report.pdf"
    doc = fitz.open()
    for text in _SAMPLE_PAGES:
        page = doc.new_page()
        rect = fitz.Rect(72, 72, page.rect.width - 72, page.rect.height - 72)
        page.insert_textbox(rect, text, fontsize=11)
    doc.save(str(path))
    doc.close()
    return path


# --------------------------------------------------------------------------- #
# Pipeline execution with stage capture
# --------------------------------------------------------------------------- #

def _process(record: Any, run_id: str, *, skip_index: bool) -> DocCapture:
    """Run one change record through the real pipeline handler, capturing the
    extraction result, canonical document, chunks, and indexed point count."""
    from app.ingestion import pipeline
    from app.ingestion.canonical import from_pdf
    from app.ingestion.chunker import chunk_canonical
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    cap = DocCapture(record=record)
    real_index = pipeline.index_chunks

    def build_doc(rec: Any) -> Any:
        # Mirrors pipeline._build_pdf_doc, keeping the extraction result too.
        cap.extraction = extract_pdf(rec.payload, rec.filename or rec.document_id)
        cap.doc = from_pdf(
            cap.extraction, document_id=rec.document_id, pdf_path=rec.source_key
        )
        return cap.doc

    def observed_chunk(doc: Any, **kwargs: Any) -> list[Any]:
        cap.chunks = chunk_canonical(doc, **kwargs)
        return cap.chunks

    def observed_index(chunks: Any, **kwargs: Any) -> int:
        cap.points = len(chunks) if skip_index else real_index(chunks, **kwargs)
        return cap.points

    patches = [
        mock.patch.object(pipeline, "chunk_canonical", observed_chunk),
        mock.patch.object(pipeline, "index_chunks", observed_index),
    ]
    if skip_index:
        patches.append(
            mock.patch.object(pipeline, "delete_document", lambda *a, **k: None)
        )

    try:
        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            cap.outcome = pipeline._handle(record, build_doc, run_id)
    except Exception as exc:  # mirror pipeline._run: one bad doc must not stop the run
        logging.getLogger(__name__).exception("Failed handling %s", record.document_id)
        cap.outcome, cap.error = "error", str(exc)
        pipeline._log(run_id, record, "error", error=str(exc))
    return cap


# --------------------------------------------------------------------------- #
# Per-document report
# --------------------------------------------------------------------------- #

def _report_stages(cap: DocCapture, show_chunks: int) -> None:
    rec = cap.record

    rep.section("Change detection")
    rep.kv("status", rec.status.value)
    rep.kv("file", rec.source_key)
    rep.kv("size (bytes)", rec.size)
    rep.kv("fingerprint (sha256)", rec.fingerprint)
    rep.kv("prior doc_version", rec.prior.doc_version if rec.prior else None)
    if cap.error:
        rep.kv("error", cap.error)

    if cap.extraction is not None:
        pages = cap.extraction.pages
        rep.section("Extraction")
        rep.kv("pages with text", len(pages))
        rep.kv("route per page", dict(Counter(p.extracted_via.value for p in pages)))
        rep.kv("tables detected", sum(len(p.tables) for p in pages))
        rep.kv("total characters", sum(len(p.text) for p in pages))
        if cap.extraction.metadata:
            rep.kv("pdf metadata", cap.extraction.metadata)
        if pages:
            rep.kv("first page preview", rep.snippet(pages[0].text))

    if cap.doc is not None:
        d = cap.doc
        rep.section("Canonical document")
        rep.kv("document_id", d.document_id)
        rep.kv("source_type", d.source_type)
        rep.kv("title", d.title)
        rep.kv("sections", len(d.sections))
        rep.kv("paginated", d.is_paginated)
        rep.kv("doc_version", d.doc_version)
        rep.kv("content_hash", d.content_hash)
        rep.kv("published_at", d.published_at)
        rep.kv("authors", d.authors)
        rep.kv("tags", d.tags)
        rep.kv("categories", d.categories)
        rep.kv("entity refs / file links", f"{len(d.entity_refs)} / {len(d.file_links)}")
        rep.kv("language / tenant / acl", f"{d.language} / {d.tenant_id} / {d.acl}")

    if cap.chunks:
        parents = [c for c in cap.chunks if c.is_parent]
        children = [c for c in cap.chunks if not c.is_parent]
        rep.section("Chunking")
        rep.kv("parents / children", f"{len(parents)} / {len(children)}")
        if children:
            tokens = [c.token_count for c in children]
            rep.kv(
                "child tokens",
                f"min={min(tokens)} max={max(tokens)} avg={sum(tokens) // len(tokens)}",
            )
        rep.table(
            [
                {
                    "kind": "parent" if c.is_parent else "child",
                    "idx": c.chunk_index,
                    "tokens": c.token_count,
                    "pages": c.page_range,
                    "section": c.section_heading,
                    "chunk_id": c.chunk_id[:13],
                }
                for c in cap.chunks[:show_chunks]
            ],
            ["kind", "idx", "tokens", "pages", "section", "chunk_id"],
        )
        if len(cap.chunks) > show_chunks:
            print(f"  ... and {len(cap.chunks) - show_chunks} more chunk(s)")
        if children:
            rep.section("Chunk payload (first child, as indexed)")
            for key, value in children[0].to_payload().items():
                rep.kv(key, rep.snippet(rep.fmt(value), 110), indent=4)

    rep.section("Indexing")
    if cap.points is None:
        rep.kv("qdrant points", "- (no indexing this outcome)")
    else:
        rep.kv("qdrant points", cap.points)


def _report_mysql(cap: DocCapture, snap: Any) -> None:
    rep.section("MySQL catalog (read back)")
    if snap.state_row is None:
        print("  (no state row)")
    else:
        for key in (
            "document_id", "source_type", "source_key", "bundle", "entity_type",
            "fingerprint", "content_hash", "doc_version", "size", "mtime_ns",
            "published_at", "title", "url", "indexed_at", "updated_at",
        ):
            rep.kv(key, snap.state_row.get(key))
        rep.kv("raw_meta", "present" if snap.state_row.get("raw_meta") else None)
    rep.kv("author facet rows", snap.authors)
    rep.kv("category facet rows", snap.categories)
    if snap.term_links:
        rep.table(snap.term_links, ["term_uuid", "role"])
    if snap.attachments:
        rep.table(snap.attachments, ["file_uuid", "origin", "filename", "url"])

    rep.section("Ingest log (this document, newest first)")
    rep.table(
        snap.log_rows[:5],
        ["status", "doc_version", "chunks_indexed", "run_id", "event_time", "error_message"],
    )


def _verify(cap: DocCapture, snap: Any, checks: Checks) -> None:
    rep.section("Checks")
    rec, doc, row = cap.record, cap.doc, snap.state_row

    if cap.outcome == "deleted":
        checks.add("state row removed", row is None)
        checks.add("'deleted' logged", any(r["status"] == "deleted" for r in snap.log_rows))
        return
    if cap.outcome == "error":
        checks.add("'error' logged", any(r["status"] == "error" for r in snap.log_rows))
        return
    if cap.outcome == "skipped":
        checks.add("'skipped' logged", any(r["status"] == "skipped" for r in snap.log_rows))
        return

    if not checks.add("state row stored", row is not None):
        return
    checks.add("fingerprint stored", row["fingerprint"] == rec.fingerprint)

    if cap.outcome == "unchanged":
        checks.add("'unchanged' logged", any(r["status"] == "unchanged" for r in snap.log_rows))
        return
    if doc is None:
        return

    checks.add("content_hash matches canonical", row["content_hash"] == doc.content_hash)
    checks.add("doc_version stored", row["doc_version"] == doc.doc_version)
    checks.add("title stored", (row["title"] or None) == doc.title)
    checks.add(
        "size/mtime stored", row["size"] == rec.size and row["mtime_ns"] == rec.mtime_ns
    )
    checks.add("author facets match", set(snap.authors) == set(doc.authors))
    checks.add("category facets match", set(snap.categories) == set(doc.categories))
    expected_terms = {r.uuid for r in doc.entity_refs if r.vocabulary}
    checks.add(
        "term links match", {t["term_uuid"] for t in snap.term_links} == expected_terms
    )
    expected_files = {f.uuid for f in doc.file_links}
    checks.add(
        "attachment links match",
        {a["file_uuid"] for a in snap.attachments} == expected_files,
    )

    if cap.outcome == "indexed":
        checks.add("indexed_at set", row["indexed_at"] is not None)
        log = next((r for r in snap.log_rows if r["status"] == "indexed"), None)
        if checks.add("'indexed' log row written", log is not None):
            checks.add("log chunk count matches", log["chunks_indexed"] == len(cap.chunks))


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exercise the PDF ingestion pipeline against isolated test tables."
    )
    parser.add_argument(
        "--dir", default=str(Path(__file__).parent / "data"),
        help="Folder of PDFs to ingest (default: app/local_tests/data).",
    )
    parser.add_argument(
        "--make-sample", action="store_true",
        help="Generate a small sample PDF into the data dir before running.",
    )
    parser.add_argument(
        "--skip-index", action="store_true",
        help="Stub embeddings + Qdrant; MySQL writes still happen for real.",
    )
    parser.add_argument(
        "--extraction-mode", choices=["hybrid", "local_only", "azure_only"],
        help="Override EXTRACTION_MODE for this run (local_only avoids Azure OCR).",
    )
    parser.add_argument(
        "--show-chunks", type=int, default=6, help="Chunks listed per document.",
    )
    parser.add_argument(
        "--cleanup", action="store_true",
        help="Drop the local_test_* tables (and test collection) after the run.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show pipeline INFO logs.")
    return parser.parse_args(argv)


def _cleanup(skip_index: bool) -> None:
    from app.config import get_settings
    from app.local_tests import db_checks

    rep.section("Cleanup")
    for name in db_checks.drop_test_tables():
        rep.kv("dropped table", name)
    if not skip_index:
        from app.deps import get_qdrant_client

        collection = get_settings().qdrant_collection
        client = get_qdrant_client()
        if client.collection_exists(collection):
            client.delete_collection(collection)
            rep.kv("dropped collection", collection)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _apply_test_env(args.extraction_mode)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    with contextlib.suppress(AttributeError, ValueError):
        sys.stdout.reconfigure(encoding="utf-8")

    # Safe to import app modules now that the env overrides are in place.
    from app.config import get_settings
    from app.ingestion import change_detection as cd
    from app.ingestion import ingest_log, state
    from app.local_tests import db_checks

    get_settings.cache_clear()
    settings = get_settings()

    data_dir = Path(args.dir).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    if args.make_sample:
        print(f"Sample PDF written: {make_sample_pdf(data_dir)}")

    rep.header("INGESTION LOCAL TEST")
    rep.kv("PDF source dir", data_dir)
    rep.kv("MySQL state table", settings.ingest_state_table)
    rep.kv("MySQL log table", settings.ingest_log_table)
    rep.kv("Qdrant collection", settings.qdrant_collection)
    rep.kv("extraction mode", settings.extraction_mode)
    rep.kv("indexing", "stubbed (--skip-index)" if args.skip_index else "real")

    state.ensure_table()
    ingest_log.ensure_table()

    records = list(cd.detect_file_changes([data_dir], []))
    if not records:
        print(f"\nNo PDFs found in {data_dir}. Add PDFs or pass --make-sample.")
        return 2

    rep.section("Change detection overview")
    rep.table(
        [
            {
                "document_id": r.document_id,
                "status": r.status.value,
                "size": r.size,
                "file": Path(r.source_key).name,
            }
            for r in records
        ],
        ["document_id", "status", "size", "file"],
    )

    run_id = uuid.uuid4().hex
    checks = Checks()
    tally: Counter = Counter()

    for record in records:
        cap = _process(record, run_id, skip_index=args.skip_index)
        tally[cap.outcome] += 1
        rep.header(f"{record.document_id}  ->  {cap.outcome.upper()}")
        _report_stages(cap, args.show_chunks)
        snap = db_checks.fetch_snapshot(record.document_id)
        _report_mysql(cap, snap)
        _verify(cap, snap, checks)

    rep.header("RUN SUMMARY")
    rep.kv("documents", len(records))
    rep.kv("outcomes", dict(tally))
    rep.section("MySQL table row counts")
    for name, count in db_checks.table_counts().items():
        rep.kv(name, "missing" if count < 0 else count)
    rep.section("Result")
    print(f"  {checks.summary()}")

    if args.cleanup:
        _cleanup(args.skip_index)

    return 0 if checks.failed == 0 and tally["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
