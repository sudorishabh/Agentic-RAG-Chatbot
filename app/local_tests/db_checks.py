"""MySQL readback for the local ingestion test.

Resolves table names through app.catalog.db so the report reads exactly the
tables the pipeline wrote — including the isolated ``local_test_*`` tables the
runner configures via environment overrides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.catalog import log as ingest_log
from app.catalog.db import log_table, state_table
from app.core.clients import mysql_connection


@dataclass
class CatalogSnapshot:
    """Everything MySQL holds for one document after an ingestion run."""

    document_id: str
    state_row: dict[str, Any] | None = None
    authors: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    term_links: list[dict[str, Any]] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    log_rows: list[dict[str, Any]] = field(default_factory=list)


def _rows(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def fetch_snapshot(document_id: str) -> CatalogSnapshot:
    """Read a document's state row, facet rows, links, and log entries back."""
    table = state_table()
    snap = CatalogSnapshot(document_id=document_id)

    rows = _rows(f"SELECT * FROM `{table}` WHERE document_id = %s", (document_id,))
    snap.state_row = rows[0] if rows else None
    snap.authors = [
        r["author"]
        for r in _rows(
            f"SELECT author FROM `{table}_author` WHERE document_id = %s ORDER BY author",
            (document_id,),
        )
    ]
    snap.themes = [
        r["theme"]
        for r in _rows(
            f"SELECT theme FROM `{table}_theme` WHERE document_id = %s ORDER BY theme",
            (document_id,),
        )
    ]
    snap.term_links = _rows(
        f"SELECT term_uuid, role FROM `{table}_term` WHERE document_id = %s ORDER BY role",
        (document_id,),
    )
    snap.attachments = _rows(
        f"SELECT file_uuid, origin, url, filename FROM `{table}_attachment` "
        "WHERE document_id = %s ORDER BY file_uuid",
        (document_id,),
    )
    snap.log_rows = ingest_log.recent(document_id=document_id, limit=20)
    return snap


def catalog_tables() -> list[str]:
    """All catalog tables the ingestion run touches, parents first."""
    table = state_table()
    children = [f"{table}_{suffix}" for suffix in ("author", "theme", "term", "attachment")]
    return [table, *children, log_table()]


def table_counts() -> dict[str, int]:
    """Row count per catalog table; -1 marks a table that does not exist yet."""
    counts: dict[str, int] = {}
    with mysql_connection() as conn, conn.cursor() as cur:
        for name in catalog_tables():
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = %s",
                (name,),
            )
            if cur.fetchone() is None:
                counts[name] = -1
                continue
            cur.execute(f"SELECT COUNT(*) AS n FROM `{name}`")
            counts[name] = int(cur.fetchone()["n"])
    return counts


def drop_test_tables() -> list[str]:
    """Drop the isolated test tables (children first, FK-safe).

    Refuses to touch anything not prefixed ``local_test_`` so the real
    catalog can never be dropped by a misconfigured run.
    """
    tables = catalog_tables()
    unsafe = [t for t in tables if not t.startswith("local_test_")]
    if unsafe:
        raise RuntimeError(
            f"Refusing to drop non-test tables {unsafe}; expected local_test_* names."
        )
    dropped: list[str] = []
    with mysql_connection() as conn, conn.cursor() as cur:
        for name in reversed(tables):
            cur.execute(f"DROP TABLE IF EXISTS `{name}`")
            dropped.append(name)
        conn.commit()
    return dropped
