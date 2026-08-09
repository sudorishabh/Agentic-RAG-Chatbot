"""Direct, out-of-band article ingest for the ``/ingest/article`` route.

Unlike the sweep this keeps no change-detection state: the document is chunked,
embedded and indexed immediately and is not tracked for later re-crawls.
"""
from __future__ import annotations

import logging
import uuid

from app.catalog import log as ingest_log
from app.core.models import CanonicalDocument
from app.ingestion.indexer import index_canonical

logger = logging.getLogger(__name__)


def ingest_article(
    *,
    title: str | None,
    body: str | None,
    url: str | None = None,
    uuid: str | None = None,
    bundle: str = "article",
) -> tuple[str, int]:
    from app.ingestion.canonical import from_drupal_export

    item = {
        "text": body or "",
        "title": title,
        "url": url,
        "uuid": uuid,
        "bundle": bundle,
    }
    doc = from_drupal_export(item)
    return _index(doc, label=url or title or doc.document_id)


def _log_doc(
    doc: CanonicalDocument,
    status: str,
    *,
    run_id: str | None = None,
    chunks: int | None = None,
    error: str | None = None,
) -> None:
    ingest_log.record(
        ingest_log.LogEntry(
            run_id=run_id,
            document_id=doc.document_id,
            source_type=doc.source_type,
            status=status,
            source_url=doc.source_url,
            bundle=(doc.extra or {}).get("bundle"),
            tags=", ".join(doc.tags) if doc.tags else None,
            title=doc.title,
            doc_version=doc.doc_version,
            chunks_indexed=chunks,
            content_hash=doc.content_hash or None,
            error_message=error,
        )
    )


def _index(doc: CanonicalDocument, *, label: str) -> tuple[str, int]:
    run_id = uuid.uuid4().hex
    try:
        ingest_log.ensure_table()
    except Exception:
        logger.exception("Could not ensure ingest_log table; events will be skipped.")

    try:
        points = index_canonical(doc)
    except Exception as exc:
        _log_doc(doc, "error", run_id=run_id, error=str(exc))
        raise

    _log_doc(doc, "indexed", run_id=run_id, chunks=points)
    logger.info("Ingested %s -> %s (%d points)", label, doc.document_id, points)
    return doc.document_id, points
