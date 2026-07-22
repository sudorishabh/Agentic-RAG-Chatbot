"""The document catalog: MySQL-backed ingest state, term registry, and audit log.

Ingestion writes through :mod:`app.catalog.state` / :mod:`app.catalog.terms` /
:mod:`app.catalog.log`; retrieval reads through :mod:`app.catalog.queries`.
Schema and migrations live in :mod:`app.catalog.schema`; shared DAO helpers
(timestamps, table-name guards) in :mod:`app.catalog.db`.
"""
