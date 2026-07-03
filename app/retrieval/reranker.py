from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Sequence

from pydantic import BaseModel, Field

from app.config import get_settings
from app.retrieval.hybrid_search import Candidate

logger = logging.getLogger(__name__)

# "website" = Drupal content (canonical value; "article" kept for points indexed
# before the rename — see scripts/migrate_source_type_website.py).
_AUTHORITY = {
    "pdf": 1.0,
    "pdf_attachment": 1.0,
    "report": 0.95,
    "policy": 0.95,
    "website": 0.65,
    "article": 0.65,
}
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


def _authority_score(payload: dict) -> float:
    explicit = payload.get("source_authority")
    if isinstance(explicit, (int, float)):
        return max(0.0, min(1.0, float(explicit)))
    return _AUTHORITY.get(payload.get("source_type", ""), 0.5)


class _Relevance(BaseModel):
    scores: list[float] = Field(description="Relevance 0..1 per candidate, in order.")


def _llm_semantic(query: str, candidates: Sequence[Candidate]) -> list[float] | None:
    from app.generation.llm_client import get_structured_llm

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
        from sentence_transformers import CrossEncoder

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


def _cohere_semantic(query: str, candidates: Sequence[Candidate]) -> list[float] | None:
    settings = get_settings()
    try:
        import os

        import cohere

        client = cohere.Client(os.environ.get("COHERE_API_KEY", ""))
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
        auth = _authority_score(cand.payload)
        blended = ws * sem_n + wr * rec + wa * auth
        if table_boost and cand.payload.get("has_table"):
            blended += table_boost
        scored.append((blended, sem_raw, cand))

    scored.sort(key=lambda t: t[0], reverse=True)
    ranked = [
        Candidate(id=c.id, score=blended, payload=c.payload, vector=c.vector)
        for blended, _sem, c in scored
    ]
    return ranked[:top_n] if top_n else ranked
