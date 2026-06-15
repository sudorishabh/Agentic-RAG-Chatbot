"""Canonical data model — the single normalized representation every source
(PDF, Drupal article, …) is converted into *before* chunking.

This is §2.1 of ``docs/cononical_data.md``: rather than teaching the chunker
about each source's quirks, every extractor produces a :class:`CanonicalDocument`
made of ordered :class:`CanonicalSection`s. The chunker then has one shape to
chunk and one place that owns the canonical metadata that lands on every Qdrant
payload (§1.5 / §3.6).

Fields that don't apply to a source type are simply left ``None`` / empty and
dropped from the payload downstream.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonicalSection:
    """One logical section of a document — a heading and its body text.

    For PDFs ``page_start`` / ``page_end`` carry the citation page(s); for
    articles they are ``None``. ``order`` is the section's position in reading
    order and seeds the chunk ids so re-ingesting identical content is
    idempotent.
    """

    text: str
    heading: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    order: int = 0


@dataclass
class CanonicalDocument:
    """A source-agnostic document ready to chunk.

    The metadata fields below are the canonical payload (§1.5): they propagate,
    unchanged, onto every parent and child chunk emitted from this document.
    Source-specific fields (``pdf_path``/``page`` vs ``source_url``/
    ``article_uuid``) are populated only by the relevant normalizer.
    """

    document_id: str
    source_type: str  # "pdf" | "article" | ...
    title: str | None = None
    sections: list[CanonicalSection] = field(default_factory=list)

    # Citation + cross-reference metadata.
    source_url: str | None = None
    pdf_id: str | None = None
    pdf_path: str | None = None
    article_uuid: str | None = None
    linked_pdf_id: str | None = None
    linked_article_uuid: str | None = None

    # Filter / display metadata.
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    language: str = "en"
    tenant_id: str = "default"
    acl: list[str] = field(default_factory=lambda: ["public"])

    # Versioning / audit.
    published_at: str | None = None
    doc_version: int = 1
    is_current: bool = True
    content_hash: str = ""

    # Anything source-specific worth carrying onto the payload verbatim.
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_paginated(self) -> bool:
        """True when any section carries page numbers (PDF-like sources)."""
        return any(s.page_start is not None for s in self.sections)

    def full_text(self) -> str:
        """All section text in reading order, headings inlined as markers so a
        downstream content hash reflects structure as well as prose."""
        parts: list[str] = []
        for section in self.sections:
            if section.heading:
                parts.append(section.heading)
            if section.text:
                parts.append(section.text)
        return "\n\n".join(parts).strip()

    def compute_content_hash(self) -> str:
        """Stable hash of title + body, for change detection (§1.5)."""
        payload = f"{self.title or ''}\n\n{self.full_text()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def ensure_content_hash(self) -> str:
        """Populate :attr:`content_hash` if unset and return it."""
        if not self.content_hash:
            self.content_hash = self.compute_content_hash()
        return self.content_hash
