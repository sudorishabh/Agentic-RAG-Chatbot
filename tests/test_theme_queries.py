"""Unit tests for the theme-scoped structured queries and distribution path.

Covers term-name resolution (current name, alias fallback), the term/category
filters in the catalog SQL, the distribution query shape, the router's theme
scoping and distribution answer, and the semantic-path theme filter. All SQL
runs against scripted fakes; the LLM parse is never invoked.
"""

from __future__ import annotations

from app.catalog import queries as state
from app.catalog import terms
from app.retrieval import query_processor as qp


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

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _patch(monkeypatch, module, cursor):
    monkeypatch.setattr(module, "mysql_connection", lambda: _FakeConn(cursor))


# --------------------------------------------------------------------------- #
# terms.resolve_terms — current names first, aliases as fallback.
# --------------------------------------------------------------------------- #

def test_resolve_terms_current_name_wins(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"term_uuid": "t1", "name": "Climate"}]])
    _patch(monkeypatch, terms, cursor)

    assert terms.resolve_terms("climate") == [{"term_uuid": "t1", "name": "Climate"}]
    assert len(cursor.calls) == 1  # alias table never consulted


def test_resolve_terms_alias_fallback(monkeypatch):
    cursor = _FakeCursor(
        fetchall_results=[[], [{"term_uuid": "t1", "name": "Climate Action"}]]
    )
    _patch(monkeypatch, terms, cursor)

    rows = terms.resolve_terms("Climate")  # old name, renamed since
    assert rows == [{"term_uuid": "t1", "name": "Climate Action"}]
    assert "alias" in cursor.calls[1][0]


def test_resolve_terms_blank_returns_empty(monkeypatch):
    cursor = _FakeCursor()
    _patch(monkeypatch, terms, cursor)
    assert terms.resolve_terms("  ") == []
    assert cursor.calls == []


# --------------------------------------------------------------------------- #
# Catalog SQL — term/category scoping and distribution.
# --------------------------------------------------------------------------- #

def test_count_by_term_uuids_joins_link_table(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"n": 7}])
    _patch(monkeypatch, state, cursor)

    total = state.count_documents(
        source_type="website", bundle="policy_brief", term_uuids=["t1", "t2"]
    )
    assert total == 7
    sql, params = cursor.calls[0]
    assert "COUNT(DISTINCT s.document_id)" in sql
    assert "_term` dt" in sql and "dt.term_uuid IN (%s, %s)" in sql
    assert params == ("website", "policy_brief", "t1", "t2")


def test_count_scoped_to_entity_type(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"n": 5}])
    _patch(monkeypatch, state, cursor)

    assert state.count_documents(source_type="website", entity_type="node") == 5
    sql, params = cursor.calls[0]
    assert "s.entity_type = %s" in sql
    assert params == ("website", "node")


def test_distribution_scoped_to_entity_type(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": "report", "n": 8}]])
    _patch(monkeypatch, state, cursor)

    assert state.distribution("bundle", entity_type="node") == [("report", 8)]
    sql, params = cursor.calls[0]
    assert "s.entity_type = %s" in sql and params == ("website", "node")


def test_count_by_category_name_fallback(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"n": 3}])
    _patch(monkeypatch, state, cursor)

    assert state.count_documents(source_type="website", category="Climate") == 3
    sql, params = cursor.calls[0]
    assert "_category` c" in sql and "c.category LIKE %s" in sql
    assert params == ("website", "%Climate%")


def test_distribution_by_category(monkeypatch):
    cursor = _FakeCursor(
        fetchall_results=[[{"k": "Climate", "n": 12}, {"k": "Energy", "n": 5}]]
    )
    _patch(monkeypatch, state, cursor)

    rows = state.distribution("category")
    assert rows == [("Climate", 12), ("Energy", 5)]
    sql, _ = cursor.calls[0]
    assert "GROUP BY k ORDER BY n DESC" in sql and "_category` f" in sql


def test_distribution_scoped_by_term_and_author(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": "2024", "n": 4}]])
    _patch(monkeypatch, state, cursor)

    rows = state.distribution(
        "year", term_uuids=["t1"], author="Sharma", limit=20,
    )
    assert rows == [("2024", 4)]
    sql, params = cursor.calls[0]
    # Scope joins apply, so undated rows drop and documents are counted once.
    assert "_term` dt" in sql and "dt.term_uuid IN (%s)" in sql
    assert "_author` a" in sql and "a.author LIKE %s" in sql
    assert "COUNT(DISTINCT s.document_id)" in sql
    assert params == ("website", "%Sharma%", "t1")


def test_distribution_by_year_skips_undated(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": 2024, "n": 9}]])
    _patch(monkeypatch, state, cursor)

    assert state.distribution("year") == [("2024", 9)]
    sql, _ = cursor.calls[0]
    assert "YEAR(s.published_at)" in sql and "IS NOT NULL" in sql


def test_distribution_rejects_unknown_dimension():
    try:
        state.distribution("acl")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown dimension must raise")


# --------------------------------------------------------------------------- #
# Semantic path — theme filter over the vector search.
#
# The router's theme-scoping and distribution answer are now covered by the
# database package (test_database_tools / test_database_registry).
# --------------------------------------------------------------------------- #

def test_theme_condition_matches_uuids_or_names(monkeypatch):
    monkeypatch.setattr(
        terms, "resolve_terms",
        lambda name: [{"term_uuid": "t1", "name": "Climate Action"}],
    )
    condition = qp._theme_condition("climate action")

    legs = {c.key: c for c in condition.should}
    assert legs["theme_ids"].match.any == ["t1"]
    # Display-name leg covers points indexed before term_ids existed, and
    # includes the canonical name alongside the user's phrasing.
    assert "Climate Action" in legs["categories"].match.any


def test_theme_condition_survives_catalog_outage(monkeypatch):
    def boom(name):
        raise RuntimeError("mysql down")

    monkeypatch.setattr(terms, "resolve_terms", boom)
    condition = qp._theme_condition("Climate")

    assert [c.key for c in condition.should] == ["categories"]
    assert "Climate" in condition.should[0].match.any
