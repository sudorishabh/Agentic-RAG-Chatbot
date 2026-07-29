"""Unit tests for the tag scope in the catalog SQL layer.

Covers the tag join in isolation and, most importantly, that a tag filter and
a theme filter combine as two independent joins (AND), never one merged IN
list (which would silently turn the query into an OR). All SQL runs against a
scripted fake cursor; no MySQL needed.
"""

from __future__ import annotations

from app.catalog import queries as state


class _FakeCursor:
    def __init__(self, fetchall_results: list | None = None,
                 fetchone_results: list | None = None):
        self.fetchall_results = list(fetchall_results or [])
        self.fetchone_results = list(fetchone_results or [])
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql: str, params: object = None) -> int:
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []

    def fetchone(self):
        return self.fetchone_results.pop(0) if self.fetchone_results else None

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


def test_count_by_tag_uuids_joins_second_term_alias(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"n": 4}])
    _patch(monkeypatch, cursor)

    total = state.count_documents(
        source_type="website", bundle="news", tag_uuids=["tag1", "tag2"]
    )
    assert total == 4
    sql, params = cursor.calls[0]
    assert "COUNT(DISTINCT s.document_id)" in sql
    assert "_term` tt" in sql and "tt.term_uuid IN (%s, %s)" in sql
    assert params == ("website", "news", "tag1", "tag2")


def test_tag_and_theme_are_two_separate_joins(monkeypatch):
    """The regression that matters: theme and tag must AND, not merge into
    one IN list — a post has to satisfy both filters, not either."""
    cursor = _FakeCursor(fetchone_results=[{"n": 1}])
    _patch(monkeypatch, cursor)

    state.count_documents(
        source_type="website", term_uuids=["theme1"], tag_uuids=["tag1"],
    )
    sql, params = cursor.calls[0]
    assert "_term` dt" in sql and "dt.term_uuid IN (%s)" in sql
    assert "_term` tt" in sql and "tt.term_uuid IN (%s)" in sql
    assert sql.count("JOIN") == 2  # two independent joins, not one shared IN list
    assert params == ("website", "theme1", "tag1")


def test_list_documents_applies_tag_scope(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[]])
    _patch(monkeypatch, cursor)

    state.list_documents(source_type="website", tag_uuids=["tag1"])
    sql, params = cursor.calls[0]
    assert "_term` tt" in sql and "tt.term_uuid IN (%s)" in sql
    assert "DISTINCT" in sql
    assert params == ("website", "tag1")


def test_distribution_scoped_by_tag_is_not_a_group_dimension(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": "report", "n": 2}]])
    _patch(monkeypatch, cursor)

    rows = state.distribution("bundle", tag_uuids=["tag1"])
    assert rows == [("report", 2)]
    sql, params = cursor.calls[0]
    assert "_term` tt" in sql and "tt.term_uuid IN (%s)" in sql
    assert params == ("website", "tag1")

    try:
        state.distribution("tag")
    except ValueError:
        pass
    else:
        raise AssertionError("tag is a scope filter, not a groupable dimension")


def test_no_tag_filter_omits_the_join(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"n": 9}])
    _patch(monkeypatch, cursor)

    state.count_documents(source_type="website")
    sql, _ = cursor.calls[0]
    assert "_term` tt" not in sql
