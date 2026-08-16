"""Incremental change detection: diff the corpus against stored state and
yield NEW/CHANGED/UNCHANGED/DELETED records.

:mod:`.drupal` crawls the JSON:API — nodes, taxonomy terms and custom blocks,
plus the PDFs attached to or linked from them — against the record/status
contract in :mod:`.base`.
"""
from app.ingestion.change_detection.base import (
    ChangeRecord,
    ChangeStatus,
    _parse_bundle_spec,
    content_changed,
    needs_rebuild,
    next_version,
    pipeline_changed,
)
from app.ingestion.change_detection.drupal import detect_drupal_changes

__all__ = [
    "ChangeRecord",
    "ChangeStatus",
    "content_changed",
    "pipeline_changed",
    "needs_rebuild",
    "next_version",
    "detect_drupal_changes",
]
