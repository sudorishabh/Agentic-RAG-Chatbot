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
"""
from __future__ import annotations

from typing import Any

from app.catalog.db import log_table, state_table
from app.core.clients import mysql_connection

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
# via COUNT(DISTINCT document_id). Rows cascade-delete with their parent.
STATE_FACETS: tuple[str, ...] = ("author", "theme")

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
        for facet in STATE_FACETS:
            cur.execute(_STATE_CHILD_DDL.format(table=table, facet=facet))
        cur.execute(_STATE_TERM_LINK_DDL.format(table=table))
        cur.execute(_STATE_ATTACHMENT_LINK_DDL.format(table=table))
        conn.commit()


# Fixed table names: terms are site-global facts, shared by any environment
# pointing at the same Drupal instance.
TERM_TABLE = "terms"
ALIAS_TABLE = "term_aliases"

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
