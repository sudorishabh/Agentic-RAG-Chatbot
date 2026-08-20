"""Read/write path for per-document knowledge runs.

One row per ``(document_id, doc_version)``, upserted. It answers three
questions that nothing else could:

* *did this document's knowledge stage run, and what did it produce?*
* *which documents need retrying, and how often have we already tried?*
* *which knowledge rules was a document processed under?* — the
  ``knowledge_version`` fingerprint, so a rule change is a query rather than
  archaeology.

Conventions follow ``app.catalog.enrichment`` and ``app.catalog.mentions``:
schema ensured once per process, raw SQL, own connection per call, and
``attempts`` incremented in the upsert so a document that keeps failing can be
stopped rather than retried forever.

Never raises into a caller that is already fail-open: :func:`record` swallows
its own failure, because a report row that cannot be written must not be the
thing that turns a successful knowledge run into a failed one.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.catalog import schema
from app.catalog.db import state_table
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)

_ensured = False

# Counter columns, in one place so the writer, the reader and the report model
# cannot disagree about what is recorded. Every one defaults to 0 in the DDL.
COUNTER_COLUMNS: tuple[str, ...] = (
    "chunks_seen", "chunks_cached", "mentions",
    "entities_auto", "entities_provisional", "entities_ambiguous",
    "entities_unresolved",
    "claims_built", "claims_staged", "claims_rejected", "claims_retracted",
    "pending_predicates", "conflicts_disputed", "conflicts_superseded",
    "projection_edges",
)


def _ensure() -> None:
    global _ensured
    if not _ensured:
        schema.ensure_knowledge_run_table()
        _ensured = True


def reset_ensure_cache() -> None:
    """Forget that the schema was ensured. For tests."""
    global _ensured
    _ensured = False


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def record(report: Any) -> bool:
    """Persist one document's knowledge run. Returns whether the row landed.

    ``attempts`` increments on every write rather than being supplied by the
    caller: the row is the only durable memory of how often this document has
    been tried, and a caller that computed it would have to read first.

    ``created_at`` is preserved on update, so the row still records when this
    document/version was first processed.
    """
    _ensure()
    table = state_table()
    now = _now()
    counters = [int(getattr(report, name, 0) or 0) for name in COUNTER_COLUMNS]
    rejection_counts = getattr(report, "rejection_counts", None) or {}
    errors = getattr(report, "errors", None) or []
    values = [
        report.document_id[:255],
        int(report.doc_version),
        (getattr(report, "run_id", None) or None),
        report.status[:16],
        float(getattr(report, "seconds", 0.0) or 0.0),
        *counters,
        (getattr(report, "projection_status", None) or "skipped")[:16],
        getattr(report, "projection_version", None),
        json.dumps(rejection_counts),
        json.dumps(errors),
        _first_error(errors),
        (getattr(report, "knowledge_version", "") or "")[:128],
        now, now,
    ]
    counter_names = ", ".join(COUNTER_COLUMNS)
    counter_updates = ", ".join(f"{c}=VALUES({c})" for c in COUNTER_COLUMNS)
    placeholders = ", ".join(["%s"] * len(values))
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO `{table}_knowledge_run` "
                "(document_id, doc_version, run_id, status, seconds, "
                f" {counter_names}, "
                " projection_status, projection_version, rejection_counts, "
                " errors, last_error, knowledge_version, created_at, updated_at) "
                f"VALUES ({placeholders}) "
                "ON DUPLICATE KEY UPDATE "
                "  run_id=VALUES(run_id), status=VALUES(status), "
                "  attempts=attempts + 1, seconds=VALUES(seconds), "
                f" {counter_updates}, "
                "  projection_status=VALUES(projection_status), "
                "  projection_version=VALUES(projection_version), "
                "  rejection_counts=VALUES(rejection_counts), "
                "  errors=VALUES(errors), last_error=VALUES(last_error), "
                "  knowledge_version=VALUES(knowledge_version), "
                "  updated_at=VALUES(updated_at)",
                values,
            )
            conn.commit()
        return True
    except Exception:
        logger.warning(
            "Could not record the knowledge run for %s v%s; the knowledge work "
            "itself is unaffected.", report.document_id, report.doc_version,
            exc_info=True,
        )
        return False


def _first_error(errors: list[dict[str, str]]) -> str | None:
    if not errors:
        return None
    first = errors[0]
    return f"{first.get('stage', '?')}/{first.get('id', '?')}: {first.get('error', '')}"[:2000]


def get(document_id: str, doc_version: int) -> dict[str, Any] | None:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}_knowledge_run` "
            "WHERE document_id=%s AND doc_version=%s",
            (document_id, doc_version),
        )
        return cur.fetchone()


def for_document(document_id: str) -> list[dict[str, Any]]:
    """Every version's run for one document, newest version first."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}_knowledge_run` WHERE document_id=%s "
            "ORDER BY doc_version DESC",
            (document_id,),
        )
        return list(cur.fetchall())


# Statuses a catch-up pass should revisit. `ok` is done; `skipped` means the
# stage decided there was nothing to do, which a retry would decide again.
RETRYABLE_STATUSES = ("partial", "failed")


def pending(*, max_attempts: int, limit: int = 100) -> list[dict[str, Any]]:
    """Documents whose knowledge stage should be retried.

    Two populations, and both matter:

    * a run that ended ``partial`` or ``failed`` and is still under the attempt
      ceiling — the ordinary retry;
    * an indexed document with **no run row at all** for its current version —
      a stage that never ran, or one that crashed before it could report. The
      row is written last precisely so this absence is detectable.

    Ordered oldest-first so a backlog drains in the order it accumulated rather
    than starving its head.
    """
    _ensure()
    table = state_table()
    statuses = ", ".join(["%s"] * len(RETRYABLE_STATUSES))
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT d.document_id, d.doc_version, d.source_type, d.bundle, "
            f"       COALESCE(k.attempts, 0) AS attempts, k.status AS status "
            f"FROM `{table}` d "
            f"LEFT JOIN `{table}_knowledge_run` k "
            "  ON k.document_id = d.document_id AND k.doc_version = d.doc_version "
            "WHERE d.indexed_at IS NOT NULL "
            "  AND ("
            "        k.document_id IS NULL "
            f"     OR (k.status IN ({statuses}) AND k.attempts < %s)"
            "      ) "
            "ORDER BY COALESCE(k.updated_at, d.indexed_at) ASC "
            "LIMIT %s",
            [*RETRYABLE_STATUSES, int(max_attempts), int(limit)],
        )
        return list(cur.fetchall())


def status_counts() -> dict[str, int]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT status, COUNT(*) AS n FROM `{table}_knowledge_run` "
            "GROUP BY status"
        )
        return {r["status"]: int(r["n"]) for r in cur.fetchall()}


def latest(limit: int = 5) -> list[dict[str, Any]]:
    """The most recently updated runs, for an operator view."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, doc_version, status, attempts, seconds, "
            f"       claims_staged, pending_predicates, projection_status, "
            f"       projection_version, knowledge_version, last_error, updated_at "
            f"FROM `{table}_knowledge_run` ORDER BY updated_at DESC LIMIT %s",
            (int(limit),),
        )
        return list(cur.fetchall())


def recent_errors(limit: int = 5) -> list[dict[str, Any]]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, doc_version, status, attempts, last_error, "
            f"       updated_at FROM `{table}_knowledge_run` "
            "WHERE last_error IS NOT NULL ORDER BY updated_at DESC LIMIT %s",
            (int(limit),),
        )
        return list(cur.fetchall())


def clear_all() -> None:
    """Drop every run row. The knowledge layer is rebuildable, so this is a
    supported reset rather than an emergency."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"DELETE FROM `{table}_knowledge_run`")
        conn.commit()
