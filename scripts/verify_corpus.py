"""Check that the stores agree: MySQL against Qdrant, and the graph beside them.

Reads only. Never repairs, re-indexes or deletes anything — a reconciliation
that acted on what it found would be a second, unsupervised ingestion path.

Run it after a rebuild, after a sweep, or whenever an answer looks wrong. The
sweep runs the same checks itself (`verify_corpus_after_sweep`); this is the
on-demand form, and the one that can gate a deployment step by exit code.

    python -m scripts.verify_corpus
    python -m scripts.verify_corpus --json

Exit codes: 0 clean, 1 drift found, 2 the stores could not be read.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

logger = logging.getLogger("verify_corpus")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    parser.add_argument(
        "--quiet", action="store_true", help="Print only checks that failed."
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    from app.ingestion.reconcile import reconcile

    report = reconcile()

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.ok else (2 if report.error else 1)

    if report.error:
        print(f"Could not read the stores: {report.error}")
        return 2

    print(f"MySQL documents {report.documents}   Qdrant points {report.points}\n")
    for check in report.checks:
        if args.quiet and check.ok:
            continue
        mark = "skip" if check.skipped else ("OK  " if check.ok else "FAIL")
        print(f"  {mark} {check.name:26} {check.count}")
        if not check.ok or check.skipped:
            print(f"       {check.detail}")
            if check.samples:
                print(f"       e.g. {', '.join(check.samples)}")
    print("\n" + ("Reconciliation balances." if report.ok else "DRIFT — see above."))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
