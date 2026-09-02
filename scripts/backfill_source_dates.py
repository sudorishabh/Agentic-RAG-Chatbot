"""Superseded by :mod:`scripts.backfill_bundle_dates`. Refuses to run.

This script applied the *field-keyed* rule: four fields were declared publication
dates in ``app.ingestion.source_dates.FIELD_KINDS``, and any record carrying one
took its value whatever content type the record was.

Dates are now **bundle-keyed** — ``news`` takes ``field_news_date``,
``completed_projects`` takes the project's start, ``article`` takes its creation
stamp — so this script's population, its rule and its reviewed
``EXPECTED_MOVES`` no longer describe anything the system does. Running it would
either do nothing or, worse, half-apply a rule ingestion has stopped following.

It is kept as a stub rather than deleted so that a runbook, a cron entry or an
operator's shell history lands on this explanation instead of an ImportError.

    python -m scripts.backfill_bundle_dates            # the replacement
"""
from __future__ import annotations

import sys

REPLACEMENT = "scripts.backfill_bundle_dates"

MESSAGE = f"""\
scripts.backfill_source_dates has been superseded and will not run.

It applied the field-keyed publication-date rule. A document's date is now
decided by its bundle (app.ingestion.bundle_dates), and attached PDFs inherit
their page's resolved date, so the correction this script made is both narrower
and differently scoped than what the corpus now needs.

Use instead:

    python -m {REPLACEMENT}            # dry run
    python -m {REPLACEMENT} --apply
"""


def main(argv: list[str] | None = None) -> int:
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
