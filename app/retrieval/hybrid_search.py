from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Sequence

from app.config import get_settings
from app.core.clients import get_embeddings, get_qdrant_client

logger = logging.getLogger(__name__)

# Section types that extract cleanly but pollute retrieval (tables of contents,
# bibliographies, glossaries) — excluded from search via the query filter.
_NON_SEARCHABLE_SECTIONS = ("toc", "references", "glossary")

# Collections confirmed to exist this process. A missing collection is a
# bootstrap/error state, not a per-query concern, so we verify it once and then
# skip the extra round-trip — steady state is a single query_points per search.
_verified_collections: set[str] = set()


def _collection_ready(client: Any, name: str) -> bool:
    if name in _verified_collections:
        return True
    if client.collection_exists(name):
        _verified_collections.add(name)
        return True
    return False


@dataclass
class Candidate:

    id: str
    score: float
    payload: dict[str, Any] = field(default_factory=dict)
    vector: list[float] = field(default_factory=list)
    # Raw semantic relevance score (pre-blend / pre-normalization) carried through
    # rerank() so the context builder can apply the website relevance floor.
    # Defaults to `score` until rerank() populates it.
    semantic_score: float = 0.0

    @property
    def parent_id(self) -> str | None:
        return self.payload.get("parent_chunk_id")

    @property
    def text(self) -> str:
        return self.payload.get("chunk_text", "")


def build_filter(
    *,
    extra: Sequence[Any] | None = None,
    extra_must_not: Sequence[Any] | None = None,
    exclude_non_searchable: bool = True,
) -> Any:
    """The mandatory shape filter, plus caller conditions.

    The corpus is public: every caller may see all of it, so there is no tenant
    or ACL leg here. What remains mandatory is what keeps retrieval pointed at
    the *searchable* view of the corpus — current child chunks, since parents
    hold no vector of their own and superseded versions are not the answer.

    ``exclude_non_searchable`` drops toc/references/glossary chunks and is on
    for every search. Fetches that must return *something* for a document —
    rather than the best thing to search — turn it off as a last resort; see
    :func:`app.retrieval.scoped_retrieval.lead_parents`.
    """
    from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

    must: list[Any] = [
        FieldCondition(key="is_parent", match=MatchValue(value=False)),
        FieldCondition(key="is_current", match=MatchValue(value=True)),
    ]
    if extra:
        must.extend(extra)
    must_not: list[Any] = []
    if exclude_non_searchable:
        must_not.append(
            FieldCondition(
                key="section_type", match=MatchAny(any=list(_NON_SEARCHABLE_SECTIONS))
            )
        )
    if extra_must_not:
        must_not.extend(extra_must_not)
    return Filter(must=must, must_not=must_not or None)


def search(
    query: str,
    *,
    limit: int | None = None,
    extra_filter: Sequence[Any] | None = None,
    extra_must_not: Sequence[Any] | None = None,
    query_vector: Sequence[float] | None = None,
    with_vectors: bool = True,
) -> list[Candidate]:
    settings = get_settings()
    limit = limit or settings.retrieval_candidate_k

    client = get_qdrant_client()
    if not _collection_ready(client, settings.qdrant_collection):
        logger.warning("Collection %r does not exist; no results.", settings.qdrant_collection)
        return []

    vector = list(query_vector) if query_vector is not None else get_embeddings().embed_query(query)
    query_filter = build_filter(extra=extra_filter, extra_must_not=extra_must_not)

    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
        with_vectors=with_vectors,
    )
    return [_to_candidate(p) for p in response.points]


def _to_candidate(point: Any) -> Candidate:
    raw = getattr(point, "vector", None)
    if isinstance(raw, dict):
        raw = raw.get("dense") or next(iter(raw.values()), None)
    vector = [float(x) for x in raw] if isinstance(raw, (list, tuple)) else []
    return Candidate(
        id=str(point.id),
        score=float(point.score or 0.0),
        payload=point.payload or {},
        vector=vector,
    )
