"""Shared change-detection types: the record/status contract the Drupal crawl
yields for nodes and their attached PDFs alike, and the NEW/CHANGED/UNCHANGED
decision it makes for both."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.catalog.models import StateRecord


class ChangeStatus(str, Enum):
    NEW = "new"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class ChangeRecord:

    status: ChangeStatus
    document_id: str
    source_type: str
    source_key: str
    fingerprint: str = ""
    bundle: str | None = None
    changed_mark: int | None = None
    prior: StateRecord | None = None
    payload: Any = None
    filename: str | None = None
    # JSON:API entity type ("node", "taxonomy_term", "block_content") for
    # Drupal records; None for attachment documents.
    entity_type: str | None = None

    @property
    def is_actionable(self) -> bool:
        return self.status in (ChangeStatus.NEW, ChangeStatus.CHANGED, ChangeStatus.DELETED)


def _parse_bundle_spec(spec: str) -> tuple[str, str, bool]:
    """Parse a --bundle value: 'report' is a node bundle; 'block_content:basic'
    scopes another entity type. Only node bundles crawl incrementally.

    Parsing only — whether a parsed source may be crawled at all is decided by
    ``change_detection.drupal._searchable_sources``, so an unsupported entity
    type still parses cleanly and is refused there with a reason.
    """
    entity_type, sep, bundle = spec.partition(":")
    if not sep:
        entity_type, bundle = "node", spec
    return entity_type, bundle, entity_type == "node"


def content_changed(record: ChangeRecord, content_hash: str) -> bool:
    if record.prior is None:
        return True
    return record.prior.content_hash != content_hash


def pipeline_stale(prev: StateRecord | None) -> bool:
    """Whether this catalogued document was built by a superseded pipeline.

    A stored version of None — a row written before versions were stamped — is
    deliberately *not* current: unknown must read as stale, or the corpus that
    most needs rebuilding is the one that never gets it. A document with no row
    at all is not stale; it is unseen, and is built anyway.
    """
    from app.ingestion.version import PIPELINE_VERSION

    return prev is not None and prev.pipeline_version != PIPELINE_VERSION


def pipeline_changed(record: ChangeRecord) -> bool:
    """:func:`pipeline_stale` for a record the crawl has just yielded."""
    return pipeline_stale(record.prior)


def needs_rebuild(record: ChangeRecord, content_hash: str) -> bool:
    """Whether this document must be chunked, embedded and indexed again.

    Two independent reasons, and the second is the one the pipeline lacked: the
    *content* changed, or the *code* did. Gating re-indexing on content alone
    pinned every document to whatever the pipeline did on the day it was first
    seen — chunker fixes, a chunk-id scheme change and a payload cleanup all
    landed and none of them ever reached the corpus, because the body text they
    would have been applied to had not changed.
    """
    return content_changed(record, content_hash) or pipeline_changed(record)


def next_version(record: ChangeRecord) -> int:
    return record.prior.doc_version + 1 if record.prior else 1


def compute_status(prev: StateRecord | None, fingerprint: str) -> ChangeStatus:
    """The NEW/CHANGED/UNCHANGED decision shared by every Drupal record (nodes,
    taxonomy terms, blocks and attachments alike): unseen before is NEW, a
    changed fingerprint is CHANGED, otherwise UNCHANGED.

    A superseded pipeline version counts as CHANGED. Without that the version
    check downstream is unreachable for exactly the documents it exists for: an
    UNCHANGED record is never built, so its content hash and its stored version
    are never compared to anything, and a chunker fix would still never reach a
    document whose source has not been edited since.

    The cost is deliberate and bounded — after a version bump, every document the
    crawl *reaches* is rebuilt — and which documents it reaches is still decided
    by the incremental window. A corpus-wide reprocess is therefore a matter of
    widening that window (see :mod:`app.ingestion.reprocess`), not of a second
    code path that re-implements ingestion.
    """
    if prev is None:
        return ChangeStatus.NEW
    if prev.fingerprint != fingerprint:
        return ChangeStatus.CHANGED
    if pipeline_stale(prev):
        return ChangeStatus.CHANGED
    return ChangeStatus.UNCHANGED
