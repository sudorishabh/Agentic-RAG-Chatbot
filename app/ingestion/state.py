from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Iterator

from app.config import get_settings
from app.deps import mysql_connection

logger = logging.getLogger(__name__)


@dataclass
class StateRecord:

    document_id: str
    source_type: str
    source_key: str
    fingerprint: str
    content_hash: str = ""
    doc_version: int = 1
    bundle: str | None = None
    changed_mark: int | None = None
    indexed_at: str | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _table() -> str:
    name = get_settings().ingest_state_table
    return name if name.replace("_", "").isalnum() else "ingest_state"


_DDL = """
CREATE TABLE IF NOT EXISTS `{table}` (
    document_id  VARCHAR(255)  NOT NULL,
    source_type  VARCHAR(32)   NOT NULL,
    source_key   VARCHAR(1024) NOT NULL,
    bundle       VARCHAR(128)  NULL,
    fingerprint  VARCHAR(128)  NOT NULL,
    content_hash VARCHAR(64)   NOT NULL DEFAULT '',
    doc_version  INT           NOT NULL DEFAULT 1,
    changed_mark BIGINT        NULL,
    indexed_at   DATETIME      NULL,
    updated_at   DATETIME      NOT NULL,
    PRIMARY KEY (document_id),
    KEY idx_source_type (source_type),
    KEY idx_bundle (source_type, bundle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_table() -> None:
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_DDL.format(table=table))
        conn.commit()


def _row_to_record(row: dict) -> StateRecord:
    indexed = row.get("indexed_at")
    return StateRecord(
        document_id=row["document_id"],
        source_type=row["source_type"],
        source_key=row["source_key"],
        fingerprint=row["fingerprint"],
        content_hash=row.get("content_hash") or "",
        doc_version=int(row.get("doc_version") or 1),
        bundle=row.get("bundle"),
        changed_mark=row.get("changed_mark"),
        indexed_at=indexed.isoformat() if isinstance(indexed, datetime) else indexed,
    )


def load(source_type: str) -> dict[str, StateRecord]:
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}` WHERE source_type = %s", (source_type,)
        )
        return {row["document_id"]: _row_to_record(row) for row in cur.fetchall()}


def get(document_id: str) -> StateRecord | None:
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}` WHERE document_id = %s", (document_id,)
        )
        row = cur.fetchone()
    return _row_to_record(row) if row else None


def upsert(record: StateRecord, *, mark_indexed: bool = True) -> None:
    table = _table()
    now = _now()
    indexed_at = now if mark_indexed else None
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO `{table}`
                (document_id, source_type, source_key, bundle, fingerprint,
                 content_hash, doc_version, changed_mark, indexed_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                source_type  = VALUES(source_type),
                source_key   = VALUES(source_key),
                bundle       = VALUES(bundle),
                fingerprint  = VALUES(fingerprint),
                content_hash = VALUES(content_hash),
                doc_version  = VALUES(doc_version),
                changed_mark = VALUES(changed_mark),
                indexed_at   = COALESCE(VALUES(indexed_at), indexed_at),
                updated_at   = VALUES(updated_at)
            """,
            (
                record.document_id,
                record.source_type,
                record.source_key,
                record.bundle,
                record.fingerprint,
                record.content_hash,
                record.doc_version,
                record.changed_mark,
                indexed_at,
                now,
            ),
        )
        conn.commit()


def delete(document_ids: Iterable[str]) -> int:
    ids = [d for d in document_ids if d]
    if not ids:
        return 0
    table = _table()
    placeholders = ", ".join(["%s"] * len(ids))
    with mysql_connection() as conn, conn.cursor() as cur:
        removed = cur.execute(
            f"DELETE FROM `{table}` WHERE document_id IN ({placeholders})", tuple(ids)
        )
        conn.commit()
    return int(removed or 0)


def high_water(source_type: str, bundle: str | None = None) -> int | None:
    table = _table()
    sql = f"SELECT MAX(changed_mark) AS hw FROM `{table}` WHERE source_type = %s"
    params: tuple = (source_type,)
    if bundle is not None:
        sql += " AND bundle = %s"
        params += (bundle,)
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return int(row["hw"]) if row and row["hw"] is not None else None


def keys(source_type: str, bundle: str | None = None) -> set[str]:
    table = _table()
    sql = f"SELECT document_id FROM `{table}` WHERE source_type = %s"
    params: tuple = (source_type,)
    if bundle is not None:
        sql += " AND bundle = %s"
        params += (bundle,)
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return {row["document_id"] for row in cur.fetchall()}


def count_documents(source_type: str | None = None, bundle: str | None = None) -> int:
    table = _table()
    clauses: list[str] = []
    params: list[str] = []
    if source_type is not None:
        clauses.append("source_type = %s")
        params.append(source_type)
    if bundle is not None:
        clauses.append("bundle = %s")
        params.append(bundle)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM `{table}`{where}", tuple(params))
        row = cur.fetchone()
    return int(row["n"]) if row and row["n"] is not None else 0


def iter_records(source_type: str) -> Iterator[StateRecord]:
    for record in load(source_type).values():
        yield record
