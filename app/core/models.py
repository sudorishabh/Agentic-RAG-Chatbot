from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

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
