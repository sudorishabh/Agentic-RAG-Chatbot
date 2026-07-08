from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.deps import mysql_connection

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """One ingestion event: where a file/record came from and what happened."""

    document_id: str
    source_type: str
    status: str
    run_id: str | None = None
    source_path: str | None = None
    source_url: str | None = None
    bundle: str | None = None
    tags: str | None = None
    title: str | None = None
    doc_version: int | None = None
    chunks_indexed: int | None = None
    fingerprint: str | None = None
    content_hash: str | None = None
    error_message: str | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _table() -> str:
    name = get_settings().ingest_log_table
    return name if name.replace("_", "").isalnum() else "ingest_log"


_DDL = """
CREATE TABLE IF NOT EXISTS `{table}` (
    id             BIGINT        NOT NULL AUTO_INCREMENT,
    run_id         VARCHAR(64)   NULL,
    document_id    VARCHAR(255)  NOT NULL,
    source_type    VARCHAR(32)   NOT NULL,
    source_path    VARCHAR(1024) NULL,
    source_url     VARCHAR(1024) NULL,
    bundle         VARCHAR(128)  NULL,
    tags           VARCHAR(1024) NULL,
    title          VARCHAR(512)  NULL,
    status         VARCHAR(32)   NOT NULL,
    doc_version    INT           NULL,
    chunks_indexed INT           NULL,
    fingerprint    VARCHAR(128)  NULL,
    content_hash   VARCHAR(64)   NULL,
    error_message  TEXT          NULL,
    event_time     DATETIME      NOT NULL,
    PRIMARY KEY (id),
    KEY idx_document (document_id),
    KEY idx_source_type (source_type),
    KEY idx_event_time (event_time),
    KEY idx_run (run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_table() -> None:
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_DDL.format(table=table))
        conn.commit()


def _clip(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    return value if len(value) <= limit else value[:limit]


def record(entry: LogEntry) -> None:
    """Append one ingestion event. Never raises — logging must not break ingestion."""
    settings = get_settings()
    if not settings.ingest_log_enabled:
        return
    table = _table()
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO `{table}`
                    (run_id, document_id, source_type, source_path, source_url,
                     bundle, tags, title, status, doc_version, chunks_indexed,
                     fingerprint, content_hash, error_message, event_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    _clip(entry.run_id, 64),
                    _clip(entry.document_id, 255),
                    _clip(entry.source_type, 32),
                    _clip(entry.source_path, 1024),
                    _clip(entry.source_url, 1024),
                    _clip(entry.bundle, 128),
                    _clip(entry.tags, 1024),
                    _clip(entry.title, 512),
                    _clip(entry.status, 32),
                    entry.doc_version,
                    entry.chunks_indexed,
                    _clip(entry.fingerprint, 128),
                    _clip(entry.content_hash, 64),
                    entry.error_message,
                    _now(),
                ),
            )
            conn.commit()
    except Exception:
        logger.exception("Failed to write ingest log for %s; continuing.", entry.document_id)


def prune(batch_size: int = 10_000) -> int:
    """Delete rows older than ``ingest_log_retention_days``; returns rows deleted.

    Deletes in batches so a large backlog (the log was unpruned historically)
    never holds one long row-lock transaction. Never raises — retention is
    housekeeping and must not break the sweep loop.
    """
    settings = get_settings()
    days = settings.ingest_log_retention_days
    if not settings.ingest_log_enabled or days <= 0:
        return 0
    cutoff = _now() - timedelta(days=days)
    table = _table()
    deleted = 0
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            while True:
                cur.execute(
                    f"DELETE FROM `{table}` WHERE event_time < %s LIMIT {int(batch_size)}",
                    (cutoff,),
                )
                conn.commit()
                deleted += cur.rowcount
                if cur.rowcount < batch_size:
                    break
        if deleted:
            logger.info("Pruned %d ingest-log rows older than %s.", deleted, cutoff.date())
    except Exception:
        logger.exception("Ingest log prune failed; continuing.")
    return deleted


def recent(
    *,
    limit: int = 100,
    source_type: str | None = None,
    document_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """Most recent events first, with optional filters. Newest by insertion order."""
    table = _table()
    clauses: list[str] = []
    params: list = []
    if source_type:
        clauses.append("source_type = %s")
        params.append(source_type)
    if document_id:
        clauses.append("document_id = %s")
        params.append(document_id)
    if status:
        clauses.append("status = %s")
        params.append(status)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    limit = max(1, min(int(limit), 1000))
    sql = f"SELECT * FROM `{table}`{where} ORDER BY id DESC LIMIT {limit}"
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    for row in rows:
        ts = row.get("event_time")
        if isinstance(ts, datetime):
            row["event_time"] = ts.isoformat()
    return rows
