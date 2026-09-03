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
class FileLink:
    """A document's link to an attached file. The file is ingested as its own
    document (keyed by this uuid); the link records which node references it."""

    uuid: str
    origin: str  # "attachment" | "inbody"
    url: str | None = None
    filename: str | None = None


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

    #: The document's primary date: the effective/business date resolved from
    #: its Drupal bundle's configured field, or its creation stamp where the
    #: bundle has nothing else. Everything that ranks, orders or filters reads
    #: this one.
    effective_start_date: str | None = None
    start_precision: str | None = None
    #: Where :attr:`effective_start_date` came from. Carried on the document so
    #: the catalogue can record it without re-deriving it, and so a value and its
    #: provenance are always written together.
    date_source: str | None = None
    #: The end of the period this document's content covers, when its bundle
    #: declares an end field and that field held a usable date. None otherwise,
    #: and **never manufactured** from `effective_start_date`: a single-date document has
    #: no end, and saying otherwise would invent a period nobody stated.
    #:
    #: `effective_start_date` remains the effective date every ranking, ordering and
    #: filtering path reads. This is retained beside it as business metadata and
    #: for date-range questions.
    effective_end_date: str | None = None
    end_precision: str | None = None
    doc_version: int = 1
    is_current: bool = True
    content_hash: str = ""

    extra: dict[str, Any] = field(default_factory=dict)
    # Entity references, attached-file links, and the full normalized source
    # metadata. Catalog-only: persisted to MySQL (terms / document_term /
    # document_attachment / raw_meta), never into chunk payloads — the chunker
    # copies fields into DocumentMeta explicitly.
    entity_refs: list[EntityRef] = field(default_factory=list)
    file_links: list[FileLink] = field(default_factory=list)
    raw_meta: dict[str, Any] = field(default_factory=dict)
    #: How `effective_start_date` was decided: the bundle, the field consulted, the raw
    #: value and the rule that fired
    #: (:class:`app.ingestion.bundle_dates.EffectiveDate`).
    #:
    #: Catalog-only, like the three fields above, and for a sharper reason: it is
    #: carried here rather than in `extra` precisely *because* `build_payload`
    #: does `payload.update(m.extra)`, so anything parked there would be
    #: replicated into every chunk payload. The value and its precision belong
    #: beside the document; the reasoning belongs in
    #: `{state}_date_decision`, which the pipeline writes from this.
    #:
    #: Untyped to keep `core` from importing `ingestion` — the domain names the
    #: shape, the model only carries it.
    date_evidence: Any = None

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
        """SHA-256 of the document's body text — and *only* its body text.

        Deliberately excludes the title and every other metadata field, because
        the hash has to be reproducible from the source bytes alone. Any field
        that could be derived (a title read off a PDF cover page rather than
        taken from the CMS) would otherwise make the hash unstable across runs:
        `content_changed` would fire on every sweep, re-versioning, re-embedding
        and re-upserting the whole corpus forever, silently and at full cost.

        Metadata still reaches storage — it just does not gate re-indexing.
        Title drift on an otherwise-unchanged document is carried to the catalog
        by `_save_state` and to the chunk payloads by `refresh_document_title`,
        neither of which needs a re-embed.
        """
        return hashlib.sha256(self.full_text().encode("utf-8")).hexdigest()

    def ensure_content_hash(self) -> str:
        if not self.content_hash:
            self.content_hash = self.compute_content_hash()
        return self.content_hash
