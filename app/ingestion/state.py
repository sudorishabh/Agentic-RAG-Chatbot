"""Ingestion manifest — the persistent record of what has already been ingested.

Change detection (:mod:`app.ingestion.change_detection`) needs to remember, across
runs, what each source looked like last time so it can answer NEW / CHANGED /
UNCHANGED / DELETED without re-extracting everything. That memory lives in a
single MySQL table (reusing the shared pooled connection from
:mod:`app.deps`):

================  ============================================================
``document_id``   canonical id (PDF: path slug; Drupal: node uuid) — primary key
``source_type``   ``"pdf"`` | ``"article"`` (matches CanonicalDocument.source_type)
``source_key``    where it came from (absolute PDF path / Drupal node url or uuid)
``bundle``        Drupal node bundle (NULL for PDFs) — scopes the high-water mark
``fingerprint``   cheap pre-extraction signal: PDF raw-bytes SHA-256, or the
                  Drupal ``changed`` timestamp
``content_hash``  CanonicalDocument.content_hash — the exact post-extraction signal
``doc_version``   bumped each time content actually changes
``changed_mark``  Drupal ``changed`` as a unix int, for the incremental high-water
``indexed_at``    when this version was last written to Qdrant
``updated_at``    when this row was last touched
================  ============================================================

Everything here is plain SQL over the shared connection; no ORM.
"""

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
    """One manifest row — the last-known state of a single document."""

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
    # The table name comes from settings, not user input; still constrain it to a
    # safe identifier so it can be interpolated into DDL/DML (params can't name a
    # table). Falls back to the default on anything unexpected.
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
    """Create the manifest table if it does not yet exist (idempotent)."""
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
    """All manifest rows for a source type, keyed by ``document_id``.

    Change detection loads the whole manifest for a source once per run, then
    classifies discovered items against it in memory — one query instead of one
    per document.
    """
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
    """Insert or update one manifest row. ``mark_indexed`` stamps ``indexed_at``
    (set it ``False`` when only refreshing a fingerprint on unchanged content)."""
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
    """Remove manifest rows for the given documents (e.g. after a source delete).
    Returns the number of rows removed."""
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
    """Greatest ``changed_mark`` seen for a source (optionally one Drupal bundle).

    This seeds the next incremental Drupal crawl's ``changed_since`` so we only
    fetch nodes modified after the newest one we already have.
    """
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
    """All known ``document_id``s for a source — used by the reconcile pass to
    diff what we have against what the source still exposes."""
    table = _table()
    sql = f"SELECT document_id FROM `{table}` WHERE source_type = %s"
    params: tuple = (source_type,)
    if bundle is not None:
        sql += " AND bundle = %s"
        params += (bundle,)
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return {row["document_id"] for row in cur.fetchall()}


def iter_records(source_type: str) -> Iterator[StateRecord]:
    """Stream every manifest row for a source type."""
    for record in load(source_type).values():
        yield record
