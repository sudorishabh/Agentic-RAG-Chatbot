"""Unit tests for the one-shot corrective retrieval loop.

Covers the confidence gate in retrieve() (flag off, score above threshold,
score below threshold), the requery composition (reformulate -> search ->
RRF-fuse -> second rerank), and every fail-open path. LLM, embedder, and
Qdrant are stubbed; no network.
"""

from __future__ import annotations

from types import SimpleNamespace

import app.ingestion.embedder as embedder
import app.rag as rag
from app.retrieval.hybrid_search import Candidate


def _cand(id, semantic_score=0.5, text="passage text"):
    return Candidate(id=id, score=semantic_score, semantic_score=semantic_score,
                     payload={"chunk_text": text})


def _settings(**overrides):
    base = dict(
        retrieval_top_k=6, retrieval_candidate_k=40, prefer_website_enabled=False,
        multi_query_enabled=False, multi_query_paraphrases=2,
        rerank_table_boost=0.15, keyword_leg_enabled=False,
        corrective_loop_enabled=True, corrective_min_score=0.2,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _wire(monkeypatch, *, settings, ranked):
    monkeypatch.setattr(rag, "get_settings", lambda: settings)
    monkeypatch.setattr(rag, "search", lambda *a, **k: list(ranked))
    monkeypatch.setattr(rag, "rerank", lambda q, cands, **kw: list(ranked))
    monkeypatch.setattr(
        rag, "build_context", lambda cands, *, limit, segregate: list(cands)
    )


# --------------------------------------------------------------------------- #
# The confidence gate in retrieve().
# --------------------------------------------------------------------------- #

def test_low_confidence_triggers_corrective(monkeypatch):
    weak = [_cand("a", semantic_score=0.1)]
    _wire(monkeypatch, settings=_settings(), ranked=weak)
    calls: list = []
    monkeypatch.setattr(
        rag, "_corrective_requery",
        lambda q, ranked, **kw: calls.append(q) or [_cand("better", 0.8)],
    )

    out = rag.retrieve("hard question", query_vector=[0.1])
    assert calls == ["hard question"]
    assert [b.id for b in out] == ["better"]


def test_confident_or_disabled_skips_corrective(monkeypatch):
    def no_requery(*a, **kw):
        raise AssertionError("corrective must not run")

    strong = [_cand("a", semantic_score=0.9)]
    _wire(monkeypatch, settings=_settings(), ranked=strong)
    monkeypatch.setattr(rag, "_corrective_requery", no_requery)
    rag.retrieve("q", query_vector=[0.1])

    weak = [_cand("a", semantic_score=0.1)]
    _wire(monkeypatch, settings=_settings(corrective_loop_enabled=False), ranked=weak)
    monkeypatch.setattr(rag, "_corrective_requery", no_requery)
    rag.retrieve("q", query_vector=[0.1])

    _wire(monkeypatch, settings=_settings(), ranked=[])  # nothing ranked at all
    monkeypatch.setattr(rag, "_corrective_requery", no_requery)
    assert rag.retrieve("q", query_vector=[0.1]) == []


# --------------------------------------------------------------------------- #
# _corrective_requery composition.
# --------------------------------------------------------------------------- #

def test_requery_fuses_and_reranks_once(monkeypatch):
    ranked = [_cand("a"), _cand("b")]
    monkeypatch.setattr(rag, "_corrective_query", lambda q, r: "reformulated query")
    monkeypatch.setattr(embedder, "embed_query", lambda q: [0.9])
    searched: list = []

    def fake_search(query, **kw):
        searched.append((query, kw.get("query_vector")))
        return [_cand("b"), _cand("c")]

    monkeypatch.setattr(rag, "search", fake_search)
    reranked: list = []
    monkeypatch.setattr(
        rag, "rerank",
        lambda q, cands, **kw: reranked.extend(cands) or list(cands),
    )

    out = rag._corrective_requery(
        "original", ranked, tenant_id="default", user_groups=["public"],
        filters=None, limit=40, table_boost=0.0,
    )

    assert searched == [("reformulated query", [0.9])]
    assert {c.id for c in reranked} == {"a", "b", "c"}  # RRF union, deduped
    assert out[0].id == "b"  # consensus of both rankings leads


def test_requery_fail_open_paths(monkeypatch):
    ranked = [_cand("a")]

    # No reformulation -> unchanged, search never runs.
    monkeypatch.setattr(rag, "_corrective_query", lambda q, r: None)

    def no_search(*a, **kw):
        raise AssertionError("search must not run without a reformulation")

    monkeypatch.setattr(rag, "search", no_search)
    assert rag._corrective_requery(
        "q", ranked, tenant_id="d", user_groups=["public"], filters=None,
        limit=40, table_boost=0.0,
    ) is ranked

    # Requery finds nothing new -> unchanged, no second rerank.
    monkeypatch.setattr(rag, "_corrective_query", lambda q, r: "other")
    monkeypatch.setattr(embedder, "embed_query", lambda q: [0.9])
    monkeypatch.setattr(rag, "search", lambda *a, **kw: [_cand("a")])

    def no_rerank(*a, **kw):
        raise AssertionError("rerank must not run when nothing new arrived")

    monkeypatch.setattr(rag, "rerank", no_rerank)
    assert rag._corrective_requery(
        "q", ranked, tenant_id="d", user_groups=["public"], filters=None,
        limit=40, table_boost=0.0,
    ) is ranked

    # Any exception -> unchanged.
    def boom(*a, **kw):
        raise RuntimeError("qdrant down")

    monkeypatch.setattr(rag, "search", boom)
    assert rag._corrective_requery(
        "q", ranked, tenant_id="d", user_groups=["public"], filters=None,
        limit=40, table_boost=0.0,
    ) is ranked


# --------------------------------------------------------------------------- #
# Reformulation call.
# --------------------------------------------------------------------------- #

class _FakeStructured:
    def __init__(self, query):
        self._query = query

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        if isinstance(self._query, Exception):
            raise self._query
        return SimpleNamespace(query=self._query)


def test_corrective_query_returns_reformulation(monkeypatch):
    import app.generation.llm_client as llm_client

    monkeypatch.setattr(
        llm_client, "get_structured_llm", lambda: _FakeStructured("  better query ")
    )
    assert rag._corrective_query("original", [_cand("a")]) == "better query"


def test_corrective_query_rejects_echo_and_errors(monkeypatch):
    import app.generation.llm_client as llm_client

    monkeypatch.setattr(
        llm_client, "get_structured_llm", lambda: _FakeStructured("ORIGINAL")
    )
    assert rag._corrective_query("original", []) is None

    monkeypatch.setattr(
        llm_client, "get_structured_llm", lambda: _FakeStructured(RuntimeError("down"))
    )
    assert rag._corrective_query("original", []) is None
