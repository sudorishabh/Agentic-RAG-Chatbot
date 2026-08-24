"""Pre-flight for the ``document_published_at`` column. Dry run by default.

Shows the DDL that would run, whether the column already exists, and the
resulting representation of the 10 annual reports. Nothing is written unless
``--apply`` is passed, and even then the only change is the additive column:
no row value is modified, because the column is created NULL and every annual
report is meant to stay NULL.

``published_at`` is not read, written or compared here. That is the point of the
design: the page date keeps its meaning and its value.

    python -m scripts.preflight_document_published_at
    python -m scripts.preflight_document_published_at --apply
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger(__name__)

COLUMN = "document_published_at"
DDL = f"ALTER TABLE `{{table}}` ADD COLUMN {COLUMN} DATETIME NULL"


def column_exists(cur, table: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) AS n FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
        (table, COLUMN),
    )
    return bool((cur.fetchone() or {}).get("n"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Create the column. Omit for a dry run.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    mode = "APPLY" if args.apply else "DRY RUN — nothing will be written"
    print(f"=== {mode} ===\n")

    with mysql_connection() as conn, conn.cursor() as cur:
        exists = column_exists(cur, table)
        print(f"table                : `{table}`")
        print(f"column `{COLUMN}` : {'present' if exists else 'ABSENT'}")
        print(f"DDL                  : {DDL.format(table=table)}")
        print("row values changed   : none (the column is created NULL, and every "
              "annual report is intended to stay NULL)")
        print("published_at         : not read, not written, not compared\n")

        if args.apply and not exists:
            # Mirrors what `schema.ensure_state_table` would do on the next
            # ingestion run; doing it here makes the moment explicit and
            # reviewable rather than a side effect of a sweep.
            cur.execute(DDL.format(table=table))
            conn.commit()
            exists = column_exists(cur, table)
            print(f"created: {exists}\n")

        if not exists:
            print("The 10 annual reports, as they would read once the column "
                  "exists (all NULL):\n")
        else:
            print("The 10 annual reports as stored now:\n")

        select_doc = f", {COLUMN}" if exists else ""
        cur.execute(
            f"SELECT document_id, title, published_at{select_doc} FROM `{table}` "
            "WHERE source_type = 'pdf_attachment' AND document_id LIKE 'inbody:%%' "
            "AND title LIKE 'Annual Report %%' ORDER BY title"
        )
        rows = list(cur.fetchall())

    print(f"{'title':<26}{'published_at (page)':<22}{COLUMN}")
    for row in rows:
        stored = row.get(COLUMN, None) if exists else None
        print(f"{str(row['title'])[:25]:<26}{str(row['published_at'])[:19]:<22}"
              f"{'NULL' if stored is None else str(stored)[:19]}")

    non_null = sum(1 for r in rows if exists and r.get(COLUMN) is not None)
    print(f"\nannual reports: {len(rows)}   with a document date: {non_null}   "
          f"NULL: {len(rows) - non_null}")
    if not args.apply:
        print("\nNo changes written. Re-run with --apply to create the column.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
