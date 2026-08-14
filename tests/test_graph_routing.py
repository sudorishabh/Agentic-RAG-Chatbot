"""Controlled graph routing: which questions go to the graph, and what happens
when it cannot answer.

The property under test throughout is that **existing retrieval is the fallback
for everything**. Each test drives one outcome — not routed, a disabled class, a
zero result, an error, a timeout, an open circuit — and asserts that production
still answers, from the retrieval it has always used.

The distinction between a *zero result* and a *failure* gets its own tests. Both
fall back, so a user cannot tell them apart, but an operator must: one is the
graph correctly reporting the corpus knows of no such relationship, the other is
the graph being unable to say.
"""
from __future__ import annotations

import time

import pytest

from app.observability import metrics
from app.retrieval.graph import policy
from app.retrieval.graph import templates as reg


ORG = "org_aeeeb2a91bdd"


class _Settings:
    def __init__(self, *, enabled=True, classes=None, budget=15.0):
        self.graph_routing_enabled = enabled
        self.graph_routing_classes = classes
        self.graph_routing_budget_seconds = budget


@pytest.fixture(autouse=True)
def _clean():
    policy.reset()
    metrics.reset()
    yield
    policy.reset()
    metrics.reset()


def _fake_attempt(monkeypatch, outcome_fn):
    """Replace the inner attempt so outcomes can be driven directly."""
    monkeypatch.setattr(policy, "_attempt", outcome_fn)


def _answered(query_class="current_funding", blocks=None):
    def _inner(question, *, top_k, allowed):
        return policy.GraphAttempt(
            policy.ANSWERED, blocks=blocks or ["block"],
            query_class=query_class, template_id="projects_funded_by_org",
            mode=reg.MODE_CURRENT, entity="DBT", rows=3,
        )
    return _inner


# --------------------------------------------------------------------------- #
# The kill switch
# --------------------------------------------------------------------------- #


def test_the_shipped_configuration_is_narrow():
    """Routing is on, for four measured classes and nothing else.

    Phase 11 turns this on deliberately, so the test records what "on" means:
    every other class — `historical` included — still falls through to existing
    retrieval, and the graph is never consulted for it.
    """
    from app.config import get_settings

    settings = get_settings()
    assert settings.graph_routing_enabled is True
    assert set(policy.enabled_classes(settings)) == {
        "current_funding", "leadership", "multi_hop", "funders_of_project",
    }


def test_the_kill_switch_stops_everything(monkeypatch):
    """One boolean, checked first. With it off the graph is never consulted."""
    called = []
    _fake_attempt(monkeypatch, lambda *a, **kw: called.append(1))
    attempt = policy.attempt("What projects are funded by DBT?",
                             settings=_Settings(enabled=False))
    assert attempt.outcome == policy.DISABLED
    assert attempt.used is False
    assert attempt.blocks == []
    assert called == [], "nothing ran"


@pytest.mark.parametrize("blank", [None, "", "   ", "\n"])
def test_an_unset_class_list_means_the_default(monkeypatch, blank):
    _fake_attempt(monkeypatch, _answered())
    attempt = policy.attempt("q", settings=_Settings(classes=blank))
    assert attempt.outcome == policy.ANSWERED


def test_a_class_list_of_only_unknown_names_disables_routing(monkeypatch):
    """A real misconfiguration, and it should fail closed rather than quietly
    reverting to the default set nobody asked for."""
    _fake_attempt(monkeypatch, _answered())
    attempt = policy.attempt("q", settings=_Settings(classes="nonexistent_class"))
    assert attempt.outcome == policy.DISABLED


def test_unknown_class_names_are_dropped_not_silently_honoured():
    allowed = policy.enabled_classes(
        _Settings(classes="current_funding,not_a_class,leadership")
    )
    assert allowed == ("current_funding", "leadership")


# --------------------------------------------------------------------------- #
# Which classes are enabled
# --------------------------------------------------------------------------- #


def test_only_classes_with_benchmark_evidence_are_enabled_by_default():
    assert set(policy.DEFAULT_ENABLED_CLASSES) == {
        "current_funding", "leadership", "multi_hop", "funders_of_project",
    }


def test_historical_routing_is_not_enabled_by_default():
    """0.83 coverage on three queries is a signal, not a mandate. History stays
    in shadow until a larger reviewed benchmark exists."""
    assert "historical" not in policy.DEFAULT_ENABLED_CLASSES


def test_unbenchmarked_classes_are_not_enabled_by_default():
    assert "employment" not in policy.DEFAULT_ENABLED_CLASSES
    assert "explain" not in policy.DEFAULT_ENABLED_CLASSES


def test_every_template_has_a_class():
    """A template with no class cannot be routed to, so a new one is opt-in."""
    for template_id in reg.TEMPLATE_IDS:
        assert policy.class_of(template_id) is not None, template_id


def test_a_routed_but_disabled_class_falls_back(monkeypatch):
    def _historical(question, *, top_k, allowed):
        assert "historical" not in allowed
        return policy.GraphAttempt(
            policy.CLASS_DISABLED, query_class="historical",
            template_id="org_funding_history",
        )

    _fake_attempt(monkeypatch, _historical)
    attempt = policy.attempt("What did DBT fund in the past?",
                             settings=_Settings())
    assert attempt.outcome == policy.CLASS_DISABLED
    assert attempt.used is False and attempt.fell_back is True


# --------------------------------------------------------------------------- #
# Zero result is not failure
# --------------------------------------------------------------------------- #


def test_a_zero_result_is_reported_as_such_and_falls_back(monkeypatch):
    """The graph ran and the corpus knows of no such relationship. Existing
    retrieval may still find something in prose, so it gets the question."""
    _fake_attempt(
        monkeypatch,
        lambda *a, **kw: policy.GraphAttempt(
            policy.ZERO_RESULT, query_class="current_funding", rows=0
        ),
    )
    attempt = policy.attempt("q", settings=_Settings())
    assert attempt.outcome == policy.ZERO_RESULT
    assert attempt.used is False and attempt.fell_back is True
    assert metrics.events()["graph_routing"]["counts"] == {"zero_result": 1}


def test_a_failure_is_reported_separately_from_a_zero_result(monkeypatch):
    _fake_attempt(
        monkeypatch,
        lambda *a, **kw: policy.GraphAttempt(
            policy.FAILED, query_class="current_funding",
            reason="ServiceUnavailable",
        ),
    )
    attempt = policy.attempt("q", settings=_Settings())
    assert attempt.outcome == policy.FAILED
    assert metrics.events()["graph_routing"]["counts"] == {"failed": 1}


def test_a_zero_result_does_not_trip_the_breaker(monkeypatch):
    """A graph that keeps saying "no such relationship" is working correctly."""
    _fake_attempt(
        monkeypatch,
        lambda *a, **kw: policy.GraphAttempt(
            policy.ZERO_RESULT, query_class="current_funding"
        ),
    )
    for _ in range(policy.BREAKER_THRESHOLD + 3):
        policy.attempt("q", settings=_Settings())
    assert policy.circuit_is_open() is False


def test_an_exception_inside_the_attempt_becomes_a_failure(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("driver exploded")

    _fake_attempt(monkeypatch, _boom)
    attempt = policy.attempt("q", settings=_Settings())
    assert attempt.outcome == policy.FAILED
    assert attempt.blocks == []


# --------------------------------------------------------------------------- #
# The budget
# --------------------------------------------------------------------------- #


def test_a_slow_graph_is_abandoned_at_its_budget(monkeypatch):
    def _slow(question, *, top_k, allowed):
        time.sleep(5)
        return policy.GraphAttempt(policy.ANSWERED, blocks=["late"])

    _fake_attempt(monkeypatch, _slow)
    started = time.perf_counter()
    attempt = policy.attempt("q", settings=_Settings(budget=0.4))
    elapsed = (time.perf_counter() - started) * 1000

    assert attempt.outcome == policy.TIMED_OUT
    assert attempt.blocks == []
    assert elapsed < 2000, f"waited {elapsed:.0f}ms for a 0.4s budget"


def test_a_timeout_trips_the_breaker_like_a_failure(monkeypatch):
    def _slow(question, *, top_k, allowed):
        time.sleep(5)
        return policy.GraphAttempt(policy.ANSWERED)

    _fake_attempt(monkeypatch, _slow)
    for _ in range(policy.BREAKER_THRESHOLD):
        policy.attempt("q", settings=_Settings(budget=0.2))
    assert policy.circuit_is_open() is True


# --------------------------------------------------------------------------- #
# The circuit breaker
# --------------------------------------------------------------------------- #


def test_the_circuit_opens_after_repeated_failures(monkeypatch):
    """Falling back keeps /chat available; the breaker keeps it fast."""
    calls = []

    def _fail(question, *, top_k, allowed):
        calls.append(1)
        return policy.GraphAttempt(policy.FAILED, reason="down")

    _fake_attempt(monkeypatch, _fail)
    for _ in range(policy.BREAKER_THRESHOLD):
        policy.attempt("q", settings=_Settings())
    assert policy.circuit_is_open() is True

    attempted = len(calls)
    for _ in range(5):
        attempt = policy.attempt("q", settings=_Settings())
        assert attempt.outcome == policy.CIRCUIT_OPEN
    assert len(calls) == attempted, "an open circuit must not call the graph"


def test_an_open_circuit_costs_almost_nothing(monkeypatch):
    _fake_attempt(
        monkeypatch, lambda *a, **kw: policy.GraphAttempt(policy.FAILED)
    )
    for _ in range(policy.BREAKER_THRESHOLD):
        policy.attempt("q", settings=_Settings())

    started = time.perf_counter()
    policy.attempt("q", settings=_Settings())
    assert (time.perf_counter() - started) * 1000 < 50


def test_a_success_closes_the_circuit(monkeypatch):
    state = {"fail": True}

    def _flaky(question, *, top_k, allowed):
        if state["fail"]:
            return policy.GraphAttempt(policy.FAILED)
        return policy.GraphAttempt(
            policy.ANSWERED, blocks=["b"], query_class="current_funding"
        )

    _fake_attempt(monkeypatch, _flaky)
    for _ in range(policy.BREAKER_THRESHOLD - 1):
        policy.attempt("q", settings=_Settings())
    assert policy.circuit_is_open() is False

    state["fail"] = False
    policy.attempt("q", settings=_Settings())
    for _ in range(policy.BREAKER_THRESHOLD - 1):
        state["fail"] = True
        policy.attempt("q", settings=_Settings())
    assert policy.circuit_is_open() is False, "the success reset the count"


def test_a_not_routed_question_does_not_affect_the_breaker(monkeypatch):
    """A question the graph never attempted says nothing about its health."""
    _fake_attempt(
        monkeypatch, lambda *a, **kw: policy.GraphAttempt(policy.NOT_ROUTED)
    )
    for _ in range(policy.BREAKER_THRESHOLD + 3):
        policy.attempt("q", settings=_Settings())
    assert policy.circuit_is_open() is False


# --------------------------------------------------------------------------- #
# The entity index cache
# --------------------------------------------------------------------------- #


def test_the_entity_index_is_loaded_once_not_per_query(monkeypatch):
    """`EntityIndex.load` rebuilds from MySQL every call — right for ingestion,
    which must see entities seeded moments earlier, and ruinous on the read
    path, where it cost ~60-100ms per query for an index that only changes when
    the graph is reprojected."""
    loads = []

    class _Index:
        pass

    monkeypatch.setattr(
        "app.knowledge.candidates.EntityIndex.load",
        classmethod(lambda cls: loads.append(1) or _Index()),
    )
    policy.reset_index_cache()
    first = policy.entity_index()
    for _ in range(10):
        assert policy.entity_index() is first
    assert len(loads) == 1


def test_the_index_cache_expires(monkeypatch):
    """So a reprojection is eventually visible without a restart."""
    loads = []
    monkeypatch.setattr(
        "app.knowledge.candidates.EntityIndex.load",
        classmethod(lambda cls: loads.append(1) or object()),
    )
    monkeypatch.setattr(policy, "INDEX_TTL_SECONDS", -1.0)
    policy.reset_index_cache()
    policy.entity_index()
    policy.entity_index()
    assert len(loads) == 2


def test_routing_shares_one_index_between_the_probe_and_the_answer(monkeypatch):
    """Routing resolves entities to decide, then the pipeline resolves them
    again to answer. Both must use the same loaded index."""
    from app.retrieval.graph import pipeline, router

    sentinel = object()
    monkeypatch.setattr(policy, "entity_index", lambda: sentinel)
    seen = []

    def _route(question, *, index=None, **kwargs):
        seen.append(("route", index))
        return router.RoutingOutcome(
            route=router.Route(
                template_id="projects_funded_by_org",
                parameters={"entity_id": ORG}, entity_id=ORG,
                entity_type="ORGANIZATION", entity_name="DBT",
                mode=reg.MODE_CURRENT, reason="t",
            ),
            reason="t",
        )

    def _answer(question, *, index=None, top_k=None, **kwargs):
        seen.append(("answer", index))
        return pipeline.GraphAnswer(blocks=["b"], result=None)

    monkeypatch.setattr(router, "route", _route)
    monkeypatch.setattr(pipeline, "answer", _answer)
    policy._attempt("q", top_k=5, allowed=("current_funding",))
    assert seen == [("route", sentinel), ("answer", sentinel)]


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #


def test_every_outcome_is_counted(monkeypatch):
    for outcome in (policy.ANSWERED, policy.ZERO_RESULT, policy.NOT_ROUTED):
        _fake_attempt(
            monkeypatch,
            lambda *a, outcome=outcome, **kw: policy.GraphAttempt(
                outcome, blocks=["b"] if outcome == policy.ANSWERED else [],
                query_class="current_funding",
            ),
        )
        policy.attempt("q", settings=_Settings())

    counts = metrics.events()["graph_routing"]["counts"]
    assert counts == {"answered": 1, "zero_result": 1, "not_routed": 1}
    assert metrics.events()["graph_routing"]["total"] == 3


def test_outcomes_are_also_counted_per_class(monkeypatch):
    _fake_attempt(monkeypatch, _answered(query_class="multi_hop"))
    policy.attempt("q", settings=_Settings())
    per_class = metrics.events()["graph_routing.class"]["counts"]
    assert per_class == {"multi_hop:answered": 1}


def test_metrics_appear_in_the_snapshot(monkeypatch):
    _fake_attempt(monkeypatch, _answered())
    policy.attempt("q", settings=_Settings())
    assert "graph_routing" in metrics.snapshot()["events"]


def test_a_metrics_failure_never_breaks_routing(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("metrics backend down")

    monkeypatch.setattr(metrics, "record_event", _boom)
    _fake_attempt(monkeypatch, _answered())
    attempt = policy.attempt("q", settings=_Settings())
    assert attempt.outcome == policy.ANSWERED


# --------------------------------------------------------------------------- #
# The production hook
# --------------------------------------------------------------------------- #


def _enable(monkeypatch, **kwargs):
    from app.config import get_settings

    settings = get_settings()
    for key, value in {"graph_routing_enabled": True,
                       "graph_routing_classes": None,
                       "graph_routing_budget_seconds": 15.0, **kwargs}.items():
        monkeypatch.setattr(settings, key, value, raising=False)
    return settings


def test_the_hook_returns_nothing_when_routing_is_off(monkeypatch):
    from app.retrieval import retriever

    _enable(monkeypatch, graph_routing_enabled=False)
    called = []
    monkeypatch.setattr(policy, "attempt", lambda *a, **kw: called.append(1))
    assert retriever._try_graph("What projects are funded by DBT?", n=5) == []
    assert called == []


def test_the_hook_returns_blocks_only_when_the_graph_answered(monkeypatch):
    from app.retrieval import retriever

    _enable(monkeypatch)
    monkeypatch.setattr(
        policy, "attempt",
        lambda *a, **kw: policy.GraphAttempt(
            policy.ANSWERED, blocks=["a", "b"], query_class="current_funding"
        ),
    )
    assert retriever._try_graph("q", n=5) == ["a", "b"]


@pytest.mark.parametrize(
    "outcome",
    [policy.ZERO_RESULT, policy.FAILED, policy.TIMED_OUT, policy.NOT_ROUTED,
     policy.CLASS_DISABLED, policy.NO_EVIDENCE, policy.CIRCUIT_OPEN],
)
def test_every_non_answer_outcome_falls_back(monkeypatch, outcome):
    """The contract in one test: anything but a useful answer returns [], and
    `retrieve` carries on with the retrieval it has always used."""
    from app.retrieval import retriever

    _enable(monkeypatch)
    monkeypatch.setattr(
        policy, "attempt",
        lambda *a, **kw: policy.GraphAttempt(outcome, blocks=["leaked"]),
    )
    assert retriever._try_graph("q", n=5) == []


def test_a_hook_exception_falls_back(monkeypatch):
    from app.retrieval import retriever

    _enable(monkeypatch)

    def _boom(*args, **kwargs):
        raise RuntimeError("policy exploded")

    monkeypatch.setattr(policy, "attempt", _boom)
    assert retriever._try_graph("q", n=5) == []


def test_a_pinned_scope_is_forwarded_to_the_policy_layer(monkeypatch):
    """`retrieve` no longer decides this itself.

    It used to skip the graph inline whenever `filters` or `source_type` was
    set. That worked but was fragile: a scope dimension added later would have
    been silently ignored at this call site. The scope is now passed down and
    refused by the policy layer, which fails closed on any key no template
    supports. See tests/test_graph_scope.py.
    """
    from qdrant_client.models import FieldCondition, MatchValue

    from app.retrieval import retriever

    _enable(monkeypatch)
    seen = []
    monkeypatch.setattr(
        retriever, "_try_graph",
        lambda q, *, n, filters=None, source_type=None: (
            seen.append((filters, source_type)) or []
        ),
    )
    monkeypatch.setattr(retriever, "search", lambda *a, **kw: [])
    monkeypatch.setattr(retriever, "dual_search", lambda *a, **kw: [])
    monkeypatch.setattr(retriever, "embed_query", lambda *a, **kw: [0.0])

    pinned = FieldCondition(key="source_type", match=MatchValue(value="website"))
    retriever.retrieve("q", filters=[pinned], n=3)
    assert seen[-1] == ([pinned], None)

    retriever.retrieve("q", source_type="website", n=3)
    assert seen[-1] == (None, "website")


def test_an_unscoped_query_may_use_the_graph(monkeypatch):
    from app.retrieval import retriever

    _enable(monkeypatch)
    monkeypatch.setattr(
        retriever, "_try_graph",
        lambda q, *, n, filters=None, source_type=None: ["graph"],
    )
    assert retriever.retrieve("What projects are funded by DBT?", n=3) == ["graph"]
