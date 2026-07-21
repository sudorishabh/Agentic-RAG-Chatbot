"""Unit tests for self-consistency voting on query analysis.

Covers the per-field majority vote (ties, list slots, intent-tie safety),
vote merging, and the process() wiring: exploratory-temperature samples when
analysis_votes > 1, dropped erroring votes, all-failed passthrough, and the
unchanged single-call path at votes=1. LLM is stubbed; no network.
"""

from __future__ import annotations

from types import SimpleNamespace

import app.generation.llm_client as llm_client
from app.retrieval import query_processor as qp


def _a(**kw):
    kw.setdefault("search_query", "q")
    return qp.QueryAnalysis(**kw)


def _u(labels, **kw):
    """Build a QueryUnderstanding (v2) from (label, confidence) pairs + attrs."""
    kw.setdefault("query_rewrite", "q")
    intents = [
        qp.IntentPrediction(label=lbl, confidence=c, rationale="") for lbl, c in labels
    ]
    return qp.QueryUnderstanding(intents=intents, **kw)


# --------------------------------------------------------------------------- #
# Voting math.
# --------------------------------------------------------------------------- #

def test_vote_majority_wins():
    assert qp._vote(["count", "count", "list"]) == "count"
    assert qp._vote([None, None, "count"]) is None  # None is a real majority
    assert qp._vote([["a"], ["a"], ["b"]]) == ["a"]  # list slots (tags)


def test_vote_ties_take_first_non_null():
    assert qp._vote(["count", "list", None]) == "count"
    assert qp._vote([None, "list", "count"]) == "list"
    assert qp._vote([None, None]) is None


def test_vote_intent_tie_falls_to_qa():
    assert qp._vote(["structured", "chitchat"], qa_on_tie=True) == "qa"
    assert qp._vote(["structured", "structured", "qa"], qa_on_tie=True) == "structured"


def test_merge_votes_per_field():
    votes = [
        _a(intent="structured", operation="count", bundle="news", limit=10,
           tags=["solar"]),
        _a(intent="structured", operation="count", bundle=None, limit=10,
           tags=["solar"]),
        _a(intent="qa", operation=None, bundle="news", limit=5, tags=[]),
    ]
    merged = qp._merge_votes(votes)
    assert merged.intent == "structured"
    assert merged.operation == "count"
    assert merged.bundle == "news"
    assert merged.limit == 10
    assert merged.tags == ["solar"]


def test_merge_votes_intent_tie_is_safe():
    assert qp._merge_votes([_a(intent="structured"), _a(intent="chitchat")]).intent == "qa"


# --------------------------------------------------------------------------- #
# process() wiring.
# --------------------------------------------------------------------------- #

class _FakeModel:
    """Pops one prepared response per invoke (list.pop is atomic, so the
    concurrent vote threads each get their own item)."""

    def __init__(self, feed):
        self._feed = list(feed)

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        item = self._feed.pop()
        if isinstance(item, Exception):
            raise item
        return item


def _settings(monkeypatch, votes):
    monkeypatch.setattr(qp, "get_settings", lambda: SimpleNamespace(analysis_votes=votes))


def test_process_merges_three_votes(monkeypatch):
    model = _FakeModel([
        _u([("database", 0.9)], operation="count"),
        _u([("database", 0.9)], operation="count"),
        _u([("qa", 0.8)], operation=None),
    ])
    temps: list = []

    def fake_get_llm(temperature=None, streaming=False):
        temps.append(temperature)
        return model

    monkeypatch.setattr(llm_client, "get_llm", fake_get_llm)
    _settings(monkeypatch, 3)

    pq = qp.process("how many news items?")

    assert temps == [0.7, 0.7, 0.7]  # exploratory temperature per sample
    assert pq.intent == "structured"
    assert pq.analysis.operation == "count"


def test_process_drops_erroring_votes(monkeypatch):
    model = _FakeModel([
        RuntimeError("one vote down"),
        _u([("database", 0.9)], operation="count"),
        _u([("database", 0.9)], operation="count"),
    ])
    monkeypatch.setattr(llm_client, "get_llm", lambda **kw: model)
    _settings(monkeypatch, 3)

    pq = qp.process("how many news items?")
    assert pq.intent == "structured"


def test_process_all_votes_failing_is_passthrough(monkeypatch):
    model = _FakeModel([RuntimeError("down")] * 3)
    monkeypatch.setattr(llm_client, "get_llm", lambda **kw: model)
    _settings(monkeypatch, 3)

    pq = qp.process("how many news items?")
    assert pq.intent == "qa" and pq.analysis is None
    assert pq.search_query == "how many news items?"


def test_single_vote_keeps_pinned_llm(monkeypatch):
    def no_exploratory(**kw):
        raise AssertionError("voted path must not run at votes=1")

    monkeypatch.setattr(llm_client, "get_llm", no_exploratory)
    monkeypatch.setattr(
        qp, "get_structured_llm", lambda: _FakeModel([_u([("chitchat", 0.9)])])
    )
    _settings(monkeypatch, 1)

    assert qp.process("hi").intent == "chitchat"
