"""Report the blast radius of the proposed attachment-date correction.

Reads the shadow table filled during ingestion (Phase 0) and answers the only
question that matters before anything is applied: how many documents would move,
by how much, and under which rule — with examples to eyeball.

    python -m scripts.report_date_candidates
    python -m scripts.report_date_candidates --examples 20 --rule migration_era
    python -m scripts.report_date_candidates --csv moves.csv

Nothing here writes. Run a Drupal sweep first to populate the table.
"""
from __future__ import annotations

import argparse
import csv
import logging
from collections import Counter
from datetime import datetime, timezone

from app.catalog import date_shadow

logger = logging.getLogger(__name__)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _bar(count: int, total: int, width: int = 40) -> str:
    return "#" * int(width * count / total) if total else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--examples", type=int, default=10,
                        help="Example rows to print per rule (default: 10).")
    parser.add_argument("--rule", help="Only report this rule.")
    parser.add_argument("--csv", help="Write every would-move row to this CSV.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    try:
        rows = date_shadow.load()
    except Exception:
        logger.exception(
            "Could not read the date-candidate table. Run a Drupal sweep with "
            "date_shadow_enabled first."
        )
        return 1

    if not rows:
        print("No measurements recorded yet. Run a Drupal ingestion sweep "
              "(app.ingestion.pipeline.ingest_drupal) with date_shadow_enabled=True.")
        return 0

    if args.rule:
        rows = [r for r in rows if r.rule == args.rule]

    total = len(rows)
    moves = [r for r in rows if r.would_move]

    print(f"\n{'=' * 72}\nDATE CANDIDATE SHADOW REPORT — {total} attachments measured\n{'=' * 72}")
    print(f"\nwould move : {len(moves)} ({100 * len(moves) / total:.1f}%)")
    print(f"unchanged  : {total - len(moves)} ({100 * (total - len(moves)) / total:.1f}%)")

    print("\n--- by rule ---")
    for rule, n in Counter(r.rule for r in rows).most_common():
        print(f"  {rule:<18} {n:>6}  {_bar(n, total)}")

    print("\n--- by proposed source ---")
    for src, n in Counter(r.source for r in rows).most_common():
        print(f"  {src:<18} {n:>6}  {_bar(n, total)}")

    print("\n--- by origin ---")
    for origin in sorted({r.origin for r in rows}):
        sub = [r for r in rows if r.origin == origin]
        mv = sum(1 for r in sub if r.would_move)
        print(f"  {origin:<18} {len(sub):>6} measured, {mv} would move "
              f"({100 * mv / len(sub):.1f}%)")

    print("\n--- candidate availability ---")
    for label, attr in (("node.created", "node_created"), ("file.created", "file_created"),
                        ("pdf CreationDate", "pdf_created")):
        n = sum(1 for r in rows if getattr(r, attr))
        print(f"  {label:<18} {n:>6}/{total}  ({100 * n / total:.1f}%)")

    print("\n--- magnitude of the move ---")
    buckets: Counter[str] = Counter()
    for r in moves:
        cur, prop = _parse(r.current), _parse(r.proposed)
        if not (cur and prop):
            buckets["unparseable"] += 1
            continue
        years = abs((prop - cur).days) / 365.25
        buckets["< 1 year" if years < 1 else
                "1-2 years" if years < 2 else
                "2-5 years" if years < 5 else
                "5-10 years" if years < 10 else "> 10 years"] += 1
    for label in ("< 1 year", "1-2 years", "2-5 years", "5-10 years", "> 10 years",
                  "unparseable"):
        if buckets[label]:
            print(f"  {label:<14} {buckets[label]:>6}  {_bar(buckets[label], len(moves))}")

    earlier = sum(1 for r in moves
                  if (_parse(r.proposed) and _parse(r.current)
                      and _parse(r.proposed) < _parse(r.current)))
    print(f"\n  moves EARLIER : {earlier}   (migration-era correction)")
    print(f"  moves LATER   : {len(moves) - earlier}   (late-upload correction)")

    for rule in sorted({r.rule for r in moves}):
        sub = [r for r in moves if r.rule == rule][: args.examples]
        if not sub:
            continue
        print(f"\n--- examples: {rule} ---")
        for r in sub:
            print(f"  {str(r.current)[:10]} -> {str(r.proposed)[:10]}  "
                  f"[{r.source}] {(r.filename or r.url or r.document_id)[:52]}")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["document_id", "origin", "rule", "source", "current",
                             "proposed", "delta_days", "filename", "url"])
            for r in moves:
                writer.writerow([r.document_id, r.origin, r.rule, r.source, r.current,
                                 r.proposed, r.delta_days, r.filename, r.url])
        print(f"\nwrote {len(moves)} would-move rows to {args.csv}")

    print("\nNothing has been changed. published_at is still node.created "
          "for every document above.\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
