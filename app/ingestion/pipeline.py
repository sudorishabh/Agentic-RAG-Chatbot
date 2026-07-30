from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from typing import Callable, Iterable, Iterator

from app.catalog import enrichment
from app.catalog import state
from app.catalog import log as ingest_log
from app.catalog.models import AttachmentLink, StateRecord
from app.config import get_settings
from app.core.models import CanonicalDocument
from app.ingestion import change_detection as cd
from app.ingestion.change_detection import ChangeRecord, ChangeStatus
from app.ingestion.chunking import chunk_canonical
from app.ingestion.enrich import abstract_version, generate_abstract
from app.ingestion.indexer import index_chunks
from app.core.clients import delete_document, refresh_document_title
from app.observability.tracing import span

logger = logging.getLogger(__name__)

DocBuilder = Callable[[ChangeRecord], "CanonicalDocument | None"]

# One corpus-wide ingestion run (sweep / PDF scan / Drupal crawl) at a time.
# Concurrent runs double-embed documents and race each other's delete/upsert
# and documents-table writes. Process-local by design: the ingestion server is a
# single private instance (celery mode serializes via its queue instead).
_run_lock = threading.Lock()


class IngestBusyError(RuntimeError):
    """Another ingestion run is already in progress in this process."""


@contextmanager
def _exclusive(what: str) -> Iterator[None]:
    if not _run_lock.acquire(blocking=False):
        raise IngestBusyError(f"Another ingestion run is in progress; {what} rejected.")
    try:
        yield
    finally:
        _run_lock.release()


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
            entity_type=record.entity_type,
            changed_mark=record.changed_mark,
            size=record.size,
            mtime_ns=record.mtime_ns,
            published_at=doc.published_at,
            title=doc.title,
            url=doc.source_url,
            authors=list(doc.authors),
            categories=list(doc.categories),
            tags=list(doc.tags),
            attachments=[
                AttachmentLink(
                    file_uuid=f.uuid, origin=f.origin, url=f.url, filename=f.filename
                )
                for f in doc.file_links
            ],
            raw_meta=doc.raw_meta or None,
        ),
        mark_indexed=indexed,
    )


def _persist(
    record: ChangeRecord,
    doc: CanonicalDocument,
    content_hash: str,
    version: int,
    *,
    indexed: bool,
) -> None:
    """Persist the content record and the facet rows derived from it.

    The document row is the primary fact — and the FK target every facet row
    hangs off — so it is written first, with its theme/author/tag/attachment rows
    following inside the same transaction.
    """
    _save_state(record, doc, content_hash, version, indexed=indexed)


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


def _enrich_once(doc: CanonicalDocument, content_hash: str, max_attempts: int) -> str:
    version = abstract_version()
    cached = enrichment.get(content_hash, version=version)
    if cached is not None and cached.abstract:
        return "hit"
    if cached is not None and cached.attempts >= max_attempts:
        return "exhausted"

    try:
        abstract = generate_abstract(doc)
    except Exception as exc:
        # A model failure is worth remembering: without a counter, a document
        # that always fails is retried at full cost on every sweep forever.
        logger.warning("Abstract generation failed for %s.", doc.document_id, exc_info=True)
        enrichment.record_failure(content_hash, version=version, error=str(exc))
        return "failed"

    if abstract is None:
        return "skipped"  # too short to be worth summarizing; never retried
    enrichment.put(content_hash, version=version, abstract=abstract)
    return "stored"


def _enrich(doc: CanonicalDocument, content_hash: str) -> str:
    """Ensure this content has a cached abstract; report what happened.

    Fails open in every direction, like the rest of the pipeline's external
    dependencies: a rate-limited deployment or an unreachable catalog leaves the
    document without an abstract rather than stopping the sweep.
    """
    settings = get_settings()
    if not settings.enrichment_enabled:
        return "off"
    try:
        return _enrich_once(doc, content_hash, settings.enrichment_max_attempts)
    except Exception:
        logger.warning(
            "Enrichment could not run for %s; continuing without an abstract.",
            doc.document_id, exc_info=True,
        )
        return "error"


def _handle(
    record: ChangeRecord,
    build_doc: DocBuilder,
    run_id: str | None = None,
    note: Callable[[str], None] | None = None,
) -> str:
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
        if get_settings().ingest_log_unchanged:
            _log(run_id, record, "unchanged", version=prior_version)
        return "unchanged"

    logger.info(
        "Ingesting %s %s (%s)", record.source_type, record.document_id, record.source_key
    )
    with span("ingest.extract", source_type=record.source_type):
        doc = build_doc(record)
    if doc is None:
        _log(run_id, record, "skipped")
        return "skipped"

    content_hash = doc.ensure_content_hash()
    # Before the content-changed branch, so an unchanged-content document that
    # predates enrichment still picks up an abstract as it is re-crawled. The
    # cache is keyed by this hash, so a hit costs one indexed lookup.
    enriched = _enrich(doc, content_hash)
    if note is not None:
        note(enriched)

    if not cd.content_changed(record, content_hash):
        version = prior_version or 1
        _persist(record, doc, content_hash, version, indexed=False)
        # The hash covers body text only, so a title-only edit lands here rather
        # than re-indexing. The catalog took the new title above; carry it to the
        # chunk payloads too (one call, no re-embed) so citations don't display
        # the old one until the body happens to change.
        if record.prior is not None and record.prior.title != doc.title:
            refresh_document_title(record.document_id, doc.title)
        logger.info("Unchanged content for %s; fingerprint refreshed.", record.document_id)
        _log(run_id, record, "unchanged_content", doc=doc, version=version)
        return "unchanged_content"

    version = cd.next_version(record)
    doc.doc_version = version
    # Index the new version FIRST, then delete everything else for the doc.
    # Chunk ids are version-scoped (uuid5 of doc|version|suffix), so the new
    # points never collide with the old ones: the old version stays searchable
    # until the swap, and a mid-index failure leaves it fully intact.
    with span("ingest.chunk"):
        new_chunks = chunk_canonical(doc)
    chunks = index_chunks(new_chunks)
    delete_document(record.document_id, keep_ids=[c.chunk_id for c in new_chunks])
    _persist(record, doc, content_hash, version, indexed=True)
    logger.info(
        "%s %s -> v%d", record.status.value, record.document_id, version
    )
    _log(run_id, record, "indexed", doc=doc, version=version, chunks=chunks)
    return "indexed"


# Outcomes that consumed real work (downloads, extraction, embedding). Only
# these count against the batch budget — unchanged scans are free and must
# never exhaust it, or a caught-up capped run would stall before reaching the
# documents that actually changed.
_WORKED_OUTCOMES = frozenset({"indexed", "deleted", "skipped", "error"})


def _run(records: Iterator[ChangeRecord], build_doc: DocBuilder) -> Counter:
    state.ensure_table()
    try:
        ingest_log.ensure_table()
    except Exception:
        logger.exception("Could not ensure ingest_log table; events will be skipped.")
    settings = get_settings()
    if settings.enrichment_enabled:
        try:
            enrichment.ensure_table()
        except Exception:
            logger.exception(
                "Could not ensure the enrichment table; abstracts will be skipped."
            )
    max_docs = settings.ingest_max_docs_per_run
    batch_size = settings.ingest_batch_size
    pause = settings.ingest_batch_pause_seconds
    workers = max(1, settings.ingest_workers)

    run_id = uuid.uuid4().hex
    tally: Counter = Counter()
    worked = 0

    # `note` is called from worker threads, unlike account() which the main
    # loop owns, so the shared Counter needs a lock here.
    tally_lock = threading.Lock()

    def note(outcome: str) -> None:
        """Record an enrichment outcome. Hit rate has to be visible: this
        cache's failure mode is silently re-paying for every document."""
        if outcome == "off":
            return
        with tally_lock:
            tally[f"enrich_{outcome}"] += 1

    def handle(record: ChangeRecord) -> str:
        try:
            return _handle(record, build_doc, run_id, note=note)
        except Exception as exc:
            logger.exception("Failed handling %s; skipping.", record.document_id)
            _log(run_id, record, "error", error=str(exc))
            return "error"

    def account(outcome: str) -> None:
        nonlocal worked
        tally[outcome] += 1
        if outcome in _WORKED_OUTCOMES:
            worked += 1
            if pause > 0 and batch_size > 0 and worked % batch_size == 0:
                time.sleep(pause)

    def budget_reached(record: ChangeRecord, pending: int) -> bool:
        # Stop only at a document boundary: a node's attachment records follow
        # it immediately and must land in the same run, or the node's state
        # row would hide them from the next crawl. In-flight documents count
        # pessimistically so the cap can never overshoot.
        if not max_docs or record.source_type == "pdf_attachment":
            return False
        if worked + pending < max_docs:
            return False
        logger.info(
            "Batch budget of %d documents reached; stopping cleanly "
            "(the next run resumes from the high-water mark).", max_docs,
        )
        tally["budget_stop"] = 1
        return True

    if workers == 1:
        for record in records:
            if budget_reached(record, pending=0):
                break
            account(handle(record))
        return tally

    # Parallel mode: the crawler stays single-threaded (per-run dedup and
    # node-before-attachment ordering live there); a bounded pool works the
    # heavy per-document I/O (download, extract, embed, index). Documents are
    # independent across MySQL (pooled connections, per-doc transactions) and
    # Qdrant (per-doc points); the one-run-at-a-time lock still applies.
    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

    from app.core.clients import ensure_collection

    try:
        # Pre-create the collection and payload indexes once, so first-run
        # workers don't race the create call.
        ensure_collection()
    except Exception:
        logger.exception("Could not pre-create the collection; workers will retry.")

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ingest") as pool:
        in_flight: set = set()
        for record in records:
            done = {f for f in in_flight if f.done()}
            in_flight -= done
            for future in done:
                account(future.result())
            if budget_reached(record, pending=len(in_flight)):
                break
            while len(in_flight) >= workers * 2:
                finished, in_flight = wait(in_flight, return_when=FIRST_COMPLETED)
                for future in finished:
                    account(future.result())
            in_flight.add(pool.submit(handle, record))
        if in_flight:
            finished, _ = wait(in_flight)
            for future in finished:
                account(future.result())
    return tally


def _build_pdf_doc(record: ChangeRecord) -> CanonicalDocument | None:
    from app.ingestion.canonical import from_pdf
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    result = extract_pdf(record.payload, record.filename or record.document_id)
    return from_pdf(result, document_id=record.document_id, pdf_path=record.source_key)


def _build_drupal_doc(record: ChangeRecord) -> CanonicalDocument | None:
    from app.ingestion.canonical import from_drupal_record

    return from_drupal_record(record.payload)


def _build_drupal_or_attachment(
    record: ChangeRecord, session: "requests.Session"
) -> CanonicalDocument | None:
    if record.source_type == "pdf_attachment":
        from app.ingestion.extractors.attachment import build_attachment_doc

        return build_attachment_doc(record, session)
    return _build_drupal_doc(record)


def ingest_pdfs(roots=None, ignore_globs=None) -> Counter:
    with _exclusive("PDF ingestion"):
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
    from functools import partial

    from app.ingestion.extractors.drupal_extractor import _build_session

    with _exclusive("Drupal ingestion"):
        logger.info("Drupal ingestion started (bundles=%s, reconcile=%s)", bundles or "default", reconcile_deletes)
        records = cd.detect_drupal_changes(
            bundles, published_only=published_only, reconcile_deletes=reconcile_deletes
        )
        # One session for the whole run: attachment downloads reuse its connection
        # pool rather than opening a new one per PDF.
        session = _build_session(get_settings().drupal_max_retries)
        try:
            tally = _run(records, partial(_build_drupal_or_attachment, session=session))
        finally:
            session.close()
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
