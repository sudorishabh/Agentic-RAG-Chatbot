"""Reindexing a document must bring it back, not remove it.

`/reindex` deleted the document's vectors *and* its catalog row. The row is what
positions the incremental crawl — the window is ``changed >= MAX(changed_mark)``
per bundle — so a document whose ``changed`` predated its bundle's high-water
mark could never be fetched again. The repair tool was the most destructive
operation in the system, and it answered ``status="reset"``.

The replacement records a retry marker (which floors the crawl window at the
document) and clears the change markers (so the crawl calls it CHANGED and the
pipeline rebuilds it). Nothing is deleted; the swap in `_handle` replaces the
vectors once the new version exists.

The catalog, the retry table, the extractor and the network are all in memory.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.catalog.models import StateRecord
from app.ingestion.change_detection import ChangeStatus, drupal
from app.ingestion.extractors import drupal_extractor
from app.workers import tasks

BUNDLE = "news"

# The document being repaired sits at the bottom of its bundle; everything else
# has been edited since. This is the shape that made reindex unrecoverable —
# 8,176 of 8,193 website documents were in it.
OLD_MARK = 1515666501      # 2018-01-11
RECENT_MARK = 1783506143   # 2026-07-08


# --------------------------------------------------------------------------- #
# In-memory catalog + retry table.
# --------------------------------------------------------------------------- #

class _Catalog:
    def __init__(self) -> None:
        self.rows: dict[str, StateRecord] = {}
        self.deleted: list[str] = []
        self.cleared: list[str] = []

    def add(self, document_id: str, mark: int) -> StateRecord:
        row = StateRecord(
            document_id=document_id,
            source_type="website",
            source_key=f"https://example.org/{document_id}",
            fingerprint=datetime.fromtimestamp(mark, tz=timezone.utc).isoformat(),
            content_hash=f"hash-of-{document_id}",
            doc_version=4,
            bundle=BUNDLE,
            changed_mark=mark,
        )
        self.rows[document_id] = row
        return row

    # The three catalog calls reindex may make.
    def get(self, document_id: str) -> StateRecord | None:
        return self.rows.get(document_id)

    def delete(self, document_ids) -> int:
        self.deleted.extend(document_ids)
        return len(list(document_ids))

    def clear_change_markers(self, document_id: str) -> bool:
        row = self.rows.get(document_id)
        if row is None:
            return False
        self.cleared.append(document_id)
        # Exactly what the real one writes: the crawl's signal and the
        # pipeline's, and nothing else.
        row.fingerprint = ""
        row.content_hash = ""
        return True


class _Retries:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}

    def ensure_table(self) -> None:
        pass

    def load(self) -> dict[str, dict]:
        return dict(self.items)

    def floors(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self.items.values():
            bundle, mark = item["bundle"], item["changed_mark"]
            if bundle is None or mark is None:
                continue
            out[bundle] = min(out.get(bundle, mark), mark)
        return out

    def record(self, document_id, *, source_type, bundle, changed_mark, outcome, error=None):
        self.items[document_id] = {
            "source_type": source_type, "bundle": bundle,
            "changed_mark": changed_mark, "outcome": outcome, "error": error,
        }

    def clear(self, document_ids) -> int:
        return sum(bool(self.items.pop(d, None)) for d in document_ids)


@pytest.fixture
def catalog(monkeypatch) -> _Catalog:
    site = _Catalog()
    retries = _Retries()
    site.retries = retries

    import app.catalog.retries as retries_module
    import app.catalog.state as state_module

    for attr in ("get", "delete", "clear_change_markers"):
        monkeypatch.setattr(state_module, attr, getattr(site, attr))
    for attr in ("ensure_table", "record", "clear", "load", "floors"):
        monkeypatch.setattr(retries_module, attr, getattr(retries, attr))

    def exploding_delete(*args, **kwargs):
        raise AssertionError("reindex must not delete vectors")

    monkeypatch.setattr("app.core.clients.delete_document", exploding_delete)
    return site


# --------------------------------------------------------------------------- #
# What reindex does, and what it refuses to do.
# --------------------------------------------------------------------------- #

def test_reindex_keeps_the_catalog_row_and_the_vectors(catalog):
    catalog.add("doc-old", OLD_MARK)

    result = tasks.reindex_document("doc-old")

    assert result["status"] == "queued"
    assert catalog.deleted == [], "the catalog row is the crawl's position; it stays"
    assert "doc-old" in catalog.rows
    # delete_document would have raised; reaching here is the vector assertion.


def test_reindex_records_a_retry_marker_at_the_documents_crawl_position(catalog):
    """The floor is what widens the next crawl window far enough to reach it."""
    catalog.add("doc-old", OLD_MARK)

    tasks.reindex_document("doc-old")

    marker = catalog.retries.items["doc-old"]
    assert marker["bundle"] == BUNDLE
    assert marker["changed_mark"] == OLD_MARK
    assert marker["outcome"] == tasks.REINDEX_OUTCOME
    assert marker["outcome"] != "error", "an operator request is not a failure"
    assert "reindex requested" in marker["error"]


def test_reindex_clears_both_change_markers(catalog):
    """The fingerprint is the crawl's test and the content hash is the
    pipeline's. Clearing only the hash leaves the record UNCHANGED, and an
    UNCHANGED record is never even built — so the hash is never consulted."""
    row = catalog.add("doc-old", OLD_MARK)

    tasks.reindex_document("doc-old")

    assert row.fingerprint == ""
    assert row.content_hash == ""
    assert row.changed_mark == OLD_MARK, "its crawl position must survive"
    assert row.doc_version == 4, "the version it still serves is untouched"


def test_reindex_uses_the_catalogued_source_type_not_the_callers(catalog):
    row = catalog.add("doc-old", OLD_MARK)
    row.source_type = "pdf_attachment"

    tasks.reindex_document("doc-old", source_type="website")

    assert catalog.retries.items["doc-old"]["source_type"] == "pdf_attachment"


def test_reindexing_an_unknown_document_writes_nothing(catalog):
    result = tasks.reindex_document("never-seen")

    assert result == {"document_id": "never-seen", "status": "unknown"}
    assert catalog.retries.items == {} and catalog.cleared == []


# --------------------------------------------------------------------------- #
# The regression the audit asked for: does the next crawl fetch it again?
# --------------------------------------------------------------------------- #

@pytest.fixture
def crawl(monkeypatch, catalog):
    """The real change detection over a fake bundle; returns the crawl's asks."""
    asked: list[int | None] = []

    monkeypatch.setattr(
        drupal, "get_settings",
        lambda: SimpleNamespace(drupal_max_retries=1, drupal_block_min_chars=200),
    )
    monkeypatch.setattr(
        drupal.state, "load",
        lambda source_type: dict(catalog.rows) if source_type == "website" else {},
    )
    monkeypatch.setattr(drupal.dead_links, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.dead_links, "load", dict)
    monkeypatch.setattr(drupal, "retries", catalog.retries)
    monkeypatch.setattr(
        drupal_extractor, "_build_session", lambda retries: SimpleNamespace(close=lambda: None)
    )

    def iter_bundle_records(session, bundle, *, changed_since=None, **kw):
        asked.append(changed_since)
        # The live site, answering the filter the crawl actually sent.
        return iter([
            SimpleNamespace(
                uuid=document_id,
                changed=datetime.fromtimestamp(row.changed_mark, tz=timezone.utc).isoformat(),
                source=row.source_key,
                body="A node with enough body text to survive the block filter.",
                files=[],
            )
            for document_id, row in sorted(
                catalog.rows.items(), key=lambda kv: kv[1].changed_mark
            )
            if changed_since is None or row.changed_mark >= changed_since
        ])

    monkeypatch.setattr(drupal_extractor, "iter_bundle_records", iter_bundle_records)
    return asked


def _crawl_once() -> dict[str, ChangeStatus]:
    return {
        record.document_id: record.status
        for record in drupal.detect_drupal_changes(bundles=[BUNDLE])
    }


def test_an_old_document_is_out_of_the_window_until_it_is_reindexed(crawl, catalog):
    """Both halves in one test: the window that stranded it, and the recovery.

    `doc-old` sits 8 years below its bundle's high-water mark, so an ordinary
    sweep never returns it. After a reindex it is fetched again *and* comes back
    as CHANGED, which is what makes the pipeline rebuild it rather than refresh
    a fingerprint.
    """
    catalog.add("doc-old", OLD_MARK)
    catalog.add("doc-recent", RECENT_MARK)

    before = _crawl_once()
    assert crawl[-1] == RECENT_MARK, "the window starts at the high-water mark"
    assert "doc-old" not in before, "which is exactly what stranded it"

    tasks.reindex_document("doc-old")
    after = _crawl_once()

    assert crawl[-1] == OLD_MARK, "the retry floor pulled the window back to it"
    assert after["doc-old"] is ChangeStatus.CHANGED
    assert after["doc-recent"] is ChangeStatus.UNCHANGED, "nothing else re-ingests"


def test_the_recovered_document_carries_its_prior_row_forward(crawl, catalog):
    """CHANGED, not NEW: the row survived, so the rebuild is a new version of a
    known document and `next_version` keeps counting from 4."""
    catalog.add("doc-old", OLD_MARK)
    catalog.add("doc-recent", RECENT_MARK)
    tasks.reindex_document("doc-old")

    record = next(
        r for r in drupal.detect_drupal_changes(bundles=[BUNDLE])
        if r.document_id == "doc-old"
    )

    assert record.prior is not None and record.prior.doc_version == 4
    assert record.changed_mark == OLD_MARK


# --------------------------------------------------------------------------- #
# The catalog write itself, against a scripted cursor. The tests above stub it
# out, so this is what holds its SQL to what it claims to do.
# --------------------------------------------------------------------------- #

class _FakeCursor:
    def __init__(self, exists: bool = True):
        self.exists = exists
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql: str, params: object = None) -> int:
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def fetchone(self):
        return {"1": 1} if self.exists else None

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


@pytest.fixture
def state_cursor(monkeypatch) -> _FakeCursor:
    import app.catalog.state as state_module

    cur = _FakeCursor()
    monkeypatch.setattr(state_module, "mysql_connection", lambda: _FakeConn(cur))
    monkeypatch.setattr(state_module, "_table", lambda: "documents")
    return cur


def test_clear_change_markers_blanks_both_signals_and_nothing_else(state_cursor):
    import app.catalog.state as state_module

    assert state_module.clear_change_markers("doc-old") is True

    update = [c for c in state_cursor.calls if c[0].startswith("UPDATE")][0]
    sql, params = update
    assert "fingerprint = ''" in sql and "content_hash = ''" in sql
    assert "changed_mark" not in sql, "the crawl position must survive"
    assert "indexed_at" not in sql, "the document is still indexed until replaced"
    assert "doc_version" not in sql
    assert params[-1] == "doc-old"


def test_clear_change_markers_reports_an_unknown_document(monkeypatch):
    import app.catalog.state as state_module

    cur = _FakeCursor(exists=False)
    monkeypatch.setattr(state_module, "mysql_connection", lambda: _FakeConn(cur))
    monkeypatch.setattr(state_module, "_table", lambda: "documents")

    assert state_module.clear_change_markers("never-seen") is False
    assert not [c for c in cur.calls if c[0].startswith("UPDATE")]


# --------------------------------------------------------------------------- #
# API semantics.
# --------------------------------------------------------------------------- #

def _client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.ingest import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_the_api_reports_queued_rather_than_reset(catalog):
    """"reset" implied the document had been cleared and would come back. It
    said that while making it unrecoverable."""
    catalog.add("doc-old", OLD_MARK)

    response = _client().post("/reindex", json={"document_id": "doc-old"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["detail"]["changed_mark"] == OLD_MARK


def test_the_api_answers_404_for_a_document_it_does_not_have(catalog):
    response = _client().post("/reindex", json={"document_id": "never-seen"})

    assert response.status_code == 404
    assert "not catalogued" in response.json()["detail"]
