"""One-shot migration: classify theme rows that predate the theme hierarchy.

``documents_theme`` used to be a flat (document, theme) list.
``app.catalog.schema.migrate_theme_hierarchy`` adds the ``theme_type``,
``parent``, and ``theme_group`` columns, but existing rows can only take the
column defaults — an unparented sub-theme with no group. This re-applies the
theme map (:mod:`app.catalog.theme_taxonomy`, backed by ``app/data.json``) to
those rows so main themes become primary tags, sub-themes point at their
parent, and every row is tagged with the Main Themes / Other Themes bucket
it traces back to.

Also deletes rows whose value is not a theme at all — the grouping-bucket names
("Main Themes" / "Other Themes") and blanks — which the flat facet had no way to
exclude.

Run once against a deployment that already has data, any time after the schema
migration (which any ingestion run applies). Not needed on a fresh install, and
not needed at all if you are going to reindex the corpus anyway: every document's
next ingest rewrites its rows classified.

Idempotent; safe to re-run (a second run reports 0 updated).

Usage:  python -m scripts.reclassify_theme_rows [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger("reclassify_theme_rows")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many rows each name covers; change nothing.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from app.catalog import state

    state.ensure_table()  # make sure the hierarchy columns are there first
    tally = state.reclassify_theme_rows(dry_run=args.dry_run)

    verb = "would reclassify" if args.dry_run else "reclassified"
    print(f"\n{tally['names']} distinct theme names seen.")
    print(f"  {verb}: {tally['updated']} row(s)")
    print(f"  {'would delete' if args.dry_run else 'deleted'}: {tally['deleted']} row(s)")
    if args.dry_run:
        print("\n(dry run: counts are rows matching each name, not rows that change)")
    print("Done (dry run)." if args.dry_run else "Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
