"""Unit tests for the retrieval-side MySQL catalog readers.

Covers the id-set scope selection (joins, params, DISTINCT, clamping), author
disambiguation lookup, and the attachment join. All SQL runs against scripted
fakes; no MySQL, Qdrant, or LLM needed.
"""

from __future__ import annotations

from datetime import datetime

from app.catalog import queries as catalog


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


def test_ids_in_scope_theme_join_distinct_and_param_order(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[{"document_id": "d1"}]])
    _patch(monkeypatch, cursor)

    catalog.document_ids_in_scope(
        theme="Environment",
        author="Sharma",
        published_from=datetime(2024, 1, 1),
        limit=30,
    )

    sql, params = cursor.calls[0]
    assert sql.startswith("SELECT DISTINCT s.document_id, s.published_at")
    assert "_theme` c" in sql and "(c.theme = %s OR c.parent = %s)" in sql
    assert "_author` a" in sql and "a.author LIKE %s" in sql
    assert "LIMIT 30" in sql
    assert params == (
        "website", "node", datetime(2024, 1, 1), "%Sharma%", "Environment", "Environment",
    )


def test_ids_in_scope_theme_and_tag_join_independently(monkeypatch):
    cursor = _FakeCursor(fetchall_results=[[]])
    _patch(monkeypatch, cursor)

    catalog.document_ids_in_scope(theme="Climate", tag="solar")

    sql, _ = cursor.calls[0]
    # Theme and tag are independent joins, so a document must satisfy both.
    assert "_theme` c" in sql and "_tag` t" in sql


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
