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


def _build_points(
    chunks: Sequence[Chunk],
    vec_by_id: dict[str, list[float]],
    dim: int,
    *,
    stamp: bool = True,
) -> list[Any]:
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
    chunks = list(chunks)
    if not chunks:
        return 0

    from app.core.clients import ensure_collection, get_qdrant_client
    from app.config import get_settings

    ensure_collection()

    children = [c for c in chunks if not c.is_parent]
    with span("ingest.embed", chunks=len(children)):
        vectors = _embed_children([c.embed_text or c.text for c in children], batch_size)
    vec_by_id = {c.chunk_id: v for c, v in zip(children, vectors)}
    dim = len(vectors[0]) if vectors else _probe_dim()

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
        "Indexed %d points (%d children, %d parents) into %r",
        len(points), len(children), len(points) - len(children), settings.qdrant_collection,
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
