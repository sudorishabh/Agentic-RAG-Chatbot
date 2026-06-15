"""Index canonical chunks into Qdrant.

The last hop of the ingestion pipeline (§3.2 / §3.7): take the parent + child
:class:`~app.ingestion.chunker.Chunk`s produced from a
:class:`~app.core.models.CanonicalDocument` and upsert them as Qdrant points.

* **Child** chunks are embedded (dense vector) — these are what search matches.
* **Parent** chunks are stored with a zero vector and ``is_parent=true`` — never
  searched, only fetched by id to feed the LLM ("search small, read big").

Both share the canonical payload from ``Chunk.to_payload()``; this module adds
the ``created_at`` / ``updated_at`` write-time timestamps. Point ids are the
deterministic chunk UUIDs, so re-indexing identical content overwrites in place
(idempotent).

Heavy clients (Qdrant, Azure embeddings) are reached lazily through
``app.deps`` / ``app.ingestion.embedder`` so importing this module stays cheap.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

from app.core.models import CanonicalDocument
from app.ingestion.chunker import Chunk, chunk_canonical

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _embed_children(texts: Sequence[str], batch_size: int) -> list[list[float]]:
    """Embed child texts in batches with the configured Azure embedding model."""
    from app.ingestion.embedder import get_embeddings

    embeddings = get_embeddings()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = list(texts[start : start + batch_size])
        vectors.extend(embeddings.embed_documents(batch))
    return vectors


def _build_points(
    chunks: Sequence[Chunk],
    vec_by_id: dict[str, list[float]],
    dim: int,
    *,
    stamp: bool = True,
) -> list[Any]:
    """Turn chunks into Qdrant points. Parents get a zero vector (never
    searched); children carry their dense embedding. Kept import-light and pure
    so it is unit-testable without a live Qdrant."""
    from qdrant_client.models import PointStruct

    timestamp = _now_iso()
    zero = [0.0] * dim
    points: list[Any] = []
    for chunk in chunks:
        payload = chunk.to_payload()
        if stamp:
            payload.setdefault("created_at", timestamp)
            payload["updated_at"] = timestamp
        vector = zero if chunk.is_parent else vec_by_id[chunk.chunk_id]
        points.append(PointStruct(id=chunk.chunk_id, vector=vector, payload=payload))
    return points


def index_chunks(chunks: Sequence[Chunk], *, batch_size: int = 128, stamp: bool = True) -> int:
    """Embed child chunks and upsert all chunks (parents + children) into the
    configured Qdrant collection. Returns the number of points upserted."""
    chunks = list(chunks)
    if not chunks:
        return 0

    from app.deps import ensure_collection, get_qdrant_client
    from app.config import get_settings

    ensure_collection()

    children = [c for c in chunks if not c.is_parent]
    vectors = _embed_children([c.text for c in children], batch_size)
    vec_by_id = {c.chunk_id: v for c, v in zip(children, vectors)}
    dim = len(vectors[0]) if vectors else _probe_dim()

    points = _build_points(chunks, vec_by_id, dim, stamp=stamp)

    settings = get_settings()
    client = get_qdrant_client()
    for start in range(0, len(points), batch_size):
        client.upsert(
            collection_name=settings.qdrant_collection,
            points=points[start : start + batch_size],
        )
    logger.info(
        "Indexed %d points (%d children, %d parents) into %r",
        len(points), len(children), len(points) - len(children), settings.qdrant_collection,
    )
    return len(points)


def _probe_dim() -> int:
    """Embedding dimension, for sizing the parents' zero vector when a document
    has no child chunks to embed."""
    from app.ingestion.embedder import get_embeddings

    return len(get_embeddings().embed_query("dimension probe"))


# --------------------------------------------------------------------------- #
# Convenience: source → chunk → index in one call
# --------------------------------------------------------------------------- #
def index_canonical(doc: CanonicalDocument, **chunk_kwargs: Any) -> int:
    """Chunk a canonical document and index the result."""
    return index_chunks(chunk_canonical(doc, **chunk_kwargs))


def index_documents(docs: Iterable[CanonicalDocument], **chunk_kwargs: Any) -> int:
    """Chunk and index a stream of canonical documents; returns total points."""
    total = 0
    for doc in docs:
        try:
            total += index_canonical(doc, **chunk_kwargs)
        except Exception:  # pragma: no cover - one bad doc shouldn't sink a crawl
            logger.exception("Failed indexing document %s; skipping", doc.document_id)
    return total


# --------------------------------------------------------------------------- #
# CLI — ingest both sources into Qdrant:
#   python -m app.ingestion.indexer --drupal-json rpapers.json
#   python -m app.ingestion.indexer --pdf report.pdf
#   python -m app.ingestion.indexer --bundle news --bundle research_papers
# --------------------------------------------------------------------------- #
def _main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Index PDF / Drupal content into Qdrant.")
    parser.add_argument("--drupal-json", help="A drupal_extractor --json dump to index.")
    parser.add_argument("--pdf", action="append", default=[], help="PDF file(s) to extract + index.")
    parser.add_argument("--bundle", action="append", default=[], help="Live Drupal bundle(s) to crawl + index.")
    parser.add_argument("--encoding", default="utf-8", help="Encoding of --drupal-json (default: utf-8).")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    total = 0

    if args.drupal_json:
        from app.ingestion.canonical import from_drupal_export

        items = json.loads(Path(args.drupal_json).read_text(encoding=args.encoding))
        total += index_documents(from_drupal_export(item) for item in items)

    for pdf_path in args.pdf:
        from app.ingestion.canonical import from_pdf
        from app.ingestion.extractors.pdf_extractor import extract_pdf

        path = Path(pdf_path)
        result = extract_pdf(path.read_bytes(), path.name)
        total += index_canonical(from_pdf(result))

    if args.bundle:
        from app.ingestion.canonical import from_drupal_record
        from app.ingestion.extractors.drupal_extractor import iter_records

        total += index_documents(from_drupal_record(rec) for rec in iter_records(args.bundle))

    print(f"Indexed {total} points.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
