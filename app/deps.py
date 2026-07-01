from __future__ import annotations

import logging
import queue
import threading
from contextlib import contextmanager
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Iterator

import pymysql
from pymysql.cursors import DictCursor

from app.config import get_settings

from app.generation.llm_client import get_llm
from app.ingestion.embedder import get_embeddings

if TYPE_CHECKING:
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

__all__ = [
    "get_qdrant_client",
    "ensure_collection",
    "get_vector_store",
    "delete_document",
    "MySQLPool",
    "get_mysql_pool",
    "mysql_connection",
    "new_mysql_connection",
    "get_redis",
    "get_embeddings",
    "get_llm",
]


@lru_cache
def get_qdrant_client() -> "QdrantClient":
    from qdrant_client import QdrantClient

    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def ensure_collection() -> None:
    from qdrant_client.models import Distance, VectorParams

    settings = get_settings()
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        dimension = len(get_embeddings().embed_query("dimension probe"))
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )


def delete_document(document_id: str) -> None:
    from qdrant_client.models import (
        FieldCondition,
        Filter,
        FilterSelector,
        MatchValue,
    )

    settings = get_settings()
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        return
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=document_id)
                    )
                ]
            )
        ),
    )


@lru_cache
def get_vector_store() -> "QdrantVectorStore":
    from langchain_qdrant import QdrantVectorStore

    settings = get_settings()
    ensure_collection()
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_collection,
        embedding=get_embeddings(),
    )


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
            conn.rollback()
        except Exception:
            self._drop_count()
            conn = self._reconnect(conn)
        return conn

    def _open_or_wait(self) -> pymysql.connections.Connection:
        with self._lock:
            if self._created < self._size:
                self._created += 1
                return new_mysql_connection()
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
    return MySQLPool(get_settings().mysql_pool_size)


@contextmanager
def mysql_connection() -> Iterator[pymysql.connections.Connection]:
    with get_mysql_pool().connection() as conn:
        yield conn


@lru_cache
def get_redis() -> Any | None:
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        import redis
    except ImportError:
        logger.warning("redis_url is set but the 'redis' package is not installed.")
        return None
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
