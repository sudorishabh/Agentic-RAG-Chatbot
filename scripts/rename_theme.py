"""Rename a theme across the catalog.

Themes are keyed by **name** (see docs/retire-term-tables-plan.md), so a rename in
the CMS does not propagate on its own: renaming a Drupal taxonomy term does not
bump the referencing nodes' ``changed`` marks, so incremental ingestion never
notices and ``documents_theme`` keeps the old name indefinitely.

**Two steps are needed, and this script is only the first:**

1. ``python -m scripts.rename_theme "Old Name" "New Name" --apply``
2. Edit ``app/data.json`` to use the new name.

Skipping step 2 leaves the new name unclassified, so documents ingested *after*
the rename get ``theme_group = NULL`` and list under "Other themes" instead of
their real bucket. The script warns when it cannot find the new name in the map.

Until the rename is applied, queries degrade rather than break: a name sharing a
word with the old one resolves to a clarification listing the right theme, and a
total rewrite reports an explicit miss. Neither produces a wrong count.

    python -m scripts.rename_theme "Waste" "Waste Management"           # dry run
    python -m scripts.rename_theme "Waste" "Waste Management" --apply
"""
from __future__ import annotations

import argparse
import logging

from app.catalog import theme_taxonomy
from app.catalog.db import state_table
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", help="The theme name as currently stored.")
    parser.add_argument("new", help="The name to store instead.")
    parser.add_argument(
        "--apply", action="store_true", help="Write the change (otherwise dry run)."
    )
    args = parser.parse_args(argv)

    if args.old == args.new:
        print("Old and new names are identical; nothing to do.")
        return 0

    table = f"{state_table()}_theme"
    with mysql_connection() as conn, conn.cursor() as cur:
        # `theme` rows name the theme; `parent` rows name it as a sub-theme's
        # primary tag. Both have to move, or a renamed primary tag orphans its
        # children from the sub-theme expansion (theme = X OR parent = X).
        cur.execute(f"SELECT COUNT(*) AS n FROM `{table}` WHERE theme = %s", (args.old,))
        as_theme = int(cur.fetchone()["n"])
        cur.execute(f"SELECT COUNT(*) AS n FROM `{table}` WHERE parent = %s", (args.old,))
        as_parent = int(cur.fetchone()["n"])

        print(f"{args.old!r} -> {args.new!r}")
        print(f"  rows naming it as a theme      : {as_theme}")
        print(f"  rows naming it as a sub-theme's parent: {as_parent}")

        if not (as_theme or as_parent):
            print("\nNo rows carry that name; check the spelling against list_themes.")
            return 1

        if theme_taxonomy.group_of(args.new) is None:
            print(
                f"\nWARNING: app/data.json does not know {args.new!r}, so newly "
                "ingested documents would get no theme_group and list under "
                "'Other themes'. Update app/data.json as well (step 2)."
            )

        if not args.apply:
            print("\nDry run. Re-run with --apply to write the change.")
            return 0

        cur.execute(
            f"UPDATE `{table}` SET theme = %s WHERE theme = %s", (args.new, args.old)
        )
        cur.execute(
            f"UPDATE `{table}` SET parent = %s WHERE parent = %s", (args.new, args.old)
        )
        conn.commit()
    print(f"\nRenamed. Remember step 2: update app/data.json to use {args.new!r}.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
