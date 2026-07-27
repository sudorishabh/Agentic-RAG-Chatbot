"""One-shot migration: rename legacy catalog table names to their simplified
names (see app.catalog.schema).

    ingest_state            -> documents
    ingest_state_author     -> documents_author
    ingest_state_category   -> documents_theme
    ingest_state_term       -> documents_term
    ingest_state_attachment -> documents_attachment
    taxonomy_term           -> terms
    taxonomy_term_alias     -> term_aliases

The theme facet was previously named ``category``; a deployment already on the
simplified ``documents_category`` name is carried forward to ``documents_theme``
by the extra pair below. Renaming that table is not enough on its own -- the
facet's *value column* is named after the facet too -- so this script also runs
``schema.migrate_renamed_facets``, which renames ``category`` -> ``theme`` in
place. Without it the table arrives under the new name still holding a
``category`` column and every theme query fails on the missing column.

Run once against a deployment that already has data, before/at the same
deploy as the code change -- otherwise the old tables are left behind and
ensure_*_table() just creates empty tables under the new names. Parent and
child tables are renamed together in one RENAME TABLE statement so MySQL
updates the FK metadata the children hold on the parent.

Idempotent; safe to re-run (only renames pairs where the old name still
exists and the new name isn't already taken).

Usage:  python -m scripts.rename_catalog_tables [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("rename_catalog_tables")

_RENAMES: list[tuple[str, str]] = [
    ("ingest_state", "documents"),
    ("ingest_state_author", "documents_author"),
    ("ingest_state_category", "documents_theme"),
    ("ingest_state_term", "documents_term"),
    ("ingest_state_attachment", "documents_attachment"),
    ("taxonomy_term", "terms"),
    ("taxonomy_term_alias", "term_aliases"),
    # Theme facet renamed from ``category``: carry an already-simplified
    # deployment forward to the final name.
    ("documents_category", "documents_theme"),
]


def _existing_tables(cur) -> set[str]:
    cur.execute(
        "SELECT table_name AS name FROM information_schema.tables "
        "WHERE table_schema = DATABASE()"
    )
    return {row["name"] for row in cur.fetchall()}


def rename_tables(dry_run: bool) -> int:
    from app.catalog.db import state_table
    from app.catalog.schema import migrate_renamed_facets
    from app.core.clients import mysql_connection

    verb = "would rename" if dry_run else "renaming"
    with mysql_connection() as conn, conn.cursor() as cur:
        existing = _existing_tables(cur)
        pending = [
            (old, new) for old, new in _RENAMES
            if old in existing and new not in existing
        ]
        for old, new in pending:
            print(f"  {verb} {old} -> {new}")
        if pending and not dry_run:
            clause = ", ".join(f"`{old}` TO `{new}`" for old, new in pending)
            cur.execute(f"RENAME TABLE {clause}")

        # Finish the theme facet: the pairs above move the table, this renames
        # the value column still called `category` inside it.
        facet_stmts = migrate_renamed_facets(cur, state_table(), dry_run=dry_run)
        for stmt in facet_stmts:
            print(f"  {verb} facet column: {stmt}")

        if not pending and not facet_stmts:
            print("Nothing to rename (already renamed, or a fresh install).")
            return 0
        if dry_run:
            return 0
        conn.commit()
    logger.info("Renamed tables: %s; facet columns: %s", pending, facet_stmts)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report which tables would be renamed; change nothing.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    rc = rename_tables(args.dry_run)
    print("Done (dry run)." if args.dry_run else "Done.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
