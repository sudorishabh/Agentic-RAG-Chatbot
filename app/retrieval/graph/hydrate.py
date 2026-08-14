"""Turn graph identifiers into source text, from Qdrant.

This is the bridge the whole architecture rests on. Neo4j knows *that* something
is true and *where* it was read; Qdrant holds the text. The hop between them is
``chunk_id``, which has been the Qdrant point ID since long before the graph
existed — no new key, no duplicated text, no second store to keep in sync.

Two lookups, and the distinction matters
----------------------------------------
``retrieve`` by point id     an **exact** fetch of known chunks. Not a search:
                             no embedding, no scoring, no filter. This is what a
                             graph result needs, because the graph already
                             decided which chunks are relevant.
``search`` by document id    used only when a claim's evidence is a *document*
                             rather than a chunk — which is every claim today,
                             since all 1,653 are CMS-field claims and a metadata
                             fact has no span to point at. The document's own
                             chunks are fetched so the answer still quotes real
                             source text.

Both are batched. A graph answer can name a hundred chunks, and a hundred round
trips would cost more than the traversal that produced them.
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

# Ids per Qdrant call. Matches the cap the existing id-scoped retrieval uses
# (app.retrieval.scoped_retrieval._MAX_IDS) so both paths behave alike.
BATCH_SIZE = 150

# Chunks fetched per document when evidence is document-level. Small: this is
# supporting evidence for a structured fact, not a semantic search, and the
# reranker will cut it down anyway.
CHUNKS_PER_DOCUMENT = 3

# Documents hydrated for one answer. A graph result may cite up to `MAX_LIMIT`
# of them, but the context builder keeps a handful of blocks, so fetching every
# one buys nothing and costs a round trip each in the fairness pass below.
MAX_DOCUMENTS = 20


def hydrate_chunks(chunk_ids: Sequence[str]) -> list[Any]:
    """Exact fetch of chunks by id, batched. Order follows ``chunk_ids``.

    Deduplicates first: a graph result routinely names the same chunk twice
    (two claims from one document), and fetching it twice would put the same
    text in the prompt twice.
    """
    from app.config import get_settings
    from app.core.clients import get_qdrant_client
    from app.retrieval.hybrid_search import Candidate

    unique: list[str] = []
    seen: set[str] = set()
    for chunk_id in chunk_ids:
        if chunk_id and chunk_id not in seen:
            seen.add(chunk_id)
            unique.append(chunk_id)
    if not unique:
        return []

    settings = get_settings()
    client = get_qdrant_client()
    by_id: dict[str, Candidate] = {}
    for start in range(0, len(unique), BATCH_SIZE):
        batch = unique[start : start + BATCH_SIZE]
        try:
            records = client.retrieve(
                collection_name=settings.qdrant_collection,
                ids=batch, with_payload=True, with_vectors=False,
            )
        except Exception:
            # A hydration failure must not fabricate evidence: the batch is
            # skipped and the answer is built from what did resolve.
            logger.warning("Chunk hydration failed for a batch.", exc_info=True)
            continue
        for record in records:
            by_id[str(record.id)] = Candidate(
                id=str(record.id), score=0.0, payload=record.payload or {}
            )

    missing = [c for c in unique if c not in by_id]
    if missing:
        # A chunk the graph cites but Qdrant no longer holds. Expected after a
        # re-index changes chunk ids, and the honest response is to drop it
        # rather than to invent a citation.
        logger.info("%d cited chunk(s) not found in Qdrant.", len(missing))
    return [by_id[c] for c in unique if c in by_id]


def hydrate_documents(
    document_ids: Sequence[str], *, per_document: int = CHUNKS_PER_DOCUMENT
) -> list[Any]:
    """Fetch a few chunks for each document, for document-level evidence.

    Uses the existing id-scoped filter rather than a new query path, so the
    mandatory shape filter (current child chunks, searchable sections) applies
    exactly as it does everywhere else.

    Two passes, because ``scroll`` has no notion of fairness. A single scroll
    over many documents returns whatever it reaches first, so one long document
    can spend the whole budget and leave every other cited document with no
    evidence at all. The broad scroll is kept because it usually does cover
    everything in one round trip; the second pass then fetches, one document at
    a time, only for documents it missed entirely.
    """
    from app.config import get_settings
    from app.core.clients import get_qdrant_client
    from app.retrieval.hybrid_search import Candidate, build_filter

    unique = list(dict.fromkeys(d for d in document_ids if d))
    if not unique:
        return []
    # The reranker keeps a handful of blocks, so evidence for the first
    # documents is ample; hydrating a hundred would cost round trips to produce
    # candidates that are discarded.
    unique = unique[:MAX_DOCUMENTS]

    from qdrant_client.models import FieldCondition, MatchAny, MatchValue

    settings = get_settings()
    client = get_qdrant_client()
    out: list[Any] = []
    per_doc: dict[str, int] = {}

    def _scroll(conditions: list[Any], limit: int) -> list[Any]:
        try:
            points, _ = client.scroll(
                collection_name=settings.qdrant_collection,
                scroll_filter=build_filter(extra=conditions),
                limit=limit, with_payload=True, with_vectors=False,
            )
            return points
        except Exception:
            logger.warning("Document hydration failed.", exc_info=True)
            return []

    def _take(points: Sequence[Any]) -> None:
        for point in points:
            payload = point.payload or {}
            document_id = payload.get("document_id")
            if per_doc.get(document_id, 0) >= per_document:
                continue
            per_doc[document_id] = per_doc.get(document_id, 0) + 1
            out.append(Candidate(id=str(point.id), score=0.0, payload=payload))

    for start in range(0, len(unique), BATCH_SIZE):
        batch = unique[start : start + BATCH_SIZE]
        _take(
            _scroll(
                [FieldCondition(key="document_id", match=MatchAny(any=batch))],
                len(batch) * per_document,
            )
        )

    for document_id in unique:
        if per_doc.get(document_id):
            continue
        _take(
            _scroll(
                [FieldCondition(key="document_id",
                                match=MatchValue(value=document_id))],
                per_document,
            )
        )
    return out


def hydrate(result: Any, *, per_document: int = CHUNKS_PER_DOCUMENT) -> list[Any]:
    """Source evidence for a graph result: chunks first, documents as fallback.

    A claim citing a chunk is preferred — the span is exact. Document evidence is
    used only for claims that have no chunk, which today is all of them, because
    a CMS metadata fact has no prose to point at.
    """
    candidates = hydrate_chunks(result.chunk_ids)
    covered = {c.payload.get("document_id") for c in candidates}
    remaining = [d for d in result.document_ids if d not in covered]
    if remaining:
        candidates.extend(hydrate_documents(remaining, per_document=per_document))
    return candidates
