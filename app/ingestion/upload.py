from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from app.core.models import CanonicalDocument, CanonicalSection
from app.ingestion import ingest_log
from app.ingestion.indexer import index_canonical

logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return slug or "document"


def _pdf_document(filename: str, content: bytes) -> CanonicalDocument:
    from app.ingestion.canonical import from_pdf
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    result = extract_pdf(content, filename)
    return from_pdf(result, document_id=_slugify(Path(filename).stem), title=filename)


def _text_document(filename: str, content: bytes) -> CanonicalDocument:
    text = content.decode("utf-8", errors="ignore")
    doc = CanonicalDocument(
        document_id=_slugify(Path(filename).stem),
        source_type="pdf",
        title=filename,
        sections=[CanonicalSection(text=text, order=0)],
        pdf_path=filename,
    )
    doc.ensure_content_hash()
    return doc


def ingest_upload(filename: str, content: bytes) -> tuple[str, int]:
    if Path(filename).suffix.lower() == ".pdf":
        doc = _pdf_document(filename, content)
    else:
        doc = _text_document(filename, content)
    return _index(doc, label=filename)


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
    is_pdf = doc.source_type == "pdf"
    ingest_log.record(
        ingest_log.LogEntry(
            run_id=run_id,
            document_id=doc.document_id,
            source_type=doc.source_type,
            status=status,
            source_path=doc.pdf_path if is_pdf else None,
            source_url=None if is_pdf else doc.source_url,
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
