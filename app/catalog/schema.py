"""Catalog schema: table DDL and idempotent migrations.

Kept apart from the read/write model code (state.py / log.py): this module only
ever CREATEs or ALTERs tables, never touches rows. Called once per process via
each ``ensure_*`` function (state.py / log.py wrap these under their historical
names so callers are unaffected).

Table names were simplified from their legacy ``ingest_state*`` forms to
``documents*``; a deployment with existing data must run
``scripts.rename_catalog_tables`` once before/at deploy so the old tables become
the new ones instead of being recreated empty.

The taxonomy-term tables (``terms``, ``term_aliases``, ``documents_term``) were
retired and dropped: the catalog is keyed by name, so themes live in
``documents_theme`` and tags in ``documents_tag``. Taxonomy no longer reaches
storage at all — terms are not crawled as documents, and the term uuids that
once rode every chunk payload were removed once nothing filtered on them. See
docs/retire-term-tables-plan.md for the original retirement.

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
STATE_FACETS: tuple[str, ...] = ("author", "tag")

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
# tag and for a sub-theme no parent is known for. `theme_group` is which
# top-level data.json bucket ("main" / "other", from theme_taxonomy._group_code)
# the theme traces back to -- tracked separately from theme_type/parent because
# two primary tags (e.g. "Energy" and "Green Shipping") can have the same
# theme_type/parent (primary, NULL) while coming from different buckets; a
# sub-theme inherits its primary tag's group. Values are classified by
# app.catalog.theme_taxonomy against app/data.json; only themes the document is
# actually tagged with get a row -- a parent is a reference, never its own row.
_STATE_THEME_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_theme` (
    document_id VARCHAR(255) NOT NULL,
    theme       VARCHAR(255) NOT NULL,
    theme_type  ENUM('primary', 'sub') NOT NULL DEFAULT 'sub',
    parent      VARCHAR(255) NULL,
    theme_group ENUM('main', 'other') NULL,
    PRIMARY KEY (document_id, theme),
    KEY idx_val (theme),
    KEY idx_parent (parent),
    KEY idx_group (theme_group),
    CONSTRAINT `fk_{table}_theme` FOREIGN KEY (document_id)
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
        ("theme_group", "theme_group ENUM('main', 'other') NULL"),
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
        cur.execute(_STATE_ATTACHMENT_LINK_DDL.format(table=table))
        conn.commit()


# Ingest-time enrichment (LLM-derived per-document output), keyed by the content
# hash it was derived from rather than by document_id — deliberately NOT a child
# table of `documents` and deliberately without a foreign key:
#
#   * it has to survive a state-table reset, which is the usual way to force a
#     reindex and exactly when re-paying for enrichment hurts most;
#   * documents whose body text is identical (the same PDF reached by two URLs,
#     or linked from several nodes) then share one row and enrich once;
#   * nothing may cascade-delete it when a document row goes away, because the
#     same content may come back under a different id.
#
# The trade is that orphan rows have to be pruned rather than cascaded. They are
# small and act as a cache for re-added content, so pruning is a maintenance
# task, not a correctness one.
_ENRICHMENT_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_enrichment` (
    content_hash VARCHAR(64) NOT NULL,
    version      VARCHAR(64) NOT NULL,
    abstract     TEXT        NULL,
    attempts     INT         NOT NULL DEFAULT 0,
    last_error   TEXT        NULL,
    updated_at   DATETIME    NOT NULL,
    PRIMARY KEY (content_hash),
    KEY idx_version (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_enrichment_table() -> None:
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_ENRICHMENT_DDL.format(table=table))
        conn.commit()


# Attachment URLs the site answers 4xx for. Like the enrichment table this is
# deliberately not a child of `documents` and carries no foreign key: a dead
# link never becomes a document row, so there is no parent to hang off.
#
# Keyed by document_id (the attachment's file uuid) and qualified by the
# fingerprint that was current when the download failed, so the marker expires
# exactly when the thing it describes could have changed: edit the node and its
# real attachments are retried, edit the body link and the in-body PDF's
# URL-derived id changes into a row that was never marked dead.
_DEAD_LINK_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_dead_link` (
    document_id VARCHAR(255)  NOT NULL,
    fingerprint VARCHAR(128)  NOT NULL,
    url         VARCHAR(1024) NULL,
    status      SMALLINT      NOT NULL,
    attempts    INT           NOT NULL DEFAULT 1,
    first_seen  DATETIME      NOT NULL,
    updated_at  DATETIME      NOT NULL,
    PRIMARY KEY (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_dead_link_table() -> None:
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_DEAD_LINK_DDL.format(table=table))
        conn.commit()


# Documents a run reached but did not index, and the crawl position each one
# sits at. The incremental cursor is derived from `documents` — MAX(changed_mark)
# over rows that exist, and a row exists only on success — so a failure leaves no
# trace and the next run's cursor advances straight past it. These rows are that
# trace: the crawl floors its cursor at the earliest one per bundle.
#
# Deliberately NOT a row in `documents`. A placeholder there would count as a
# catalogued document in every analytical read (bundle counts, list_documents,
# theme distributions) — a document that was never indexed showing up as one that
# was. `changed_mark` mirrors the column it is compared against; `bundle` is what
# the cursor is computed per.
_RETRY_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_retry` (
    document_id  VARCHAR(255) NOT NULL,
    source_type  VARCHAR(32)  NOT NULL,
    bundle       VARCHAR(128) NULL,
    changed_mark BIGINT       NULL,
    outcome      VARCHAR(16)  NOT NULL,
    attempts     INT          NOT NULL DEFAULT 1,
    error        TEXT         NULL,
    first_seen   DATETIME     NOT NULL,
    updated_at   DATETIME     NOT NULL,
    PRIMARY KEY (document_id),
    KEY idx_retry_floor (bundle, changed_mark)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_retry_table() -> None:
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_RETRY_DDL.format(table=table))
        conn.commit()


# Shadow-mode measurement of attachment publication dates (Phase 0). Deliberately
# its own table and not a column on `documents`: the point of the exercise is to
# compare a proposed date against the one in use without touching the row that
# holds the one in use, so a bad reading can never leak into retrieval. Keyed by
# document_id and overwritten per sweep — this is a current-state snapshot to
# query, not an audit trail (`ingest_log` already is one).
_DATE_SHADOW_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_date_candidate` (
    document_id   VARCHAR(255)  NOT NULL,
    origin        VARCHAR(16)   NOT NULL,
    node_created  DATETIME      NULL,
    file_created  DATETIME      NULL,
    pdf_created   DATETIME      NULL,
    pdf_modified  DATETIME      NULL,
    current_date_ DATETIME      NULL,
    proposed_date DATETIME      NULL,
    source        VARCHAR(32)   NOT NULL,
    rule          VARCHAR(32)   NOT NULL,
    delta_days    INT           NULL,
    would_move    TINYINT(1)    NOT NULL DEFAULT 0,
    url           VARCHAR(1024) NULL,
    filename      VARCHAR(512)  NULL,
    updated_at    DATETIME      NOT NULL,
    PRIMARY KEY (document_id),
    KEY idx_rule (rule),
    KEY idx_would_move (would_move)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_date_shadow_table() -> None:
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_DATE_SHADOW_DDL.format(table=table))
        conn.commit()


# Shadow output of the evidence-based resolver (deterministic rules + LLM
# interpretation). Separate from both `documents` and `{table}_date_candidate`:
# the first must not be touched at all, and the second records the simpler
# node/file/DocInfo comparison it supersedes. Nothing reads this back into
# ingestion or retrieval — it exists to be reviewed.
_DATE_DECISION_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_date_decision` (
    document_id     VARCHAR(255)  NOT NULL,
    origin          VARCHAR(16)   NOT NULL,
    bundle          VARCHAR(128)  NULL,
    node_uuid       VARCHAR(255)  NULL,
    page_pdf_count  INT           NOT NULL DEFAULT 1,
    current_published_at DATETIME NULL,
    candidate_date  DATETIME      NULL,
    date_type       VARCHAR(16)   NOT NULL,
    edition_label   VARCHAR(64)   NULL,
    candidate_source VARCHAR(32)  NOT NULL,
    confidence      DECIMAL(4,3)  NOT NULL DEFAULT 0,
    action          VARCHAR(24)   NOT NULL,
    rule            VARCHAR(48)   NOT NULL,
    decided_by      VARCHAR(16)   NOT NULL,
    evidence        TEXT          NULL,
    llm_raw         JSON          NULL,
    prompt_version  VARCHAR(32)   NULL,
    url             VARCHAR(1024) NULL,
    filename        VARCHAR(512)  NULL,
    updated_at      DATETIME      NOT NULL,
    PRIMARY KEY (document_id),
    KEY idx_action (action),
    KEY idx_decided_by (decided_by),
    KEY idx_rule (rule)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_date_decision_table() -> None:
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_DATE_DECISION_DDL.format(table=table))
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


# Entity mentions: one row per sighting of a name in a chunk. An append-heavy
# audit log — this is the largest table the knowledge layer adds — which is why
# it stays relational rather than becoming nodes in the graph.
#
# Deliberately NOT a child of `documents`:
#   * chunk ids are version-scoped, so a re-index replaces a document's whole
#     mention set anyway, by (document_id, doc_version);
#   * the same guard the enrichment table documents applies — content that comes
#     back under a different id must not lose its rows to a cascade.
#
# UNIQUE(chunk_id, start_offset, end_offset, normalized_text) is what makes
# repeated extraction idempotent: re-running writes the same rows, so retries
# and re-sweeps cannot duplicate knowledge. No entity_id column exists here —
# a mention is a sighting, and resolution owns identity.
_ENTITY_MENTION_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_entity_mention` (
    id                BIGINT       NOT NULL AUTO_INCREMENT,
    chunk_id          VARCHAR(64)  NOT NULL,
    document_id       VARCHAR(255) NOT NULL,
    doc_version       INT          NULL,
    start_offset      INT          NOT NULL,
    end_offset        INT          NOT NULL,
    surface_text      VARCHAR(512) NOT NULL,
    normalized_text   VARCHAR(512) NOT NULL,
    entity_type       VARCHAR(32)  NOT NULL,
    extraction_method VARCHAR(32)  NOT NULL,
    extractor_version VARCHAR(64)  NOT NULL,
    confidence        FLOAT        NOT NULL,
    created_at        DATETIME     NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_span (chunk_id, start_offset, end_offset, normalized_text),
    KEY idx_document (document_id, doc_version),
    KEY idx_normalized (entity_type, normalized_text),
    KEY idx_method (extraction_method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

# The extraction cost cache, modelled on `{table}_enrichment`: keyed by the
# chunk's own content hash (not its id) so a re-index whose paragraphs are
# unchanged still hits, and qualified by a key covering the extractor version
# and the gazetteer, so newer code never serves output it would not produce.
_ENTITY_EXTRACTION_DDL = """
CREATE TABLE IF NOT EXISTS `{table}_entity_extraction` (
    content_hash      VARCHAR(64) NOT NULL,
    extraction_key    VARCHAR(64) NOT NULL,
    extractor_version VARCHAR(64) NOT NULL,
    mention_count     INT         NOT NULL DEFAULT 0,
    attempts          INT         NOT NULL DEFAULT 0,
    last_error        TEXT        NULL,
    updated_at        DATETIME    NOT NULL,
    PRIMARY KEY (content_hash),
    KEY idx_key (extraction_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def ensure_entity_tables() -> None:
    """Create the mention log and its extraction cache. Idempotent."""
    table = state_table()
    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(_ENTITY_MENTION_DDL.format(table=table))
        cur.execute(_ENTITY_EXTRACTION_DDL.format(table=table))
        conn.commit()
