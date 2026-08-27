"""Unit tests for the dead-attachment-link markers.

Runs against a fake cursor that models the one-row-per-document table and
applies the ON DUPLICATE KEY semantics the write statement relies on, so the
fingerprint-reset rule is observable without MySQL.
"""

from __future__ import annotations

from app.catalog import dead_links

TABLE = "documents"
DOC = "inbody:abc123"
URL = "https://teriin.org/sites/default/files/files/gone.pdf"
F1 = "inbody:abc123"
F2 = "2026-08-04T10:00:00"


class _FakeCursor:
    """An in-memory {document_id: row} store behind the module's statements."""

    def __init__(self, rows: dict[str, dict] | None = None):
        self.rows = dict(rows or {})
        self.statements: list[str] = []
        self._result: list[dict] = []

    def execute(self, sql: str, params: tuple = ()) -> int:
        flat = " ".join(sql.split())
        self.statements.append(flat)
        if flat.startswith("SELECT"):
            self._result = list(self.rows.values())
            return len(self._result)
        if flat.startswith("DELETE"):
            removed = [d for d in params if d in self.rows]
            for document_id in removed:
                del self.rows[document_id]
            return len(removed)
        if flat.startswith("CREATE TABLE"):
            return 0

        document_id, fingerprint, url, status, first_seen, updated = params
        prior = self.rows.get(document_id)
        same = prior is not None and prior["fingerprint"] == fingerprint
        self.rows[document_id] = {
            "document_id": document_id,
            "fingerprint": fingerprint,
            "url": url,
            "status": status,
            "attempts": prior["attempts"] + 1 if same else 1,
            "first_seen": prior["first_seen"] if same else first_seen,
            "updated_at": updated,
        }
        return 1

    def fetchall(self):
        return self._result

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


def _patch(monkeypatch, cursor):
    monkeypatch.setattr(dead_links, "_table", lambda: TABLE)
    monkeypatch.setattr(dead_links, "mysql_connection", lambda: _FakeConn(cursor))
    return cursor


# --------------------------------------------------------------------------- #
# record / load — the marker round-trips.
# --------------------------------------------------------------------------- #

def test_record_then_load_round_trips(monkeypatch):
    _patch(monkeypatch, _FakeCursor())

    dead_links.record(DOC, fingerprint=F1, url=URL, status=404)
    marked = dead_links.load()

    assert list(marked) == [DOC]
    assert marked[DOC].fingerprint == F1
    assert marked[DOC].url == URL
    assert marked[DOC].status == 404
    assert marked[DOC].attempts == 1


def test_load_is_empty_when_nothing_is_marked(monkeypatch):
    _patch(monkeypatch, _FakeCursor())
    assert dead_links.load() == {}


# --------------------------------------------------------------------------- #
# The fingerprint qualifies the marker.
# --------------------------------------------------------------------------- #

def test_the_same_fingerprint_counts_another_attempt(monkeypatch):
    """Two sweeps reaching the URL before the marker takes effect must not read
    as two different dead states."""
    _patch(monkeypatch, _FakeCursor())

    dead_links.record(DOC, fingerprint=F1, url=URL, status=404)
    dead_links.record(DOC, fingerprint=F1, url=URL, status=404)

    marker = dead_links.load()[DOC]
    assert marker.attempts == 2
    assert marker.first_seen is not None


def test_a_new_fingerprint_restarts_the_count(monkeypatch):
    """The source changed, so the old marker described a state that is gone."""
    _patch(monkeypatch, _FakeCursor())

    dead_links.record(DOC, fingerprint=F1, url=URL, status=404)
    dead_links.record(DOC, fingerprint=F2, url=URL, status=410)

    marker = dead_links.load()[DOC]
    assert marker.fingerprint == F2
    assert marker.status == 410
    assert marker.attempts == 1


# --------------------------------------------------------------------------- #
# clear — the escape hatch for a link the site restored.
# --------------------------------------------------------------------------- #

def test_clear_removes_the_marker(monkeypatch):
    _patch(monkeypatch, _FakeCursor())
    dead_links.record(DOC, fingerprint=F1, url=URL, status=404)

    assert dead_links.clear([DOC]) == 1
    assert dead_links.load() == {}


def test_clear_without_ids_never_touches_the_database(monkeypatch):
    cursor = _patch(monkeypatch, _FakeCursor())

    assert dead_links.clear([]) == 0
    assert dead_links.clear(["", None]) == 0
    assert cursor.statements == []


def test_an_empty_document_id_never_touches_the_database(monkeypatch):
    cursor = _patch(monkeypatch, _FakeCursor())

    dead_links.record("", fingerprint=F1, url=URL, status=404)
    assert cursor.statements == []
