"""Record where each existing ``published_at`` came from. Moves no dates.

``published_at_source`` was added without being backfilled, deliberately: writing
``created`` across the board would have been *false* for the four PDFs whose
dates come from a publication statement quoted out of the document itself. So
10,956 rows read NULL — "not recorded" — and the one query worth having is
unanswerable:

    which documents are dated by an import stamp rather than by a statement?

This fills it in, and every value is **derived, not assumed**:

* **Website documents** → ``created``. Provable from the code rather than from
  the value: ``canonical._drupal_document`` is the only place a website date has
  ever been assigned (both ``from_drupal_record`` and ``from_drupal_export``
  route through it), and before ``_published_at_for`` existed that line read
  ``published_at=created``. Rows already stamped ``cms_field`` by
  ``scripts.backfill_source_dates`` are skipped, so what remains is by
  construction the untouched creation stamp.

* **Attachments** → whatever their own decision row says. ``propose_override``
  is granted only for a publication statement quoted from the PDF and verified
  against its text, so those are ``document_text``; every other action kept the
  parent page's stamp, so those are ``created``.

  For an attachment, ``created`` means *the parent page's* creation stamp — the
  attachment has no record of its own. That distinction is not lost: it lives in
  ``{state}_date_decision`` alongside ``page_pdf_count``, which is what says
  whether the page held one document or a shelf of them.

Nothing an answer depends on changes, so unlike the source-date backfill this
touches no Qdrant payload and needs no cache drop. The ``published_at`` checksum
over all 12,003 documents is asserted identical before and after.

    python -m scripts.backfill_date_provenance
    python -m scripts.backfill_date_provenance --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from typing import Any

#: ``(label, description, WHERE clause)`` for each class of row, evaluated
#: against ``documents d`` left-joined to its decision row as ``dd``. Every
#: clause requires ``published_at_source IS NULL``, so an existing value is never
#: overwritten — this script can be re-run safely and is a no-op the second time.
CLASSES: list[tuple[str, str, str, str]] = [
    (
        "created", "day",
        "website documents: the CMS record's own creation stamp",
        "d.source_type = 'website' AND d.published_at_source IS NULL",
    ),
    (
        "document_text", "day",
        "attachments dated from a publication statement quoted in the PDF",
        "d.source_type <> 'website' AND d.published_at_source IS NULL "
        "AND dd.action = 'propose_override'",
    ),
    (
        "created", "day",
        "attachments that kept their parent page's stamp",
        "d.source_type <> 'website' AND d.published_at_source IS NULL "
        "AND dd.document_id IS NOT NULL AND dd.action <> 'propose_override'",
    ),
]


def _counts(cur, table: str, decision: str) -> list[tuple[str, str, str, int]]:
    out = []
    for source, precision, description, clause in CLASSES:
        cur.execute(
            f"SELECT COUNT(*) n FROM `{table}` d "
            f"LEFT JOIN `{decision}` dd ON dd.document_id = d.document_id "
            f"WHERE {clause}"
        )
        out.append((source, precision, description, int(cur.fetchall()[0]["n"])))
    return out


def _undeterminable(cur, table: str, decision: str) -> int:
    """Rows this cannot explain, which are left NULL rather than guessed at."""
    cur.execute(
        f"SELECT COUNT(*) n FROM `{table}` d "
        f"LEFT JOIN `{decision}` dd ON dd.document_id = d.document_id "
        f"WHERE d.published_at_source IS NULL AND d.source_type <> 'website' "
        f"AND dd.document_id IS NULL"
    )
    return int(cur.fetchall()[0]["n"])


def _date_checksum(cur, table: str) -> tuple[str, int]:
    cur.execute(f"SELECT document_id, published_at FROM `{table}` ORDER BY document_id")
    digest = hashlib.sha256()
    rows = 0
    for row in cur.fetchall():
        digest.update(f"{row['document_id']}|{row['published_at']}\n".encode())
        rows += 1
    return digest.hexdigest()[:16], rows


def stale_labels(cur, table: str) -> list[tuple[str, str, str]]:
    """``(document_id, source, precision)`` for rows whose label ingestion disagrees with.

    The classes above are SQL clauses; this one cannot be. Whether the source
    states a publication date depends on a field inside the ``raw_meta`` JSON, on
    an Asia/Kolkata conversion, and on which field the record's **bundle** is
    dated by — so it is decided by calling ``resolve_published_at``, the same
    function ingestion calls, with the same bundle.

    What this catches: a backfill stamps ``cms_field`` only on documents whose
    date it *moved*. Where the bundle's field already agreed with the stored
    value there was nothing to move, so the label was left as ``created`` — while
    ``resolve_published_at`` returns ``cms_field`` for those rows regardless of
    whether the value changes. The stored labels are therefore stale against the
    very next re-crawl, and the documents the publisher corroborates are
    invisible to ``WHERE published_at_source = 'cms_field'``.

    **No date is proposed here.** A row is only reported when the label differs
    and the date does not, so this can be applied under a checksum that forbids
    ``published_at`` moving at all.
    """
    from app.ingestion.source_dates import resolve_published_at

    cur.execute(
        f"SELECT document_id, bundle, raw_meta, published_at, "
        f"published_at_source, published_at_precision FROM `{table}` "
        f"WHERE source_type = 'website' AND raw_meta IS NOT NULL"
    )
    out: list[tuple[str, str, str]] = []
    for row in cur.fetchall():
        try:
            meta = (json.loads(row["raw_meta"]) if isinstance(row["raw_meta"], str)
                    else row["raw_meta"])
        except (TypeError, ValueError):
            continue
        if not isinstance(meta, dict):
            continue
        stored = row["published_at"]
        value, source, precision = resolve_published_at(
            stored.isoformat(), meta, bundle=row["bundle"])
        if source != "cms_field" or not value:
            continue
        if value[:10] != stored.date().isoformat():
            # The date itself disagrees, which is the source-date backfill's job
            # and not a labelling question. Left alone so one script cannot
            # quietly do the other's work.
            continue
        if (row["published_at_source"], row["published_at_precision"]) == (source, precision):
            continue
        out.append((row["document_id"], source, precision))
    return out


def _distribution(cur, table: str) -> dict[str, int]:
    cur.execute(
        f"SELECT COALESCE(published_at_source, '(not recorded)') s, COUNT(*) n "
        f"FROM `{table}` GROUP BY s ORDER BY n DESC"
    )
    return {r["s"]: int(r["n"]) for r in cur.fetchall()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Commit the changes. Omit for a dry run.")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    decision = f"{table}_date_decision"
    mode = "APPLY" if args.apply else "DRY RUN — nothing will be written"
    print(f"=== {mode} ===\n")

    with mysql_connection() as conn, conn.cursor() as cur:
        planned = _counts(cur, table, decision)
        unknown = _undeterminable(cur, table, decision)
        stale = stale_labels(cur, table)
        before_dist = _distribution(cur, table)
        before_sum, before_rows = _date_checksum(cur, table)

        print("provenance recorded now:")
        for source, n in before_dist.items():
            print(f"  {source:18} {n:6}")

        print(f"\nrows this would stamp:")
        total = 0
        for source, precision, description, n in planned:
            print(f"  {source:14} {precision:4} {n:6}  {description}")
            total += n
        print(f"  {'TOTAL':14} {'':4} {total:6}")
        if unknown:
            print(f"\n  {unknown} attachment(s) have no decision row; left NULL "
                  f"rather than guessed at")

        print(f"\nrows whose label disagrees with what ingestion would write: "
              f"{len(stale)}")
        if stale:
            relabels = Counter((s, p) for _d, s, p in stale)
            for (source, precision), n in relabels.most_common():
                print(f"  created  ->  {source:14} {precision:4} {n:6}")
            print("  (the publisher states these dates; the source-date backfill "
                  "left the label alone because it had no date to move)")

        if not args.apply:
            print("\nNo changes written. Re-run with --apply to commit.")
            return 0

        for source, precision, _description, clause in CLASSES:
            cur.execute(
                f"UPDATE `{table}` d "
                f"LEFT JOIN `{decision}` dd ON dd.document_id = d.document_id "
                f"SET d.published_at_source = %s, d.published_at_precision = %s "
                # updated_at is deliberately not moved: no fact about the
                # document changed, only what we recorded about our own
                # knowledge of it.
                f"WHERE {clause}",
                (source, precision),
            )
        if stale:
            cur.executemany(
                f"UPDATE `{table}` SET published_at_source = %s, "
                f"published_at_precision = %s WHERE document_id = %s",
                [(source, precision, doc_id) for doc_id, source, precision in stale],
            )
        conn.commit()

        after_dist = _distribution(cur, table)
        after_sum, after_rows = _date_checksum(cur, table)

    print("\nprovenance recorded after:")
    for source, n in after_dist.items():
        print(f"  {source:18} {n:6}")

    print("\ninvariants (must be identical):")
    ok = True
    for label, before, after in (("documents", before_rows, after_rows),
                                 ("published_at_checksum", before_sum, after_sum)):
        same = before == after
        ok = ok and same
        print(f"  {label:24} {before!s:>18} -> {after!s:<18}"
              + ("OK" if same else "*** CHANGED ***"))
    if not ok:
        print("\nA date moved. That should be impossible here; investigate.")
        return 1
    print("\nNo date moved and no payload was touched, so no cached answer is "
          "stale and the semantic cache is left alone.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
