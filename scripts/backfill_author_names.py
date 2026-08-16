"""Populate `documents_author.author_norm` for rows written before it existed.

The column is derived, so this is always safe to re-run: it recomputes from the
raw `author` value, which is never modified. A document's next ingest would set
it anyway (see `app.catalog.state._replace_authors`); this fills the existing
corpus without waiting for one.

    python -m scripts.backfill_author_names --dry-run
    python -m scripts.backfill_author_names
"""
from __future__ import annotations

import argparse

from app.catalog import author_names, schema
from app.catalog.db import state_table
from app.core.clients import mysql_connection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="report without writing"
    )
    args = parser.parse_args(argv)

    table = f"{state_table()}_author"
    with mysql_connection() as conn, conn.cursor() as cur:
        applied = schema.migrate_author_names(
            cur, state_table(), dry_run=args.dry_run
        )
        for statement in applied:
            print(f"schema: {statement}")

        if args.dry_run and applied:
            print("(column does not exist yet; nothing to backfill)")
            return 0

        cur.execute(f"SELECT DISTINCT author FROM `{table}`")
        names = [row["author"] for row in cur.fetchall()]
        updates = [
            (author_names.normalize(name)[:255] or None, name) for name in names
        ]
        collapsed = len(names) - len({n for n, _ in updates if n})
        print(f"distinct raw author strings : {len(names)}")
        print(f"distinct normalized names   : {len({n for n, _ in updates if n})}")
        print(f"strings absorbed by merging : {collapsed}")

        if args.dry_run:
            print("\n(dry run — no rows written)")
            return 0

        cur.executemany(
            f"UPDATE `{table}` SET author_norm = %s WHERE author = %s", updates
        )
        conn.commit()

        cur.execute(f"SELECT COUNT(*) n FROM `{table}` WHERE author_norm IS NULL")
        remaining = cur.fetchone()["n"]
        cur.execute(f"SELECT COUNT(DISTINCT author_norm) n FROM `{table}`")
        distinct = cur.fetchone()["n"]
    print(f"\nrows still without a normalized form: {remaining}")
    print(f"distinct author_norm values         : {distinct}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
