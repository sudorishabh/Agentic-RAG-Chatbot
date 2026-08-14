"""Entity resolution: which canonical entity does this mention denote?

Named ``resolver`` rather than ``resolve`` because
``app.retrieval.structured.resolve`` already exists and means something else
(query-time fuzzy matching of a name against catalog facets).

Tiers, first decisive one wins
------------------------------
=======  ==========================================================  =========
Tier     Rule                                                        May link?
=======  ==========================================================  =========
0        exact identifier — a project code                           yes
1        exact canonical name, unambiguous                           yes
2        exact alias, unambiguous and autolinkable                   yes
3        name + corroborating context                                yes
4        scored candidate clearing score *and* margin                yes
5        LLM adjudication (flagged, OFF, not implemented)             no
=======  ==========================================================  =========

Decision states
---------------
``AUTO``         linked to a **canonical** identity: may carry claims, may be a
                 graph-retrieval target.
``PROVISIONAL``  linked to a name the corpus attests but has not shown to denote
                 one real-world thing. Groups sightings by name and asserts no
                 identity, so it may **not** carry claims. Person names from the
                 author facet are what this exists for: two different people
                 called "Arun Kumar" are one row, and calling that row a person
                 would be a false merge committed at seed time.
``AMBIGUOUS``    plausible but undecided.
``UNRESOLVED``   no candidate, or every candidate vetoed.
``NEW``          reserved for a deliberate promotion step; never written here.

There is no ``REVIEW`` state: a review band is worth nothing without a reviewer,
and this repository has no such workflow, so a case that would have been queued
is simply left ``AMBIGUOUS`` — which is the safe direction anyway.

The rule the whole design serves: **a false merge is worse than an unresolved
mention.** Every threshold, veto and margin here is set to fail toward
``UNRESOLVED``. The resolver never mints a canonical id because a name looked
similar; ``NEW`` is reserved for a later, deliberate promotion step and is
currently only *reported*, never written.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.knowledge.candidates import CandidateSet, EntityIndex, ResolutionContext, generate
from app.knowledge.scoring import THRESHOLDS, Scored, margin, score_candidates

logger = logging.getLogger(__name__)

# Bumped whenever a change here would decide the same mention differently.
# Stored on every decision row, so a rerun under new rules is distinguishable
# from the old verdict rather than silently replacing it.
RESOLVER_VERSION = "entity-resolve-v1"

AUTO = "AUTO"
# Linked, but to a *provisional* identity — a name the corpus attests without
# having shown it denotes one real-world thing. Useful for grouping sightings by
# name; explicitly NOT a canonical identity, so it may not carry claims or be a
# graph-retrieval target. Kept as its own state rather than folded into AUTO so
# that "we know who this is" and "we know what this is called" cannot be
# confused by anything reading the decision log.
PROVISIONAL = "PROVISIONAL"
AMBIGUOUS = "AMBIGUOUS"
UNRESOLVED = "UNRESOLVED"
NEW = "NEW"
DECISIONS = (AUTO, PROVISIONAL, AMBIGUOUS, UNRESOLVED, NEW)

# The states that assert a canonical identity. Claims and graph projection read
# this, never the raw `entity_id`.
CANONICAL_DECISIONS = (AUTO,)


@dataclass
class Decision:
    """One resolution verdict, with everything needed to explain it."""

    chunk_id: str
    start_offset: int
    end_offset: int
    surface_text: str
    normalized_text: str
    entity_type: str
    decision: str
    tier: str
    reason: str
    entity_id: str | None = None
    score: float | None = None
    margin: float | None = None
    candidate_audit: list[dict[str, Any]] = field(default_factory=list)
    resolver_version: str = RESOLVER_VERSION

    # False when the link is to a provisional identity. Carried on the decision
    # itself so a consumer never has to re-look-up the entity to find out.
    claim_eligible: bool = True

    @property
    def linked(self) -> bool:
        """Linked to anything at all, canonical or provisional."""
        return self.decision in (AUTO, PROVISIONAL) and self.entity_id is not None

    @property
    def canonical(self) -> bool:
        """Linked to an identity that may carry claims and answer graph queries."""
        return self.decision in CANONICAL_DECISIONS and self.entity_id is not None


def _link(
    mention: Any, candidate: Any, *, tier: str, reason: str,
    scored: list[Scored] | None = None, score: float | None = None,
    gap: float | None = None,
) -> "Decision":
    """A link, downgraded to PROVISIONAL when the target is not canonical.

    The single place a link is built, so the provisional distinction cannot be
    forgotten by a tier that decides to link.
    """
    eligible = getattr(candidate, "claim_eligible", True)
    return _decide(
        mention,
        decision=AUTO if eligible else PROVISIONAL,
        tier=tier,
        reason=reason if eligible else f"{reason} (provisional identity)",
        entity_id=candidate.entity_id, scored=scored, score=score, gap=gap,
        claim_eligible=eligible,
    )


def _decide(
    mention: Any, *, decision: str, tier: str, reason: str,
    entity_id: str | None = None, scored: list[Scored] | None = None,
    score: float | None = None, gap: float | None = None,
    claim_eligible: bool = True,
) -> Decision:
    return Decision(
        chunk_id=mention.chunk_id,
        start_offset=mention.start_offset,
        end_offset=mention.end_offset,
        surface_text=mention.surface_text,
        normalized_text=mention.normalized_text,
        entity_type=mention.entity_type,
        decision=decision,
        tier=tier,
        reason=reason,
        entity_id=entity_id,
        score=score,
        margin=gap,
        claim_eligible=claim_eligible,
        # Capped: the audit is for explaining a decision, not for storing the
        # whole index in every row.
        candidate_audit=[s.audit() for s in (scored or [])][:8],
    )


def resolve_mention(
    mention: Any,
    index: EntityIndex,
    context: ResolutionContext | None = None,
    *,
    candidate_set: CandidateSet | None = None,
) -> Decision:
    """Resolve one mention. Never raises; never invents an entity id."""
    context = context or ResolutionContext()
    thresholds = THRESHOLDS.get(mention.entity_type)
    if thresholds is None:
        return _decide(
            mention, decision=UNRESOLVED, tier="none",
            reason=f"no thresholds for type {mention.entity_type}",
        )

    candidates = candidate_set if candidate_set is not None else generate(mention, index)

    if not len(candidates):
        # No candidate is not a failure: it is the honest answer for a name the
        # CMS has never asserted. Promotion to a new entity is a separate,
        # deliberate act, so nothing is minted here.
        return _decide(
            mention, decision=UNRESOLVED, tier="none",
            reason="no candidate entity",
        )

    if candidates.truncated:
        # The surface matched more entities than a shortlist can hold, so it is
        # too common to be evidence. Choosing from a truncated list would turn
        # "undecidable" into an arbitrary pick.
        return _decide(
            mention, decision=AMBIGUOUS, tier="none",
            reason=f"more than {len(candidates)} candidates; surface too common",
        )

    # ------------------------------------------------------------------ #
    # Tier 0 — an authoritative identifier. A lookup, not an inference.
    # ------------------------------------------------------------------ #
    identifier_hits = [c for c in candidates if c.source == "identifier"]
    if identifier_hits:
        return _link(
            mention, identifier_hits[0], tier="tier0_identifier",
            reason="exact identifier match", score=1.0, gap=1.0,
        )

    scored = score_candidates(mention, candidates, context)
    survivors = [s for s in scored if not s.vetoed]
    if not survivors:
        reasons = sorted({v for s in scored for v in s.vetoes})
        return _decide(
            mention, decision=UNRESOLVED, tier="veto",
            reason="every candidate vetoed: " + ", ".join(reasons),
            scored=scored,
        )

    best = survivors[0]
    gap = margin(survivors)

    # ------------------------------------------------------------------ #
    # Tiers 1 and 2 — an exact name or alias that denotes exactly one entity.
    # A single surviving candidate means the margin is the score itself.
    # ------------------------------------------------------------------ #
    if len(survivors) == 1 and best.candidate.source in ("exact_name", "alias"):
        exact = best.candidate.source == "exact_name"
        tier = "tier1_exact_name" if exact else "tier2_alias"
        # PERSON still needs corroboration even here. One seeded "Ritu Sharma"
        # does not mean every "Ritu Sharma" in the corpus is that person - it
        # means the corpus has only met one so far.
        if thresholds.require_corroboration and not best.corroborated:
            return _decide(
                mention, decision=AMBIGUOUS, tier=tier,
                reason="unique name match but no corroborating context",
                scored=survivors, score=best.score, gap=gap,
            )
        return _link(
            mention, best.candidate, tier=tier,
            reason="unique exact match" if exact else "unique alias match",
            scored=survivors, score=best.score, gap=gap,
        )

    # ------------------------------------------------------------------ #
    # Tiers 3 and 4 — several candidates survive, so score and margin decide.
    # ------------------------------------------------------------------ #
    clears_score = best.score >= thresholds.auto_score
    clears_margin = gap >= thresholds.auto_margin
    corroborated = best.corroborated or not thresholds.require_corroboration

    if clears_score and clears_margin and corroborated:
        tier = "tier3_corroborated" if best.corroborated else "tier4_scored"
        return _link(
            mention, best.candidate, tier=tier,
            reason=f"score {best.score:.2f} >= {thresholds.auto_score} "
                   f"and margin {gap:.2f} >= {thresholds.auto_margin}",
            scored=survivors, score=best.score, gap=gap,
        )

    if best.score >= thresholds.ambiguous_floor:
        # Plausible but undecided. Recorded as ambiguous rather than linked,
        # which is the whole point: two people with one name land here.
        missing = []
        if not clears_score:
            missing.append(f"score {best.score:.2f} < {thresholds.auto_score}")
        if not clears_margin:
            missing.append(f"margin {gap:.2f} < {thresholds.auto_margin}")
        if not corroborated:
            missing.append("no corroborating context")
        return _decide(
            mention, decision=AMBIGUOUS, tier="tier4_scored",
            reason="; ".join(missing), scored=survivors,
            score=best.score, gap=gap,
        )

    return _decide(
        mention, decision=UNRESOLVED, tier="tier4_scored",
        reason=f"best score {best.score:.2f} below floor "
               f"{thresholds.ambiguous_floor}",
        scored=survivors, score=best.score, gap=gap,
    )


def resolve_mentions(
    mentions: list[Any], index: EntityIndex,
    context: ResolutionContext | None = None,
) -> list[Decision]:
    """Resolve a chunk's mentions, sharing co-occurrence context between them.

    Co-mentions are collected across the chunk, but a mention never contributes
    to its *own* context: a candidate is always the same type as its mention, so
    a name corroborating itself is circular. It is recorded as a weak score
    feature only, and never satisfies the corroboration requirement (see
    ``scoring.CORROBORATING``).
    """
    context = context or ResolutionContext()
    by_type: dict[str, list[str]] = {}
    for mention in mentions:
        by_type.setdefault(mention.entity_type, []).append(mention.normalized_text)

    decisions: list[Decision] = []
    for mention in mentions:
        others = ResolutionContext(
            document_id=context.document_id,
            cms_names=context.cms_names,
            co_mentions={
                entity_type: {
                    name
                    for name in names
                    if not (
                        entity_type == mention.entity_type
                        and name == mention.normalized_text
                    )
                }
                for entity_type, names in by_type.items()
            },
        )
        decisions.append(resolve_mention(mention, index, others))
    return decisions
