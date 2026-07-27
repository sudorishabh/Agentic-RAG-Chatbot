"""Unit tests for the renamed-facet schema migration.

The theme facet used to be called ``category``, and the facet name is both the
child table's suffix and its value column. A deployment can therefore sit at any
of three points, all covered here:

* fully old -- ``documents_category`` with a ``category`` column;
* table moved but column not -- what ``scripts.rename_catalog_tables`` leaves
  behind, and the state that broke every ``c.theme`` query;
* fully migrated -- nothing to do.

All of it runs against a fake cursor that models information_schema and applies
RENAME statements to itself, so idempotency is observable without MySQL.
"""

from __future__ import annotations

from app.catalog import schema

TABLE = "documents"


class _FakeCursor:
    """Answers information_schema probes from an in-memory {table: [columns]}
    map, and applies RENAME statements to it so repeat runs see real state."""

    def __init__(self, tables: dict[str, list[str]]):
        self.tables = {t: list(cols) for t, cols in tables.items()}
        self.statements: list[str] = []
        self._result: tuple | None = None

    def execute(self, sql: str, params: tuple = ()) -> None:
        flat = " ".join(sql.split())
        if "information_schema.TABLES" in flat:
            self._result = (1,) if params[0] in self.tables else None
            return
        if "information_schema.COLUMNS" in flat:
            table, column = params
            self._result = (1,) if column in self.tables.get(table, []) else None
            return
        self._result = None
        self.statements.append(flat)
        self._apply(flat)

    def _apply(self, stmt: str) -> None:
        words = [w.strip("`") for w in stmt.split()]
        if stmt.startswith("RENAME TABLE"):
            self.tables[words[4]] = self.tables.pop(words[2])
        elif "RENAME COLUMN" in stmt:
            cols = self.tables[words[2]]
            cols[cols.index(words[5])] = words[7]
        elif stmt.startswith("CREATE TABLE IF NOT EXISTS"):
            self.tables.setdefault(words[5], [])

    def fetchone(self):
        return self._result

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _renames(cursor) -> list[str]:
    return [s for s in cursor.statements if "RENAME" in s]


# --------------------------------------------------------------------------- #
# migrate_renamed_facets — the two independent steps.
# --------------------------------------------------------------------------- #

def test_migrates_table_and_column_for_fully_old_schema():
    cursor = _FakeCursor({f"{TABLE}_category": ["document_id", "category"]})

    applied = schema.migrate_renamed_facets(cursor, TABLE)

    assert applied == [
        f"RENAME TABLE `{TABLE}_category` TO `{TABLE}_theme`",
        f"ALTER TABLE `{TABLE}_theme` RENAME COLUMN `category` TO `theme`",
    ]
    assert cursor.tables == {f"{TABLE}_theme": ["document_id", "theme"]}


def test_renames_column_when_table_was_already_moved():
    """The regression: rename_catalog_tables moves the table but not the column,
    leaving `documents_theme`.`category` — every theme query fails on it."""
    cursor = _FakeCursor({f"{TABLE}_theme": ["document_id", "category"]})

    applied = schema.migrate_renamed_facets(cursor, TABLE)

    assert applied == [
        f"ALTER TABLE `{TABLE}_theme` RENAME COLUMN `category` TO `theme`"
    ]
    assert cursor.tables[f"{TABLE}_theme"] == ["document_id", "theme"]


def test_noop_when_already_migrated():
    cursor = _FakeCursor({f"{TABLE}_theme": ["document_id", "theme"]})

    assert schema.migrate_renamed_facets(cursor, TABLE) == []
    assert _renames(cursor) == []


def test_noop_on_fresh_install_with_no_facet_table():
    cursor = _FakeCursor({TABLE: ["document_id"]})

    assert schema.migrate_renamed_facets(cursor, TABLE) == []


def test_is_idempotent():
    cursor = _FakeCursor({f"{TABLE}_category": ["document_id", "category"]})

    assert schema.migrate_renamed_facets(cursor, TABLE)
    assert schema.migrate_renamed_facets(cursor, TABLE) == []
    assert cursor.tables == {f"{TABLE}_theme": ["document_id", "theme"]}


def test_honours_the_configured_table_prefix():
    """Local tests point ingest_state_table at their own prefix; the migration
    has to follow it rather than assume `documents`."""
    cursor = _FakeCursor({"local_test_ingest_state_category": ["document_id", "category"]})

    schema.migrate_renamed_facets(cursor, "local_test_ingest_state")

    assert cursor.tables == {"local_test_ingest_state_theme": ["document_id", "theme"]}


# --------------------------------------------------------------------------- #
# dry_run — report only, change nothing.
# --------------------------------------------------------------------------- #

def test_dry_run_reports_column_rename_without_executing():
    cursor = _FakeCursor({f"{TABLE}_theme": ["document_id", "category"]})

    applied = schema.migrate_renamed_facets(cursor, TABLE, dry_run=True)

    assert applied == [
        f"ALTER TABLE `{TABLE}_theme` RENAME COLUMN `category` TO `theme`"
    ]
    assert cursor.statements == []
    assert cursor.tables == {f"{TABLE}_theme": ["document_id", "category"]}


def test_dry_run_reports_both_steps_for_fully_old_schema():
    """Nothing moves under dry_run, so the column probe has to fall back to the
    table that still holds the rows or the second step goes unreported."""
    cursor = _FakeCursor({f"{TABLE}_category": ["document_id", "category"]})

    applied = schema.migrate_renamed_facets(cursor, TABLE, dry_run=True)

    assert len(applied) == 2
    assert cursor.statements == []
    assert cursor.tables == {f"{TABLE}_category": ["document_id", "category"]}


# --------------------------------------------------------------------------- #
# ensure_state_table — ordering against the facet DDL.
# --------------------------------------------------------------------------- #

def test_ensure_state_table_migrates_before_creating_facet_tables(monkeypatch):
    """CREATE TABLE IF NOT EXISTS `documents_theme` would silently shadow the
    populated `documents_category` with an empty table, so the rename must run
    first."""
    cursor = _FakeCursor({
        TABLE: ["document_id", "published_at", "size", "mtime_ns", "title",
                "url", "raw_meta", "entity_type"],
        f"{TABLE}_category": ["document_id", "category"],
    })
    monkeypatch.setattr(schema, "state_table", lambda: TABLE)
    monkeypatch.setattr(schema, "mysql_connection", lambda: _FakeConn(cursor))

    schema.ensure_state_table()

    rename = next(i for i, s in enumerate(cursor.statements) if s.startswith("RENAME TABLE"))
    create = next(
        i for i, s in enumerate(cursor.statements)
        if s.startswith("CREATE TABLE IF NOT EXISTS") and f"`{TABLE}_theme`" in s
    )
    assert rename < create
    assert cursor.tables[f"{TABLE}_theme"] == ["document_id", "theme"]
    assert f"{TABLE}_category" not in cursor.tables
