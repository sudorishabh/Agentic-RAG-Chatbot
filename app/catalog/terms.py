"""Taxonomy-term catalog: the entity tables behind theme facets.

Terms are keyed by their Drupal UUID so document links survive renames: a
rename updates one row here and archives the previous name as an alias, which
keeps user queries using the stale name resolvable. Populated from the full
taxonomy_term fetch every ingestion run — a rebuildable projection of Drupal,
never hand-edited. Schema/DDL lives in :mod:`app.catalog.schema`.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from app.catalog import schema
from app.catalog.db import now as _now
from app.catalog.schema import ALIAS_TABLE, TERM_TABLE
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)


def ensure_tables() -> None:
    schema.ensure_term_tables()


def upsert_term(
    term_uuid: str,
    vocabulary: str,
    name: str,
    *,
    parent_uuid: str | None = None,
    changed_mark: int | None = None,
) -> str | None:
    """Insert or update one term; returns the previous name when this was a
    rename (the trigger for the payload display refresh), else None.

    On a rename the previous name is archived into the alias table in the
    same transaction, so it stays resolvable for queries. Document links are
    untouched — they join on term_uuid."""
    name = name.strip()[:255]
    if not (term_uuid and vocabulary and name):
        return None

    renamed = False
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT name FROM `{TERM_TABLE}` WHERE term_uuid = %s", (term_uuid,)
        )
        row = cur.fetchone()
        prior_name = row["name"] if row else None
        renamed = prior_name is not None and prior_name != name
        if renamed:
            cur.execute(
                f"INSERT IGNORE INTO `{ALIAS_TABLE}` (term_uuid, old_name, renamed_at) "
                "VALUES (%s, %s, %s)",
                (term_uuid, prior_name, _now()),
            )
        cur.execute(
            f"""
            INSERT INTO `{TERM_TABLE}`
                (term_uuid, vocabulary, name, parent_uuid, changed_mark, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                vocabulary   = VALUES(vocabulary),
                name         = VALUES(name),
                parent_uuid  = VALUES(parent_uuid),
                changed_mark = VALUES(changed_mark),
                updated_at   = VALUES(updated_at)
            """,
            (term_uuid, vocabulary, name, parent_uuid, changed_mark, _now()),
        )
        conn.commit()

    if renamed:
        logger.info("Term %s renamed %r -> %r", term_uuid, prior_name, name)
        return prior_name
    return None


def delete_terms(term_uuids: Iterable[str]) -> int:
    ids = [t for t in term_uuids if t]
    if not ids:
        return 0
    placeholders = ", ".join(["%s"] * len(ids))
    with mysql_connection() as conn, conn.cursor() as cur:
        removed = cur.execute(
            f"DELETE FROM `{TERM_TABLE}` WHERE term_uuid IN ({placeholders})", tuple(ids)
        )
        conn.commit()
    return int(removed or 0)


def resolve_terms(name: str, vocabulary: str | None = None) -> list[dict[str, Any]]:
    """Resolve a user-supplied term name to catalog rows [{term_uuid, name}].

    Case-insensitive exact match on current names; archived aliases are only
    consulted when no current name matches, so a rename keeps old phrasing
    working without dragging history into unrelated matches."""
    name = (name or "").strip()
    if not name:
        return []
    vocab_params: tuple = (vocabulary,) if vocabulary else ()
    current_clause = " AND vocabulary = %s" if vocabulary else ""
    alias_clause = " AND t.vocabulary = %s" if vocabulary else ""
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT term_uuid, name FROM `{TERM_TABLE}` "
            f"WHERE LOWER(name) = LOWER(%s){current_clause}",
            (name, *vocab_params),
        )
        rows = list(cur.fetchall())
        if rows:
            return rows
        cur.execute(
            f"SELECT t.term_uuid, t.name FROM `{ALIAS_TABLE}` a "
            f"JOIN `{TERM_TABLE}` t ON t.term_uuid = a.term_uuid "
            f"WHERE LOWER(a.old_name) = LOWER(%s){alias_clause}",
            (name, *vocab_params),
        )
        return list(cur.fetchall())


def descendant_uuids(roots: Iterable[str]) -> list[str]:
    """Expand term UUIDs to include every transitive child (via ``parent_uuid``).

    The roots are always included and returned first. Walks UUIDs only, so it
    is rename-proof, and the ``seen`` set makes it safe against cyclic parent
    links. Lets a parent theme scope its whole subtree — a document tagged only
    with a sub-theme still counts under the parent.
    """
    seen: dict[str, None] = {}
    frontier = [u for u in roots if u]
    for uuid in frontier:
        seen.setdefault(uuid, None)
    if not frontier:
        return []
    with mysql_connection() as conn, conn.cursor() as cur:
        while frontier:
            placeholders = ", ".join(["%s"] * len(frontier))
            cur.execute(
                f"SELECT term_uuid FROM `{TERM_TABLE}` "
                f"WHERE parent_uuid IN ({placeholders})",
                tuple(frontier),
            )
            children = [row["term_uuid"] for row in cur.fetchall()]
            frontier = [c for c in children if c not in seen]
            for uuid in frontier:
                seen.setdefault(uuid, None)
    return list(seen)


def list_themes(vocabulary: str = "themes", *, limit: int = 200) -> list[dict[str, Any]]:
    """The theme vocabulary as catalog rows ``[{term_uuid, name, parent_uuid}]``,
    ordered by name.

    Reads the canonical terms table, not the free-text facet, so it reflects the
    real taxonomy — including themes with no documents yet — and is unaffected by
    display-name drift. ``limit`` clamps to [1, 1000].
    """
    capped = max(1, min(int(limit or 200), 1000))
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT term_uuid, name, parent_uuid FROM `{TERM_TABLE}` "
            f"WHERE vocabulary = %s ORDER BY name ASC LIMIT {capped}",
            (vocabulary,),
        )
        return list(cur.fetchall())
