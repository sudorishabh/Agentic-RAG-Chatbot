"""Chunk -> Qdrant payload serialization, kept apart from the chunk data model."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.ingestion.chunking.models import Chunk


def build_payload(chunk: "Chunk") -> dict[str, Any]:
    from app.ingestion.version import PIPELINE_VERSION

    m = chunk.meta
    payload: dict[str, Any] = {
        "chunk_id": chunk.chunk_id,
        "document_id": m.document_id,
        # What built this point. On the payload as well as the catalog row so
        # drift is answerable from the store that holds the data: "which points
        # predate the chunker fix" is a question about points, and the catalog
        # cannot answer it for a document whose row says one thing while its
        # points say another.
        "pipeline_version": PIPELINE_VERSION,
        "is_parent": chunk.is_parent,
        "source_type": m.source_type,
        "title": m.title,
        "section_heading": chunk.section_heading,
        "section_type": chunk.section_type,
        "chunk_text": chunk.text,
        "content_hash": chunk.content_hash,
        "token_count": chunk.token_count,
        # `has_table` is read by the prompt builder and the rerank table boost.
        # The table markdown itself is deliberately NOT stored: `join_blocks`
        # already put every table row into `chunk_text`, so persisting it again
        # duplicated ~10% of the payload for no reader. It stays on the Chunk
        # for tooling and to derive `has_table`. See tests/test_chunk_payload.py.
        "has_table": chunk.has_table or None,
        "doc_version": m.doc_version,
        "is_current": m.is_current,
        "tags": m.tags,
        "categories": m.categories,
        "authors": m.authors,
        "language": m.language,
        "source_url": m.source_url,
        "file_url": m.file_url,
        "published_at": m.published_at,
        "pdf_id": m.pdf_id,
        "pdf_path": m.pdf_path,
        "article_uuid": m.article_uuid,
        "linked_pdf_id": m.linked_pdf_id,
        "linked_article_uuid": m.linked_article_uuid,
    }
    if not chunk.is_parent:
        # Only children carry a real vector, so only they carry the fingerprint
        # of the text it was built from — the key `_reusable_vectors` checks
        # before skipping an embedding call.
        payload["embed_hash"] = chunk.embed_hash
        payload["parent_chunk_id"] = chunk.parent_chunk_id
        payload["chunk_index"] = chunk.chunk_index
        payload["page_number"] = chunk.page_number
    if chunk.page_range is not None:
        payload["page_range"] = list(chunk.page_range)
    if chunk.overlap_page_range is not None:
        payload["overlap_page_range"] = list(chunk.overlap_page_range)
    payload.update(m.extra)
    return {k: v for k, v in payload.items() if v not in (None, "", [])}
