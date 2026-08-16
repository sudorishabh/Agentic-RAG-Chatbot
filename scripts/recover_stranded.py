"""Make documents reachable again that failed before retry markers existed.

Reads the append-only ingest log for documents whose last outcome was `skipped`
or `error` and which never reached the catalog, then writes ordinary retry
markers so the next sweep goes back for them. No queue, no new ingestion path,
and nothing is deleted.

Attachments are recovered through the page that links them — see
:mod:`app.ingestion.recovery` for why marking the attachment's own id would
strand the crawl window instead.

    python -m scripts.recover_stranded --dry-run
    python -m scripts.recover_stranded
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

logger = logging.getLogger("recover_stranded")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would be marked; write nothing.",
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    from app.ingestion.recovery import recover

    report = recover(dry_run=args.dry_run)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0

    print(
        f"{len(report.stranded)} stranded document(s); "
        f"{sum(len(v) for v in report.markers.values())} recoverable via "
        f"{len(report.markers)} marker(s)."
    )
    for marker, recovering in sorted(report.markers.items()):
        print(f"  crawl {marker} -> recovers {len(recovering)}")
    for item in report.unfloorable:
        print(
            f"  ! {item.document_id}: {item.blocked} (marked for triage; it "
            f"returns only when its source is crawled in full)"
        )
    for item in report.unrecoverable:
        print(f"  x {item.document_id}: {item.blocked}")
    if args.dry_run:
        print("\nDry run: no markers were written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
