"""Unit tests for the rename-driven payload display refresh.

Covers the theme-facet rewrite helper and the orchestration in
``refresh_renamed_term`` (MySQL facet + Qdrant set_payload per affected
document, catalog-only when the collection is missing). Qdrant and the
state helpers are stubbed; no datastores needed.
"""

from __future__ import annotations

from app.catalog import payload_refresh, state


class _FakeQdrant:
    def __init__(self, exists: bool = True):
        self.exists = exists
        self.calls: list[tuple[str, dict, object]] = []

    def collection_exists(self, name: str) -> bool:
        return self.exists

    def set_payload(self, collection_name: str, payload: dict, points) -> None:
        self.calls.append((collection_name, payload, points))


def _patch_state(monkeypatch, docs: list[str], facets: dict[str, list[str]]):
    monkeypatch.setattr(
        payload_refresh.state, "documents_for_term", lambda uuid: list(docs)
    )
    monkeypatch.setattr(
        payload_refresh.state,
        "rename_theme_facet",
        lambda doc_id, old, new: facets[doc_id],
    )


def test_refresh_updates_facet_and_payload_per_document(monkeypatch):
    client = _FakeQdrant()
    monkeypatch.setattr(payload_refresh, "get_qdrant_client", lambda: client)
    _patch_state(
        monkeypatch,
        docs=["d1", "d2"],
        facets={"d1": ["Climate Action"], "d2": ["Climate Action", "Energy"]},
    )

    assert payload_refresh.refresh_renamed_term("t1", "Climate", "Climate Action") == 2

    assert [c[1] for c in client.calls] == [
        {"categories": ["Climate Action"]},
        {"categories": ["Climate Action", "Energy"]},
    ]
    # Each set_payload targets exactly one document by payload filter.
    targeted = [c[2].must[0] for c in client.calls]
    assert [t.key for t in targeted] == ["document_id", "document_id"]
    assert [t.match.value for t in targeted] == ["d1", "d2"]


def test_refresh_no_linked_documents_is_a_noop(monkeypatch):
    client = _FakeQdrant()
    monkeypatch.setattr(payload_refresh, "get_qdrant_client", lambda: client)
    _patch_state(monkeypatch, docs=[], facets={})

    assert payload_refresh.refresh_renamed_term("t1", "Old", "New") == 0
    assert client.calls == []


def test_refresh_missing_collection_still_fixes_catalog(monkeypatch):
    client = _FakeQdrant(exists=False)
    monkeypatch.setattr(payload_refresh, "get_qdrant_client", lambda: client)
    touched: list[str] = []

    monkeypatch.setattr(payload_refresh.state, "documents_for_term", lambda uuid: ["d1"])
    monkeypatch.setattr(
        payload_refresh.state,
        "rename_theme_facet",
        lambda doc_id, old, new: touched.append(doc_id) or ["New"],
    )

    assert payload_refresh.refresh_renamed_term("t1", "Old", "New") == 1
    assert touched == ["d1"]      # MySQL facet still rewritten
    assert client.calls == []     # no Qdrant writes attempted


# --------------------------------------------------------------------------- #
# state.rename_theme_facet — rewrite semantics over a fake connection.
# --------------------------------------------------------------------------- #

class _FakeCursor:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql: str, params: object = None) -> int:
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def executemany(self, sql: str, rows: list) -> int:
        self.calls.append((" ".join(sql.split()), rows))
        return len(rows)

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
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


def test_rename_theme_facet_replaces_and_dedupes(monkeypatch):
    # "Climate Action" already present alongside old "Climate": must collapse.
    cursor = _FakeCursor(rows=[{"theme": "Climate"}, {"theme": "Climate Action"}])
    conn = _FakeConn(cursor)
    monkeypatch.setattr(state, "mysql_connection", lambda: conn)

    result = state.rename_theme_facet("d1", "Climate", "Climate Action")

    assert result == ["Climate Action"]
    inserts = [c for c in cursor.calls if isinstance(c[1], list)]
    assert inserts and inserts[0][1] == [("d1", "Climate Action")]
    assert conn.commits == 1


def test_rename_theme_facet_untouched_document_writes_nothing(monkeypatch):
    cursor = _FakeCursor(rows=[{"theme": "Energy"}])
    conn = _FakeConn(cursor)
    monkeypatch.setattr(state, "mysql_connection", lambda: conn)

    assert state.rename_theme_facet("d1", "Climate", "Climate Action") == ["Energy"]
    assert conn.commits == 0  # read-only when the term name isn't present
