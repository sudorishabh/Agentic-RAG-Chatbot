"""Unit tests for theme classification and the theme rows it writes.

Two layers: :mod:`app.catalog.theme_taxonomy` turning raw theme names into
primary-tag / sub-theme assignments against ``app/data.json``, and the
``documents_theme`` writes in :mod:`app.catalog.state` that persist them. The SQL
runs against a scripted fake cursor; the real statements run in
``app/local_tests``.
"""

from __future__ import annotations

import json

import pytest

from app.catalog import state, theme_taxonomy
from app.catalog.models import StateRecord

TABLE = "documents"


# --------------------------------------------------------------------------- #
# theme_taxonomy.classify — the data.json hierarchy.
# --------------------------------------------------------------------------- #

def _rows(names) -> list[tuple[str, str, str | None, str | None]]:
    return [
        (a.name, a.theme_type, a.parent, a.group) for a in theme_taxonomy.classify(names)
    ]


def test_bucket_child_is_a_primary_tag():
    assert _rows(["Energy"]) == [("Energy", "primary", None, "main")]
    assert _rows(["Climate Change"]) == [
        ("Climate Change", "primary", None, "main")
    ]
    # "Other Themes" children are primary tags too, children or not — but the
    # group distinguishes them from a "Main Themes" primary tag.
    assert _rows(["Green Shipping"]) == [
        ("Green Shipping", "primary", None, "other")
    ]


def test_descendant_is_a_sub_theme_pointing_at_its_primary_tag():
    assert _rows(["Energy Access"]) == [("Energy Access", "sub", "Energy", "main")]
    assert _rows(["Air"]) == [("Air", "sub", "Environment", "main")]
    # Inherits its primary tag's group even though that primary tag sits under
    # "Other Themes", not "Main Themes".
    assert _rows(["Education for Youth Empowerment"]) == [
        (
            "Education for Youth Empowerment",
            "sub",
            "Environment Education",
            "other",
        )
    ]


def test_grouping_buckets_are_never_themes():
    """"Main Themes" / "Other Themes" are containers in data.json — storing them
    would credit every document with a theme it was never tagged with."""
    assert _rows(["Main Themes", "Other Themes"]) == []
    assert _rows(["Energy", "Main Themes"]) == [
        ("Energy", "primary", None, "main")
    ]


def test_blank_values_are_dropped_rather_than_stored_as_placeholders():
    assert _rows([None, "", "   ", "\t\n"]) == []


def test_unknown_theme_is_kept_as_an_unparented_sub_theme_with_no_group():
    """A theme added in the CMS but not yet in data.json is still recorded — it
    just has no parent or group to point at."""
    assert _rows(["Quantum Beekeeping"]) == [
        ("Quantum Beekeeping", "sub", None, None)
    ]


def test_matching_tolerates_case_and_whitespace_drift():
    assert _rows(["  energy   ACCESS "]) == [
        ("energy ACCESS", "sub", "Energy", "main")
    ]


def test_names_are_deduplicated_case_insensitively_keeping_input_order():
    assert _rows(["Air", "Energy", "AIR", "air"]) == [
        ("Air", "sub", "Environment", "main"),
        ("Energy", "primary", None, "main"),
    ]


def test_a_parent_is_a_reference_not_an_extra_row():
    """Tagging a post with only a sub-theme must not invent the parent's row —
    the document was never tagged with the parent."""
    assert _rows(["Energy Access"]) == [("Energy Access", "sub", "Energy", "main")]


def test_missing_data_file_degrades_instead_of_raising(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(theme_taxonomy, "TAXONOMY_PATH", tmp_path / "nope.json")
    theme_taxonomy.reload_taxonomy()
    try:
        assert _rows(["Energy"]) == [("Energy", "sub", None, None)]
        assert "Could not read the theme map" in caplog.text
    finally:
        theme_taxonomy.reload_taxonomy()


def test_deeper_nesting_still_points_at_the_primary_tag_and_inherits_its_group(
    monkeypatch, tmp_path
):
    """The table models one level of parenthood, so a great-grandchild hangs off
    the primary tag rather than its immediate parent — and still inherits that
    primary tag's bucket, however deep it sits."""
    path = tmp_path / "data.json"
    path.write_text(
        json.dumps(
            [{
                "name": "Main Themes",
                "children": [{
                    "name": "Energy",
                    "children": [{
                        "name": "Renewables",
                        "children": [{"name": "Rooftop Solar"}],
                    }],
                }],
            }]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(theme_taxonomy, "TAXONOMY_PATH", path)
    theme_taxonomy.reload_taxonomy()
    try:
        assert _rows(["Rooftop Solar"]) == [
            ("Rooftop Solar", "sub", "Energy", "main")
        ]
    finally:
        theme_taxonomy.reload_taxonomy()


def test_two_primary_tags_from_different_buckets_are_distinguishable_by_group():
    """"Energy" and "Green Shipping" are both primary tags with parent=None --
    only theme_group tells them apart as main vs other."""
    energy, shipping = _rows(["Energy"])[0], _rows(["Green Shipping"])[0]
    assert (energy[1], energy[2]) == (shipping[1], shipping[2]) == ("primary", None)
    assert energy[3] == "main"
    assert shipping[3] == "other"
    assert energy[3] != shipping[3]


def test_group_code_matches_on_substring_not_position():
    """A bucket named after "main" maps to "main" wherever it sits in the file;
    anything else falls to "other" rather than raising."""
    assert theme_taxonomy._group_code("Main Themes") == "main"
    assert theme_taxonomy._group_code("MAIN") == "main"
    assert theme_taxonomy._group_code("Other Themes") == "other"
    assert theme_taxonomy._group_code("Emerging Themes") == "other"


# --------------------------------------------------------------------------- #
# theme_taxonomy.group_of / themes_by_group — Main/Other lookup for the theme
# listing (list_themes), which needs to label a theme without a document ever
# carrying it — unlike classify(), which only labels themes a document has.
# --------------------------------------------------------------------------- #

def test_group_of_known_primary_tags():
    assert theme_taxonomy.group_of("Energy") == "main"
    assert theme_taxonomy.group_of("Green Shipping") == "other"


def test_group_of_matches_case_and_whitespace_drift():
    assert theme_taxonomy.group_of("  green   SHIPPING ") == "other"


def test_group_of_sub_theme_inherits_primary_tags_group():
    assert theme_taxonomy.group_of("Air") == "main"  # sub of Environment
    assert theme_taxonomy.group_of("Education for Youth Empowerment") == "other"


def test_group_of_unknown_theme_is_none():
    assert theme_taxonomy.group_of("Quantum Beekeeping") is None


def test_themes_by_group_splits_main_and_other():
    groups = theme_taxonomy.themes_by_group()
    assert set(groups) == {"main", "other"}
    assert "Energy" in groups["main"] and "Air" in groups["main"]
    assert "Green Shipping" in groups["other"]
    assert "Energy" not in groups["other"] and "Green Shipping" not in groups["main"]


# --------------------------------------------------------------------------- #
# state — the documents_theme writes.
# --------------------------------------------------------------------------- #

class _FakeCursor:
    def __init__(self, fetchall_results: list | None = None):
        self.fetchalls = list(fetchall_results or [])
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql: str, params: object = None) -> int:
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def executemany(self, sql: str, rows: list) -> int:
        self.calls.append((" ".join(sql.split()), rows))
        return len(rows)

    def fetchone(self):
        return {"n": 7}

    def fetchall(self):
        return self.fetchalls.pop(0) if self.fetchalls else []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def __init__(self, cursor: _FakeCursor):
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


@pytest.fixture
def cursor(monkeypatch):
    cur = _FakeCursor()
    monkeypatch.setattr(state, "mysql_connection", lambda: _FakeConn(cur))
    monkeypatch.setattr(state, "_table", lambda: TABLE)
    return cur


def _theme_sql(cursor: _FakeCursor, verb: str) -> list[tuple[str, object]]:
    return [c for c in cursor.calls if c[0].startswith(verb) and f"{TABLE}_theme" in c[0]]


def _record(**kwargs) -> StateRecord:
    defaults = dict(
        document_id="doc-1",
        source_type="website",
        source_key="https://example.org/brief",
        fingerprint="2024-02-01",
    )
    defaults.update(kwargs)
    return StateRecord(**defaults)


def test_upsert_writes_classified_theme_rows(cursor):
    state.upsert(_record(categories=["Energy", "Air", "Quantum Beekeeping"]))

    inserts = _theme_sql(cursor, "INSERT")
    assert len(inserts) == 1
    sql, rows = inserts[0]
    assert "(document_id, theme, theme_type, parent, theme_group)" in sql
    assert rows == [
        ("doc-1", "Energy", "primary", None, "main"),
        ("doc-1", "Air", "sub", "Environment", "main"),
        ("doc-1", "Quantum Beekeeping", "sub", None, None),
    ]


def test_upsert_inserts_nothing_when_no_valid_theme(cursor):
    """Requirement: no placeholder/NULL theme row. The DELETE still runs, so a
    document that lost its last theme is cleaned up rather than left stale."""
    state.upsert(_record(categories=["", None, "Main Themes"]))

    assert _theme_sql(cursor, "INSERT") == []
    deletes = _theme_sql(cursor, "DELETE")
    assert len(deletes) == 1 and deletes[0][1] == ("doc-1",)


def test_upsert_writes_the_document_row_before_its_theme_rows(cursor):
    """The content record is the primary fact and the FK target — it has to be
    in place before any theme row references it."""
    state.upsert(_record(categories=["Energy"]))

    statements = [sql for sql, _ in cursor.calls]
    doc_insert = next(i for i, s in enumerate(statements) if f"INSERT INTO `{TABLE}` " in s)
    theme_write = next(i for i, s in enumerate(statements) if f"{TABLE}_theme" in s)
    assert doc_insert < theme_write


def test_upsert_with_no_themes_at_all_still_clears_prior_rows(cursor):
    state.upsert(_record())

    assert _theme_sql(cursor, "INSERT") == []
    assert len(_theme_sql(cursor, "DELETE")) == 1


def test_backfill_facets_classifies_too(monkeypatch, cursor):
    monkeypatch.setattr(_FakeCursor, "fetchone", lambda self: {"document_id": "doc-1"})

    assert state.backfill_facets("doc-1", None, ["Jane"], ["Energy Access"]) is True

    _, rows = _theme_sql(cursor, "INSERT")[0]
    assert rows == [("doc-1", "Energy Access", "sub", "Energy", "main")]


def test_rename_theme_facet_reclassifies_the_new_name(cursor):
    """A term renamed into a known theme picks up that theme's position instead
    of keeping the one the old name had."""
    cursor.fetchalls = [[{"theme": "Atmosphere"}]]

    assert state.rename_theme_facet("doc-1", "Atmosphere", "Air") == ["Air"]

    _, rows = _theme_sql(cursor, "INSERT")[0]
    assert rows == [("doc-1", "Air", "sub", "Environment", "main")]


# --------------------------------------------------------------------------- #
# state.reclassify_theme_rows — the one-shot for rows predating the hierarchy.
# --------------------------------------------------------------------------- #

def test_reclassify_updates_known_names_and_drops_non_themes(cursor):
    cursor.fetchalls = [
        [{"theme": "Energy"}, {"theme": "Air"}, {"theme": "Main Themes"}]
    ]

    tally = state.reclassify_theme_rows()

    updates = _theme_sql(cursor, "UPDATE")
    assert [params for _, params in updates] == [
        ("primary", None, "main", "Energy"),
        ("sub", "Environment", "main", "Air"),
    ]
    deletes = _theme_sql(cursor, "DELETE")
    assert [params for _, params in deletes] == [("Main Themes",)]
    assert tally == {"names": 3, "updated": 2, "deleted": 1}


def test_reclassify_dry_run_writes_nothing(cursor):
    cursor.fetchalls = [[{"theme": "Energy"}, {"theme": "Main Themes"}]]

    tally = state.reclassify_theme_rows(dry_run=True)

    assert _theme_sql(cursor, "UPDATE") == [] and _theme_sql(cursor, "DELETE") == []
    # Counts are rows matching each name (the fake reports 7 per name).
    assert tally == {"names": 2, "updated": 7, "deleted": 7}


def test_reclassify_on_an_empty_table_does_nothing(cursor):
    assert state.reclassify_theme_rows() == {"names": 0, "updated": 0, "deleted": 0}
    assert _theme_sql(cursor, "UPDATE") == [] and _theme_sql(cursor, "DELETE") == []
