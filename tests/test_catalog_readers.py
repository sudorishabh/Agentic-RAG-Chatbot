"""Unit tests for the retrieval-side MySQL catalog readers.

Covers the id-set scope selection (joins, params, DISTINCT, clamping), author
disambiguation lookup, the attachment join, and the theme-scoped distribution
that ``state.distribution`` lacks. All SQL runs against scripted fakes; no
MySQL, Qdrant, or LLM needed.
"""

from __future__ import annotations

from datetime import datetime

from app.retrieval import catalog


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
    monkeypatch.setattr(catalog, "mysql_connection", lambda: _FakeConn(cursor))


# --------------------------------------------------------------------------- #
# document_ids_in_scope — membership selection for id-scoped retrieval.
# --------------------------------------------------------------------------- #

def test_ids_in_scope_bakes_in_website_nodes(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"document_id": "d1"}, {"document_id": "d2"}]])
    _patch(monkeypatch, cursor)

    ids = catalog.document_ids_in_scope(bundle="news")

    assert ids == ["d1", "d2"]
    sql, params = cursor.calls[0]
    assert "s.source_type = %s" in sql and "s.entity_type = %s" in sql
    assert "ORDER BY s.published_at DESC" in sql and "LIMIT 150" in sql
    assert "DISTINCT" not in sql  # no facet join -> no duplicate rows
    assert params == ("website", "node", "news")


def test_ids_in_scope_term_join_distinct_and_param_order(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"document_id": "d1"}]])
    _patch(monkeypatch, cursor)

    catalog.document_ids_in_scope(
        term_uuids=["t1", "t2"],
        author="Sharma",
        published_from=datetime(2024, 1, 1),
        limit=30,
    )

    sql, params = cursor.calls[0]
    assert sql.startswith("SELECT DISTINCT s.document_id, s.published_at")
    assert "_term` dt" in sql and "dt.term_uuid IN (%s, %s)" in sql
    assert "_author` a" in sql and "a.author LIKE %s" in sql
    assert "LIMIT 30" in sql
    assert params == ("website", "node", datetime(2024, 1, 1), "%Sharma%", "t1", "t2")


def test_ids_in_scope_category_fallback_only_without_terms(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[]])
    _patch(monkeypatch, cursor)

    catalog.document_ids_in_scope(term_uuids=["t1"], category="Climate")

    sql, _ = cursor.calls[0]
    assert "_term` dt" in sql and "_category`" not in sql  # uuids win


def test_ids_in_scope_clamps_limit(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[], []])
    _patch(monkeypatch, cursor)

    catalog.document_ids_in_scope(limit=9999)
    catalog.document_ids_in_scope(limit=-3)

    assert "LIMIT 300" in cursor.calls[0][0]
    assert "LIMIT 1" in cursor.calls[1][0]


def test_ids_in_scope_fails_open(monkeypatch):
    def boom():
        raise RuntimeError("mysql down")

    monkeypatch.setattr(catalog, "mysql_connection", boom)
    assert catalog.document_ids_in_scope(bundle="news") == []


# --------------------------------------------------------------------------- #
# authors_matching — disambiguation lookup.
# --------------------------------------------------------------------------- #

def test_authors_matching_shape_and_escaping(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"author": "Dr R K Sharma"}]])
    _patch(monkeypatch, cursor)

    assert catalog.authors_matching("50%_Sharma") == ["Dr R K Sharma"]
    sql, params = cursor.calls[0]
    assert "SELECT DISTINCT author" in sql and "_author`" in sql
    assert "ORDER BY author ASC LIMIT 10" in sql
    assert params == (r"%50\%\_Sharma%",)


def test_authors_matching_blank_skips_query(monkeypatch):
    cursor = _FakeCursor()
    _patch(monkeypatch, cursor)
    assert catalog.authors_matching("   ") == []
    assert cursor.calls == []


# --------------------------------------------------------------------------- #
# attachments_for — website -> attached-PDF join.
# --------------------------------------------------------------------------- #

def test_attachments_for_keys_rows_by_document(monkeypatch):
    rows = [
        {"document_id": "d1", "file_uuid": "f1", "origin": "attachment",
         "url": "https://t/f1.pdf", "filename": "f1.pdf"},
        {"document_id": "d1", "file_uuid": "f2", "origin": "inbody",
         "url": "https://t/f2.pdf", "filename": "f2.pdf"},
        {"document_id": "d2", "file_uuid": "f3", "origin": "attachment",
         "url": None, "filename": None},
    ]
    cursor = _FakeCursor(fetchall_results=[rows])
    _patch(monkeypatch, cursor)

    out = catalog.attachments_for(["d1", "d2"])

    assert [a["file_uuid"] for a in out["d1"]] == ["f1", "f2"]
    assert out["d2"][0]["origin"] == "attachment"
    sql, params = cursor.calls[0]
    assert "_attachment` WHERE document_id IN (%s, %s)" in sql
    assert params == ("d1", "d2")


def test_attachments_for_empty_ids_skip_query(monkeypatch):
    cursor = _FakeCursor()
    _patch(monkeypatch, cursor)
    assert catalog.attachments_for([]) == {}
    assert catalog.attachments_for(["", None]) == {}
    assert cursor.calls == []


def test_attachments_for_fails_open(monkeypatch):
    def boom():
        raise RuntimeError("mysql down")

    monkeypatch.setattr(catalog, "mysql_connection", boom)
    assert catalog.attachments_for(["d1"]) == {}


# --------------------------------------------------------------------------- #
# distribution_scoped — theme-scoped breakdowns.
# --------------------------------------------------------------------------- #

def test_distribution_scoped_by_author_joins_both_tables(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": "Sharma", "n": 4}, {"k": None, "n": 1}]])
    _patch(monkeypatch, cursor)

    rows = catalog.distribution_scoped("author", term_uuids=["t1", "t2"])

    assert rows == [("Sharma", 4)]  # NULL group dropped
    sql, params = cursor.calls[0]
    assert "_term` dt" in sql and "_author` f" in sql
    assert "COUNT(DISTINCT s.document_id)" in sql
    assert "GROUP BY k ORDER BY n DESC, k ASC LIMIT 20" in sql
    assert params == ("website", "node", "t1", "t2")


def test_distribution_scoped_by_year_skips_undated(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"k": 2024, "n": 9}]])
    _patch(monkeypatch, cursor)

    assert catalog.distribution_scoped("year", term_uuids=["t1"]) == [("2024", 9)]
    sql, _ = cursor.calls[0]
    assert "YEAR(s.published_at)" in sql and "IS NOT NULL" in sql


def test_distribution_scoped_rejects_unknown_dimension():
    try:
        catalog.distribution_scoped("acl", term_uuids=["t1"])
    except ValueError:
        pass
    else:
        raise AssertionError("unknown dimension must raise")


def test_distribution_scoped_empty_terms_returns_empty(monkeypatch):
    cursor = _FakeCursor()
    _patch(monkeypatch, cursor)
    assert catalog.distribution_scoped("bundle", term_uuids=[]) == []
    assert cursor.calls == []
