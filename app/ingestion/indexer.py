from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

from app.core.models import CanonicalDocument
from app.ingestion.chunking import Chunk, chunk_canonical
from app.observability.tracing import span

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _embed_children(texts: Sequence[str], batch_size: int) -> list[list[float]]:
    from app.core.clients import get_embeddings

    embeddings = get_embeddings()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = list(texts[start : start + batch_size])
        vectors.extend(embeddings.embed_documents(batch))
    return vectors


def _reusable_vectors(children: Sequence[Chunk]) -> dict[str, list[float]]:
    """Stored vectors for these chunk ids whose embedding input is unchanged.

    A chunk id is derived from its owned content, so an unchanged chunk keeps its
    id across re-index. ``embed_hash`` covers the exact string the embedder was
    handed — overlap carry and "title › heading" breadcrumb included — so a
    matching hash means the stored vector still describes what this chunk would
    embed to, and the call can be skipped. Anything that moves that string
    re-embeds: an edit to the chunk, to its carry, to the document title, or to
    the heading above it.

    Deliberately not ``content_hash``: that covers ``text`` alone, so keying on
    it reused a vector built from the old title whenever a document was renamed.

    The same input embedded by a different model is a different vector, so
    ``embed_model`` has to agree too. Without that check, repointing the
    deployment leaves the collection a silent mix of two models' vectors that no
    re-index repairs — re-indexing is exactly what reuses them.

    Best-effort: any failure reading the store falls back to embedding
    everything, which is what the pipeline did before this existed. A point
    stored before either key existed has nothing to match and is re-embedded,
    which is the safe direction.
    """
    if not children:
        return {}

    from app.config import get_settings
    from app.core.clients import embedding_version, get_qdrant_client

    settings = get_settings()
    want = {c.chunk_id: c.embed_hash for c in children}
    model = embedding_version()
    try:
        records = get_qdrant_client().retrieve(
            collection_name=settings.qdrant_collection,
            ids=list(want),
            with_payload=["embed_hash", "embed_model"],
            with_vectors=True,
        )
    except Exception:  # pragma: no cover - store hiccup / collection missing
        logger.debug("Could not read stored vectors; embedding every chunk.", exc_info=True)
        return {}

    reusable: dict[str, list[float]] = {}
    for record in records:
        vector = getattr(record, "vector", None)
        if not isinstance(vector, list) or not vector:
            continue
        payload = getattr(record, "payload", None) or {}
        if payload.get("embed_model") != model:
            continue
        stored = payload.get("embed_hash")
        chunk_id = str(record.id)
        if stored and stored == want.get(chunk_id):
            reusable[chunk_id] = list(vector)
    return reusable


def _build_points(
    chunks: Sequence[Chunk],
    vec_by_id: dict[str, list[float]],
    dim: int,
    *,
    stamp: bool = True,
) -> list[Any]:
    from qdrant_client.models import PointStruct

    from app.core.clients import embedding_version

    timestamp = _now_iso()
    model = embedding_version()
    zero = [0.0] * dim
    points: list[Any] = []
    for chunk in chunks:
        payload = chunk.to_payload()
        if stamp:
            payload.setdefault("created_at", timestamp)
            payload["updated_at"] = timestamp
        if not chunk.is_parent:
            # Which configuration produced this vector. Identity, not a stamp,
            # so it is written even when timestamping is off — reuse compares it.
            payload["embed_model"] = model
        vector = zero if chunk.is_parent else vec_by_id[chunk.chunk_id]
        points.append(PointStruct(id=chunk.chunk_id, vector=vector, payload=payload))
    return points


def index_chunks(chunks: Sequence[Chunk], *, batch_size: int = 128, stamp: bool = True) -> int:
    chunks = list(chunks)
    if not chunks:
        return 0

    from app.core.clients import ensure_collection, get_qdrant_client
    from app.config import get_settings

    ensure_collection()

    children = [c for c in chunks if not c.is_parent]
    reused = _reusable_vectors(children)
    pending = [c for c in children if c.chunk_id not in reused]
    with span("ingest.embed", chunks=len(pending), reused=len(reused)):
        vectors = _embed_children([c.embed_input for c in pending], batch_size)
    vec_by_id = dict(reused)
    vec_by_id.update(zip((c.chunk_id for c in pending), vectors))
    dim = len(next(iter(vec_by_id.values()))) if vec_by_id else _probe_dim()

    points = _build_points(chunks, vec_by_id, dim, stamp=stamp)

    settings = get_settings()
    client = get_qdrant_client()
    with span("ingest.upsert", points=len(points)):
        for start in range(0, len(points), batch_size):
            client.upsert(
                collection_name=settings.qdrant_collection,
                points=points[start : start + batch_size],
            )
    logger.info(
        "Indexed %d points (%d children: %d embedded, %d reused; %d parents) into %r",
        len(points), len(children), len(pending), len(reused),
        len(points) - len(children), settings.qdrant_collection,
    )
    return len(points)


def _probe_dim() -> int:
    from app.core.clients import get_embeddings

    return len(get_embeddings().embed_query("dimension probe"))


def index_canonical(doc: CanonicalDocument, **chunk_kwargs: Any) -> int:
    return index_chunks(chunk_canonical(doc, **chunk_kwargs))


def index_documents(docs: Iterable[CanonicalDocument], **chunk_kwargs: Any) -> int:
    total = 0
    for doc in docs:
        try:
            total += index_canonical(doc, **chunk_kwargs)
        except Exception:  # pragma: no cover - one bad doc shouldn't sink a crawl
            logger.exception("Failed indexing document %s; skipping", doc.document_id)
    return total


def _main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Index Drupal content into Qdrant.")
    parser.add_argument("--drupal-json", help="A drupal_extractor --json dump to index.")
    parser.add_argument("--bundle", action="append", default=[], help="Live Drupal bundle(s) to crawl + index.")
    parser.add_argument("--encoding", default="utf-8", help="Encoding of --drupal-json (default: utf-8).")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    total = 0

    if args.drupal_json:
        from app.ingestion.canonical import from_drupal_export

        items = json.loads(Path(args.drupal_json).read_text(encoding=args.encoding))
        total += index_documents(from_drupal_export(item) for item in items)

    if args.bundle:
        from app.ingestion.canonical import from_drupal_record
        from app.ingestion.extractors.drupal_extractor import iter_records

        total += index_documents(from_drupal_record(rec) for rec in iter_records(args.bundle))

    print(f"Indexed {total} points.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
