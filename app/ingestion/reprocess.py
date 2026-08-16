"""Rebuild catalogued documents that a superseded pipeline produced.

The incremental crawl cannot do this on its own. Its window is
``changed >= MAX(changed_mark)`` per bundle, and a code change moves nothing in
Drupal — so a document last edited in 2018 stays outside every window forever,
however many chunker fixes land. That is why ~99% of the corpus was pinned to
whatever the pipeline did the day each document was first seen.

The selection therefore comes from the **catalog**: which documents are not on
:data:`app.ingestion.version.PIPELINE_VERSION`, and how far back the crawl would
have to reach to include them. That per-bundle floor is then handed to the
ordinary crawl (``extra_floors``), which reaches them, and the ordinary pipeline
rebuilds them — no second ingestion path, no re-implemented extraction, and
every guard on the normal path still in force.

Three properties matter for a corpus-sized run:

* **Resumable.** Progress lives in the catalog: a rebuilt document is stamped
  with the current version and leaves the stale set. Interrupt this at any point
  and re-run it; it recomputes what is left and carries on. Nothing is written to
  track a run.
* **Bounded.** ``limit`` caps the documents processed, ``batch_size``/``pause``
  throttle within a pass, and the existing budget only counts real work — the
  documents re-fetched inside the widened window that turn out to be current cost
  a fingerprint comparison and nothing else.
* **Non-destructive.** Reconciliation is never enabled here, so no crawl driven
  by this module can delete a document. Replacement is the ordinary swap: index
  the new points, then remove what they replaced.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

from app.catalog.db import state_table as _table
from app.core.clients import mysql_connection
from app.ingestion.version import PIPELINE_VERSION

logger = logging.getLogger(__name__)

__all__ = ["BundleStale", "Census", "census", "floors_for", "reprocess", "ReprocessReport"]


@dataclass(frozen=True)
class BundleStale:
    """One bundle's share of the work, and how far back it reaches."""

    bundle: str | None
    documents: int
    #: The earliest crawl position among this bundle's stale documents — the
    #: floor the window has to be pulled back to for the crawl to include them.
    floor: int | None
    #: Stale documents carrying no crawl position at all. They cannot widen a
    #: window; they are reached only if their bundle is crawled in full.
    without_position: int


@dataclass(frozen=True)
class Census:
    """What is stale right now, per bundle."""

    version: str
    bundles: list[BundleStale] = field(default_factory=list)

    @property
    def documents(self) -> int:
        return sum(b.documents for b in self.bundles)

    @property
    def without_position(self) -> int:
        return sum(b.without_position for b in self.bundles)

    def as_dict(self) -> dict:
        return {
            "version": self.version,
            "documents": self.documents,
            "without_position": self.without_position,
            "bundles": [
                {"bundle": b.bundle, "documents": b.documents, "floor": b.floor}
                for b in self.bundles
            ],
        }


def census(*, version: str = PIPELINE_VERSION, bundles: Sequence[str] | None = None) -> Census:
    """Which catalogued documents were built by something other than ``version``.

    One grouped read rather than a scan: the question is per bundle, because the
    crawl window is.

    A NULL version counts as stale — every row written before versions were
    stamped has one, and those are precisely the documents this exists for.
    """
    table = _table()
    clauses = ["(pipeline_version IS NULL OR pipeline_version <> %s)"]
    params: list[object] = [version]
    if bundles:
        clauses.append(f"bundle IN ({', '.join(['%s'] * len(bundles))})")
        params.extend(bundles)
    sql = (
        f"SELECT bundle, COUNT(*) AS documents, MIN(changed_mark) AS floor, "
        f"SUM(changed_mark IS NULL) AS without_position "
        f"FROM `{table}` WHERE {' AND '.join(clauses)} "
        f"GROUP BY bundle ORDER BY documents DESC"
    )
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    return Census(
        version=version,
        bundles=[
            BundleStale(
                bundle=row["bundle"],
                documents=int(row["documents"]),
                floor=int(row["floor"]) if row["floor"] is not None else None,
                without_position=int(row["without_position"] or 0),
            )
            for row in rows
        ],
    )


def floors_for(report: Census) -> dict[str, int]:
    """The per-bundle window the crawl needs to reach everything stale."""
    return {
        b.bundle: b.floor
        for b in report.bundles
        if b.bundle is not None and b.floor is not None
    }


@dataclass
class ReprocessReport:
    """What a run did, pass by pass."""

    version: str
    dry_run: bool
    stale_before: int
    stale_after: int
    passes: list[dict] = field(default_factory=list)
    stopped_because: str = "complete"

    @property
    def rebuilt(self) -> int:
        return max(0, self.stale_before - self.stale_after)

    def as_dict(self) -> dict:
        return {
            "version": self.version,
            "dry_run": self.dry_run,
            "stale_before": self.stale_before,
            "stale_after": self.stale_after,
            "rebuilt": self.rebuilt,
            "stopped_because": self.stopped_because,
            "passes": self.passes,
        }


def reprocess(
    bundles: Iterable[str] | None = None,
    *,
    limit: int | None = None,
    batch_size: int | None = None,
    pause: float | None = None,
    max_passes: int = 50,
    dry_run: bool = False,
    published_only: bool = True,
    progress: Callable[[str], None] = logger.info,
    run: Callable[..., object] | None = None,
) -> ReprocessReport:
    """Walk the catalog and rebuild everything not on the current version.

    Each pass recomputes the stale census, widens the crawl window to the oldest
    stale document per bundle, and runs one ordinary ingestion. Passes repeat
    until nothing is stale, the limit is spent, or a pass makes no progress —
    that last guard matters because a document that fails to rebuild stays stale,
    and without it the loop would run forever re-attempting it.

    ``dry_run`` reports the census and the window it would ask for, and returns
    before any ingestion.
    """
    from app.catalog import state
    from app.config import get_settings
    from app.ingestion.pipeline import ingest_drupal

    # The question cannot be asked before the column exists. This is the same
    # idempotent call every ingestion run makes; it adds a nullable column and
    # an index and changes no row, so a dry run is still a dry run.
    state.ensure_table()

    run = run or ingest_drupal
    selected = list(bundles) if bundles else None
    start = census(bundles=selected)
    report = ReprocessReport(
        version=PIPELINE_VERSION,
        dry_run=dry_run,
        stale_before=start.documents,
        stale_after=start.documents,
    )

    progress(
        f"{start.documents} document(s) are not on pipeline version "
        f"{PIPELINE_VERSION}"
        + (f" (bundles: {', '.join(selected)})" if selected else "")
    )
    for bundle in start.bundles:
        progress(
            f"  {bundle.bundle or '(no bundle)':<28} {bundle.documents:>6} stale, "
            f"crawl from {bundle.floor if bundle.floor is not None else 'n/a'}"
        )
    if start.without_position:
        progress(
            f"  note: {start.without_position} stale document(s) carry no crawl "
            f"position and are reached only when their source is fetched in full"
        )

    if dry_run:
        report.stopped_because = "dry run"
        progress("Dry run: nothing was crawled, indexed or deleted.")
        return report
    if not start.documents:
        return report

    settings = get_settings()
    remaining = limit
    current = start
    for number in range(1, max_passes + 1):
        if remaining is not None and remaining <= 0:
            report.stopped_because = "limit reached"
            break

        floors = floors_for(current)
        with _limits(settings, max_docs=remaining, batch_size=batch_size, pause=pause):
            # reconcile_deletes is never passed: a reprocess replaces documents,
            # and nothing about a version bump says anything is gone.
            tally = dict(
                run(
                    selected,
                    published_only=published_only,
                    extra_floors=floors,
                )
            )

        after = census(bundles=selected)
        done = current.documents - after.documents
        report.passes.append(
            {
                "pass": number,
                "stale_before": current.documents,
                "stale_after": after.documents,
                "rebuilt": done,
                "tally": tally,
            }
        )
        report.stale_after = after.documents
        progress(
            f"pass {number}: rebuilt {done}, {after.documents} still stale "
            f"({tally})"
        )
        if remaining is not None:
            remaining -= max(0, done)

        if not after.documents:
            report.stopped_because = "complete"
            break
        if done <= 0:
            report.stopped_because = "no progress"
            logger.warning(
                "A pass rebuilt nothing while %d document(s) remain stale. They "
                "are failing to rebuild rather than waiting their turn — check "
                "ingest_log and documents_retry for the reason.",
                after.documents,
            )
            break
        current = after
    else:
        report.stopped_because = "max passes"

    return report


class _limits:
    """Apply this run's batch controls, then put the settings back.

    The pipeline reads its budget from settings, which is right for a deployment
    and wrong for one invocation of a CLI that wants different numbers. Restoring
    them keeps this usable from a long-lived process (and from a test) without
    leaving the deployment's configuration edited behind it.
    """

    _FIELDS = {
        "max_docs": "ingest_max_docs_per_run",
        "batch_size": "ingest_batch_size",
        "pause": "ingest_batch_pause_seconds",
    }

    def __init__(self, settings, **values) -> None:
        self._settings = settings
        self._wanted = {
            self._FIELDS[name]: value
            for name, value in values.items()
            if value is not None
        }
        self._restore: dict[str, object] = {}

    def __enter__(self):
        for attribute, value in self._wanted.items():
            self._restore[attribute] = getattr(self._settings, attribute)
            setattr(self._settings, attribute, value)
        return self

    def __exit__(self, *exc) -> bool:
        for attribute, value in self._restore.items():
            setattr(self._settings, attribute, value)
        return False
