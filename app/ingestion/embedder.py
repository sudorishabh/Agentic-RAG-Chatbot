"""Backwards-compatible facade.

The embeddings gateway now lives in :mod:`app.core.clients.embeddings` (it is a
shared concern used by the query/retrieval path as much as by ingestion). This
module re-exports it so existing ``app.ingestion.embedder`` imports keep working;
prefer importing from ``app.core.clients`` in new code.
"""
from app.core.clients.embeddings import embed_query, get_embeddings

__all__ = ["embed_query", "get_embeddings"]
