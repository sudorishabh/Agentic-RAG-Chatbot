"""Ingest-time enrichment cache: LLM-derived per-document output.

Enrichment (currently the document abstract) is expensive to produce and cheap
to store, so it is cached against the content it was derived from and reused
until either that content or the way it is produced changes.

**Keyed by ``content_hash``, not ``document_id``.** Since
``CanonicalDocument.compute_content_hash`` covers body text only, the key is
reproducible from the source bytes alone — so the cache survives a state-table
reset and is shared by documents whose body text is identical. See the DDL in
:mod:`app.catalog.schema` for why that rules out a foreign key.

**Invalidated by version, not TTL.** Enrichment of immutable input does not go
stale, but a changed prompt, schema or model makes it wrong. Callers own what
the version string means (see :mod:`app.ingestion.enrich`); this module stores
it and refuses to serve a mismatch, so a retune self-invalidates in the same way
``cache_keys._pref_fingerprint`` invalidates the semantic cache.

**Failures are recorded, not just dropped.** A document that always fails would
otherwise be retried at full cost on every sweep forever. ``record_failure``
tracks attempts so the caller can stop after a few, while a version change
resets the counter and gives the document a fresh start.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.catalog import schema
from app.catalog.db import now as _now
from app.catalog.db import state_table as _table
from app.core.clients import mysql_connection

__all__ = ["Enrichment", "ensure_table", "get", "put", "record_failure"]


@dataclass
class Enrichment:
    """One cached enrichment result.

    ``abstract`` is None on a row that only records failed attempts — the row
    still exists so ``attempts`` survives across runs.
    """

    content_hash: str
    version: str
    abstract: str | None = None
    attempts: int = 0
    last_error: str | None = None
    updated_at: str | None = None


def ensure_table() -> None:
    schema.ensure_enrichment_table()


def _row_to_enrichment(row: dict) -> Enrichment:
    updated = row.get("updated_at")
    return Enrichment(
        content_hash=row["content_hash"],
        version=row["version"],
        abstract=row.get("abstract"),
        attempts=int(row.get("attempts") or 0),
        last_error=row.get("last_error"),
        updated_at=updated.isoformat() if isinstance(updated, datetime) else updated,
    )


def get(content_hash: str, *, version: str) -> Enrichment | None:
    """The cached row for this content, or None when absent or stale.

    A version mismatch reads as a miss, so a prompt/model change transparently
    re-enriches. Returns the row even when ``abstract`` is None: that is a
    record of prior failed attempts, and the caller needs its ``attempts`` count
    to decide whether to try again.
    """
    if not content_hash:
        return None
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}_enrichment` "
            "WHERE content_hash = %s AND version = %s",
            (content_hash, version),
        )
        row = cur.fetchone()
    return _row_to_enrichment(row) if row else None


def put(content_hash: str, *, version: str, abstract: str) -> None:
    """Store a successful enrichment, clearing any prior failure record."""
    if not content_hash:
        return
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO `{table}_enrichment` "
            "(content_hash, version, abstract, attempts, last_error, updated_at) "
            "VALUES (%s, %s, %s, 0, NULL, %s) "
            "ON DUPLICATE KEY UPDATE "
            "  version = VALUES(version),"
            "  abstract = VALUES(abstract),"
            "  attempts = 0,"
            "  last_error = NULL,"
            "  updated_at = VALUES(updated_at)",
            (content_hash, version, abstract, _now()),
        )
        conn.commit()


def record_failure(content_hash: str, *, version: str, error: str) -> None:
    """Count a failed attempt so a hopeless document stops being retried.

    A row already at this version increments; a row at another version restarts
    at 1, because a new prompt or model deserves a fresh attempt budget. The
    assignment order below matters: ``attempts`` reads the *stored* version, so
    it has to be evaluated before ``version`` is overwritten (MySQL applies
    ON DUPLICATE KEY assignments left to right).
    """
    if not content_hash:
        return
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO `{table}_enrichment` "
            "(content_hash, version, abstract, attempts, last_error, updated_at) "
            "VALUES (%s, %s, NULL, 1, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "  attempts = IF(version = VALUES(version), attempts + 1, 1),"
            "  version = VALUES(version),"
            "  last_error = VALUES(last_error),"
            "  updated_at = VALUES(updated_at)",
            (content_hash, version, error[:1000], _now()),
        )
        conn.commit()
