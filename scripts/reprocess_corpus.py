"""Rebuild catalogued documents that a superseded pipeline produced.

Selection comes from the catalog, not from Drupal's changed-since window: a code
change moves nothing at the source, so the incremental crawl can never reach a
document whose page has not been edited. See :mod:`app.ingestion.reprocess`.

Safe to interrupt and re-run — progress is the catalog's stamped
`pipeline_version`, not a cursor file. Nothing here deletes a document:
reconciliation is never enabled, and replacement is the ordinary
index-then-remove swap.

    python -m scripts.reprocess_corpus --dry-run          # census + window only
    python -m scripts.reprocess_corpus --limit 200        # a cautious first pass
    python -m scripts.reprocess_corpus --bundle news      # one bundle
    python -m scripts.reprocess_corpus                    # everything, in passes
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

logger = logging.getLogger("reprocess_corpus")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--bundle", action="append", default=[],
        help="Limit to bundle(s); repeatable. Default: every stale bundle.",
    )
    parser.add_argument(
        "--limit", type=int,
        help="Stop after roughly this many documents have been rebuilt.",
    )
    parser.add_argument(
        "--batch-size", type=int,
        help="Pause after this many processed documents (0 disables).",
    )
    parser.add_argument(
        "--pause", type=float,
        help="Seconds to pause between batches.",
    )
    parser.add_argument(
        "--max-passes", type=int, default=50,
        help="Ceiling on crawl passes in one invocation (default: 50).",
    )
    parser.add_argument(
        "--include-unpublished", action="store_true",
        help="Include unpublished Drupal nodes, as the crawl flag does.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what is stale and how far back the crawl would reach. "
             "Crawls nothing, indexes nothing, deletes nothing.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the report as JSON."
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    from app.ingestion.reprocess import reprocess

    report = reprocess(
        args.bundle or None,
        limit=args.limit,
        batch_size=args.batch_size,
        pause=args.pause,
        max_passes=args.max_passes,
        dry_run=args.dry_run,
        published_only=not args.include_unpublished,
        progress=print,
    )

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(
            f"\nRebuilt {report.rebuilt} document(s); {report.stale_after} still "
            f"on an older pipeline version ({report.stopped_because})."
        )
    # Non-zero only when a run stopped on a problem rather than on an
    # instruction, so this can gate a deployment step.
    return 1 if report.stopped_because == "no progress" else 0


if __name__ == "__main__":
    sys.exit(main())
