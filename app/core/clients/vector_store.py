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


# Every payload field the running application filters on, and how Qdrant has to
# index it for that filter to be served. This is the single list: a fresh
# deployment gets all of it from `ensure_collection`, and the two index scripts
# apply exactly this rather than keeping their own copies — which is how nine of
# these came to exist only on machines where someone remembered to run them.
#
# Derived from the filters in the code, not from what happens to be in the
# collection:
#   is_parent          every search excludes parent points
#   is_current         every search filters on it (app/retrieval/hybrid_search)
#   source_type        website / pdf_attachment splits, website preference
#   language           language filter
#   section_type       section-type filters
#   categories         theme filtering (app/retrieval/understanding/filters)
#   tags               tag filtering
#   authors            author-scoped retrieval
#   document_id        delete_document, title refresh, scoped retrieval
#   chunk_index        neighbour expansion (app/retrieval/scoped_retrieval)
#   parent_chunk_id    child -> parent resolution
#   published_at       date range filters and recency
#   chunk_text         the keyword leg's MatchText pulls
#
# Deliberately absent: `term_ids` / `theme_ids` (taxonomy, retired) and
# `tenant_id` / `acl` (no document-level access control — the corpus is public).
# Their payload fields are gone; indexing them would be reviving a removed model.
PAYLOAD_INDEXES: dict[str, str] = {
    "is_parent": "bool",
    "is_current": "bool",
    "source_type": "keyword",
    "language": "keyword",
    "section_type": "keyword",
    "categories": "keyword",
    "tags": "keyword",
    "authors": "keyword",
    "document_id": "keyword",
    "parent_chunk_id": "keyword",
    "chunk_index": "integer",
    "published_at": "datetime",
    # The heaviest index here, and the one the lexical path cannot work without:
    # `keyword_leg_enabled` degrades to dense-only while it is missing, silently.
    "chunk_text": "text",
}


class VectorDimensionMismatch(RuntimeError):
    """The collection's vectors are not the size this deployment embeds to."""


def _schema_for(kind: str):
    """The Qdrant schema object for one index kind (imported lazily, as ever)."""
    from qdrant_client.models import PayloadSchemaType, TextIndexParams, TokenizerType

    if kind == "text":
        return TextIndexParams(type="text", tokenizer=TokenizerType.WORD, lowercase=True)
    return {
        "bool": PayloadSchemaType.BOOL,
        "keyword": PayloadSchemaType.KEYWORD,
        "integer": PayloadSchemaType.INTEGER,
        "datetime": PayloadSchemaType.DATETIME,
    }[kind]


def configured_dimension() -> int | None:
    """The vector size this deployment embeds to, without asking the model.

    ``None`` when the deployment does not pin one (ada-002 has no dimensions
    parameter), in which case there is nothing to validate against and the
    probe below decides.
    """
    return get_settings().azure_openai_embedding_dimensions


def ensure_payload_indexes(
    client: "QdrantClient", collection: str, *, dry_run: bool = False
) -> list[str]:
    """Create every index in :data:`PAYLOAD_INDEXES` that is missing.

    Best-effort per field: one index that cannot be built must not stop the
    others, because each one it does build is one filter that works. Returns the
    fields it created (or, under ``dry_run``, would create).

    Building a text index over a large collection routinely outlives the client's
    request timeout while Qdrant carries on server-side, so a failure is
    confirmed by reading the schema back rather than believed from the exception.
    """
    try:
        existing = set(client.get_collection(collection).payload_schema or {})
    except Exception:
        logger.warning(
            "Could not read %r's payload schema; leaving its indexes alone.",
            collection, exc_info=True,
        )
        return []

    created: list[str] = []
    for field, kind in PAYLOAD_INDEXES.items():
        if field in existing:
            continue
        if dry_run:
            created.append(field)
            continue
        try:
            client.create_payload_index(
                collection_name=collection,
                field_name=field,
                field_schema=_schema_for(kind),
                wait=True,
            )
            created.append(field)
        except Exception:
            if field in set(client.get_collection(collection).payload_schema or {}):
                logger.info(
                    "Index on %r did not return in time; the server built it anyway.",
                    field,
                )
                created.append(field)
                continue
            logger.warning(
                "Could not create the %s index on %r; filters on it will be "
                "unindexed (slower, and MatchText will not work at all).",
                kind, field, exc_info=True,
            )
    if created and not dry_run:
        logger.info("Created %d payload index(es) on %r: %s", len(created), collection, ", ".join(created))
    return created


def _validate_dimension(client: "QdrantClient", collection: str) -> None:
    """Refuse to use a collection whose vectors are the wrong size.

    Repointing a deployment at a different embedding model (or changing the
    Matryoshka dimension) leaves a collection whose vectors cannot be compared
    with the ones this process produces. Qdrant rejects the writes, but only
    per request and with a message about vector sizes rather than about
    configuration — and the reads it does not reject return nothing useful. One
    clear failure at the boundary beats a deployment that half-works.
    """
    wanted = configured_dimension()
    if not wanted:
        return
    try:
        vectors = client.get_collection(collection).config.params.vectors
        actual = getattr(vectors, "size", None)
    except Exception:
        logger.debug("Could not read %r's vector size.", collection, exc_info=True)
        return
    if actual is None or actual == wanted:
        return
    raise VectorDimensionMismatch(
        f"Collection {collection!r} stores {actual}-dimensional vectors but this "
        f"deployment embeds to {wanted} (azure_openai_embedding_dimensions). "
        f"Point AZURE_OPENAI_EMBEDDING_DIMENSIONS at {actual}, or use a different "
        f"collection — writing into this one would mix two vector spaces."
    )


def ensure_collection() -> None:
    """Make the collection usable: it exists, it is the right shape, it is indexed.

    A fresh deployment used to come up with one of the thirteen indexes below and
    no way to know: filtering silently fell back to full scans and the keyword leg
    silently did nothing, because the other twelve lived in scripts someone had to
    remember to run.
    """
    from qdrant_client.models import Distance, VectorParams

    settings = get_settings()
    collection = settings.qdrant_collection
    if collection in _ensured_collections:
        return

    client = get_qdrant_client()
    if not client.collection_exists(collection):
        # The configured size when there is one, so creation follows
        # configuration rather than whatever the model answered first; the probe
        # remains for deployments that pin no dimension.
        dimension = configured_dimension() or len(
            get_embeddings().embed_query("dimension probe")
        )
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )
        logger.info("Created collection %r with %d-dimensional vectors.", collection, dimension)
    else:
        _validate_dimension(client, collection)

    ensure_payload_indexes(client, collection)
    # Recorded only after the collection is confirmed/created so a transient
    # failure above retries on the next call rather than being cached as done.
    _ensured_collections.add(collection)


def delete_document(document_id: str, *, keep_ids: Sequence[str] | None = None) -> None:
    """Delete a document's points; ``keep_ids`` spares the listed point ids.

    Reindexing upserts the new version's points first and then calls this with
    their ids, so the document never disappears from search mid-swap.

    ``keep_ids=None`` means "delete the document outright" — the delete path and
    the orphan collector. An **empty list is refused**, because it can only ever
    arrive from a swap that indexed nothing, and "replace this document with
    nothing" is never what a swap means. It read as "spare no point" and wiped
    the document while the caller believed it had just re-indexed it.

    The refusal and the ``is not None`` test below are deliberately redundant:
    one makes the mistake loud at the boundary, the other keeps the filter
    correct even if some future caller is allowed to pass an empty list.
    """
    from qdrant_client.models import (
        FieldCondition,
        Filter,
        FilterSelector,
        HasIdCondition,
        MatchValue,
    )

    if not document_id:
        raise ValueError("delete_document needs a document_id.")
    if keep_ids is not None and not keep_ids:
        raise ValueError(
            f"delete_document(keep_ids=[]) would delete every point for "
            f"{document_id!r}. Pass keep_ids=None to delete the document "
            f"deliberately; a replacement that produced no points must not "
            f"delete the version it failed to replace."
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
                must_not=(
                    [HasIdCondition(has_id=list(keep_ids))]
                    if keep_ids is not None
                    else None
                ),
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
