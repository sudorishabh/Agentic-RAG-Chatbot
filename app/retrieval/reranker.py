"""Candidate reranking — relevance decides the ranking, recency decides ties.

Ordering used to be a weighted blend of a normalized semantic score, recency and
authority. A blend gets this backwards in the case that matters: because the
semantic scores are min-max normalized first, it separates candidates most
aggressively exactly when their scores are closest together — when the relevance
difference means least — while a fixed recency weight small enough not to
overrule a genuinely better passage is also too small to break the ties it is
there for.

So candidates are grouped into *relevance bands* instead. Scores within
``rerank_relevance_tolerance`` of each other are "similarly relevant" and settle
their order on recency; a candidate a band below never climbs past one above it,
however new it is. Two editions of the same annual report land in one band and
the newer leads, while an older passage that actually answers the question still
outranks a newer one that merely mentions it.
"""

from __future__ import annotations

import logging
from datetime import datetime
from functools import lru_cache
from typing import NamedTuple, Sequence

from pydantic import BaseModel, Field

from app.config import get_settings
from app.retrieval.hybrid_search import Candidate

logger = logging.getLogger(__name__)

_MAX_LLM_CANDIDATES = 40
_LLM_SNIPPET_CHARS = 600
# Recency/authority for a candidate carrying no signal either way. Mid-scale, so
# an unknown neither leads nor trails its band on a fact we do not have.
_UNKNOWN = 0.5


def _recency_scores(candidates: Sequence[Candidate]) -> list[float]:
    """Publication date per candidate, scaled to [0,1] across the set.

    Only the *order* of these values is read (recency ranks within a band, it is
    no longer weighted into a score), so the scaling exists to place an undated
    candidate at `_UNKNOWN` — mid-set — rather than to make the number comparable
    to anything else."""
    epochs: list[float | None] = []
    for c in candidates:
        raw = c.payload.get("published_at")
        epoch: float | None = None
        if isinstance(raw, str) and raw:
            try:
                epoch = datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
            except ValueError:
                epoch = None
        epochs.append(epoch)
    known = [e for e in epochs if e is not None]
    if not known:
        return [_UNKNOWN] * len(candidates)
    lo, hi = min(known), max(known)
    span = hi - lo
    return [
        _UNKNOWN if e is None else (_UNKNOWN if span < 1e-9 else (e - lo) / span)
        for e in epochs
    ]


def _authority_scores(candidates: Sequence[Candidate]) -> list[float]:
    """Source trustworthiness in [0,1], from an optional `source_authority`
    payload value.

    Nothing writes that key today — the source-type authority map was removed and
    website preference is handled by the dual pull and segregation, not a scoring
    tilt — so every candidate scores `_UNKNOWN`, a constant that cannot reorder
    anything. It stays as the lowest-priority ranking key so a corpus that does
    start stamping authority gets the behavior without another ranking change."""
    scores: list[float] = []
    for c in candidates:
        try:
            scores.append(min(1.0, max(0.0, float(c.payload["source_authority"]))))
        except (KeyError, TypeError, ValueError):
            scores.append(_UNKNOWN)
    return scores


def _relevance_bands(relevance: Sequence[float], *, tolerance: float) -> list[int]:
    """Band index per candidate, 0 being the most relevant band.

    A band starts at its leader and holds every candidate within `tolerance` of
    it; the first candidate that falls further than that opens the next band.
    Grown greedily down the relevance-sorted order rather than cut into
    fixed-width buckets, so two near-identical scores can never land either side
    of an arbitrary boundary — and measured against the *leader* rather than the
    previous candidate, so a long chain of small steps cannot drift an
    arbitrarily weak candidate into the top band."""
    if not relevance:
        return []
    order = sorted(range(len(relevance)), key=lambda i: relevance[i], reverse=True)
    bands = [0] * len(relevance)
    band = 0
    leader = relevance[order[0]]
    for i in order:
        if leader - relevance[i] > tolerance:
            band += 1
            leader = relevance[i]
        bands[i] = band
    return bands


class _Ranked(NamedTuple):
    """A candidate with everything the ranking sorts it on."""

    band: int          # 0 is the most relevant band
    recency: float
    authority: float
    relevance: float   # semantic score plus any table boost; the band is cut from this
    semantic: float    # raw provider score, carried through for the context floors
    candidate: Candidate


def _sort_key(r: _Ranked) -> tuple[float, ...]:
    """The ranking priority, most significant first: relevance band, then
    recency, then authority, then the fine-grained relevance within the band —
    a deterministic last resort, and by construction a sub-tolerance difference
    that the band already declared immaterial."""
    return (r.band, -r.recency, -r.authority, -r.relevance)


class _Relevance(BaseModel):
    scores: list[float] = Field(description="Relevance 0..1 per candidate, in order.")


def _llm_semantic(query: str, candidates: Sequence[Candidate]) -> list[float] | None:
    from app.core.clients.llm import get_structured_llm

    listing = "\n".join(
        f"[{i}] {c.text[:_LLM_SNIPPET_CHARS]}" for i, c in enumerate(candidates)
    )
    try:
        model = get_structured_llm().with_structured_output(_Relevance)
        result: _Relevance = model.invoke(
            [
                (
                    "system",
                    "Rate how well each numbered passage answers the query, from 0 "
                    "(irrelevant) to 1 (directly answers). Return one score per "
                    "passage, in order.",
                ),
                ("human", f"Query: {query}\n\nPassages:\n{listing}"),
            ]
        )
    except Exception:
        logger.warning("LLM rerank failed; falling back to dense score.", exc_info=True)
        return None
    if len(result.scores) != len(candidates):
        logger.warning("LLM rerank returned %d scores for %d candidates; ignoring.",
                       len(result.scores), len(candidates))
        return None
    return [max(0.0, min(1.0, float(s))) for s in result.scores]


def _cross_encoder_semantic(query: str, candidates: Sequence[Candidate]) -> list[float] | None:
    model_name = get_settings().rerank_model or "BAAI/bge-reranker-v2-m3"
    try:
        encoder = _load_cross_encoder(model_name)
        scores = encoder.predict([(query, c.text) for c in candidates])
        return [float(s) for s in scores]
    except Exception:
        logger.warning("cross_encoder rerank unavailable; falling back.", exc_info=True)
        return None


_CROSS_ENCODER_CACHE: dict[str, object] = {}


def _load_cross_encoder(model_name: str):
    if model_name not in _CROSS_ENCODER_CACHE:
        from sentence_transformers import CrossEncoder

        _CROSS_ENCODER_CACHE[model_name] = CrossEncoder(model_name)
    return _CROSS_ENCODER_CACHE[model_name]


@lru_cache(maxsize=1)
def _cohere_client():
    import os

    import cohere

    return cohere.Client(os.environ.get("COHERE_API_KEY", ""))


def _cohere_semantic(query: str, candidates: Sequence[Candidate]) -> list[float] | None:
    settings = get_settings()
    try:
        # Cached client: constructing one per rerank call rebuilds an HTTP
        # connection pool on every query.
        client = _cohere_client()
        model = settings.rerank_model or "rerank-3.5"
        resp = client.rerank(
            query=query, documents=[c.text for c in candidates], model=model
        )
        scores = [0.0] * len(candidates)
        for r in resp.results:
            scores[r.index] = float(r.relevance_score)
        return scores
    except Exception:
        logger.warning("cohere rerank unavailable; falling back.", exc_info=True)
        return None


def _semantic_scores(query: str, candidates: Sequence[Candidate], provider: str) -> list[float]:
    dense = [c.score for c in candidates]
    if provider == "llm" and len(candidates) <= _MAX_LLM_CANDIDATES:
        return _llm_semantic(query, candidates) or dense
    if provider == "cross_encoder":
        return _cross_encoder_semantic(query, candidates) or dense
    if provider == "cohere":
        return _cohere_semantic(query, candidates) or dense
    return dense


def rerank(
    query: str,
    candidates: Sequence[Candidate],
    *,
    top_n: int | None = None,
    table_boost: float = 0.0,
) -> list[Candidate]:
    """Candidates in ranked order, best first, capped at `top_n`.

    Each returned candidate carries the relevance its band was cut from in
    `score` and the raw provider score in `semantic_score` (the context builder's
    floors read the latter). `score` is not monotone with the returned order:
    inside a band the ranking is by recency, so a newer candidate can lead one
    scoring marginally higher."""
    candidates = list(candidates)
    if not candidates:
        return []
    settings = get_settings()
    provider = (settings.reranker_provider or "embedding").lower()

    semantic = _semantic_scores(query, candidates, provider)
    threshold = settings.rerank_score_threshold
    recency = _recency_scores(candidates)
    authority = _authority_scores(candidates)

    kept: list[tuple[Candidate, float, float, float, float]] = []
    for cand, sem, rec, auth in zip(candidates, semantic, recency, authority):
        if threshold and sem < threshold:
            continue
        # The boost lifts relevance rather than a final score, so a table-bearing
        # chunk can climb a band when the answer wants a table. Still a nudge and
        # not a filter — and inert when it is smaller than the band tolerance.
        boost = table_boost if table_boost and cand.payload.get("has_table") else 0.0
        kept.append((cand, sem + boost, sem, rec, auth))

    bands = _relevance_bands(
        [relevance for _, relevance, _, _, _ in kept],
        tolerance=settings.rerank_relevance_tolerance,
    )
    ranked = sorted(
        (
            _Ranked(band=band, recency=rec, authority=auth, relevance=relevance,
                    semantic=sem, candidate=cand)
            for band, (cand, relevance, sem, rec, auth) in zip(bands, kept)
        ),
        key=_sort_key,
    )
    out = [
        Candidate(
            id=r.candidate.id, score=r.relevance, payload=r.candidate.payload,
            vector=r.candidate.vector, semantic_score=r.semantic,
        )
        for r in ranked
    ]
    return out[:top_n] if top_n else out
