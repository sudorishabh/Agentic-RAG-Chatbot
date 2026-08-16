"""Bring back documents that failed before anything recorded that they had.

The retry marker — the thing that keeps a failed document reachable — landed
after the corpus was built. Documents that errored or were skipped before it
existed left no trace at all: no catalog row (so they contribute no
``changed_mark``, and the incremental cursor sits above them), and no retry row
(so no floor pulls the window back). The only evidence they ever existed is the
append-only ``ingest_log``, which nothing reads.

This module reads it, and reuses the existing floor machinery to make them
reachable again. It is not a queue: it writes ordinary retry markers and the next
ordinary sweep does the work.

Why the *parent* is marked, not the attachment
----------------------------------------------
The obvious repair — a retry marker per stranded attachment id — is wrong for
in-body PDFs, which are 77 of the 91 stranded here. Their id is a hash of the
URL (``inbody:<sha1>``), and most were stranded precisely *because* that URL was
malformed (an undecoded ``&amp;``, a whitespace-padded href). Once the extractor
resolves those correctly the same link yields a *different* id, so a marker on
the old id can never resolve: it is never seen again, and its floor holds that
bundle's window open forever, scanning the whole bundle every sweep.

Marking the parent node has none of that. The parent's id is stable, the crawl
re-yields whatever attachments it currently links to — corrected URLs included —
and the marker clears the moment the parent re-ingests, in the same run. One
marker also covers every stranded attachment on that page: 91 attachments here
resolve to 47 parents.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.catalog.db import log_table, state_table
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)

#: What a recovery marker is called in ``documents_retry.outcome``. Its own
#: value, like a reindex request: the document did not fail *this* run, and a
#: queue that cannot tell a fresh failure from a historical one cannot be triaged.
RECOVER_OUTCOME = "recover"

#: Log statuses that mean "this document did not make it into the corpus".
UNRESOLVED_STATUSES = ("skipped", "error")

__all__ = [
    "RECOVER_OUTCOME",
    "Stranded",
    "RecoveryReport",
    "stranded",
    "recover",
]


@dataclass(frozen=True)
class Stranded:
    """A document the log says failed, which the catalog has never heard of."""

    document_id: str
    source_type: str
    status: str
    source_url: str | None = None
    #: The catalogued page that links to it, if it is an attachment.
    parent_id: str | None = None
    #: The crawl position to recover from — the parent's, or the document's own
    #: bundle when it is not an attachment.
    bundle: str | None = None
    changed_mark: int | None = None

    @property
    def recover_via(self) -> str | None:
        """Which document has to be re-crawled to bring this one back."""
        if self.parent_id:
            return self.parent_id
        # A node's own id is stable, so it can be marked directly.
        return self.document_id if self.bundle else None

    @property
    def blocked(self) -> str | None:
        """Why this one cannot be recovered, or None if it can."""
        if self.recover_via is None:
            return "no linking page and no bundle to crawl from"
        if self.changed_mark is None:
            return "no crawl position, so the window cannot be widened for it"
        return None


@dataclass
class RecoveryReport:
    dry_run: bool = False
    stranded: list[Stranded] = field(default_factory=list)
    #: document_id -> the stranded documents that marker is for.
    markers: dict[str, list[str]] = field(default_factory=dict)
    unrecoverable: list[Stranded] = field(default_factory=list)
    unfloorable: list[Stranded] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "stranded": len(self.stranded),
            "markers": len(self.markers),
            "recovering": sum(len(v) for v in self.markers.values()),
            "unrecoverable": [
                {"document_id": s.document_id, "reason": s.blocked, "url": s.source_url}
                for s in self.unrecoverable
            ],
            "unfloorable": [s.document_id for s in self.unfloorable],
        }


# The last thing the log said about each document. An append-only log holds
# every attempt, and only the final one says whether the document is still out.
_LATEST = """
SELECT l.document_id, l.source_type, l.status, l.source_url, l.bundle
FROM `{log}` l
JOIN (SELECT document_id, MAX(id) AS id FROM `{log}` GROUP BY document_id) last
  ON last.id = l.id
"""


def stranded() -> list[Stranded]:
    """Documents whose last logged outcome failed and which never landed.

    A document with a catalog row is not stranded whatever the log says: it was
    indexed later, or it is being retried already. A document with a retry marker
    is likewise left alone — it is already reachable, and re-marking it would
    only reset its attempt count.
    """
    log, table = log_table(), state_table()
    placeholders = ", ".join(["%s"] * len(UNRESOLVED_STATUSES))
    sql = (
        f"SELECT t.document_id, t.source_type, t.status, t.source_url, t.bundle, "
        f"       a.document_id AS parent_id, p.bundle AS parent_bundle, "
        f"       p.changed_mark AS parent_mark "
        f"FROM ({_LATEST.format(log=log)}) t "
        f"LEFT JOIN `{table}` d ON d.document_id = t.document_id "
        f"LEFT JOIN `{table}_retry` r ON r.document_id = t.document_id "
        f"LEFT JOIN `{table}_attachment` a ON a.file_uuid = t.document_id "
        f"LEFT JOIN `{table}` p ON p.document_id = a.document_id "
        f"WHERE t.status IN ({placeholders}) "
        f"  AND d.document_id IS NULL AND r.document_id IS NULL"
    )
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, UNRESOLVED_STATUSES)
        rows = cur.fetchall()

    # One attachment can hang off several pages. Recover from the earliest one:
    # its position is the furthest back, so the widened window covers the others
    # too, and one crawl reaches every page that links the file.
    best: dict[str, Stranded] = {}
    for row in rows:
        item = Stranded(
            document_id=row["document_id"],
            source_type=row["source_type"],
            status=row["status"],
            source_url=row.get("source_url"),
            parent_id=row.get("parent_id"),
            bundle=row.get("parent_bundle") or row.get("bundle"),
            changed_mark=(
                int(row["parent_mark"]) if row.get("parent_mark") is not None else None
            ),
        )
        held = best.get(item.document_id)
        if held is None or _earlier(item, held):
            best[item.document_id] = item
    return sorted(best.values(), key=lambda s: s.document_id)


def _earlier(candidate: Stranded, held: Stranded) -> bool:
    """Whether ``candidate`` gives the better recovery route of the two."""
    if candidate.changed_mark is None:
        return False
    if held.changed_mark is None:
        return True
    return candidate.changed_mark < held.changed_mark


def recover(*, dry_run: bool = False) -> RecoveryReport:
    """Write the retry markers that make the stranded documents reachable again.

    Idempotent in the way that matters: a document that already has a marker is
    not in :func:`stranded`, so re-running this neither duplicates markers nor
    resets an attempt count. Nothing is deleted and no document id is invented —
    every marker names a document the catalog already holds.
    """
    from app.catalog import retries, state

    items = stranded()
    report = RecoveryReport(dry_run=dry_run, stranded=items)

    for item in items:
        if item.recover_via is None:
            report.unrecoverable.append(item)
            continue
        if item.changed_mark is None:
            # Recorded anyway: it makes the document visible for triage and it
            # resolves if its source is crawled in full. It just cannot pull a
            # window back, and saying so is better than implying it will return.
            report.unfloorable.append(item)
        report.markers.setdefault(item.recover_via, []).append(item.document_id)

    if dry_run:
        return report

    retries.ensure_table()
    for marker_id, recovering in report.markers.items():
        source = next(i for i in items if i.recover_via == marker_id)
        parent = state.get(marker_id)
        retries.record(
            marker_id,
            source_type=parent.source_type if parent else source.source_type,
            bundle=parent.bundle if parent else source.bundle,
            changed_mark=parent.changed_mark if parent else source.changed_mark,
            outcome=RECOVER_OUTCOME,
            error=(
                f"re-crawled to recover {len(recovering)} document(s) that failed "
                f"before retry markers existed: {', '.join(recovering[:5])}"
                + ("…" if len(recovering) > 5 else "")
            ),
        )
    logger.info(
        "Recovery: %d stranded document(s), %d marker(s) written, %d unrecoverable.",
        len(items), len(report.markers), len(report.unrecoverable),
    )
    return report
