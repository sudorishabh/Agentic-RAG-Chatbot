"""Display-name refresh after a taxonomy term rename.

Correctness never depends on this module: filters and counts join on term
UUIDs, which a rename does not touch. What goes stale are the display-name
arrays (``categories``) baked into chunk payloads and the MySQL category
facet at ingest time — this refreshes both for the affected documents, with
no re-embedding or reindex.
"""

from __future__ import annotations

import logging

from app.config import get_settings
from app.deps import get_qdrant_client
from app.ingestion import state

logger = logging.getLogger(__name__)


def refresh_renamed_term(term_uuid: str, old_name: str, new_name: str) -> int:
    """Rewrite ``old_name`` -> ``new_name`` in the category facet and chunk
    payloads of every document linked to the term; returns the number of
    documents touched."""
    document_ids = state.documents_for_term(term_uuid)
    if not document_ids:
        return 0

    from qdrant_client.models import FieldCondition, Filter, MatchValue

    settings = get_settings()
    client = get_qdrant_client()
    collection_live = client.collection_exists(settings.qdrant_collection)

    for document_id in document_ids:
        categories = state.rename_category_facet(document_id, old_name, new_name)
        if not collection_live:
            continue
        client.set_payload(
            collection_name=settings.qdrant_collection,
            payload={"categories": categories},
            points=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=document_id)
                    )
                ]
            ),
        )

    logger.info(
        "Term rename %r -> %r: refreshed %d documents%s.",
        old_name, new_name, len(document_ids),
        "" if collection_live else " (catalog only; collection missing)",
    )
    return len(document_ids)
