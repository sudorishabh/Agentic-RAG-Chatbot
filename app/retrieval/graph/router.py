"""Decide whether a question is graph-shaped, and which template answers it.

Deterministic on purpose. A model *may* later choose a ``template_id`` — that is
the design the security model allows — but nothing here needs one, and a
pattern-matched route is testable, free, and cannot be talked into selecting a
template by the question text. What a model must never do is write the query,
and no code path here would let it.

Routing needs two things to agree:

1. **a resolved entity** — the question names something the knowledge layer has
   a canonical, claim-eligible identity for. Resolution reuses the *same*
   resolver the ingest path uses, so a name that is ambiguous there is ambiguous
   here, and an ambiguous entity yields no route rather than a guess;
2. **a relational shape** — the question asks about a relationship, not a topic.

Either alone is not enough. "Tell me about TERI" resolves an entity and asks
nothing relational; "who funds research" is relational and names nobody.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.retrieval.graph import templates as reg

logger = logging.getLogger(__name__)

# Phrases that mark a question as asking about *the past* rather than the
# present. A historical question must not be answered from current-state edges,
# because those deliberately exclude everything that has ended.
_HISTORICAL_MARKERS = re.compile(
    r"\b(?:used to|previously|formerly|history|historical|past|"
    r"between\s+\d{4}|in\s+(?:19|20)\d{2}|as of|back then|earlier|"
    r"who led .* in |before\s+(?:19|20)\d{2}|ever)\b",
    re.IGNORECASE,
)

_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")


@dataclass(frozen=True)
class Route:
    """A selected template and its typed parameters."""

    template_id: str
    parameters: dict[str, Any]
    entity_id: str
    entity_type: str
    entity_name: str
    mode: str
    reason: str
    confidence: float = 0.0

    @property
    def is_historical(self) -> bool:
        return self.mode == reg.MODE_HISTORICAL


@dataclass
class RoutingOutcome:
    """Why routing did or did not produce a route."""

    route: Route | None = None
    reason: str = ""
    # Entities the question named but could not be resolved to one identity.
    ambiguous: list[str] = field(default_factory=list)

    @property
    def routed(self) -> bool:
        return self.route is not None


# Question shape -> (template for an entity of this type, mode). Ordered: the
# first pattern that matches a question wins, so the more specific multi-hop
# shapes are listed before the single-hop ones they contain.
_PATTERNS: tuple[tuple[re.Pattern[str], dict[str, str], str], ...] = (
    (
        # "who leads projects funded by X" — the four-hop case.
        re.compile(
            r"\b(?:who|which people|people)\b.{0,40}\b(?:lead|leads|leading|led|"
            r"head|heads|run|runs)\b.{0,40}\b(?:project|programme|program)s?\b"
            r".{0,30}\b(?:funded|financed|sponsored|supported)\b",
            re.IGNORECASE,
        ),
        {"ORGANIZATION": "people_leading_projects_funded_by_org"},
        "people leading projects funded by an organization",
    ),
    (
        re.compile(
            r"\b(?:what|which|list)\b.{0,30}\b(?:project|programme|program)s?\b"
            r".{0,30}\b(?:funded|financed|sponsored|supported)\b",
            re.IGNORECASE,
        ),
        {"ORGANIZATION": "projects_funded_by_org"},
        "projects funded by an organization",
    ),
    (
        re.compile(
            r"\b(?:who|which organisations?|which organizations?|what)\b"
            r".{0,30}\b(?:funds?|funded|finances?|financed|sponsors?|sponsored)\b",
            re.IGNORECASE,
        ),
        {"PROJECT": "funders_of_project", "ORGANIZATION": "projects_funded_by_org"},
        "funders of a project",
    ),
    (
        re.compile(
            r"\b(?:what|which|list)\b.{0,30}\b(?:project|programme|program)s?\b"
            r".{0,30}\b(?:lead|leads|leading|led|head|heads|run|runs)\b",
            re.IGNORECASE,
        ),
        {"PERSON": "projects_led_by_person"},
        "projects led by a person",
    ),
    (
        re.compile(
            r"\b(?:who|which person)\b.{0,30}\b(?:lead|leads|leading|led|head|"
            r"heads|runs?)\b",
            re.IGNORECASE,
        ),
        {"PROJECT": "project_history", "PERSON": "projects_led_by_person"},
        "who leads a project",
    ),
    (
        re.compile(
            r"\b(?:work|works|worked|working|employed|employment)\b.{0,20}\bat\b",
            re.IGNORECASE,
        ),
        {"PERSON": "person_works_at"},
        "where a person works",
    ),
    (
        re.compile(
            r"\b(?:member|members|membership|belongs?|part of|sits? on)\b",
            re.IGNORECASE,
        ),
        {"PERSON": "person_member_of"},
        "a person's memberships",
    ),
    (
        re.compile(
            r"\b(?:history|historical|timeline|over time|past)\b", re.IGNORECASE
        ),
        {
            "PROJECT": "project_history",
            "PERSON": "person_history",
            "ORGANIZATION": "org_funding_history",
        },
        "the history of an entity",
    ),
)

# Historical counterparts, used when a question is relational *and* about the
# past. Falling back to a current-state template there would silently answer a
# different question.
_HISTORICAL_EQUIVALENT = {
    "projects_funded_by_org": "org_funding_history",
    "people_leading_projects_funded_by_org": "org_funding_history",
    "funders_of_project": "project_history",
    "projects_led_by_person": "person_history",
    "person_works_at": "person_history",
    "person_member_of": "person_history",
}


# Tiers that mean "exactly one candidate survived scoring". Anything else that
# comes back AMBIGUOUS had a genuine choice to make, and a query must not make
# it silently.
_SINGLE_CANDIDATE_TIERS = ("tier1_exact_name", "tier2_alias")

# Trust levels a query may target. `provisional` is excluded: those identities
# are not in the graph, so routing to one could only ever return nothing.
_ROUTABLE_TRUST = ("authoritative", "pi_attested", "derived")


@dataclass(frozen=True)
class _QueryMatch:
    """A resolver decision accepted for routing, canonical or query-only."""

    entity_id: str
    entity_type: str
    surface_text: str
    score: float


def _accept_unique_match(decision: Any) -> _QueryMatch | None:
    """Accept a name the resolver left AMBIGUOUS *only* for lack of context.

    PERSON resolution requires corroboration — a co-occurring employer or
    project — because one seeded "Ritu Sharma" does not make every "Ritu Sharma"
    that person. During ingestion that rule is essential: a wrong link is
    written into the graph and outlives the mistake.

    A question is a one-line document. It has no co-mentions by construction, so
    that same rule rejects **every** person question, which is why the benchmark
    showed leadership queries never routing. The rule is right; applying it
    unchanged to a query is not.

    So the query side accepts a decision when, and only when, the resolver found
    *exactly one* surviving candidate and withheld it purely for missing
    context. Uniqueness in the entity store is the corroboration. Two candidates,
    any veto, an ineligible entity or a provisional identity still decline —
    a wrong answer is worse than falling back to ordinary retrieval.

    The resolver is not modified; this reads its audit trail and decides what a
    *query* may do with it.
    """
    if decision.decision != "AMBIGUOUS" or decision.tier not in _SINGLE_CANDIDATE_TIERS:
        return None
    if not decision.claim_eligible:
        return None
    audit = decision.candidate_audit or []
    if len(audit) != 1:
        return None
    candidate = audit[0]
    if candidate.get("vetoes"):
        return None
    if candidate.get("trust") not in _ROUTABLE_TRUST:
        return None
    entity_id = candidate.get("entity_id")
    if not entity_id:
        return None
    return _QueryMatch(
        entity_id=entity_id,
        entity_type=decision.entity_type,
        surface_text=decision.surface_text,
        score=decision.score or 0.0,
    )


def _resolve_entities(question: str, index: Any) -> tuple[list[Any], list[str]]:
    """Entities named in the question, via the ingest-path resolver.

    Reusing ``app.knowledge`` extraction and resolution rather than a query-time
    matcher is what keeps one name meaning one thing on both sides: a surface
    too ambiguous to link during ingestion is equally unusable here. The one
    query-side departure is `_accept_unique_match`, and it is narrow.
    """
    from app.knowledge.candidates import ResolutionContext
    from app.knowledge.extract import extract_mentions
    from app.knowledge.gazetteer import get_gazetteer
    from app.knowledge.resolver import resolve_mention

    mentions = extract_mentions(
        question, chunk_id="query", document_id="query",
        gazetteer=get_gazetteer(),
    )
    resolved: list[Any] = []
    ambiguous: list[str] = []
    context = ResolutionContext(document_id="query")
    for mention in mentions:
        decision = resolve_mention(mention, index, context)
        if decision.canonical and decision.entity_id:
            resolved.append(decision)
            continue
        accepted = _accept_unique_match(decision)
        if accepted is not None:
            resolved.append(accepted)
        elif decision.decision in ("AMBIGUOUS", "PROVISIONAL"):
            ambiguous.append(mention.surface_text)
    return resolved, ambiguous


def route(
    question: str, *, index: Any = None, as_of: str | None = None
) -> RoutingOutcome:
    """Choose a template for a question, or explain why not."""
    if not question or not question.strip():
        return RoutingOutcome(reason="empty question")

    if index is None:
        from app.knowledge.candidates import EntityIndex

        index = EntityIndex.load()

    resolved, ambiguous = _resolve_entities(question, index)
    if not resolved:
        return RoutingOutcome(
            reason=(
                "no entity in the question resolved to a canonical identity"
                if not ambiguous
                else "the entity named is ambiguous"
            ),
            ambiguous=ambiguous,
        )

    historical = bool(_HISTORICAL_MARKERS.search(question))
    year = _YEAR.search(question)

    for pattern, by_type, reason in _PATTERNS:
        if not pattern.search(question):
            continue
        for decision in resolved:
            template_id = by_type.get(decision.entity_type)
            if template_id is None:
                continue
            if historical:
                template_id = _HISTORICAL_EQUIVALENT.get(template_id, template_id)
            template = reg.TEMPLATES[template_id]
            params: dict[str, Any] = {"entity_id": decision.entity_id}
            # "as of" needs an explicit date; a year in the question supplies
            # one, and without either the template is not usable.
            if "as_of" in template.parameters:
                moment = as_of or (f"{year.group(1)}-01-01" if year else None)
                if moment is None:
                    continue
                params["as_of"] = moment
            return RoutingOutcome(
                route=Route(
                    template_id=template_id, parameters=params,
                    entity_id=decision.entity_id,
                    entity_type=decision.entity_type,
                    entity_name=decision.surface_text,
                    mode=template.mode, reason=reason,
                    confidence=decision.score or 0.0,
                ),
                reason=reason,
                ambiguous=ambiguous,
            )

    return RoutingOutcome(
        reason="entity resolved but the question is not relational",
        ambiguous=ambiguous,
    )
