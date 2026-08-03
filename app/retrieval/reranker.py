"""Candidate reranking — relevance decides the ranking, recency decides ties.

Ordering used to be a weighted blend of a normalized semantic score, recency and
authority. A blend gets this backwards in the case that matters: because the
semantic scores are min-max normalized first, it separates candidates most
aggressively exactly when their scores are closest together — when the relevance
difference means least — while a fixed recency weight small enough not to
overrule a genuinely better passage is also too small to break the ties it is
there for.

So candidates are *banded* instead, and ranked on the bands in priority order:

1. **relevance** — scores within ``rerank_relevance_tolerance`` are "similarly
   relevant" and go on to compete on the keys below; a candidate a band lower
   never climbs past one above it, however new or full it is;
2. **completeness** — within a relevance band, a passage holding
   ``rerank_substance_ratio`` times the text of another says substantially more
   and leads it;
3. **recency** — comparable passages settle on publication date, newest first;
4. **authority** — a `source_authority` payload override, if one is ever written.

Two editions of the same annual report land in one relevance band, and unless one
is a fragment the newer leads. An older passage that actually answers the
question still outranks a newer one that merely mentions it.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from functools import lru_cache
from typing import NamedTuple, Sequence

from pydantic import BaseModel, Field

from app.config import get_settings
from app.retrieval.hybrid_search import Candidate
from app.retrieval.volatility import is_volatile

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


def _substance_scores(candidates: Sequence[Candidate]) -> list[float]:
    """Log-scaled passage length — the stand-in for "completeness".

    Accuracy cannot be measured at ranking time and neither, strictly, can
    completeness; what is visible is how much a passage actually says, and a
    chunk cut short at a document boundary does carry less of an answer than a
    full one.

    Log scale so the band tolerance reads as a *ratio*: one passage says
    substantially more than another when it holds `rerank_substance_ratio` times
    the text. That claim survives the fact that chunks are already roughly
    uniform in size, where a linear scale would not — min-max normalization would
    inflate the gap between 1,400 and 1,500 characters into a decisive one, which
    is the mistake the relevance blend used to make.

    Measured on the child chunk that matched; the parent expansion happens later,
    in the context builder."""
    return [math.log1p(len(c.text)) for c in candidates]


def _bands(values: Sequence[float], *, tolerance: float) -> list[int]:
    """Band index per value, 0 being the highest band.

    A band starts at its leader and holds every value within `tolerance` of it;
    the first value that falls further than that opens the next band. Grown
    greedily down the sorted order rather than cut into fixed-width buckets, so
    two near-identical values can never land either side of an arbitrary
    boundary — and measured against the *leader* rather than the previous value,
    so a long chain of small steps cannot drift an arbitrarily weak value into
    the top band."""
    if not values:
        return []
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    bands = [0] * len(values)
    band = 0
    leader = values[order[0]]
    for i in order:
        if leader - values[i] > tolerance:
            band += 1
            leader = values[i]
        bands[i] = band
    return bands


class _Scored(NamedTuple):
    """A candidate's ranking signals, before they are cut into bands."""

    candidate: Candidate
    relevance: float   # semantic score plus any table boost; the band is cut from this
    semantic: float    # raw provider score, carried through for the context floors
    substance: float
    recency: float
    authority: float


class _Ranked(NamedTuple):
    """A scored candidate placed in the ranking."""

    relevance_band: int   # 0 is the most relevant band
    substance_band: int   # 0 is the fullest band, cut within the relevance band
    scored: _Scored


def _relevance_tolerance(query: str, settings) -> float:
    """Relevance band width for this query — widened when the topic goes stale.

    Nothing can cross a band however wide it gets, so this only changes how often
    the lower-priority keys are reachable, never whether relevance wins."""
    tolerance = settings.rerank_relevance_tolerance
    if not is_volatile(query):
        return tolerance
    widened = tolerance * settings.rerank_volatile_tolerance_multiplier
    logger.debug("Volatile topic; relevance band widened to %.3f.", widened)
    return widened


def _substance_tolerance(settings) -> float:
    """Completeness band width, as the log of the configured length ratio — see
    `_substance_scores`. A ratio at or below 1 would make every difference in
    length substantial, so it is clamped away."""
    return math.log(max(float(settings.rerank_substance_ratio), 1.0))


def _substance_bands(
    scored: Sequence[_Scored], relevance_bands: Sequence[int], *, tolerance: float
) -> list[int]:
    """Completeness band per candidate, cut *within* each relevance band.

    Banding across the whole set would let a long passage from a much less
    relevant document place the boundary that splits two similarly relevant ones.
    Completeness is only ever a question between candidates that already tied on
    relevance."""
    bands = [0] * len(scored)
    for relevance_band in set(relevance_bands):
        members = [i for i, b in enumerate(relevance_bands) if b == relevance_band]
        within = _bands([scored[i].substance for i in members], tolerance=tolerance)
        for i, band in zip(members, within):
            bands[i] = band
    return bands


def _sort_key(r: _Ranked) -> tuple[float, ...]:
    """The ranking priority, most significant first: relevance band, then
    completeness band, then recency, then authority, then the fine-grained
    relevance within the band — a deterministic last resort, and by construction
    a sub-tolerance difference that the band already declared immaterial."""
    return (
        r.relevance_band,
        r.substance_band,
        -r.scored.recency,
        -r.scored.authority,
        -r.scored.relevance,
    )


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
    substance = _substance_scores(candidates)
    recency = _recency_scores(candidates)
    authority = _authority_scores(candidates)

    kept: list[_Scored] = []
    for cand, sem, sub, rec, auth in zip(
        candidates, semantic, substance, recency, authority
    ):
        if threshold and sem < threshold:
            continue
        # The boost lifts relevance rather than a final score, so a table-bearing
        # chunk can climb a band when the answer wants a table. Still a nudge and
        # not a filter — and inert when it is smaller than the band tolerance.
        boost = table_boost if table_boost and cand.payload.get("has_table") else 0.0
        kept.append(
            _Scored(
                candidate=cand, relevance=sem + boost, semantic=sem,
                substance=sub, recency=rec, authority=auth,
            )
        )

    relevance_bands = _bands(
        [s.relevance for s in kept], tolerance=_relevance_tolerance(query, settings)
    )
    substance_bands = _substance_bands(
        kept, relevance_bands, tolerance=_substance_tolerance(settings)
    )
    ranked = sorted(
        (
            _Ranked(relevance_band=rb, substance_band=sb, scored=s)
            for rb, sb, s in zip(relevance_bands, substance_bands, kept)
        ),
        key=_sort_key,
    )
    out = [
        Candidate(
            id=r.scored.candidate.id, score=r.scored.relevance,
            payload=r.scored.candidate.payload, vector=r.scored.candidate.vector,
            semantic_score=r.scored.semantic,
        )
        for r in ranked
    ]
    return out[:top_n] if top_n else out
