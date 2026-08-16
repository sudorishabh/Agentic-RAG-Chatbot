"""A code change must be able to reach data that is already indexed.

Re-indexing was gated on `content_hash` alone, which covers body text. Four
chunker correctness fixes, a chunk-id scheme change and a payload cleanup all
landed after the corpus was built, and none of them ever reached it: the body
text had not changed, so `content_changed` stayed False forever and ~99% of
stored chunks kept whatever the pipeline produced on the day they were first
seen.

`PIPELINE_VERSION` is the missing signal. It is stamped on the catalog row and
on every point, and a document whose stored version is not the current one is
rebuilt on its next crawl even when its content is byte-identical.

Collaborators are stubbed; no MySQL, Qdrant or network.
"""

from __future__ import annotations

import pytest

from app.catalog.models import StateRecord
from app.core.models import CanonicalDocument, CanonicalSection
from app.ingestion import pipeline, version
from app.ingestion.change_detection import (
    ChangeRecord,
    ChangeStatus,
    content_changed,
    needs_rebuild,
    pipeline_changed,
)
from app.ingestion.chunking import DocumentMeta
from app.ingestion.chunking.payload import build_payload
from app.ingestion.version import PIPELINE_VERSION

BODY = "Groundwater salinity rose across the eastern wards through the decade."


# --------------------------------------------------------------------------- #
# The version itself.
# --------------------------------------------------------------------------- #

def test_the_version_names_every_component_that_forces_a_rebuild():
    """Chunking, chunk identity, payload schema and embedding input — the four
    things whose change makes stored output wrong for the current code."""
    assert PIPELINE_VERSION == (
        f"c{version.CHUNKING}.i{version.CHUNK_IDENTITY}"
        f".p{version.PAYLOAD}.e{version.EMBED_INPUT}"
    )


def test_the_version_fits_the_column_it_is_stored_in():
    assert len(PIPELINE_VERSION) <= 32, "documents.pipeline_version is VARCHAR(32)"


def test_bumping_any_component_changes_the_version(monkeypatch):
    """Each component is load-bearing: none of them can move without the stored
    version moving with it."""
    import importlib

    for component in ("CHUNKING", "CHUNK_IDENTITY", "PAYLOAD", "EMBED_INPUT"):
        module = importlib.reload(version)
        before = module.PIPELINE_VERSION
        monkeypatch.setattr(module, component, getattr(module, component) + 1)
        after = (
            f"c{module.CHUNKING}.i{module.CHUNK_IDENTITY}"
            f".p{module.PAYLOAD}.e{module.EMBED_INPUT}"
        )
        assert after != before, component
    importlib.reload(version)


# --------------------------------------------------------------------------- #
# The predicate.
# --------------------------------------------------------------------------- #

def _prior(**kwargs) -> StateRecord:
    defaults = dict(
        document_id="doc-1",
        source_type="website",
        source_key="https://example.org/brief",
        fingerprint="2026-01-01",
        content_hash="hash-of-the-body",
        doc_version=3,
        pipeline_version=PIPELINE_VERSION,
    )
    defaults.update(kwargs)
    return StateRecord(**defaults)


def _record(**kwargs) -> ChangeRecord:
    defaults = dict(
        status=ChangeStatus.CHANGED,
        document_id="doc-1",
        source_type="website",
        source_key="https://example.org/brief",
        fingerprint="2026-02-01",
        bundle="policy_brief",
        changed_mark=1234,
        prior=_prior(),
    )
    defaults.update(kwargs)
    return ChangeRecord(**defaults)


def test_unchanged_content_on_the_current_version_is_not_rebuilt():
    record = _record()

    assert content_changed(record, "hash-of-the-body") is False
    assert pipeline_changed(record) is False
    assert needs_rebuild(record, "hash-of-the-body") is False


def test_unchanged_content_on_an_older_version_is_rebuilt():
    """The case the corpus was stuck in: identical text, superseded code."""
    record = _record(prior=_prior(pipeline_version="c0.i0.p0.e0"))

    assert content_changed(record, "hash-of-the-body") is False
    assert needs_rebuild(record, "hash-of-the-body") is True


def test_an_unstamped_row_reads_as_stale():
    """Every document indexed before versions existed has NULL here. Unknown has
    to mean stale, or the corpus that most needs rebuilding never gets it."""
    record = _record(prior=_prior(pipeline_version=None))

    assert pipeline_changed(record) is True
    assert needs_rebuild(record, "hash-of-the-body") is True


def test_a_new_document_needs_no_version_comparison():
    record = _record(status=ChangeStatus.NEW, prior=None)

    assert pipeline_changed(record) is False, "nothing to compare"
    assert needs_rebuild(record, "any-hash") is True, "but it is built anyway"


def test_changed_content_is_rebuilt_whatever_the_version():
    record = _record()

    assert needs_rebuild(record, "a-different-hash") is True


# --------------------------------------------------------------------------- #
# What the pipeline does with it.
# --------------------------------------------------------------------------- #

class _World:
    def __init__(self) -> None:
        self.upserts: list[StateRecord] = []
        self.indexed: list[list] = []
        self.titles: list[tuple[str, str | None]] = []


@pytest.fixture
def world(monkeypatch) -> _World:
    w = _World()

    def chunk(doc):
        from types import SimpleNamespace

        return [SimpleNamespace(chunk_id="c-1", text=BODY, is_parent=False)]

    monkeypatch.setattr(pipeline, "chunk_canonical", chunk)
    monkeypatch.setattr(pipeline, "index_chunks", lambda chunks: w.indexed.append(list(chunks)) or len(chunks))
    monkeypatch.setattr(pipeline, "delete_document", lambda doc_id, keep_ids=None: None)
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "_enrich", lambda doc, content_hash: "off")
    monkeypatch.setattr(
        pipeline, "refresh_document_title", lambda doc_id, title: w.titles.append((doc_id, title))
    )
    monkeypatch.setattr(pipeline.state, "attachment_ids_for", lambda doc_id: [])
    monkeypatch.setattr(pipeline.state, "upsert", lambda rec, mark_indexed: w.upserts.append(rec))
    return w


def _doc() -> CanonicalDocument:
    return CanonicalDocument(
        document_id="doc-1",
        source_type="website",
        title="A brief",
        sections=[CanonicalSection(text=BODY, order=0)],
    )


def _hash_of_body() -> str:
    return _doc().ensure_content_hash()


def test_a_stale_version_forces_a_real_reindex(world):
    """Same body, old version: the document is chunked, indexed and versioned
    up, not waved through as unchanged."""
    record = _record(
        prior=_prior(content_hash=_hash_of_body(), pipeline_version="c0.i0.p0.e0")
    )

    outcome = pipeline._handle(record, build_doc=lambda r: _doc())

    assert outcome == "indexed"
    assert world.indexed, "it re-chunked and re-indexed"
    assert world.upserts[0].doc_version == 4, "and counted a new version"


def test_the_current_version_still_short_circuits(world):
    record = _record(prior=_prior(content_hash=_hash_of_body()))

    assert pipeline._handle(record, build_doc=lambda r: _doc()) == "unchanged_content"
    assert world.indexed == [], "no chunking, no embedding, no upsert of points"


def test_an_indexed_document_records_the_version_that_built_it(world):
    record = _record(prior=_prior(content_hash="something-else"))

    pipeline._handle(record, build_doc=lambda r: _doc())

    assert world.upserts[0].pipeline_version == PIPELINE_VERSION


def test_a_fingerprint_refresh_does_not_claim_the_current_version(world):
    """The trap this avoids: if an unchanged-content write stamped the current
    version, a document would be marked rebuilt without being rebuilt, and the
    mismatch that should have forced the rebuild would never fire again.

    None is passed so the upsert's COALESCE keeps whatever is stored.
    """
    record = _record(prior=_prior(content_hash=_hash_of_body()))

    pipeline._handle(record, build_doc=lambda r: _doc())

    assert world.upserts[0].pipeline_version is None


# --------------------------------------------------------------------------- #
# The catalog write. Fake cursors accept any parameter count, so the one thing
# they cannot catch is asserted directly.
# --------------------------------------------------------------------------- #

def test_the_upsert_binds_exactly_as_many_parameters_as_it_declares(monkeypatch):
    """Adding a column means touching the column list, the VALUES list and the
    parameter tuple. Miss one and every write fails against real MySQL while
    every test that stubs the cursor still passes."""
    from app.catalog import state as state_module

    calls: list[tuple[str, tuple]] = []

    class _Cursor:
        def execute(self, sql, params=()):
            calls.append((sql, params))
            return 1

        def executemany(self, sql, rows):
            return len(rows)

        def fetchone(self):
            return None

        def fetchall(self):
            return []

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class _Conn:
        def cursor(self):
            return _Cursor()

        def commit(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(state_module, "mysql_connection", lambda: _Conn())
    monkeypatch.setattr(state_module, "_table", lambda: "documents")

    state_module.upsert(
        StateRecord(
            document_id="doc-1",
            source_type="website",
            source_key="https://example.org/brief",
            fingerprint="f",
            content_hash="h",
            pipeline_version=PIPELINE_VERSION,
        )
    )

    insert = next(sql for sql, _ in calls if "INSERT INTO" in sql)
    params = next(params for sql, params in calls if "INSERT INTO" in sql)
    values = insert.split("VALUES", 1)[1].split(")", 1)[0]
    assert values.count("%s") == len(params)
    assert "pipeline_version" in insert
    assert PIPELINE_VERSION in params


# --------------------------------------------------------------------------- #
# The payload carries it too, so drift is visible from the store.
# --------------------------------------------------------------------------- #

def test_every_point_is_stamped_with_the_pipeline_that_built_it():
    from app.ingestion.chunking.models import Chunk

    chunk = Chunk(
        chunk_id="c-1", text=BODY, is_parent=False,
        meta=DocumentMeta(document_id="doc-1", source_type="website"),
    )

    assert build_payload(chunk)["pipeline_version"] == PIPELINE_VERSION


def test_parents_are_stamped_as_well():
    """A parent is a point in the collection like any other; a reconciliation
    that scrolled for stale points would otherwise report every parent as
    unversioned forever."""
    from app.ingestion.chunking.models import Chunk

    parent = Chunk(
        chunk_id="p-1", text=BODY, is_parent=True,
        meta=DocumentMeta(document_id="doc-1", source_type="website"),
    )

    assert build_payload(parent)["pipeline_version"] == PIPELINE_VERSION
