"""Catalog domain models: the ingest-state record and its link/log types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AttachmentLink:
    """A node's link to an attached PDF (its own document, keyed by file_uuid)."""

    file_uuid: str
    origin: str  # "attachment" | "inbody"
    url: str | None = None
    filename: str | None = None


@dataclass
class StateRecord:

    document_id: str
    source_type: str
    source_key: str
    fingerprint: str
    content_hash: str = ""
    doc_version: int = 1
    # Which ingestion pipeline produced the indexed content (see
    # app.ingestion.version). A row whose version differs from the running
    # pipeline's is rebuilt on its next crawl even when its content is
    # unchanged — content hashes cannot see a code change. None on a row written
    # before the column existed, which is treated as "not the current version".
    pipeline_version: str | None = None
    bundle: str | None = None
    # JSON:API entity type ("node", "taxonomy_term", "block_content") for
    # Drupal records; None for attachment documents.
    # Content counts filter on it so facet terms don't count as documents.
    entity_type: str | None = None
    changed_mark: int | None = None
    indexed_at: str | None = None
    published_at: str | None = None
    #: The date the document itself states it was published. None unless the
    #: document says so; ``published_at`` above is the page date and stays the
    #: field chronology uses. Never inferred from an edition label, a PDF
    #: CreationDate or an upload time.
    document_published_at: str | None = None
    # Display fields so structured list/lookup queries can be answered from the
    # catalog (no live site fetch). url is the document's public page/file URL.
    title: str | None = None
    url: str | None = None
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    # Free-text keyword tags (documents_tag). Separate from `categories`
    # (themes): tags are a flat, long-tail vocabulary with no hierarchy.
    tags: list[str] = field(default_factory=list)
    # Attachment links and the lossless source metadata (JSON column).
    attachments: list[AttachmentLink] = field(default_factory=list)
    raw_meta: dict[str, Any] | None = None


@dataclass
class LogEntry:
    """One ingestion event: where a file/record came from and what happened."""

    document_id: str
    source_type: str
    status: str
    run_id: str | None = None
    source_path: str | None = None
    source_url: str | None = None
    bundle: str | None = None
    tags: str | None = None
    title: str | None = None
    doc_version: int | None = None
    chunks_indexed: int | None = None
    fingerprint: str | None = None
    content_hash: str | None = None
    error_message: str | None = None
