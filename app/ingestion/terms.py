"""Taxonomy-term catalog: the entity tables behind theme/category facets.

Terms are keyed by their Drupal UUID so document links survive renames: a
rename updates one row here and archives the previous name as an alias, which
keeps user queries using the stale name resolvable. Populated from the full
taxonomy_term fetch every ingestion run — a rebuildable projection of Drupal,
never hand-edited.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable

from app.deps import mysql_connection

logger = logging.getLogger(__name__)

# Fixed table names: terms are site-global facts, shared by any environment
# pointing at the same Drupal instance.
TERM_TABLE = "taxonomy_term"
ALIAS_TABLE = "taxonomy_term_alias"

_TERM_DDL = f"""
CREATE TABLE IF NOT EXISTS `{TERM_TABLE}` (
    term_uuid    VARCHAR(64)  NOT NULL,
    vocabulary   VARCHAR(128) NOT NULL,
    name         VARCHAR(255) NOT NULL,
    parent_uuid  VARCHAR(64)  NULL,
    changed_mark BIGINT       NULL,
    updated_at   DATETIME     NOT NULL,
    PRIMARY KEY (term_uuid),
    KEY idx_vocab_name (vocabulary, name),
    KEY idx_parent (parent_uuid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

_ALIAS_DDL = f"""
CREATE TABLE IF NOT EXISTS `{ALIAS_TABLE}` (
    term_uuid  VARCHAR(64)  NOT NULL,
    old_name   VARCHAR(255) NOT NULL,
    renamed_at DATETIME     NOT NULL,
    PRIMARY KEY (term_uuid, old_name),
    KEY idx_old_name (old_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_tables() -> None:
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_TERM_DDL)
        cur.execute(_ALIAS_DDL)
        conn.commit()


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


def get_term(term_uuid: str) -> dict[str, Any] | None:
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT * FROM `{TERM_TABLE}` WHERE term_uuid = %s", (term_uuid,)
        )
        return cur.fetchone()
