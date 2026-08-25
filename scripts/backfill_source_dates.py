"""Apply the publication dates the source states. Dry run first.

``published_at`` for a website document has only ever been the CMS record's
*creation* stamp, which is why 3,409 documents sit inside the Dec 2017 - Jan 2018
import window sharing 85 timestamps. The CMS separately states when many of
those were published, and this applies that statement — the same value the site
itself displays, verified against the rendered pages 40 times over.

What it does **not** touch, by construction:

* **PDFs.** Their dates come from ``app.ingestion.date_resolution`` and are
  correct by that design; a PDF date moving here would be a bug, so the run
  fails if the PDF date checksum changes.
* **Event and project-period dates.** ~5,500 values that look like a fix and
  describe when the work ran or the conference happened, not when the document
  was published. ``app.ingestion.source_dates`` is what keeps them out.
* **Year-precision sources.** 617 research papers state a year; 228 already sit
  in the right year with a real timestamp, so rewriting them to 1 January would
  lose precision for nothing. Gated behind ``ACTIONABLE_PRECISIONS``.

Nothing is re-extracted, re-chunked or re-embedded: a date is metadata, so the
correction is an ``UPDATE`` plus a ``set_payload``. No ``PIPELINE_VERSION`` bump,
because no payload *key* changes — only the value of one that already exists.

    python -m scripts.backfill_source_dates                 # show the diff
    python -m scripts.backfill_source_dates --limit 20       # scoped trial
    python -m scripts.backfill_source_dates --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.ingestion.source_dates import publication_date, resolve_published_at

#: What a reviewed dry run showed. The run refuses to apply if the corpus has
#: drifted since, rather than silently rewriting a different set.
EXPECTED_MOVES = 1047


@dataclass(frozen=True)
class Move:
    """One document's date correction."""

    document_id: str
    bundle: str | None
    url: str | None
    created: str
    new_value: str
    field: str
    precision: str

    @property
    def days(self) -> int:
        """How many days too late the stored date was. Negative = too early."""
        old = datetime.fromisoformat(self.created[:19]).date()
        new = datetime.fromisoformat(self.new_value[:19]).date()
        return (old - new).days


def _metadata(raw: Any) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def candidates() -> list[Move]:
    """Website documents whose source states a different publication date.

    Scoped to ``source_type='website'`` in the query itself rather than filtered
    afterwards, so a PDF cannot reach the write path even if the classifier were
    to change.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, bundle, url, raw_meta, published_at "
            f"FROM `{state_table()}` "
            f"WHERE source_type = 'website' AND raw_meta IS NOT NULL "
            # Ordered so `--limit` selects the same subset every run. Without it
            # a scoped trial cannot be verified: the rows inspected beforehand
            # would not be the rows written.
            f"ORDER BY document_id"
        )
        rows = list(cur.fetchall())

    moves: list[Move] = []
    for row in rows:
        metadata = _metadata(row["raw_meta"])
        created = row["published_at"].isoformat()
        # The same single decision ingestion makes, so a document re-crawled
        # after this runs keeps the date the backfill gave it.
        new_value, source, precision = resolve_published_at(created, metadata)
        if source != "cms_field" or not new_value or new_value[:10] == created[:10]:
            continue
        stated = publication_date(metadata)
        moves.append(Move(
            document_id=row["document_id"], bundle=row["bundle"], url=row["url"],
            created=created, new_value=new_value,
            field=stated.field if stated else "", precision=precision,
        ))
    return moves


def invariants() -> dict[str, Any]:
    """Everything this run must leave alone, in a form that can be compared.

    The PDF checksum is the important one: PDFs are out of scope, and a change
    there means the scoping failed.
    """
    from app.catalog.db import state_table
    from app.config import get_settings
    from app.core.clients import get_qdrant_client, mysql_connection

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) n FROM `{table}`")
        documents = int(cur.fetchall()[0]["n"])
        cur.execute(
            f"SELECT document_id, published_at FROM `{table}` "
            f"WHERE source_type <> 'website' ORDER BY document_id"
        )
        digest = hashlib.sha256()
        pdfs = 0
        for row in cur.fetchall():
            digest.update(f"{row['document_id']}|{row['published_at']}\n".encode())
            pdfs += 1
        cur.execute(f"SELECT COUNT(*) n FROM `{table}` WHERE published_at IS NULL")
        undated = int(cur.fetchall()[0]["n"])

    points = None
    try:
        client = get_qdrant_client()
        collection = get_settings().qdrant_collection
        if client.collection_exists(collection):
            points = client.count(collection_name=collection, exact=True).count
    except Exception:
        points = "unreadable"

    return {
        "documents": documents,
        "non_website_documents": pdfs,
        "non_website_date_checksum": digest.hexdigest()[:16],
        "documents_without_a_date": undated,
        "qdrant_points": points,
    }


def preflight(moves: list[Move], *, expect: int) -> list[str]:
    """Reasons to refuse, computed before the first write.

    Encodes what the reviewed dry run showed. A corpus that has drifted since
    then stops the run rather than having a different set rewritten silently.
    """
    problems: list[str] = []
    if expect >= 0 and len(moves) != expect:
        problems.append(
            f"{len(moves)} documents would move, expected {expect}. Re-review the "
            f"dry run and pass --expect if the corpus has legitimately changed."
        )
    fields = {m.field for m in moves}
    from app.ingestion.source_dates import FIELD_KINDS

    for field in sorted(fields):
        kind, _ = FIELD_KINDS.get(field, ("unknown", "day"))
        if kind != "publication":
            problems.append(f"{field} is classified {kind!r}, not a publication date")
    from app.ingestion.source_dates import ACTIONABLE_PRECISIONS

    stray = {m.precision for m in moves} - ACTIONABLE_PRECISIONS
    if stray:
        problems.append(f"precision(s) {sorted(stray)} are not actionable")
    # A year-precision value is stored as 1 January *as a marker for the year*.
    # Any other day would mean the value and its precision disagree about what
    # is known, which is the thing `year_precision_not_january` watches for.
    off_january = [m for m in moves
                   if m.precision == "year" and not m.new_value.startswith(
                       m.new_value[:4] + "-01-01")]
    if off_january:
        problems.append(
            f"{len(off_january)} year-precision value(s) are not 1 January")
    if any(not m.new_value.endswith("+00:00") for m in moves):
        problems.append("a value is not stored as UTC; the calendar date would shift")
    return problems


def apply(moves: list[Move], *, progress_every: int = 200) -> dict[str, int]:
    """Write the corrections to MySQL and Qdrant, and record why.

    Both stores, in that order. MySQL alone would be reverted the next time
    anyone ran ``app.ingestion.backfill`` — it lifts ``published_at`` out of the
    chunk payloads and writes it back with a bare SET.
    """
    from qdrant_client import models as qm

    from app.catalog import date_decisions
    from app.catalog.db import state_table
    from app.config import get_settings
    from app.core.clients import get_qdrant_client, mysql_connection

    table = state_table()
    client = get_qdrant_client()
    collection = get_settings().qdrant_collection
    tally = Counter()

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"UPDATE `{table}` SET published_at = %s, published_at_source = 'cms_field', "
            f"published_at_precision = %s, updated_at = NOW() WHERE document_id = %s",
            # updated_at moves; indexed_at deliberately does not. That column
            # means "was re-chunked and re-indexed", which has not happened —
            # and `corpus_revision` reads MAX(indexed_at), so claiming it here
            # would be both false and a silent cache invalidation.
            [(m.new_value[:19].replace("T", " "), m.precision, m.document_id)
             for m in moves],
        )
        tally["mysql_rows"] = cur.rowcount
        conn.commit()

    for index, move in enumerate(moves, start=1):
        # Precision goes with the value, not after it. A year-precision date is
        # 1 January standing in for a year, and the payload is the only place the
        # answer layer can learn that — set the date alone and the model reports
        # a January publication nobody stated. Written only for "year", so a
        # full-date document adds no key and old points stay valid.
        payload: dict[str, Any] = {"published_at": move.new_value}
        if move.precision == "year":
            payload["published_at_precision"] = "year"
        client.set_payload(
            collection_name=collection,
            payload=payload,
            points=qm.Filter(must=[qm.FieldCondition(
                key="document_id", match=qm.MatchValue(value=move.document_id))]),
        )
        tally["payloads_set"] += 1
        if index % progress_every == 0:
            print(f"    payloads rewritten: {index}/{len(moves)}")

    date_decisions.ensure_table()
    for move in moves:
        row = date_decisions.from_source_record(
            document_id=move.document_id, bundle=move.bundle, url=move.url,
            created=move.created, applied=move.new_value,
            stated=publication_date({move.field: move.new_value}),
        )
        if row is not None:
            date_decisions.record(row)
            tally["decisions_recorded"] += 1
    return dict(tally)


def clear_answer_cache() -> str:
    """Drop the semantic cache so pre-correction answers stop being served.

    Necessary because the cache's partition key is
    ``retrieval settings + top_k + answer_format + corpus revision``, and the
    corpus revision is ``MAX(indexed_at) + COUNT(*)`` — neither of which a date
    correction moves. Without this, a question asked in the previous 24 hours
    replays its old answer, with the old date, and the lookup happens *before*
    retrieval so nothing about the fix is consulted.

    Dropping rather than emptying: ``semantic_cache._ensure_collection``
    recreates it, with its payload index, on the next store.
    """
    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    name = get_settings().semantic_cache_collection
    try:
        client = get_qdrant_client()
        if not client.collection_exists(name):
            return "already absent"
        count = client.count(collection_name=name, exact=True).count
        client.delete_collection(name)
        return f"dropped ({count} cached answers)"
    except Exception as exc:
        return f"FAILED ({type(exc).__name__}) — clear it manually or wait out the TTL"


def report(moves: list[Move]) -> None:
    print(f"documents whose date would change: {len(moves)}\n")
    by_bundle = Counter(m.bundle for m in moves)
    by_field = Counter(m.field for m in moves)
    print(f"  {'bundle':24} {'documents':>9}")
    for bundle, n in by_bundle.most_common():
        print(f"  {str(bundle):24} {n:9}")
    print(f"\n  {'source field':28} {'documents':>9}")
    for field, n in by_field.most_common():
        print(f"  {field:28} {n:9}")

    later = [m for m in moves if m.days < 0]
    print(f"\n  direction: {len(moves) - len(later)} earlier, {len(later)} later")
    buckets = Counter()
    for move in moves:
        gap = abs(move.days)
        buckets["1 day" if gap == 1 else
                "2-7 days" if gap <= 7 else
                "8-30 days" if gap <= 30 else
                "1-6 months" if gap <= 183 else
                "6-12 months" if gap <= 365 else
                "1-3 years" if gap <= 1095 else "over 3 years"] += 1
    print(f"\n  {'shift':16} {'documents':>9}")
    for label in ("1 day", "2-7 days", "8-30 days", "1-6 months", "6-12 months",
                  "1-3 years", "over 3 years"):
        if buckets[label]:
            print(f"  {label:16} {buckets[label]:9}")

    if later:
        print(f"\n  every document moving LATER ({len(later)}) — worth eyeballing:")
        for move in sorted(later, key=lambda m: m.days):
            print(f"    {move.created[:10]} -> {move.new_value[:10]} "
                  f"({-move.days:+d}d) {str(move.url)[-52:]}")

    print("\n  largest corrections:")
    for move in sorted(moves, key=lambda m: -m.days)[:8]:
        print(f"    {move.created[:10]} -> {move.new_value[:10]} "
              f"(-{move.days}d) [{move.bundle}] {str(move.url)[-46:]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Commit the changes. Omit for a dry run.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Apply only the first N moves (a scoped trial).")
    parser.add_argument("--expect", type=int, default=EXPECTED_MOVES,
                        help="Refuse to apply unless this many documents move. "
                             "-1 disables the check.")
    parser.add_argument("--keep-cache", action="store_true",
                        help="Do not drop the semantic cache. Old answers will "
                             "then be served for up to its TTL.")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    moves = candidates()
    mode = "APPLY" if args.apply else "DRY RUN — nothing will be written"
    print(f"=== {mode} ===\n")
    report(moves)

    if not args.apply:
        print("\nNo changes written. Re-run with --apply to commit.")
        return 0

    problems = preflight(moves, expect=args.expect)
    if problems:
        print("\nREFUSING TO APPLY:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    precisions = ", ".join(sorted({m.precision for m in moves})) or "none"
    print(f"\npre-flight OK: {len(moves)} documents, all website, all "
          f"publication-kind, precision {precisions}, all UTC, "
          f"year values all 1 January")

    selected = moves[:args.limit] if args.limit else moves
    if args.limit:
        print(f"--limit {args.limit}: applying {len(selected)} of {len(moves)}")

    before = invariants()
    tally = apply(selected)
    after = invariants()

    print(f"\napplied: {tally}")
    print("\ninvariants (must be identical):")
    ok = True
    for key in before:
        same = before[key] == after[key]
        ok = ok and same
        print(f"  {key:30} {before[key]!s:>20} -> {after[key]!s:<20}"
              + ("OK" if same else "*** CHANGED ***"))
    if not ok:
        print("\nAn invariant moved. Investigate before trusting this run.")
        return 1

    if args.keep_cache:
        print("\nsemantic cache: left alone (--keep-cache); old answers may "
              "still be served")
    else:
        print(f"\nsemantic cache: {clear_answer_cache()}")
    print("\nRe-run `python -m scripts.audit_dates --compare <baseline>` to "
          "measure the change.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
