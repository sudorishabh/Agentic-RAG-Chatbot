"""Infrastructure / dependency providers (DI).

The single place that builds and hands out the app's shared infra clients, so
the rest of the code (and FastAPI ``Depends(...)``) imports from one surface
instead of reaching into each service:

* **Qdrant** — the vector DB client / collection / store.
* **MySQL** — a process-wide connection **pool** (see :class:`MySQLPool`), plus a
  pooled ``mysql_connection()`` context manager and a raw ``new_mysql_connection()``.
* **Redis** — a shared cache client (or ``None`` when ``redis_url`` is unset).
* **Models** — the Azure embeddings + chat/reasoning LLM wrappers.

Each client is a cached singleton, so the whole process shares one of each. The
Qdrant and model providers are re-exported from their existing service modules
so this stays the canonical import surface without duplicating construction;
heavy/optional packages (``redis``) are imported lazily.
"""

from __future__ import annotations

import logging
import queue
import threading
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor

from app.config import get_settings

# Re-exported infra providers (canonical construction lives in these modules).
from app.generation.llm_client import get_llm, get_reasoning_llm
from app.ingestion.embedder import get_embeddings
from app.services.vector_store import (
    ensure_collection,
    get_qdrant_client,
    get_vector_store,
)

logger = logging.getLogger(__name__)

__all__ = [
    # Qdrant
    "get_qdrant_client",
    "ensure_collection",
    "get_vector_store",
    # MySQL
    "MySQLPool",
    "get_mysql_pool",
    "mysql_connection",
    "new_mysql_connection",
    # Redis
    "get_redis",
    # Models
    "get_embeddings",
    "get_llm",
    "get_reasoning_llm",
]


# --------------------------------------------------------------------------- #
# MySQL connection pool
# --------------------------------------------------------------------------- #
def new_mysql_connection() -> pymysql.connections.Connection:
    """Open a fresh, unpooled MySQL connection from the configured settings.

    The single source of connection parameters; the pool and any caller that
    needs to own a connection outright build through here.
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


class MySQLPool:
    """A small thread-safe MySQL connection pool over PyMySQL.

    Up to ``size`` connections are created lazily and reused. On checkout a
    connection is ``ping``-validated (reconnecting if the server dropped it) and
    rolled back so each borrow starts a clean transaction — without this, a reused
    connection's open snapshot would serve stale reads. Connections returned after
    an error are discarded rather than reused.
    """

    def __init__(self, size: int) -> None:
        self._size = max(1, size)
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
            conn.rollback()  # discard any lingering transaction/snapshot
        except Exception:
            self._drop_count()
            conn = self._reconnect(conn)
        return conn

    def _open_or_wait(self) -> pymysql.connections.Connection:
        with self._lock:
            if self._created < self._size:
                self._created += 1
                return new_mysql_connection()
        # At capacity — block until another caller returns a connection.
        return self._idle.get()

    def _reconnect(self, conn: pymysql.connections.Connection) -> pymysql.connections.Connection:
        try:
            conn.close()
        except Exception:
            pass
        with self._lock:
            self._created += 1
        return new_mysql_connection()

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
        """Borrow a pooled connection for the duration of the ``with`` block.

        Returned to the pool on clean exit; discarded (closed) if the block
        raised, since the connection may be in an unknown state.
        """
        conn = self._checkout()
        try:
            yield conn
        except BaseException:
            self._discard(conn)
            raise
        else:
            self._release(conn)

    def dispose(self) -> None:
        """Close every idle connection (e.g. on shutdown or in tests)."""
        while True:
            try:
                conn = self._idle.get_nowait()
            except queue.Empty:
                break
            self._discard(conn)


@lru_cache
def get_mysql_pool() -> MySQLPool:
    """The process-wide MySQL pool (one per process)."""
    return MySQLPool(get_settings().mysql_pool_size)


@contextmanager
def mysql_connection() -> Iterator[pymysql.connections.Connection]:
    """Pooled MySQL connection context manager — the preferred way to talk to MySQL."""
    with get_mysql_pool().connection() as conn:
        yield conn


# --------------------------------------------------------------------------- #
# Redis
# --------------------------------------------------------------------------- #
@lru_cache
def get_redis() -> Any | None:
    """The shared Redis client, or ``None`` when ``redis_url`` isn't configured.

    Callers treat Redis as an optional cache: ``None`` means "no cache, carry on".
    The ``redis`` package is imported lazily so it's only required when used.
    """
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        import redis
    except ImportError:
        logger.warning("redis_url is set but the 'redis' package is not installed.")
        return None
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
