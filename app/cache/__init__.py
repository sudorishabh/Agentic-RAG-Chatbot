"""Semantic answer cache: a near-verbatim repeat question reuses its answer.

Backed by its own Qdrant collection, gated by cosine threshold *and* a stored
facet fingerprint (:mod:`.cache_keys`), expired by a stored ``expires_at``
because Qdrant has no TTL. Read by :mod:`app.pipeline.query_pipeline`; pruned by
the ingestion sweep loop.
"""
