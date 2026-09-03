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
    map plus a set of tables holding a primary key, and applies RENAME / ALTER
    statements to itself so repeat runs see real state.

    ``fail_on`` makes any statement containing that substring raise, which is how
    the duplicate-rows-block-the-primary-key path is exercised."""

    def __init__(
        self,
        tables: dict[str, list[str]],
        pks: set[str] | None = None,
        fail_on: str | None = None,
        indexes: set[tuple[str, str]] | None = None,
    ):
        self.tables = {t: list(cols) for t, cols in tables.items()}
        self.pks = set(pks or ())
        self.indexes = set(indexes or ())
        self.fail_on = fail_on
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
        if "information_schema.STATISTICS" in flat:
            # Two probes share this table: the primary-key one passes just the
            # table, the named-index one passes (table, index_name).
            if len(params) == 2:
                self._result = (1,) if tuple(params) in self.indexes else None
            else:
                self._result = (1,) if params[0] in self.pks else None
            return
        self._result = None
        self.statements.append(flat)
        if self.fail_on and self.fail_on in flat:
            raise RuntimeError(f"refused: {flat}")
        self._apply(flat)

    def _apply(self, stmt: str) -> None:
        words = [w.strip("`") for w in stmt.split()]
        if stmt.startswith("RENAME TABLE"):
            self.tables[words[4]] = self.tables.pop(words[2])
        elif "RENAME COLUMN" in stmt:
            cols = self.tables[words[2]]
            cols[cols.index(words[5])] = words[7]
        elif "ADD PRIMARY KEY" in stmt:
            self.pks.add(words[2])
        elif "ADD COLUMN" in stmt:
            self.tables.setdefault(words[2], []).append(words[5])
        elif "ADD KEY" in stmt:
            self.indexes.add((words[2], words[5]))
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
# migrate_theme_hierarchy — flat facet table -> primary tag / sub-theme rows.
# --------------------------------------------------------------------------- #

_FLAT_THEME_TABLE = {f"{TABLE}_theme": ["document_id", "theme"]}


def test_theme_hierarchy_adds_columns_then_key_to_a_flat_table():
    cursor = _FakeCursor(dict(_FLAT_THEME_TABLE))

    applied = schema.migrate_theme_hierarchy(cursor, TABLE)

    assert applied == [
        f"ALTER TABLE `{TABLE}_theme` ADD COLUMN "
        "theme_type ENUM('primary', 'sub') NOT NULL DEFAULT 'sub'",
        f"ALTER TABLE `{TABLE}_theme` ADD COLUMN parent VARCHAR(255) NULL",
        f"ALTER TABLE `{TABLE}_theme` ADD COLUMN theme_group ENUM('main', 'other') NULL",
        f"ALTER TABLE `{TABLE}_theme` ADD PRIMARY KEY (document_id, theme)",
    ]
    assert cursor.tables[f"{TABLE}_theme"] == [
        "document_id", "theme", "theme_type", "parent", "theme_group",
    ]
    assert f"{TABLE}_theme" in cursor.pks


def test_theme_hierarchy_noop_when_already_current():
    cursor = _FakeCursor(
        {f"{TABLE}_theme": ["document_id", "theme", "theme_type", "parent", "theme_group"]},
        pks={f"{TABLE}_theme"},
    )

    assert schema.migrate_theme_hierarchy(cursor, TABLE) == []
    assert cursor.statements == []


def test_theme_hierarchy_noop_when_the_table_does_not_exist_yet():
    """A fresh install gets the hierarchy from the CREATE, so there is nothing
    to migrate — and no ALTER may be aimed at a table that isn't there."""
    cursor = _FakeCursor({TABLE: ["document_id"]})

    assert schema.migrate_theme_hierarchy(cursor, TABLE) == []
    assert cursor.statements == []


def test_theme_hierarchy_is_idempotent():
    cursor = _FakeCursor(dict(_FLAT_THEME_TABLE))

    assert len(schema.migrate_theme_hierarchy(cursor, TABLE)) == 4
    assert schema.migrate_theme_hierarchy(cursor, TABLE) == []


def test_theme_hierarchy_adds_only_the_missing_half():
    """A deployment interrupted mid-way through the ADD COLUMNs resumes cleanly."""
    cursor = _FakeCursor(
        {f"{TABLE}_theme": ["document_id", "theme", "theme_type"]},
        pks={f"{TABLE}_theme"},
    )

    applied = schema.migrate_theme_hierarchy(cursor, TABLE)

    assert applied == [
        f"ALTER TABLE `{TABLE}_theme` ADD COLUMN parent VARCHAR(255) NULL",
        f"ALTER TABLE `{TABLE}_theme` ADD COLUMN theme_group ENUM('main', 'other') NULL",
    ]


def test_theme_hierarchy_dry_run_reports_without_executing():
    cursor = _FakeCursor(dict(_FLAT_THEME_TABLE))

    applied = schema.migrate_theme_hierarchy(cursor, TABLE, dry_run=True)

    assert len(applied) == 4
    assert cursor.statements == []
    assert cursor.tables == _FLAT_THEME_TABLE


def test_theme_hierarchy_survives_a_key_the_table_will_not_take(caplog):
    """Legacy rows can hold duplicate (document_id, theme) pairs, which blocks
    the primary key. The columns still land and ensure_state_table must not die
    — every theme write replaces a document's rows wholesale regardless."""
    cursor = _FakeCursor(dict(_FLAT_THEME_TABLE), fail_on="ADD PRIMARY KEY")

    applied = schema.migrate_theme_hierarchy(cursor, TABLE)  # no raise

    assert len(applied) == 4
    assert cursor.tables[f"{TABLE}_theme"] == [
        "document_id", "theme", "theme_type", "parent", "theme_group",
    ]
    assert f"{TABLE}_theme" not in cursor.pks
    assert "Could not add the primary key" in caplog.text


# --------------------------------------------------------------------------- #
# ensure_state_table — ordering against the facet DDL.
# --------------------------------------------------------------------------- #

def test_ensure_state_table_migrates_before_creating_facet_tables(monkeypatch):
    """CREATE TABLE IF NOT EXISTS `documents_theme` would silently shadow the
    populated `documents_category` with an empty table, so the rename must run
    first."""
    cursor = _FakeCursor({
        TABLE: ["document_id", "effective_start_date", "size", "mtime_ns", "title",
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
    alter = next(
        i for i, s in enumerate(cursor.statements)
        if f"ALTER TABLE `{TABLE}_theme` ADD COLUMN theme_type" in s
    )
    # rename -> create (which no-ops on the renamed table) -> hierarchy migration,
    # so the carried-forward rows end up under the current shape.
    assert rename < create < alter
    assert cursor.tables[f"{TABLE}_theme"] == [
        "document_id", "theme", "theme_type", "parent", "theme_group",
    ]
    assert f"{TABLE}_category" not in cursor.tables


# --------------------------------------------------------------------------- #
# pipeline_version — the column and index a corpus reprocess is driven from.
# --------------------------------------------------------------------------- #

def _legacy_state_table() -> dict[str, list[str]]:
    """A `documents` table from before either was added.

    ``size``/``mtime_ns`` are deliberately still here. The current DDL no longer
    creates them — they were leftovers from the retired local-file pipeline and
    were never written — but a deployed table *does* carry them, and these tests
    exist to prove migrations cope with a table as it really is.
    """
    return {
        TABLE: ["document_id", "effective_start_date", "size", "mtime_ns", "title",
                "url", "raw_meta", "entity_type"],
    }


def test_an_existing_table_gains_the_pipeline_version_column(monkeypatch):
    cursor = _FakeCursor(_legacy_state_table())
    monkeypatch.setattr(schema, "state_table", lambda: TABLE)
    monkeypatch.setattr(schema, "mysql_connection", lambda: _FakeConn(cursor))

    schema.ensure_state_table()

    assert "pipeline_version" in cursor.tables[TABLE]
    assert (TABLE, "idx_pipeline_version") in cursor.indexes


def test_the_column_arrives_null_so_existing_rows_read_as_stale(monkeypatch):
    """Nothing already indexed was produced by a pipeline that stamped a
    version, so all of it must be rebuilt as it is next crawled. A DEFAULT would
    have declared the whole corpus current in one statement."""
    cursor = _FakeCursor(_legacy_state_table())
    monkeypatch.setattr(schema, "state_table", lambda: TABLE)
    monkeypatch.setattr(schema, "mysql_connection", lambda: _FakeConn(cursor))

    schema.ensure_state_table()

    added = next(s for s in cursor.statements if "ADD COLUMN pipeline_version" in s)
    assert "NULL" in added and "DEFAULT" not in added


def test_the_migration_is_idempotent(monkeypatch):
    cursor = _FakeCursor(_legacy_state_table())
    monkeypatch.setattr(schema, "state_table", lambda: TABLE)
    monkeypatch.setattr(schema, "mysql_connection", lambda: _FakeConn(cursor))

    schema.ensure_state_table()
    first = len(cursor.statements)
    schema.ensure_state_table()

    # CREATE TABLE IF NOT EXISTS carries the column in its DDL and is a no-op on
    # the second run; what must not repeat is the ALTER.
    altered = [
        s for s in cursor.statements[first:]
        if "pipeline_version" in s and not s.startswith("CREATE TABLE")
    ]
    assert altered == []


def test_an_index_that_cannot_be_added_is_not_fatal(monkeypatch):
    """An index is a performance property. Failing to add one must not stop
    ensure_state_table from creating the tables everything else needs."""
    # Only the ALTER that adds the index: the CREATE DDL names it too, and
    # refusing that would be testing something else entirely.
    cursor = _FakeCursor(_legacy_state_table(), fail_on=f"`{TABLE}` ADD KEY")
    monkeypatch.setattr(schema, "state_table", lambda: TABLE)
    monkeypatch.setattr(schema, "mysql_connection", lambda: _FakeConn(cursor))

    schema.ensure_state_table()  # must not raise

    assert "pipeline_version" in cursor.tables[TABLE]
    assert f"{TABLE}_theme" in cursor.tables, "the rest of the schema still landed"
