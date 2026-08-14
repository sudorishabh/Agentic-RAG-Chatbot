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

Decisions are ``AUTO`` / ``AMBIGUOUS`` / ``UNRESOLVED`` / ``NEW``. There is no
``REVIEW`` state: a review band is worth nothing without a reviewer, and this
repository has no such workflow, so a case that would have been queued is simply
left ``AMBIGUOUS`` — which is the safe direction anyway.

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
AMBIGUOUS = "AMBIGUOUS"
UNRESOLVED = "UNRESOLVED"
NEW = "NEW"
DECISIONS = (AUTO, AMBIGUOUS, UNRESOLVED, NEW)


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

    @property
    def linked(self) -> bool:
        return self.decision == AUTO and self.entity_id is not None


def _decide(
    mention: Any, *, decision: str, tier: str, reason: str,
    entity_id: str | None = None, scored: list[Scored] | None = None,
    score: float | None = None, gap: float | None = None,
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
        return _decide(
            mention, decision=AUTO, tier="tier0_identifier",
            reason="exact identifier match", entity_id=identifier_hits[0].entity_id,
            score=1.0, gap=1.0,
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
        return _decide(
            mention, decision=AUTO, tier=tier,
            reason="unique exact match" if exact else "unique alias match",
            entity_id=best.candidate.entity_id, scored=survivors,
            score=best.score, gap=gap,
        )

    # ------------------------------------------------------------------ #
    # Tiers 3 and 4 — several candidates survive, so score and margin decide.
    # ------------------------------------------------------------------ #
    clears_score = best.score >= thresholds.auto_score
    clears_margin = gap >= thresholds.auto_margin
    corroborated = best.corroborated or not thresholds.require_corroboration

    if clears_score and clears_margin and corroborated:
        tier = "tier3_corroborated" if best.corroborated else "tier4_scored"
        return _decide(
            mention, decision=AUTO, tier=tier,
            reason=f"score {best.score:.2f} >= {thresholds.auto_score} "
                   f"and margin {gap:.2f} >= {thresholds.auto_margin}",
            entity_id=best.candidate.entity_id, scored=survivors,
            score=best.score, gap=gap,
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
