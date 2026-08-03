"""Unit tests for the reranker's ranking priority.

Relevance bands first, recency inside a band, authority under that. The
`embedding` provider is used throughout so `_semantic_scores` just reads back
the candidate's own score — no model, no network.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.retrieval import reranker
from app.retrieval.hybrid_search import Candidate


def _cand(id: str, score: float, published: str | None = None, **payload) -> Candidate:
    body = {"chunk_text": f"text {id}", **payload}
    if published:
        body["published_at"] = published
    return Candidate(id=id, score=score, payload=body, vector=[0.1])


def _ids(candidates) -> list[str]:
    return [c.id for c in candidates]


@pytest.fixture
def settings(monkeypatch):
    cfg = SimpleNamespace(
        reranker_provider="embedding",
        rerank_score_threshold=0.0,
        rerank_relevance_tolerance=0.03,
        rerank_volatile_tolerance_multiplier=2.0,
    )
    monkeypatch.setattr(reranker, "get_settings", lambda: cfg)
    return cfg


def test_relevance_outranks_recency_across_bands(settings):
    """A clearly better old passage beats a newer one that barely matches."""
    out = reranker.rerank("q", [
        _cand("new", 0.60, "2025-01-01"),
        _cand("old", 0.90, "2019-01-01"),
    ])
    assert _ids(out) == ["old", "new"]


def test_recency_decides_inside_a_band(settings):
    """Two editions of the same report: comparable relevance, newest leads."""
    out = reranker.rerank("q", [
        _cand("2023-edition", 0.80, "2023-06-01"),
        _cand("2025-edition", 0.79, "2025-06-01"),
        _cand("2024-edition", 0.78, "2024-06-01"),
    ])
    assert _ids(out) == ["2025-edition", "2024-edition", "2023-edition"]


def test_a_gap_wider_than_the_tolerance_keeps_relevance_order(settings):
    """0.10 apart is a real relevance difference, not a tie to break on date."""
    out = reranker.rerank("q", [
        _cand("newer", 0.70, "2025-01-01"),
        _cand("better", 0.80, "2019-01-01"),
    ])
    assert _ids(out) == ["better", "newer"]


def test_bands_are_measured_from_the_leader_not_the_neighbour(settings):
    """Small steps must not chain: 0.76 is within tolerance of 0.78 but 0.04
    below the band leader, so it drops a band and its newer date cannot save
    it."""
    out = reranker.rerank("q", [
        _cand("leader", 0.80, "2019-01-01"),
        _cand("mate", 0.78, "2020-01-01"),
        _cand("drifted", 0.76, "2025-01-01"),
    ])
    assert _ids(out) == ["mate", "leader", "drifted"]


def test_an_undated_candidate_sits_between_the_dated_ones(settings):
    """Unknown publication date is neutral — it neither leads nor trails a band
    on a fact we do not have."""
    out = reranker.rerank("q", [
        _cand("undated", 0.79),
        _cand("old", 0.80, "2019-01-01"),
        _cand("new", 0.78, "2025-01-01"),
    ])
    assert _ids(out) == ["new", "undated", "old"]


def test_recency_is_ignored_when_no_candidate_is_dated(settings):
    """With nothing to compare, the band falls through to relevance order."""
    out = reranker.rerank("q", [_cand("b", 0.78), _cand("a", 0.80)])
    assert _ids(out) == ["a", "b"]


def test_authority_breaks_a_tie_under_recency(settings):
    out = reranker.rerank("q", [
        _cand("unknown", 0.80, "2024-01-01"),
        _cand("trusted", 0.79, "2024-01-01", source_authority=0.9),
    ])
    assert _ids(out) == ["trusted", "unknown"]


def test_unusable_authority_falls_back_to_neutral(settings):
    """A junk payload value must not throw or win — it reads as unknown, so the
    fine-grained relevance settles the tie."""
    out = reranker.rerank("q", [
        _cand("junk", 0.79, "2024-01-01", source_authority="very"),
        _cand("plain", 0.80, "2024-01-01"),
    ])
    assert _ids(out) == ["plain", "junk"]


def test_the_score_threshold_still_drops_candidates(settings):
    settings.rerank_score_threshold = 0.5
    out = reranker.rerank("q", [
        _cand("weak", 0.40, "2025-01-01"),
        _cand("strong", 0.60, "2019-01-01"),
    ])
    assert _ids(out) == ["strong"]


def test_the_table_boost_can_lift_a_candidate_a_band(settings):
    out = reranker.rerank(
        "q",
        [_cand("prose", 0.80), _cand("tabular", 0.70, has_table=True)],
        table_boost=0.15,
    )
    assert _ids(out) == ["tabular", "prose"]


def test_semantic_score_stays_the_raw_provider_score(settings):
    """The context builder's floors read `semantic_score`, so the table boost
    must not leak into it — only into `score`, which the bands are cut from."""
    out = reranker.rerank(
        "q", [_cand("tabular", 0.70, has_table=True)], table_boost=0.15
    )
    assert out[0].semantic_score == pytest.approx(0.70)
    assert out[0].score == pytest.approx(0.85)


def test_a_volatile_topic_widens_the_band(settings):
    """0.05 apart is two bands at the base tolerance but one at the volatile
    tolerance, so the newer document leads only on the volatile query."""
    docs = [_cand("2019", 0.80, "2019-01-01"), _cand("2025", 0.75, "2025-01-01")]
    assert _ids(reranker.rerank("how does composting work", docs)) == ["2019", "2025"]
    assert _ids(reranker.rerank("current pricing policy", docs)) == ["2025", "2019"]


def test_a_widened_band_still_cannot_outrank_real_relevance(settings):
    """Doubling the tolerance moves the boundary; it does not remove it."""
    out = reranker.rerank("latest pricing policy", [
        _cand("relevant", 0.80, "2019-01-01"),
        _cand("newer", 0.60, "2025-01-01"),
    ])
    assert _ids(out) == ["relevant", "newer"]


def test_the_volatile_multiplier_can_be_switched_off(settings):
    settings.rerank_volatile_tolerance_multiplier = 1.0
    out = reranker.rerank("current pricing policy", [
        _cand("2019", 0.80, "2019-01-01"),
        _cand("2025", 0.75, "2025-01-01"),
    ])
    assert _ids(out) == ["2019", "2025"]


def test_top_n_caps_the_result(settings):
    out = reranker.rerank(
        "q", [_cand("a", 0.9), _cand("b", 0.5), _cand("c", 0.1)], top_n=2
    )
    assert _ids(out) == ["a", "b"]


def test_no_candidates_is_not_an_error(settings):
    assert reranker.rerank("q", []) == []
