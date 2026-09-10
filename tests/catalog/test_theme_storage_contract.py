"""The theme storage contract, stated as tests.

Companion to ``test_theme_rows.py``, which unit-tests the classifier and the
statements ``state`` emits. This module asserts the *properties* the storage
model has to hold — sparseness, hierarchy at arbitrary depth, open vocabulary,
idempotence — and it does so end to end where that is what makes the test worth
having.

The theme-scope predicate is executed rather than pattern-matched. Asserting
that the generated SQL "contains LIKE" says nothing about whether a query for
Energy actually reaches a document tagged only "Mini Grids" three levels down;
so :func:`_documents_matching` builds the real ``documents_theme`` rows in
SQLite, runs the real clause from :func:`app.catalog.queries._theme_scope_clause`
against them, and returns who matched. That is the requirement, checked.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from app.catalog import queries, state, theme_taxonomy
from app.catalog.models import StateRecord

TABLE = "documents"


# --------------------------------------------------------------------------- #
# A four-level map, so "deeper than a sub-theme" is a real case and not a
# hypothetical. Energy > Energy Access > Rural Energy Access > Mini Grids, with
# siblings at two levels to catch over-matching.
# --------------------------------------------------------------------------- #

_DEEP_TAXONOMY = [
    {
        "name": "Main Themes",
        "children": [
            {
                "name": "Energy",
                "children": [
                    {
                        "name": "Energy Access",
                        "children": [
                            {
                                "name": "Rural Energy Access",
                                "children": [{"name": "Mini Grids"}],
                            }
                        ],
                    },
                    {"name": "Energy Efficiency"},
                    # Shares a prefix with "Energy" but is its sibling, not its
                    # child: the guard against prefix matching without the
                    # separator.
                ],
            },
            {"name": "Climate Change", "children": [{"name": "Adaptation"}]},
        ],
    },
    {"name": "Other Themes", "children": [{"name": "Energy Storage"}]},
]


@pytest.fixture
def deep_taxonomy(monkeypatch, tmp_path):
    path = tmp_path / "theme_structure.json"
    path.write_text(json.dumps(_DEEP_TAXONOMY), encoding="utf-8")
    monkeypatch.setattr(theme_taxonomy, "TAXONOMY_PATH", path)
    theme_taxonomy.reload_taxonomy()
    yield
    theme_taxonomy.reload_taxonomy()


# --------------------------------------------------------------------------- #
# Executing the theme-scope predicate.
# --------------------------------------------------------------------------- #

def _documents_matching(scope: str, tagged: dict[str, list[str]]) -> set[str]:
    """Which of ``tagged`` fall inside a ``scope`` theme filter.

    ``tagged`` maps document id -> the theme names it is tagged with; the rows
    are classified exactly as ingestion would classify them. The WHERE clause is
    the production one, executed by SQLite so the prefix semantics are the real
    ones rather than a paraphrase.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE t (document_id TEXT, theme TEXT, theme_type TEXT,"
        " parent TEXT, theme_group TEXT, theme_path TEXT, depth INTEGER)"
    )
    for document_id, names in tagged.items():
        for a in theme_taxonomy.classify(names):
            conn.execute(
                "INSERT INTO t VALUES (?, ?, ?, ?, ?, ?, ?)",
                (document_id, a.name, a.theme_type, a.parent, a.group,
                 a.path, a.depth),
            )
    clause, params = queries._theme_scope_clause("t", scope)
    rows = conn.execute(
        f"SELECT DISTINCT document_id FROM t WHERE {clause.replace('%s', '?')}",
        tuple(params),
    ).fetchall()
    conn.close()
    return {r[0] for r in rows}


#: One document per level of the hierarchy, each tagged with exactly one theme
#: and never with its parent — the shape the "a parent is a reference, not a
#: row" rule produces.
_CORPUS = {
    "top": ["Energy"],
    "level2": ["Energy Access"],
    "level3": ["Rural Energy Access"],
    "level4": ["Mini Grids"],
    "sibling2": ["Energy Efficiency"],
    "other-branch": ["Adaptation"],
    "prefix-trap": ["Energy Storage"],
    "unknown": ["Green Hydrogen"],
}


# --------------------------------------------------------------------------- #
# Requirement: a parent-theme query includes every descendant, at any depth.
# --------------------------------------------------------------------------- #

def test_a_parent_theme_query_reaches_every_depth(deep_taxonomy):
    """"How many documents are in Energy?" has to count the document tagged only
    "Mini Grids", four levels down. With one `parent` column it could not: the
    filter was `theme = X OR parent = X`, which stops after one hop."""
    assert _documents_matching("Energy", _CORPUS) == {
        "top", "level2", "level3", "level4", "sibling2",
    }


def test_a_mid_level_theme_query_reaches_its_own_descendants_only(deep_taxonomy):
    """"Energy Access" includes what is under it and excludes its siblings —
    and it works even though no document is tagged "Energy Access"'s parent."""
    assert _documents_matching("Energy Access", _CORPUS) == {
        "level2", "level3", "level4",
    }


def test_an_exact_leaf_query_returns_only_that_leaf(deep_taxonomy):
    assert _documents_matching("Mini Grids", _CORPUS) == {"level4"}


def test_a_sibling_sharing_a_name_prefix_is_not_swept_in(deep_taxonomy):
    """"Energy Storage" starts with "Energy" but is not beneath it. The prefix
    includes the path separator precisely so this cannot match — a bare
    `LIKE 'Energy%'` would have counted it under Energy."""
    assert "prefix-trap" not in _documents_matching("Energy", _CORPUS)
    assert _documents_matching("Energy Storage", _CORPUS) == {"prefix-trap"}


def test_a_separate_branch_is_untouched(deep_taxonomy):
    assert _documents_matching("Climate Change", _CORPUS) == {"other-branch"}
    assert _documents_matching("Adaptation", _CORPUS) == {"other-branch"}


def test_an_unknown_theme_is_queryable_and_has_no_descendants(deep_taxonomy):
    """Requirement: a theme absent from the map must still be countable and
    listable. It expands to itself, because nothing is known to sit under it."""
    assert _documents_matching("Green Hydrogen", _CORPUS) == {"unknown"}


def test_legacy_rows_with_no_path_still_match_by_name_and_parent(deep_taxonomy):
    """The compatibility branch. A deployment that has not run
    `reclassify_theme_rows` yet has NULL paths, and those rows must keep the old
    one-level behaviour instead of silently dropping out of every theme filter.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE t (document_id TEXT, theme TEXT, theme_type TEXT,"
        " parent TEXT, theme_group TEXT, theme_path TEXT, depth INTEGER)"
    )
    conn.executemany(
        "INSERT INTO t VALUES (?, ?, ?, ?, ?, NULL, 1)",
        [
            ("legacy-self", "Energy", "primary", None, "main"),
            ("legacy-child", "Energy Access", "sub", "Energy", "main"),
            # Pre-path rows were flattened onto the primary tag, so a
            # grandchild's `parent` said "Energy". That still resolves.
            ("legacy-grandchild", "Rural Energy Access", "sub", "Energy", "main"),
            ("legacy-elsewhere", "Adaptation", "sub", "Climate Change", "main"),
        ],
    )
    clause, params = queries._theme_scope_clause("t", "Energy")
    rows = conn.execute(
        f"SELECT DISTINCT document_id FROM t WHERE {clause.replace('%s', '?')}",
        tuple(params),
    ).fetchall()
    conn.close()
    assert {r[0] for r in rows} == {
        "legacy-self", "legacy-child", "legacy-grandchild",
    }


# --------------------------------------------------------------------------- #
# Requirement: sparseness. "No theme" is the absence of rows, never a row
# saying so.
# --------------------------------------------------------------------------- #

class _RecordingCursor:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def executemany(self, sql, rows):
        self.calls.append((" ".join(sql.split()), rows))
        return len(rows)

    def fetchone(self):
        return {"n": 0, "document_id": "doc-1"}

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _RecordingConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def cursor(monkeypatch):
    cur = _RecordingCursor()
    monkeypatch.setattr(state, "mysql_connection", lambda: _RecordingConn(cur))
    monkeypatch.setattr(state, "_table", lambda: TABLE)
    return cur


def _record(**kwargs) -> StateRecord:
    return StateRecord(
        **{
            "document_id": "doc-1",
            "source_type": "website",
            "source_key": "https://example.org/x",
            "fingerprint": "2024-02-01",
            **kwargs,
        }
    )


def _theme_rows(cursor) -> list:
    inserts = [
        c for c in cursor.calls
        if c[0].startswith("INSERT") and f"{TABLE}_theme" in c[0]
    ]
    return inserts[0][1] if inserts else []


def test_a_document_with_no_themes_gets_no_theme_row(cursor):
    """Requirement 1. The document itself still persists — only the theme rows
    are absent."""
    state.upsert(_record(categories=[]))

    assert _theme_rows(cursor) == []
    assert any(f"INSERT INTO `{TABLE}` " in sql for sql, _ in cursor.calls)


@pytest.mark.parametrize(
    "categories",
    [
        [],
        ["", None],
        ["Main Themes", "Other Themes"],   # grouping buckets are not themes
        ["False", "None", "null", "nan"],  # stringified non-values
    ],
)
def test_nothing_theme_shaped_is_ever_stored_as_a_placeholder(cursor, categories):
    """Requirement: no empty objects, no NULL rows, no "unknown" row for a
    document that simply has no theme. Each of these inputs has produced junk
    theme rows at some point; none may produce one now."""
    state.upsert(_record(categories=categories))

    assert _theme_rows(cursor) == []


def test_no_theme_is_different_from_an_unrecognised_theme(cursor):
    """The distinction the requirement turns on. An empty facet yields nothing;
    a theme the map has never heard of yields a real, countable row."""
    state.upsert(_record(categories=["Green Hydrogen"]))

    assert _theme_rows(cursor) == [
        ("doc-1", "Green Hydrogen", "unknown", None, None, "Green Hydrogen", 1)
    ]


def test_the_delete_runs_even_with_no_themes_to_write(cursor):
    """Requirement 10, the losing-your-last-theme case: a document that used to
    be themed and no longer is must end up with no rows, not its old ones."""
    state.upsert(_record(categories=[]))

    deletes = [
        c for c in cursor.calls
        if c[0].startswith("DELETE") and f"{TABLE}_theme" in c[0]
    ]
    assert len(deletes) == 1 and deletes[0][1] == ("doc-1",)


# --------------------------------------------------------------------------- #
# Requirement: what a themed document actually stores.
# --------------------------------------------------------------------------- #

def test_a_main_theme_only(cursor, deep_taxonomy):
    state.upsert(_record(categories=["Climate Change"]))

    assert _theme_rows(cursor) == [
        ("doc-1", "Climate Change", "primary", None, "main", "Climate Change", 1)
    ]


def test_a_main_theme_with_several_sub_themes(cursor, deep_taxonomy):
    state.upsert(
        _record(categories=["Energy", "Energy Access", "Energy Efficiency"])
    )

    assert _theme_rows(cursor) == [
        ("doc-1", "Energy", "primary", None, "main", "Energy", 1),
        ("doc-1", "Energy Access", "sub", "Energy", "main",
         "Energy > Energy Access", 2),
        ("doc-1", "Energy Efficiency", "sub", "Energy", "main",
         "Energy > Energy Efficiency", 2),
    ]


def test_several_main_themes(cursor, deep_taxonomy):
    """Both are primary tags with parent NULL; only the group and path tell them
    apart, and one comes from each bucket."""
    state.upsert(_record(categories=["Energy", "Energy Storage"]))

    assert _theme_rows(cursor) == [
        ("doc-1", "Energy", "primary", None, "main", "Energy", 1),
        ("doc-1", "Energy Storage", "primary", None, "other", "Energy Storage", 1),
    ]


def test_a_deep_sub_theme_keeps_its_immediate_parent(cursor, deep_taxonomy):
    """Requirement 7. The row names its own parent, not the primary tag, and the
    path carries the chain that makes the rollup work."""
    state.upsert(_record(categories=["Mini Grids"]))

    assert _theme_rows(cursor) == [
        ("doc-1", "Mini Grids", "sub", "Rural Energy Access", "main",
         "Energy > Energy Access > Rural Energy Access > Mini Grids", 4)
    ]


def test_only_the_themes_the_document_carries_get_rows(cursor, deep_taxonomy):
    """A document tagged one deep theme is credited with one theme. Its four
    ancestors are references, not rows — materialising them would make it count
    as tagged with themes nobody assigned it."""
    state.upsert(_record(categories=["Mini Grids"]))

    assert len(_theme_rows(cursor)) == 1


# --------------------------------------------------------------------------- #
# Requirement: idempotence and duplicate prevention.
# --------------------------------------------------------------------------- #

def test_re_ingestion_replaces_rather_than_accumulates(cursor, deep_taxonomy):
    """Requirement 10. Every write deletes the document's rows first, so a theme
    it no longer carries disappears instead of lingering beside the new set. An
    upsert keyed on (document_id, theme) could only ever add."""
    state.upsert(_record(categories=["Energy", "Adaptation"]))
    first = _theme_rows(cursor)
    cursor.calls.clear()

    state.upsert(_record(categories=["Adaptation"]))

    assert len(first) == 2
    ordered = [c[0].split()[0] for c in cursor.calls if f"{TABLE}_theme" in c[0]]
    assert ordered == ["DELETE", "INSERT"]
    assert [r[1] for r in _theme_rows(cursor)] == ["Adaptation"]


def test_duplicate_and_case_variant_themes_collapse_to_one_row(cursor, deep_taxonomy):
    """Requirement 11. Repeats are dropped in Python; a case variant the
    database's collation would treat as the same key is absorbed by the
    keep-first clause rather than raising 1062 and losing the whole document."""
    state.upsert(
        _record(categories=["Energy", "Energy", "  ENERGY  ", "energy"])
    )

    rows = _theme_rows(cursor)
    assert len(rows) == 1 and rows[0][1] == "Energy"


def test_the_insert_absorbs_a_duplicate_key_and_nothing_else(cursor, deep_taxonomy):
    """`ON DUPLICATE KEY UPDATE document_id = document_id`, not INSERT IGNORE:
    the collation-only collision above must be swallowed while a foreign-key
    violation or an over-long value still fails loudly."""
    state.upsert(_record(categories=["Energy"]))

    sql = next(
        s for s, _ in cursor.calls
        if s.startswith("INSERT") and f"{TABLE}_theme" in s
    )
    assert "ON DUPLICATE KEY UPDATE document_id = document_id" in sql
    assert "IGNORE" not in sql


def test_classification_is_stable_across_repeated_calls(deep_taxonomy):
    """Nothing about a theme's stored shape depends on when it was classified,
    so re-ingesting an unchanged document is a no-op in content as well as in
    row count."""
    once = theme_taxonomy.classify(["Mini Grids", "Energy"])
    twice = theme_taxonomy.classify(["Mini Grids", "Energy"])
    assert once == twice
