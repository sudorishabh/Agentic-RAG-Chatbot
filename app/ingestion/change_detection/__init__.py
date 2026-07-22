"""Incremental change detection: diff the corpus against stored state and
yield NEW/CHANGED/UNCHANGED/DELETED records.

Two independent sources share the record/status contract in :mod:`.base`:
:mod:`.files` walks local PDF directories; :mod:`.drupal` crawls the JSON:API.
"""
from app.ingestion.change_detection.base import (
    ChangeRecord,
    ChangeStatus,
    _parse_bundle_spec,
    content_changed,
    next_version,
)
from app.ingestion.change_detection.drupal import detect_drupal_changes
from app.ingestion.change_detection.files import _parse_roots, detect_file_changes

__all__ = [
    "ChangeRecord",
    "ChangeStatus",
    "content_changed",
    "next_version",
    "detect_file_changes",
    "detect_drupal_changes",
]
