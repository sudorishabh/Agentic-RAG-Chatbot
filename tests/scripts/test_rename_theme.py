"""Unit tests for ``scripts.rename_theme``.

A theme is named in three places once the hierarchy is materialized — ``theme``,
``parent`` and every segment of ``theme_path`` — and the path is the one the
descendant expansion reads. A rename that moved the first two and not the third
would leave the rows in place but unreachable through their parent, which is a
worse failure than not renaming at all: the count changes and nothing errors.

The segment-wise rewrite is the other thing worth pinning. "Energy" is a
substring of "Energy Access", so a SQL ``REPLACE`` over the path would rename
the sibling too.
"""

from __future__ import annotations

import pytest

from scripts import rename_theme


class _Cursor:
    """Answers the two COUNT probes and the path scan, and records writes."""

    def __init__(self, as_theme: int, as_parent: int, paths: list[str]):
        self._counts = [as_theme, as_parent]
        self._paths = [{"theme_path": p} for p in paths]
        self.writes: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        flat = " ".join(sql.split())
        if flat.startswith("SELECT"):
            self._last = flat
        else:
            self.writes.append((flat, params))
        return 1

    def fetchone(self):
        return {"n": self._counts.pop(0)}

    def fetchall(self):
        return list(self._paths)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _Conn:
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


@pytest.fixture
def run(monkeypatch):
    """Returns a callable: (argv, rows...) -> (exit code, cursor)."""

    def _run(argv, *, as_theme=1, as_parent=0, paths=()):
        cursor = _Cursor(as_theme, as_parent, list(paths))
        monkeypatch.setattr(rename_theme, "mysql_connection", lambda: _Conn(cursor))
        monkeypatch.setattr(rename_theme, "state_table", lambda: "documents")
        return rename_theme.main(argv), cursor

    return _run


def _path_writes(cursor):
    return [
        params for sql, params in cursor.writes if "SET theme_path" in sql
    ]


def test_the_path_is_rewritten_segment_by_segment(run):
    """Every path carrying the old name as a segment moves, at any position:
    as the leaf, in the middle, and as the root."""
    code, cursor = run(
        ["Energy Access", "Electricity Access", "--apply"],
        paths=[
            "Energy > Energy Access",
            "Energy > Energy Access > Rural Energy Access",
            "Energy > Energy Efficiency",
        ],
    )

    assert code == 0
    assert set(_path_writes(cursor)) == {
        ("Energy > Electricity Access", "Energy > Energy Access"),
        (
            "Energy > Electricity Access > Rural Energy Access",
            "Energy > Energy Access > Rural Energy Access",
        ),
    }


def test_a_root_segment_rename_moves_every_descendant_path(run):
    code, cursor = run(
        ["Energy", "Power", "--apply"],
        paths=["Energy", "Energy > Energy Access", "Climate Change > Adaptation"],
    )

    assert code == 0
    assert set(_path_writes(cursor)) == {
        ("Power", "Energy"),
        ("Power > Energy Access", "Energy > Energy Access"),
    }


def test_a_sibling_whose_name_contains_the_old_one_is_untouched(run):
    """The regression a SQL REPLACE would cause: renaming "Energy" must not
    touch "Energy Access", which merely starts with the same word."""
    code, cursor = run(["Energy", "Power", "--apply"], paths=["Energy > Energy Access"])

    assert code == 0
    written = _path_writes(cursor)
    assert written == [("Power > Energy Access", "Energy > Energy Access")]
    assert "Power > Power Access" not in [w[0] for w in written]


def test_theme_and_parent_move_alongside_the_path(run):
    code, cursor = run(["Air", "Atmosphere", "--apply"], as_theme=4, as_parent=2,
                       paths=["Environment > Air"])

    assert code == 0
    verbs = [sql.split(" WHERE ")[0] for sql, _ in cursor.writes]
    assert any("SET theme = %s" in v for v in verbs)
    assert any("SET parent = %s" in v for v in verbs)
    assert any("SET theme_path = %s" in v for v in verbs)


def test_a_dry_run_writes_nothing(run):
    code, cursor = run(["Air", "Atmosphere"], paths=["Environment > Air"])

    assert code == 0
    assert cursor.writes == []


def test_identical_names_are_a_no_op(run, monkeypatch):
    """Checked before any connection is opened."""
    monkeypatch.setattr(
        rename_theme,
        "mysql_connection",
        lambda: pytest.fail("opened a connection for a no-op rename"),
    )
    assert rename_theme.main(["Air", "Air", "--apply"]) == 0


def test_a_name_nothing_carries_reports_a_miss(run):
    """Including in the paths — a theme could in principle appear only as an
    ancestor segment, so all three sources have to be empty to call it a miss."""
    code, cursor = run(
        ["Nonexistent", "Whatever", "--apply"], as_theme=0, as_parent=0, paths=[]
    )

    assert code == 1
    assert cursor.writes == []


def test_rows_with_no_path_yet_still_rename(run):
    """A deployment that has not backfilled `theme_path` has nothing to rewrite
    there, but the theme/parent rename must still go through."""
    code, cursor = run(["Air", "Atmosphere", "--apply"], as_theme=3, paths=[])

    assert code == 0
    assert _path_writes(cursor) == []
    assert any("SET theme = %s" in sql for sql, _ in cursor.writes)
