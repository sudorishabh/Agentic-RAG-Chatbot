"""Unit tests for the term catalog and the entity-link state writes.

Exercises the SQL wiring against a scripted fake connection — rename
detection + alias archiving in ``terms.upsert_term``, and the term/attachment
link + raw_meta writes inside ``state.upsert``. No MySQL needed; the real SQL
runs in ``app/local_tests``.
"""

from __future__ import annotations

import json

from app.catalog import state, terms
from app.catalog.models import AttachmentLink, StateRecord, TermLink


class _FakeCursor:
    def __init__(self, fetchone_results: list | None = None):
        self.results = list(fetchone_results or [])
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql: str, params: object = None) -> int:
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def executemany(self, sql: str, rows: list) -> int:
        self.calls.append((" ".join(sql.split()), rows))
        return len(rows)

    def fetchone(self):
        return self.results.pop(0) if self.results else None

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


def _patch(monkeypatch, module, cursor: _FakeCursor) -> _FakeConn:
    conn = _FakeConn(cursor)
    monkeypatch.setattr(module, "mysql_connection", lambda: conn)
    return conn


def _sql(cursor: _FakeCursor, verb: str) -> list[tuple[str, object]]:
    return [c for c in cursor.calls if c[0].startswith(verb)]


# --------------------------------------------------------------------------- #
# terms.upsert_term — rename detection and alias archiving.
# --------------------------------------------------------------------------- #

def test_upsert_new_term_no_alias(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[None])  # no prior row
    conn = _patch(monkeypatch, terms, cursor)

    assert terms.upsert_term("t1", "themes", "Climate") is None
    assert not [c for c in cursor.calls if "alias" in c[0].lower()]
    assert conn.commits == 1


def test_upsert_same_name_no_alias(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"name": "Climate"}])
    _patch(monkeypatch, terms, cursor)

    assert terms.upsert_term("t1", "themes", "Climate") is None
    assert not [c for c in cursor.calls if "alias" in c[0].lower()]


def test_upsert_rename_archives_old_name(monkeypatch):
    cursor = _FakeCursor(fetchone_results=[{"name": "Climate"}])
    _patch(monkeypatch, terms, cursor)

    # The archived previous name comes back — the payload-refresh trigger.
    assert terms.upsert_term("t1", "themes", "Climate Action") == "Climate"

    alias_calls = [c for c in cursor.calls if "taxonomy_term_alias" in c[0]]
    assert len(alias_calls) == 1
    _, params = alias_calls[0]
    assert params[0] == "t1" and params[1] == "Climate"  # old name archived

    upserts = [c for c in cursor.calls if "ON DUPLICATE KEY" in c[0]]
    assert upserts and upserts[0][1][2] == "Climate Action"  # new name stored


def test_upsert_rejects_blank_identity(monkeypatch):
    cursor = _FakeCursor()
    _patch(monkeypatch, terms, cursor)
    assert terms.upsert_term("", "themes", "X") is None
    assert terms.upsert_term("t1", "themes", "  ") is None
    assert cursor.calls == []


# --------------------------------------------------------------------------- #
# state.upsert — term/attachment links and raw_meta in one transaction.
# --------------------------------------------------------------------------- #

def _record() -> StateRecord:
    return StateRecord(
        document_id="doc-1",
        source_type="website",
        source_key="https://example.org/brief",
        fingerprint="2024-02-01",
        term_links=[
            TermLink("t-climate", "field_focus"),
            TermLink("t-climate", "field_focus"),  # duplicate — must collapse
            TermLink("", "field_focus"),           # blank uuid — must drop
        ],
        attachments=[
            AttachmentLink("f1", "attachment", url="https://x/a.pdf", filename="a.pdf"),
            AttachmentLink("f1", "inbody"),        # same file — first wins
        ],
        raw_meta={"field_isbn": "978-81-7993"},
    )


def test_upsert_writes_links_and_raw_meta(monkeypatch):
    cursor = _FakeCursor()
    conn = _patch(monkeypatch, state, cursor)

    state.upsert(_record())

    term_inserts = [c for c in cursor.calls if "_term` (document_id" in c[0]]
    assert len(term_inserts) == 1
    assert term_inserts[0][1] == [("doc-1", "t-climate", "field_focus")]

    att_inserts = [c for c in cursor.calls if "_attachment` (file_uuid" in c[0]]
    assert len(att_inserts) == 1
    assert att_inserts[0][1] == [("f1", "doc-1", "attachment", "https://x/a.pdf", "a.pdf")]

    insert_sql, insert_params = _sql(cursor, "INSERT INTO")[0]
    assert "raw_meta" in insert_sql
    json_params = [p for p in insert_params if isinstance(p, str) and p.startswith("{")]
    assert [json.loads(p) for p in json_params] == [{"field_isbn": "978-81-7993"}]

    assert conn.commits == 1  # everything in one transaction


def test_upsert_without_links_clears_stale_rows(monkeypatch):
    cursor = _FakeCursor()
    _patch(monkeypatch, state, cursor)

    state.upsert(
        StateRecord(
            document_id="doc-2",
            source_type="pdf",
            source_key="a.pdf",
            fingerprint="abc",
        )
    )

    deletes = [c[0] for c in _sql(cursor, "DELETE")]
    assert any("_term" in d for d in deletes)
    assert any("_attachment" in d for d in deletes)
    # No link rows to insert, and raw_meta stays NULL.
    assert not [c for c in cursor.calls if isinstance(c[1], list)]
    _, insert_params = _sql(cursor, "INSERT INTO")[0]
    assert not [p for p in insert_params if isinstance(p, str) and p.startswith("{")]
