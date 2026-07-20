from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

from app.config import get_settings
from app.deps import mysql_connection

logger = logging.getLogger(__name__)


@dataclass
class TermLink:
    """A document's reference to a taxonomy term. ``role`` is the referencing
    Drupal field (field_theme, field_tags, parent, ...), so queries can
    distinguish a theme link from a tag link on the same term."""

    term_uuid: str
    role: str


@dataclass
class AttachmentLink:
    """A node's link to an attached PDF (its own document, keyed by file_uuid)."""

    file_uuid: str
    origin: str  # "attachment" | "inbody"
    url: str | None = None
    filename: str | None = None


@dataclass
class StateRecord:

    document_id: str
    source_type: str
    source_key: str
    fingerprint: str
    content_hash: str = ""
    doc_version: int = 1
    bundle: str | None = None
    # JSON:API entity type ("node", "taxonomy_term", "block_content") for
    # Drupal records; None for filesystem PDFs and attachment documents.
    # Content counts filter on it so facet terms don't count as documents.
    entity_type: str | None = None
    changed_mark: int | None = None
    # Cheap file-change signal for local PDFs: byte size + mtime (ns). Lets a scan
    # skip re-reading/hashing a file whose size and mtime are unchanged.
    size: int | None = None
    mtime_ns: int | None = None
    indexed_at: str | None = None
    published_at: str | None = None
    # Display fields so structured list/lookup queries can be answered from the
    # catalog (no live site fetch). url is the document's public page/file URL.
    title: str | None = None
    url: str | None = None
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    # Entity-modeled links and the lossless source metadata (JSON column).
    term_links: list[TermLink] = field(default_factory=list)
    attachments: list[AttachmentLink] = field(default_factory=list)
    raw_meta: dict[str, Any] | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _table() -> str:
    name = get_settings().ingest_state_table
    return name if name.replace("_", "").isalnum() else "ingest_state"


_DDL = """
CREATE TABLE IF NOT EXISTS `{table}` (
    document_id  VARCHAR(255)  NOT NULL,
    source_type  VARCHAR(32)   NOT NULL,
    source_key   VARCHAR(1024) NOT NULL,
    bundle       VARCHAR(128)  NULL,
    entity_type  VARCHAR(32)   NULL,
    fingerprint  VARCHAR(128)  NOT NULL,
    content_hash VARCHAR(64)   NOT NULL DEFAULT '',
    doc_version  INT           NOT NULL DEFAULT 1,
    changed_mark BIGINT        NULL,
    size         BIGINT        NULL,
    mtime_ns     BIGINT        NULL,
    published_at DATETIME      NULL,
    title        VARCHAR(1024) NULL,
    url          VARCHAR(1024) NULL,
    indexed_at   DATETIME      NULL,
    updated_at   DATETIME      NOT NULL,
    PRIMARY KEY (document_id),
    KEY idx_source_type (source_type),
    KEY idx_bundle (source_type, bundle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

# Multi-valued facets stored one row per (document, value) so they count exactly
# via COUNT(DISTINCT document_id). Rows cascade-delete with their parent.
_FACETS: tuple[str, ...] = ("author", "category")

_CHILD_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_{facet}` (
    document_id VARCHAR(255) NOT NULL,
    {facet}     VARCHAR(255) NOT NULL,
    KEY idx_doc (document_id),
    KEY idx_val ({facet}),
    CONSTRAINT `fk_{table}_{facet}` FOREIGN KEY (document_id)
        REFERENCES `{table}` (document_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

# Document -> taxonomy term links, joined on term_uuid (rename-proof; the
# term's name/hierarchy live in the taxonomy_term table, see terms.py).
_TERM_LINK_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_term` (
    document_id VARCHAR(255) NOT NULL,
    term_uuid   VARCHAR(64)  NOT NULL,
    role        VARCHAR(128) NOT NULL,
    PRIMARY KEY (document_id, term_uuid, role),
    KEY idx_term (term_uuid),
    CONSTRAINT `fk_{table}_term` FOREIGN KEY (document_id)
        REFERENCES `{table}` (document_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

# Node -> attached PDF links. Composite key: one in-body PDF can be linked
# from several nodes. The PDF's own catalog row is keyed by file_uuid.
_ATTACHMENT_LINK_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_attachment` (
    file_uuid   VARCHAR(255)  NOT NULL,
    document_id VARCHAR(255)  NOT NULL,
    origin      VARCHAR(16)   NOT NULL,
    url         VARCHAR(1024) NULL,
    filename    VARCHAR(255)  NULL,
    PRIMARY KEY (file_uuid, document_id),
    KEY idx_doc (document_id),
    CONSTRAINT `fk_{table}_attachment` FOREIGN KEY (document_id)
        REFERENCES `{table}` (document_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def _to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def _ensure_column(cur: Any, table: str, column: str, ddl: str) -> None:
    """Add a column to an existing table only if it is missing (idempotent
    migration for deployments created before the column existed)."""
    cur.execute(
        "SELECT 1 FROM information_schema.COLUMNS "
        "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
        (table, column),
    )
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN {ddl}")


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


def ensure_table() -> None:
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_DDL.format(table=table))
        _ensure_column(cur, table, "published_at", "published_at DATETIME NULL")
        _ensure_column(cur, table, "size", "size BIGINT NULL")
        _ensure_column(cur, table, "mtime_ns", "mtime_ns BIGINT NULL")
        _ensure_column(cur, table, "title", "title VARCHAR(1024) NULL")
        _ensure_column(cur, table, "url", "url VARCHAR(1024) NULL")
        _ensure_column(cur, table, "raw_meta", "raw_meta JSON NULL")
        _ensure_column(cur, table, "entity_type", "entity_type VARCHAR(32) NULL")
        for facet in _FACETS:
            cur.execute(_CHILD_DDL.format(table=table, facet=facet))
        cur.execute(_TERM_LINK_DDL.format(table=table))
        cur.execute(_ATTACHMENT_LINK_DDL.format(table=table))
        conn.commit()


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


def high_water(source_type: str, bundle: str | None = None) -> int | None:
    table = _table()
    sql = f"SELECT MAX(changed_mark) AS hw FROM `{table}` WHERE source_type = %s"
    params: tuple = (source_type,)
    if bundle is not None:
        sql += " AND bundle = %s"
        params += (bundle,)
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return int(row["hw"]) if row and row["hw"] is not None else None


def keys(source_type: str, bundle: str | None = None) -> set[str]:
    table = _table()
    sql = f"SELECT document_id FROM `{table}` WHERE source_type = %s"
    params: tuple = (source_type,)
    if bundle is not None:
        sql += " AND bundle = %s"
        params += (bundle,)
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return {row["document_id"] for row in cur.fetchall()}


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
    category: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
) -> tuple[str, list[str], list[Any], bool]:
    """Shared JOIN/WHERE assembly for the catalog count/list queries.

    ``entity_type`` scopes to one Drupal entity kind — the query layer passes
    "node" so taxonomy-term and block rows never count as content documents.
    ``term_uuids`` scopes by taxonomy links (rename-proof); ``category`` is the
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
    elif category:
        joins.append(f" JOIN `{table}_category` c ON c.document_id = s.document_id")
        clauses.append("c.category LIKE %s")
        params.append(_like(category))
        distinct = True
    return "".join(joins), clauses, params, distinct


def count_documents(
    source_type: str | None = None,
    bundle: str | None = None,
    *,
    entity_type: str | None = None,
    author: str | None = None,
    term_uuids: Sequence[str] | None = None,
    category: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
) -> int:
    """Count catalog documents (not chunks) matching the given filters.

    ``author``/``category`` match substrings against their facets; ``term_uuids``
    scopes by taxonomy links and wins over ``category``. Date bounds are a
    half-open ``[from, to)`` interval over ``published_at``."""
    table = _table()
    joins, clauses, params, distinct = _catalog_filters(
        source_type, bundle, entity_type=entity_type,
        author=author, term_uuids=term_uuids, category=category,
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
    category: str | None = None,
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
        term_uuids=term_uuids, category=category,
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


# Dimensions the distribution query can group by. "category" and "author" use
# the facet tables (the rename refresh keeps category values canonical);
# "bundle" and "year" come off the document row itself.
_DISTRIBUTION_DIMENSIONS = ("bundle", "author", "category", "year")


def distribution(
    group_by: str,
    source_type: str | None = "website",
    bundle: str | None = None,
    *,
    entity_type: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 20,
) -> list[tuple[str, int]]:
    """Grouped document counts ("how many per theme/type/author/year"),
    largest group first. Returns (group value, count) pairs."""
    if group_by not in _DISTRIBUTION_DIMENSIONS:
        raise ValueError(f"group_by must be one of {_DISTRIBUTION_DIMENSIONS}")
    table = _table()
    clauses: list[str] = []
    params: list[Any] = []
    if source_type is not None:
        clauses.append("s.source_type = %s")
        params.append(source_type)
    if bundle is not None:
        clauses.append("s.bundle = %s")
        params.append(bundle)
    if entity_type is not None:
        clauses.append("s.entity_type = %s")
        params.append(entity_type)
    if published_from is not None:
        clauses.append("s.published_at >= %s")
        params.append(published_from)
    if published_to is not None:
        clauses.append("s.published_at < %s")
        params.append(published_to)

    joins = ""
    if group_by == "bundle":
        key, count_expr = "s.bundle", "COUNT(*)"
    elif group_by == "year":
        key, count_expr = "YEAR(s.published_at)", "COUNT(*)"
        clauses.append("s.published_at IS NOT NULL")
    else:
        joins = f" JOIN `{table}_{group_by}` f ON f.document_id = s.document_id"
        key, count_expr = f"f.{group_by}", "COUNT(DISTINCT s.document_id)"

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    capped = max(1, min(int(limit or 20), 100))
    sql = (
        f"SELECT {key} AS k, {count_expr} AS n FROM `{table}` s{joins}{where} "
        f"GROUP BY k ORDER BY n DESC, k ASC LIMIT {capped}"
    )
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    return [(str(row["k"]), int(row["n"])) for row in rows if row["k"] is not None]


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
