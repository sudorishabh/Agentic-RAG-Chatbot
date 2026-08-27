"""Unit tests for list_documents paging (LIMIT/OFFSET). All SQL runs against a
scripted fake cursor; no MySQL needed.
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


def test_default_offset_omits_clause(monkeypatch):
    """The overwhelmingly common no-paging call stays byte-stable SQL."""
    cursor = _FakeCursor(fetchall_results=[[]])
    _patch(monkeypatch, cursor)

    state.list_documents(source_type="website")

    sql, _ = cursor.calls[0]
    assert "OFFSET" not in sql


def test_offset_appends_clause(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[]])
    _patch(monkeypatch, cursor)

    state.list_documents(source_type="website", limit=5, offset=10)

    sql, _ = cursor.calls[0]
    assert "LIMIT 5 OFFSET 10" in sql


def test_offset_clamps_negative_to_zero(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[]])
    _patch(monkeypatch, cursor)

    state.list_documents(source_type="website", offset=-5)

    sql, _ = cursor.calls[0]
    assert "OFFSET" not in sql  # clamps to 0, which omits the clause entirely
