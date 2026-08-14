"""Query scope and the graph: honour it, or decline the graph.

Removing RBAC/ACL removed *permission* filtering. It did not remove legitimate
query scoping — a question narrowed to PDFs, or to one theme, or to a date range
has been narrowed, and an answer drawn from outside that scope is wrong whether
or not anyone's permissions were involved.

The graph templates express no scope at all, so every one of these tests ends
the same way: the scoped query falls back to existing retrieval, which honours
it exactly. The tests are written against the *mechanism* rather than against
today's empty support set, so the day a template does implement a scope key they
keep meaning something.
"""
from __future__ import annotations

import pytest
from qdrant_client.models import (
    DatetimeRange, FieldCondition, Filter, HasIdCondition, MatchAny, MatchValue,
)

from app.observability import metrics
from app.retrieval.graph import policy
from app.retrieval.graph import scope as scoping


@pytest.fixture(autouse=True)
def _clean():
    policy.reset()
    metrics.reset()
    yield
    policy.reset()
    metrics.reset()


class _Settings:
    graph_routing_enabled = True
    graph_routing_classes = None
    graph_routing_budget_seconds = 15.0


def _answers(monkeypatch, blocks=("block",)):
    """Make the graph succeed, so any decline is attributable to scope."""
    monkeypatch.setattr(
        policy, "_attempt",
        lambda question, *, top_k, allowed: policy.GraphAttempt(
            policy.ANSWERED, blocks=list(blocks), query_class="current_funding",
            template_id="projects_funded_by_org", rows=3,
        ),
    )


def _source_filter(value="pdf"):
    return FieldCondition(key="source_type", match=MatchValue(value=value))


def _document_filter(*ids):
    return FieldCondition(key="document_id", match=MatchAny(any=list(ids)))


# --------------------------------------------------------------------------- #
# Describing a scope
# --------------------------------------------------------------------------- #


def test_no_scope_is_empty():
    described = scoping.describe(None, None)
    assert described.is_empty
    assert described.is_supported
    assert described.describe() == "no scope"


def test_no_scope_from_an_empty_filter_list():
    assert scoping.describe([], None).is_empty


def test_a_source_type_argument_is_a_scope():
    described = scoping.describe(None, "website")
    assert described.keys == {scoping.SOURCE_TYPE_KEY}
    assert described.is_supported is False


def test_a_field_condition_contributes_its_key():
    described = scoping.describe([_document_filter("doc-1", "doc-2")], None)
    assert described.keys == {"document_id"}


@pytest.mark.parametrize(
    "condition,expected",
    [
        (FieldCondition(key="tags", match=MatchAny(any=["energy"])), "tags"),
        (FieldCondition(key="categories", match=MatchAny(any=["x"])), "categories"),
        (FieldCondition(key="language", match=MatchValue(value="en")), "language"),
        (FieldCondition(key="published_at",
                        range=DatetimeRange(gte="2020-01-01T00:00:00Z")),
         "published_at"),
    ],
)
def test_every_real_filter_dimension_is_detected(condition, expected):
    """The dimensions query understanding actually produces."""
    assert scoping.describe([condition], None).keys == {expected}


def test_a_scope_nested_inside_a_filter_is_still_found():
    """A constraint hidden in a `should` branch scopes the query just as much."""
    nested = Filter(should=[_source_filter("pdf"), _document_filter("doc-1")])
    described = scoping.describe([nested], None)
    assert described.keys == {"source_type", "document_id"}


def test_a_negated_constraint_is_still_a_scope():
    described = scoping.describe(
        [Filter(must_not=[_source_filter("website")])], None
    )
    assert described.keys == {"source_type"}


def test_an_unrecognised_condition_counts_as_a_scope():
    """Fail closed. A condition shape this module cannot read is a constraint we
    cannot prove the graph honours, not an absence of one."""
    described = scoping.describe([HasIdCondition(has_id=[1, 2, 3])], None)
    assert scoping.UNKNOWN_KEY in described.keys
    assert described.is_supported is False


def test_an_unreadable_condition_does_not_raise():
    class _Weird:
        @property
        def key(self):
            raise RuntimeError("nope")

    described = scoping.describe([_Weird()], None)
    assert described.is_supported is False


def test_nothing_is_supported_today():
    """The honest state of the system, asserted so it cannot drift silently.

    A key belongs in `SUPPORTED_SCOPE_KEYS` only once a template implements it
    and a test proves equivalence with existing retrieval's semantics.
    """
    assert scoping.SUPPORTED_SCOPE_KEYS == frozenset()


# --------------------------------------------------------------------------- #
# Routing with scope
# --------------------------------------------------------------------------- #


def test_a_graph_class_with_no_scope_is_answered(monkeypatch):
    _answers(monkeypatch)
    attempt = policy.attempt(
        "What projects are funded by DBT?", settings=_Settings()
    )
    assert attempt.outcome == policy.ANSWERED
    assert attempt.used is True
    assert attempt.scope == "no scope"


def test_a_graph_class_with_a_supported_scope_is_answered(monkeypatch):
    """The mechanism, proven by declaring a key supported.

    Nothing is supported in production, so this is the only way to test that the
    check passes rather than merely that it blocks — and it is what will exercise
    a real scoped template when one exists.
    """
    _answers(monkeypatch)
    monkeypatch.setattr(scoping, "SUPPORTED_SCOPE_KEYS", frozenset({"source_type"}))
    attempt = policy.attempt(
        "What projects are funded by DBT?", source_type="pdf", settings=_Settings()
    )
    assert attempt.outcome == policy.ANSWERED
    assert attempt.used is True
    assert attempt.scope == "source_type"


def test_a_partially_supported_scope_still_declines(monkeypatch):
    """One unsupported key is enough. A scope is honoured completely or not
    at all — partially applying it is the silent-drop failure by another name."""
    _answers(monkeypatch)
    monkeypatch.setattr(scoping, "SUPPORTED_SCOPE_KEYS", frozenset({"source_type"}))
    attempt = policy.attempt(
        "What projects are funded by DBT?",
        filters=[_document_filter("doc-1")], source_type="pdf",
        settings=_Settings(),
    )
    assert attempt.outcome == policy.SCOPE_UNSUPPORTED
    assert "document_id" in attempt.reason


def test_a_graph_class_with_an_unsupported_scope_declines(monkeypatch):
    _answers(monkeypatch)
    attempt = policy.attempt(
        "What projects are funded by DBT?",
        filters=[FieldCondition(key="tags", match=MatchAny(any=["energy"]))],
        settings=_Settings(),
    )
    assert attempt.outcome == policy.SCOPE_UNSUPPORTED
    assert attempt.used is False
    assert attempt.blocks == []
    assert attempt.fell_back is True


def test_a_source_type_scope_declines(monkeypatch):
    _answers(monkeypatch)
    attempt = policy.attempt(
        "What projects are funded by DBT?", source_type="website",
        settings=_Settings(),
    )
    assert attempt.outcome == policy.SCOPE_UNSUPPORTED
    assert attempt.used is False


def test_a_document_scope_declines(monkeypatch):
    _answers(monkeypatch)
    attempt = policy.attempt(
        "What projects are funded by DBT?",
        filters=[_document_filter("doc-1", "doc-2")], settings=_Settings(),
    )
    assert attempt.outcome == policy.SCOPE_UNSUPPORTED
    assert attempt.used is False


def test_the_scope_check_runs_before_the_graph_is_touched(monkeypatch):
    """Cheap and early: a scoped query must not pay for a traversal whose result
    is going to be discarded."""
    called = []
    monkeypatch.setattr(
        policy, "_attempt",
        lambda *a, **kw: called.append(1) or policy.GraphAttempt(policy.ANSWERED),
    )
    policy.attempt("q", source_type="pdf", settings=_Settings())
    assert called == [], "the graph must not run for an unsupported scope"


def test_an_unsupported_scope_does_not_trip_the_circuit_breaker(monkeypatch):
    """Declining on scope is the system working, not the graph failing."""
    _answers(monkeypatch)
    for _ in range(policy.BREAKER_THRESHOLD + 3):
        policy.attempt("q", source_type="pdf", settings=_Settings())
    assert policy.circuit_is_open() is False


def test_the_scope_outcome_is_counted(monkeypatch):
    _answers(monkeypatch)
    policy.attempt("q", source_type="pdf", settings=_Settings())
    assert metrics.events()["graph_routing"]["counts"] == {"scope_unsupported": 1}


# --------------------------------------------------------------------------- #
# End to end through `retrieve`
# --------------------------------------------------------------------------- #


def _enable(monkeypatch):
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "graph_routing_enabled", True, raising=False)
    monkeypatch.setattr(settings, "graph_routing_classes", None, raising=False)
    monkeypatch.setattr(
        settings, "graph_routing_budget_seconds", 15.0, raising=False
    )


def _capture_scope(monkeypatch):
    """Record the scope `retrieve` hands to the policy layer."""
    from app.retrieval import retriever

    seen = {}

    def _attempt(question, *, top_k=None, filters=None, source_type=None, **kw):
        seen["filters"] = filters
        seen["source_type"] = source_type
        return policy.GraphAttempt(policy.ANSWERED, blocks=["graph"])

    monkeypatch.setattr(policy, "attempt", _attempt)
    monkeypatch.setattr(retriever, "search", lambda *a, **kw: [])
    monkeypatch.setattr(retriever, "dual_search", lambda *a, **kw: [])
    monkeypatch.setattr(retriever, "embed_query", lambda *a, **kw: [0.0])
    return seen


def test_retrieve_forwards_the_scope_rather_than_deciding_itself(monkeypatch):
    """The call site must not re-implement the check; a dimension added later
    would be forgotten there."""
    from app.retrieval import retriever

    _enable(monkeypatch)
    seen = _capture_scope(monkeypatch)
    pinned = _source_filter("pdf")

    retriever.retrieve("q", filters=[pinned], source_type="pdf", n=3)
    assert seen["filters"] == [pinned]
    assert seen["source_type"] == "pdf"


def test_retrieve_falls_back_when_the_scope_is_unsupported(monkeypatch):
    """The real path, with the real policy: a scoped query is answered by
    existing retrieval, and the graph contributes nothing."""
    from app.retrieval import retriever

    _enable(monkeypatch)
    graph_ran = []
    monkeypatch.setattr(
        policy, "_attempt",
        lambda *a, **kw: graph_ran.append(1) or policy.GraphAttempt(
            policy.ANSWERED, blocks=["graph"]
        ),
    )
    monkeypatch.setattr(retriever, "search", lambda *a, **kw: [])
    monkeypatch.setattr(retriever, "dual_search", lambda *a, **kw: [])
    monkeypatch.setattr(retriever, "embed_query", lambda *a, **kw: [0.0])

    blocks = retriever.retrieve(
        "What projects are funded by DBT?", source_type="pdf", n=3
    )
    assert graph_ran == [], "the graph must not have run"
    assert blocks == [], "existing retrieval answered (it found nothing here)"


def test_an_unscoped_query_still_reaches_the_graph(monkeypatch):
    from app.retrieval import retriever

    _enable(monkeypatch)
    _capture_scope(monkeypatch)
    assert retriever.retrieve("What projects are funded by DBT?", n=3) == ["graph"]
