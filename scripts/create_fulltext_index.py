"""Create the Qdrant full-text index on chunk_text for the keyword leg.

`ensure_collection()` now provisions this alongside every other payload index,
so a fresh deployment needs nothing from here. It remains for an existing
collection that predates it, and because this is the one index worth being able
to build on its own: it is the heaviest, and the lexical path (`keyword_leg_enabled`)
degrades silently to dense-only while it is missing.

MatchText filtering is what covers the classic dense-retrieval failures —
acronyms, proper nouns, exact figures — without ingest-time sparse vectors. The
index is built server-side over existing points; nothing is re-ingested or
re-embedded, but run it while no ingestion is active.

Usage:  python -m scripts.create_fulltext_index [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("create_fulltext_index")

_FIELD = "chunk_text"


def create_index(dry_run: bool) -> int:
    from app.config import get_settings
    from app.core.clients import get_qdrant_client
    from app.core.clients.vector_store import ensure_payload_indexes

    collection = get_settings().qdrant_collection
    client = get_qdrant_client()
    if not client.collection_exists(collection):
        logger.error("Qdrant collection %r does not exist; nothing to index.", collection)
        return 1

    if _FIELD in set(client.get_collection(collection).payload_schema or {}):
        print(f"  = {_FIELD}: already indexed")
        return 0
    if dry_run:
        print(f"  + {_FIELD}: would create (text, word tokenizer, lowercase)")
        return 0

    # The shared helper owns the schema and the read-back that distinguishes "the
    # request timed out" from "the index was not built" — a text index over a
    # whole collection routinely outlives the client timeout while Qdrant carries
    # on server-side.
    created = ensure_payload_indexes(client, collection)
    if _FIELD in created:
        print(f"  + {_FIELD}: created (text, word tokenizer, lowercase)")
        return 0
    logger.warning("Could not create the text index on %r.", _FIELD)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report whether the index would be created; change nothing.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    rc = create_index(args.dry_run)
    print("Done (dry run)." if args.dry_run else "Done.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
