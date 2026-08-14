"""Deterministic claims from CMS metadata.

Free, exact, and the largest source of true relationships this corpus has. The
CMS asserts the relationship directly, so there is nothing to infer and no model
to distrust.

What the fields actually say
----------------------------
``field_completed_sponsors`` (915) and ``field_ongoing_sponsors`` (377) name the
organizations that funded a project. **All 915 completed-sponsor values resolve
to a seeded ORGANIZATION**, which is what makes this worth preferring over any
text extraction.

``field_completed_pi_name`` (497) and ``field_ongoing_pi_name`` (414) name the
principal investigator — a person who leads the project. Most of those names are
*provisional* identities, so most of these claims are refused by the eligibility
gate; that refusal is correct and is the point of the gate.

``field_completed_start_date`` / ``field_completed_end_date`` (1,030 each) give a
completed project a closed period. ``field_ongoing_start_date`` (593) gives an
ongoing one a start and no end — the corpus's own way of saying "current".
Both feed :func:`app.knowledge.claims.temporal.subject_period`.

``field_ongoing_stakeholders`` is deliberately **not** used: its values are
audience categories ("Policy Makers", "Businesses", "Academicians"), not
organizations, so no relationship can be built from it.

Evidence is ``cms_field`` rather than a quote: the fact lives in a metadata
field, not in prose, and inventing a quote would fabricate a span.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from app.knowledge.claims import temporal, types as t
from app.knowledge.normalize import normalize_org, normalize_person

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "claims-cms-v2"

# CMS field -> (predicate, object entity type). Only fields whose meaning is
# unambiguous: these claims assert at confidence 1.0, so there is no score to
# hedge with and an arguable reading does not belong here.
_FIELD_RULES: tuple[tuple[str, str, str], ...] = (
    ("field_completed_sponsors", "FUNDED_BY", "ORGANIZATION"),
    ("field_ongoing_sponsors", "FUNDED_BY", "ORGANIZATION"),
    ("field_completed_pi_name", "LED_BY", "PERSON"),
    ("field_ongoing_pi_name", "LED_BY", "PERSON"),
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


def _meta(raw: Any) -> dict[str, Any]:
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return {}
    return raw or {}


def _value_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def extract_cms_claims(index: Any, *, limit: int | None = None) -> list[Any]:
    """Every claim the CMS states outright, as unvalidated assertions.

    Returns assertions rather than staging them, so validation still runs. A
    sponsor whose organization was demoted, or a PI who is only a provisional
    identity, must be rejected like anything else rather than trusted for its
    provenance — which is exactly what happens to most PI names here.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    lookup: dict[str, dict[str, str]] = {"ORGANIZATION": {}, "PERSON": {}}
    for entity_id, row in index.entities.items():
        entity_type = row["entity_type"]
        if entity_type in lookup:
            lookup[entity_type][row["normalized_name"]] = entity_id
    normalizers = {"ORGANIZATION": normalize_org, "PERSON": normalize_person}
    projects_by_uuid = {
        row.get("cms_uuid"): entity_id
        for entity_id, row in index.entities.items()
        if row["entity_type"] == "PROJECT" and row.get("cms_uuid")
    }

    placeholders = ", ".join(["%s"] * len(_PROJECT_BUNDLES))
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, raw_meta FROM `{table}` "
            f"WHERE bundle IN ({placeholders}) AND entity_type = 'node' "
            "AND raw_meta IS NOT NULL",
            _PROJECT_BUNDLES,
        )
        rows = cur.fetchall()

    out: list[Any] = []
    for row in rows:
        subject = projects_by_uuid.get(row["document_id"])
        if subject is None:
            continue
        meta = _meta(row["raw_meta"])
        # The project's own CMS-stated period scopes every relationship to it.
        # The single approved inference in the claim layer, and recorded under
        # its own basis so it is never mistaken for a stated relationship date.
        window = temporal.subject_period(meta)

        for field_name, predicate, object_type in _FIELD_RULES:
            for value in _values(meta.get(field_name)):
                object_id = lookup[object_type].get(normalizers[object_type](value))
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
                        source_value=value[:512],
                        source_value_hash=_value_hash(value),
                        valid_from=window.valid_from,
                        valid_until=window.valid_until,
                        temporal_basis=window.basis,
                        confidence=CMS_CONFIDENCE,
                        extraction_method="cms_field",
                        extractor_version=EXTRACTOR_VERSION,
                    )
                )
        if limit is not None and len(out) >= limit:
            break

    logger.info("Built %d CMS-field assertions.", len(out))
    return out


def stale_claim_ids(fresh: list[Any], staged: list[dict[str, Any]]) -> list[str]:
    """Staged CMS claims whose source field no longer supports them.

    The answer to "can an edit to a structured field silently change a claim's
    meaning?" — it cannot, because the field's *value* reaches ``claim_id``
    through the object, so an edit produces a different claim. What an edit
    *can* do is leave the old claim behind, still asserting a sponsor that was
    corrected away.

    So the correct treatment is retraction, not content hashing: any staged
    ``cms_field`` claim for a (document, field) that the current extraction no
    longer produces is stale. Retracted rather than deleted, because the claim
    was true of the source as it stood, and that history is worth keeping.
    """
    fresh_ids = {a.claim_id for a in fresh}
    covered = {
        (a.document_id, a.source_field)
        for a in fresh
        if a.evidence_kind == t.EVIDENCE_CMS_FIELD
    }
    stale: list[str] = []
    for row in staged:
        if row.get("evidence_kind") != t.EVIDENCE_CMS_FIELD:
            continue
        if row.get("status") == t.STATUS_RETRACTED:
            continue
        key = (row.get("document_id"), row.get("source_field"))
        # Only judge a (document, field) the current pass actually looked at;
        # a field absent from this run's scope says nothing about its claims.
        if key not in covered:
            continue
        if row["claim_id"] not in fresh_ids:
            stale.append(row["claim_id"])
    return stale
