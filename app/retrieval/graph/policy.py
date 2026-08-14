"""Which questions production may answer from the graph, and what happens next.

The decision layer between `retriever.retrieve` and the graph. Phase 10 measured
graph retrieval class by class; this module encodes the classes that earned
routing and refuses the rest, so enabling a class is a deliberate edit rather
than a side effect of adding a template.

    query -> route -> class enabled? -> traverse -> useful? -> graph context
                 |             |                        |
                 |             |                        +-- zero rows -> fallback
                 |             +-- no -----------------------------------> fallback
                 +-- not graph-shaped ----------------------------------> fallback

Every path that is not "useful result" ends at existing retrieval, which stays
authoritative. The graph is an accelerator for a narrow, measured set of
questions, not a replacement for anything.

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

logger = logging.getLogger(__name__)

METRIC_FAMILY = "graph_routing"

# Template -> query class. The class is the unit routing is enabled by, because
# it is the unit Phase 10 measured; a template with no class cannot be routed to
# at all.
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
}

# Classes with benchmark evidence behind them. `historical` is deliberately
# absent: 0.83 coverage on three queries is a promising signal, not a mandate,
# and it stays in shadow until a larger reviewed historical set exists.
# `employment` and `explain` have never been benchmarked at all.
DEFAULT_ENABLED_CLASSES = (
    "current_funding",
    "leadership",
    "multi_hop",
    "funders_of_project",
)

ALL_CLASSES = tuple(sorted(set(TEMPLATE_CLASSES.values())))

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

# Outcomes that mean "the graph could not answer", as opposed to "the graph
# answered that there is nothing". Only these trip the breaker: a zero result is
# the graph working correctly.
BREAKING_OUTCOMES = frozenset({FAILED, TIMED_OUT})

FALLBACK_OUTCOMES = frozenset(
    {DISABLED, NOT_ROUTED, CLASS_DISABLED, ZERO_RESULT, NO_EVIDENCE,
     FAILED, TIMED_OUT, CIRCUIT_OPEN}
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
            "reason": self.reason,
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


def entity_index() -> Any:
    """The entity index for the read path, rebuilt at most once per TTL."""
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


def reset_index_cache() -> None:
    """Force the next query to reload the index. For tests and after a reprojection."""
    global _index, _index_loaded_at
    with _index_lock:
        _index = None
        _index_loaded_at = 0.0


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
    index = entity_index()

    outcome = router.route(question, index=index)
    if not outcome.routed:
        return GraphAttempt(NOT_ROUTED, reason=outcome.reason)

    route = outcome.route
    query_class = class_of(route.template_id)
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
) -> GraphAttempt:
    """Try to answer from the graph. Never raises; never blocks past its budget.

    Returns an attempt whose ``blocks`` are empty unless the outcome is
    ``ANSWERED``, so a caller that simply checks ``used`` cannot accidentally
    answer from a failed or empty graph query.
    """
    started = time.perf_counter()

    def _finish(result: GraphAttempt) -> GraphAttempt:
        result.elapsed_ms = (time.perf_counter() - started) * 1000
        _note_outcome(result.outcome)
        _record(result.outcome, result.query_class)
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
        if circuit_is_open():
            # Skipped without waiting. During an outage this is what keeps the
            # graph from taxing every relational query with a doomed attempt.
            return _finish(
                GraphAttempt(CIRCUIT_OPEN, reason="graph is failing; skipped")
            )

        allowed = enabled_classes(settings)
        if not allowed:
            return _finish(
                GraphAttempt(DISABLED, reason="no graph query class is enabled")
            )

        budget = budget_seconds or getattr(
            settings, "graph_routing_budget_seconds", DEFAULT_BUDGET_SECONDS
        )
        future = _executor_for_graph().submit(
            _attempt, question, top_k=top_k, allowed=allowed
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
