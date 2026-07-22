"""One-shot migration: rename legacy catalog table names to their simplified
names (see app.catalog.schema).

    ingest_state            -> documents
    ingest_state_author     -> documents_author
    ingest_state_category   -> documents_category
    ingest_state_term       -> documents_term
    ingest_state_attachment -> documents_attachment
    taxonomy_term           -> terms
    taxonomy_term_alias     -> term_aliases

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
    ("ingest_state_category", "documents_category"),
    ("ingest_state_term", "documents_term"),
    ("ingest_state_attachment", "documents_attachment"),
    ("taxonomy_term", "terms"),
    ("taxonomy_term_alias", "term_aliases"),
]


def _existing_tables(cur) -> set[str]:
    cur.execute(
        "SELECT table_name AS name FROM information_schema.tables "
        "WHERE table_schema = DATABASE()"
    )
    return {row["name"] for row in cur.fetchall()}


def rename_tables(dry_run: bool) -> int:
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        existing = _existing_tables(cur)
        pending = [
            (old, new) for old, new in _RENAMES
            if old in existing and new not in existing
        ]
        if not pending:
            print("Nothing to rename (already renamed, or a fresh install).")
            return 0
        for old, new in pending:
            print(f"  {'would rename' if dry_run else 'renaming'} {old} -> {new}")
        if dry_run:
            return 0
        clause = ", ".join(f"`{old}` TO `{new}`" for old, new in pending)
        cur.execute(f"RENAME TABLE {clause}")
        conn.commit()
    logger.info("Renamed: %s", pending)
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
