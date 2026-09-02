"""Re-date the corpus from the bundle -> date-field mapping. Dry run first.

Changing ingestion code does not re-date anything already ingested. A sweep that
finds a document unchanged returns before the document is even rebuilt
(``pipeline._handle``), so an existing row keeps whatever date the old rule gave
it until something rewrites it. This is that something.

Two passes, in order, because the second depends on the first:

1. **Pages.** Re-resolve every ``website`` document from its stored ``bundle``
   and ``raw_meta`` through :func:`app.ingestion.bundle_dates.resolve` — the same
   function ingestion calls, so a document re-crawled after this runs keeps the
   date this gave it.
2. **Attachments.** Every ``pdf_attachment`` takes its parent page's new date and
   precision. Not re-derived per file: the parent's resolution is the answer, and
   the link table is what says which files hang off which page.

Nothing is re-extracted, re-chunked or re-embedded: a date is metadata, so the
correction is an ``UPDATE`` plus a ``set_payload``. No ``PIPELINE_VERSION`` bump,
because no payload *key* changes — only the value of keys that already exist. The
content hash is untouched, so the next ordinary sweep does not re-index the
corpus.

    python -m scripts.backfill_bundle_dates                  # show the diff
    python -m scripts.backfill_bundle_dates --limit 20       # scoped trial
    python -m scripts.backfill_bundle_dates --apply
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

from app.ingestion.bundle_dates import BUNDLE_DATE_FIELDS, EffectiveDate, resolve


@dataclass(frozen=True)
class Move:
    """One document's date correction."""

    document_id: str
    source_type: str
    bundle: str | None
    url: str | None
    old_value: str
    new_value: str
    precision: str
    source: str
    rule: str
    field: str | None
    #: The page this attachment inherited from. None for a page.
    parent_id: str | None = None

    @property
    def days(self) -> int:
        """How many days too late the stored date was. Negative = too early."""
        old = datetime.fromisoformat(self.old_value[:19]).date()
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


def _iso(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


def created_stamps() -> dict[str, str]:
    """Each website document's *original* creation stamp, where it is recoverable.

    Needed because ``documents.published_at`` is no longer necessarily the
    creation stamp: a previous run of ``scripts.backfill_source_dates`` moved
    ~1,000 rows onto a CMS field, and ``raw_meta`` does not carry ``created`` (the
    extractor keeps only ``field_*`` attributes).

    Two recoverable cases, and one that is not:

    * ``published_at_source`` is ``created`` or NULL — the stored value *is* the
      creation stamp, which is what that label means.
    * a ``{state}_date_decision`` row exists — its ``current_published_at`` is
      the creation stamp, recorded there by the write path that moved the row.
    * neither — the original is genuinely lost, and this run reports the document
      rather than guessing. Re-ingesting it restores the stamp.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    stamps: dict[str, str] = {}
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, published_at, published_at_source "
            f"FROM `{table}` WHERE source_type = 'website'"
        )
        for row in cur.fetchall():
            if row["published_at_source"] in (None, "", "created"):
                stamp = _iso(row["published_at"])
                if stamp:
                    stamps[row["document_id"]] = stamp
        try:
            cur.execute(
                f"SELECT document_id, current_published_at "
                f"FROM `{table}_date_decision` WHERE origin = 'website'"
            )
            for row in cur.fetchall():
                stamp = _iso(row["current_published_at"])
                if stamp:
                    # Wins over the inference above: it is a recorded fact rather
                    # than a deduction from a label.
                    stamps[row["document_id"]] = stamp
        except Exception:
            # The table may not exist on a deployment that never ran the
            # resolver. The first branch still covers every unmoved row.
            pass
    return stamps


def page_moves() -> tuple[list[Move], dict[str, EffectiveDate], list[str]]:
    """``(moves, resolution per page, documents whose creation stamp is lost)``.

    The resolution map is returned whole — not just the moves — because an
    attachment inherits its parent's date whether or not that date *changed*.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    stamps = created_stamps()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, bundle, url, raw_meta, published_at, "
            f"       published_at_precision "
            f"FROM `{state_table()}` "
            f"WHERE source_type = 'website' "
            # Ordered so `--limit` selects the same subset every run. Without it
            # a scoped trial cannot be verified: the rows inspected beforehand
            # would not be the rows written.
            f"ORDER BY document_id"
        )
        rows = list(cur.fetchall())

    moves: list[Move] = []
    resolutions: dict[str, EffectiveDate] = {}
    unrecoverable: list[str] = []
    for row in rows:
        document_id = row["document_id"]
        stored = _iso(row["published_at"])
        created = stamps.get(document_id)
        if created is None and stored is not None:
            unrecoverable.append(document_id)
            continue
        # The same single decision ingestion makes, from the metadata rather than
        # from the current value — so the run is idempotent and cannot compound.
        resolved = resolve(row["bundle"], created, _metadata(row["raw_meta"]))
        resolutions[document_id] = resolved
        if not resolved.value or not stored:
            continue
        if (resolved.value[:10] == stored[:10]
                and resolved.precision == (row["published_at_precision"] or "day")):
            continue
        moves.append(Move(
            document_id=document_id, source_type="website", bundle=row["bundle"],
            url=row["url"], old_value=stored, new_value=resolved.value,
            precision=resolved.precision, source=resolved.source,
            rule=resolved.rule, field=resolved.field,
        ))
    return moves, resolutions, unrecoverable


def attachment_moves(resolutions: dict[str, EffectiveDate]) -> list[Move]:
    """Every attached file that does not currently carry its page's date.

    An attachment reached from more than one page — 84 of them are — takes the
    first parent by document id, deterministically, which is the same rule the
    crawl's per-run dedup applies.

    A document whose date came from a verified publication statement inside its
    own text (``published_at_source = 'document_text'``) is left alone: that is
    the one override the design grants, and it outranks inheritance.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT a.document_id AS parent_id, a.file_uuid AS document_id, "
            f"       d.published_at, d.published_at_precision, "
            f"       d.published_at_source, d.url, d.bundle "
            f"FROM `{table}_attachment` a "
            f"JOIN `{table}` d ON d.document_id = a.file_uuid "
            f"WHERE d.source_type = 'pdf_attachment' "
            f"ORDER BY a.file_uuid, a.document_id"
        )
        rows = list(cur.fetchall())

    seen: set[str] = set()
    moves: list[Move] = []
    for row in rows:
        document_id = row["document_id"]
        if document_id in seen:
            continue
        seen.add(document_id)
        if row["published_at_source"] == "document_text":
            continue
        parent = resolutions.get(row["parent_id"])
        if parent is None or not parent.value:
            continue
        stored = _iso(row["published_at"])
        if (stored and parent.value[:10] == stored[:10]
                and parent.precision == (row["published_at_precision"] or "day")):
            continue
        moves.append(Move(
            document_id=document_id, source_type="pdf_attachment",
            bundle=parent.bundle or row["bundle"], url=row["url"],
            old_value=stored or "", new_value=parent.value,
            precision=parent.precision, source="parent_page",
            rule="inherited_from_parent", field=parent.field,
            parent_id=row["parent_id"],
        ))
    return moves


def invariants() -> dict[str, Any]:
    """Everything this run must leave alone, in a form that can be compared.

    The content-hash checksum is the important one: this run is metadata-only,
    and a change there means something re-chunked the corpus.
    """
    from app.catalog.db import state_table
    from app.config import get_settings
    from app.core.clients import get_qdrant_client, mysql_connection

    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) n FROM `{table}`")
        documents = int(cur.fetchall()[0]["n"])
        cur.execute(
            f"SELECT document_id, content_hash, doc_version FROM `{table}` "
            f"ORDER BY document_id"
        )
        digest = hashlib.sha256()
        for row in cur.fetchall():
            digest.update(
                f"{row['document_id']}|{row['content_hash']}|{row['doc_version']}\n"
                .encode())
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
        "content_checksum": digest.hexdigest()[:16],
        "documents_without_a_date": undated,
        "qdrant_points": points,
    }


def preflight(moves: list[Move], *, expect: int) -> list[str]:
    """Reasons to refuse, computed before the first write."""
    problems: list[str] = []
    if expect >= 0 and len(moves) != expect:
        problems.append(
            f"{len(moves)} documents would move, expected {expect}. Re-review the "
            f"dry run and pass --expect if the corpus has legitimately changed."
        )
    mapped = {f.field for f in BUNDLE_DATE_FIELDS.values()}
    stray = {m.field for m in moves} - mapped - {None}
    if stray:
        problems.append(f"field(s) {sorted(stray)} are not in the bundle mapping")
    stray_sources = {m.source for m in moves} - {"created", "cms_field", "parent_page"}
    if stray_sources:
        problems.append(f"unexpected provenance {sorted(stray_sources)}")
    # A year-precision value is stored as 1 January *as a marker for the year*.
    # Any other day would mean the value and its precision disagree about what is
    # known, which is what `year_precision_not_january` watches for.
    off_january = [m for m in moves
                   if m.precision == "year"
                   and not m.new_value.startswith(m.new_value[:4] + "-01-01")]
    if off_january:
        problems.append(
            f"{len(off_january)} year-precision value(s) are not 1 January")
    if any(not m.new_value.endswith("+00:00") and "+" not in m.new_value[10:]
           for m in moves):
        problems.append("a value carries no timezone; the calendar date would shift")
    return problems


def apply(moves: list[Move], *, progress_every: int = 200) -> dict[str, int]:
    """Write the corrections to MySQL and Qdrant, and record why.

    Both stores, in that order. MySQL alone would be reverted the next time
    anyone ran ``app.ingestion.backfill`` — it lifts ``published_at`` out of the
    chunk payloads and writes it back with a bare SET.
    """
    from qdrant_client import models as qm

    from app.catalog.db import state_table
    from app.config import get_settings
    from app.core.clients import get_qdrant_client, mysql_connection

    table = state_table()
    client = get_qdrant_client()
    collection = get_settings().qdrant_collection
    tally: Counter = Counter()

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"UPDATE `{table}` SET published_at = %s, published_at_source = %s, "
            f"published_at_precision = %s, updated_at = NOW() "
            f"WHERE document_id = %s",
            # updated_at moves; indexed_at deliberately does not. That column
            # means "was re-chunked and re-indexed", which has not happened —
            # and `corpus_revision` reads MAX(indexed_at), so claiming it here
            # would be both false and a silent cache invalidation.
            [(m.new_value[:19].replace("T", " "), m.source, m.precision,
              m.document_id) for m in moves],
        )
        tally["mysql_rows"] = cur.rowcount
        conn.commit()

    for index, move in enumerate(moves, start=1):
        # Precision goes with the value, not after it. A year-precision date is
        # 1 January standing in for a year, and the payload is the only place the
        # answer layer can learn that — set the date alone and the model reports
        # a January publication nobody stated. Written only for "year", and
        # explicitly cleared otherwise: a document that *was* year-precision and
        # is no longer would keep a stale marker.
        payload: dict[str, Any] = {
            "published_at": move.new_value,
            "published_at_precision": ("year" if move.precision == "year" else None),
        }
        selector = qm.Filter(must=[qm.FieldCondition(
            key="document_id", match=qm.MatchValue(value=move.document_id))])
        client.set_payload(collection_name=collection,
                           payload={k: v for k, v in payload.items()
                                    if v is not None},
                           points=selector)
        if move.precision != "year":
            client.delete_payload(collection_name=collection,
                                  keys=["published_at_precision"],
                                  points=selector)
        tally["payloads_set"] += 1
        if index % progress_every == 0:
            print(f"    payloads rewritten: {index}/{len(moves)}")

    return dict(tally)


def record_decisions(
    resolutions: dict[str, EffectiveDate], urls: dict[str, str | None]
) -> int:
    """Rewrite the audit rows so the review queue matches the applied dates."""
    from app.catalog import date_decisions

    date_decisions.ensure_table()
    written = 0
    for document_id, resolved in resolutions.items():
        row = date_decisions.from_effective_date(
            document_id=document_id, url=urls.get(document_id),
            # `created` is only used to decide whether the field moved the date;
            # the value written is the resolution itself.
            created=(resolved.value if resolved.source == "created" else None),
            resolved=resolved,
        )
        if row is not None:
            date_decisions.record(row)
            written += 1
    return written


def clear_answer_cache() -> str:
    """Drop the semantic cache so pre-correction answers stop being served.

    Necessary because the cache's partition key is
    ``retrieval settings + top_k + answer_format + corpus revision``, and the
    corpus revision is ``MAX(indexed_at) + COUNT(*)`` — neither of which a date
    correction moves. Without this, a question asked in the previous 24 hours
    replays its old answer, with the old date, and the lookup happens *before*
    retrieval so nothing about the fix is consulted.
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


def report(moves: list[Move], unrecoverable: list[str]) -> None:
    pages = [m for m in moves if m.source_type == "website"]
    files = [m for m in moves if m.source_type == "pdf_attachment"]
    print(f"documents whose date would change: {len(moves)} "
          f"({len(pages)} pages, {len(files)} attachments)\n")

    print(f"  {'bundle':24} {'pages':>7} {'files':>7}")
    by_bundle: Counter = Counter(m.bundle for m in pages)
    file_bundle: Counter = Counter(m.bundle for m in files)
    for bundle, _ in (by_bundle + file_bundle).most_common():
        print(f"  {str(bundle):24} {by_bundle[bundle]:7} {file_bundle[bundle]:7}")

    print(f"\n  {'source field':30} {'documents':>9}")
    for field, n in Counter(m.field for m in moves).most_common():
        print(f"  {str(field):30} {n:9}")

    print(f"\n  {'rule':30} {'documents':>9}")
    for rule, n in Counter(m.rule for m in moves).most_common():
        print(f"  {rule:30} {n:9}")

    dated = [m for m in moves if m.old_value]
    later = [m for m in dated if m.days < 0]
    print(f"\n  direction: {len(dated) - len(later)} earlier, {len(later)} later")
    buckets: Counter = Counter()
    for move in dated:
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

    print("\n  largest corrections:")
    for move in sorted(dated, key=lambda m: -abs(m.days))[:10]:
        print(f"    {move.old_value[:10]} -> {move.new_value[:10]} "
              f"({-move.days:+d}d) [{move.bundle}] {str(move.url)[-46:]}")

    if unrecoverable:
        print(f"\n  {len(unrecoverable)} document(s) whose original creation stamp "
              f"is not recoverable from the catalogue and were skipped. Re-ingest "
              f"them to restore it; the first few:")
        for document_id in unrecoverable[:10]:
            print(f"    {document_id}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Commit the changes. Omit for a dry run.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Apply only the first N moves (a scoped trial).")
    parser.add_argument("--expect", type=int, default=-1,
                        help="Refuse to apply unless this many documents move. "
                             "-1 (the default) disables the check; set it to what "
                             "a reviewed dry run showed.")
    parser.add_argument("--pages-only", action="store_true",
                        help="Skip the attachment pass.")
    parser.add_argument("--keep-cache", action="store_true",
                        help="Do not drop the semantic cache. Old answers will "
                             "then be served for up to its TTL.")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    pages, resolutions, unrecoverable = page_moves()
    files = [] if args.pages_only else attachment_moves(resolutions)
    moves = pages + files

    mode = "APPLY" if args.apply else "DRY RUN — nothing will be written"
    print(f"=== {mode} ===\n")
    report(moves, unrecoverable)

    if not args.apply:
        print("\nNo changes written. Re-run with --apply to commit.")
        return 0

    problems = preflight(moves, expect=args.expect)
    if problems:
        print("\nREFUSING TO APPLY:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"\npre-flight OK: {len(moves)} documents, every field in the bundle "
          f"mapping, year values all 1 January")

    selected = moves[:args.limit] if args.limit else moves
    if args.limit:
        print(f"--limit {args.limit}: applying {len(selected)} of {len(moves)}")

    before = invariants()
    tally = apply(selected)
    urls = {m.document_id: m.url for m in pages}
    tally["decisions_recorded"] = record_decisions(
        {k: v for k, v in resolutions.items()
         if not args.limit or k in {m.document_id for m in selected}},
        urls,
    )
    after = invariants()

    print(f"\napplied: {tally}")
    print("\ninvariants (must be identical):")
    ok = True
    for key in before:
        if key == "documents_without_a_date":
            continue
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
