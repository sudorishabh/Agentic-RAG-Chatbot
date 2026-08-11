"""Chunking data model: the per-document metadata carried onto every chunk,
and the chunk itself."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentMeta:

    document_id: str
    source_type: str
    title: str | None = None
    source_url: str | None = None
    file_url: str | None = None
    pdf_id: str | None = None
    pdf_path: str | None = None
    article_uuid: str | None = None
    linked_pdf_id: str | None = None
    linked_article_uuid: str | None = None
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    authors: list[str] = field(default_factory=list)
    # Taxonomy term UUIDs (theme_ids = category vocabularies only). Filters
    # join on these; the name lists above are display-only and may go stale
    # between a term rename and the payload refresh.
    term_ids: list[str] = field(default_factory=list)
    theme_ids: list[str] = field(default_factory=list)
    language: str | None = "en"
    tenant_id: str | None = None
    acl: list[str] = field(default_factory=list)
    doc_version: int = 1
    is_current: bool = True
    published_at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:

    chunk_id: str
    text: str
    is_parent: bool
    meta: DocumentMeta
    # What the embedder actually sees: `text` behind a "title › heading"
    # breadcrumb. Kept apart from `text` because `text` is what citations quote
    # and what `content_hash` covers, and neither may drift. Empty on parents,
    # which are stored as zero vectors and never embedded.
    embed_text: str = ""
    section_heading: str | None = None
    section_type: str | None = None
    parent_chunk_id: str | None = None
    chunk_index: int | None = None
    # `page_number` and `page_range` describe the chunk's OWN content, so a
    # citation resolves to where the substance is. A child's text is prefixed
    # with an overlap carry from the previous chunk, which may come from an
    # earlier page; `overlap_page_range` records that origin so the leading text
    # is not silently attributed to this chunk's page.
    page_number: int | None = None
    page_range: tuple[int, int] | None = None
    overlap_page_range: tuple[int, int] | None = None
    token_count: int = 0
    content_hash: str = ""
    has_table: bool = False
    table_markdown: str = ""

    def to_payload(self) -> dict[str, Any]:
        from app.ingestion.chunking.payload import build_payload

        return build_payload(self)
