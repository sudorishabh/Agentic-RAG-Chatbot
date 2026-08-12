"""Documents a run reached but did not index, so the crawl can go back for them.

The incremental cursor is derived from the catalog: ``MAX(changed_mark)`` over
the rows a bundle has, and a row is written only when a document is indexed. A
document that errored or was skipped therefore leaves nothing behind — while
every document processed *after* it does, and the crawl runs oldest-first, so
the next run's cursor sits above the failure and the ``changed >= mark`` filter
never returns it again. Editing the document in Drupal was the only way back.

A row here is that missing trace. The crawl floors its cursor at the earliest
unresolved row per bundle, so the window always reaches back far enough to
include the failure, and a successful outcome deletes the row so the floor lifts
on its own. Everything already indexed inside the widened window resolves
UNCHANGED on its fingerprint, which costs no work and no batch budget.

Kept out of ``documents`` on purpose: a placeholder row there would be counted as
a catalogued document by every analytical read, which is precisely the claim a
failed document must not make.

There is no attempt cap. A document that fails forever holds its bundle's floor
down forever — the cost is a larger scan per run, not lost work — and that is
the deliberate trade for "a temporary failure stays visible without anyone
editing the source".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.catalog import schema
from app.catalog.db import now as _now
from app.catalog.db import state_table as _table
from app.core.clients import mysql_connection

__all__ = ["RetryItem", "ensure_table", "load", "floors", "record", "clear"]


@dataclass
class RetryItem:
    """One document that reached processing and did not come out indexed."""

    document_id: str
    source_type: str
    bundle: str | None = None
    changed_mark: int | None = None
    outcome: str = "error"
    attempts: int = 1
    error: str | None = None
    first_seen: str | None = None
    updated_at: str | None = None


def ensure_table() -> None:
    schema.ensure_retry_table()


def _row_to_item(row: dict) -> RetryItem:
    first_seen, updated = row.get("first_seen"), row.get("updated_at")
    return RetryItem(
        document_id=row["document_id"],
        source_type=row["source_type"],
        bundle=row.get("bundle"),
        changed_mark=row.get("changed_mark"),
        outcome=row.get("outcome") or "error",
        attempts=int(row.get("attempts") or 0),
        error=row.get("error"),
        first_seen=first_seen.isoformat() if isinstance(first_seen, datetime) else first_seen,
        updated_at=updated.isoformat() if isinstance(updated, datetime) else updated,
    )


def load() -> dict[str, RetryItem]:
    """Every unresolved item, by document_id."""
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT * FROM `{_table()}_retry`")
        return {row["document_id"]: _row_to_item(row) for row in cur.fetchall()}


def floors() -> dict[str, int]:
    """The earliest unresolved crawl position per bundle.

    What the crawl actually needs, asked for directly: one grouped read rather
    than loading every row to take a minimum. Rows with no ``changed_mark``
    cannot position the cursor and are left out — they are still retried when
    their bundle is crawled, they just cannot pull the window back.
    """
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT bundle, MIN(changed_mark) AS floor FROM `{_table()}_retry` "
            f"WHERE bundle IS NOT NULL AND changed_mark IS NOT NULL GROUP BY bundle"
        )
        return {row["bundle"]: int(row["floor"]) for row in cur.fetchall()}


def record(
    document_id: str,
    *,
    source_type: str,
    bundle: str | None,
    changed_mark: int | None,
    outcome: str,
    error: str | None = None,
) -> None:
    """Mark a document unresolved, or count another attempt at one.

    ``first_seen`` is preserved across attempts so how long something has been
    failing stays readable; ``attempts`` counts every run that tried.
    """
    if not document_id:
        return
    now = _now()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO `{_table()}_retry` "
            "(document_id, source_type, bundle, changed_mark, outcome, attempts, "
            " error, first_seen, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, 1, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "  source_type  = VALUES(source_type),"
            "  bundle       = VALUES(bundle),"
            "  changed_mark = VALUES(changed_mark),"
            "  outcome      = VALUES(outcome),"
            "  attempts     = attempts + 1,"
            "  error        = VALUES(error),"
            "  updated_at   = VALUES(updated_at)",
            (
                document_id,
                source_type,
                bundle,
                changed_mark,
                outcome[:16],
                (error[:2000] if error else None),
                now,
                now,
            ),
        )
        conn.commit()


def clear(document_ids: Iterable[str]) -> int:
    """Drop items, lifting whatever floor they held."""
    ids = [d for d in document_ids if d]
    if not ids:
        return 0
    placeholders = ", ".join(["%s"] * len(ids))
    with mysql_connection() as conn, conn.cursor() as cur:
        removed = cur.execute(
            f"DELETE FROM `{_table()}_retry` WHERE document_id IN ({placeholders})",
            tuple(ids),
        )
        conn.commit()
    return int(removed or 0)
