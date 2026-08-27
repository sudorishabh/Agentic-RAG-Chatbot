"""The entity index warms off the request path instead of timing out on it.

Regression cover for the defect the 86-question benchmark exposed: the graph
contributed to 0 of 86 answers because ``EntityIndex.load()`` takes ~7s cold
while the routing budget is 3s, so every first attempt timed out *inside the
load* — and because ``TIMED_OUT`` trips the circuit breaker, three of them shut
routing off before the index had ever finished loading. A cold cache whose build
cost exceeds the budget guarding it can never warm up.
"""
from __future__ import annotations

import time

from app.retrieval.graph import policy


def _await_warm(timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if policy._fresh_index() is not None:
            return True
        time.sleep(0.05)
    return False


def test_a_cold_index_declines_immediately_instead_of_burning_the_budget(monkeypatch):
    policy.reset()
    started = []

    class _SlowIndex:
        @staticmethod
        def load():
            started.append(time.monotonic())
            time.sleep(0.4)
            return object()

    import app.knowledge.candidates as candidates

    monkeypatch.setattr(candidates, "EntityIndex", _SlowIndex)

    began = time.monotonic()
    index = policy.entity_index_or_warm()
    elapsed = time.monotonic() - began

    assert index is None, "a cold index must not be waited for on the request path"
    # The caller returns without paying the load. Generous bound: the assertion is
    # "did not block for the load", not a latency benchmark.
    assert elapsed < 0.3
    assert _await_warm(), "the warm-up must complete in the background"
    assert policy.entity_index_or_warm() is not None
    policy.reset()


def test_warming_does_not_trip_the_circuit_breaker():
    """The whole point: declining while warm-up runs must not look like failure."""
    assert policy.INDEX_WARMING not in policy.BREAKING_OUTCOMES
    # And it must still be a fallback outcome, so the caller carries on with
    # ordinary retrieval rather than treating it as an answer.
    assert policy.INDEX_WARMING in policy.FALLBACK_OUTCOMES


def test_repeated_warming_outcomes_leave_the_breaker_closed():
    policy.reset()
    for _ in range(policy.BREAKER_THRESHOLD + 2):
        policy._note_outcome(policy.INDEX_WARMING)
    assert not policy.circuit_is_open()
    policy.reset()


def test_only_one_warm_up_is_scheduled_for_concurrent_callers(monkeypatch):
    policy.reset()
    loads = []

    class _CountingIndex:
        @staticmethod
        def load():
            loads.append(1)
            time.sleep(0.3)
            return object()

    import app.knowledge.candidates as candidates

    monkeypatch.setattr(candidates, "EntityIndex", _CountingIndex)

    assert [policy.entity_index_or_warm() for _ in range(5)] == [None] * 5
    assert _await_warm()
    assert sum(loads) == 1, "a stampede must not start five loads"
    policy.reset()


def test_attempt_reports_index_warming_rather_than_timing_out(monkeypatch):
    """End to end through `_attempt`: a cold index yields INDEX_WARMING."""
    policy.reset()
    monkeypatch.setattr(policy, "entity_index_or_warm", lambda: None)
    attempt = policy._attempt("who funds what", top_k=5, allowed=policy.ALL_CLASSES)
    assert attempt.outcome == policy.INDEX_WARMING
    assert not attempt.used
    assert attempt.blocks == []
    policy.reset()
