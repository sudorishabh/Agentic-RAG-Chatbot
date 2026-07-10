"""Reciprocal-rank fusion of parallel candidate rankings.

Merges the result lists of several searches (base query, paraphrases, keyword
leg) into one ranking. RRF only looks at ranks, so lists whose raw scores are
not comparable (dense cosine vs full-text match) fuse cleanly.
"""

from __future__ import annotations

from typing import Sequence

from app.retrieval.hybrid_search import Candidate


def rrf(rankings: Sequence[Sequence[Candidate]], k: int = 60) -> list[Candidate]:
    """Fuse rankings by candidate id: score = Σ 1/(k + rank). The candidate
    object (payload/vector) is kept from its first sighting; the fused score
    replaces ``.score``. Deterministic: ties break on id."""
    fused: dict[str, Candidate] = {}
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, cand in enumerate(ranking, start=1):
            scores[cand.id] = scores.get(cand.id, 0.0) + 1.0 / (k + rank)
            fused.setdefault(cand.id, cand)
    ordered = sorted(fused.values(), key=lambda c: (-scores[c.id], c.id))
    for cand in ordered:
        cand.score = scores[cand.id]
    return ordered
