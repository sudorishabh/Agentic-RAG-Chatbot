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

from app.catalog import author_names, schema, theme_taxonomy
from app.catalog.db import now as _now
from app.catalog.db import state_table as _table
from app.catalog.models import AttachmentLink, StateRecord
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)

__all__ = [
    "AttachmentLink",
    "StateRecord",
    "ensure_table",
    "load",
    "get",
    "upsert",
    "delete",
    "clear_change_markers",
    "attachment_ids_for",
    "orphaned_attachments",
    "backfill_facets",
    "rename_theme_facet",
    "reclassify_theme_rows",
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


# Facet value columns are VARCHAR(255); anything longer is stored truncated.
_FACET_WIDTH = 255


def _stored_values(values: Iterable[str], width: int = _FACET_WIDTH) -> list[str]:
    """The distinct values as they will actually be stored.

    Truncate first, de-duplicate second. The other order de-duplicates strings
    the database will never hold: two tags differing only past character 255 are
    distinct as read and identical as written, so the old order emitted two rows
    the table then had no constraint to reject. 144 duplicate (document, tag)
    pairs came from exactly that.

    Order is preserved — it is the order the source listed them in, and a facet
    list that reshuffles itself between ingests is noise in every diff.
    """
    return list(dict.fromkeys(v[:width] for v in values if v))


def _replace_facet(
    cur: Any, table: str, facet: str, document_id: str, values: Iterable[str]
) -> None:
    cur.execute(f"DELETE FROM `{table}_{facet}` WHERE document_id = %s", (document_id,))
    rows = [(document_id, value) for value in _stored_values(values)]
    if rows:
        cur.executemany(
            f"INSERT INTO `{table}_{facet}` (document_id, {facet}) VALUES (%s, %s)", rows
        )


def _replace_authors(
    cur: Any, table: str, document_id: str, values: Iterable[str]
) -> None:
    """Rewrite a document's author rows, each with its normalized form beside it.

    `author` is exactly what Drupal sent and is never rewritten — it is what an
    answer displays and what makes a count traceable to the source.
    `author_norm` is the formatting-normalized form (see
    :mod:`app.catalog.author_names`), which is what a *distinct name* count
    should group on: "Dr Jayanta Mitra" and "Dr. Jayanta Mitra" are one name
    written two ways.

    It is emphatically not a person id. Two people called "Arun Kumar" share a
    normalized form here, exactly as they already share a raw one.
    """
    cur.execute(f"DELETE FROM `{table}_author` WHERE document_id = %s", (document_id,))
    # De-duplicated on the stored (truncated) spelling for the same reason tags
    # are, and normalized from that same stored value so the pair in one row
    # always describes one string.
    rows = [
        (document_id, value, author_names.normalize(value)[:_FACET_WIDTH] or None)
        for value in _stored_values(values)
    ]
    if rows:
        cur.executemany(
            f"INSERT INTO `{table}_author` (document_id, author, author_norm) "
            "VALUES (%s, %s, %s)",
            rows,
        )


def _replace_themes(
    cur: Any, table: str, document_id: str, names: Iterable[str]
) -> None:
    """Rewrite a document's theme rows: its main theme as the primary tag and
    every other theme as a sub-theme naming the primary tag it hangs off, each
    tagged with the top-level bucket ("main" / "other") it traces back to.

    Only the themes the document itself carries are written — a sub-theme's
    parent is recorded as a reference, never materialized as an extra row, so a
    document is never credited with a theme it wasn't tagged with. A document
    with no valid theme (all values empty, or only grouping-bucket names) gets no
    row at all rather than a placeholder. See :mod:`app.catalog.theme_taxonomy`
    for the classification."""
    cur.execute(f"DELETE FROM `{table}_theme` WHERE document_id = %s", (document_id,))
    rows = [
        (document_id, a.name[:255], a.theme_type, a.parent[:255] if a.parent else None, a.group)
        for a in theme_taxonomy.classify(names)
    ]
    if rows:
        cur.executemany(
            f"INSERT INTO `{table}_theme` "
            "(document_id, theme, theme_type, parent, theme_group) "
            "VALUES (%s, %s, %s, %s, %s)",
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
        pipeline_version=row.get("pipeline_version") or None,
        bundle=row.get("bundle"),
        entity_type=row.get("entity_type"),
        changed_mark=row.get("changed_mark"),
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


def attachment_ids_for(document_id: str) -> list[str]:
    """The attachments this document links to.

    Read *before* the document is deleted: its link rows cascade away with it,
    which is exactly the information :func:`orphaned_attachments` then needs a
    candidate list for.
    """
    if not document_id:
        return []
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT file_uuid FROM `{_table()}_attachment` WHERE document_id = %s",
            (document_id,),
        )
        return [row["file_uuid"] for row in cur.fetchall()]


def orphaned_attachments(
    file_uuids: Iterable[str], *, ignoring_parents: Iterable[str] = ()
) -> list[str]:
    """Which of these attachments no longer hang off any document at all.

    An attachment is shared: 84 of them are reachable from more than one page,
    so losing one parent is not losing the attachment. The link table is the
    whole truth about that, so the question is asked of it directly — after the
    parent's rows have gone, an attachment with no rows left has no parent left.

    ``ignoring_parents`` answers the same question a step earlier: treat these
    parents as though they were already gone. That is what lets a dry run report
    the attachments a deletion *would* orphan without deleting anything to find
    out, using this query rather than a second copy of its reasoning.

    Restricted to ids that are attachment documents in their own right, so a
    file that was linked but never successfully ingested costs no delete call.
    """
    ids = [f for f in dict.fromkeys(file_uuids) if f]
    if not ids:
        return []
    ignored = [p for p in dict.fromkeys(ignoring_parents) if p]
    table = _table()
    params = list(ids)
    unless_gone = ""
    if ignored:
        unless_gone = f" AND a.document_id NOT IN ({', '.join(['%s'] * len(ignored))})"
        params.extend(ignored)
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT d.document_id FROM `{table}` d "
            f"WHERE d.document_id IN ({', '.join(['%s'] * len(ids))}) "
            f"  AND d.source_type = 'pdf_attachment' "
            f"  AND NOT EXISTS (SELECT 1 FROM `{table}_attachment` a "
            f"                  WHERE a.file_uuid = d.document_id{unless_gone})",
            tuple(params),
        )
        return [row["document_id"] for row in cur.fetchall()]


def upsert(record: StateRecord, *, mark_indexed: bool = True) -> None:
    table = _table()
    now = _now()
    indexed_at = now if mark_indexed else None
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO `{table}`
                (document_id, source_type, source_key, bundle, entity_type,
                 fingerprint, content_hash, doc_version, pipeline_version,
                 changed_mark, published_at, title, url, raw_meta, indexed_at,
                 updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                source_type  = VALUES(source_type),
                source_key   = VALUES(source_key),
                bundle       = VALUES(bundle),
                entity_type  = COALESCE(VALUES(entity_type), entity_type),
                fingerprint  = VALUES(fingerprint),
                content_hash = VALUES(content_hash),
                doc_version  = VALUES(doc_version),
                -- COALESCE, like entity_type and indexed_at: only a write that
                -- actually re-chunked the document may claim its pipeline
                -- version. A fingerprint refresh (`indexed=False`) passes NULL
                -- and keeps the stored one, so a document that has not been
                -- rebuilt still reads as stale and is rebuilt later.
                pipeline_version = COALESCE(VALUES(pipeline_version), pipeline_version),
                changed_mark = VALUES(changed_mark),
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
                record.pipeline_version,
                record.changed_mark,
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
        _replace_authors(cur, table, record.document_id, record.authors)
        _replace_facet(cur, table, "tag", record.document_id, record.tags)
        _replace_themes(cur, table, record.document_id, record.categories)
        _replace_attachment_links(cur, table, record.document_id, record.attachments)
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


def clear_change_markers(document_id: str) -> bool:
    """Make the next crawl treat this document as changed — without deleting it.

    Two independent signals gate re-indexing, and anything asking for a document
    to be rebuilt has to clear both:

    * ``fingerprint`` is the *crawl's* change test (:func:`compute_status`).
      While it still matches the source's ``changed`` value the record resolves
      UNCHANGED and the document is never even built, so the content hash below
      would never be consulted.
    * ``content_hash`` is the *pipeline's* test, which decides between refreshing
      the fingerprint and re-indexing for real.

    ``changed_mark`` is deliberately left in place. It is the document's position
    in the crawl, and the retry marker written alongside this call needs it to
    pull the window back far enough to reach the document at all — clearing it
    would strand exactly the document being repaired.

    Nothing else is touched: the row, its facets, its attachments links and its
    indexed vectors all survive, so the document stays searchable and correctly
    catalogued right up until its replacement is indexed.

    Returns False when no such document is catalogued.
    """
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT 1 FROM `{table}` WHERE document_id = %s", (document_id,))
        if cur.fetchone() is None:
            return False
        cur.execute(
            f"UPDATE `{table}` SET fingerprint = '', content_hash = '', "
            f"updated_at = %s WHERE document_id = %s",
            (_now(), document_id),
        )
        conn.commit()
    return True


def backfill_facets(
    document_id: str,
    published_at: str | None,
    authors: Iterable[str],
    categories: Iterable[str],
    *,
    title: str | None = None,
    url: str | None = None,
) -> bool:
    """Set the date/author/theme facets (and optionally title/url) for an
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
        _replace_authors(cur, table, document_id, authors)
        _replace_themes(cur, table, document_id, categories)
        conn.commit()
    return True


def reclassify_theme_rows(*, dry_run: bool = False) -> dict[str, int]:
    """Re-apply the theme map to theme rows already in the table, in place.

    For deployments whose rows predate the hierarchy columns
    (:func:`app.catalog.schema.migrate_theme_hierarchy` gives them the column
    default — an unparented sub-theme). Keyed on the distinct theme *names*, not
    on documents, since the classification depends only on the name: a whole
    corpus is a few dozen statements. Names that are not themes at all (grouping
    buckets, blanks) have their rows deleted.

    Idempotent — a second run reports 0 updated. Under ``dry_run`` nothing is
    written and the counts are rows that *match* each name, not rows that would
    actually change. Returns ``{'names', 'updated', 'deleted'}``.
    """
    table = _table()
    tally = {"names": 0, "updated": 0, "deleted": 0}
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT DISTINCT theme FROM `{table}_theme`")
        for name in [row["theme"] for row in cur.fetchall()]:
            tally["names"] += 1
            assignment = next(iter(theme_taxonomy.classify([name])), None)
            bucket = "deleted" if assignment is None else "updated"
            if dry_run:
                cur.execute(
                    f"SELECT COUNT(*) AS n FROM `{table}_theme` WHERE theme = %s",
                    (name,),
                )
                tally[bucket] += int(cur.fetchone()["n"])
                continue
            if assignment is None:
                logger.info("Dropping theme rows for non-theme value %r", name)
                affected = cur.execute(
                    f"DELETE FROM `{table}_theme` WHERE theme = %s", (name,)
                )
            else:
                affected = cur.execute(
                    f"UPDATE `{table}_theme` SET theme_type = %s, parent = %s, "
                    "theme_group = %s WHERE theme = %s",
                    (assignment.theme_type, assignment.parent, assignment.group, name),
                )
            tally[bucket] += int(affected or 0)
        if not dry_run:
            conn.commit()
    return tally


def rename_theme_facet(document_id: str, old: str, new: str) -> list[str]:
    """Replace ``old`` with ``new`` in a document's theme facet, collapsing
    duplicates; returns the resulting theme list (payload-refresh input).

    The rewrite re-classifies, so a theme renamed into (or out of) the theme map
    picks up its correct primary/sub position rather than keeping the old one."""
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT theme FROM `{table}_theme` WHERE document_id = %s",
            (document_id,),
        )
        themes = [row["theme"] for row in cur.fetchall()]
        updated = list(dict.fromkeys(new if c == old else c for c in themes))
        if updated != themes:
            _replace_themes(cur, table, document_id, updated)
            conn.commit()
    return updated
