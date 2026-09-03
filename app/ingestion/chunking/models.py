"""Chunking data model: the per-document metadata carried onto every chunk,
and the chunk itself."""
from __future__ import annotations

import hashlib
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
    language: str | None = "en"
    doc_version: int = 1
    is_current: bool = True
    effective_start_date: str | None = None
    #: ``"year"`` when the source stated only a year and ``effective_start_date`` holds
    #: 1 January as a marker for it. None means a full date. Carried to the chunk
    #: payload because the answer layer is the only place that can keep a marker
    #: from being read as a day.
    start_precision: str | None = None
    #: End of the period the content covers. None for a single-date document.
    effective_end_date: str | None = None
    end_precision: str | None = None
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

    @property
    def embed_input(self) -> str:
        """Exactly the string the embedder is handed.

        The single definition of that, so the vector, its fingerprint and the
        payload can never disagree about what was embedded.
        """
        return self.embed_text or self.text

    @property
    def embed_hash(self) -> str:
        """Fingerprint of :attr:`embed_input` — the vector-reuse key.

        Distinct from ``content_hash`` on purpose. That one covers ``text``:
        what citations quote and what dedup compares, and it says nothing about
        the breadcrumb. The embedder sees the breadcrumb too, so retitling a
        document — or correcting one heading — changes what would be embedded
        while leaving ``content_hash`` byte-identical. Reuse has to key on what
        was embedded, or those edits silently keep a vector of the old title.
        """
        return hashlib.sha256(self.embed_input.encode("utf-8")).hexdigest()

    def to_payload(self) -> dict[str, Any]:
        from app.ingestion.chunking.payload import build_payload

        return build_payload(self)
