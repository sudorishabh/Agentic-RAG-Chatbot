"""A document's facet is a set, and the table has to say so.

Two defects made it not one. The write path de-duplicated the *source* values and
truncated afterwards, so two tags differing only past character 255 arrived as
one pair of distinct strings and left as two identical rows. And `documents_tag`
carried only lookup keys, so nothing rejected them: 144 duplicated
(document_id, tag) pairs, each one an over-count in every read of the table.

`documents_theme` never had the problem — it has had (document_id, theme) as its
primary key from the start, which is the shape the other facets now take.

SQL runs against scripted fake cursors; no MySQL.
"""

from __future__ import annotations

import pytest

from app.catalog import schema, state

TABLE = "documents"
WIDTH = 255


# --------------------------------------------------------------------------- #
# The write path: truncate, then de-duplicate.
# --------------------------------------------------------------------------- #

def _long(suffix: str, prefix: str = "Sustainable urban water management in Indian cities ") -> str:
    """A value longer than the column, differing only past the cut."""
    return (prefix * 10)[:WIDTH] + suffix


def test_values_colliding_after_truncation_become_one_row():
    first, second = _long("-alpha"), _long("-beta")
    assert first != second, "distinct as read"
    assert first[:WIDTH] == second[:WIDTH], "identical as written"

    assert state._stored_values([first, second]) == [first[:WIDTH]]


def test_ordinary_duplicates_still_collapse():
    assert state._stored_values(["Energy", "Energy", "Water"]) == ["Energy", "Water"]


def test_blank_values_are_dropped():
    assert state._stored_values(["", "Energy", None or ""]) == ["Energy"]


def test_order_is_preserved():
    """It is the order the source listed them in; a facet list that reshuffles
    itself between ingests is noise in every diff."""
    assert state._stored_values(["Water", "Energy", "Air"]) == ["Water", "Energy", "Air"]


def test_short_values_are_untouched():
    assert state._stored_values(["Energy Access"]) == ["Energy Access"]


# --------------------------------------------------------------------------- #
# ...applied by both writers.
# --------------------------------------------------------------------------- #

class _FakeCursor:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def executemany(self, sql, rows):
        self.calls.append((" ".join(sql.split()), rows))
        return len(rows)

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _inserted(cursor: _FakeCursor, table: str) -> list:
    return [
        params for sql, params in cursor.calls
        if sql.startswith("INSERT INTO") and table in sql
    ][0]


def test_the_tag_writer_stores_one_row_per_collision():
    cursor = _FakeCursor()

    state._replace_facet(cursor, TABLE, "tag", "doc-1", [_long("-a"), _long("-b")])

    assert _inserted(cursor, f"{TABLE}_tag") == [("doc-1", _long("-a")[:WIDTH])]


def test_the_author_writer_stores_one_row_per_collision():
    """Zero duplicates in production today, and the identical defect: the
    de-duplication ran on values the column cannot hold."""
    cursor = _FakeCursor()

    state._replace_authors(cursor, TABLE, "doc-1", [_long("-a"), _long("-b")])

    rows = _inserted(cursor, f"{TABLE}_author")
    assert len(rows) == 1
    document_id, raw, normalized = rows[0]
    assert raw == _long("-a")[:WIDTH]
    assert len(normalized) <= WIDTH


def test_the_author_normalisation_describes_the_stored_spelling():
    """`author_norm` is normalised from the truncated value that is actually
    stored, so the two columns of a row always describe one string."""
    from app.catalog import author_names

    cursor = _FakeCursor()
    state._replace_authors(cursor, TABLE, "doc-1", ["Dr. Jayanta Mitra"])

    _, raw, normalized = _inserted(cursor, f"{TABLE}_author")[0]
    assert normalized == author_names.normalize(raw)


# --------------------------------------------------------------------------- #
# The constraint, and the migration that makes room for it.
# --------------------------------------------------------------------------- #

class _MigrationCursor:
    """Models one facet table's rows, its indexes and the duplicate query."""

    def __init__(self, rows: list[tuple], *, has_key: bool = False,
                 exists: bool = True, fail_on: str | None = None):
        self.rows = list(rows)          # (document_id, value[, extra])
        self.has_key = has_key
        self.exists = exists
        self.fail_on = fail_on
        self.statements: list[str] = []
        self._result: list[dict] = []

    def execute(self, sql, params=()):
        flat = " ".join(sql.split())
        if "information_schema.TABLES" in flat:
            self._one = (1,) if self.exists else None
            return
        if "information_schema.STATISTICS" in flat:
            self._one = (1,) if self.has_key else None
            return
        if flat.startswith("SELECT document_id"):
            counts: dict[tuple, list] = {}
            for row in self.rows:
                counts.setdefault(row[:2], []).append(row)
            self._result = [
                {
                    "document_id": key[0], "value": key[1], "copies": len(group),
                    "extra": next((r[2] for r in group if len(r) > 2), None),
                }
                for key, group in counts.items() if len(group) > 1
            ]
            return
        self.statements.append(flat)
        if self.fail_on and self.fail_on in flat:
            raise RuntimeError(f"refused: {flat}")
        if flat.startswith("DELETE FROM"):
            self.rows = [r for r in self.rows if r[:2] != tuple(params)]
        elif flat.startswith("INSERT INTO"):
            self.rows.append(tuple(params))
        elif "ADD UNIQUE KEY" in flat:
            self.has_key = True

    def fetchone(self):
        return getattr(self, "_one", None)

    def fetchall(self):
        return self._result


def test_the_migration_collapses_duplicates_before_adding_the_key():
    """Order matters: MySQL refuses the key while duplicates are present."""
    cursor = _MigrationCursor([
        ("doc-1", "Energy"), ("doc-1", "Energy"), ("doc-2", "Water"),
    ])

    applied = schema.migrate_facet_uniqueness(cursor, TABLE, "tag")

    assert sorted(cursor.rows) == [("doc-1", "Energy"), ("doc-2", "Water")]
    assert "ADD UNIQUE KEY" in applied[-1]
    delete = next(i for i, s in enumerate(cursor.statements) if s.startswith("DELETE"))
    key = next(i for i, s in enumerate(cursor.statements) if "ADD UNIQUE KEY" in s)
    assert delete < key


def test_a_clean_table_is_only_keyed():
    cursor = _MigrationCursor([("doc-1", "Energy"), ("doc-2", "Water")])

    applied = schema.migrate_facet_uniqueness(cursor, TABLE, "tag")

    assert len(applied) == 1 and "ADD UNIQUE KEY" in applied[0]
    assert not [s for s in cursor.statements if s.startswith("DELETE")]
    assert len(cursor.rows) == 2


def test_collapsing_an_author_pair_carries_its_normalised_form():
    cursor = _MigrationCursor([
        ("doc-1", "Dr Jayanta Mitra", "jayanta mitra"),
        ("doc-1", "Dr Jayanta Mitra", "jayanta mitra"),
    ])

    schema.migrate_facet_uniqueness(cursor, TABLE, "author")

    assert cursor.rows == [("doc-1", "Dr Jayanta Mitra", "jayanta mitra")]


def test_the_migration_is_idempotent():
    cursor = _MigrationCursor([("doc-1", "Energy"), ("doc-1", "Energy")])

    schema.migrate_facet_uniqueness(cursor, TABLE, "tag")
    again = schema.migrate_facet_uniqueness(cursor, TABLE, "tag")

    assert again == [], "the key's presence is the guard"


def test_a_dry_run_reports_without_touching_a_row():
    cursor = _MigrationCursor([("doc-1", "Energy"), ("doc-1", "Energy")])

    applied = schema.migrate_facet_uniqueness(cursor, TABLE, "tag", dry_run=True)

    assert len(applied) == 2, "the collapse and the key"
    assert cursor.statements == []
    assert len(cursor.rows) == 2, "still duplicated"


def test_a_key_that_cannot_be_added_is_not_fatal():
    """The table works without it; failing ensure_state_table for everything
    else would not."""
    cursor = _MigrationCursor([("doc-1", "Energy")], fail_on="ADD UNIQUE KEY")

    schema.migrate_facet_uniqueness(cursor, TABLE, "tag")  # must not raise

    assert cursor.has_key is False


def test_a_missing_table_is_skipped():
    cursor = _MigrationCursor([], exists=False)

    assert schema.migrate_facet_uniqueness(cursor, TABLE, "tag") == []


def test_a_fresh_table_declares_the_constraint():
    ddl = schema._STATE_CHILD_DDL.format(table=TABLE, facet="tag")

    assert "UNIQUE KEY uq_tag (document_id, tag)" in " ".join(ddl.split())
    assert "KEY idx_doc" not in ddl, "subsumed by the unique key's leftmost column"


def test_the_theme_table_already_had_this_shape():
    """Stated as a test so the two facets cannot drift apart again."""
    ddl = " ".join(schema._STATE_THEME_DDL.format(table=TABLE).split())

    assert "PRIMARY KEY (document_id, theme)" in ddl
