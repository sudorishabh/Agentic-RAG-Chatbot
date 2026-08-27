"""Reciprocal-rank fusion of parallel candidate rankings.

Merges the result lists of several searches (base query, paraphrases, keyword
leg) into one ranking. RRF only looks at ranks, so lists whose raw scores are
not comparable (dense cosine vs full-text match) fuse cleanly.
"""

from __future__ import annotations

from typing import Sequence

from app.retrieval.search.hybrid_search import Candidate


def rrf(rankings: Sequence[Sequence[Candidate]], k: int = 60) -> list[Candidate]:
    """Fuse rankings by candidate id: score = Σ 1/(k + rank). The candidate
    object (payload/vector) is kept from its first sighting; the fused score
    lands on ``.fusion_score`` and drives ``.score``. Deterministic: ties break
    on id.

    ``semantic_score`` is deliberately left untouched. A reciprocal-rank value
    is a *ranking* quantity roughly two orders of magnitude below a cosine
    similarity, so writing it over the semantic score would put every fused
    candidate under thresholds calibrated in cosine — which is exactly how
    enabling a recall leg used to empty the website group.
    """
    fused: dict[str, Candidate] = {}
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, cand in enumerate(ranking, start=1):
            scores[cand.id] = scores.get(cand.id, 0.0) + 1.0 / (k + rank)
            fused.setdefault(cand.id, cand)
    ordered = sorted(fused.values(), key=lambda c: (-scores[c.id], c.id))
    for cand in ordered:
        cand.fusion_score = scores[cand.id]
        cand.score = cand.fusion_score
    return ordered
