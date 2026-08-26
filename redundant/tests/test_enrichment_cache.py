"""Unit tests for the ingest-time enrichment cache.

Runs against a fake cursor that models the one-row-per-content-hash table and
applies the ON DUPLICATE KEY semantics the real statements rely on, so the
version-invalidation and attempt-counting rules are observable without MySQL.
"""

from __future__ import annotations

from app.catalog import enrichment, schema

TABLE = "documents"
HASH = "a" * 64
V1 = "v1-fingerprint"
V2 = "v2-fingerprint"


class _FakeCursor:
    """An in-memory {content_hash: row} store behind the two write statements.

    The writes are distinguished by whether they carry an abstract (``put``) or
    a NULL abstract plus an error (``record_failure``); everything else is
    modelled from the parameters, including the version-reset rule for attempts.
    """

    def __init__(self, rows: dict[str, dict] | None = None):
        self.rows = dict(rows or {})
        self.statements: list[str] = []
        self._result: dict | None = None

    def execute(self, sql: str, params: tuple = ()) -> None:
        flat = " ".join(sql.split())
        self.statements.append(flat)
        if flat.startswith("SELECT"):
            content_hash, version = params
            row = self.rows.get(content_hash)
            self._result = row if row and row["version"] == version else None
            return
        if flat.startswith("CREATE TABLE"):
            return
        if "abstract = VALUES(abstract)" in flat:
            content_hash, version, abstract, updated = params
            self.rows[content_hash] = {
                "content_hash": content_hash, "version": version,
                "abstract": abstract, "attempts": 0, "last_error": None,
                "updated_at": updated,
            }
            return
        # record_failure
        content_hash, version, error, updated = params
        prior = self.rows.get(content_hash)
        attempts = prior["attempts"] + 1 if prior and prior["version"] == version else 1
        self.rows[content_hash] = {
            "content_hash": content_hash, "version": version,
            "abstract": prior["abstract"] if prior and prior["version"] == version else None,
            "attempts": attempts, "last_error": error, "updated_at": updated,
        }

    def fetchone(self):
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
    monkeypatch.setattr(enrichment, "_table", lambda: TABLE)
    monkeypatch.setattr(enrichment, "mysql_connection", lambda: _FakeConn(cursor))
    return cursor


# --------------------------------------------------------------------------- #
# get / put — the hit-and-miss contract.
# --------------------------------------------------------------------------- #

def test_put_then_get_round_trips(monkeypatch):
    cursor = _patch(monkeypatch, _FakeCursor())

    enrichment.put(HASH, version=V1, abstract="A short abstract.")
    hit = enrichment.get(HASH, version=V1)

    assert hit is not None
    assert hit.abstract == "A short abstract."
    assert hit.attempts == 0


def test_get_misses_on_unknown_content(monkeypatch):
    _patch(monkeypatch, _FakeCursor())
    assert enrichment.get(HASH, version=V1) is None


def test_a_version_change_reads_as_a_miss(monkeypatch):
    """A retuned prompt or a new model must transparently re-enrich rather than
    serve output produced by the old one."""
    cursor = _patch(monkeypatch, _FakeCursor())
    enrichment.put(HASH, version=V1, abstract="Produced by the old prompt.")

    assert enrichment.get(HASH, version=V2) is None
    assert enrichment.get(HASH, version=V1) is not None


def test_an_empty_content_hash_never_touches_the_database(monkeypatch):
    cursor = _patch(monkeypatch, _FakeCursor())

    assert enrichment.get("", version=V1) is None
    enrichment.put("", version=V1, abstract="x")
    enrichment.record_failure("", version=V1, error="x")

    assert cursor.statements == []


# --------------------------------------------------------------------------- #
# record_failure — a hopeless document must stop costing money every sweep.
# --------------------------------------------------------------------------- #

def test_failures_accumulate_across_runs(monkeypatch):
    cursor = _patch(monkeypatch, _FakeCursor())

    enrichment.record_failure(HASH, version=V1, error="timeout")
    enrichment.record_failure(HASH, version=V1, error="timeout again")

    row = enrichment.get(HASH, version=V1)
    assert row is not None
    assert row.attempts == 2
    assert row.abstract is None
    assert row.last_error == "timeout again"


def test_a_version_change_resets_the_attempt_budget(monkeypatch):
    """A new prompt deserves a fresh start — otherwise a document that failed
    under an old prompt stays permanently un-enrichable."""
    cursor = _patch(monkeypatch, _FakeCursor())
    enrichment.record_failure(HASH, version=V1, error="boom")
    enrichment.record_failure(HASH, version=V1, error="boom")

    enrichment.record_failure(HASH, version=V2, error="boom")

    row = enrichment.get(HASH, version=V2)
    assert row is not None and row.attempts == 1


def test_success_clears_a_prior_failure_record(monkeypatch):
    cursor = _patch(monkeypatch, _FakeCursor())
    enrichment.record_failure(HASH, version=V1, error="transient")

    enrichment.put(HASH, version=V1, abstract="Recovered.")

    row = enrichment.get(HASH, version=V1)
    assert row is not None
    assert row.abstract == "Recovered."
    assert row.attempts == 0
    assert row.last_error is None


def test_long_errors_are_clipped_to_fit_the_column(monkeypatch):
    cursor = _patch(monkeypatch, _FakeCursor())

    enrichment.record_failure(HASH, version=V1, error="x" * 5000)

    row = enrichment.get(HASH, version=V1)
    assert row is not None and len(row.last_error) == 1000


def test_writes_are_committed(monkeypatch):
    cursor = _FakeCursor()
    conns: list[_FakeConn] = []
    monkeypatch.setattr(enrichment, "_table", lambda: TABLE)
    monkeypatch.setattr(
        enrichment, "mysql_connection", lambda: conns.append(_FakeConn(cursor)) or conns[-1]
    )

    enrichment.put(HASH, version=V1, abstract="A.")

    assert conns[-1].commits == 1


# --------------------------------------------------------------------------- #
# DDL.
# --------------------------------------------------------------------------- #

def test_ensure_enrichment_table_is_keyed_by_content_hash(monkeypatch):
    """Keying on content_hash (not document_id) is what lets the cache survive a
    state reset and be shared by identical content — assert it stays that way."""
    cursor = _FakeCursor()
    monkeypatch.setattr(schema, "state_table", lambda: TABLE)
    monkeypatch.setattr(schema, "mysql_connection", lambda: _FakeConn(cursor))

    schema.ensure_enrichment_table()

    ddl = cursor.statements[0]
    assert f"CREATE TABLE IF NOT EXISTS `{TABLE}_enrichment`" in ddl
    assert "PRIMARY KEY (content_hash)" in ddl
    assert "FOREIGN KEY" not in ddl
