"""Rebuild a :class:`DocumentInput` for a document that is already indexed.

The ingest hook has the chunks in memory and passes them straight through. The
retry sweep and ``scripts.knowledge_document`` do not — they are looking at a
document that was indexed minutes or weeks ago — so they read it back from the
two stores that hold it: the catalog for the document's metadata, Qdrant for the
text of its current chunks.

Qdrant is the right source for the text. It is authoritative for chunk text and
vector evidence, and reading the chunk that is *actually indexed* is what keeps
a claim's ``chunk_id`` pointing at something a citation can fetch. Re-chunking
the document here would produce different ids and silently break that chain.

Tables of contents and bibliographies are deliberately **not** filtered out.
Retrieval excludes them because they pollute *search*; a bibliography is exactly
where author names live, so extraction wants them. This mirrors the filter in
``scripts.build_knowledge._documents`` for the same reason.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Points fetched per Qdrant scroll. A document's chunk count is small; this is
# a ceiling, not a target.
_SCROLL_BATCH = 256

__all__ = ["load_document", "load_chunks"]


def load_chunks(document_id: str, *, doc_version: int | None = None) -> list[Any]:
    """This document's current child chunks, ordered by chunk index.

    Ordered because mention offsets and quotes are per chunk but a reader of the
    report expects the document's own order; unordered scroll results would make
    two runs of the same document report their chunks differently for no reason.
    """
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    from app.config import get_settings
    from app.core.clients import get_qdrant_client
    from app.knowledge.document_pipeline import ChunkText

    must = [
        FieldCondition(key="document_id", match=MatchValue(value=document_id)),
        FieldCondition(key="is_parent", match=MatchValue(value=False)),
        FieldCondition(key="is_current", match=MatchValue(value=True)),
    ]
    if doc_version is not None:
        must.append(
            FieldCondition(key="doc_version", match=MatchValue(value=doc_version))
        )

    client = get_qdrant_client()
    collection = get_settings().qdrant_collection
    found: list[tuple[int, Any]] = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection, scroll_filter=Filter(must=must),
            limit=_SCROLL_BATCH, with_payload=True, with_vectors=False,
            offset=offset,
        )
        for point in points:
            payload = point.payload or {}
            found.append((
                int(payload.get("chunk_index") or 0),
                ChunkText(
                    chunk_id=str(point.id),
                    text=payload.get("chunk_text") or "",
                    content_hash=payload.get("content_hash") or "",
                ),
            ))
        if offset is None:
            break
    return [chunk for _, chunk in sorted(found, key=lambda pair: pair[0])]


def load_document(document_id: str, *, run_id: str | None = None) -> Any:
    """A :class:`DocumentInput` for an indexed document, or None.

    None when the document is not catalogued or has no current chunks. Both are
    ordinary answers rather than errors: a document deleted between being queued
    for retry and being retried is exactly the first case, and the caller should
    move on rather than fail.
    """
    from app.catalog import state
    from app.knowledge.document_pipeline import DocumentInput

    record = state.get(document_id)
    if record is None:
        logger.info(
            "Knowledge build requested for %s, which is not catalogued.",
            document_id,
        )
        return None

    doc_version = int(getattr(record, "doc_version", 1) or 1)
    chunks = load_chunks(document_id, doc_version=doc_version)
    if not chunks:
        # A catalogued document with no current points: mid-reindex, or never
        # indexed. Either way there is no text to extract from right now.
        logger.info(
            "%s has no current chunks in Qdrant; nothing to build knowledge "
            "from.", document_id,
        )
        return None

    return DocumentInput(
        document_id=document_id,
        doc_version=doc_version,
        chunks=tuple(chunks),
        source_type=getattr(record, "source_type", "") or "",
        bundle=getattr(record, "bundle", None),
        content_hash=getattr(record, "content_hash", "") or "",
        # Read separately, not from the record. `StateRecord` has a `raw_meta`
        # field but `state._row_to_record` never fills it — the blob is far too
        # large to carry on every record `state.load` builds — so taking it from
        # the record would silently always be None, and every CMS claim on this
        # path would vanish without an error to explain it.
        raw_meta=state.raw_meta_for(document_id),
        # From the facet, not the metadata blob: author names were moved to
        # `documents_author` and `raw_meta.field_authors` is empty corpus-wide,
        # so the blob alone leaves PERSON resolution with no corroboration.
        authors=tuple(state.authors_for(document_id)),
        run_id=run_id,
    )
