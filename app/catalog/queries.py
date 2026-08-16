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
import time
from datetime import datetime
from typing import Any, Sequence

from app.catalog.db import state_table as _table
from app.catalog.state import StateRecord, _row_to_record
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)


# Theme values that are ingestion artefacts rather than themes: a boolean field
# stringified into the theme facet. Filtered in SQL so `limit` applies to real
# themes only. The ingestion-side guard is the actual fix; this keeps the
# artefact out of answers for rows already written.
_NON_THEME_VALUES: tuple[str, ...] = ("False", "True")


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
    theme: str | None = None,
    tag: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
) -> tuple[str, list[str], list[Any], bool]:
    """Shared JOIN/WHERE assembly for the catalog count/list queries.

    ``entity_type`` scopes to one Drupal entity kind — the query layer passes
    "node" so taxonomy-term and block rows never count as content documents.

    ``theme`` matches a theme **name exactly, or any sub-theme hanging off it**
    (``documents_theme.parent``), so scoping to a primary tag includes documents
    tagged only with one of its children. Exact rather than substring: the
    caller canonicalizes the name first (see
    ``app.retrieval.structured.filters``), and a substring match both misses
    sub-themes and wrongly merges siblings — "Environment" would sweep in
    "Environment Education" while missing "Air" and "Water". One level of
    ``parent`` is enough because ``theme_taxonomy`` flattens deeper nesting onto
    the primary tag.

    ``tag`` joins ``documents_tag`` separately from the theme join, so a theme
    filter and a tag filter combine as AND rather than collapsing into one
    condition. Returns (joins, clauses, params, needs_distinct)."""
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
    if theme:
        joins.append(f" JOIN `{table}_theme` c ON c.document_id = s.document_id")
        clauses.append("(c.theme = %s OR c.parent = %s)")
        params.extend((theme, theme))
        distinct = True
    if tag:
        joins.append(f" JOIN `{table}_tag` t ON t.document_id = s.document_id")
        clauses.append("t.tag = %s")
        params.append(tag)
        distinct = True
    return "".join(joins), clauses, params, distinct


def count_documents(
    source_type: str | None = None,
    bundle: str | None = None,
    *,
    entity_type: str | None = None,
    title_contains: str | None = None,
    author: str | None = None,
    theme: str | None = None,
    tag: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
) -> int:
    """Count catalog documents (not chunks) matching the given filters.

    ``author`` and ``title_contains`` match substrings; ``theme`` and ``tag``
    match names exactly (``theme`` also matching its sub-themes) — see
    :func:`_catalog_filters`. Date bounds are a half-open ``[from, to)`` interval
    over ``published_at``. Takes the same filter set as
    ``list_documents``/``distribution`` so a count and a listing of the same
    query can never disagree."""
    table = _table()
    joins, clauses, params, distinct = _catalog_filters(
        source_type, bundle, entity_type=entity_type, title_contains=title_contains,
        author=author, theme=theme, tag=tag,
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
    theme: str | None = None,
    tag: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 10,
    offset: int = 0,
) -> list[StateRecord]:
    """List catalog documents matching the filters, most recent first.

    Mirrors ``count_documents`` but returns the matching rows so structured
    list/lookup queries are answered from the local catalog instead of a live
    site fetch. ``limit`` is clamped to [1, 100]; ``offset`` clamps to >= 0 and
    pages through the same ordering (published_at desc, document_id asc)."""
    table = _table()
    joins, clauses, params, needs_distinct = _catalog_filters(
        source_type, bundle, entity_type=entity_type,
        title_contains=title_contains, author=author,
        theme=theme, tag=tag,
        published_from=published_from, published_to=published_to,
    )
    distinct = "DISTINCT " if needs_distinct else ""
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    capped = max(1, min(int(limit or 10), 100))
    capped_offset = max(0, int(offset or 0))
    offset_clause = f" OFFSET {capped_offset}" if capped_offset else ""
    sql = (
        f"SELECT {distinct}s.* FROM `{table}` s{joins}{where} "
        f"ORDER BY s.published_at DESC, s.document_id ASC LIMIT {capped}{offset_clause}"
    )
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        return [_row_to_record(row) for row in cur.fetchall()]


# Dimensions the distribution query can group by. "author" groups on its facet
# table; "theme" groups on the documents_theme facet; "bundle" and "year" come
# off the document row itself.
_DISTRIBUTION_DIMENSIONS = ("bundle", "author", "theme", "year")


def distribution(
    group_by: str,
    source_type: str | None = "website",
    bundle: str | None = None,
    *,
    entity_type: str | None = None,
    author: str | None = None,
    theme: str | None = None,
    tag: str | None = None,
    title_contains: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 20,
) -> list[tuple[str, int]]:
    """Grouped document counts ("how many per theme/type/author/year"),
    largest group first. Returns (group value, count) pairs.

    Applies the same theme/tag/author/title/date scope as ``count_documents``
    and ``list_documents`` (via :func:`_catalog_filters`), so a breakdown can be
    narrowed to one theme, tag, author, period, etc. — ``tag`` is a scope filter
    here, not a groupable dimension (see ``_DISTRIBUTION_DIMENSIONS``). A
    document that fans out across a facet join is counted once per group."""
    if group_by not in _DISTRIBUTION_DIMENSIONS:
        raise ValueError(f"group_by must be one of {_DISTRIBUTION_DIMENSIONS}")
    table = _table()
    scope_joins, clauses, params, scoped = _catalog_filters(
        source_type, bundle, entity_type=entity_type,
        title_contains=title_contains, author=author,
        theme=theme, tag=tag,
        published_from=published_from, published_to=published_to,
    )

    if group_by == "bundle":
        group_join, key = "", "s.bundle"
    elif group_by == "year":
        group_join, key = "", "YEAR(s.published_at)"
        clauses.append("s.published_at IS NOT NULL")
    elif group_by == "theme":
        # Group on the theme facet, excluding the boolean-literal artefacts
        # `theme_vocabulary` also filters, so a breakdown and a listing of the
        # vocabulary can never disagree about which themes exist.
        group_join = f" JOIN `{table}_theme` gt ON gt.document_id = s.document_id"
        key = "gt.theme"
        placeholders = ", ".join(["%s"] * len(_NON_THEME_VALUES))
        clauses.append(f"gt.theme <> '' AND gt.theme NOT IN ({placeholders})")
        params.extend(_NON_THEME_VALUES)
    else:  # author -> multi-valued facet table
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


def distinct_authors(*, limit: int = 2000) -> list[str]:
    """Every distinct author string in the catalog, ordered by name.

    Backs entity resolution's fuzzy author matching (see
    ``app.retrieval.structured.resolve``): the full set is fetched and scored in
    Python rather than narrowed by a SQL ``LIKE`` prefilter, because a genuine
    misspelling ("rishab negi") is not a substring of the stored name
    ("Rishabh Negi") — a prefilter tight enough to be cheap would systematically
    exclude exactly the fuzzy matches this exists to catch. Correct at this
    corpus's scale (low hundreds of distinct authors); revisit if that changes.
    ``limit`` clamps to [1, 5000]."""
    table = _table()
    capped = max(1, min(int(limit or 2000), 5000))
    sql = f"SELECT DISTINCT author FROM `{table}_author` ORDER BY author ASC LIMIT {capped}"
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return [row["author"] for row in cur.fetchall() if row["author"]]


# How long an inventory read is trusted. Short enough that an ingest adding a
# content type — or a newer document — shows up without a restart, long enough
# that the extra query is noise next to the LLM calls on the same request.
_INVENTORY_TTL_SECONDS = 600
_bundle_inventory: tuple[float, tuple[str, ...]] | None = None
_published_range: tuple[float, tuple[str | None, str | None]] | None = None


def available_bundles(*, refresh: bool = False) -> tuple[str, ...]:
    """The bundles this catalog actually holds content documents for.

    ``DEFAULT_BUNDLES`` is the list ingestion *attempts*, not what a given
    deployment ended up with — a source that has no press releases, or a bundle
    that was never crawled, leaves a content type that is advertised to the LLM
    but can only ever match zero rows. Asking the catalog closes that gap.

    Scoped to website nodes, matching what the entity registry considers a
    content document (see ``app.retrieval.structured.entities``); PDF
    attachments reuse their parent's bundle and would otherwise imply a type
    exists as browsable content when it does not.

    Fails open with an empty tuple: callers must read that as "unknown", never
    as "the catalog is empty", or a MySQL blip would retract the whole
    vocabulary.

    Cached here rather than in the callers so the prompt builder and the query
    guard share one inventory (and one query) per request."""
    global _bundle_inventory
    now = time.monotonic()
    if (
        not refresh
        and _bundle_inventory is not None
        and now - _bundle_inventory[0] < _INVENTORY_TTL_SECONDS
    ):
        return _bundle_inventory[1]
    table = _table()
    sql = (
        f"SELECT DISTINCT bundle FROM `{table}` "
        "WHERE bundle IS NOT NULL AND source_type = 'website' AND entity_type = 'node'"
    )
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            found = tuple(sorted(r["bundle"] for r in cur.fetchall() if r["bundle"]))
    except Exception:
        logger.warning("Bundle inventory lookup failed; treating it as unknown.",
                       exc_info=True)
        return ()
    _bundle_inventory = (now, found)
    return found


def _as_iso_date(value: Any) -> str | None:
    """A ``published_at`` bound as a bare ISO date, or None when unusable."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = str(value or "")[:10]
    return text or None


def published_range(*, refresh: bool = False) -> tuple[str | None, str | None]:
    """The oldest and newest publication dates the catalog holds, as ISO dates.

    The date-extracting prompts anchor relative expressions to *today*, which is
    right for reading the user ("last six months" means the last six months) and
    wrong for the corpus: an archive whose newest document is two years old
    answers "what changed this year" with a confident zero that reads as a fact
    about the world rather than about the catalog. Naming the real span lets the
    model scope to a period that can actually match — the same gap
    ``available_bundles`` closes for content types.

    Unscoped, unlike ``available_bundles``: a bundle is a browsable-type concept
    that only applies to website nodes, whereas any indexed document can carry a
    date and be retrieved by one.

    Fails open with ``(None, None)``, which callers must read as "unknown" — a
    MySQL blip must not tell the model the catalog covers nothing."""
    global _published_range
    now = time.monotonic()
    if (
        not refresh
        and _published_range is not None
        and now - _published_range[0] < _INVENTORY_TTL_SECONDS
    ):
        return _published_range[1]
    table = _table()
    sql = (
        f"SELECT MIN(published_at) AS lo, MAX(published_at) AS hi FROM `{table}` "
        "WHERE published_at IS NOT NULL"
    )
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        row = rows[0] if rows else {}
        found = (_as_iso_date(row.get("lo")), _as_iso_date(row.get("hi")))
    except Exception:
        logger.warning("Published-range lookup failed; treating it as unknown.",
                       exc_info=True)
        return (None, None)
    _published_range = (now, found)
    return found


def theme_vocabulary(*, limit: int = 500) -> list[dict[str, Any]]:
    """The theme vocabulary as the catalog knows it — one row per distinct theme
    with its hierarchy and Main/Other group, ordered by name.

    ``documents_theme`` is the source of truth for what themes exist: it stores
    the theme *name* alongside the ``theme_type`` / ``parent`` / ``theme_group``
    that ``app.catalog.theme_taxonomy`` materialized at ingest. Nothing here
    reads app/theme_structure.json — that file shapes the columns during ingestion, and the
    columns answer queries afterwards.

    A theme carrying more than one hierarchy variant (the theme map changed between
    ingests, so some rows are stale) collapses to the variant the most documents
    agree on, ties broken by name, so callers always see exactly one row per
    theme. ``documents`` is that variant's document count. ``limit`` clamps to
    [1, 2000] and applies to themes, not rows.
    """
    table = _table()
    capped = max(1, min(int(limit or 500), 2000))
    placeholders = ", ".join(["%s"] * len(_NON_THEME_VALUES))
    sql = (
        f"SELECT theme, theme_type, parent, theme_group,"
        f" COUNT(DISTINCT document_id) AS documents"
        f" FROM `{table}_theme`"
        f" WHERE theme <> '' AND theme NOT IN ({placeholders})"
        f" GROUP BY theme, theme_type, parent, theme_group"
        f" ORDER BY theme ASC, documents DESC, theme_type ASC"
    )
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, _NON_THEME_VALUES)
        rows = cur.fetchall()
    vocabulary: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not row["theme"]:
            continue
        # ORDER BY put the best-supported variant first, so the first win sticks.
        vocabulary.setdefault(
            row["theme"],
            {
                "theme": row["theme"],
                "theme_type": row["theme_type"],
                "parent": row["parent"],
                "theme_group": row["theme_group"],
                "documents": int(row["documents"] or 0),
            },
        )
        if len(vocabulary) >= capped:
            break
    return list(vocabulary.values())


def find_tag(name: str) -> str | None:
    """The stored casing of ``name`` if any document carries that tag, else None.

    A targeted lookup rather than a vocabulary scan, because tags are matched
    **exactly** (they are a long-tail freeform set — see
    docs/database-retrieval-redesign.md §3, and `filters._resolve_tag_name`).
    Loading every tag to compare in Python would also silently truncate: this
    corpus already has more distinct tags than a sane row cap.
    ``idx_val`` on the tag column makes this an index hit."""
    if not name or not name.strip():
        return None
    table = _table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT tag FROM `{table}_tag` WHERE tag = %s LIMIT 1", (name.strip(),)
        )
        row = cur.fetchone()
        if row:
            return row["tag"]
        # Only fall back to a case-insensitive scan when the exact form missed —
        # LOWER() on the column cannot use the index.
        cur.execute(
            f"SELECT tag FROM `{table}_tag` WHERE LOWER(tag) = LOWER(%s) LIMIT 1",
            (name.strip(),),
        )
        row = cur.fetchone()
    return row["tag"] if row else None


def distinct_tags(*, limit: int = 5000) -> list[str]:
    """Every distinct tag name in ``documents_tag``, ordered by name.

    Diagnostics only — matching a tag goes through :func:`find_tag`, which does
    not have to load the vocabulary. ``limit`` clamps to [1, 10000]."""
    table = _table()
    capped = max(1, min(int(limit or 5000), 10000))
    sql = f"SELECT DISTINCT tag FROM `{table}_tag` ORDER BY tag ASC LIMIT {capped}"
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return [row["tag"] for row in cur.fetchall() if row["tag"]]


def distinct_themes(*, limit: int = 500) -> list[str]:
    """Every distinct theme name in ``documents_theme``, ordered by name.

    A names-only view of :func:`theme_vocabulary`, so it inherits the same junk
    filtering and one-row-per-theme guarantee."""
    return [row["theme"] for row in theme_vocabulary(limit=limit)]


# --------------------------------------------------------------------------- #
# Id-scoped reads for retrieval (scoped summarization, attachment
# supplementation). Website nodes (source_type='website', entity_type='node')
# are baked in as the catalog of record; DB errors fail open to empty results
# so callers degrade to the plain semantic pipeline.
# --------------------------------------------------------------------------- #

def document_ids_in_scope(
    *,
    bundle: str | None = None,
    theme: str | None = None,
    tag: str | None = None,
    author: str | None = None,
    title_contains: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    limit: int = 150,
) -> list[str]:
    """Document ids matching a metadata scope, most recent first.

    The id-set selection behind catalog-scoped retrieval: MySQL decides set
    membership, Qdrant ranks content within it. Scoping matches
    :func:`_catalog_filters` — ``theme`` by exact name or sub-theme, ``tag`` by
    exact name. ``limit`` clamps to [1, 300] — honest truncation beats an
    unbounded MatchAny downstream.
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
    if theme:
        joins.append(f" JOIN `{table}_theme` c ON c.document_id = s.document_id")
        clauses.append("(c.theme = %s OR c.parent = %s)")
        params.extend((theme, theme))
        distinct = True
    if tag:
        joins.append(f" JOIN `{table}_tag` t ON t.document_id = s.document_id")
        clauses.append("t.tag = %s")
        params.append(tag)
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


def abstracts_for(document_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    """Ingest-time abstracts plus display fields, keyed by document_id.

    Joins the documents table to the enrichment cache on ``content_hash`` —
    the cache is keyed by content rather than by document (see
    :mod:`app.catalog.enrichment`), so this is where the two are brought back
    together. Documents with no cached abstract are simply absent from the
    result and the caller falls back to a lead chunk.

    Deliberately does **not** filter on the enrichment version. A version
    mismatch means the abstract predates the current prompt, not that it is
    wrong about the document; serving it still beats the fallback, and the next
    sweep or backfill refreshes it.
    """
    ids = [d for d in document_ids if d]
    if not ids:
        return {}
    table = _table()
    placeholders = ", ".join(["%s"] * len(ids))
    sql = (
        f"SELECT s.document_id, s.title, s.url, s.published_at, e.abstract"
        f" FROM `{table}` s"
        f" JOIN `{table}_enrichment` e ON e.content_hash = s.content_hash"
        f" WHERE s.document_id IN ({placeholders}) AND e.abstract IS NOT NULL"
    )
    try:
        with mysql_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(ids))
            rows = cur.fetchall()
    except Exception:
        # Includes the enrichment table not existing yet — an un-enriched
        # deployment must keep summarizing from lead chunks as before.
        logger.warning("Catalog abstract lookup failed.", exc_info=True)
        return {}
    # A blank abstract counts as absent, not as an empty summary: otherwise the
    # document would be preferred over its own lead chunk and then dropped for
    # having no text, silently vanishing from the scope.
    return {
        row["document_id"]: {
            "abstract": row["abstract"],
            "title": row["title"],
            "url": row["url"],
            "published_at": row["published_at"],
        }
        for row in rows
        if (row["abstract"] or "").strip()
    }


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
