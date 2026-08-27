from __future__ import annotations

import queue
import threading
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

import pymysql
from pymysql.cursors import DictCursor

from app.config import get_settings
from app.observability.retrieval_log import sql as sql_tracing


def new_mysql_connection() -> pymysql.connections.Connection:
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


class MySQLPool:

    def __init__(self, size: int, *, checkout_timeout: float = 30.0) -> None:
        self._size = max(1, size)
        self._checkout_timeout = checkout_timeout
        self._idle: queue.LifoQueue[pymysql.connections.Connection] = queue.LifoQueue(
            maxsize=self._size
        )
        self._lock = threading.Lock()
        self._created = 0

    def _checkout(self) -> pymysql.connections.Connection:
        try:
            conn = self._idle.get_nowait()
        except queue.Empty:
            conn = self._open_or_wait()
        try:
            conn.ping(reconnect=True)
            conn.rollback()
        except Exception:
            self._drop_count()
            conn = self._reconnect(conn)
        return conn

    def _open_new(self) -> pymysql.connections.Connection:
        """Open a connection for an already-reserved slot, releasing the slot if
        the connect fails — otherwise a transient outage permanently shrinks the
        pool until every checkout blocks forever."""
        try:
            return new_mysql_connection()
        except Exception:
            self._drop_count()
            raise

    def _open_or_wait(self) -> pymysql.connections.Connection:
        with self._lock:
            reserved = self._created < self._size
            if reserved:
                self._created += 1
        # Connect outside the lock so a slow handshake never serializes checkouts.
        if reserved:
            return self._open_new()
        try:
            return self._idle.get(timeout=self._checkout_timeout)
        except queue.Empty:
            raise TimeoutError(
                f"MySQL pool exhausted; no connection available within "
                f"{self._checkout_timeout}s."
            )

    def _reconnect(self, conn: pymysql.connections.Connection) -> pymysql.connections.Connection:
        try:
            conn.close()
        except Exception:
            pass
        with self._lock:
            self._created += 1
        return self._open_new()

    def _release(self, conn: pymysql.connections.Connection) -> None:
        try:
            self._idle.put_nowait(conn)
        except queue.Full:
            self._discard(conn)

    def _discard(self, conn: pymysql.connections.Connection) -> None:
        try:
            conn.close()
        except Exception:
            pass
        self._drop_count()

    def _drop_count(self) -> None:
        with self._lock:
            self._created = max(0, self._created - 1)

    @contextmanager
    def connection(self) -> Iterator[pymysql.connections.Connection]:
        conn = self._checkout()
        try:
            yield conn
        except BaseException:
            self._discard(conn)
            raise
        else:
            self._release(conn)

    def dispose(self) -> None:
        while True:
            try:
                conn = self._idle.get_nowait()
            except queue.Empty:
                break
            self._discard(conn)


@lru_cache
def get_mysql_pool() -> MySQLPool:
    settings = get_settings()
    return MySQLPool(settings.mysql_pool_size, checkout_timeout=settings.mysql_pool_timeout)


@contextmanager
def mysql_connection() -> Iterator[pymysql.connections.Connection]:
    """A pooled connection, checked out for the duration of the block.

    While a query is being traced (``is_retrieval_log``) the caller gets a
    proxy that records every statement it executes — the SQL, its parameters,
    the tables it touched, its latency and the rows it returned — into that
    query's trace. The proxy delegates everything else to the real connection,
    so the pool and every caller behave identically; with logging off the real
    connection is handed out untouched and nothing is wrapped. Instrumenting
    the gateway rather than the ~30 call sites in ``app.catalog`` is what keeps
    the logging out of the queries themselves.
    """
    with get_mysql_pool().connection() as conn:
        yield sql_tracing.instrument(conn)
