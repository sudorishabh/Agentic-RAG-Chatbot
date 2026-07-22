"""Ingest-state write model: the document catalog's source of truth.

Schema/migrations live in :mod:`app.catalog.schema`; the retrieval-facing
analytical reads (count/list/distribution) live in :mod:`app.catalog.queries`.
This module owns the per-document write path (upsert / delete / facet & link
replacement) and the handful of point reads ingestion itself needs.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Iterable

from app.catalog import schema
from app.catalog.db import now as _now
from app.catalog.db import state_table as _table
from app.catalog.models import AttachmentLink, StateRecord, TermLink
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)

__all__ = [
    "AttachmentLink",
    "StateRecord",
    "TermLink",
    "ensure_table",
    "load",
    "get",
    "upsert",
    "update_stat",
    "delete",
    "backfill_facets",
    "documents_for_term",
    "rename_category_facet",
]


def ensure_table() -> None:
    schema.ensure_state_table()


def _to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def _replace_facet(
    cur: Any, table: str, facet: str, document_id: str, values: Iterable[str]
) -> None:
    cur.execute(f"DELETE FROM `{table}_{facet}` WHERE document_id = %s", (document_id,))
    rows = [(document_id, v[:255]) for v in dict.fromkeys(x for x in values if x)]
    if rows:
        cur.executemany(
            f"INSERT INTO `{table}_{facet}` (document_id, {facet}) VALUES (%s, %s)", rows
        )


def _replace_term_links(
    cur: Any, table: str, document_id: str, links: Iterable[TermLink]
) -> None:
    cur.execute(f"DELETE FROM `{table}_term` WHERE document_id = %s", (document_id,))
    rows = list(
        dict.fromkeys(
            (document_id, l.term_uuid, l.role[:128]) for l in links if l.term_uuid
        )
    )
    if rows:
        cur.executemany(
            f"INSERT INTO `{table}_term` (document_id, term_uuid, role) "
            "VALUES (%s, %s, %s)",
            rows,
        )


def _replace_attachment_links(
    cur: Any, table: str, document_id: str, links: Iterable[AttachmentLink]
) -> None:
    cur.execute(f"DELETE FROM `{table}_attachment` WHERE document_id = %s", (document_id,))
    # First link wins per file: an explicit attachment ref carries url/filename
    # and outranks a later in-body sighting of the same PDF.
    seen: dict[str, AttachmentLink] = {}
    for link in links:
        if link.file_uuid and link.file_uuid not in seen:
            seen[link.file_uuid] = link
    rows = [
        (l.file_uuid, document_id, l.origin[:16], l.url, l.filename)
        for l in seen.values()
    ]
    if rows:
        cur.executemany(
            f"INSERT INTO `{table}_attachment` "
            "(file_uuid, document_id, origin, url, filename) "
            "VALUES (%s, %s, %s, %s, %s)",
            rows,
        )


def _row_to_record(row: dict) -> StateRecord:
    indexed = row.get("indexed_at")
    published = row.get("published_at")
    return StateRecord(
        document_id=row["document_id"],
        source_type=row["source_type"],
        source_key=row["source_key"],
        fingerprint=row["fingerprint"],
        content_hash=row.get("content_hash") or "",
        doc_version=int(row.get("doc_version") or 1),
        bundle=row.get("bundle"),
        entity_type=row.get("entity_type"),
        changed_mark=row.get("changed_mark"),
        size=row.get("size"),
        mtime_ns=row.get("mtime_ns"),
        title=row.get("title"),
        url=row.get("url"),
        indexed_at=indexed.isoformat() if isinstance(indexed, datetime) else indexed,
        published_at=published.isoformat() if isinstance(published, datetime) else published,
    )


def load(source_type: str) -> dict[str, StateRecord]:
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}` WHERE source_type = %s", (source_type,)
        )
        return {row["document_id"]: _row_to_record(row) for row in cur.fetchall()}


def get(document_id: str) -> StateRecord | None:
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{table}` WHERE document_id = %s", (document_id,)
        )
        row = cur.fetchone()
    return _row_to_record(row) if row else None


def upsert(record: StateRecord, *, mark_indexed: bool = True) -> None:
    table = _table()
    now = _now()
    indexed_at = now if mark_indexed else None
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO `{table}`
                (document_id, source_type, source_key, bundle, entity_type,
                 fingerprint, content_hash, doc_version, changed_mark, size,
                 mtime_ns, published_at, title, url, raw_meta, indexed_at,
                 updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                source_type  = VALUES(source_type),
                source_key   = VALUES(source_key),
                bundle       = VALUES(bundle),
                entity_type  = COALESCE(VALUES(entity_type), entity_type),
                fingerprint  = VALUES(fingerprint),
                content_hash = VALUES(content_hash),
                doc_version  = VALUES(doc_version),
                changed_mark = VALUES(changed_mark),
                size         = VALUES(size),
                mtime_ns     = VALUES(mtime_ns),
                published_at = VALUES(published_at),
                title        = VALUES(title),
                url          = VALUES(url),
                raw_meta     = COALESCE(VALUES(raw_meta), raw_meta),
                indexed_at   = COALESCE(VALUES(indexed_at), indexed_at),
                updated_at   = VALUES(updated_at)
            """,
            (
                record.document_id,
                record.source_type,
                record.source_key,
                record.bundle,
                record.entity_type,
                record.fingerprint,
                record.content_hash,
                record.doc_version,
                record.changed_mark,
                record.size,
                record.mtime_ns,
                _to_datetime(record.published_at),
                record.title,
                record.url,
                json.dumps(record.raw_meta, ensure_ascii=False, default=str)
                if record.raw_meta is not None
                else None,
                indexed_at,
                now,
            ),
        )
        _replace_facet(cur, table, "author", record.document_id, record.authors)
        _replace_facet(cur, table, "category", record.document_id, record.categories)
        _replace_term_links(cur, table, record.document_id, record.term_links)
        _replace_attachment_links(cur, table, record.document_id, record.attachments)
        conn.commit()


def update_stat(document_id: str, size: int | None, mtime_ns: int | None) -> None:
    """Refresh only the cheap change-detection stat (size + mtime) for a document
    whose content is unchanged, so a later scan can skip re-hashing it after a
    metadata-only touch."""
    if size is None and mtime_ns is None:
        return
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE `{table}` SET size = %s, mtime_ns = %s WHERE document_id = %s",
            (size, mtime_ns, document_id),
        )
        conn.commit()


def delete(document_ids: Iterable[str]) -> int:
    ids = [d for d in document_ids if d]
    if not ids:
        return 0
    table = _table()
    placeholders = ", ".join(["%s"] * len(ids))
    with mysql_connection() as conn, conn.cursor() as cur:
        removed = cur.execute(
            f"DELETE FROM `{table}` WHERE document_id IN ({placeholders})", tuple(ids)
        )
        conn.commit()
    return int(removed or 0)


def backfill_facets(
    document_id: str,
    published_at: str | None,
    authors: Iterable[str],
    categories: Iterable[str],
    *,
    title: str | None = None,
    url: str | None = None,
) -> bool:
    """Set the date/author/category facets (and optionally title/url) for an
    already-cataloged document (e.g. one indexed before these columns existed).
    title/url only overwrite when a value is supplied (COALESCE), so rows already
    populated at ingest are left intact. Returns False when no catalog row exists
    for the id, leaving child rows untouched (FK safety)."""
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT 1 FROM `{table}` WHERE document_id = %s", (document_id,))
        if cur.fetchone() is None:
            return False
        cur.execute(
            f"UPDATE `{table}` SET published_at = %s, "
            f"title = COALESCE(%s, title), url = COALESCE(%s, url) "
            f"WHERE document_id = %s",
            (_to_datetime(published_at), title, url, document_id),
        )
        _replace_facet(cur, table, "author", document_id, authors)
        _replace_facet(cur, table, "category", document_id, categories)
        conn.commit()
    return True


def documents_for_term(term_uuid: str) -> list[str]:
    """Document ids linked to a taxonomy term (any role)."""
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT DISTINCT document_id FROM `{table}_term` WHERE term_uuid = %s",
            (term_uuid,),
        )
        return [row["document_id"] for row in cur.fetchall()]


def rename_category_facet(document_id: str, old: str, new: str) -> list[str]:
    """Replace ``old`` with ``new`` in a document's category facet, collapsing
    duplicates; returns the resulting category list (payload-refresh input)."""
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT category FROM `{table}_category` WHERE document_id = %s",
            (document_id,),
        )
        categories = [row["category"] for row in cur.fetchall()]
        updated = list(dict.fromkeys(new if c == old else c for c in categories))
        if updated != categories:
            _replace_facet(cur, table, "category", document_id, updated)
            conn.commit()
    return updated
