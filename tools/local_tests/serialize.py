"""Turn captured ingestion artifacts into complete, untruncated dicts.

Every field is preserved verbatim (full page text, full chunk text, full
payloads, full metadata, full MySQL rows) so the raw dumps show exactly what
each stage produced. One dict per document feeds both the JSON file and the
readable text dump, so the two never drift.
"""

from __future__ import annotations

from typing import Any


def record_to_dict(record: Any) -> dict[str, Any]:
    prior = record.prior
    return {
        "status": record.status.value,
        "document_id": record.document_id,
        "source_type": record.source_type,
        "source_key": record.source_key,
        "bundle": record.bundle,
        "entity_type": record.entity_type,
        "fingerprint": record.fingerprint,
        "changed_mark": record.changed_mark,
        "filename": record.filename,
        "prior": None if prior is None else {
            "doc_version": prior.doc_version,
            "content_hash": prior.content_hash,
            "fingerprint": prior.fingerprint,
            "indexed_at": prior.indexed_at,
        },
    }


def extraction_to_dict(result: Any) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "source": result.source,
        "metadata": result.metadata,
        "page_count": len(result.pages),
        "pages": [
            {
                "page_number": page.page_number,
                "extracted_via": page.extracted_via.value,
                "char_count": len(page.text),
                "text": page.text,
                "tables": [
                    {
                        "page_number": table.page_number,
                        "rows": table.rows,
                        "cols": table.cols,
                        "caption": table.caption,
                        "markdown": table.markdown,
                        "cells": table.cells,
                    }
                    for table in page.tables
                ],
            }
            for page in result.pages
        ],
    }


def canonical_to_dict(doc: Any) -> dict[str, Any] | None:
    if doc is None:
        return None
    return {
        "document_id": doc.document_id,
        "source_type": doc.source_type,
        "title": doc.title,
        "source_url": doc.source_url,
        "file_url": doc.file_url,
        "pdf_id": doc.pdf_id,
        "pdf_path": doc.pdf_path,
        "article_uuid": doc.article_uuid,
        "linked_pdf_id": doc.linked_pdf_id,
        "linked_article_uuid": doc.linked_article_uuid,
        "authors": list(doc.authors),
        "tags": list(doc.tags),
        "categories": list(doc.categories),
        "language": doc.language,
        "effective_start_date": doc.effective_start_date,
        "doc_version": doc.doc_version,
        "is_current": doc.is_current,
        "content_hash": doc.content_hash,
        "is_paginated": doc.is_paginated,
        "extra": dict(doc.extra),
        "entity_refs": [
            {
                "field_name": ref.field_name,
                "uuid": ref.uuid,
                "entity_type": ref.entity_type,
                "label": ref.label,
                "vocabulary": ref.vocabulary,
            }
            for ref in doc.entity_refs
        ],
        "file_links": [
            {
                "uuid": link.uuid,
                "origin": link.origin,
                "url": link.url,
                "filename": link.filename,
            }
            for link in doc.file_links
        ],
        "raw_meta": doc.raw_meta,
        "section_count": len(doc.sections),
        "sections": [
            {
                "order": section.order,
                "heading": section.heading,
                "page_start": section.page_start,
                "page_end": section.page_end,
                "char_count": len(section.text),
                "text": section.text,
            }
            for section in doc.sections
        ],
        "full_text": doc.full_text(),
    }


def chunk_to_dict(chunk: Any) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "is_parent": chunk.is_parent,
        "parent_chunk_id": chunk.parent_chunk_id,
        "chunk_index": chunk.chunk_index,
        "section_heading": chunk.section_heading,
        "section_type": chunk.section_type,
        "page_number": chunk.page_number,
        "page_range": list(chunk.page_range) if chunk.page_range else None,
        "token_count": chunk.token_count,
        "content_hash": chunk.content_hash,
        "has_table": chunk.has_table,
        "table_markdown": chunk.table_markdown,
        "text": chunk.text,
        # The exact payload upserted into Qdrant (parents carry a zero vector).
        "payload": chunk.to_payload(),
    }


def chunks_to_dict(chunks: list[Any]) -> dict[str, Any]:
    parents = [chunk_to_dict(c) for c in chunks if c.is_parent]
    children = [chunk_to_dict(c) for c in chunks if not c.is_parent]
    return {
        "parent_count": len(parents),
        "child_count": len(children),
        "parents": parents,
        "children": children,
    }


def snapshot_to_dict(snap: Any) -> dict[str, Any]:
    row = dict(snap.state_row) if snap.state_row else None
    if row and isinstance(row.get("raw_meta"), (bytes, bytearray)):
        row["raw_meta"] = row["raw_meta"].decode("utf-8", "replace")
    return {
        "state_row": row,
        "author_rows": list(snap.authors),
        "theme_rows": snap.theme_rows,
        "term_link_rows": snap.term_links,
        "attachment_rows": snap.attachments,
        "ingest_log_rows": snap.log_rows,
    }


def capture_to_dict(cap: Any, snap: Any) -> dict[str, Any]:
    """The complete record of one document across every ingestion stage."""
    return {
        "document_id": cap.record.document_id,
        "outcome": cap.outcome,
        "error": cap.error,
        "change_detection": record_to_dict(cap.record),
        "extraction": extraction_to_dict(cap.extraction),
        "canonical": canonical_to_dict(cap.doc),
        "chunking": chunks_to_dict(cap.chunks),
        "indexing": {"qdrant_points": cap.points},
        "mysql": snapshot_to_dict(snap),
    }
