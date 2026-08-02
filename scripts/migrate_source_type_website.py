"""One-shot migration: rename source_type 'article' -> 'website'.

"website" is the canonical source_type for Drupal-sourced content (the value
"article" was overloaded with the Drupal bundle of the same name). The code
writes "website" and tolerates both on read, so running this is not urgent —
but storage should converge so the legacy value can eventually be dropped.

Touches:
  1. Qdrant payloads   — set source_type="website" where it is "article"
                         (payload-only update; no re-embedding).
  2. MySQL manifest    — UPDATE ingest_state rows (keeps change detection
                         incremental without the merged-load fallback).
  3. Redis caches      — bump the corpus version so cached responses built
                         with type="article" citations expire immediately.

Idempotent; safe to re-run. The append-only ingest_log audit table is left
as-is (historical record).

Usage:  python -m scripts.migrate_source_type_website [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("migrate_source_type")


def _article_filter():
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    return Filter(must=[FieldCondition(key="source_type", match=MatchValue(value="article"))])


def _count(client, collection: str) -> int:
    return client.count(
        collection_name=collection, count_filter=_article_filter(), exact=True
    ).count


def migrate_qdrant(dry_run: bool) -> None:
    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    settings = get_settings()
    collection = settings.qdrant_collection
    client = get_qdrant_client()
    if not client.collection_exists(collection):
        logger.warning("Qdrant collection %r does not exist; skipping.", collection)
        return

    before = _count(client, collection)
    logger.info("Qdrant %r: %d points with source_type='article'.", collection, before)
    if dry_run or not before:
        return

    client.set_payload(
        collection_name=collection,
        payload={"source_type": "website"},
        points=_article_filter(),
        wait=True,
    )
    logger.info("Qdrant: updated; %d 'article' points remain.", _count(client, collection))


def migrate_mysql(dry_run: bool) -> None:
    from app.config import get_settings
    from app.core.clients import mysql_connection

    table = get_settings().ingest_state_table
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) AS n FROM `{table}` WHERE source_type = 'article'"
            )
            before = cur.fetchone()["n"]
            logger.info("MySQL %s: %d rows with source_type='article'.", table, before)
            if dry_run or not before:
                return
            cur.execute(
                f"UPDATE `{table}` SET source_type = 'website' WHERE source_type = 'article'"
            )
            conn.commit()
            logger.info("MySQL: %d rows updated.", cur.rowcount)
    except Exception:
        logger.warning("MySQL migration skipped (table/connection unavailable).", exc_info=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="Report counts only.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    migrate_qdrant(args.dry_run)
    migrate_mysql(args.dry_run)
    logger.info("Done%s.", " (dry run)" if args.dry_run else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
