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


def next_version(record: ChangeRecord) -> int:
    return record.prior.doc_version + 1 if record.prior else 1


def compute_status(prev: StateRecord | None, fingerprint: str) -> ChangeStatus:
    """The NEW/CHANGED/UNCHANGED decision shared by every Drupal record (nodes,
    taxonomy terms, blocks and attachments alike): unseen before is NEW, a
    changed fingerprint is CHANGED, otherwise UNCHANGED."""
    if prev is None:
        return ChangeStatus.NEW
    if prev.fingerprint != fingerprint:
        return ChangeStatus.CHANGED
    return ChangeStatus.UNCHANGED
