from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Sequence

from app.config import get_settings
from app.core.clients.embeddings import get_embeddings

if TYPE_CHECKING:
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


@lru_cache
def get_qdrant_client() -> "QdrantClient":
    from qdrant_client import QdrantClient

    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


# Collections whose existence + payload index we've already verified this
# process. Ingestion calls ensure_collection() once per document; without this
# guard each call re-hits Qdrant with collection_exists + create_payload_index.
_ensured_collections: set[str] = set()


def ensure_collection() -> None:
    from qdrant_client.models import Distance, VectorParams

    settings = get_settings()
    if settings.qdrant_collection in _ensured_collections:
        return

    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        dimension = len(get_embeddings().embed_query("dimension probe"))
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )
    _ensure_datetime_index(client, settings.qdrant_collection, "published_at")
    # Recorded only after the collection is confirmed/created so a transient
    # failure above retries on the next call rather than being cached as done.
    _ensured_collections.add(settings.qdrant_collection)


def _ensure_datetime_index(client: "QdrantClient", collection: str, field: str) -> None:
    """Index a payload field as datetime so range filters work. Idempotent and
    best-effort: date filtering degrades gracefully if the index can't be made."""
    try:
        from qdrant_client.models import PayloadSchemaType

        client.create_payload_index(
            collection_name=collection,
            field_name=field,
            field_schema=PayloadSchemaType.DATETIME,
        )
    except Exception:
        logger.debug("Could not ensure datetime index on %r.", field, exc_info=True)


def _ensure_keyword_index(client: "QdrantClient", collection: str, field: str) -> None:
    """Index a payload field as keyword for exact-match filters. Idempotent and
    best-effort, like the datetime variant."""
    try:
        from qdrant_client.models import PayloadSchemaType

        client.create_payload_index(
            collection_name=collection,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception:
        logger.debug("Could not ensure keyword index on %r.", field, exc_info=True)


def delete_document(document_id: str, *, keep_ids: Sequence[str] | None = None) -> None:
    """Delete a document's points; ``keep_ids`` spares the listed point ids.

    Reindexing upserts the new version's points first and then calls this with
    their ids, so the document never disappears from search mid-swap.
    """
    from qdrant_client.models import (
        FieldCondition,
        Filter,
        FilterSelector,
        HasIdCondition,
        MatchValue,
    )

    settings = get_settings()
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        return
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=document_id)
                    )
                ],
                must_not=[HasIdCondition(has_id=list(keep_ids))] if keep_ids else None,
            )
        ),
    )


def refresh_document_title(document_id: str, title: str | None) -> None:
    """Rewrite ``title`` on a document's existing points, without re-embedding.

    The content hash covers body text only, so a title-only edit resolves to
    ``unchanged_content`` and never re-indexes — which would leave the payload
    title (what citations display) stale against the catalog. Rewriting the one
    field is a single call and costs no embedding.

    Best-effort: a failure here leaves a stale display title, which the
    document's next real re-index heals anyway.
    """
    if not title:
        return
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    settings = get_settings()
    try:
        client = get_qdrant_client()
        if not client.collection_exists(settings.qdrant_collection):
            return
        client.set_payload(
            collection_name=settings.qdrant_collection,
            payload={"title": title},
            points=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=document_id)
                    )
                ]
            ),
        )
    except Exception:
        logger.warning(
            "Could not refresh the payload title for %s; it heals on the next "
            "reindex.", document_id, exc_info=True,
        )


@lru_cache
def get_vector_store() -> "QdrantVectorStore":
    from langchain_qdrant import QdrantVectorStore

    settings = get_settings()
    ensure_collection()
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_collection,
        embedding=get_embeddings(),
    )
