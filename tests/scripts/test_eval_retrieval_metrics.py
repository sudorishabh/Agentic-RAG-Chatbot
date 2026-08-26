"""Unit tests for the retrieval benchmark's metrics (scripts.eval_retrieval).

Pure ranking arithmetic — no Qdrant, no LLM, no judgments file. These exist
because the metrics are what the BM25 decision will be argued from, and a
silently wrong nDCG is indistinguishable from a real result.
"""

from __future__ import annotations

import math

from scripts.eval_retrieval import ndcg_at_k, recall_at_k, reciprocal_rank


# --------------------------------------------------------------------------- #
# recall_at_k
# --------------------------------------------------------------------------- #

def test_recall_counts_only_the_top_k():
    ranked = ["a", "b", "c", "d"]
    assert recall_at_k(ranked, {"a", "d"}, 4) == 1.0
    assert recall_at_k(ranked, {"a", "d"}, 2) == 0.5


def test_recall_is_none_when_nothing_relevant_is_known():
    """A query with no judged relevant chunk must not score zero: that would
    punish every configuration for a hole in the gold set, and the hole is the
    thing to report."""
    assert recall_at_k(["a"], set(), 10) is None


def test_recall_ignores_relevant_chunks_nobody_retrieved():
    assert recall_at_k(["a"], {"a", "z"}, 10) == 0.5


# --------------------------------------------------------------------------- #
# reciprocal_rank
# --------------------------------------------------------------------------- #

def test_reciprocal_rank_uses_the_first_relevant_position():
    assert reciprocal_rank(["x", "a"], {"a"}) == 0.5
    assert reciprocal_rank(["a", "x"], {"a"}) == 1.0


def test_reciprocal_rank_is_zero_when_nothing_relevant_is_retrieved():
    """Distinct from None: the gold set has relevant chunks, this ranking simply
    missed them all."""
    assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


def test_reciprocal_rank_is_none_without_judgments():
    assert reciprocal_rank(["x"], set()) is None


# --------------------------------------------------------------------------- #
# ndcg_at_k
# --------------------------------------------------------------------------- #

def test_ndcg_is_one_for_the_ideal_ordering():
    grades = {"a": 2, "b": 1, "c": 0}
    assert ndcg_at_k(["a", "b", "c"], grades, 3) == 1.0


def test_ndcg_penalises_burying_the_best_result():
    grades = {"a": 2, "b": 1}
    assert ndcg_at_k(["b", "a"], grades, 2) < 1.0


def test_ndcg_uses_the_graded_scale_not_just_relevance():
    """A 2 above a 1 must beat a 1 above a 2 — the distinction binary metrics
    cannot express, and the reason grades are kept on a 0/1/2 scale."""
    grades = {"a": 2, "b": 1}
    assert ndcg_at_k(["a", "b"], grades, 2) > ndcg_at_k(["b", "a"], grades, 2)


def test_ndcg_discounts_by_log_position():
    grades = {"a": 2, "b": 2}
    # Ideal DCG puts both at ranks 1 and 2; retrieving only the second one at
    # rank 1 yields 2/log2(2) over (2/log2(2) + 2/log2(3)).
    expected = (2 / math.log2(2)) / (2 / math.log2(2) + 2 / math.log2(3))
    assert ndcg_at_k(["b"], grades, 2) == expected


def test_ndcg_is_none_when_every_grade_is_zero():
    assert ndcg_at_k(["a"], {"a": 0}, 10) is None


def test_ndcg_ignores_unjudged_chunks_rather_than_guessing():
    """An unjudged chunk contributes gain 0. It is not evidence of irrelevance,
    which is why pooling both configurations matters — anything only one leg
    found would otherwise be scored as a miss by construction."""
    assert ndcg_at_k(["unjudged", "a"], {"a": 2}, 2) < 1.0
