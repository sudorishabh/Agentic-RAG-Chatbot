"""Incremental ingest runner — turn change verdicts into Qdrant + manifest writes.

This is the glue that wires the pieces together (§3 of the pipeline): for each
:class:`~app.ingestion.change_detection.ChangeRecord` it,

* **DELETED**   → purge the document's points from Qdrant and drop its manifest row.
* **UNCHANGED** → do nothing (the fingerprint already matched pre-extraction).
* **NEW/CHANGED** → extract → normalize → tier-2 content-hash check. If the content
  is genuinely new, purge any prior version's points, (re)index, and bump the
  manifest version. If only the fingerprint moved (same content), just refresh the
  fingerprint — no embedding spend.

Both sources (local PDFs, Drupal JSON:API) share one handler; only the
"normalize to a :class:`CanonicalDocument`" step differs.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Callable, Iterable, Iterator

from app.core.models import CanonicalDocument
from app.ingestion import change_detection as cd
from app.ingestion import state
from app.ingestion.change_detection import ChangeRecord, ChangeStatus
from app.ingestion.indexer import index_canonical
from app.ingestion.state import StateRecord
from app.services.vector_store import delete_document

logger = logging.getLogger(__name__)

# A builder normalizes a NEW/CHANGED record's payload into a CanonicalDocument.
DocBuilder = Callable[[ChangeRecord], "CanonicalDocument | None"]


def _save_state(record: ChangeRecord, content_hash: str, version: int, *, indexed: bool) -> None:
    state.upsert(
        StateRecord(
            document_id=record.document_id,
            source_type=record.source_type,
            source_key=record.source_key,
            fingerprint=record.fingerprint,
            content_hash=content_hash,
            doc_version=version,
            bundle=record.bundle,
            changed_mark=record.changed_mark,
        ),
        mark_indexed=indexed,
    )


def _handle(record: ChangeRecord, build_doc: DocBuilder) -> str:
    """Apply one change record. Returns a short outcome label for tallying."""
    if record.status is ChangeStatus.DELETED:
        delete_document(record.document_id)
        state.delete([record.document_id])
        logger.info("Deleted %s (%s)", record.document_id, record.source_key)
        return "deleted"

    if record.status is ChangeStatus.UNCHANGED:
        return "unchanged"

    doc = build_doc(record)
    if doc is None:
        return "skipped"

    content_hash = doc.ensure_content_hash()
    if not cd.content_changed(record, content_hash):
        # Fingerprint moved but the content is identical (re-saved file, metadata-
        # only touch): refresh the fingerprint, keep the version, skip re-embedding.
        prior_version = record.prior.doc_version if record.prior else 1
        _save_state(record, content_hash, prior_version, indexed=False)
        logger.info("Unchanged content for %s; fingerprint refreshed.", record.document_id)
        return "unchanged_content"

    version = cd.next_version(record)
    doc.doc_version = version
    delete_document(record.document_id)  # purge any prior version's points (no-op if new)
    index_canonical(doc)
    _save_state(record, content_hash, version, indexed=True)
    logger.info(
        "%s %s -> v%d", record.status.value, record.document_id, version
    )
    return "indexed"


def _run(records: Iterator[ChangeRecord], build_doc: DocBuilder) -> Counter:
    """Drive a stream of change records through ``_handle``, isolating failures so
    one bad document never sinks the whole run."""
    state.ensure_table()
    tally: Counter = Counter()
    for record in records:
        try:
            tally[_handle(record, build_doc)] += 1
        except Exception:
            logger.exception("Failed handling %s; skipping.", record.document_id)
            tally["error"] += 1
    return tally


# --------------------------------------------------------------------------- #
# Source-specific normalizers
# --------------------------------------------------------------------------- #
def _build_pdf_doc(record: ChangeRecord) -> CanonicalDocument | None:
    from app.ingestion.canonical import from_pdf
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    result = extract_pdf(record.payload, record.filename or record.document_id)
    return from_pdf(result, document_id=record.document_id, pdf_path=record.source_key)


def _build_drupal_doc(record: ChangeRecord) -> CanonicalDocument | None:
    from app.ingestion.canonical import from_drupal_record

    return from_drupal_record(record.payload)


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #
def ingest_pdfs(roots=None, ignore_globs=None) -> Counter:
    """Detect and ingest changes across the configured PDF source dirs."""
    return _run(cd.detect_file_changes(roots, ignore_globs), _build_pdf_doc)


def ingest_drupal(
    bundles: Iterable[str] | None = None,
    *,
    published_only: bool = True,
    reconcile_deletes: bool = False,
) -> Counter:
    """Detect and ingest changes from the Drupal JSON:API (incrementally)."""
    records = cd.detect_drupal_changes(
        bundles, published_only=published_only, reconcile_deletes=reconcile_deletes
    )
    return _run(records, _build_drupal_doc)


# --------------------------------------------------------------------------- #
# CLI:
#   python -m app.ingestion.pipeline --pdf
#   python -m app.ingestion.pipeline --pdf --dir "C:\docs" --dir "D:\more"
#   python -m app.ingestion.pipeline --drupal --bundle news --reconcile
# --------------------------------------------------------------------------- #
def _main(argv: list[str] | None = None) -> int:
    import argparse
    import sys
    from pathlib import Path

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Incremental ingest of PDFs / Drupal into Qdrant.")
    parser.add_argument("--pdf", action="store_true", help="Ingest changed PDFs from the source dirs.")
    parser.add_argument("--drupal", action="store_true", help="Ingest changed Drupal nodes (incremental).")
    parser.add_argument("--dir", action="append", default=[], help="Override PDF source dir(s).")
    parser.add_argument("--bundle", action="append", default=[], help="Limit Drupal crawl to bundle(s).")
    parser.add_argument("--reconcile", action="store_true", help="Also reconcile Drupal deletes/unpublishes.")
    parser.add_argument("--include-unpublished", action="store_true", help="Include unpublished Drupal nodes.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if not (args.pdf or args.drupal):
        parser.error("choose at least one of --pdf / --drupal")

    if args.pdf:
        roots = [Path(d) for d in args.dir] or None
        tally = ingest_pdfs(roots)
        print(f"PDFs: {dict(tally)}")

    if args.drupal:
        tally = ingest_drupal(
            args.bundle or None,
            published_only=not args.include_unpublished,
            reconcile_deletes=args.reconcile,
        )
        print(f"Drupal: {dict(tally)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
