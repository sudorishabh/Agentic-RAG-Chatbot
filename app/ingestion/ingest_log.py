from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

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
