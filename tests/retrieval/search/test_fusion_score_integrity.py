"""Regression tests: rank fusion must not corrupt the semantic score.

``rrf`` fuses on *rank*, so its output is on a reciprocal-rank scale
(~0.016-0.033) that has nothing to do with cosine similarity. Several consumers
read a candidate's semantic relevance to compare it against a *cosine-scaled*
threshold:

- ``context_builder`` gates website slots on ``website_chunk_floor`` (0.30) and
  the extra PDF slot on ``pdf_high_confidence_floor`` (0.5);
- ``retriever`` opens the corrective loop below ``corrective_min_score`` (0.2);
- ``reranker`` drops candidates below ``rerank_score_threshold``.

Before the fix these read the fused value, so merely enabling the keyword leg or
multi-query silently starved the website group and pinned the corrective loop
open. The invariant enforced here: ``semantic_score`` is the raw dense/reranker
relevance and survives fusion untouched, while the fused ranking value lives in
``fusion_score`` and orders the candidates. Qdrant and the LLM are stubbed.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.retrieval import retriever
from app.retrieval.context.builder import build_context
from app.retrieval.search.fusion import rrf
from app.retrieval.search.hybrid_search import Candidate, _to_candidate
from app.retrieval.search.reranker import rerank

# The two floors this whole file is about, at their production defaults.
WEBSITE_FLOOR = 0.30
CORRECTIVE_MIN = 0.2

# A rank-1/rank-2 RRF contribution, for asserting on the fused scale directly.
RRF_RANK1 = 1 / 61
RRF_RANK2 = 1 / 62


def _point(id_, score, payload=None, vector=None):
    """A Qdrant scored point, as ``search()`` receives it."""
    return SimpleNamespace(
        id=id_, score=score, payload=payload or {}, vector=vector or [1.0, 0.0]
    )


def _searched(id_, score, source_type="website", vector=None):
    """A candidate exactly as the search layer produces it."""
    return _to_candidate(
        _point(
            id_, score,
            payload={
                "source_type": source_type,
                "document_id": id_,
                "chunk_text": f"body text for {id_}",
            },
            vector=vector,
        )
    )


# --------------------------------------------------------------------------- #
# 1. Dense-only retrieval preserves semantic scoring.
# --------------------------------------------------------------------------- #

def test_dense_only_retrieval_preserves_semantic_score():
    cand = _searched("a", 0.72)
    assert cand.semantic_score == pytest.approx(0.72)
    assert cand.fusion_score == 0.0  # nothing fused this candidate

    ranked = rerank("solar capacity", [cand])
    assert ranked[0].semantic_score == pytest.approx(0.72)
    assert ranked[0].semantic_score >= WEBSITE_FLOOR


# --------------------------------------------------------------------------- #
# 4/6. RRF reorders without touching the semantic scale, and its own ranking
#      behaviour is unchanged.
# --------------------------------------------------------------------------- #

def test_rrf_reorders_without_corrupting_semantic_scores():
    strong = _searched("strong", 0.72)   # better cosine, only in one list
    consensus = _searched("consensus", 0.55)  # weaker cosine, in both lists

    fused = rrf([[strong, consensus], [consensus]])
    by_id = {c.id: c for c in fused}

    # Consensus wins the ranking — that is RRF doing its job.
    assert [c.id for c in fused] == ["consensus", "strong"]
    # ...but neither candidate's semantic relevance moved.
    assert by_id["strong"].semantic_score == pytest.approx(0.72)
    assert by_id["consensus"].semantic_score == pytest.approx(0.55)
    # ...and both still clear a cosine-scaled floor.
    assert min(c.semantic_score for c in fused) >= WEBSITE_FLOOR

    # The fused value is on its own scale, in its own field.
    assert by_id["consensus"].fusion_score == pytest.approx(RRF_RANK2 + RRF_RANK1)
    assert by_id["strong"].fusion_score == pytest.approx(RRF_RANK1)


def test_rrf_ranking_contract_is_unchanged():
    """The pre-existing contract: fused ordering, id-dedup, first-sighting
    payload, deterministic ties, and ``score`` carrying the fused value."""
    a, b, c = _searched("a", 0.9), _searched("b", 0.9), _searched("c", 0.9)
    fused = rrf([[a, b, c], [c, _searched("d", 0.9)]])

    assert [x.id for x in fused][0] == "c"
    assert {x.id for x in fused} == {"a", "b", "c", "d"}
    assert fused[0].score == pytest.approx(1 / 63 + RRF_RANK1)

    first = _searched("x", 0.9)
    first.payload["chunk_text"] = "first"
    second = _searched("x", 0.9)
    second.payload["chunk_text"] = "second"
    deduped = rrf([[first], [second]])
    assert len(deduped) == 1 and deduped[0].payload["chunk_text"] == "first"

    assert [x.id for x in rrf([[_searched("b", 0.9)], [_searched("a", 0.9)]])] == ["a", "b"]


def test_rerank_after_fusion_keeps_the_dense_scale():
    fused = rrf([[_searched("a", 0.72)], [_searched("b", 0.55)]])
    ranked = rerank("solar capacity", fused)
    assert {c.id: c.semantic_score for c in ranked} == {
        "a": pytest.approx(0.72),
        "b": pytest.approx(0.55),
    }


# --------------------------------------------------------------------------- #
# 2/3. A legitimate website candidate survives the floor when a recall leg is on.
# --------------------------------------------------------------------------- #

def _settings(**overrides):
    base = dict(
        retrieval_top_k=6, retrieval_candidate_k=40, website_candidate_k=20,
        prefer_website_enabled=True, multi_query_enabled=False,
        multi_query_paraphrases=2, keyword_leg_enabled=False,
        corrective_loop_enabled=False, corrective_min_score=CORRECTIVE_MIN,
        rerank_table_boost=0.15, graph_routing_enabled=False,
        # reranker
        reranker_provider="embedding", rerank_score_threshold=0.0,
        rerank_relevance_tolerance=0.03, rerank_volatile_tolerance_multiplier=2.0,
        rerank_substance_ratio=1.5,
        # context builder
        context_token_budget=9000, dedup_cosine_threshold=0.92,
        website_max_slots=2, website_chunk_floor=WEBSITE_FLOOR,
        pdf_max_slots=2, pdf_high_confidence_floor=0.5,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _wire(monkeypatch, settings, *, website, pdfs, extra_leg):
    """Wire ``retrieve`` onto stub pulls but the *real* rrf / rerank / context
    builder, so the floors are exercised end to end."""
    from app.retrieval.context import builder as context_builder
    from app.retrieval.search import reranker

    for module in (retriever, reranker, context_builder):
        monkeypatch.setattr(module, "get_settings", lambda s=settings: s)
    monkeypatch.setattr(retriever, "dual_search", lambda *a, **k: [website] + pdfs)
    monkeypatch.setattr(retriever, "search", lambda *a, **k: [website] + pdfs)
    monkeypatch.setattr(retriever, "_observe_in_shadow", lambda *a, **k: None)
    monkeypatch.setattr(retriever, "keyword_search", lambda *a, **k: extra_leg)
    monkeypatch.setattr(retriever, "paraphrases", lambda q, n: ["p1"])
    monkeypatch.setattr(retriever, "paraphrase_search", lambda q, **k: extra_leg)


QUERY = "what are the impacts of biofuel adoption on rural incomes"


@pytest.mark.parametrize(
    "leg", ["keyword_leg_enabled", "multi_query_enabled"]
)
def test_recall_leg_does_not_starve_the_website_group(monkeypatch, leg):
    """A website chunk at cosine 0.72 clears the 0.30 floor whether or not a
    second retrieval leg was fused in."""
    settings = _settings(**{leg: True})
    website = _searched("w1", 0.72, source_type="website", vector=[1.0, 0.0])
    pdf = _searched("p1", 0.61, source_type="pdf_attachment", vector=[0.0, 1.0])
    # The extra leg ranks the PDF first, so fusion genuinely reorders.
    _wire(monkeypatch, settings, website=website, pdfs=[pdf], extra_leg=[pdf])

    blocks = retriever.retrieve(QUERY, query_vector=[0.1, 0.2])

    sources = [b.payload.get("source_type") for b in blocks]
    assert "website" in sources, f"website chunk lost to the floor ({leg} on)"
    assert sources[0] == "website"  # segregated context leads with website


def test_dense_only_and_fused_admit_the_same_website_block(monkeypatch):
    """The recall leg must not change *which* groups are representable."""
    website = _searched("w1", 0.72, source_type="website", vector=[1.0, 0.0])
    pdf = _searched("p1", 0.61, source_type="pdf_attachment", vector=[0.0, 1.0])

    _wire(monkeypatch, _settings(), website=website, pdfs=[pdf], extra_leg=[])
    dense_only = retriever.retrieve(QUERY, query_vector=[0.1, 0.2])

    _wire(monkeypatch, _settings(keyword_leg_enabled=True),
          website=website, pdfs=[pdf], extra_leg=[pdf])
    fused = retriever.retrieve(QUERY, query_vector=[0.1, 0.2])

    assert [b.payload["document_id"] for b in dense_only] == \
           [b.payload["document_id"] for b in fused]


def test_website_floor_still_rejects_a_genuinely_weak_chunk(monkeypatch):
    """The fix must not defeat the floor: a 0.05-cosine website chunk stays out."""
    settings = _settings(keyword_leg_enabled=True)
    website = _searched("w1", 0.05, source_type="website", vector=[1.0, 0.0])
    pdf = _searched("p1", 0.61, source_type="pdf_attachment", vector=[0.0, 1.0])
    _wire(monkeypatch, settings, website=website, pdfs=[pdf], extra_leg=[pdf])

    blocks = retriever.retrieve(QUERY, query_vector=[0.1, 0.2])
    assert [b.payload.get("source_type") for b in blocks] == ["pdf_attachment"]


# --------------------------------------------------------------------------- #
# 5. The corrective loop is not tripped merely because fusion ran.
# --------------------------------------------------------------------------- #

def test_corrective_loop_not_triggered_by_fusion(monkeypatch):
    settings = _settings(keyword_leg_enabled=True, corrective_loop_enabled=True)
    website = _searched("w1", 0.72, source_type="website", vector=[1.0, 0.0])
    pdf = _searched("p1", 0.61, source_type="pdf_attachment", vector=[0.0, 1.0])
    _wire(monkeypatch, settings, website=website, pdfs=[pdf], extra_leg=[pdf])

    def _boom(*a, **k):
        raise AssertionError(
            "corrective loop ran: the top semantic score was read off the "
            "fused scale, not the dense one"
        )

    monkeypatch.setattr(retriever, "corrective_requery", _boom)
    assert retriever.retrieve(QUERY, query_vector=[0.1, 0.2])


def test_corrective_loop_still_fires_on_genuinely_weak_results(monkeypatch):
    """The loop must keep working for the case it exists for."""
    settings = _settings(keyword_leg_enabled=True, corrective_loop_enabled=True)
    website = _searched("w1", 0.05, source_type="website", vector=[1.0, 0.0])
    pdf = _searched("p1", 0.08, source_type="pdf_attachment", vector=[0.0, 1.0])
    _wire(monkeypatch, settings, website=website, pdfs=[pdf], extra_leg=[pdf])

    calls: list = []
    monkeypatch.setattr(
        retriever, "corrective_requery",
        lambda q, ranked, **k: calls.append(q) or list(ranked),
    )
    retriever.retrieve(QUERY, query_vector=[0.1, 0.2])
    assert calls == [QUERY]


# --------------------------------------------------------------------------- #
# The floor itself, isolated from retrieval.
# --------------------------------------------------------------------------- #

def test_build_context_floor_reads_the_semantic_score(monkeypatch):
    from app.retrieval.context import builder as context_builder

    settings = _settings()
    monkeypatch.setattr(context_builder, "get_settings", lambda: settings)

    admitted = Candidate(
        id="w", score=RRF_RANK1, semantic_score=0.72, vector=[1.0, 0.0],
        payload={"source_type": "website", "chunk_text": "text", "document_id": "w"},
    )
    blocks = build_context([admitted], limit=6, segregate=True)
    assert [b.payload["document_id"] for b in blocks] == ["w"]
