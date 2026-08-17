"""Semantic response cache backed by a dedicated Qdrant collection.

A near-duplicate question is answered from a prior result via nearest-neighbor
search on the query embedding, gated by a cosine threshold. Entries self-
invalidate on corpus *or* preference changes via the partition key, which names
the indexed corpus's revision alongside the retrieval settings (see
``app.cache.cache_keys``) — so an answer stops being servable the moment
ingestion changes what it was grounded in, rather than at the end of its TTL.
Entries are not scoped to a caller: the corpus is public and every caller
retrieves over all of it. Qdrant has no native TTL, so each point carries an
``expires_at`` that lookups filter out and ``prune`` deletes.

Every operation degrades gracefully: any Qdrant error disables the cache for that
call rather than failing the query.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Sequence

from app.cache.cache_keys import semantic_partition
from app.config import get_settings

logger = logging.getLogger(__name__)

_store_count = 0


def _client() -> Any | None:
    from app.core.clients import get_qdrant_client

    try:
        return get_qdrant_client()
    except Exception:  # pragma: no cover - misconfigured qdrant
        logger.warning("Qdrant unavailable; semantic cache disabled.", exc_info=True)
        return None


def _index(client: Any, name: str) -> None:
    from qdrant_client.models import PayloadSchemaType

    for field, schema in (
        ("scope", PayloadSchemaType.KEYWORD),
        ("expires_at", PayloadSchemaType.FLOAT),
    ):
        try:
            client.create_payload_index(
                collection_name=name, field_name=field, field_schema=schema
            )
        except Exception:  # pragma: no cover - best-effort
            logger.debug("Could not index %r on semantic cache.", field, exc_info=True)


def _ensure_collection(client: Any, dim: int) -> bool:
    from qdrant_client.models import Distance, VectorParams

    name = get_settings().semantic_cache_collection
    try:
        if not client.collection_exists(name):
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            _index(client, name)
        return True
    except Exception:
        logger.warning("Could not ensure semantic cache collection.", exc_info=True)
        return False


def facet_fingerprint(pq: Any) -> dict[str, Any]:
    """Compact facet identity of a processed query. A cached answer built
    under different facets (another period, theme, author…) must never be
    served, however close the embeddings.

    Uses the normalized theme *name* rather than resolved term uuids: the
    name→uuid resolution is deterministic, so name equality is at least as
    strict — and it costs no extra MySQL round-trip per query. ``tags`` are
    included since they filter retrieval too.
    """
    analysis = getattr(pq, "analysis", None)

    def norm(value: Any) -> str | None:
        text = str(value or "").strip().lower()
        return text or None

    fp: dict[str, Any] = {
        "source_type": norm(getattr(pq, "source_type", None)),
        "language": norm(getattr(pq, "language", None)),
        "theme": norm(getattr(analysis, "theme", None)),
        "author": norm(getattr(analysis, "author", None)),
        "date_from": norm(getattr(analysis, "date_from", None)),
        "date_to": norm(getattr(analysis, "date_to", None)),
        "tags": sorted(t for t in (norm(v) for v in getattr(analysis, "tags", []) or []) if t)
        or None,
    }
    return {k: v for k, v in fp.items() if v is not None}


def lookup(
    query_vector: Sequence[float],
    *,
    top_k: int,
    answer_format: str = "default",
    fingerprint: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.semantic_cache_enabled or not query_vector:
        return None
    client = _client()
    if client is None:
        return None

    name = settings.semantic_cache_collection
    scope = semantic_partition(top_k, answer_format)
    if scope is None:
        # The corpus revision is unreadable, so no stored answer can be shown to
        # still match the corpus. Answer it fresh.
        return None
    try:
        if not client.collection_exists(name):
            return None
        from qdrant_client.models import FieldCondition, Filter, MatchValue, Range

        response = client.query_points(
            collection_name=name,
            query=list(query_vector),
            query_filter=Filter(
                must=[
                    FieldCondition(key="scope", match=MatchValue(value=scope)),
                    FieldCondition(key="expires_at", range=Range(gte=time.time())),
                ]
            ),
            limit=1,
            with_payload=True,
            score_threshold=settings.semantic_cache_threshold,
        )
    except Exception:  # pragma: no cover - store hiccup
        logger.warning("Semantic cache lookup failed.", exc_info=True)
        return None

    points = response.points
    if not points:
        return None
    payload = points[0].payload or {}
    # Post-filter on the single candidate: the stored facet fingerprint must
    # match the query's. Legacy entries without one count as mismatches (they
    # age out via expires_at).
    if payload.get("facets") != (fingerprint or {}):
        return None
    return payload.get("result")


def store(
    query_vector: Sequence[float],
    result: dict[str, Any],
    *,
    top_k: int,
    answer_format: str = "default",
    fingerprint: dict[str, Any] | None = None,
) -> None:
    settings = get_settings()
    if not settings.semantic_cache_enabled or not query_vector:
        return
    scope = semantic_partition(top_k, answer_format)
    if scope is None:
        # Storing under a key that does not name the corpus would make this
        # entry unservable-but-present at best, and stale-servable at worst.
        return
    client = _client()
    if client is None or not _ensure_collection(client, len(query_vector)):
        return

    from qdrant_client.models import PointStruct

    name = settings.semantic_cache_collection
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=list(query_vector),
        payload={
            "result": result,
            "scope": scope,
            "facets": fingerprint or {},
            "expires_at": time.time() + settings.semantic_cache_ttl,
        },
    )
    try:
        client.upsert(collection_name=name, points=[point])
    except Exception:  # pragma: no cover
        logger.warning("Semantic cache store failed.", exc_info=True)
        return
    _maybe_prune(client, name)


def _maybe_prune(client: Any, name: str) -> None:
    global _store_count
    every = get_settings().semantic_cache_prune_every
    if every <= 0:
        return
    _store_count += 1
    if _store_count % every == 0:
        prune(client, name)


def prune(client: Any | None = None, name: str | None = None) -> None:
    """Delete points whose ``expires_at`` has passed. Safe to call from a
    scheduler; also invoked opportunistically from ``store``."""
    client = client or _client()
    if client is None:
        return
    name = name or get_settings().semantic_cache_collection
    try:
        if not client.collection_exists(name):
            return
        from qdrant_client.models import (
            FieldCondition,
            Filter,
            FilterSelector,
            Range,
        )

        client.delete(
            collection_name=name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="expires_at", range=Range(lt=time.time()))]
                )
            ),
        )
    except Exception:  # pragma: no cover
        logger.warning("Semantic cache prune failed.", exc_info=True)
