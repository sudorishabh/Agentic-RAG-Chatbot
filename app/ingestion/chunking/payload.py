"""Chunk -> Qdrant payload serialization, kept apart from the chunk data model."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.ingestion.chunking.models import Chunk


def build_payload(chunk: "Chunk") -> dict[str, Any]:
    m = chunk.meta
    payload: dict[str, Any] = {
        "chunk_id": chunk.chunk_id,
        "document_id": m.document_id,
        "is_parent": chunk.is_parent,
        "source_type": m.source_type,
        "title": m.title,
        "section_heading": chunk.section_heading,
        "section_type": chunk.section_type,
        "chunk_text": chunk.text,
        "content_hash": chunk.content_hash,
        "token_count": chunk.token_count,
        "has_table": chunk.has_table or None,
        "table_markdown": chunk.table_markdown,
        "doc_version": m.doc_version,
        "is_current": m.is_current,
        "tenant_id": m.tenant_id,
        "acl": m.acl,
        "tags": m.tags,
        "categories": m.categories,
        "authors": m.authors,
        "term_ids": m.term_ids,
        "theme_ids": m.theme_ids,
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
        payload["parent_chunk_id"] = chunk.parent_chunk_id
        payload["chunk_index"] = chunk.chunk_index
        payload["page_number"] = chunk.page_number
    if chunk.page_range is not None:
        payload["page_range"] = list(chunk.page_range)
    payload.update(m.extra)
    return {k: v for k, v in payload.items() if v not in (None, "", [])}
