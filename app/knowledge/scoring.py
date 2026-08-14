"""Candidate scoring: features, vetoes, and per-type thresholds.

Scoring answers "how much does the evidence support *this* candidate", never
"which candidate wins" — that is the resolver's decision, and keeping them apart
is what lets the thresholds be argued about separately from the features.

Two things carry the safety property that a false merge is worse than leaving a
mention unresolved:

**Vetoes beat scores.** A veto is evidence *against* identity, and no amount of
name similarity overrides it. "Raj Sharma — TERI" and "Raj Sharma — IIT Delhi"
score identically on name and stay two entities, because the organization
context contradicts.

**Thresholds are per type.** PERSON is the open-world type in this corpus — 8
authoritative CMS records against ~931 seeded names, most of them derived from a
noisy author facet — so it demands a higher score, a wider margin, and at least
one corroborating feature that is not the name itself. ORGANIZATION and PROJECT
are grounded in CMS metadata and can be linked on the name alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.knowledge.normalize import is_initials_only

# A project title has to look like a name before it can identify a project.
# Same thresholds the extractor uses to decide what may be matched in text
# (app.knowledge.gazetteer), restated here because resolution can reach an
# entity by its canonical name without any alias flag being consulted.
_MIN_PROJECT_TOKENS = 3
_MIN_PROJECT_CHARS = 12


def is_specific_project_name(normalized: str) -> bool:
    """Whether a project title is distinctive enough to denote that project."""
    return (
        len(normalized.split()) >= _MIN_PROJECT_TOKENS
        and len(normalized) >= _MIN_PROJECT_CHARS
    )

# --------------------------------------------------------------------------- #
# Thresholds
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TypeThresholds:
    """What a candidate must clear, for one entity type."""

    auto_score: float
    auto_margin: float
    ambiguous_floor: float
    # Whether a link needs evidence beyond the name matching. PERSON does: a
    # name alone is exactly the false-merge case, and this corpus has ~975
    # author strings full of shared surnames.
    require_corroboration: bool


# PERSON is deliberately the strictest row. The margin is what stops a link when
# two people share a name: without a clear winner there is no link at all.
THRESHOLDS: dict[str, TypeThresholds] = {
    "PERSON": TypeThresholds(
        auto_score=0.92, auto_margin=0.20, ambiguous_floor=0.55,
        require_corroboration=True,
    ),
    "ORGANIZATION": TypeThresholds(
        auto_score=0.85, auto_margin=0.12, ambiguous_floor=0.50,
        require_corroboration=False,
    ),
    "PROJECT": TypeThresholds(
        auto_score=0.85, auto_margin=0.12, ambiguous_floor=0.50,
        require_corroboration=False,
    ),
}

# Feature weights. Not probabilities: an ordering chosen so that an exact name
# plus one corroborating signal clears AUTO, and an exact name alone does not
# for PERSON.
_WEIGHTS = {
    "f_exact_name": 0.60,
    "f_alias": 0.50,
    "f_initials_only_block": 0.15,
    "f_cms_asserted": 0.35,
    "f_co_mention": 0.15,
    "f_authoritative": 0.10,
    "f_alias_unique": 0.10,
}

# Features that count as corroboration — evidence that is *not* the name.
#
# Only `f_cms_asserted` qualifies, and the omission of `f_co_mention` is
# deliberate. A candidate is always the same entity type as its mention, so a
# co-mention of that candidate's name *is* the mention's own name appearing
# again: repetition, not evidence. Treating it as corroboration silently
# disabled PERSON's whole safety requirement — every name auto-linked to itself.
#
# Real cross-entity corroboration ("this person beside their employer") needs a
# person-to-organization relationship, which is the claim layer's to supply. It
# does not exist yet, so PERSON corroboration currently means exactly one thing:
# this document's own CMS metadata names this person.
CORROBORATING = ("f_cms_asserted",)


@dataclass
class Scored:
    """A candidate with its features, score and any veto."""

    candidate: Any
    features: dict[str, float] = field(default_factory=dict)
    vetoes: list[str] = field(default_factory=list)
    score: float = 0.0

    @property
    def vetoed(self) -> bool:
        return bool(self.vetoes)

    @property
    def corroborated(self) -> bool:
        return any(self.features.get(name) for name in CORROBORATING)

    def audit(self) -> dict[str, Any]:
        """The record kept for every decision, so it can be explained later."""
        return {
            "entity_id": self.candidate.entity_id,
            "canonical_name": self.candidate.canonical_name,
            "source": self.candidate.source,
            "trust": self.candidate.trust,
            "score": round(self.score, 4),
            "features": {k: round(v, 4) for k, v in self.features.items() if v},
            "vetoes": list(self.vetoes),
        }


# --------------------------------------------------------------------------- #
# Vetoes — evidence against identity
# --------------------------------------------------------------------------- #

def _vetoes(mention: Any, candidate: Any, context: Any) -> list[str]:
    found: list[str] = []

    # A type mismatch cannot be a match at all. Candidate generation is typed,
    # so this only fires on a corrupted index — but it is the cheapest possible
    # guard against the worst possible error.
    if candidate.entity_type != mention.entity_type:
        found.append("v_type_conflict")

    # The alias that produced this candidate is shared with another entity, or
    # is too generic to link on. Data-driven: the moment a second entity claims
    # the surface, it stops linking for everyone.
    if candidate.is_ambiguous:
        found.append("v_ambiguous_alias")
    elif candidate.source == "alias" and not candidate.autolink:
        found.append("v_alias_not_autolinkable")

    # An initials-only mention names nobody in particular. "A. K." must never
    # link, however many candidates share those initials.
    if mention.entity_type == "PERSON" and is_initials_only(mention.normalized_text):
        found.append("v_initials_only")

    # A project whose title is a short descriptive phrase is not identifiable by
    # that phrase. "Steel", "Summary" and "Study of Studies" are all real titles
    # in this CMS, and linking them from text would attach every mention of the
    # material to a project. Phase 4 applies the same rule when deciding what
    # may be *extracted*; it has to hold here too, because an exact match
    # against the entity's own canonical name never consults the alias flags.
    # The project *code* is unaffected — it resolves at Tier 0, before scoring.
    if (
        mention.entity_type == "PROJECT"
        and candidate.source in ("exact_name", "alias")
        and not is_specific_project_name(candidate.normalized_name)
    ):
        found.append("v_project_name_not_specific")

    # The document's CMS metadata names a *different* organization of the same
    # kind, and none matching this candidate. This is the "Raj Sharma — TERI"
    # vs "Raj Sharma — IIT Delhi" guard: contradictory context beats a perfect
    # name match.
    if mention.entity_type == "PERSON":
        asserted = context.cms_names.get("PERSON", set())
        if asserted and candidate.normalized_name not in asserted:
            found.append("v_cms_names_someone_else")

    return found


# --------------------------------------------------------------------------- #
# Features
# --------------------------------------------------------------------------- #

def _features(mention: Any, candidate: Any, context: Any, *, alias_unique: bool) -> dict[str, float]:
    features: dict[str, float] = {}
    normalized = mention.normalized_text

    if candidate.source == "identifier":
        # Nothing to weigh: the identifier is a database invariant, handled by
        # the resolver's Tier 0 before scoring is reached.
        features["f_exact_name"] = 1.0
        return features

    if candidate.normalized_name == normalized:
        features["f_exact_name"] = _WEIGHTS["f_exact_name"]
    elif candidate.source == "alias":
        features["f_alias"] = _WEIGHTS["f_alias"]
    elif candidate.source == "blocked":
        # Shared initials only. Deliberately small: it is a reason to look, not
        # a reason to link.
        features["f_initials_only_block"] = _WEIGHTS["f_initials_only_block"]

    if context.asserts(candidate.entity_type, candidate.normalized_name):
        features["f_cms_asserted"] = _WEIGHTS["f_cms_asserted"]
    if context.co_mentioned(candidate.entity_type, candidate.normalized_name):
        features["f_co_mention"] = _WEIGHTS["f_co_mention"]
    if candidate.trust == "authoritative":
        features["f_authoritative"] = _WEIGHTS["f_authoritative"]
    if alias_unique and candidate.source == "alias" and candidate.autolink:
        features["f_alias_unique"] = _WEIGHTS["f_alias_unique"]

    return features


def score_candidates(mention: Any, candidate_set: Any, context: Any) -> list[Scored]:
    """Score every candidate, highest first. Vetoed candidates score 0.

    Sorted deterministically — score, then entity_id — so repeated resolution of
    the same mention produces the same ranking and therefore the same decision.
    """
    alias_unique = sum(1 for c in candidate_set if c.source == "alias") == 1
    scored: list[Scored] = []
    for candidate in candidate_set:
        vetoes = _vetoes(mention, candidate, context)
        features = _features(mention, candidate, context, alias_unique=alias_unique)
        entry = Scored(candidate=candidate, features=features, vetoes=vetoes)
        entry.score = 0.0 if vetoes else min(1.0, sum(features.values()))
        scored.append(entry)
    scored.sort(key=lambda s: (-s.score, s.candidate.entity_id))
    return scored


def margin(scored: list[Scored]) -> float:
    """Gap between the best candidate and the runner-up.

    The single most important number for PERSON: two people sharing a name score
    identically, so the margin collapses to zero and the link is refused. Score
    alone would happily link either one.
    """
    if not scored:
        return 0.0
    if len(scored) == 1:
        return scored[0].score
    return scored[0].score - scored[1].score
