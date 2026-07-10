"""Unit tests for title-lookup -> content chaining.

Covers the content-question heuristic (format hint or interrogative), the
exactly-one-match confidence rule, and fail-open on catalog errors. The
catalog is stubbed; no MySQL, Qdrant, or LLM.
"""

from __future__ import annotations

from app.ingestion import state
from app.retrieval import drupal_router as dr
from app.retrieval import query_processor as qp


def _rec(document_id="d1", title="Thoothukudi report"):
    return state.StateRecord(
        document_id=document_id, source_type="website", source_key="k",
        fingerprint="f", title=title, url=f"https://t/{document_id}",
    )


def _lookup(**kw):
    kw.setdefault("search_query", "x")
    kw.setdefault("intent", "structured")
    kw.setdefault("operation", "lookup")
    kw.setdefault("title_contains", "Thoothukudi")
    return qp.QueryAnalysis(**kw)


def test_chains_on_interrogative_with_single_match(monkeypatch):
    seen: dict = {}
    monkeypatch.setattr(
        state, "list_documents", lambda **kw: seen.update(kw) or [_rec()]
    )
    out = dr.resolve_lookup_document(
        _lookup(), "what does the Thoothukudi report say about emissions?"
    )
    assert out == "d1"
    assert seen["title_contains"] == "Thoothukudi"
    assert seen["limit"] == 3
    assert seen["entity_type"] == "node"


def test_chains_on_summary_format_without_interrogative(monkeypatch):
    monkeypatch.setattr(state, "list_documents", lambda **kw: [_rec()])
    out = dr.resolve_lookup_document(
        _lookup(answer_format="summary"), "show me the article titled Thoothukudi"
    )
    assert out == "d1"


def test_browse_question_does_not_chain(monkeypatch):
    def no_db(**kw):
        raise AssertionError("catalog must not be queried for a browse lookup")

    monkeypatch.setattr(state, "list_documents", no_db)
    out = dr.resolve_lookup_document(
        _lookup(), "show me the article titled Thoothukudi"
    )
    assert out is None


def test_ambiguous_and_missing_matches_do_not_chain(monkeypatch):
    monkeypatch.setattr(state, "list_documents", lambda **kw: [_rec("d1"), _rec("d2")])
    assert dr.resolve_lookup_document(_lookup(), "what does it say?") is None

    monkeypatch.setattr(state, "list_documents", lambda **kw: [])
    assert dr.resolve_lookup_document(_lookup(), "what does it say?") is None


def test_non_lookup_or_untitled_does_not_chain(monkeypatch):
    def no_db(**kw):
        raise AssertionError("catalog must not be queried")

    monkeypatch.setattr(state, "list_documents", no_db)
    assert dr.resolve_lookup_document(_lookup(operation="list"), "what?") is None
    assert dr.resolve_lookup_document(_lookup(title_contains=None), "what?") is None
    assert dr.resolve_lookup_document(None, "what?") is None


def test_catalog_error_falls_back(monkeypatch):
    def boom(**kw):
        raise RuntimeError("db down")

    monkeypatch.setattr(state, "list_documents", boom)
    assert dr.resolve_lookup_document(_lookup(), "what does it say?") is None
