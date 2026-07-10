"""Create the Qdrant full-text index on chunk_text for the keyword leg.

Enables MatchText filtering (acronyms, proper nouns, exact figures — the
classic dense-retrieval failure modes) without ingest-time sparse vectors.
The index is built server-side over existing points — nothing is re-ingested
or re-embedded — but this is the heaviest index the retrieval plan creates,
so run it only while no ingestion run is active.

Idempotent; safe to re-run (an existing index is reported and skipped).

Usage:  python -m scripts.create_fulltext_index [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("create_fulltext_index")

_FIELD = "chunk_text"


def create_index(dry_run: bool) -> int:
    from qdrant_client.models import TextIndexParams, TokenizerType

    from app.config import get_settings
    from app.deps import get_qdrant_client

    collection = get_settings().qdrant_collection
    client = get_qdrant_client()
    if not client.collection_exists(collection):
        logger.error("Qdrant collection %r does not exist; nothing to index.", collection)
        return 1

    existing = set(client.get_collection(collection).payload_schema or {})
    if _FIELD in existing:
        print(f"  = {_FIELD}: already indexed")
        return 0
    if dry_run:
        print(f"  + {_FIELD}: would create (text, word tokenizer, lowercase)")
        return 0
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name=_FIELD,
            field_schema=TextIndexParams(
                type="text",
                tokenizer=TokenizerType.WORD,
                lowercase=True,
            ),
            wait=True,
        )
        print(f"  + {_FIELD}: created (text, word tokenizer, lowercase)")
    except Exception:
        logger.warning("Could not create text index on %r.", _FIELD, exc_info=True)
        return 1
    return 0


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
