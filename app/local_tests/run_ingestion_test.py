"""Run ONLY the ingestion pipeline and report every stage per document:
change detection, extraction, canonical mapping, chunking, indexing, and
exactly what landed in MySQL.

Two sources:
  --source drupal   (default) crawl live Drupal nodes of one bundle plus the
                    PDFs attached to / linked from them (pdf_attachment docs)
  --source pdf      scan a local folder of PDF files

Isolated by default: all writes go to ``local_test_*`` MySQL tables and a
``local_test_documents`` Qdrant collection, never the real catalog. Documents
are processed through the pipeline's own per-document handler, so this test
exercises the real ingestion code path.

Usage:
    python -m app.local_tests.run_ingestion_test --bundle article --max-docs 3
    python -m app.local_tests.run_ingestion_test --source pdf --make-sample
    python -m app.local_tests.run_ingestion_test --cleanup

Run it twice to see change detection in action: the second run reports the
same documents as UNCHANGED straight from the MySQL state table.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import re
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from unittest import mock

# Only stdlib and these dependency-free local modules are imported at module
# level: the test-table env overrides must land before app settings are first
# built, so every app.* import happens after _apply_test_env() ran.
from app.local_tests import dump
from app.local_tests import reporting as rep
from app.local_tests import serialize

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


def _safe_name(document_id: str) -> str:
    """Filesystem-safe report filename stem (in-body PDF ids contain ':')."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", document_id)[:60]


# --------------------------------------------------------------------------- #
# Sample data (--source pdf --make-sample)
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

def _process(
    record: Any, run_id: str, *, skip_index: bool, session: Any = None
) -> DocCapture:
    """Run one change record through the real pipeline handler, capturing the
    extraction result, canonical document, chunks, and indexed point count."""
    from app.ingestion import pipeline
    from app.ingestion.chunking import chunk_canonical
    from app.ingestion.extractors import pdf_extractor

    cap = DocCapture(record=record)
    real_index = pipeline.index_chunks
    real_extract = pdf_extractor.extract_pdf

    def build_doc(rec: Any) -> Any:
        if rec.source_type == "pdf_attachment":
            cap.doc = pipeline._build_attachment_doc(rec, session)
        elif rec.source_type == "pdf":
            cap.doc = pipeline._build_pdf_doc(rec)
        else:
            cap.doc = pipeline._build_drupal_doc(rec)
        return cap.doc

    def observed_extract(content: bytes, filename: str) -> Any:
        cap.extraction = real_extract(content, filename)
        return cap.extraction

    def observed_chunk(doc: Any, **kwargs: Any) -> list[Any]:
        cap.chunks = chunk_canonical(doc, **kwargs)
        return cap.chunks

    def observed_index(chunks: Any, **kwargs: Any) -> int:
        cap.points = len(chunks) if skip_index else real_index(chunks, **kwargs)
        return cap.points

    patches = [
        # The PDF builders import extract_pdf from its module at call time,
        # so patching the module attribute captures the extraction result.
        mock.patch.object(pdf_extractor, "extract_pdf", observed_extract),
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
# Per-document verification
# --------------------------------------------------------------------------- #
# The full raw content of each stage is rendered by app.local_tests.dump; the
# function below only asserts that what MySQL stored matches the canonical doc.

def _verify(cap: DocCapture, snap: Any, checks: rep.Checks) -> None:
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
    checks.add("url stored", (row["url"] or None) == doc.source_url)
    checks.add("author facets match", set(snap.authors) == set(doc.authors))
    checks.add("theme facets match", set(snap.themes) == set(doc.categories))
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
        description="Exercise the ingestion pipeline against isolated test tables."
    )
    parser.add_argument(
        "--source", choices=["drupal", "pdf"], default="drupal",
        help="Ingest live Drupal nodes (+ attached PDFs) or a local PDF folder.",
    )
    parser.add_argument(
        "--bundle", default="article",
        help="Drupal node bundle to crawl (default: article).",
    )
    parser.add_argument(
        "--max-docs", type=int, default=5,
        help="Max nodes/PDF files to process (0 = no limit; attached PDFs "
        "ride along with their node and do not count). Default: 5.",
    )
    parser.add_argument(
        "--dir", default=str(Path(__file__).parent / "data"),
        help="[pdf] Folder of PDFs to ingest (default: app/local_tests/data).",
    )
    parser.add_argument(
        "--make-sample", action="store_true",
        help="[pdf] Generate a small sample PDF into the data dir first.",
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
        "--results-dir",
        help="Folder for the raw dumps (default: app/local_tests/results/run-<timestamp>).",
    )
    parser.add_argument(
        "--cleanup", action="store_true",
        help="Drop the local_test_* tables (and test collection) after the run.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show pipeline INFO logs.")
    return parser.parse_args(argv)


def _iter_records(args: argparse.Namespace) -> tuple[Iterator[Any], Any]:
    """Change-record stream for the chosen source, plus the shared HTTP
    session used for attachment downloads (None for the pdf source)."""
    from app.config import get_settings
    from app.ingestion import change_detection as cd

    if args.source == "pdf":
        data_dir = Path(args.dir).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        if args.make_sample:
            rep.emit(f"Sample PDF written: {make_sample_pdf(data_dir)}")
        return cd.detect_file_changes([data_dir], []), None

    from app.ingestion.extractors.drupal_extractor import _build_session

    session = _build_session(get_settings().drupal_max_retries)
    return cd.detect_drupal_changes([args.bundle]), session


def _preflight_index(settings: Any) -> str | None:
    """Verify the vector store + embeddings are usable before processing docs.

    Runs the same ``ensure_collection()`` the indexer calls first, so real
    indexing failures surface once, up front, instead of as a traceback per
    document. Returns an error message when unavailable, else None.
    """
    try:
        from app.core.clients import ensure_collection

        ensure_collection()
        return None
    except Exception as exc:  # connection refused, missing creds, ...
        return f"{type(exc).__name__}: {exc}"


def _cleanup(skip_index: bool) -> None:
    from app.config import get_settings
    from app.local_tests import db_checks

    rep.section("Cleanup")
    for name in db_checks.drop_test_tables():
        rep.kv("dropped table", name)
    if not skip_index:
        from app.core.clients import get_qdrant_client

        collection = get_settings().qdrant_collection
        client = get_qdrant_client()
        if client.collection_exists(collection):
            client.delete_collection(collection)
            rep.kv("dropped collection", collection)


def _write_summary(
    run_dir: Path,
    args: argparse.Namespace,
    settings: Any,
    run_id: str,
    started: datetime,
    documents: list[dict[str, Any]],
    tally: Counter,
    table_counts: dict[str, int],
    checks: rep.Checks,
    exit_code: int,
) -> Path:
    summary = {
        "run_id": run_id,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "source": args.source,
        "bundle": args.bundle if args.source == "drupal" else None,
        "pdf_dir": str(Path(args.dir).resolve()) if args.source == "pdf" else None,
        "max_docs": args.max_docs,
        "skip_index": args.skip_index,
        "extraction_mode": settings.extraction_mode,
        "mysql_state_table": settings.ingest_state_table,
        "mysql_log_table": settings.ingest_log_table,
        "qdrant_collection": settings.qdrant_collection,
        "outcomes": dict(tally),
        "mysql_table_counts": table_counts,
        "checks_total": checks.total,
        "checks_failed": checks.failed,
        "exit_code": exit_code,
        "documents": documents,
    }
    path = run_dir / "summary.json"
    path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return path


def _run(args: argparse.Namespace, run_dir: Path, started: datetime) -> int:
    from app.catalog import log as ingest_log
    from app.catalog import state
    from app.config import get_settings
    from app.local_tests import db_checks

    get_settings.cache_clear()
    settings = get_settings()

    rep.header("INGESTION LOCAL TEST")
    rep.kv("source", args.source)
    if args.source == "drupal":
        rep.kv("bundle", args.bundle)
        rep.kv("jsonapi base", settings.drupal_jsonapi_base)
    else:
        rep.kv("PDF source dir", Path(args.dir).resolve())
    rep.kv("max docs", args.max_docs or "no limit")
    rep.kv("results dir", run_dir)
    rep.kv("MySQL state table", settings.ingest_state_table)
    rep.kv("MySQL log table", settings.ingest_log_table)
    rep.kv("Qdrant collection", settings.qdrant_collection)
    rep.kv("extraction mode", settings.extraction_mode)
    rep.kv("indexing", "stubbed (--skip-index)" if args.skip_index else "real")

    state.ensure_table()
    ingest_log.ensure_table()

    if not args.skip_index:
        error = _preflight_index(settings)
        if error:
            rep.section("Preflight FAILED")
            rep.emit(f"  Real indexing is enabled but the vector store / embeddings")
            rep.emit(f"  are unavailable (Qdrant at {settings.qdrant_url}):")
            rep.emit(f"    {error}")
            rep.emit("")
            rep.emit("  Fix one of:")
            rep.emit("   - start Qdrant + set Azure embedding credentials, or")
            rep.emit("   - re-run with --skip-index: extraction, canonical mapping,")
            rep.emit("     chunking and MySQL writes all still run and are dumped in")
            rep.emit("     full; only the embedding + Qdrant upsert is skipped.")
            return 3

    records, session = _iter_records(args)
    run_id = uuid.uuid4().hex
    checks = rep.Checks()
    tally: Counter = Counter()
    documents: list[dict[str, Any]] = []
    primary_done = 0  # nodes / local PDF files processed (attachments excluded)

    rep.section("Processing (full raw dump written per document)")
    try:
        for record in records:
            is_attachment = record.source_type == "pdf_attachment"
            if args.max_docs and primary_done >= args.max_docs and not is_attachment:
                break
            cap = _process(record, run_id, skip_index=args.skip_index, session=session)
            if not is_attachment:
                primary_done += 1
            tally[cap.outcome] += 1

            snap = db_checks.fetch_snapshot(record.document_id)
            data = serialize.capture_to_dict(cap, snap)

            stem = f"{len(documents) + 1:02d}_{_safe_name(record.document_id)}"
            raw_file = Path("raw") / f"{stem}.json"
            txt_file = Path("docs") / f"{stem}.txt"
            (run_dir / "raw").mkdir(parents=True, exist_ok=True)
            (run_dir / raw_file).write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )

            print(
                f"  [{len(documents) + 1}] {record.source_type:15} "
                f"{cap.outcome.upper():9} chunks={len(cap.chunks):<4} {record.document_id}"
            )
            checks_before = len(checks.results)
            # The full dump goes to files only (it is large); the console shows
            # the one-line progress above and the run summary at the end.
            with rep.sink(run_dir / txt_file), rep.quiet_console():
                dump.render(data)
                _verify(cap, snap, checks)
            documents.append(
                {
                    "document_id": record.document_id,
                    "source_type": record.source_type,
                    "status": record.status.value,
                    "outcome": cap.outcome,
                    "error": cap.error,
                    "title": cap.doc.title if cap.doc else None,
                    "doc_version": cap.doc.doc_version if cap.doc else None,
                    "chunks": len(cap.chunks),
                    "points": cap.points,
                    "raw_file": raw_file.as_posix(),
                    "text_file": txt_file.as_posix(),
                    "checks": checks.results[checks_before:],
                }
            )
    finally:
        records.close()
        if session is not None:
            session.close()

    if not documents:
        rep.emit("\nNo documents detected. Check the source configuration above.")
        return 2

    rep.header("RUN SUMMARY")
    rep.kv("documents processed", len(documents))
    rep.kv("outcomes", dict(tally))
    rep.section("Documents")
    rep.table(
        [
            {
                "document_id": d["document_id"],
                "type": d["source_type"],
                "status": d["status"],
                "outcome": d["outcome"],
                "chunks": d["chunks"] or None,
                "checks": "FAIL" if any(not c["ok"] for c in d["checks"]) else "ok",
                "title": d["title"],
            }
            for d in documents
        ],
        ["document_id", "type", "status", "outcome", "chunks", "checks", "title"],
    )
    rep.section("MySQL table row counts")
    table_counts = db_checks.table_counts()
    for name, count in table_counts.items():
        rep.kv(name, "missing" if count < 0 else count)

    exit_code = 0 if checks.failed == 0 and tally["error"] == 0 else 1
    rep.section("Result")
    rep.emit(f"  {checks.summary()}")
    summary_path = _write_summary(
        run_dir, args, settings, run_id, started, documents,
        tally, table_counts, checks, exit_code,
    )
    rep.kv("summary json", summary_path)

    if args.cleanup:
        _cleanup(args.skip_index)

    return exit_code


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _apply_test_env(args.extraction_mode)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    with contextlib.suppress(AttributeError, ValueError):
        sys.stdout.reconfigure(encoding="utf-8")

    started = datetime.now()
    run_dir = (
        Path(args.results_dir)
        if args.results_dir
        else Path(__file__).parent / "results" / f"run-{started:%Y%m%d-%H%M%S}"
    ).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    # all_documents.txt is the full raw dump of every document concatenated;
    # per-document copies live in docs/*.txt and raw/*.json.
    with rep.sink(run_dir / "all_documents.txt"):
        code = _run(args, run_dir, started)
    print(f"\nRaw results written to: {run_dir}")
    print("  all_documents.txt   full raw dump, every document")
    print("  docs/NN_<id>.txt    per-document readable raw dump")
    print("  raw/NN_<id>.json    per-document raw data (machine-readable)")
    print("  summary.json        run config + per-document outcomes and checks")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
