"""Unit tests for the scoped-summary route.

Covers scope-filter derivation from the unified analysis, the map-batch
packing math, direct-vs-map-reduce path selection, fall-through on empty or
unresolvable scopes, and the result/citation shape. Catalog, Qdrant, and LLM
calls are all stubbed; no network.
"""

from __future__ import annotations

from datetime import datetime

from app.pipeline import summarize as sm
from app.retrieval import query_processor as qp


def _analysis(**kw):
    kw.setdefault("search_query", "summarize the Climate theme")
    kw.setdefault("intent", "scoped_summary")
    return qp.QueryAnalysis(**kw)


def _payload(doc_id, text="Some content.", title=None, published="2024-03-15T00:00:00"):
    return {
        "document_id": doc_id,
        "title": title or f"Title {doc_id}",
        "source_url": f"https://t/{doc_id}",
        "published_at": published,
        "chunk_text": text,
    }


# --------------------------------------------------------------------------- #
# Scope filters — what the analysis translates to in catalog kwargs.
# --------------------------------------------------------------------------- #

def test_scope_filters_theme_resolves_to_term_uuids(monkeypatch):
    monkeypatch.setattr(
        sm.terms, "resolve_terms", lambda name: [{"term_uuid": "t1", "name": "Climate"}]
    )
    monkeypatch.setattr(sm.terms, "descendant_uuids", lambda uuids: list(uuids))
    filters = sm._scope_filters(_analysis(theme="Climate"))
    assert filters == {"term_uuids": ["t1"]}


def test_scope_filters_theme_expands_to_descendant_subthemes(monkeypatch):
    monkeypatch.setattr(
        sm.terms, "resolve_terms", lambda name: [{"term_uuid": "parent", "name": "Environment"}]
    )
    monkeypatch.setattr(
        sm.terms, "descendant_uuids", lambda uuids: list(uuids) + ["air"]
    )
    filters = sm._scope_filters(_analysis(theme="Environment"))
    assert filters == {"term_uuids": ["parent", "air"]}


def test_scope_filters_theme_falls_back_to_theme_name(monkeypatch):
    monkeypatch.setattr(sm.terms, "resolve_terms", lambda name: [])
    filters = sm._scope_filters(_analysis(theme="Oceans"))
    assert filters == {"theme": "Oceans"}


def test_scope_filters_unknown_bundle_dropped_dates_kept(monkeypatch):
    filters = sm._scope_filters(
        _analysis(bundle="widgets", date_from="2024-01-01", date_to="2025-01-01")
    )
    # A summary scope is soft: an unknown bundle must not zero the set.
    assert filters == {
        "published_from": datetime(2024, 1, 1),
        "published_to": datetime(2025, 1, 1),
    }


def test_scope_filters_bundle_author_title(monkeypatch):
    filters = sm._scope_filters(
        _analysis(bundle="paper", author="Sharma", title_contains="solar")
    )
    assert filters == {
        "bundle": "research_papers",
        "author": "Sharma",
        "title_contains": "solar",
    }


def test_scope_filters_no_scope_returns_none():
    assert sm._scope_filters(_analysis()) is None


# --------------------------------------------------------------------------- #
# Map-batch packing.
# --------------------------------------------------------------------------- #

def test_batch_documents_packs_by_token_budget():
    docs = [
        sm._Doc(document_id=f"d{i}", title="t", url=None, published="", text="x" * 8000)
        for i in range(5)
    ]  # ~2050 est. tokens each -> 2 per 6k batch
    batches = sm._batch_documents(docs)
    assert [len(b) for b in batches] == [2, 2, 1]
    assert [d.document_id for b in batches for d in b] == [f"d{i}" for i in range(5)]


def test_batch_documents_oversized_doc_gets_own_batch():
    docs = [
        sm._Doc(document_id="big", title="t", url=None, published="", text="x" * 60000),
        sm._Doc(document_id="small", title="t", url=None, published="", text="x" * 100),
    ]
    assert [[d.document_id for d in b] for b in sm._batch_documents(docs)] == [
        ["big"], ["small"]
    ]


# --------------------------------------------------------------------------- #
# summarize_scope — path selection, fall-through, result shape.
# --------------------------------------------------------------------------- #

def _stub_scope(monkeypatch, ids, payloads):
    monkeypatch.setattr(
        sm.terms, "resolve_terms", lambda name: [{"term_uuid": "t1", "name": "Climate"}]
    )
    monkeypatch.setattr(
        sm.catalog, "document_ids_in_scope", lambda **kw: ids
    )
    monkeypatch.setattr(
        sm.scoped_retrieval, "lead_parents", lambda i, **kw: payloads
    )


def test_small_scope_uses_direct_path(monkeypatch):
    ids = ["d1", "d2"]
    _stub_scope(monkeypatch, ids, {i: _payload(i) for i in ids})
    calls = []
    monkeypatch.setattr(
        sm, "_summarize_direct", lambda q, docs: calls.append(len(docs)) or "Overview [1][2]."
    )

    def no_map(q, docs):
        raise AssertionError("map-reduce must not run for small scopes")

    monkeypatch.setattr(sm, "_summarize_map_reduce", no_map)

    out = sm.summarize_scope(_analysis(theme="Climate"))

    assert calls == [2]
    assert out["answer"] == "Overview [1][2]."
    assert out["intent"] == "scoped_summary"
    assert out["used_chunks"] == 2
    assert [c["document_id"] for c in out["citations"]] == ["d1", "d2"]
    assert out["citations"][0]["type"] == "website"
    assert out["citations"][0]["url"] == "https://t/d1"


def test_large_scope_uses_map_reduce(monkeypatch):
    ids = [f"d{i}" for i in range(8)]
    _stub_scope(monkeypatch, ids, {i: _payload(i) for i in ids})

    def no_direct(q, docs):
        raise AssertionError("direct path must not run for large scopes")

    monkeypatch.setattr(sm, "_summarize_direct", no_direct)
    monkeypatch.setattr(sm, "_summarize_map_reduce", lambda q, docs: "Thematic summary.")

    out = sm.summarize_scope(_analysis(theme="Climate"))
    assert out["answer"] == "Thematic summary."
    assert out["used_chunks"] == 8


def test_empty_scope_falls_through(monkeypatch):
    _stub_scope(monkeypatch, [], {})
    assert sm.summarize_scope(_analysis(theme="Climate")) is None


def test_no_scope_falls_through(monkeypatch):
    assert sm.summarize_scope(_analysis()) is None
    assert sm.summarize_scope(None) is None


def test_blank_texts_fall_through(monkeypatch):
    ids = ["d1"]
    _stub_scope(monkeypatch, ids, {"d1": _payload("d1", text="   ")})
    assert sm.summarize_scope(_analysis(theme="Climate")) is None


def test_llm_failure_falls_through(monkeypatch):
    ids = ["d1"]
    _stub_scope(monkeypatch, ids, {"d1": _payload("d1")})

    def boom(q, docs):
        raise RuntimeError("llm down")

    monkeypatch.setattr(sm, "_summarize_direct", boom)
    assert sm.summarize_scope(_analysis(theme="Climate")) is None


def test_docs_missing_payloads_are_skipped(monkeypatch):
    ids = ["d1", "d2", "d3"]
    _stub_scope(monkeypatch, ids, {"d1": _payload("d1"), "d3": _payload("d3")})
    monkeypatch.setattr(sm, "_summarize_direct", lambda q, docs: "S.")

    out = sm.summarize_scope(_analysis(theme="Climate"))
    assert out["used_chunks"] == 2
    assert [c["document_id"] for c in out["citations"]] == ["d1", "d3"]
