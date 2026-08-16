"""Create the Qdrant payload indexes the query path filters on.

`ensure_collection()` now provisions all of them, so a fresh deployment needs
nothing from this script. It remains for an existing collection that predates a
new index, and for checking one without changing it (`--dry-run`).

The index list lives in `app.core.clients.vector_store.PAYLOAD_INDEXES` and this
applies exactly that — the two used to keep separate lists, which is how nine of
them came to exist only where someone had remembered to run this.

Index creation runs server-side over existing points — nothing is re-ingested or
re-embedded — but it does alter the collection, so run it while no ingestion is
in progress. Idempotent; already-indexed fields are skipped.

Usage:  python -m scripts.create_payload_indexes [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("create_payload_indexes")


def create_indexes(dry_run: bool) -> int:
    from app.config import get_settings
    from app.core.clients import get_qdrant_client
    from app.core.clients.vector_store import PAYLOAD_INDEXES, ensure_payload_indexes

    collection = get_settings().qdrant_collection
    client = get_qdrant_client()
    if not client.collection_exists(collection):
        logger.error("Qdrant collection %r does not exist; nothing to index.", collection)
        return 1

    print(f"Collection {collection!r}: ensuring {len(PAYLOAD_INDEXES)} payload indexes")
    created = ensure_payload_indexes(client, collection, dry_run=dry_run)
    for field, kind in PAYLOAD_INDEXES.items():
        if field in created:
            print(f"  + {field}: {'would create' if dry_run else 'created'} ({kind})")
        else:
            print(f"  = {field}: already indexed")
    return 0


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
