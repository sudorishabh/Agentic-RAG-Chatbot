"""The document catalog: MySQL-backed ingest state and audit log.

Ingestion writes through :mod:`app.catalog.state` / :mod:`app.catalog.log`;
retrieval reads through :mod:`app.catalog.queries`. Schema and migrations live in
:mod:`app.catalog.schema`; shared DAO helpers (timestamps, table-name guards) in
:mod:`app.catalog.db`; the theme hierarchy map in
:mod:`app.catalog.theme_taxonomy`.

Themes and tags are keyed by **name** (``documents_theme`` / ``documents_tag``);
taxonomy UUIDs live only in Qdrant payloads. See
docs/retire-term-tables-plan.md.
"""
