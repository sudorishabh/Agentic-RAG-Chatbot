"""Create the Qdrant payload indexes the query path filters on.

Every search filters on is_parent / is_current / tenant_id / acl and often
source_type, language and section_type, but only published_at is indexed at
ingest time. Index creation runs server-side over
existing points — nothing is re-ingested or re-embedded — but it does alter
the collection, so run this only while no ingestion run is in progress.

Idempotent; safe to re-run (already-indexed fields are reported and skipped).

Usage:  python -m scripts.create_payload_indexes [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("create_payload_indexes")

# Field -> payload schema kind. Booleans filter as BOOL; the rest are
# exact-match keyword filters (document_id is filtered by delete_document
# today and by the Phase 2 id-scoped retrieval).
_INDEX_FIELDS: dict[str, str] = {
    "is_parent": "bool",
    "is_current": "bool",
    "tenant_id": "keyword",
    "acl": "keyword",
    "source_type": "keyword",
    "language": "keyword",
    "section_type": "keyword",
    "authors": "keyword",
    "tags": "keyword",
    "document_id": "keyword",
}


def create_indexes(dry_run: bool) -> int:
    from qdrant_client.models import PayloadSchemaType

    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    schema = {"bool": PayloadSchemaType.BOOL, "keyword": PayloadSchemaType.KEYWORD}
    collection = get_settings().qdrant_collection
    client = get_qdrant_client()
    if not client.collection_exists(collection):
        logger.error("Qdrant collection %r does not exist; nothing to index.", collection)
        return 1

    existing = set(client.get_collection(collection).payload_schema or {})
    print(f"Collection {collection!r}: ensuring {len(_INDEX_FIELDS)} payload indexes")
    failures = 0
    for field, kind in _INDEX_FIELDS.items():
        if field in existing:
            print(f"  = {field}: already indexed")
        elif dry_run:
            print(f"  + {field}: would create ({kind})")
        else:
            # Best-effort per field (vector_store._ensure_keyword_index style): one
            # failure must not abort the remaining indexes.
            try:
                client.create_payload_index(
                    collection_name=collection,
                    field_name=field,
                    field_schema=schema[kind],
                    wait=True,
                )
                print(f"  + {field}: created ({kind})")
            except Exception:
                failures += 1
                logger.warning("Could not create %s index on %r.", kind, field, exc_info=True)
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report which indexes would be created; change nothing.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    rc = create_indexes(args.dry_run)
    print("Done (dry run)." if args.dry_run else "Done.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
