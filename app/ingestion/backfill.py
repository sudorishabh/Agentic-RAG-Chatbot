from __future__ import annotations

import logging
from typing import Any, Iterator

from app.catalog import state
from app.config import get_settings
from app.core.clients import get_qdrant_client

logger = logging.getLogger(__name__)

# Document-level fields to lift out of the chunk payloads back into the catalog.
_PAYLOAD_FIELDS = [
    "document_id", "published_at", "authors", "categories", "title", "source_url",
]


def _iter_payloads(batch_size: int = 512) -> Iterator[dict[str, Any]]:
    settings = get_settings()
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        logger.warning(
            "Collection %r does not exist; nothing to backfill.", settings.qdrant_collection
        )
        return

    offset: Any = None
    while True:
        points, offset = client.scroll(
            collection_name=settings.qdrant_collection,
            limit=batch_size,
            offset=offset,
            with_payload=_PAYLOAD_FIELDS,
            with_vectors=False,
        )
        for point in points:
            if point.payload:
                yield point.payload
        if offset is None:
            break


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if v]
    return [str(value)]


def collect() -> dict[str, dict[str, Any]]:
    """Aggregate document-level facets across every chunk payload, keyed by
    document_id. Chunks of one document share these fields, so first-seen date
    and unioned author/category values reconstruct the document's facets."""
    docs: dict[str, dict[str, Any]] = {}
    for payload in _iter_payloads():
        doc_id = payload.get("document_id")
        if not doc_id:
            continue
        entry = docs.setdefault(
            doc_id,
            {"published_at": None, "authors": [], "categories": [], "title": None, "url": None},
        )
        if entry["published_at"] is None and payload.get("published_at"):
            entry["published_at"] = payload["published_at"]
        if entry["title"] is None and payload.get("title"):
            entry["title"] = payload["title"]
        if entry["url"] is None and payload.get("source_url"):
            entry["url"] = payload["source_url"]
        for key in ("authors", "categories"):
            for value in _as_list(payload.get(key)):
                if value not in entry[key]:
                    entry[key].append(value)
    return docs


def backfill_catalog() -> dict[str, int]:
    docs = collect()
    updated = skipped = 0
    for doc_id, facets in docs.items():
        if state.backfill_facets(
            doc_id, facets["published_at"], facets["authors"], facets["categories"],
            title=facets["title"], url=facets["url"],
        ):
            updated += 1
        else:
            skipped += 1
    logger.info(
        "Backfill complete: %d updated, %d skipped (no catalog row).", updated, skipped
    )
    return {"updated": updated, "skipped": skipped}


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill catalog title/url/date/author/category from Qdrant payloads."
    )
    parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(f"Backfill: {backfill_catalog()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
