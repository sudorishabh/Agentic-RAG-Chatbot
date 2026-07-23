"""Unit tests for facet-filter relaxation in retrieve().

LLM-extracted facet filters (theme / author / source_type / date) are applied
as hard AND conditions. When they lift terms straight out of the question — a
title query parsed into theme="SDG 7", author="TERI" — those literals rarely
equal the stored metadata and their intersection can be empty even when the
corpus plainly answers the question. retrieve() must then retry once without the
facets rather than returning nothing (which the pipeline turns into a blanket
refusal). Relaxation is precision-preserving: it fires only on a total miss.
Qdrant is stubbed; no network.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.retrieval import retriever
from app.retrieval.hybrid_search import Candidate


def _cand(id, payload=None):
    return Candidate(id=id, score=0.9, payload=payload or {})


def _settings(**overrides):
    base = dict(
        retrieval_top_k=6, retrieval_candidate_k=40, prefer_website_enabled=False,
        multi_query_enabled=False, multi_query_paraphrases=2, rerank_table_boost=0.15,
        keyword_leg_enabled=False, corrective_loop_enabled=False,
        corrective_min_score=0.2,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _wire(monkeypatch, *, settings, search_fn):
    monkeypatch.setattr(retriever, "get_settings", lambda: settings)
    monkeypatch.setattr(retriever, "search", search_fn)
    monkeypatch.setattr(retriever, "rerank", lambda q, cands, **kw: list(cands))
    monkeypatch.setattr(
        retriever, "build_context", lambda ranked, *, limit, segregate: list(ranked)
    )


def test_zero_under_facets_retries_without_them(monkeypatch):
    calls: list = []

    def fake_search(*a, **k):
        calls.append(k.get("extra_filter"))
        # Empty while facets are applied; the corpus answer only surfaces once
        # they are dropped.
        return [] if k.get("extra_filter") else [_cand("a"), _cand("b")]

    _wire(monkeypatch, settings=_settings(), search_fn=fake_search)
    out = retriever.retrieve("a title query", query_vector=[0.1], filters=["facet"])

    assert calls == [["facet"], None]  # faceted pull, then one relaxed retry
    assert [b.id for b in out] == ["a", "b"]


def test_facet_hits_are_not_relaxed(monkeypatch):
    calls: list = []

    def fake_search(*a, **k):
        calls.append(k.get("extra_filter"))
        return [_cand("scoped")]

    _wire(monkeypatch, settings=_settings(), search_fn=fake_search)
    out = retriever.retrieve("scoped query", query_vector=[0.1], filters=["facet"])

    assert calls == [["facet"]]  # no relaxed retry — the facet pull found matches
    assert [b.id for b in out] == ["scoped"]


def test_no_facets_no_relaxation(monkeypatch):
    calls: list = []

    def fake_search(*a, **k):
        calls.append(k.get("extra_filter"))
        return []

    _wire(monkeypatch, settings=_settings(), search_fn=fake_search)
    out = retriever.retrieve("unanswerable", query_vector=[0.1])

    assert calls == [None]  # a genuine empty pull is not retried
    assert out == []
