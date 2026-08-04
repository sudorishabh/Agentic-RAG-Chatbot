"""Attachments the site no longer serves, remembered so they stop being refetched.

Old node body HTML links tender notices, RFQs and similar PDFs that were taken
down once they closed. The link stays in the text forever, so every sweep
harvests it, downloads it, and gets the same 404 — work that can never succeed
and that nothing in the catalog records, since a failed download produces no
document row and therefore no fingerprint to compare against next time.

A marker here closes that loop. It is recorded only for a *client* error, where
the server positively answered that the file is not there; a timeout or a 5xx
stays retryable, because those clear on their own.

**Qualified by fingerprint, not permanent.** A marker suppresses the download
only while the attachment's fingerprint still matches the one that failed, so
the retry comes back exactly when something could have changed: a real
attachment is fingerprinted on its node's changed mark, so re-uploading the file
and saving the node revives it, and an in-body PDF is fingerprinted on its own
URL-derived id, so editing the link revives it as a row that was never marked
dead. A link nobody touches is never downloaded again.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.catalog import schema
from app.catalog.db import now as _now
from app.catalog.db import state_table as _table
from app.core.clients import mysql_connection

__all__ = ["DeadLink", "ensure_table", "load", "record", "clear"]


@dataclass
class DeadLink:
    """One attachment URL that answered with a client error."""

    document_id: str
    fingerprint: str
    url: str | None = None
    status: int = 0
    attempts: int = 1
    first_seen: str | None = None
    updated_at: str | None = None


def ensure_table() -> None:
    schema.ensure_dead_link_table()


def _row_to_dead_link(row: dict) -> DeadLink:
    first_seen, updated = row.get("first_seen"), row.get("updated_at")
    return DeadLink(
        document_id=row["document_id"],
        fingerprint=row["fingerprint"],
        url=row.get("url"),
        status=int(row.get("status") or 0),
        attempts=int(row.get("attempts") or 0),
        first_seen=first_seen.isoformat() if isinstance(first_seen, datetime) else first_seen,
        updated_at=updated.isoformat() if isinstance(updated, datetime) else updated,
    )


def load() -> dict[str, DeadLink]:
    """Every marker, by document_id — the crawl's skip list.

    Loaded once per run and consulted per attachment, the same shape as
    ``state.load``: the table holds one row per dead URL, a handful in practice.
    """
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT * FROM `{_table()}_dead_link`")
        return {row["document_id"]: _row_to_dead_link(row) for row in cur.fetchall()}


def record(document_id: str, *, fingerprint: str, url: str | None, status: int) -> None:
    """Mark an attachment dead at this fingerprint.

    Re-recording the same fingerprint counts another attempt (the sweep reached
    it before the marker existed, or the crawl chose to retry); a different
    fingerprint restarts the count, since it describes a different state of the
    source.
    """
    if not document_id:
        return
    now = _now()
    # Assignment order matters: `attempts` and `first_seen` compare against the
    # *stored* fingerprint, so both have to be evaluated before `fingerprint` is
    # overwritten (MySQL applies ON DUPLICATE KEY assignments left to right).
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO `{_table()}_dead_link` "
            "(document_id, fingerprint, url, status, attempts, first_seen, updated_at) "
            "VALUES (%s, %s, %s, %s, 1, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "  attempts = IF(fingerprint = VALUES(fingerprint), attempts + 1, 1),"
            "  first_seen = IF(fingerprint = VALUES(fingerprint), first_seen, VALUES(first_seen)),"
            "  fingerprint = VALUES(fingerprint),"
            "  url = VALUES(url),"
            "  status = VALUES(status),"
            "  updated_at = VALUES(updated_at)",
            (document_id, fingerprint or "", (url or None), int(status), now, now),
        )
        conn.commit()


def clear(document_ids: Iterable[str]) -> int:
    """Drop markers, so the next sweep downloads these attachments again."""
    ids = [d for d in document_ids if d]
    if not ids:
        return 0
    placeholders = ", ".join(["%s"] * len(ids))
    with mysql_connection() as conn, conn.cursor() as cur:
        removed = cur.execute(
            f"DELETE FROM `{_table()}_dead_link` WHERE document_id IN ({placeholders})",
            tuple(ids),
        )
        conn.commit()
    return int(removed or 0)
