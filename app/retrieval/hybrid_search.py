"""Hybrid search over Qdrant (§5.5 / step 3 of §6).

First-stage retrieval: embed the query and pull a *wide* candidate pool of
**child** chunks, filtered server-side (filterable vector search keeps recall —
§5.4) by tenant, ACL, ``is_current`` and any query-derived facets.

The collection is dense-only today, so this runs a single filtered dense search
through Qdrant's Query API (``query_points``). The code is shaped for the full
dense+sparse RRF setup from §5.5 — when sparse vectors are indexed, flip
``hybrid_use_sparse`` and add the sparse prefetch leg here; the rest of the
pipeline (rerank → context → cite) is unchanged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Sequence

from app.config import get_settings
from app.deps import get_embeddings, get_qdrant_client

logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    """One first-stage hit: a child chunk with its dense similarity score."""

    id: str
    score: float
    payload: dict[str, Any] = field(default_factory=dict)
    # Dense vector, when retrieved with ``with_vectors`` — used for query-time
    # near-duplicate dedup (§9.2). May be empty when vectors weren't requested.
    vector: list[float] = field(default_factory=list)

    @property
    def parent_id(self) -> str | None:
        return self.payload.get("parent_chunk_id")

    @property
    def text(self) -> str:
        return self.payload.get("chunk_text", "")


def build_filter(
    *,
    tenant_id: str = "default",
    user_groups: Sequence[str] | None = None,
    extra: Sequence[Any] | None = None,
) -> Any:
    """Assemble the mandatory query filter (§5.4): search children only, current
    versions only, scoped to the tenant and the user's ACL groups (§10.7). Any
    query-derived ``extra`` conditions (categories, language, date range) are
    appended."""
    from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

    must: list[Any] = [
        FieldCondition(key="is_parent", match=MatchValue(value=False)),
        FieldCondition(key="is_current", match=MatchValue(value=True)),
        FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
    ]
    groups = list(user_groups or ["public"])
    if groups:
        must.append(FieldCondition(key="acl", match=MatchAny(any=groups)))
    if extra:
        must.extend(extra)
    return Filter(must=must)


def search(
    query: str,
    *,
    limit: int | None = None,
    tenant_id: str = "default",
    user_groups: Sequence[str] | None = None,
    extra_filter: Sequence[Any] | None = None,
    query_vector: Sequence[float] | None = None,
    with_vectors: bool = True,
) -> list[Candidate]:
    """Return up to ``limit`` filtered child candidates, ranked by dense score.

    ``query_vector`` may be supplied to reuse a cached embedding; otherwise the
    query is embedded here. ``with_vectors`` returns each hit's dense vector so
    downstream context selection can dedup near-duplicates (§9.2).
    """
    settings = get_settings()
    limit = limit or settings.retrieval_candidate_k

    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        logger.warning("Collection %r does not exist; no results.", settings.qdrant_collection)
        return []

    vector = list(query_vector) if query_vector is not None else get_embeddings().embed_query(query)
    query_filter = build_filter(
        tenant_id=tenant_id, user_groups=user_groups, extra=extra_filter
    )

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
    # Default (unnamed) vector comes back as a list; named-vector configs return a
    # dict — take the dense leg if so.
    if isinstance(raw, dict):
        raw = raw.get("dense") or next(iter(raw.values()), None)
    vector = [float(x) for x in raw] if isinstance(raw, (list, tuple)) else []
    return Candidate(
        id=str(point.id),
        score=float(point.score or 0.0),
        payload=point.payload or {},
        vector=vector,
    )
