from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

@dataclass
class EntityRef:
    """A resolved reference from a document to another CMS entity (taxonomy
    term, people node, ...). Carries the referenced entity's UUID so joins
    stay correct when the entity is later renamed; the label is display-only.
    ``entity_type`` is the JSON:API type, e.g. "taxonomy_term--themes";
    ``field_name`` is the referencing field on the source document."""

    field_name: str
    uuid: str
    entity_type: str
    label: str | None = None

    @property
    def vocabulary(self) -> str | None:
        """Vocabulary of a taxonomy_term reference, else None."""
        prefix, _, bundle = self.entity_type.partition("--")
        return bundle if prefix == "taxonomy_term" else None


@dataclass
class CanonicalSection:
    text: str
    heading: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    order: int = 0

@dataclass
class CanonicalDocument:
    document_id: str
    source_type: str
    title: str | None = None
    sections: list[CanonicalSection] = field(default_factory=list)

    source_url: str | None = None
    file_url: str | None = None
    pdf_id: str | None = None
    pdf_path: str | None = None
    article_uuid: str | None = None
    linked_pdf_id: str | None = None
    linked_article_uuid: str | None = None

    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    language: str = "en"
    tenant_id: str = "default"
    acl: list[str] = field(default_factory=lambda: ["public"])

    published_at: str | None = None
    doc_version: int = 1
    is_current: bool = True
    content_hash: str = ""

    extra: dict[str, Any] = field(default_factory=dict)
    # Entity references and the full normalized source metadata. Catalog-only:
    # persisted to MySQL (terms / document_term / raw_meta), never into chunk
    # payloads — the chunker copies fields into DocumentMeta explicitly.
    entity_refs: list[EntityRef] = field(default_factory=list)
    raw_meta: dict[str, Any] = field(default_factory=dict)

    @property
    def is_paginated(self) -> bool:
        return any(s.page_start is not None for s in self.sections)

    def full_text(self) -> str:
        parts: list[str] = []
        for section in self.sections:
            if section.heading:
                parts.append(section.heading)
            if section.text:
                parts.append(section.text)
        return "\n\n".join(parts).strip()

    def compute_content_hash(self) -> str:
        payload = f"{self.title or ''}\n\n{self.full_text()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def ensure_content_hash(self) -> str:
        if not self.content_hash:
            self.content_hash = self.compute_content_hash()
        return self.content_hash
