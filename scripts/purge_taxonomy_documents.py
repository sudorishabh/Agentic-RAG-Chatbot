"""Delete the taxonomy-term documents the searchable crawl no longer produces.

Terms were once crawled as documents in their own right. `detect_drupal_changes`
stopped admitting them (only `node` and `block_content` are searchable sources
now), but the rows and points already written stayed behind: a frozen, unowned
slice of the catalog that nothing refreshes and that still answers searches.

Most terms carry no description, so they chunked to nothing — the catalog rows
far outnumber the Qdrant points. Both are removed here.

Facet rows (`_theme`, `_tag`, `_author`, `_attachment`) cascade with the parent
row via their foreign keys, so they are reported but not deleted directly.

This deletes rather than migrates: the corpus is re-ingested from source, and a
taxonomy term is not a document in the new model. Nothing reads these rows —
theme and tag filtering match on names carried in each content chunk's own
payload (`categories` / `tags`), never on a term document.

    python -m scripts.purge_taxonomy_documents            # report only
    python -m scripts.purge_taxonomy_documents --apply    # actually delete
"""
from __future__ import annotations

import argparse
import logging
import sys

from app.catalog.db import state_table
from app.core.clients import get_qdrant_client, mysql_connection

logger = logging.getLogger(__name__)

# The JSON:API entity type recorded for a crawled taxonomy term. Content
# documents are "node" / "block_content"; attachments carry NULL.
_TAXONOMY_ENTITY_TYPE = "taxonomy_term"

# Qdrant caps how much a single filter may carry, so document ids are matched in
# batches rather than one MatchAny over every term.
_ID_BATCH = 400

# Facet tables whose rows disappear with the parent document via ON DELETE
# CASCADE. Listed to report the blast radius, not to delete from.
_FACETS = ("author", "tag", "theme", "attachment")


def _taxonomy_ids(cur) -> list[str]:
    cur.execute(
        f"SELECT document_id FROM `{state_table()}` WHERE entity_type = %s",
        (_TAXONOMY_ENTITY_TYPE,),
    )
    return [row["document_id"] for row in cur.fetchall()]


def _cascade_counts(cur) -> dict[str, int]:
    counts: dict[str, int] = {}
    for facet in _FACETS:
        table = f"{state_table()}_{facet}"
        cur.execute(
            f"SELECT COUNT(*) AS n FROM `{table}` f "
            f"JOIN `{state_table()}` d ON d.document_id = f.document_id "
            "WHERE d.entity_type = %s",
            (_TAXONOMY_ENTITY_TYPE,),
        )
        row = cur.fetchone()
        counts[table] = int(row["n"]) if row else 0
    return counts


def _point_count(document_ids: list[str]) -> int:
    """Points belonging to the given documents; 0 if Qdrant is unreachable."""
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    from app.config import get_settings

    collection = get_settings().qdrant_collection
    client = get_qdrant_client()
    if not client.collection_exists(collection):
        return 0
    total = 0
    for start in range(0, len(document_ids), _ID_BATCH):
        batch = document_ids[start : start + _ID_BATCH]
        total += client.count(
            collection_name=collection,
            count_filter=Filter(
                must=[FieldCondition(key="document_id", match=MatchAny(any=batch))]
            ),
            exact=True,
        ).count
    return total


def _delete_points(document_ids: list[str]) -> int:
    """Drop every point owned by the given documents. Returns batches deleted."""
    from qdrant_client.models import (
        FieldCondition,
        Filter,
        FilterSelector,
        MatchAny,
    )

    from app.config import get_settings

    collection = get_settings().qdrant_collection
    client = get_qdrant_client()
    if not client.collection_exists(collection):
        return 0
    batches = 0
    for start in range(0, len(document_ids), _ID_BATCH):
        batch = document_ids[start : start + _ID_BATCH]
        client.delete(
            collection_name=collection,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(key="document_id", match=MatchAny(any=batch))
                    ]
                )
            ),
        )
        batches += 1
    return batches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually delete. Without it, only report what would go.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    with mysql_connection() as conn, conn.cursor() as cur:
        ids = _taxonomy_ids(cur)
        if not ids:
            print("No taxonomy-term documents remain. Nothing to do.")
            return 0

        cascades = _cascade_counts(cur)
        points = _point_count(ids)

        print(f"  {state_table():28} {len(ids):>8} taxonomy-term rows")
        for table, count in cascades.items():
            print(f"  {table:28} {count:>8} rows (cascade)")
        print(f"  {'qdrant points':28} {points:>8}")

        if not args.apply:
            print(
                "\nDry run. Re-run with --apply to delete. This cannot be undone "
                "without re-crawling the terms."
            )
            return 0

        batches = _delete_points(ids)
        print(f"  deleted qdrant points in {batches} batch(es)")

        cur.execute(
            f"DELETE FROM `{state_table()}` WHERE entity_type = %s",
            (_TAXONOMY_ENTITY_TYPE,),
        )
        deleted = cur.rowcount
        conn.commit()
        print(f"  deleted {deleted} catalog rows (facets cascaded)")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
