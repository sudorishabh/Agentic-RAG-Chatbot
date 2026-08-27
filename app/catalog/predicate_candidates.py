"""Read/write path for pending relationship candidates.

Staging only, like ``app.catalog.assertions`` — and rather more strictly:
nothing here ever reaches Neo4j, and there is no code path that could take it
there. A candidate names a predicate outside the closed vocabulary, and
``app.knowledge.graph.writer.safe_relationship`` raises for exactly those, so
the refusal is structural rather than a matter of this module's discipline.

See :mod:`app.knowledge.claims.pending` for what a candidate is and why the
evidence is kept.
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
        schema.ensure_predicate_candidate_table()
        _ensured = True


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def record(candidates: Sequence[Any]) -> int:
    """Persist pending candidates. Returns rows offered.

    Upserts on ``candidate_id``, so a retry does not duplicate. ``observations``
    increments on each write and ``first_seen_at`` is preserved: the row then
    says both when this evidence first proposed the predicate and how many times
    it has been read since, which is what distinguishes a one-off model slip
    from a phrasing the corpus keeps producing.

    ``status`` is deliberately **not** updated. An operator who rejected a
    candidate must not have that verdict undone by the next sweep re-observing
    the same sentence.
    """
    _ensure()
    if not candidates:
        return 0
    table = state_table()
    now = _now()
    rows = [
        (
            c.candidate_id, c.predicate_surface, c.predicate_normalized,
            c.subject_entity_id, c.object_entity_id, c.object_literal,
            c.document_id, c.chunk_id, c.evidence_kind,
            c.quote, c.quote_start, c.quote_end, c.confidence,
            c.extraction_method, c.extractor_version, c.vocabulary_version,
            c.model, c.prompt_version, c.status, now, now,
        )
        for c in candidates
    ]
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO `{table}_predicate_candidate` "
            "(candidate_id, predicate_surface, predicate_normalized, "
            " subject_entity_id, object_entity_id, object_literal, "
            " document_id, chunk_id, evidence_kind, quote, quote_start, "
            " quote_end, confidence, extraction_method, extractor_version, "
            " vocabulary_version, model, prompt_version, status, "
            " first_seen_at, last_seen_at) "
            "VALUES (" + ",".join(["%s"] * 21) + ") "
            "ON DUPLICATE KEY UPDATE "
            "  predicate_surface=VALUES(predicate_surface), "
            "  quote=VALUES(quote), quote_start=VALUES(quote_start), "
            "  quote_end=VALUES(quote_end), confidence=VALUES(confidence), "
            "  extraction_method=VALUES(extraction_method), "
            "  extractor_version=VALUES(extractor_version), "
            "  vocabulary_version=VALUES(vocabulary_version), "
            "  model=VALUES(model), prompt_version=VALUES(prompt_version), "
            "  observations=observations + 1, "
            "  last_seen_at=VALUES(last_seen_at)",
            rows,
        )
        conn.commit()
    return len(rows)


def pending(limit: int = 100) -> list[dict[str, Any]]:
    """Candidates awaiting a vocabulary decision, most-proposed first."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}_predicate_candidate` "
            "WHERE status='pending' ORDER BY observations DESC, last_seen_at DESC "
            "LIMIT %s",
            (int(limit),),
        )
        return list(cur.fetchall())


def for_document(document_id: str) -> list[dict[str, Any]]:
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}_predicate_candidate` WHERE document_id=%s "
            "ORDER BY candidate_id",
            (document_id,),
        )
        return list(cur.fetchall())


def clear_all() -> None:
    """Drop every candidate. Rebuildable like the rest of the layer."""
    _ensure()
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"DELETE FROM `{table}_predicate_candidate`")
        conn.commit()
