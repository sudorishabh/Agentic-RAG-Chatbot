from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator

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
    published_at: str | None = None
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)


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
    published_at DATETIME      NULL,
    indexed_at   DATETIME      NULL,
    updated_at   DATETIME      NOT NULL,
    PRIMARY KEY (document_id),
    KEY idx_source_type (source_type),
    KEY idx_bundle (source_type, bundle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

# Multi-valued facets stored one row per (document, value) so they count exactly
# via COUNT(DISTINCT document_id). Rows cascade-delete with their parent.
_FACETS: tuple[str, ...] = ("author", "category")

_CHILD_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_{facet}` (
    document_id VARCHAR(255) NOT NULL,
    {facet}     VARCHAR(255) NOT NULL,
    KEY idx_doc (document_id),
    KEY idx_val ({facet}),
    CONSTRAINT `fk_{table}_{facet}` FOREIGN KEY (document_id)
        REFERENCES `{table}` (document_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def _to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def _ensure_column(cur: Any, table: str, column: str, ddl: str) -> None:
    """Add a column to an existing table only if it is missing (idempotent
    migration for deployments created before the column existed)."""
    cur.execute(
        "SELECT 1 FROM information_schema.COLUMNS "
        "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
        (table, column),
    )
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN {ddl}")


def _replace_facet(
    cur: Any, table: str, facet: str, document_id: str, values: Iterable[str]
) -> None:
    cur.execute(f"DELETE FROM `{table}_{facet}` WHERE document_id = %s", (document_id,))
    rows = [(document_id, v[:255]) for v in dict.fromkeys(x for x in values if x)]
    if rows:
        cur.executemany(
            f"INSERT INTO `{table}_{facet}` (document_id, {facet}) VALUES (%s, %s)", rows
        )


def ensure_table() -> None:
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_DDL.format(table=table))
        _ensure_column(cur, table, "published_at", "published_at DATETIME NULL")
        for facet in _FACETS:
            cur.execute(_CHILD_DDL.format(table=table, facet=facet))
        conn.commit()


def _row_to_record(row: dict) -> StateRecord:
    indexed = row.get("indexed_at")
    published = row.get("published_at")
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
        published_at=published.isoformat() if isinstance(published, datetime) else published,
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
                 content_hash, doc_version, changed_mark, published_at,
                 indexed_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                source_type  = VALUES(source_type),
                source_key   = VALUES(source_key),
                bundle       = VALUES(bundle),
                fingerprint  = VALUES(fingerprint),
                content_hash = VALUES(content_hash),
                doc_version  = VALUES(doc_version),
                changed_mark = VALUES(changed_mark),
                published_at = VALUES(published_at),
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
                _to_datetime(record.published_at),
                indexed_at,
                now,
            ),
        )
        _replace_facet(cur, table, "author", record.document_id, record.authors)
        _replace_facet(cur, table, "category", record.document_id, record.categories)
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


def backfill_facets(
    document_id: str,
    published_at: str | None,
    authors: Iterable[str],
    categories: Iterable[str],
) -> bool:
    """Set the date/author/category facets for an already-cataloged document
    (e.g. one indexed before these columns existed). Returns False when no
    catalog row exists for the id, leaving child rows untouched (FK safety)."""
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT 1 FROM `{table}` WHERE document_id = %s", (document_id,))
        if cur.fetchone() is None:
            return False
        cur.execute(
            f"UPDATE `{table}` SET published_at = %s WHERE document_id = %s",
            (_to_datetime(published_at), document_id),
        )
        _replace_facet(cur, table, "author", document_id, authors)
        _replace_facet(cur, table, "category", document_id, categories)
        conn.commit()
    return True


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


def _like(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def count_documents(
    source_type: str | None = None,
    bundle: str | None = None,
    *,
    author: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
) -> int:
    """Count catalog documents (not chunks) matching the given filters.

    ``author`` matches a substring against the author facet; the date bounds are
    a half-open ``[from, to)`` interval over ``published_at``."""
    table = _table()
    clauses: list[str] = []
    params: list[Any] = []
    if source_type is not None:
        clauses.append("s.source_type = %s")
        params.append(source_type)
    if bundle is not None:
        clauses.append("s.bundle = %s")
        params.append(bundle)
    if published_from is not None:
        clauses.append("s.published_at >= %s")
        params.append(published_from)
    if published_to is not None:
        clauses.append("s.published_at < %s")
        params.append(published_to)

    join = ""
    count_expr = "COUNT(*)"
    if author:
        join = f" JOIN `{table}_author` a ON a.document_id = s.document_id"
        clauses.append("a.author LIKE %s")
        params.append(_like(author))
        count_expr = "COUNT(DISTINCT s.document_id)"

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT {count_expr} AS n FROM `{table}` s{join}{where}"
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
    return int(row["n"]) if row and row["n"] is not None else 0


def iter_records(source_type: str) -> Iterator[StateRecord]:
    for record in load(source_type).values():
        yield record
