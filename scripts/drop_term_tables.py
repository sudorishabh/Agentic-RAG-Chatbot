"""Drop the retired taxonomy-term tables.

The catalog is keyed by **name** now: themes live in ``documents_theme``, tags in
``documents_tag``, and taxonomy UUIDs only in Qdrant payloads. Nothing reads or
writes ``documents_term`` / ``terms`` / ``term_aliases`` any more — see
docs/retire-term-tables-plan.md.

Deliberately a manual script rather than part of ``schema.ensure_tables()``:
``documents_term`` holds tens of thousands of link rows, and rebuilding them
would need a full re-ingest. Run this only once the name-keyed path has been
verified in place.

    python -m scripts.drop_term_tables            # show what would be dropped
    python -m scripts.drop_term_tables --apply    # actually drop
"""
from __future__ import annotations

import argparse
import logging

from app.catalog.db import state_table
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)

# `documents_term` follows the configured table prefix; the other two were always
# fixed names (terms were site-global facts shared across environments).
_FIXED_TABLES = ("terms", "term_aliases")


def _tables() -> list[str]:
    return [f"{state_table()}_term", *_FIXED_TABLES]


def _row_count(cur, table: str) -> int | None:
    """Rows in `table`, or None when it does not exist (already dropped)."""
    cur.execute(
        "SELECT 1 FROM information_schema.TABLES "
        "WHERE table_schema = DATABASE() AND table_name = %s",
        (table,),
    )
    if cur.fetchone() is None:
        return None
    cur.execute(f"SELECT COUNT(*) AS n FROM `{table}`")
    row = cur.fetchone()
    return int(row["n"]) if row else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually drop the tables. Without it, only report what would go.",
    )
    args = parser.parse_args(argv)

    with mysql_connection() as conn, conn.cursor() as cur:
        counts = {table: _row_count(cur, table) for table in _tables()}
        present = {t: n for t, n in counts.items() if n is not None}

        for table, count in counts.items():
            if count is None:
                print(f"  {table:24} already gone")
            else:
                print(f"  {table:24} {count:>8} rows")

        if not present:
            print("\nNothing to drop.")
            return 0
        if not args.apply:
            print(
                f"\nDry run. Re-run with --apply to drop {len(present)} table(s). "
                "This cannot be undone without a full re-ingest."
            )
            return 0

        for table in present:
            cur.execute(f"DROP TABLE IF EXISTS `{table}`")
            print(f"  dropped {table}")
        conn.commit()
    print("\nDone.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
