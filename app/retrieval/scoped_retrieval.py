"""Id-scoped Qdrant reads: search within a catalog-selected document set.

Inverts the usual vector-search-plus-facet-filter flow for queries where
MySQL is authoritative for set membership (theme/author/period/title scopes):
the catalog picks the ids, Qdrant ranks or fetches content strictly inside
them. Read-only against the documents collection; every path fails open.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from app.config import get_settings
from app.deps import get_qdrant_client
from app.retrieval.hybrid_search import Candidate, build_filter, search

logger = logging.getLogger(__name__)

# Safety cap on MatchAny id sets (callers pre-cap via the catalog limit, but
# an unbounded id filter must never reach Qdrant).
_MAX_IDS = 150


def search_within_documents(
    query_vector: Sequence[float],
    document_ids: Sequence[str],
    *,
    limit: int,
    tenant_id: str = "default",
    user_groups: Sequence[str] | None = None,
) -> list[Candidate]:
    """Dense search constrained to the given document ids."""
    from qdrant_client.models import FieldCondition, MatchAny

    ids = [d for d in document_ids if d][:_MAX_IDS]
    if not ids:
        return []
    try:
        return search(
            "",  # query text unused when query_vector is supplied
            limit=limit,
            tenant_id=tenant_id,
            user_groups=user_groups,
            extra_filter=[FieldCondition(key="document_id", match=MatchAny(any=ids))],
            query_vector=query_vector,
        )
    except Exception:
        logger.warning("Id-scoped search failed.", exc_info=True)
        return []


def lead_parents(
    document_ids: Sequence[str],
    *,
    tenant_id: str = "default",
    user_groups: Sequence[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """document_id -> the best single payload to represent the document.

    A document's lead parent chunk (~1600 tokens max) is its best one-block
    representation for summarization. Children carry ``chunk_index`` and
    parents don't, so fetch each document's first child (chunk_index == 0)
    and hop to its ``parent_chunk_id`` in one batched retrieve. Documents
    whose first child has no parent fall back to the child payload itself
    (single-child documents skip parent emission).
    """
    from qdrant_client.models import FieldCondition, MatchAny, MatchValue

    ids = [d for d in document_ids if d][:_MAX_IDS]
    if not ids:
        return {}
    settings = get_settings()
    client = get_qdrant_client()
    lead_filter = build_filter(
        tenant_id=tenant_id,
        user_groups=user_groups,
        extra=[
            FieldCondition(key="document_id", match=MatchAny(any=ids)),
            FieldCondition(key="chunk_index", match=MatchValue(value=0)),
        ],
    )
    try:
        points, _ = client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=lead_filter,
            limit=len(ids),
            with_payload=True,
            with_vectors=False,
        )
    except Exception:
        logger.warning("Lead-child scroll failed.", exc_info=True)
        return {}

    children = [p.payload or {} for p in points]
    parent_ids = [c["parent_chunk_id"] for c in children if c.get("parent_chunk_id")]
    parents: dict[str, dict[str, Any]] = {}
    if parent_ids:
        try:
            records = client.retrieve(
                collection_name=settings.qdrant_collection,
                ids=parent_ids,
                with_payload=True,
                with_vectors=False,
            )
            parents = {str(r.id): (r.payload or {}) for r in records}
        except Exception:
            logger.warning("Parent retrieve failed; using child payloads.", exc_info=True)

    out: dict[str, dict[str, Any]] = {}
    for child in children:
        doc_id = child.get("document_id")
        if not doc_id:
            continue
        out[doc_id] = parents.get(str(child.get("parent_chunk_id") or "")) or child
    return out
