from __future__ import annotations

import logging
import uuid
from collections import Counter
from typing import Callable, Iterable, Iterator

from app.core.models import CanonicalDocument
from app.ingestion import change_detection as cd
from app.ingestion import ingest_log
from app.ingestion import state
from app.ingestion.change_detection import ChangeRecord, ChangeStatus
from app.ingestion.indexer import index_canonical
from app.ingestion.state import StateRecord
from app.deps import delete_document

logger = logging.getLogger(__name__)

DocBuilder = Callable[[ChangeRecord], "CanonicalDocument | None"]


def _save_state(
    record: ChangeRecord,
    doc: CanonicalDocument,
    content_hash: str,
    version: int,
    *,
    indexed: bool,
) -> None:
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
            size=record.size,
            mtime_ns=record.mtime_ns,
            published_at=doc.published_at,
            authors=list(doc.authors),
            categories=list(doc.categories),
        ),
        mark_indexed=indexed,
    )


def _log(
    run_id: str | None,
    record: ChangeRecord,
    status: str,
    *,
    doc: CanonicalDocument | None = None,
    version: int | None = None,
    chunks: int | None = None,
    error: str | None = None,
) -> None:
    is_pdf = record.source_type == "pdf"
    prior_hash = record.prior.content_hash if record.prior else None
    ingest_log.record(
        ingest_log.LogEntry(
            run_id=run_id,
            document_id=record.document_id,
            source_type=record.source_type,
            status=status,
            source_path=record.source_key if is_pdf else None,
            source_url=None if is_pdf else record.source_key,
            bundle=record.bundle,
            tags=", ".join(doc.tags) if doc and doc.tags else None,
            title=doc.title if doc else None,
            doc_version=version,
            chunks_indexed=chunks,
            fingerprint=record.fingerprint or None,
            content_hash=(doc.content_hash if doc else prior_hash) or None,
            error_message=error,
        )
    )


def _handle(record: ChangeRecord, build_doc: DocBuilder, run_id: str | None = None) -> str:
    prior_version = record.prior.doc_version if record.prior else None

    if record.status is ChangeStatus.DELETED:
        delete_document(record.document_id)
        state.delete([record.document_id])
        logger.info("Deleted %s (%s)", record.document_id, record.source_key)
        _log(run_id, record, "deleted", version=prior_version)
        return "deleted"

    if record.status is ChangeStatus.UNCHANGED:
        # A touched-but-identical file re-hashes to UNCHANGED with a new size/mtime;
        # refresh the stored stat so the next scan skips it via the pre-filter.
        if record.size is not None and record.prior is not None and (
            record.prior.size != record.size or record.prior.mtime_ns != record.mtime_ns
        ):
            state.update_stat(record.document_id, record.size, record.mtime_ns)
        _log(run_id, record, "unchanged", version=prior_version)
        return "unchanged"

    logger.info(
        "Ingesting %s %s (%s)", record.source_type, record.document_id, record.source_key
    )
    doc = build_doc(record)
    if doc is None:
        _log(run_id, record, "skipped")
        return "skipped"

    content_hash = doc.ensure_content_hash()
    if not cd.content_changed(record, content_hash):
        version = prior_version or 1
        _save_state(record, doc, content_hash, version, indexed=False)
        logger.info("Unchanged content for %s; fingerprint refreshed.", record.document_id)
        _log(run_id, record, "unchanged_content", doc=doc, version=version)
        return "unchanged_content"

    version = cd.next_version(record)
    doc.doc_version = version
    delete_document(record.document_id)
    chunks = index_canonical(doc)
    _save_state(record, doc, content_hash, version, indexed=True)
    logger.info(
        "%s %s -> v%d", record.status.value, record.document_id, version
    )
    _log(run_id, record, "indexed", doc=doc, version=version, chunks=chunks)
    return "indexed"


def _run(records: Iterator[ChangeRecord], build_doc: DocBuilder) -> Counter:
    state.ensure_table()
    try:
        ingest_log.ensure_table()
    except Exception:
        logger.exception("Could not ensure ingest_log table; events will be skipped.")
    run_id = uuid.uuid4().hex
    tally: Counter = Counter()
    for record in records:
        try:
            tally[_handle(record, build_doc, run_id)] += 1
        except Exception as exc:
            logger.exception("Failed handling %s; skipping.", record.document_id)
            _log(run_id, record, "error", error=str(exc))
            tally["error"] += 1
    return tally


def _build_pdf_doc(record: ChangeRecord) -> CanonicalDocument | None:
    from app.ingestion.canonical import from_pdf
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    result = extract_pdf(record.payload, record.filename or record.document_id)
    return from_pdf(result, document_id=record.document_id, pdf_path=record.source_key)


def _build_drupal_doc(record: ChangeRecord) -> CanonicalDocument | None:
    from app.ingestion.canonical import from_drupal_record

    return from_drupal_record(record.payload)


def _build_drupal_or_attachment(record: ChangeRecord) -> CanonicalDocument | None:
    if record.source_type == "pdf_attachment":
        return _build_attachment_doc(record)
    return _build_drupal_doc(record)


def _build_attachment_doc(record: ChangeRecord) -> CanonicalDocument | None:
    """Download a node's attached PDF, extract it, and build a canonical PDF
    document linked back to the node. ``record.payload`` is a (DrupalRecord,
    DrupalFile) pair; ``source_type`` is 'pdf_attachment' so the local on-disk
    PDF pipeline's delete-reconcile never touches these web-sourced docs."""
    import requests

    from app.config import get_settings
    from app.ingestion.canonical import from_pdf
    from app.ingestion.extractors.drupal_extractor import _build_session
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    node, file = record.payload
    settings = get_settings()
    session = _build_session(settings.drupal_max_retries)
    try:
        response = session.get(file.url, timeout=settings.drupal_request_timeout)
        response.raise_for_status()
        content = response.content
    except requests.RequestException:
        logger.exception("Could not download attachment %s; skipping.", file.url)
        return None
    finally:
        session.close()
    if not content:
        logger.warning("Empty attachment body for %s; skipping.", file.url)
        return None

    result = extract_pdf(content, file.filename or record.document_id)
    return from_pdf(
        result,
        document_id=record.document_id,
        source_type="pdf_attachment",
        title=(file.description or node.title or file.filename or None),
        source_url=node.url,
        file_url=file.url,
        linked_article_uuid=(node.uuid or None),
        published_at=node.created,
        extra={"bundle": node.bundle},
    )


def ingest_pdfs(roots=None, ignore_globs=None) -> Counter:
    logger.info("PDF ingestion started (roots=%s)", roots or "configured PDF source")
    tally = _run(cd.detect_file_changes(roots, ignore_globs), _build_pdf_doc)
    logger.info("PDF ingestion finished: %s", dict(tally))
    return tally


def ingest_drupal(
    bundles: Iterable[str] | None = None,
    *,
    published_only: bool = True,
    reconcile_deletes: bool = False,
) -> Counter:
    logger.info("Drupal ingestion started (bundles=%s, reconcile=%s)", bundles or "default", reconcile_deletes)
    records = cd.detect_drupal_changes(
        bundles, published_only=published_only, reconcile_deletes=reconcile_deletes
    )
    tally = _run(records, _build_drupal_or_attachment)
    logger.info("Drupal ingestion finished: %s", dict(tally))
    return tally


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
