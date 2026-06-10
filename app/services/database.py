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
from pymysql.cursors import DictCursor

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_connection() -> pymysql.connections.Connection:
    """Open a new MySQL connection using settings from the environment.

    The caller owns the connection and is responsible for closing it. Prefer
    :func:`mysql_connection` (context manager) or :func:`fetch_all` for most
    call sites so the connection is always closed.
    """
    settings = get_settings()
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database or None,
        connect_timeout=settings.mysql_connect_timeout,
        cursorclass=DictCursor,
    )


@contextmanager
def mysql_connection() -> Iterator[pymysql.connections.Connection]:
    """Context manager that opens a connection and reliably closes it."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


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
