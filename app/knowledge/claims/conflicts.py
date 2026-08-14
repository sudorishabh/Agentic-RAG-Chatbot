"""Conflict detection, supersession, and current-state eligibility.

Detection is **mechanical, not heuristic** — that is what ``Predicate.functional``
buys. For a functional predicate, two active claims about the same subject whose
validity windows overlap and whose objects differ cannot both be true. For a
non-functional one, several objects are simply several facts: a project has many
funders, and treating that as a contradiction would be a bug.

Nothing is ever discarded
-------------------------
A conflict changes *status*, never existence. Every original claim keeps its
evidence, its window and its row; a contradiction is recorded as a link between
claims, not as a deletion. Two consequences worth stating:

* history stays queryable — "who led this in 2019" is answerable after a
  successor arrives, because the earlier claim is still there;
* the system under-reports rather than mis-reports — disputed claims produce no
  current-state edge at all, so traversal misses a relationship rather than
  confidently asserting the wrong one.

The resolution ladder
---------------------
Applied in order by deterministic code, never by a model:

1. **Non-overlapping windows are not a conflict.** "Bob until 2026-03" then
   "Alice from 2026-03" is a succession. Both stay ``active``; only the later
   one is current.
2. **Overlapping, one basis stronger than the other** → the stronger wins, the
   weaker becomes ``superseded``. A relationship the source dated beats one
   scoped from the subject's period.
3. **Overlapping, equal basis, one strictly later start** → the later claim
   wins and ``supersedes`` the earlier, which keeps its own window and evidence.
4. **Overlapping, equal basis, no ordering** → **both become ``disputed``** and
   neither projects. A review case would be queued here if there were a
   reviewer; there is not, so the safe state is the terminal one.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from app.knowledge.claims import predicates as vocab
from app.knowledge.claims import temporal, types as t

logger = logging.getLogger(__name__)

DETECTOR_VERSION = "claim-conflicts-v1"

# How two claims relate. Recorded as links between claim ids so a contradiction
# is inspectable rather than implied by two status flags.
LINK_CONTRADICTS = "contradicts"
LINK_SUPERSEDES = "supersedes"
LINK_KINDS = (LINK_CONTRADICTS, LINK_SUPERSEDES)

# Ranked strength of a validity basis. A window the source stated outranks one
# derived from the subject's period, which outranks having no window at all.
_BASIS_RANK = {
    t.BASIS_STATED: 3,
    t.BASIS_SUBJECT_PERIOD: 2,
    t.BASIS_DOCUMENT: 1,
    t.BASIS_UNKNOWN: 0,
}


@dataclass(frozen=True)
class ClaimLink:
    """One directed relationship between two claims."""

    from_claim_id: str
    to_claim_id: str
    kind: str
    reason: str


@dataclass
class ConflictReport:
    """What a detection pass concluded."""

    links: list[ClaimLink]
    # claim_id -> new status. Only claims whose status changed appear.
    status_changes: dict[str, str]
    examined: int = 0
    groups: int = 0

    @property
    def disputed(self) -> list[str]:
        return sorted(
            cid for cid, s in self.status_changes.items() if s == t.STATUS_DISPUTED
        )

    @property
    def superseded(self) -> list[str]:
        return sorted(
            cid for cid, s in self.status_changes.items() if s == t.STATUS_SUPERSEDED
        )


def _object_key(assertion: Any) -> str:
    return t.object_key(assertion.object_entity_id, assertion.object_literal)


def _basis_rank(assertion: Any) -> int:
    return _BASIS_RANK.get(assertion.temporal_basis, 0)


def _sort_key(assertion: Any) -> tuple:
    """Deterministic ordering, so a pass over the same claims always reaches the
    same verdict regardless of how the rows arrived."""
    window = temporal.window_of(assertion)
    return (
        window.valid_from or "",
        window.valid_until or "",
        -_basis_rank(assertion),
        assertion.claim_id,
    )


def _pair_verdict(a: Any, b: Any) -> tuple[str | None, str, str]:
    """Decide one overlapping pair.

    Returns ``(kind, winner_id, reason)``; ``kind`` is None when the pair is not
    a conflict at all. ``a`` and ``b`` arrive in sorted order.
    """
    window_a, window_b = temporal.window_of(a), temporal.window_of(b)

    # Rung 1 — succession, not contradiction.
    if not temporal.overlaps(window_a, window_b):
        return (None, "", "non-overlapping validity")

    # Rung 2 — a stronger basis wins.
    rank_a, rank_b = _basis_rank(a), _basis_rank(b)
    if rank_a != rank_b:
        winner, loser = (a, b) if rank_a > rank_b else (b, a)
        return (
            LINK_SUPERSEDES, winner.claim_id,
            f"{winner.temporal_basis} basis outranks {loser.temporal_basis}",
        )

    # Rung 3 — same basis, but one clearly starts later.
    start_a = window_a.valid_from
    start_b = window_b.valid_from
    if start_a and start_b and start_a != start_b:
        winner = b if start_b > start_a else a
        return (
            LINK_SUPERSEDES, winner.claim_id,
            "later stated start supersedes the earlier claim",
        )

    # Rung 4 — genuinely undecidable.
    return (
        LINK_CONTRADICTS, "",
        "overlapping validity, equal basis, no ordering",
    )


def detect(assertions: Sequence[Any]) -> ConflictReport:
    """Find conflicts among staged claims.

    Only ``active`` claims of **functional** predicates are examined: a
    non-functional predicate cannot conflict on multiplicity, and a claim
    already retracted or disputed is not evidence for a new verdict.
    """
    links: list[ClaimLink] = []
    status: dict[str, str] = {}
    groups: dict[tuple[str, str], list[Any]] = defaultdict(list)

    examined = 0
    for assertion in assertions:
        predicate = vocab.get(assertion.predicate)
        if predicate is None or not predicate.functional:
            continue
        if assertion.status != t.STATUS_ACTIVE:
            continue
        examined += 1
        groups[(assertion.subject_entity_id, assertion.predicate)].append(assertion)

    for (subject, predicate_name), group in sorted(groups.items()):
        if len(group) < 2:
            continue
        group.sort(key=_sort_key)
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                if _object_key(a) == _object_key(b):
                    # Same object from different evidence is corroboration, not
                    # conflict — exactly what independent claim ids are for.
                    continue
                kind, winner_id, reason = _pair_verdict(a, b)
                if kind is None:
                    continue
                if kind == LINK_SUPERSEDES:
                    loser = b if winner_id == a.claim_id else a
                    links.append(ClaimLink(winner_id, loser.claim_id,
                                           LINK_SUPERSEDES, reason))
                    # A claim already disputed stays disputed: an unresolved
                    # contradiction is not cured by a third claim outranking one
                    # side of it.
                    if status.get(loser.claim_id) != t.STATUS_DISPUTED:
                        status[loser.claim_id] = t.STATUS_SUPERSEDED
                else:
                    links.append(ClaimLink(a.claim_id, b.claim_id,
                                           LINK_CONTRADICTS, reason))
                    links.append(ClaimLink(b.claim_id, a.claim_id,
                                           LINK_CONTRADICTS, reason))
                    status[a.claim_id] = t.STATUS_DISPUTED
                    status[b.claim_id] = t.STATUS_DISPUTED

    report = ConflictReport(
        links=links, status_changes=status, examined=examined, groups=len(groups)
    )
    if links:
        logger.info(
            "Conflict pass: %d functional claims, %d disputed, %d superseded.",
            examined, len(report.disputed), len(report.superseded),
        )
    return report


# --------------------------------------------------------------------------- #
# Current-state eligibility
# --------------------------------------------------------------------------- #

# Everything a claim must satisfy before a later phase may derive a current-state
# relationship from it. Stated here, in one predicate, so the projection phase
# has nothing to decide: it projects what this admits and nothing else.
def is_current_state_eligible(assertion: Any, *, as_of: str | None = None) -> bool:
    """Whether this claim may become a derived current-state edge.

    Five conditions, each with a reason it cannot be dropped:

    1. **status is ``active``** — a disputed claim must not become a confident
       edge, and a superseded or retracted one is history.
    2. **the validity basis is stated or subject-period** — an undated claim is
       not evidence about *now*, and a document-date inference was never
       approved.
    3. **the window is open at ``as_of``** — a closed interval that ended is
       history, not current state.
    4. **the claim references entities, not literals**, for entity-valued
       predicates — a literal is a property, not a relationship.
    5. **the predicate is still in the vocabulary** — a claim made under a
       retired predicate is not projectable.

    Eligibility here is *necessary*, not sufficient: projection will additionally
    require that both entities are still claim-eligible, which only the entity
    store can answer.
    """
    from datetime import date

    if getattr(assertion, "status", None) != t.STATUS_ACTIVE:
        return False
    predicate = vocab.get(assertion.predicate)
    if predicate is None:
        return False
    if assertion.temporal_basis not in t.CURRENT_STATE_BASES:
        return False
    if predicate.entity_valued and not assertion.object_entity_id:
        return False

    window = temporal.window_of(assertion)
    if window.is_unknown:
        return False
    moment = as_of or date.today().isoformat()
    if window.valid_from and window.valid_from > moment:
        return False
    if window.valid_until and window.valid_until <= moment:
        return False
    return True


def current_state_claims(
    assertions: Iterable[Any], *, as_of: str | None = None
) -> list[Any]:
    """The claims a projection pass would be allowed to derive edges from."""
    return [a for a in assertions if is_current_state_eligible(a, as_of=as_of)]
