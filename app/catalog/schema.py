"""Catalog schema: table DDL and idempotent migrations.

Kept apart from the read/write model code (state.py / terms.py / log.py): this
module only ever CREATEs or ALTERs tables, never touches rows. Called once per
process via each ``ensure_*`` function (state.py / terms.py / log.py wrap these
under their historical names so callers are unaffected).

Table names were simplified from their legacy ``ingest_state*`` /
``taxonomy_term*`` forms to ``documents*`` / ``terms`` / ``term_aliases``; a
deployment with existing data must run ``scripts.rename_catalog_tables`` once
before/at deploy so the old tables become the new ones instead of being
recreated empty.

The theme facet was likewise renamed from ``category``. That one is handled here
rather than by the script, in ``migrate_renamed_facets``, because it also has to
rename the child table's *value column* and must work for whatever
``ingest_state_table`` prefix the process is configured with.

The theme facet also grew from a flat (document, value) list into a primary-tag /
sub-theme hierarchy; ``migrate_theme_hierarchy`` adds those columns to a table
that predates them.
"""
from __future__ import annotations

import logging
from typing import Any

from app.catalog.db import log_table, state_table
from app.core.clients import mysql_connection

logger = logging.getLogger(__name__)

_STATE_DDL = """
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
# via COUNT(DISTINCT document_id). Rows cascade-delete with their parent. The
# facet name doubles as the child table's suffix and its value column.
# Themes are such a facet too, but they carry hierarchy, so they have their own
# DDL (_STATE_THEME_DDL) instead of the generic one.
STATE_FACETS: tuple[str, ...] = ("author",)

# Facets renamed after deployments already had data. Because the facet name is
# both the table suffix and the column name, both have to be carried forward --
# and scripts.rename_catalog_tables only ever renamed tables, so a deployment
# can sit on `documents_theme` while its value column is still `category`.
# {current facet: previous facet}
_RENAMED_FACETS: dict[str, str] = {"theme": "category"}

_STATE_CHILD_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_{facet}` (
    document_id VARCHAR(255) NOT NULL,
    {facet}     VARCHAR(255) NOT NULL,
    KEY idx_doc (document_id),
    KEY idx_val ({facet}),
    CONSTRAINT `fk_{table}_{facet}` FOREIGN KEY (document_id)
        REFERENCES `{table}` (document_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

# The theme facet, with the taxonomy shape a flat facet has no room for: a
# document's main theme is stored as the primary tag and every other theme as a
# sub-theme naming the primary tag it hangs off. `parent` is NULL for a primary
# tag and for a sub-theme no parent is known for. Values are classified by
# app.catalog.theme_taxonomy against app/data.json; only themes the document is
# actually tagged with get a row -- a parent is a reference, never its own row.
_STATE_THEME_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_theme` (
    document_id VARCHAR(255) NOT NULL,
    theme       VARCHAR(255) NOT NULL,
    theme_type  ENUM('primary', 'sub') NOT NULL DEFAULT 'sub',
    parent      VARCHAR(255) NULL,
    PRIMARY KEY (document_id, theme),
    KEY idx_val (theme),
    KEY idx_parent (parent),
    CONSTRAINT `fk_{table}_theme` FOREIGN KEY (document_id)
        REFERENCES `{table}` (document_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

# Document -> taxonomy term links, joined on term_uuid (rename-proof; the
# term's name/hierarchy live in the taxonomy_term table).
_STATE_TERM_LINK_DDL = """
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
_STATE_ATTACHMENT_LINK_DDL = """
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


def _table_exists(cur: Any, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.TABLES "
        "WHERE table_schema = DATABASE() AND table_name = %s",
        (table,),
    )
    return cur.fetchone() is not None


def _column_exists(cur: Any, table: str, column: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.COLUMNS "
        "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
        (table, column),
    )
    return cur.fetchone() is not None


def _has_primary_key(cur: Any, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.STATISTICS "
        "WHERE table_schema = DATABASE() AND table_name = %s "
        "AND index_name = 'PRIMARY'",
        (table,),
    )
    return cur.fetchone() is not None


def _ensure_column(cur: Any, table: str, column: str, ddl: str) -> None:
    """Add a column to an existing table only if it is missing (idempotent
    migration for deployments created before the column existed)."""
    if not _column_exists(cur, table, column):
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN {ddl}")


def migrate_renamed_facets(cur: Any, table: str, *, dry_run: bool = False) -> list[str]:
    """Carry a renamed facet's child table *and* value column forward.

    Two independent steps, because a deployment can be part-way through: the
    table rename (``documents_category`` -> ``documents_theme``) may already have
    been done by ``scripts.rename_catalog_tables``, which leaves the value column
    named after the old facet. Renaming in place preserves the existing rows --
    the child DDL below cannot, since ``CREATE TABLE IF NOT EXISTS`` silently
    no-ops against the old table.

    Must run *before* the facet DDL: creating the new facet's table first would
    shadow the still-populated old one with an empty table.

    Idempotent -- each step only fires while the old name is the one present.
    Returns the statements applied (or, under ``dry_run``, the ones that would be).
    """
    applied: list[str] = []
    for facet, old in _RENAMED_FACETS.items():
        old_table, new_table = f"{table}_{old}", f"{table}_{facet}"
        # The table still holding the rows: under dry_run nothing moves, so a
        # pending table rename means the column lives on the old table.
        holder = new_table
        if _table_exists(cur, old_table) and not _table_exists(cur, new_table):
            stmt = f"RENAME TABLE `{old_table}` TO `{new_table}`"
            applied.append(stmt)
            if dry_run:
                holder = old_table
            else:
                cur.execute(stmt)
        if (
            _table_exists(cur, holder)
            and _column_exists(cur, holder, old)
            and not _column_exists(cur, holder, facet)
        ):
            stmt = f"ALTER TABLE `{new_table}` RENAME COLUMN `{old}` TO `{facet}`"
            applied.append(stmt)
            if not dry_run:
                cur.execute(stmt)
    return applied


def migrate_theme_hierarchy(cur: Any, table: str, *, dry_run: bool = False) -> list[str]:
    """Bring a pre-hierarchy ``documents_theme`` up to the current shape.

    The flat facet table held only (document_id, theme) with no primary key.
    Existing rows keep their theme and take the column default -- an unparented
    sub-theme -- until something reclassifies them
    (``scripts.reclassify_theme_rows``, or the document's next ingest).

    The key is added last and its failure is non-fatal: a legacy table can hold
    duplicate (document_id, theme) pairs, and the table works without the key
    anyway (every write replaces a document's rows wholesale), so a duplicate is
    logged rather than allowed to fail ``ensure_state_table`` for everything else.

    Idempotent. Returns the statements applied (or, under ``dry_run``, the ones
    that would be).
    """
    theme_table = f"{table}_theme"
    applied: list[str] = []
    if not _table_exists(cur, theme_table):
        return applied

    for column, ddl in (
        ("theme_type", "theme_type ENUM('primary', 'sub') NOT NULL DEFAULT 'sub'"),
        ("parent", "parent VARCHAR(255) NULL"),
    ):
        if _column_exists(cur, theme_table, column):
            continue
        stmt = f"ALTER TABLE `{theme_table}` ADD COLUMN {ddl}"
        applied.append(stmt)
        if not dry_run:
            cur.execute(stmt)

    if not _has_primary_key(cur, theme_table):
        stmt = f"ALTER TABLE `{theme_table}` ADD PRIMARY KEY (document_id, theme)"
        applied.append(stmt)
        if not dry_run:
            try:
                cur.execute(stmt)
            except Exception:
                logger.warning(
                    "Could not add the primary key to `%s` -- duplicate "
                    "(document_id, theme) rows from before it existed? The table "
                    "still works; collapse the duplicates and re-run to get the "
                    "key.", theme_table, exc_info=True,
                )
    return applied


def ensure_state_table() -> None:
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_STATE_DDL.format(table=table))
        _ensure_column(cur, table, "published_at", "published_at DATETIME NULL")
        _ensure_column(cur, table, "size", "size BIGINT NULL")
        _ensure_column(cur, table, "mtime_ns", "mtime_ns BIGINT NULL")
        _ensure_column(cur, table, "title", "title VARCHAR(1024) NULL")
        _ensure_column(cur, table, "url", "url VARCHAR(1024) NULL")
        _ensure_column(cur, table, "raw_meta", "raw_meta JSON NULL")
        _ensure_column(cur, table, "entity_type", "entity_type VARCHAR(32) NULL")
        migrate_renamed_facets(cur, table)
        for facet in STATE_FACETS:
            cur.execute(_STATE_CHILD_DDL.format(table=table, facet=facet))
        # Create then migrate: a fresh install gets the hierarchy from the DDL
        # and the migration no-ops; a legacy table survives CREATE IF NOT EXISTS
        # untouched and gets its columns from the migration.
        cur.execute(_STATE_THEME_DDL.format(table=table))
        migrate_theme_hierarchy(cur, table)
        cur.execute(_STATE_TERM_LINK_DDL.format(table=table))
        cur.execute(_STATE_ATTACHMENT_LINK_DDL.format(table=table))
        conn.commit()


# Fixed table names: terms are site-global facts, shared by any environment
# pointing at the same Drupal instance.
TERM_TABLE = "terms"
ALIAS_TABLE = "term_aliases"

# Taxonomy vocabulary that holds themes — the canonical source for theme
# enumeration and theme-distribution grouping (mirrors ingestion's
# CATEGORY_VOCABULARIES).
THEME_VOCABULARY = "themes"

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


def ensure_term_tables() -> None:
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_TERM_DDL)
        cur.execute(_ALIAS_DDL)
        conn.commit()


_LOG_DDL = """
CREATE TABLE IF NOT EXISTS `{table}` (
    id             BIGINT        NOT NULL AUTO_INCREMENT,
    run_id         VARCHAR(64)   NULL,
    document_id    VARCHAR(255)  NOT NULL,
    source_type    VARCHAR(32)   NOT NULL,
    source_path    VARCHAR(1024) NULL,
    source_url     VARCHAR(1024) NULL,
    bundle         VARCHAR(128)  NULL,
    tags           VARCHAR(1024) NULL,
    title          VARCHAR(512)  NULL,
    status         VARCHAR(32)   NOT NULL,
    doc_version    INT           NULL,
    chunks_indexed INT           NULL,
    fingerprint    VARCHAR(128)  NULL,
    content_hash   VARCHAR(64)   NULL,
    error_message  TEXT          NULL,
    event_time     DATETIME      NOT NULL,
    PRIMARY KEY (id),
    KEY idx_document (document_id),
    KEY idx_source_type (source_type),
    KEY idx_event_time (event_time),
    KEY idx_run (run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_log_table() -> None:
    table = log_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_LOG_DDL.format(table=table))
        conn.commit()
