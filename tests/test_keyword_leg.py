"""Unit tests for the full-text keyword leg.

Covers salient-term extraction (quoted phrases, acronyms, years, proper-noun
bigrams, dedup), the MatchText filter on the extra pull, RRF fusion with the
dense pull in ``retrieve()``, and fail-open when the full-text index is
missing. Qdrant is stubbed; no network.
"""

from __future__ import annotations

from types import SimpleNamespace

import app.rag as rag
from app.retrieval.hybrid_search import Candidate


def _cand(id, payload=None):
    return Candidate(id=id, score=0.9, payload=payload or {})


# --------------------------------------------------------------------------- #
# Salient-term extraction.
# --------------------------------------------------------------------------- #

def test_extract_quoted_acronyms_years_bigrams():
    out = rag._extract_key_terms(
        'what does the "solar mission" report say about GHG output in Tamil Nadu in 2024'
    )
    assert out == "solar mission Tamil Nadu GHG 2024"


def test_extract_dedupes_case_insensitively():
    out = rag._extract_key_terms('"GHG emissions" and GHG levels of 2024, again 2024')
    assert out == "GHG emissions GHG 2024"


def test_extract_none_when_no_salient_terms():
    assert rag._extract_key_terms("what are the impacts of biofuel adoption") is None
    assert rag._extract_key_terms("") is None


# --------------------------------------------------------------------------- #
# _keyword_search — MatchText condition and fail-open.
# --------------------------------------------------------------------------- #

def test_keyword_search_builds_matchtext_condition(monkeypatch):
    seen: dict = {}

    def fake_search(query, **kw):
        seen.update(kw)
        return [_cand("k1")]

    monkeypatch.setattr(rag, "search", fake_search)
    out = rag._keyword_search(
        "q", "GHG 2024", tenant_id="default", user_groups=["public"],
        filters=["prior"], query_vector=[0.1], limit=40,
    )

    assert [c.id for c in out] == ["k1"]
    prior, cond = seen["extra_filter"]
    assert prior == "prior"  # existing facet filters preserved
    assert cond.key == "chunk_text" and cond.match.text == "GHG 2024"
    assert seen["limit"] == 40 and seen["query_vector"] == [0.1]


def test_keyword_search_fails_open_without_index(monkeypatch):
    def boom(query, **kw):
        raise RuntimeError("Index required but not found for chunk_text")

    monkeypatch.setattr(rag, "search", boom)
    out = rag._keyword_search(
        "q", "GHG", tenant_id="default", user_groups=["public"],
        filters=None, query_vector=[0.1], limit=40,
    )
    assert out == []


# --------------------------------------------------------------------------- #
# retrieve() wiring — keyword hits fuse with the dense pull.
# --------------------------------------------------------------------------- #

def _settings(**overrides):
    base = dict(
        retrieval_top_k=6, retrieval_candidate_k=40, prefer_website_enabled=False,
        multi_query_enabled=False, multi_query_paraphrases=2, rerank_table_boost=0.15,
        keyword_leg_enabled=True,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _wire(monkeypatch, *, settings, base_candidates):
    monkeypatch.setattr(rag, "get_settings", lambda: settings)
    monkeypatch.setattr(rag, "search", lambda *a, **k: base_candidates)
    monkeypatch.setattr(rag, "rerank", lambda q, cands, **kw: cands)
    monkeypatch.setattr(
        rag, "build_context", lambda ranked, *, limit, segregate: list(ranked)
    )


def test_keyword_leg_fuses_with_dense_pull(monkeypatch):
    _wire(monkeypatch, settings=_settings(), base_candidates=[_cand("a"), _cand("b")])
    pulls: list = []
    monkeypatch.setattr(
        rag, "_keyword_search",
        lambda q, terms, **kw: pulls.append(terms) or [_cand("b"), _cand("k")],
    )

    out = rag.retrieve("what happened at COP in 2024", query_vector=[0.1])

    assert pulls == ["COP 2024"]
    assert [b.id for b in out][0] == "b"  # consensus candidate leads after RRF
    assert {b.id for b in out} == {"a", "b", "k"}


def test_keyword_leg_empty_hits_keep_dense_only(monkeypatch):
    base = [_cand("a")]
    _wire(monkeypatch, settings=_settings(), base_candidates=base)
    monkeypatch.setattr(rag, "_keyword_search", lambda q, terms, **kw: [])

    out = rag.retrieve("what happened at COP in 2024", query_vector=[0.1])
    assert [b.id for b in out] == ["a"]


def test_keyword_leg_skipped_without_terms_or_flag(monkeypatch):
    def no_keyword(*a, **kw):
        raise AssertionError("keyword search must not run")

    base = [_cand("a")]

    # Flag on, but nothing salient in the query.
    _wire(monkeypatch, settings=_settings(), base_candidates=base)
    monkeypatch.setattr(rag, "_keyword_search", no_keyword)
    rag.retrieve("what are the impacts of biofuel adoption", query_vector=[0.1])

    # Salient terms, but flag off.
    _wire(monkeypatch, settings=_settings(keyword_leg_enabled=False), base_candidates=base)
    monkeypatch.setattr(rag, "_keyword_search", no_keyword)
    rag.retrieve("what happened at COP in 2024", query_vector=[0.1])
