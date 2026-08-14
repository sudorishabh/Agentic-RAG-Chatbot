"""Promoting principal-investigator names to claim-eligible identities.

The problem this solves
-----------------------
Phase 7 staged 1,064 claims and rejected **716** — every one of them a
``LED_BY`` claim whose principal investigator is a *provisional* PERSON. Only 5
survived. That is the eligibility gate working correctly, but it means the
corpus's best record of who leads what is almost entirely unusable.

Why a PI field is stronger evidence than an author string
---------------------------------------------------------
Measured, not assumed:

============================================  ==================  ==============
                                              ``documents_author``  PI fields
============================================  ==================  ==============
distinct names                                975                 **258**
on a project carrying an authoritative code   n/a                 **257 of 258**
============================================  ==================  ==============

An author facet accumulates every name printed on anything. A PI field is a
curated CMS assertion about one specific project: *this project's principal
investigator is X*. It is smaller, structured, and anchored to a project the CMS
identifies by code.

Two further measurements say the PI population behaves like real individuals
rather than conflated names:

* **no PI name spans more than 30 years** of project start dates (105 span under
  a decade, 44 under two, one under three);
* **129 of 143** PI names with a division recorded stay inside a single division
  area.

If "Arun Kumar" were three different people, wide spans and scattered divisions
are exactly what would show. They do not.

What this does NOT do
---------------------
It does not make PI membership sufficient. Rule 2 of the brief is explicit, and
so is the design: appearing in a PI field earns a name *consideration*, and it
must then survive every discriminating test below. A name that fails any of them
stays provisional, because an unresolved person is better than a wrong one.

Promoted names get their own trust level, ``pi_attested`` — claim-eligible, but
never conflated with ``authoritative``, which means a CMS person record with a
real UUID. The distinction is preserved so a promotion is auditable and
reversible.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.knowledge.normalize import is_initials_only, normalize_person

logger = logging.getLogger(__name__)

PROMOTION_VERSION = "pi-promotion-v1"

# The trust level a promoted PI name carries. Deliberately its own value: it is
# stronger than a bare facet name and weaker than a CMS person record, and
# collapsing it into either would lose why the promotion happened.
TRUST_PI_ATTESTED = "pi_attested"

_PI_FIELDS = ("field_completed_pi_name", "field_ongoing_pi_name")
_CODE_FIELDS = ("field_completed_project_code", "field_ongoing_project_code")
_START_FIELDS = ("field_completed_start_date", "field_ongoing_start_date")
_DIVISION_FIELDS = ("field_completed_division_area", "field_ongoing_division_area")
_PROJECT_BUNDLES = ("completed_projects", "ongoing_projects")

# --- the discriminating thresholds, each targeting one failure mode --------- #

# A single-token name identifies nobody: "Neha" is a real PI value.
MIN_NAME_TOKENS = 2

# How many *other* people may share a surname before the name is treated as
# collision-prone. "Arun Kumar" is the shape being guarded against: with 24
# Kumars and 28 Singhs in the person population, a two-token name built from a
# crowded surname is a poor identity.
MAX_SHARED_SURNAME = 5

# A career longer than this suggests the name covers more than one person.
# Nothing in the corpus exceeds 30 years, so this rejects nothing today and
# exists to catch the case as the corpus grows.
MAX_CAREER_YEARS = 35

# A PI whose projects sit in several division areas may be one senior person or
# two unrelated ones. 14 of 143 names do this; they stay provisional.
MAX_DIVISION_AREAS = 1


@dataclass
class PiEvidence:
    """Everything the CMS says about one PI name, gathered across projects."""

    normalized: str
    surface: str
    project_ids: set[str] = field(default_factory=set)
    project_codes: set[str] = field(default_factory=set)
    divisions: set[str] = field(default_factory=set)
    start_dates: list[str] = field(default_factory=list)

    @property
    def career_years(self) -> int:
        if len(self.start_dates) < 2:
            return 0
        return int(max(self.start_dates)[:4]) - int(min(self.start_dates)[:4])

    def as_audit(self) -> dict[str, Any]:
        return {
            "projects": len(self.project_ids),
            "project_codes": sorted(self.project_codes)[:5],
            "divisions": sorted(self.divisions),
            "career_years": self.career_years,
        }


@dataclass
class PromotionDecision:
    """Whether one PI name may become claim-eligible, and why."""

    normalized: str
    surface: str
    promote: bool
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)


def _values(raw: Any) -> list[str]:
    if raw is None:
        return []
    items = raw if isinstance(raw, list) else [raw]
    return [str(v).strip() for v in items if str(v).strip()]


def _iso(value: Any) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).date().isoformat()
    except ValueError:
        return None


def collect_pi_evidence() -> dict[str, PiEvidence]:
    """Gather, per normalized PI name, what the CMS records across projects."""
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    placeholders = ", ".join(["%s"] * len(_PROJECT_BUNDLES))
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, raw_meta FROM `{table}` "
            f"WHERE bundle IN ({placeholders}) AND entity_type = 'node' "
            "AND raw_meta IS NOT NULL",
            _PROJECT_BUNDLES,
        )
        rows = cur.fetchall()

    evidence: dict[str, PiEvidence] = {}
    for row in rows:
        raw = row["raw_meta"]
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        try:
            meta = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except (TypeError, ValueError):
            continue

        code = next(
            (str(meta[f]).strip() for f in _CODE_FIELDS if meta.get(f)), None
        )
        start = next((_iso(meta.get(f)) for f in _START_FIELDS if meta.get(f)), None)
        divisions = {
            value for f in _DIVISION_FIELDS for value in _values(meta.get(f))
        }

        for pi_field in _PI_FIELDS:
            for surface in _values(meta.get(pi_field)):
                normalized = normalize_person(surface)
                if not normalized:
                    continue
                entry = evidence.setdefault(
                    normalized, PiEvidence(normalized=normalized, surface=surface)
                )
                entry.project_ids.add(row["document_id"])
                if code:
                    entry.project_codes.add(code)
                if start:
                    entry.start_dates.append(start)
                entry.divisions.update(divisions)
    return evidence


def surname_frequency(person_names: list[str]) -> dict[str, int]:
    """How many people share each surname, across the whole person population."""
    counts: dict[str, int] = defaultdict(int)
    for name in person_names:
        tokens = name.split()
        if len(tokens) >= MIN_NAME_TOKENS:
            counts[tokens[-1]] += 1
    return dict(counts)


def decide(
    entry: PiEvidence, *, surnames: dict[str, int], ambiguous: set[str],
) -> PromotionDecision:
    """Whether this PI name may be promoted. Every test must pass.

    Ordered so the cheapest and most decisive refusals come first, and so the
    reason recorded is the *first* thing wrong rather than an arbitrary one.
    """
    def refuse(reason: str) -> PromotionDecision:
        return PromotionDecision(
            entry.normalized, entry.surface, False, reason, entry.as_audit()
        )

    tokens = entry.normalized.split()

    # A name that identifies nobody cannot be made to identify someone.
    if is_initials_only(entry.normalized):
        return refuse("initials only")
    if len(tokens) < MIN_NAME_TOKENS:
        return refuse(f"fewer than {MIN_NAME_TOKENS} name tokens")

    # Already known to denote more than one thing.
    if entry.normalized in ambiguous:
        return refuse("name is marked ambiguous")

    # The "Arun Kumar" guard: a two-token name built on a crowded surname is a
    # poor identity however good the rest of the evidence is.
    shared = surnames.get(tokens[-1], 0) - 1
    if len(tokens) == MIN_NAME_TOKENS and shared >= MAX_SHARED_SURNAME:
        return refuse(f"surname shared with {shared} other people")

    # Requirement: project codes are authoritative project identifiers and must
    # be used wherever available. A PI anchored to a coded project is anchored
    # to a record the CMS identifies exactly.
    if not entry.project_codes:
        return refuse("no project carries an authoritative project code")

    # Contextual coherence — the two signals that would betray a conflated name.
    if entry.career_years > MAX_CAREER_YEARS:
        return refuse(f"career span of {entry.career_years} years")
    if len(entry.divisions) > MAX_DIVISION_AREAS:
        return refuse(f"spans {len(entry.divisions)} division areas")

    return PromotionDecision(
        entry.normalized, entry.surface, True,
        f"PI on {len(entry.project_ids)} project(s), "
        f"{len(entry.project_codes)} coded",
        entry.as_audit(),
    )


def evaluate_promotions() -> list[PromotionDecision]:
    """Decide every PI name against the current entity store. No writes."""
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT normalized_name FROM `{table}_entity` WHERE entity_type='PERSON'"
        )
        person_names = [r["normalized_name"] for r in cur.fetchall()]
        cur.execute(
            f"SELECT DISTINCT normalized FROM `{table}_entity_alias` "
            "WHERE is_ambiguous = 1"
        )
        ambiguous = {r["normalized"] for r in cur.fetchall()}

    surnames = surname_frequency(person_names)
    known = set(person_names)
    decisions: list[PromotionDecision] = []
    for normalized, entry in sorted(collect_pi_evidence().items()):
        if normalized not in known:
            # A PI name the seeder never created an entity for — nothing to
            # promote. It is unresolvable rather than provisional.
            continue
        decisions.append(decide(entry, surnames=surnames, ambiguous=ambiguous))
    return decisions


def apply_promotions(decisions: list[PromotionDecision]) -> int:
    """Raise promoted names to ``pi_attested`` and claim-eligible.

    Only ever promotes a **provisional** person. An authoritative identity is
    left alone — it already outranks this — and nothing is ever demoted here, so
    running the pass cannot take eligibility away from something that earned it
    another way.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    promote = [d.normalized for d in decisions if d.promote]
    if not promote:
        return 0
    table = state_table()
    changed = 0
    with mysql_connection() as conn, conn.cursor() as cur:
        for batch_start in range(0, len(promote), 500):
            batch = promote[batch_start : batch_start + 500]
            placeholders = ", ".join(["%s"] * len(batch))
            cur.execute(
                f"UPDATE `{table}_entity` SET trust=%s, claim_eligible=1 "
                f"WHERE entity_type='PERSON' AND trust='provisional' "
                f"AND normalized_name IN ({placeholders})",
                [TRUST_PI_ATTESTED, *batch],
            )
            changed += cur.rowcount
        conn.commit()
    logger.info("Promoted %d PI names to %s.", changed, TRUST_PI_ATTESTED)
    return changed
