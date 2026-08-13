"""Read/write path for the entity-mention log and its extraction cache.

Mirrors ``app.catalog.enrichment``: schema ensured once per process, raw SQL,
one batched write per chunk set. Mentions are stored in MySQL and nowhere else
— the graph gets canonical entities later, never this log, which is millions of
append-only rows with no traversal shape.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Sequence

from app.catalog import schema
from app.catalog.db import state_table
from app.core.clients import mysql_connection
from app.knowledge.types import Mention

logger = logging.getLogger(__name__)

_ensured = False


def _ensure() -> None:
    global _ensured
    if not _ensured:
        schema.ensure_entity_tables()
        _ensured = True


def reset_ensure_cache() -> None:
    """Forget that the schema was ensured. For tests."""
    global _ensured
    _ensured = False


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def save_mentions(
    mentions: Sequence[Mention], *, doc_version: int | None = None
) -> int:
    """Persist a chunk's mentions. Returns rows offered, not rows created.

    ``INSERT IGNORE`` against ``uq_span`` makes repeated extraction a no-op:
    re-running a sweep, retrying a failed run, or re-processing the same chunk
    writes the same rows and creates no duplicates. That is what lets the whole
    pipeline be resumable without a bookkeeping table.
    """
    if not mentions:
        return 0
    _ensure()
    table = state_table()
    now = _now()
    rows = [
        (
            m.chunk_id, m.document_id, doc_version, m.start_offset, m.end_offset,
            m.surface_text[:512], m.normalized_text[:512], m.entity_type,
            m.extraction_method, m.extractor_version, m.confidence, now,
        )
        for m in mentions
    ]
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"INSERT IGNORE INTO `{table}_entity_mention` "
            "(chunk_id, document_id, doc_version, start_offset, end_offset, "
            " surface_text, normalized_text, entity_type, extraction_method, "
            " extractor_version, confidence, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            rows,
        )
        conn.commit()
    return len(rows)


def delete_document_mentions(document_id: str, *, doc_version: int | None = None) -> int:
    """Drop a document's mentions, optionally only one version's.

    Called when a document is re-indexed: chunk ids are version-scoped, so the
    previous version's spans point at text that no longer exists.
    """
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        if doc_version is None:
            cur.execute(
                f"DELETE FROM `{table}_entity_mention` WHERE document_id = %s",
                (document_id,),
            )
        else:
            cur.execute(
                f"DELETE FROM `{table}_entity_mention` "
                "WHERE document_id = %s AND doc_version = %s",
                (document_id, doc_version),
            )
        deleted = cur.rowcount
        conn.commit()
    return deleted


def mentions_for_chunk(chunk_id: str) -> list[dict[str, Any]]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}_entity_mention` WHERE chunk_id = %s "
            "ORDER BY start_offset",
            (chunk_id,),
        )
        return list(cur.fetchall())


def type_counts() -> dict[str, int]:
    """Mentions per entity type. The headline extraction metric."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT entity_type, COUNT(*) AS n FROM `{table}_entity_mention` "
            "GROUP BY entity_type"
        )
        return {r["entity_type"]: int(r["n"]) for r in cur.fetchall()}


def method_counts() -> dict[str, int]:
    """Mentions per extraction method — how much each stage actually earns."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT extraction_method, COUNT(*) AS n "
            f"FROM `{table}_entity_mention` GROUP BY extraction_method"
        )
        return {r["extraction_method"]: int(r["n"]) for r in cur.fetchall()}


# --------------------------------------------------------------------------- #
# Extraction cache
# --------------------------------------------------------------------------- #

def cached_extraction(content_hash: str, extraction_key: str) -> int | None:
    """Mention count for an already-extracted chunk, or None for a miss.

    A stale ``extraction_key`` (new extractor version, or a changed gazetteer)
    reads as a miss, so newer code never reuses output it would not produce.
    """
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT mention_count FROM `{table}_entity_extraction` "
            "WHERE content_hash = %s AND extraction_key = %s",
            (content_hash, extraction_key),
        )
        row = cur.fetchone()
    return int(row["mention_count"]) if row else None


def record_extraction(
    content_hash: str, extraction_key: str, extractor_version: str,
    mention_count: int, *, error: str | None = None,
) -> None:
    """Record that a chunk was extracted (or failed).

    ``attempts`` increments on every write, so a chunk that keeps failing can be
    stopped rather than retried forever — the durable-retry-as-state pattern the
    enrichment and dead-link tables already use, rather than a job queue.
    """
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO `{table}_entity_extraction` "
            "(content_hash, extraction_key, extractor_version, mention_count, "
            " attempts, last_error, updated_at) "
            "VALUES (%s, %s, %s, %s, 1, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "  extraction_key = VALUES(extraction_key), "
            "  extractor_version = VALUES(extractor_version), "
            "  mention_count = VALUES(mention_count), "
            "  attempts = attempts + 1, "
            "  last_error = VALUES(last_error), "
            "  updated_at = VALUES(updated_at)",
            (
                content_hash, extraction_key, extractor_version, mention_count,
                error, _now(),
            ),
        )
        conn.commit()
