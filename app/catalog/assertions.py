"""Read/write path for staged assertions and their rejections.

Staging only. Nothing here reaches Neo4j: projection is a separate pass, so a
graph outage costs a retry rather than a re-extraction, and no transaction spans
two databases.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Sequence

from app.catalog import schema
from app.catalog.db import state_table
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)

_ensured = False


def _ensure() -> None:
    global _ensured
    if not _ensured:
        schema.ensure_assertion_tables()
        _ensured = True


def reset_ensure_cache() -> None:
    global _ensured
    _ensured = False


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def stage(assertions: Sequence[Any]) -> int:
    """Persist validated assertions. Returns rows offered.

    Upserts on ``claim_id``. Because that id covers only what the source states,
    re-extracting the same chunk updates the row's *interpretation* — validity,
    confidence, the quote, the model that read it — while leaving its identity
    alone. That is what makes repeated extraction idempotent without a
    bookkeeping table, and what stops a better prompt forking every claim.

    ``created_at`` is preserved on update so the row still records when the
    claim was first seen.
    """
    _ensure()
    if not assertions:
        return 0
    table = state_table()
    now = _now()
    rows = [
        (
            a.claim_id, a.subject_entity_id, a.predicate, a.object_entity_id,
            (a.object_literal or None), a.document_id, a.chunk_id,
            a.evidence_kind, a.source_field, a.quote, a.quote_start, a.quote_end,
            a.valid_from, a.valid_until, a.temporal_basis, a.confidence,
            a.status, a.extraction_method, a.extractor_version,
            a.vocabulary_version, a.model, a.prompt_version, now, now, now,
        )
        for a in assertions
    ]
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO `{table}_assertion` "
            "(claim_id, subject_entity_id, predicate, object_entity_id, "
            " object_literal, document_id, chunk_id, evidence_kind, source_field, "
            " quote, quote_start, quote_end, valid_from, valid_until, "
            " temporal_basis, confidence, status, extraction_method, "
            " extractor_version, vocabulary_version, model, prompt_version, "
            " asserted_at, created_at, updated_at) "
            "VALUES (" + ",".join(["%s"] * 25) + ") "
            "ON DUPLICATE KEY UPDATE "
            "  quote=VALUES(quote), quote_start=VALUES(quote_start), "
            "  quote_end=VALUES(quote_end), valid_from=VALUES(valid_from), "
            "  valid_until=VALUES(valid_until), "
            "  temporal_basis=VALUES(temporal_basis), "
            "  confidence=VALUES(confidence), status=VALUES(status), "
            "  extraction_method=VALUES(extraction_method), "
            "  extractor_version=VALUES(extractor_version), "
            "  vocabulary_version=VALUES(vocabulary_version), "
            "  model=VALUES(model), prompt_version=VALUES(prompt_version), "
            "  asserted_at=VALUES(asserted_at), updated_at=VALUES(updated_at)",
            rows,
        )
        conn.commit()
    return len(rows)


def record_rejections(rejections: Sequence[Any]) -> int:
    """Append why assertions were refused."""
    _ensure()
    if not rejections:
        return 0
    table = state_table()
    now = _now()
    rows = []
    for rejection in rejections:
        assertion = rejection.assertion
        rows.append((
            rejection.code[:48], (rejection.detail or "")[:255],
            getattr(assertion, "subject_entity_id", None),
            getattr(assertion, "predicate", None),
            getattr(assertion, "document_id", None),
            getattr(assertion, "chunk_id", None),
            getattr(assertion, "extraction_method", None),
            now,
        ))
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO `{table}_assertion_rejection` "
            "(code, detail, subject_entity_id, predicate, document_id, chunk_id, "
            " extraction_method, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            rows,
        )
        conn.commit()
    return len(rows)


def counts_by_predicate() -> dict[str, int]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT predicate, COUNT(*) AS n FROM `{table}_assertion` "
            "WHERE status='active' GROUP BY predicate ORDER BY n DESC"
        )
        return {r["predicate"]: int(r["n"]) for r in cur.fetchall()}


def counts_by_method() -> dict[str, int]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT extraction_method, COUNT(*) AS n FROM `{table}_assertion` "
            "GROUP BY extraction_method"
        )
        return {r["extraction_method"]: int(r["n"]) for r in cur.fetchall()}


def rejection_counts() -> dict[str, int]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT code, COUNT(*) AS n FROM `{table}_assertion_rejection` "
            "GROUP BY code ORDER BY n DESC"
        )
        return {r["code"]: int(r["n"]) for r in cur.fetchall()}


def for_document(document_id: str) -> list[dict[str, Any]]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}_assertion` WHERE document_id = %s "
            "ORDER BY claim_id",
            (document_id,),
        )
        return list(cur.fetchall())


def total() -> int:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM `{table}_assertion`")
        return int(cur.fetchone()["n"])


def clear_all() -> None:
    """Drop every staged assertion. The corpus is re-ingested clean, so
    rebuilding is the supported path and this is how it starts."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"DELETE FROM `{table}_assertion`")
        cur.execute(f"DELETE FROM `{table}_assertion_rejection`")
        conn.commit()
