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

Two ways to satisfy the second condition
----------------------------------------
**The planner**, tried first. It reads a predicate out of the closed vocabulary
(:mod:`app.retrieval.graph.intent`), a direction out of that predicate's
declared domain and range, and a validity window out of the question's own
words, then asks :mod:`app.retrieval.graph.plans` for a reviewed template to
bind them to. Every approved predicate is reachable this way, in both directions
the schema allows, over any period — which is the point: a predicate approved
into the vocabulary becomes askable without anything being added here.

**The pattern table**, kept below as a fallback. It maps a handful of memorised
question shapes onto template ids, and it is what routing used to be *entirely*.
Three of the seven approved predicates appear nowhere in it, which is how the
graph came to hold claims no question could reach. It survives for phrasings the
cue vocabulary has not learnt, and because narrowing a route is a cheaper
mistake than losing one.

Masking
-------
Cues are matched against the question with the resolved entity spans blanked
out. A cue inside a name is part of the name: this corpus is full of
organizations called "Department of ...", and "department" is exactly the word
that would otherwise mark the question as being about organizational structure.
See :func:`_mask_entities`.
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
    # The capability class of a schema-derived plan. Empty for a route from the
    # legacy pattern table, whose class the policy layer still looks up by
    # template id — which is what keeps an existing `GRAPH_ROUTING_CLASSES`
    # meaning exactly what it meant.
    query_class: str = ""
    # The plan behind the route, when one produced it. Carried for metrics and
    # explanation; nothing downstream needs it to execute.
    plan: Any = None

    @property
    def is_historical(self) -> bool:
        return self.mode == reg.MODE_HISTORICAL

    @property
    def predicates(self) -> tuple[str, ...]:
        return tuple(getattr(self.plan, "predicates", ()) or ())


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


# The provenance stamp `approved_aliases` puts on the mentions it produces. A
# query-side acceptance below is allowed only for those: it is the proof that the
# surface was an *exact* match against a reviewed, unambiguous, autolinkable
# alias of an active claim-eligible entity, rather than a heuristic hit in prose.
_APPROVED_ALIAS_VERSION = "approved-alias-v1"

# The one veto a *query* may look past, and only under `_accept_approved_project`.
_QUERY_ACCEPTABLE_VETOES = frozenset({"v_project_name_not_specific"})


def _accept_approved_project(decision: Any, mention: Any) -> "_QueryMatch | None":
    """Accept a short project title that a reviewed alias matched exactly.

    ``v_project_name_not_specific`` rejects a project whose title is under three
    tokens or twelve characters, because "Steel", "Summary" and "Study of
    Studies" are all real titles in this CMS and linking them *from prose* would
    attach every mention of the material to a project. That reasoning is sound
    and the veto is left exactly as it is — including for ingestion, which is
    where a wrong link becomes permanent.

    A question is not prose. "Who led Green Jobs?" is someone naming a thing, and
    the corpus has four such projects the veto made unreachable: WEO 2007,
    HI-AWARE, Green Jobs, Water4Crops — each an authoritative CMS project node
    with a reviewed, unambiguous, autolinkable title alias.

    So this reads the resolver's audit trail and decides what a *query* may do
    with it, exactly as `_accept_unique_match` does for PERSON. The conditions
    are deliberately narrow, and every one of them is load-bearing:

    * the mention came from the approved-alias pass, so the surface matched a
      reviewed alias exactly rather than being spotted in text;
    * exactly one candidate survived, so there is nothing to choose between;
    * its **only** veto is the specificity one — any other veto (ambiguous
      alias, type conflict, non-autolinkable) still declines;
    * the entity is an ``authoritative`` PROJECT and still claim-eligible.

    The resolver is not modified, ingestion is unaffected, and a surface too
    generic to have survived `approved_aliases._admissible` never gets here.
    """
    if decision.entity_type != "PROJECT":
        return None
    if getattr(mention, "extractor_version", None) != _APPROVED_ALIAS_VERSION:
        return None
    if not decision.claim_eligible:
        return None
    audit = decision.candidate_audit or []
    if len(audit) != 1:
        return None
    candidate = audit[0]
    vetoes = set(candidate.get("vetoes") or ())
    if not vetoes or vetoes - _QUERY_ACCEPTABLE_VETOES:
        return None
    if candidate.get("trust") != "authoritative":
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


def _resolve_entities(
    question: str, index: Any
) -> tuple[list[Any], list[str], list[tuple[int, int]], list[tuple[int, int]]]:
    """Entities named in the question, their spans, and any ambiguous surface.

    Reusing ``app.knowledge`` extraction and resolution rather than a query-time
    matcher is what keeps one name meaning one thing on both sides: a surface
    too ambiguous to link during ingestion is equally unusable here. The one
    query-side departure is `_accept_unique_match`, and it is narrow.

    Returns two span lists, because they answer different questions and mixing
    them up is a real bug: ``spans`` covers *every* mention and is what masking
    blanks out, while ``resolved_spans`` is index-aligned with ``resolved`` and is
    where each anchor actually sits. An unresolved mention still has to be
    masked — a cue inside a name is part of the name whether or not the name
    resolved — so the first list is strictly the longer one.
    """
    from app.knowledge.candidates import ResolutionContext
    from app.knowledge.extract import extract_mentions
    from app.knowledge.gazetteer import get_gazetteer
    from app.knowledge.resolver import resolve_mention
    from app.retrieval.understanding.approved_aliases import lookup_mentions

    mentions = extract_mentions(
        question, chunk_id="query", document_id="query",
        gazetteer=get_gazetteer(),
    )
    # Second pass, query-side only: the reviewed alias table. The gazetteer is
    # built from raw CMS metadata and needs conservative heuristics against
    # prose — a minimum token count, a minimum length, case-sensitive matching
    # for short surfaces — and those heuristics silently drop whole classes of
    # ordinary phrasing in a *question*: acronyms ("ADB"), lower case ("dr alok
    # adholeya"), short authoritative titles ("WEO 2007", "HI-AWARE"), and
    # punctuation variants of a stored name. Measured: none of those produced a
    # mention at all, so resolution was never reached.
    #
    # This adds candidates from `documents_entity_alias`, where every row belongs
    # to a deliberately seeded entity and carries the `autolink` / `is_ambiguous`
    # flags review produced. It changes nothing about *identity*: each mention
    # goes through the same `resolve_mention` below, so trust, eligibility and
    # every veto still decide. Only spans the gazetteer did not already cover are
    # added, so its findings always win.
    covered = [(m.start_offset, m.end_offset) for m in mentions]
    for extra in lookup_mentions(question, chunk_id="query", document_id="query"):
        if any(
            extra.start_offset < end and start < extra.end_offset
            for start, end in covered
        ):
            continue
        covered.append((extra.start_offset, extra.end_offset))
        mentions.append(extra)
    resolved: list[Any] = []
    ambiguous: list[str] = []
    spans: list[tuple[int, int]] = []
    resolved_spans: list[tuple[int, int]] = []
    context = ResolutionContext(document_id="query")
    for mention in mentions:
        span = (mention.start_offset, mention.end_offset)
        spans.append(span)
        decision = resolve_mention(mention, index, context)
        if decision.canonical and decision.entity_id:
            resolved.append(decision)
            resolved_spans.append(span)
            continue
        accepted = _accept_unique_match(decision) or _accept_approved_project(
            decision, mention
        )
        if accepted is not None:
            resolved.append(accepted)
            resolved_spans.append(span)
        elif decision.decision in ("AMBIGUOUS", "PROVISIONAL"):
            ambiguous.append(mention.surface_text)
    return resolved, ambiguous, spans, resolved_spans


def _mask_entities(question: str, spans: list[tuple[int, int]]) -> str:
    """Blank out the names, leaving the words *around* them.

    Without this the question's own subject supplies its own relationship. This
    corpus is full of organizations called "Department of Biotechnology",
    "National Centre for ...", "Energy and Resources Institute" — and
    "department", "centre" and "unit" are exactly the words that mark a
    ``PARENT_OF`` question. Matching cues against the raw text made every
    question about such an organization look like a question about its internal
    structure, and the same names contain years ("Highlights 2008-11") that read
    as validity windows.

    A cue inside a recognised name is part of the name. Spans are replaced with
    spaces rather than removed so every remaining offset still indexes into the
    original question, which is what keeps the "in the order the question names
    them" rule below meaningful.
    """
    if not spans:
        return question
    text = list(question)
    for start, end in spans:
        for i in range(max(0, start), min(len(text), end)):
            text[i] = " "
    return "".join(text)


def _nearest_first(relational: Any, span: tuple[int, int]) -> tuple[str, ...]:
    """The named predicates, the one closest to the anchor entity first.

    Distance is measured between the predicate's cue and the nearer edge of the
    anchor's own span, so a cue on either side of the name counts equally:
    "projects funded by X" and "X's funded projects" both put FUNDED_BY next to
    the anchor. Ties keep the question's own order, which is what the single-cue
    and two-cue cases already relied on.

    A predicate whose offset is unknown sorts last rather than being dropped — it
    is still a legal candidate, just not one this ordering can speak for.
    """
    offsets = getattr(relational, "offsets", None) or {}
    start, end = span

    def distance(name: str) -> tuple[int, int]:
        offset = offsets.get(name)
        if offset is None:
            return (1, 0)
        return (0, 0 if start <= offset <= end else min(
            abs(offset - start), abs(offset - end)
        ))

    return tuple(
        sorted(relational.predicates, key=lambda name: distance(name))
    )


def _plan_route(
    question: str,
    resolved: list[Any],
    resolved_spans: list[tuple[int, int]],
    *,
    as_of: str | None,
) -> Route | None:
    """The schema-aware path: predicate + direction + validity window.

    Tried before the pattern table below, and in practice it answers everything
    the table did and a good deal it could not. The table remains because it
    encodes two things worth keeping — the cheap derived-edge traversals, which
    a plan selects by name, and a fallback for any phrasing the cue vocabulary
    has not learnt yet.

    Nothing here composes a query. It picks a predicate from the closed
    vocabulary, a direction from that predicate's declared domain and range, a
    validity window from the question's own words, and hands all three to
    ``plans``, which selects a reviewed template and binds them as parameters.
    """
    from app.retrieval.graph import intent as qi
    from app.retrieval.graph import plans

    temporal = qi.read_temporal(question)
    if as_of and temporal.kind in (qi.TEMPORAL_UNSPECIFIED, qi.TEMPORAL_CURRENT):
        # An explicit caller-supplied moment beats an inferred tense: this is
        # how a benchmark or a replay asks what was true on a given date.
        temporal = qi.TemporalIntent(
            qi.TEMPORAL_AS_OF, as_of, qi._day_after(as_of), f"as of {as_of}"
        )
    relational = qi.read_relational(question)

    def _as_route(plan: Any, decision: Any) -> Route:
        return Route(
            template_id=plan.template_id, parameters=dict(plan.parameters),
            entity_id=decision.entity_id, entity_type=decision.entity_type,
            entity_name=decision.surface_text, mode=plan.mode,
            reason=plan.reason, confidence=decision.score or 0.0,
            query_class=plan.capability, plan=plan,
        )

    # Two hops first: a question naming two relationships is asking about the
    # chain between them, and answering only the nearer one answers something
    # else.
    #
    # The schema decides which orderings are *legal*; among those, the chain is
    # built outward from the anchor, so the first hop is the relationship named
    # nearest the anchor entity. Relying on the schema alone was not enough, and
    # the failure was measured: "Which investigators lead **work** granted by the
    # Ministry of Environment and Forests?" names three predicates, because
    # "work" is a WORKS_AT cue. Iterating in cue order reached
    # (WORKS_AT, LED_BY) — legal, since an organization may be an employer and a
    # person may lead a project — and returned it, so the query asked for
    # employees of the Ministry who lead projects. The corpus holds no WORKS_AT
    # claim at all, so the answer was zero rows, while the chain the question
    # actually asked for (FUNDED_BY then LED_BY) held ten.
    #
    # Ordering by distance to the anchor fixes that without narrowing any cue
    # vocabulary: "granted" sits next to the Ministry, "work" and "lead" do not.
    # It also reproduces every chain that already worked, where the relationship
    # adjacent to the anchor was the correct first hop anyway.
    if len(relational.predicates) > 1:
        for decision, span in zip(resolved, resolved_spans):
            for first in _nearest_first(relational, span):
                for second in relational.predicates:
                    plan = plans.two_hop(
                        entity_id=decision.entity_id,
                        entity_type=decision.entity_type,
                        first=first, second=second, temporal=temporal,
                    )
                    if plan is not None:
                        return _as_route(plan, decision)

    for predicate in relational.predicates:
        for decision in resolved:
            plan = plans.one_hop(
                entity_id=decision.entity_id,
                entity_type=decision.entity_type,
                predicate=predicate, temporal=temporal,
                inverse_hint=relational.inverse_hint,
            )
            if plan is not None:
                return _as_route(plan, decision)

    # No predicate named, but the question is explicitly about a period: "what
    # happened with X in 2015", "the history of X". The answer is everything
    # recorded about the entity within that window.
    if not relational.is_relational and temporal.kind in (
        qi.TEMPORAL_HISTORY, qi.TEMPORAL_RANGE, qi.TEMPORAL_AS_OF
    ):
        decision = resolved[0]
        plan = plans.timeline(
            entity_id=decision.entity_id, entity_type=decision.entity_type,
            temporal=temporal,
        )
        return _as_route(plan, decision)

    return None


def route(
    question: str, *, index: Any = None, as_of: str | None = None
) -> RoutingOutcome:
    """Choose a template for a question, or explain why not."""
    if not question or not question.strip():
        return RoutingOutcome(reason="empty question")

    if index is None:
        from app.knowledge.candidates import EntityIndex

        index = EntityIndex.load()

    resolved, ambiguous, spans, resolved_spans = _resolve_entities(question, index)
    if not resolved:
        return RoutingOutcome(
            reason=(
                "no entity in the question resolved to a canonical identity"
                if not ambiguous
                else "the entity named is ambiguous"
            ),
            ambiguous=ambiguous,
        )

    planned = _plan_route(
        _mask_entities(question, spans), resolved, resolved_spans, as_of=as_of
    )
    if planned is not None:
        return RoutingOutcome(
            route=planned, reason=planned.reason, ambiguous=ambiguous
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
