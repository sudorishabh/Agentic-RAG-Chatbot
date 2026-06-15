"""MySQL/MariaDB connectivity for the Drupal CMS content source.

Website content lives in a Drupal MySQL database; PDFs are the other ingestion
source. This module centralizes connection handling so extraction code can pull
rows without repeating connection boilerplate.

Connection settings are read from the environment via ``get_settings`` (see
``MYSQL_*`` keys in ``.env``).

Quick connectivity check:
    venv/Scripts/python.exe -m app.services.database
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

import pymysql

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_connection() -> pymysql.connections.Connection:
    """Open a new, unpooled MySQL connection that the caller owns and must close.

    Prefer :func:`mysql_connection` (pooled context manager) or :func:`fetch_all`
    for most call sites. Connection construction now lives in :mod:`app.deps`.
    """
    from app.deps import new_mysql_connection

    return new_mysql_connection()


@contextmanager
def mysql_connection() -> Iterator[pymysql.connections.Connection]:
    """Pooled MySQL connection context manager (borrows from the shared pool)."""
    from app.deps import mysql_connection as pooled_connection

    with pooled_connection() as conn:
        yield conn


def fetch_all(sql: str, params: tuple | dict | None = None) -> list[dict[str, Any]]:
    """Run a read query and return all rows as dicts."""
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def check_connection() -> dict[str, Any]:
    """Connectivity probe: server version, current database, and table count."""
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT VERSION() AS version")
        version = cur.fetchone()["version"]
        cur.execute("SELECT DATABASE() AS db")
        database = cur.fetchone()["db"]
        cur.execute("SHOW TABLES")
        tables = [next(iter(row.values())) for row in cur.fetchall()]
    return {"version": version, "database": database, "table_count": len(tables)}


if __name__ == "__main__":
    settings = get_settings()
    target = f"{settings.mysql_user}@{settings.mysql_host}:{settings.mysql_port}"
    print(f"Connecting to {target} ...")
    info = check_connection()
    print(f"Connected. Server version: {info['version']}")
    print(f"Current database: {info['database']}")
    print(f"Tables: {info['table_count']}")
