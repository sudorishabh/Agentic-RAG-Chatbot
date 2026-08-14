"""Deterministic claims from CMS metadata.

Free, exact, and the largest single source of true relationships this corpus
has: every project node's ``field_completed_sponsors`` names organizations that
funded it, and **all 915 sponsor mentions resolve to a seeded ORGANIZATION**.
The CMS is asserting the relationship directly, so there is nothing to infer and
no model to distrust.

Evidence is ``cms_field`` rather than a quote: the fact lives in a metadata
field, not in prose, and inventing a quote for it would fabricate a span. The
document id and the field name are the provenance, and both are real.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Iterable

from app.knowledge.claims import types as t
from app.knowledge.normalize import normalize_org

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "claims-cms-v1"

# CMS metadata field -> the relationship it asserts. Only fields whose meaning
# is unambiguous: a sponsor funds, a partner delivers alongside. A field whose
# reading is arguable does not belong here, because there is no confidence score
# to hedge with — these claims are asserted at 1.0.
_FIELD_PREDICATES: tuple[tuple[str, str], ...] = (
    ("field_completed_sponsors", "FUNDED_BY"),
)

# The CMS states these as fact, so they carry full confidence. That is the point
# of preferring them: no model, no interpretation, nothing to review.
CMS_CONFIDENCE = 1.0

_PROJECT_BUNDLES = ("completed_projects", "ongoing_projects")


def _values(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            return [raw.strip()] if raw.strip() else []
    items = raw if isinstance(raw, list) else [raw]
    return [str(v).strip() for v in items if str(v).strip()]


def extract_cms_claims(index: Any, *, limit: int | None = None) -> list[Any]:
    """Every claim the CMS states outright, as unvalidated assertions.

    Returns assertions rather than staging them, so validation still runs: a
    sponsor name that no longer resolves, or a project whose entity was demoted,
    must be rejected like anything else rather than trusted for its provenance.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    # Organizations by normalized name, so a sponsor string can be turned into
    # an identity without guessing.
    orgs = {
        row["normalized_name"]: entity_id
        for entity_id, row in index.entities.items()
        if row["entity_type"] == "ORGANIZATION"
    }
    projects_by_uuid = {
        row.get("cms_uuid"): entity_id
        for entity_id, row in index.entities.items()
        if row["entity_type"] == "PROJECT" and row.get("cms_uuid")
    }

    fields = [field for field, _ in _FIELD_PREDICATES]
    json_paths = ", ".join(["%s"] * len(fields))
    placeholders = ", ".join(["%s"] * len(_PROJECT_BUNDLES))
    out: list[Any] = []
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, raw_meta FROM `{table}` "
            f"WHERE bundle IN ({placeholders}) AND entity_type = 'node' "
            "AND raw_meta IS NOT NULL",
            _PROJECT_BUNDLES,
        )
        rows = cur.fetchall()

    for row in rows:
        subject = projects_by_uuid.get(row["document_id"])
        if subject is None:
            continue
        raw = row["raw_meta"]
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        try:
            meta = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except (TypeError, ValueError):
            continue
        for field_name, predicate in _FIELD_PREDICATES:
            for value in _values(meta.get(field_name)):
                object_id = orgs.get(normalize_org(value))
                if object_id is None:
                    continue
                out.append(
                    t.build(
                        subject_entity_id=subject,
                        predicate=predicate,
                        object_entity_id=object_id,
                        document_id=row["document_id"],
                        evidence_kind=t.EVIDENCE_CMS_FIELD,
                        source_field=field_name,
                        confidence=CMS_CONFIDENCE,
                        extraction_method="cms_field",
                        extractor_version=EXTRACTOR_VERSION,
                        # The CMS states the relationship, never its dates.
                        temporal_basis=t.BASIS_UNKNOWN,
                    )
                )
        if limit is not None and len(out) >= limit:
            break
    logger.info("Built %d CMS-field assertions.", len(out))
    return out
