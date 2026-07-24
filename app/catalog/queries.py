"""Retrieval-facing analytical reads over the document catalog.

Everything here is SELECT-only over the ingest-state tables (see
:mod:`app.catalog.schema` for DDL, :mod:`app.catalog.state` for the write
path). Two families live in this one module because they share the same
filter-building logic and table:

- ``count_documents`` / ``list_documents`` / ``distribution`` answer the
  structured (database-intent) catalog tools;
- ``document_ids_in_scope`` / ``attachments_for`` answer id-scoped retrieval
  (scoped summarization, website-attachment supplementation) — these bake in
  ``source_type='website', entity_type='node'`` since that's the retrieval
  layer's catalog of record.

DB errors fail open: the count/list/distribution functions let real errors
raise (callers already guard), while the id-scope helpers below swallow errors
and return empty, so a MySQL outage degrades retrieval instead of failing it.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Sequence

from app.catalog.db import state_table as _table
from app.catalog.state import StateRecord, _row_to_record
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)


def _like(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _catalog_filters(
    source_type: str | None,
    bundle: str | None,
    *,
    entity_type: str | None = None,
    title_contains: str | None = None,
    author: str | None = None,
    term_uuids: Sequence[str] | None = None,
    theme: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
) -> tuple[str, list[str], list[Any], bool]:
    """Shared JOIN/WHERE assembly for the catalog count/list queries.

    ``entity_type`` scopes to one Drupal entity kind — the query layer passes
    "node" so taxonomy-term and block rows never count as content documents.
    ``term_uuids`` scopes by taxonomy links (rename-proof); ``theme`` is the
    display-name fallback for documents ingested before the term catalog.
    Returns (joins, clauses, params, needs_distinct)."""
    table = _table()
    joins: list[str] = []
    clauses: list[str] = []
    params: list[Any] = []
    distinct = False
    if source_type is not None:
        clauses.append("s.source_type = %s")
        params.append(source_type)
    if bundle is not None:
        clauses.append("s.bundle = %s")
        params.append(bundle)
    if entity_type is not None:
        clauses.append("s.entity_type = %s")
        params.append(entity_type)
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
    elif theme:
        joins.append(f" JOIN `{table}_theme` c ON c.document_id = s.document_id")
        clauses.append("c.theme LIKE %s")
        params.append(_like(theme))
        distinct = True
    return "".join(joins), clauses, params, distinct


def count_documents(
    source_type: str | None = None,
    bundle: str | None = None,
    *,
    entity_type: str | None = None,
    author: str | None = None,
    term_uuids: Sequence[str] | None = None,
    theme: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
) -> int:
    """Count catalog documents (not chunks) matching the given filters.

    ``author``/``theme`` match substrings against their facets; ``term_uuids``
    scopes by taxonomy links and wins over ``theme``. Date bounds are a
    half-open ``[from, to)`` interval over ``published_at``."""
    table = _table()
    joins, clauses, params, distinct = _catalog_filters(
        source_type, bundle, entity_type=entity_type,
        author=author, term_uuids=term_uuids, theme=theme,
        published_from=published_from, published_to=published_to,
    )
    count_expr = "COUNT(DISTINCT s.document_id)" if distinct else "COUNT(*)"
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT {count_expr} AS n FROM `{table}` s{joins}{where}"
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
    return int(row["n"]) if row and row["n"] is not None else 0


def list_documents(
    source_type: str | None = None,
    bundle: str | None = None,
    *,
    entity_type: str | None = None,
    title_contains: str | None = None,
    author: str | None = None,
    term_uuids: Sequence[str] | None = None,
    theme: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 10,
) -> list[StateRecord]:
    """List catalog documents matching the filters, most recent first.

    Mirrors ``count_documents`` but returns the matching rows so structured
    list/lookup queries are answered from the local catalog instead of a live
    site fetch. ``limit`` is clamped to [1, 100]."""
    table = _table()
    joins, clauses, params, needs_distinct = _catalog_filters(
        source_type, bundle, entity_type=entity_type,
        title_contains=title_contains, author=author,
        term_uuids=term_uuids, theme=theme,
        published_from=published_from, published_to=published_to,
    )
    distinct = "DISTINCT " if needs_distinct else ""
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    capped = max(1, min(int(limit or 10), 100))
    sql = (
        f"SELECT {distinct}s.* FROM `{table}` s{joins}{where} "
        f"ORDER BY s.published_at DESC, s.document_id ASC LIMIT {capped}"
    )
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        return [_row_to_record(row) for row in cur.fetchall()]


# Dimensions the distribution query can group by. "theme" and "author" use
# the facet tables (the rename refresh keeps theme values canonical);
# "bundle" and "year" come off the document row itself.
_DISTRIBUTION_DIMENSIONS = ("bundle", "author", "theme", "year")


def distribution(
    group_by: str,
    source_type: str | None = "website",
    bundle: str | None = None,
    *,
    entity_type: str | None = None,
    author: str | None = None,
    term_uuids: Sequence[str] | None = None,
    theme: str | None = None,
    title_contains: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 20,
) -> list[tuple[str, int]]:
    """Grouped document counts ("how many per theme/type/author/year"),
    largest group first. Returns (group value, count) pairs.

    Applies the same theme/author/title/date scope as ``count_documents`` and
    ``list_documents`` (via :func:`_catalog_filters`), so a breakdown can be
    narrowed to one theme, author, period, etc. A document that fans out across
    a facet join is counted once per group."""
    if group_by not in _DISTRIBUTION_DIMENSIONS:
        raise ValueError(f"group_by must be one of {_DISTRIBUTION_DIMENSIONS}")
    table = _table()
    scope_joins, clauses, params, scoped = _catalog_filters(
        source_type, bundle, entity_type=entity_type,
        title_contains=title_contains, author=author,
        term_uuids=term_uuids, theme=theme,
        published_from=published_from, published_to=published_to,
    )

    if group_by == "bundle":
        group_join, key = "", "s.bundle"
    elif group_by == "year":
        group_join, key = "", "YEAR(s.published_at)"
        clauses.append("s.published_at IS NOT NULL")
    else:
        group_join = f" JOIN `{table}_{group_by}` f ON f.document_id = s.document_id"
        key = f"f.{group_by}"

    # A facet join — from the scope filters or the group key itself — can repeat
    # a document across rows, so count distinct documents unless the query stays
    # purely on the document row (bundle/year with no scoped join).
    count_expr = (
        "COUNT(*)"
        if group_by in ("bundle", "year") and not scoped
        else "COUNT(DISTINCT s.document_id)"
    )
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    capped = max(1, min(int(limit or 20), 100))
    sql = (
        f"SELECT {key} AS k, {count_expr} AS n "
        f"FROM `{table}` s{scope_joins}{group_join}{where} "
        f"GROUP BY k ORDER BY n DESC, k ASC LIMIT {capped}"
    )
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    return [(str(row["k"]), int(row["n"])) for row in rows if row["k"] is not None]


# --------------------------------------------------------------------------- #
# Id-scoped reads for retrieval (scoped summarization, attachment
# supplementation). Website nodes (source_type='website', entity_type='node')
# are baked in as the catalog of record; DB errors fail open to empty results
# so callers degrade to the plain semantic pipeline.
# --------------------------------------------------------------------------- #

def document_ids_in_scope(
    *,
    bundle: str | None = None,
    term_uuids: Sequence[str] | None = None,
    theme: str | None = None,
    author: str | None = None,
    title_contains: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 150,
) -> list[str]:
    """Document ids matching a metadata scope, most recent first.

    The id-set selection behind catalog-scoped retrieval: MySQL decides set
    membership, Qdrant ranks content within it. ``term_uuids`` wins over the
    ``theme`` display-name fallback. ``limit`` clamps to [1, 300] — honest
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
    elif theme:
        joins.append(f" JOIN `{table}_theme` c ON c.document_id = s.document_id")
        clauses.append("c.theme LIKE %s")
        params.append(_like(theme))
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
