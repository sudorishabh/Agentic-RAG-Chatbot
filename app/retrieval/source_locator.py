from __future__ import annotations

import logging
from pathlib import Path

from app.config import get_settings
from app.deps import get_qdrant_client

logger = logging.getLogger(__name__)


def _allowed_roots() -> list[Path]:
    """Resolved PDF source roots — the only directories a source file may be
    served from. Parsed the same way ingestion discovers PDFs."""
    from app.ingestion.change_detection import _parse_roots

    settings = get_settings()
    raw = settings.pdf_source_dirs or settings.pdf_source_path
    roots: list[Path] = []
    for root in _parse_roots(raw):
        try:
            roots.append(root.resolve())
        except OSError:
            continue
    return roots


def _within_roots(path: Path, roots: list[Path]) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    for root in roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _lookup_pdf_path(document_id: str) -> str | None:
    """Read the stored on-disk path for a document from the index. The id may
    match either the document_id or the pdf_id payload field."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    settings = get_settings()
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        return None

    flt = Filter(
        should=[
            FieldCondition(key="document_id", match=MatchValue(value=document_id)),
            FieldCondition(key="pdf_id", match=MatchValue(value=document_id)),
        ]
    )
    points, _ = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=flt,
        limit=1,
        with_payload=["pdf_path"],
        with_vectors=False,
    )
    if not points:
        return None
    return (points[0].payload or {}).get("pdf_path")


def resolve_source_file(document_id: str) -> Path | None:
    """Resolve a document_id / pdf_id to a readable PDF on disk.

    Returns None when the document is unknown, the file is missing, no source
    roots are configured, or the stored path escapes the configured roots
    (path-traversal guard). Callers should treat None as a 404.
    """
    raw = _lookup_pdf_path(document_id)
    if not raw:
        return None

    roots = _allowed_roots()
    if not roots:
        logger.warning(
            "No PDF source roots configured (PDF_SOURCE_PATH / PDF_SOURCE_DIRS); "
            "refusing to serve %s.",
            document_id,
        )
        return None

    path = Path(raw)
    if not _within_roots(path, roots):
        logger.warning("Path %r for %s is outside configured roots; refusing.", raw, document_id)
        return None
    if not path.is_file():
        logger.warning("Path %r for %s does not exist on disk.", raw, document_id)
        return None
    return path
