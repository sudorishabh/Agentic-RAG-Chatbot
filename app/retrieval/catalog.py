"""Read-only MySQL catalog readers for the retrieval layer.

Query needs that ``app.ingestion.state`` lacks live here — the ingestion
freeze forbids editing that module, not querying the same tables. Everything
is SELECT-only over ``ingest_state*`` via a closed set of parameterized
templates; website nodes (source_type='website', entity_type='node') are the
catalog of record and are baked into every query. DB errors fail open to
empty results — callers degrade to the plain semantic pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Sequence

from app.config import get_settings
from app.deps import mysql_connection

logger = logging.getLogger(__name__)


def _table() -> str:
    """Whitelisted table identifier (mirrors the guard in ``state._table``)."""
    name = get_settings().ingest_state_table
    return name if name.replace("_", "").isalnum() else "ingest_state"


def _like(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def document_ids_in_scope(
    *,
    bundle: str | None = None,
    term_uuids: Sequence[str] | None = None,
    category: str | None = None,
    author: str | None = None,
    title_contains: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 150,
) -> list[str]:
    """Document ids matching a metadata scope, most recent first.

    The id-set selection behind catalog-scoped retrieval: MySQL decides set
    membership, Qdrant ranks content within it. ``term_uuids`` wins over the
    ``category`` display-name fallback. ``limit`` clamps to [1, 300] — honest
    truncation beats an unbounded MatchAny downstream.
    """
    table = _table()
    joins: list[str] = []
    clauses = ["s.source_type = %s", "s.entity_type = %s"]
    params: list[Any] = ["website", "node"]
    distinct = False
    if bundle is not None:
        clauses.append("s.bundle = %s")
        params.append(bundle)
    if title_contains:
        clauses.append("s.title LIKE %s")
        params.append(_like(title_contains))
    if published_from is not None:
        clauses.append("s.published_at >= %s")
        params.append(published_from)
    if published_to is not None:
        clauses.append("s.published_at < %s")
        params.append(published_to)
    if author:
        joins.append(f" JOIN `{table}_author` a ON a.document_id = s.document_id")
        clauses.append("a.author LIKE %s")
        params.append(_like(author))
        distinct = True
    if term_uuids:
        placeholders = ", ".join(["%s"] * len(term_uuids))
        joins.append(f" JOIN `{table}_term` dt ON dt.document_id = s.document_id")
        clauses.append(f"dt.term_uuid IN ({placeholders})")
        params.extend(term_uuids)
        distinct = True
    elif category:
        joins.append(f" JOIN `{table}_category` c ON c.document_id = s.document_id")
        clauses.append("c.category LIKE %s")
        params.append(_like(category))
        distinct = True

    # published_at is selected alongside the id: MySQL rejects DISTINCT with
    # an ORDER BY column that is not in the select list.
    select = "SELECT DISTINCT" if distinct else "SELECT"
    capped = max(1, min(int(limit or 150), 300))
    sql = (
        f"{select} s.document_id, s.published_at FROM `{table}` s{''.join(joins)}"
        f" WHERE {' AND '.join(clauses)}"
        f" ORDER BY s.published_at DESC, s.document_id ASC LIMIT {capped}"
    )
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return [row["document_id"] for row in cur.fetchall()]
    except Exception:
        logger.warning("Catalog id-scope query failed.", exc_info=True)
        return []


def authors_matching(fragment: str, limit: int = 10) -> list[str]:
    """Distinct author facet values matching a name fragment (disambiguation)."""
    if not fragment or not fragment.strip():
        return []
    table = _table()
    capped = max(1, min(int(limit or 10), 50))
    sql = (
        f"SELECT DISTINCT author FROM `{table}_author`"
        f" WHERE author LIKE %s ORDER BY author ASC LIMIT {capped}"
    )
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, (_like(fragment.strip()),))
            return [row["author"] for row in cur.fetchall()]
    except Exception:
        logger.warning("Catalog author lookup failed.", exc_info=True)
        return []


def attachments_for(document_ids: Sequence[str]) -> dict[str, list[dict[str, Any]]]:
    """Attachment rows keyed by document_id — the website→PDF supplementation
    join. Each row: {file_uuid, origin, url, filename}."""
    ids = [d for d in document_ids if d]
    if not ids:
        return {}
    table = _table()
    placeholders = ", ".join(["%s"] * len(ids))
    sql = (
        f"SELECT document_id, file_uuid, origin, url, filename"
        f" FROM `{table}_attachment` WHERE document_id IN ({placeholders})"
    )
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(ids))
            rows = cur.fetchall()
    except Exception:
        logger.warning("Catalog attachment lookup failed.", exc_info=True)
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        out.setdefault(row["document_id"], []).append(
            {
                "file_uuid": row["file_uuid"],
                "origin": row["origin"],
                "url": row["url"],
                "filename": row["filename"],
            }
        )
    return out


# Dimensions mirroring state.distribution: facet tables for author/category,
# the document row for bundle/year.
_DISTRIBUTION_DIMENSIONS = ("bundle", "author", "category", "year")


def distribution_scoped(
    group_by: str,
    *,
    term_uuids: Sequence[str],
    bundle: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 20,
) -> list[tuple[str, int]]:
    """Grouped document counts within a taxonomy-term scope — the term-uuid
    join ``state.distribution`` lacks. Largest group first."""
    if group_by not in _DISTRIBUTION_DIMENSIONS:
        raise ValueError(f"group_by must be one of {_DISTRIBUTION_DIMENSIONS}")
    if not term_uuids:
        return []
    table = _table()
    placeholders = ", ".join(["%s"] * len(term_uuids))
    joins = [f" JOIN `{table}_term` dt ON dt.document_id = s.document_id"]
    clauses = [
        "s.source_type = %s",
        "s.entity_type = %s",
        f"dt.term_uuid IN ({placeholders})",
    ]
    params: list[Any] = ["website", "node", *term_uuids]
    if bundle is not None:
        clauses.append("s.bundle = %s")
        params.append(bundle)
    if published_from is not None:
        clauses.append("s.published_at >= %s")
        params.append(published_from)
    if published_to is not None:
        clauses.append("s.published_at < %s")
        params.append(published_to)

    if group_by == "bundle":
        key = "s.bundle"
    elif group_by == "year":
        key = "YEAR(s.published_at)"
        clauses.append("s.published_at IS NOT NULL")
    else:
        joins.append(f" JOIN `{table}_{group_by}` f ON f.document_id = s.document_id")
        key = f"f.{group_by}"

    capped = max(1, min(int(limit or 20), 100))
    sql = (
        f"SELECT {key} AS k, COUNT(DISTINCT s.document_id) AS n"
        f" FROM `{table}` s{''.join(joins)}"
        f" WHERE {' AND '.join(clauses)}"
        f" GROUP BY k ORDER BY n DESC, k ASC LIMIT {capped}"
    )
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    except Exception:
        logger.warning("Catalog scoped distribution failed.", exc_info=True)
        return []
    return [(str(row["k"]), int(row["n"])) for row in rows if row["k"] is not None]
