"""The graph's queryable surface, derived from the approved schema.

The problem this solves
-----------------------
Routing used to be a table of question shapes mapped onto template ids, and a
second table of template ids mapped onto routing classes, and a third list of
which classes were switched on. Three hand-maintained tables meant a predicate
was queryable only if someone had written a template, a route and a class for
it. Three of the seven approved predicates — ``PARTNER_OF``, ``PARENT_OF``,
``HAS_ROLE`` — had none of the three, so the graph held claims nothing could
ask for.

Here the surface is *computed* from things that already exist:

    the closed predicate vocabulary  (what may be asserted)
  + each predicate's domain and range (which entity types may sit at each end)
  + the predicate-parameterized templates (what may be executed)
  = every (predicate, direction) a question could ask about

Adding a predicate to ``app.knowledge.claims.predicates`` and its phrasing to
``app.retrieval.graph.intent.PREDICATE_CUES`` makes it queryable. No template,
no route, no class, no configuration.

What did *not* become dynamic
-----------------------------
The Cypher. A plan chooses among reviewed templates and supplies bound
parameters; it never assembles a query, and the predicate it carries reaches
Neo4j as a ``$predicate`` **value** rather than as a relationship type. An
unapproved predicate has no plan, and even if one were forged
``templates.validate_parameters`` rejects it against the vocabulary before the
driver sees it. The safety boundary is unchanged; only the bookkeeping above it
is smaller.

Capability classes
------------------
``GRAPH_ROUTING_CLASSES`` survives as a rollout switch, but it can no longer be
the definition of what the graph knows. Plans carry one of a small, closed set
of *capability* classes that describe the shape of the retrieval rather than the
subject matter, so a new predicate lands in a class that already exists and is
already enabled:

``relational_current``     one hop, asserted as true now
``relational_history``     one hop, past / point-in-time / windowed / unstated
``relational_multi_hop``   two hops
``entity_timeline``        every predicate at once, for "tell me the history of X"

The legacy class names still gate the legacy derived-edge templates, so an
existing deployment's ``GRAPH_ROUTING_CLASSES`` keeps meaning what it meant.

Current versus historical
-------------------------
Preserved exactly, and it decides which template a plan selects:

*Current* questions prefer a **derived current-state edge** template where one
exists — the traversal is cheaper and the edges are the graph's own statement of
what is true now. Where none exists the claim-based template is used with
``current_only=True``, which applies the *same* eligibility rule the projector
applies (see ``templates._current_clause``). Either way a claim that has ended
cannot be returned as current.

*Historical, point-in-time, windowed and unstated* questions read Claim nodes
and their validity windows, which is where ended relationships live. There is no
lower bound on how old a claim may be: a 1996-1999 relationship is retrieved on
the same terms as a 2018 one, and no comparison anywhere in this module or the
templates it selects tests a claim's age against the present.

The unstated case
-----------------
"Who led Project X?" states no period, and the safe reading is neither "now" nor
"in the past".

Reading it as *current* would be wrong for this corpus in the strongest possible
way: every one of the 1,143 claims in the graph has an end date in the past, so
a current-only reading answers "nothing is known" to a question the graph can
answer completely. Reading it as *historical* would be wrong in the other
direction, since it would suppress an ongoing relationship where one exists.

So an unstated question is answered as ``latest``: no temporal filter, results
ordered newest-first, and — this is the part that makes it safe — **every row
carries its own validity window into the answer**, so an ended relationship is
rendered "(2016-01-01 until 2019-03-31)" and cannot be read as present tense.
The distinction is preserved in the output rather than guessed at in the query.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.retrieval.graph import intent as qi

logger = logging.getLogger(__name__)

# Which end of a relationship the question named.
SIDE_SUBJECT = "subject"
SIDE_OBJECT = "object"

# Capability classes. Closed, small, and about retrieval shape rather than
# subject matter — which is what lets a new predicate be queryable without a
# new class name appearing in anyone's configuration.
CLASS_CURRENT = "relational_current"
CLASS_HISTORY = "relational_history"
CLASS_MULTI_HOP = "relational_multi_hop"
CLASS_TIMELINE = "entity_timeline"

CAPABILITY_CLASSES: tuple[str, ...] = (
    CLASS_CURRENT, CLASS_HISTORY, CLASS_MULTI_HOP, CLASS_TIMELINE,
)

# Derived current-state edge templates, by (predicate, the side the question
# named). These are the pre-existing hand-written templates: a current question
# that matches one gets the cheap edge traversal instead of a claim scan.
#
# Absence is not a gap. A (predicate, side) with no entry falls to the
# claim-based current template, which applies the identical eligibility rule —
# so every approved predicate has a current-state path whether or not anyone
# wrote a bespoke query for it.
CURRENT_EDGE_TEMPLATES: dict[tuple[str, str], str] = {
    ("FUNDED_BY", SIDE_SUBJECT): "funders_of_project",
    ("FUNDED_BY", SIDE_OBJECT): "projects_funded_by_org",
    ("LED_BY", SIDE_OBJECT): "projects_led_by_person",
    ("WORKS_AT", SIDE_SUBJECT): "person_works_at",
    ("MEMBER_OF", SIDE_SUBJECT): "person_member_of",
}

# The one hand-written multi-hop template, and the chain it answers. Used for a
# current-state multi-hop question; anything else goes through the generic
# two-hop template.
CURRENT_TWO_HOP_TEMPLATES: dict[tuple[str, str, str], str] = {
    ("FUNDED_BY", "LED_BY", SIDE_OBJECT): "people_leading_projects_funded_by_org",
}


@dataclass(frozen=True)
class GraphPlan:
    """A selected template with the parameters that make it answer a question.

    Everything a caller needs to execute safely, and nothing it could use to
    build a query: ``template_id`` names a registry entry and ``parameters``
    are values that ``templates.validate_parameters`` will check again.
    """

    plan_id: str
    template_id: str
    parameters: dict[str, Any]
    capability: str
    mode: str
    # The predicates the plan reads, for explanation and metrics.
    predicates: tuple[str, ...]
    side: str
    hops: int
    temporal: qi.TemporalIntent = field(default_factory=qi.TemporalIntent)
    reason: str = ""

    @property
    def is_current(self) -> bool:
        from app.retrieval.graph import templates as reg

        return self.mode == reg.MODE_CURRENT


def sides_for(predicate_name: str, entity_type: str) -> tuple[str, ...]:
    """Which end of ``predicate`` an entity of this type may occupy.

    Read straight off the predicate's declared domain and range, so the type
    system that governs what may be *asserted* also governs what may be *asked*.
    An entity type that fits neither end yields no side and therefore no plan —
    which is how "who funds Ritu Sharma" declines instead of running a query
    that could only ever return nothing.
    """
    from app.knowledge.claims import predicates as vocab

    predicate = vocab.get(predicate_name)
    if predicate is None:
        return ()
    sides: list[str] = []
    if entity_type in predicate.domain:
        sides.append(SIDE_SUBJECT)
    if predicate.entity_valued and entity_type in predicate.range:
        sides.append(SIDE_OBJECT)
    return tuple(sides)


def _pick_side(sides: tuple[str, ...], *, inverse_hint: bool) -> str | None:
    """The side to anchor on when an entity type fits both ends.

    Only ``PARENT_OF`` has the same type at both ends today, so this decides
    between "which units does this organization contain" and "which organization
    is this one part of". The question's own phrasing settles it; with nothing to
    go on, the subject side is the canonical reading of the predicate.
    """
    if not sides:
        return None
    if len(sides) == 1:
        return sides[0]
    return SIDE_OBJECT if inverse_hint else SIDE_SUBJECT


def _capability(*, hops: int, current: bool, timeline: bool) -> str:
    if timeline:
        return CLASS_TIMELINE
    if hops > 1:
        return CLASS_MULTI_HOP
    return CLASS_CURRENT if current else CLASS_HISTORY


def _window_params(temporal: qi.TemporalIntent) -> dict[str, Any]:
    return {
        "window_start": temporal.window_start,
        "window_end": temporal.window_end,
    }


def one_hop(
    *,
    entity_id: str,
    entity_type: str,
    predicate: str,
    temporal: qi.TemporalIntent,
    inverse_hint: bool = False,
) -> GraphPlan | None:
    """A plan for one approved relationship, or None when the schema forbids it."""
    from app.retrieval.graph import templates as reg

    side = _pick_side(
        sides_for(predicate, entity_type), inverse_hint=inverse_hint
    )
    if side is None:
        return None

    current = temporal.is_current
    edge_template = CURRENT_EDGE_TEMPLATES.get((predicate, side)) if current else None
    if edge_template is not None:
        # The cheap path: a reviewed derived-edge traversal, whose only
        # parameter is the entity. Its own Cypher already restricts to
        # `{current: true}`, so no window is passed.
        return GraphPlan(
            plan_id=f"{predicate}:{side}:current_edge",
            template_id=edge_template,
            parameters={"entity_id": entity_id},
            capability=CLASS_CURRENT,
            mode=reg.MODE_CURRENT,
            predicates=(predicate,),
            side=side,
            hops=1,
            temporal=temporal,
            reason=f"{predicate} ({side} side), current state",
        )

    template_id = (
        "relationship_by_subject" if side == SIDE_SUBJECT
        else "relationship_by_object"
    )
    return GraphPlan(
        plan_id=f"{predicate}:{side}:{temporal.kind}",
        template_id=template_id,
        parameters={
            "entity_id": entity_id,
            "predicate": predicate,
            "current_only": current,
            **_window_params(temporal),
        },
        capability=_capability(hops=1, current=current, timeline=False),
        mode=reg.MODE_CURRENT if current else reg.MODE_HISTORICAL,
        predicates=(predicate,),
        side=side,
        hops=1,
        temporal=temporal,
        reason=f"{predicate} ({side} side), {temporal.describe()}",
    )


def two_hop(
    *,
    entity_id: str,
    entity_type: str,
    first: str,
    second: str,
    temporal: qi.TemporalIntent,
) -> GraphPlan | None:
    """A plan chaining two approved relationships through a shared entity.

    The chain is admitted only when the schema allows it end to end: the anchor
    entity must be a legal end of the first predicate, and the type at the
    first predicate's *other* end must be a legal end of the second. That is
    what stops "who funds the people who partner with X" — a chain the
    vocabulary has no path for — becoming a query that scans for nothing.
    """
    from app.knowledge.claims import predicates as vocab
    from app.retrieval.graph import templates as reg

    if first == second:
        return None
    first_predicate, second_predicate = vocab.get(first), vocab.get(second)
    if first_predicate is None or second_predicate is None:
        return None
    if not (first_predicate.entity_valued and second_predicate.entity_valued):
        # A literal-valued predicate has no entity at its far end to chain from.
        return None

    side = _pick_side(sides_for(first, entity_type), inverse_hint=False)
    if side is None:
        return None
    # The type sitting at the middle of the chain.
    middle_types = (
        first_predicate.range if side == SIDE_SUBJECT else first_predicate.domain
    )
    if not any(
        sides_for(second, middle_type) for middle_type in middle_types
    ):
        return None

    current = temporal.is_current
    edge_template = (
        CURRENT_TWO_HOP_TEMPLATES.get((first, second, side)) if current else None
    )
    if edge_template is not None:
        return GraphPlan(
            plan_id=f"{first}+{second}:{side}:current_edge",
            template_id=edge_template,
            parameters={"entity_id": entity_id},
            capability=CLASS_MULTI_HOP,
            mode=reg.MODE_CURRENT,
            predicates=(first, second),
            side=side,
            hops=2,
            temporal=temporal,
            reason=f"{first} then {second}, current state",
        )

    return GraphPlan(
        plan_id=f"{first}+{second}:{side}:{temporal.kind}",
        template_id="relationship_two_hop",
        parameters={
            "entity_id": entity_id,
            "predicate": first,
            "predicate2": second,
            "current_only": current,
            **_window_params(temporal),
        },
        capability=CLASS_MULTI_HOP,
        mode=reg.MODE_CURRENT if current else reg.MODE_HISTORICAL,
        predicates=(first, second),
        side=side,
        hops=2,
        temporal=temporal,
        reason=f"{first} then {second}, {temporal.describe()}",
    )


def timeline(
    *, entity_id: str, entity_type: str, temporal: qi.TemporalIntent
) -> GraphPlan:
    """A plan for "what is the history of X" — every predicate, either end."""
    from app.retrieval.graph import templates as reg

    current = temporal.is_current
    return GraphPlan(
        plan_id=f"timeline:{temporal.kind}",
        template_id="entity_timeline",
        parameters={
            "entity_id": entity_id,
            "current_only": current,
            **_window_params(temporal),
        },
        capability=CLASS_TIMELINE,
        mode=reg.MODE_CURRENT if current else reg.MODE_HISTORICAL,
        predicates=(),
        side=SIDE_SUBJECT,
        hops=1,
        temporal=temporal,
        reason=f"everything recorded about this entity, {temporal.describe()}",
    )


def queryable_predicates() -> tuple[str, ...]:
    """Approved predicates a question could actually reach.

    A predicate is queryable when it is in the vocabulary *and* the question
    layer knows how people say it. Reported by ``scripts.eval_graph_retrieval``
    and asserted by the tests, so a predicate approved without phrasing is a
    visible gap rather than a silent one.
    """
    from app.knowledge.claims import predicates as vocab

    return tuple(
        name for name in vocab.PREDICATE_NAMES if qi.PREDICATE_CUES.get(name)
    )


def coverage() -> dict[str, Any]:
    """A description of the graph's queryable surface, for diagnostics."""
    from app.knowledge.claims import predicates as vocab

    surface: dict[str, Any] = {}
    for name in vocab.PREDICATE_NAMES:
        predicate = vocab.PREDICATES[name]
        surface[name] = {
            "domain": list(predicate.domain),
            "range": list(predicate.range),
            "askable": bool(qi.PREDICATE_CUES.get(name)),
            "current_edge_templates": sorted(
                side for (p, side) in CURRENT_EDGE_TEMPLATES if p == name
            ),
        }
    return {
        "predicates": surface,
        "queryable": list(queryable_predicates()),
        "capability_classes": list(CAPABILITY_CLASSES),
    }
