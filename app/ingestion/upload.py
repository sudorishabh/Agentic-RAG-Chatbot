"""Ad-hoc ingestion of an uploaded file (the ``POST /ingest`` path).

The folder-scan / Drupal crawl paths (:mod:`app.ingestion.pipeline`) are the
bulk, change-detected sources. This module handles the one-off case: a user
uploads a single file through the API and wants it embedded *now*. It funnels
through the same canonical → chunk → index pipeline (so the chunking, payload,
and idempotent point ids are identical to a crawl), just without the manifest /
change-detection bookkeeping.

PDFs go through the real extractor (Docling + OCR + figure captioning); other
files are treated as a single plain-text document.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from app.core.models import CanonicalDocument, CanonicalSection
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
        source_type="pdf",  # unpaginated text; reuse the doc-style chunking preset
        title=filename,
        sections=[CanonicalSection(text=text, order=0)],
        pdf_path=filename,
    )
    doc.ensure_content_hash()
    return doc


def ingest_upload(filename: str, content: bytes) -> tuple[str, int]:
    """Extract, chunk, and index one uploaded file.

    Returns ``(document_id, points_indexed)`` where ``points_indexed`` counts the
    parent + child points upserted into Qdrant.
    """
    if Path(filename).suffix.lower() == ".pdf":
        doc = _pdf_document(filename, content)
    else:
        doc = _text_document(filename, content)
    points = index_canonical(doc)
    logger.info("Ingested upload %s -> %s (%d points)", filename, doc.document_id, points)
    return doc.document_id, points
