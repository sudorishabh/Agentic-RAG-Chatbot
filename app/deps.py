"""Backwards-compatible facade over :mod:`app.core.clients`.

Historically this module owned the Qdrant / MySQL / Redis clients and re-exported
the embedding and LLM gateways. Those now live in :mod:`app.core.clients`; this
facade keeps the old ``app.deps`` import paths working. Prefer importing from
``app.core.clients`` in new code.
"""
from app.core.clients import (
    MySQLPool,
    delete_document,
    embed_query,
    ensure_collection,
    get_embeddings,
    get_llm,
    get_mysql_pool,
    get_qdrant_client,
    get_redis,
    get_structured_llm,
    get_vector_store,
    mysql_connection,
    new_mysql_connection,
)

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
