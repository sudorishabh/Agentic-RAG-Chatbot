"""Populate `documents_tag` from the names already stored in `documents.raw_meta`,
and clear boolean artefacts out of `documents_theme`.

Tags used to live only in `documents_term` as taxonomy UUIDs. That table is
retired (docs/retire-term-tables-plan.md) and tags now have their own facet
table, which ingestion writes going forward — but existing documents would have
no tag rows until they are next re-ingested. The names are already present:
`raw_meta` keeps every source field verbatim, e.g.
``field_tags: ["Solid waste", "Urban waste"]``. So this is a local reshuffle, not
a re-crawl: no network, no Drupal, no re-embedding.

Also deletes theme rows whose value is a stringified boolean ("False"/"True") —
an upstream field leaking into the theme facet. `theme_taxonomy` now rejects
these at ingest; this clears the ones already written.

    python -m scripts.backfill_tag_facet            # report only
    python -m scripts.backfill_tag_facet --apply
"""
from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from app.catalog.db import state_table
from app.catalog.schema import ensure_state_table
from app.core.clients import mysql_connection
from app.ingestion.canonical import TAG_HINTS

logger = logging.getLogger(__name__)

# Matches `theme_taxonomy._NOT_A_THEME` / `queries._NON_THEME_VALUES`, kept in
# SQL-friendly form here.
_NOT_A_THEME = ("False", "True", "None", "null", "nan")


def _tags_from_raw_meta(raw: Any) -> list[str]:
    """Tag names out of one document's raw_meta, using the same field-name hints
    ingestion uses, so a backfilled row matches what a re-ingest would write."""
    if not raw:
        return []
    meta = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    if not isinstance(meta, dict):
        return []
    found: list[str] = []
    for key, value in meta.items():
        if not any(hint in key.lower() for hint in TAG_HINTS):
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            name = str(item or "").strip()
            if name and name not in found:
                found.append(name)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write the changes.")
    args = parser.parse_args(argv)

    if args.apply:
        ensure_state_table()  # creates documents_tag if this is its first run

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, raw_meta FROM `{table}` WHERE raw_meta IS NOT NULL"
        )
        rows = cur.fetchall()

        pending = [
            (row["document_id"], tags)
            for row in rows
            if (tags := _tags_from_raw_meta(row["raw_meta"]))
        ]
        total_links = sum(len(tags) for _, tags in pending)
        distinct = len({t for _, tags in pending for t in tags})
        print(f"documents with raw_meta       : {len(rows)}")
        print(f"documents carrying tags       : {len(pending)}")
        print(f"tag links to write            : {total_links} ({distinct} distinct)")

        placeholders = ", ".join(["%s"] * len(_NOT_A_THEME))
        cur.execute(
            f"SELECT COUNT(*) AS n FROM `{table}_theme` WHERE theme IN ({placeholders})",
            _NOT_A_THEME,
        )
        junk = int(cur.fetchone()["n"])
        print(f"boolean-artefact theme rows    : {junk}")

        if not args.apply:
            print("\nDry run. Re-run with --apply to write.")
            return 0

        for document_id, tags in pending:
            cur.execute(
                f"DELETE FROM `{table}_tag` WHERE document_id = %s", (document_id,)
            )
            cur.executemany(
                f"INSERT INTO `{table}_tag` (document_id, tag) VALUES (%s, %s)",
                [(document_id, tag[:255]) for tag in tags],
            )
        cur.execute(
            f"DELETE FROM `{table}_theme` WHERE theme IN ({placeholders})", _NOT_A_THEME
        )
        conn.commit()
    print(f"\nWrote {total_links} tag links; removed {junk} artefact theme rows.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
