"""Unit tests for the distinct-name catalog readers backing entity resolution
(app.retrieval.structured.resolve). All SQL runs against a scripted fake
cursor; no MySQL needed.
"""

from __future__ import annotations

from app.catalog import queries as state


class _FakeCursor:
    def __init__(self, fetchall_results: list | None = None):
        self.fetchall_results = list(fetchall_results or [])
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql: str, params: object = None) -> int:
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _patch(monkeypatch, cursor):
    monkeypatch.setattr(state, "mysql_connection", lambda: _FakeConn(cursor))


def test_distinct_authors_filters_blank_and_returns_names(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[
        {"author": "Rishabh Negi"}, {"author": ""}, {"author": "A Sharma"},
    ]])
    _patch(monkeypatch, cursor)

    names = state.distinct_authors()
    assert names == ["Rishabh Negi", "A Sharma"]
    sql, params = cursor.calls[0]
    assert sql.startswith("SELECT DISTINCT author FROM")
    assert "ORDER BY author ASC" in sql and "LIMIT 2000" in sql
    assert params is None


def test_distinct_authors_clamps_limit(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[], []])
    _patch(monkeypatch, cursor)

    state.distinct_authors(limit=99999)
    state.distinct_authors(limit=-3)

    assert "LIMIT 5000" in cursor.calls[0][0]
    assert "LIMIT 1" in cursor.calls[1][0]


def test_distinct_themes_filters_blank_and_returns_names(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[
        {"theme": "Climate"}, {"theme": None}, {"theme": "Energy"},
    ]])
    _patch(monkeypatch, cursor)

    names = state.distinct_themes()
    assert names == ["Climate", "Energy"]
    sql, _ = cursor.calls[0]
    assert sql.startswith("SELECT DISTINCT theme FROM")
    assert "_theme` ORDER BY theme ASC LIMIT 500" in sql


def test_distinct_themes_clamps_limit(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[], []])
    _patch(monkeypatch, cursor)

    state.distinct_themes(limit=99999)
    state.distinct_themes(limit=-3)

    assert "LIMIT 2000" in cursor.calls[0][0]
    assert "LIMIT 1" in cursor.calls[1][0]
