from __future__ import annotations

import logging
from datetime import datetime
from functools import lru_cache
from typing import Sequence

from pydantic import BaseModel, Field

from app.config import get_settings
from app.retrieval.hybrid_search import Candidate

logger = logging.getLogger(__name__)

_MAX_LLM_CANDIDATES = 40
_LLM_SNIPPET_CHARS = 600


def _normalize(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _recency_scores(candidates: Sequence[Candidate]) -> list[float]:
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
        return [0.5] * len(candidates)
    lo, hi = min(known), max(known)
    span = hi - lo
    return [0.5 if e is None else (0.5 if span < 1e-9 else (e - lo) / span) for e in epochs]


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
    candidates = list(candidates)
    if not candidates:
        return []
    settings = get_settings()
    provider = (settings.reranker_provider or "embedding").lower()

    semantic = _semantic_scores(query, candidates, provider)
    threshold = settings.rerank_score_threshold
    norm_sem = _normalize(semantic)
    recency = _recency_scores(candidates)
    wr, wa = settings.rerank_recency_weight, settings.rerank_authority_weight
    ws = max(0.0, 1.0 - wr - wa)

    scored: list[tuple[float, float, Candidate]] = []
    for cand, sem_raw, sem_n, rec in zip(candidates, semantic, norm_sem, recency):
        if threshold and sem_raw < threshold:
            continue
        # Neutral authority baseline: the source-type map and the per-document
        # source_authority override were both removed, so wa*0.5 is a constant
        # offset that does not affect ranking.
        auth = 0.5
        blended = ws * sem_n + wr * rec + wa * auth
        if table_boost and cand.payload.get("has_table"):
            blended += table_boost
        scored.append((blended, sem_raw, cand))

    scored.sort(key=lambda t: t[0], reverse=True)
    ranked = [
        Candidate(
            id=c.id, score=blended, payload=c.payload, vector=c.vector,
            semantic_score=sem,
        )
        for blended, sem, c in scored
    ]
    return ranked[:top_n] if top_n else ranked
