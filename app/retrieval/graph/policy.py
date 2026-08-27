"""Which questions production may answer from the graph, and what happens next.

The decision layer between `retriever.retrieve` and the graph.

    query -> route -> class enabled? -> traverse -> useful? -> graph context
                 |             |                        |
                 |             |                        +-- zero rows -> fallback
                 |             +-- no -----------------------------------> fallback
                 +-- not graph-shaped ----------------------------------> fallback

Every path that is not "useful result" ends at existing retrieval, which stays
authoritative. The graph is an accelerator, not a replacement for anything.

What the class gate is, and is not
----------------------------------
Phase 10 measured graph retrieval class by class, and this module encoded the
four classes that had earned routing. That list then became the ceiling on what
the graph could answer at all — and, because all four read current-state edges
of which this corpus has none, the ceiling was zero.

The gate remains, because staging a rollout and isolating a class while
debugging are both worth having. What changed is what it gates: a *capability*
(one hop, two hops, current, historical) rather than a subject matter. So a
predicate approved into the vocabulary lands in a class that already exists and
is already enabled, and nothing has to be added to anyone's configuration for
its claims to become reachable. Safety is not the gate's job and never was — it
comes from the closed vocabulary, the reviewed templates, the parameter
validation and the scope check, every one of which applies whatever class a
route lands in.

Zero results and failure are different things
---------------------------------------------
Both fall back, so a user cannot tell them apart — but an operator must. A
`ZERO_RESULT` is the graph correctly reporting the corpus knows of no such
relationship; a `FAILED` is the graph being unable to say. Counting them
together would let Neo4j degrade silently behind a fallback that keeps working.
Each outcome is its own counter.

Availability
------------
Nothing here can make `/chat` unavailable. The attempt runs under a wall-clock
budget on a worker thread, every exception is caught, and every failure returns
`blocks=[]`, which the caller reads as "carry on with existing retrieval".
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Any

from app.observability import retrieval_log
from app.retrieval.graph import plans

logger = logging.getLogger(__name__)

METRIC_FAMILY = "graph_routing"

# Template -> query class, for the **legacy** hand-written templates. Kept
# verbatim so a deployment that pins `GRAPH_ROUTING_CLASSES=current_funding`
# still gates exactly the templates it always gated.
#
# It is no longer the definition of what the graph can answer. A schema-derived
# plan carries its own capability class (see `app.retrieval.graph.plans`), and
# this table is consulted only when a route did not come from one. The new
# generic templates appear here too, mapped to the class their plans use, so
# that every registry entry still has a class and none is reachable by accident.
TEMPLATE_CLASSES: dict[str, str] = {
    "projects_funded_by_org": "current_funding",
    "people_leading_projects_funded_by_org": "multi_hop",
    "projects_led_by_person": "leadership",
    "funders_of_project": "funders_of_project",
    "person_works_at": "employment",
    "person_member_of": "employment",
    "project_history": "historical",
    "person_history": "historical",
    "org_funding_history": "historical",
    "claims_as_of": "historical",
    "explain_claim": "explain",
    "relationship_by_subject": plans.CLASS_HISTORY,
    "relationship_by_object": plans.CLASS_HISTORY,
    "relationship_two_hop": plans.CLASS_MULTI_HOP,
    "entity_timeline": plans.CLASS_TIMELINE,
}

LEGACY_CLASSES: tuple[str, ...] = tuple(
    sorted(
        {
            name for template, name in TEMPLATE_CLASSES.items()
            if name not in plans.CAPABILITY_CLASSES
        }
    )
)

# What routing may use when nothing is configured.
#
# Previously four classes, chosen because they were the four Phase 10 had
# benchmarked. That list turned out to be the thing standing between the graph
# and every question it could answer: all four route to current-state templates,
# and every claim in this corpus ended before 2020, so the shipped configuration
# could only ever return zero rows. Meanwhile `historical` — the one class whose
# templates read the Claim nodes that actually hold the data — was switched off.
#
# The default is now every class, because the *class* is no longer what makes a
# question safe to answer. Safety comes from the closed vocabulary, the reviewed
# templates, the parameter validation and the scope check, all of which apply
# whatever class a route lands in. `GRAPH_ROUTING_CLASSES` keeps working as an
# allow-list for a staged rollout or for isolating a class while debugging; it
# simply no longer decides which predicates exist.
DEFAULT_ENABLED_CLASSES: tuple[str, ...] = tuple(
    sorted(set(TEMPLATE_CLASSES.values()) | set(plans.CAPABILITY_CLASSES))
)

ALL_CLASSES = tuple(
    sorted(set(TEMPLATE_CLASSES.values()) | set(plans.CAPABILITY_CLASSES))
)

# Wall-clock budget for the whole attempt — route, traverse, hydrate, context.
# Measured p95 is well under 500 ms; this exists so a pathological graph costs a
# fallback rather than a request.
DEFAULT_BUDGET_SECONDS = 3.0

# Circuit breaker. Falling back keeps `/chat` *available* during a Neo4j
# outage, but every relational query still pays the failure — measured at ~2.3 s
# per attempt against an unreachable server, and a full budget's 3 s when the
# driver hangs instead. Availability is not enough if every question gets slow.
#
# After this many consecutive failures the graph is skipped outright until the
# cooldown expires, so an outage costs a few slow queries and then nothing. Any
# success closes it again.
BREAKER_THRESHOLD = 3
BREAKER_COOLDOWN_SECONDS = 60.0

# How long a loaded entity index is reused on the read path. `EntityIndex.load`
# rebuilds from MySQL every call — right for ingestion, which must see entities
# seeded moments earlier, and ruinous for retrieval, which was paying ~60-100 ms
# per query to rebuild an index that changes only when the graph is reprojected.
# Cached here rather than in the knowledge layer so ingestion keeps its fresh
# read and only retrieval gets the warm one.
INDEX_TTL_SECONDS = 300.0

_executor: ThreadPoolExecutor | None = None
_breaker_lock = __import__("threading").Lock()
_consecutive_failures = 0
_circuit_open_until = 0.0
_index_lock = __import__("threading").Lock()
_index: Any = None
_index_loaded_at = 0.0
_index_warming = False


# Outcomes. Each is a distinct operational story, so each is counted apart.
DISABLED = "disabled"              # kill switch or flag off
NOT_ROUTED = "not_routed"          # not a graph-shaped question
CLASS_DISABLED = "class_disabled"  # graph-shaped, but that class is not enabled
ANSWERED = "answered"              # useful result: graph context is used
ZERO_RESULT = "zero_result"        # graph ran, corpus knows of no such relation
NO_EVIDENCE = "no_evidence"        # rows, but nothing renderable or hydratable
FAILED = "failed"                  # graph error
TIMED_OUT = "timed_out"            # graph exceeded its budget
CIRCUIT_OPEN = "circuit_open"      # skipped: the graph is failing, don't wait
SCOPE_UNSUPPORTED = "scope_unsupported"  # query is scoped in a way no template honours
INDEX_WARMING = "index_warming"    # the entity index is still being built; declined fast

# Outcomes that mean "the graph could not answer", as opposed to "the graph
# answered that there is nothing". Only these trip the breaker: a zero result is
# the graph working correctly.
#
# `INDEX_WARMING` is deliberately absent. It is the graph declining on purpose
# while a one-time cache builds, and counting it as a failure is precisely the bug
# it was introduced to fix: three of them in a row would open the breaker and stop
# the warm-up ever being used.
BREAKING_OUTCOMES = frozenset({FAILED, TIMED_OUT})

FALLBACK_OUTCOMES = frozenset(
    {DISABLED, NOT_ROUTED, CLASS_DISABLED, ZERO_RESULT, NO_EVIDENCE,
     FAILED, TIMED_OUT, CIRCUIT_OPEN, SCOPE_UNSUPPORTED, INDEX_WARMING}
)


@dataclass
class GraphAttempt:
    """What routing decided, and what production should do about it."""

    outcome: str
    blocks: list[Any] = field(default_factory=list)
    query_class: str | None = None
    template_id: str | None = None
    mode: str | None = None
    entity: str | None = None
    rows: int = 0
    elapsed_ms: float = 0.0
    reason: str = ""
    answer: Any = None
    scope: str = "no scope"

    @property
    def used(self) -> bool:
        """Whether production should answer from these blocks."""
        return self.outcome == ANSWERED and bool(self.blocks)

    @property
    def fell_back(self) -> bool:
        return self.outcome in FALLBACK_OUTCOMES

    def summary(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome, "class": self.query_class,
            "template_id": self.template_id, "mode": self.mode,
            "entity": self.entity, "rows": self.rows,
            "blocks": len(self.blocks), "elapsed_ms": round(self.elapsed_ms, 1),
            "scope": self.scope, "reason": self.reason,
        }


def _executor_for_graph() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="graph-route"
        )
    return _executor


def enabled_classes(settings: Any = None) -> tuple[str, ...]:
    """The classes routing is allowed to use, from configuration.

    A name that is not a known class is dropped with a warning rather than
    silently ignored — a typo in configuration should be visible, not quietly
    disable routing.
    """
    if settings is None:
        from app.config import get_settings

        settings = get_settings()
    raw = getattr(settings, "graph_routing_classes", None)
    # Whitespace-only is a formatting artifact, not an instruction to disable
    # routing; an explicit list of names nobody recognises is a real mistake and
    # is left to disable it, loudly.
    if not raw or not str(raw).strip():
        return DEFAULT_ENABLED_CLASSES
    names = tuple(
        part.strip() for part in str(raw).split(",") if part.strip()
    )
    known = tuple(n for n in names if n in ALL_CLASSES)
    unknown = [n for n in names if n not in ALL_CLASSES]
    if unknown:
        logger.warning(
            "Ignoring unknown graph routing class(es): %s. Known: %s",
            ", ".join(unknown), ", ".join(ALL_CLASSES),
        )
    return known


def class_of(template_id: str | None) -> str | None:
    return TEMPLATE_CLASSES.get(template_id or "")


def class_of_route(route: Any) -> str | None:
    """The class a route is gated by.

    A schema-derived plan states its own capability class; a legacy pattern
    route has none and is looked up by template id. Both go through here so the
    gate has one definition and neither path can drift from it.
    """
    return getattr(route, "query_class", "") or class_of(
        getattr(route, "template_id", None)
    )


def entity_index() -> Any:
    """The entity index for the read path, rebuilt at most once per TTL.

    Blocking. Callers on the request path want :func:`entity_index_or_warm`.
    """
    global _index, _index_loaded_at
    with _index_lock:
        if _index is not None and time.monotonic() - _index_loaded_at < INDEX_TTL_SECONDS:
            return _index
    # Loaded outside the lock: a slow rebuild would otherwise block every
    # concurrent query. A rare duplicate load costs less than a stampede wait.
    from app.knowledge.candidates import EntityIndex

    loaded = EntityIndex.load()
    with _index_lock:
        _index = loaded
        _index_loaded_at = time.monotonic()
    return loaded


def _fresh_index() -> Any:
    """The cached index if it is still within its TTL, else None. Never loads."""
    with _index_lock:
        if _index is not None and time.monotonic() - _index_loaded_at < INDEX_TTL_SECONDS:
            return _index
    return None


def entity_index_or_warm() -> Any:
    """The index if it is ready; otherwise start building it and return None.

    This exists because the blocking version could never finish inside a request.
    Measured on this corpus: ``EntityIndex.load()`` takes about 7 seconds cold and
    0 ms warm, while the routing budget is 3 seconds. Every first attempt
    therefore timed out *inside the load*, and because ``TIMED_OUT`` trips the
    breaker, three of them shut routing off — so the load never completed, the
    cache never populated, and the graph contributed to 0 of 86 benchmark
    questions. A cold cache whose build cost exceeds the budget that guards it can
    never warm up.

    Raising the budget to cover a 7-second load would have made every user wait
    for it. Instead the load moves off the request path entirely: the first caller
    starts it on the graph executor and gets None, callers during the build get
    None immediately, and once it lands every later query routes at the warm cost
    (~0.3s to route, ~1.6s to answer) well inside the budget.

    Returning None is a *decline*, not a failure — see ``INDEX_WARMING``.
    """
    global _index_warming
    ready = _fresh_index()
    if ready is not None:
        return ready
    with _index_lock:
        if _index_warming:
            return None
        _index_warming = True

    def _warm() -> None:
        global _index_warming
        try:
            entity_index()
            logger.info("Graph entity index warmed; routing is live.")
        except Exception:
            logger.warning("Graph entity index warm-up failed.", exc_info=True)
        finally:
            with _index_lock:
                _index_warming = False

    try:
        _executor_for_graph().submit(_warm)
    except Exception:  # pragma: no cover - defence in depth
        with _index_lock:
            _index_warming = False
        logger.warning("Could not schedule graph index warm-up.", exc_info=True)
    return None


def prewarm_entity_index() -> None:
    """Kick off the index build without waiting for a first question.

    Safe to call from a startup hook or a health probe; a no-op once warm.
    """
    entity_index_or_warm()


def reset_index_cache() -> None:
    """Force the next query to reload the index. For tests and after a reprojection."""
    global _index, _index_loaded_at, _index_warming
    with _index_lock:
        _index = None
        _index_loaded_at = 0.0
        _index_warming = False


def circuit_is_open() -> bool:
    """Whether the graph is being skipped after repeated failures."""
    with _breaker_lock:
        return time.monotonic() < _circuit_open_until


def _note_outcome(outcome: str) -> None:
    """Advance the breaker. Failures accumulate; anything else clears them."""
    global _consecutive_failures, _circuit_open_until
    with _breaker_lock:
        if outcome in BREAKING_OUTCOMES:
            _consecutive_failures += 1
            if _consecutive_failures >= BREAKER_THRESHOLD:
                _circuit_open_until = time.monotonic() + BREAKER_COOLDOWN_SECONDS
                logger.warning(
                    "Graph unavailable after %d consecutive failures; "
                    "skipping graph routing for %.0fs.",
                    _consecutive_failures, BREAKER_COOLDOWN_SECONDS,
                )
        elif outcome != CIRCUIT_OPEN:
            # A route that was never attempted says nothing about health, but
            # anything the graph actually completed does.
            if outcome not in (DISABLED, NOT_ROUTED, CLASS_DISABLED):
                _consecutive_failures = 0
                _circuit_open_until = 0.0


def reset_circuit() -> None:
    """Close the circuit. For tests and for an operator forcing a retry."""
    global _consecutive_failures, _circuit_open_until
    with _breaker_lock:
        _consecutive_failures = 0
        _circuit_open_until = 0.0


def _record(outcome: str, query_class: str | None) -> None:
    try:
        from app.observability.metrics import record_event

        record_event(METRIC_FAMILY, outcome)
        if query_class:
            record_event(f"{METRIC_FAMILY}.class", f"{query_class}:{outcome}")
    except Exception:  # pragma: no cover - metrics must never break retrieval
        logger.debug("Could not record a graph routing metric.", exc_info=True)


def _attempt(question: str, *, top_k: int | None, allowed: tuple[str, ...]) -> GraphAttempt:
    """The body of an attempt. Runs on a worker thread; may raise."""
    from app.retrieval.graph import pipeline, router

    # One index, shared by the routing probe and the answer below. Loading it
    # twice per query was the whole of the routing overhead.
    #
    # Non-blocking: a cold index is built off the request path and this attempt
    # declines instead of waiting (see `entity_index_or_warm`). Declining costs
    # the caller nothing and does not trip the breaker, so the warm-up survives.
    index = entity_index_or_warm()
    if index is None:
        return GraphAttempt(
            INDEX_WARMING, reason="entity index is warming; skipped this query"
        )

    outcome = router.route(question, index=index)
    if not outcome.routed:
        return GraphAttempt(NOT_ROUTED, reason=outcome.reason)

    route = outcome.route
    query_class = class_of_route(route)
    if query_class not in allowed:
        # Routed, but to a class without evidence behind it. Shadow mode still
        # observes these; production does not answer from them.
        return GraphAttempt(
            CLASS_DISABLED, query_class=query_class,
            template_id=route.template_id, mode=route.mode,
            entity=route.entity_name,
            reason=f"class {query_class!r} is not enabled for routing",
        )

    answer = pipeline.answer(question, index=index, top_k=top_k)
    result = answer.result
    common = {
        "query_class": query_class, "template_id": route.template_id,
        "mode": route.mode, "entity": route.entity_name,
        "rows": len(result.rows) if result else 0, "answer": answer,
    }

    if result is not None and result.error:
        return GraphAttempt(FAILED, reason=result.error, **common)
    if result is None or result.empty:
        # Not a failure: the graph ran and the corpus knows of no such
        # relationship. Existing retrieval may still find something in prose.
        return GraphAttempt(
            ZERO_RESULT, reason="the graph holds no such relationship", **common
        )
    if not answer.blocks:
        return GraphAttempt(NO_EVIDENCE, reason=answer.reason, **common)

    return GraphAttempt(
        ANSWERED, blocks=list(answer.blocks), reason=answer.reason, **common
    )


def attempt(
    question: str,
    *,
    top_k: int | None = None,
    budget_seconds: float | None = None,
    settings: Any = None,
    filters: Any = None,
    source_type: str | None = None,
) -> GraphAttempt:
    """Try to answer from the graph. Never raises; never blocks past its budget.

    Returns an attempt whose ``blocks`` are empty unless the outcome is
    ``ANSWERED``, so a caller that simply checks ``used`` cannot accidentally
    answer from a failed or empty graph query.

    ``filters`` and ``source_type`` are the query's scope. They are checked here
    rather than at the call site so a caller cannot forget them: a scope no
    template can honour declines the graph outright.
    """
    from app.retrieval.graph import scope as scoping

    started = time.perf_counter()
    query_scope = scoping.describe(filters, source_type)
    # Read by the trace in `_finish`; set once the gate below has resolved it.
    allowed_classes: tuple[str, ...] = ()

    def _finish(result: GraphAttempt) -> GraphAttempt:
        result.elapsed_ms = (time.perf_counter() - started) * 1000
        result.scope = query_scope.describe()
        _note_outcome(result.outcome)
        _record(result.outcome, result.query_class)
        # The routing decision itself, as one graph event: which template the
        # question was routed to (or why it was not), the entity it resolved to,
        # how many rows came back and how many blocks survived. The traversal
        # inside `_attempt` records its own event; this one is what explains a
        # query where the graph contributed nothing.
        retrieval_log.record(
            retrieval_log.GRAPH,
            "route",
            stage="graph_routing",
            request=lambda: {
                "question": question,
                "top_k": top_k,
                "scope": result.scope,
                "enabled_classes": list(allowed_classes),
            },
            latency_ms=result.elapsed_ms,
            result_count=result.rows,
            metrics={
                "outcome": result.outcome,
                "used": result.used,
                "query_class": result.query_class,
                "template_id": result.template_id,
                "mode": result.mode,
                "entity": result.entity,
                "blocks": len(result.blocks),
                "reason": result.reason,
            },
            error=result.reason if result.outcome in BREAKING_OUTCOMES else None,
        )
        logger.info("graph routing: %s", result.summary())
        return result

    try:
        if settings is None:
            from app.config import get_settings

            settings = get_settings()

        # The kill switch. One boolean, checked first, and with it off nothing
        # below runs and the graph package is not even imported.
        if not getattr(settings, "graph_routing_enabled", False):
            return _finish(GraphAttempt(DISABLED, reason="graph routing is off"))
        if not question or not question.strip():
            return _finish(GraphAttempt(NOT_ROUTED, reason="empty question"))
        if not query_scope.is_supported:
            # The question was narrowed in a way no template expresses. Answering
            # anyway would drop the constraint silently, which is worse than not
            # using the graph: existing retrieval honours it exactly.
            return _finish(
                GraphAttempt(
                    SCOPE_UNSUPPORTED,
                    reason=(
                        "query scope not supported by any graph template: "
                        + ", ".join(sorted(query_scope.unsupported))
                    ),
                )
            )
        if circuit_is_open():
            # Skipped without waiting. During an outage this is what keeps the
            # graph from taxing every relational query with a doomed attempt.
            return _finish(
                GraphAttempt(CIRCUIT_OPEN, reason="graph is failing; skipped")
            )

        allowed = enabled_classes(settings)
        allowed_classes = allowed
        if not allowed:
            return _finish(
                GraphAttempt(DISABLED, reason="no graph query class is enabled")
            )

        budget = budget_seconds or getattr(
            settings, "graph_routing_budget_seconds", DEFAULT_BUDGET_SECONDS
        )
        # `bound` carries this request's retrieval trace onto the graph
        # executor: a worker thread starts with an empty context, so without it
        # the traversal below would run untraced.
        future = _executor_for_graph().submit(
            retrieval_log.bound(_attempt), question, top_k=top_k, allowed=allowed
        )
        try:
            return _finish(future.result(timeout=budget))
        except FutureTimeout:
            # The work is abandoned rather than awaited. A hung graph costs one
            # worker thread until it returns, never the request.
            future.cancel()
            logger.warning("Graph routing exceeded its %.1fs budget.", budget)
            return _finish(
                GraphAttempt(TIMED_OUT, reason=f"exceeded {budget}s budget")
            )
    except Exception as exc:
        # Including a failure to submit, import or read settings. Retrieval must
        # continue: this is the guarantee that Neo4j cannot take /chat down.
        logger.warning("Graph routing attempt failed.", exc_info=True)
        return _finish(GraphAttempt(FAILED, reason=f"{type(exc).__name__}: {exc}"))


def reset() -> None:
    """Drop the executor, the cached index and the circuit. For tests."""
    global _executor
    executor, _executor = _executor, None
    reset_circuit()
    reset_index_cache()
    if executor is not None:
        executor.shutdown(wait=False)
