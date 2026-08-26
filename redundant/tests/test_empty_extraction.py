"""An empty extraction must never replace a document's indexed content.

The failure this pins down had two halves, either of which was survivable and
which together lost data silently:

* `chunk_canonical` returned no chunks, `index_chunks([])` no-opped, and the
  swap then called `delete_document(id, keep_ids=[])`;
* `[]` was falsy, so the "spare these points" filter became "spare nothing" and
  every point for the document was deleted — after which the run stamped
  `indexed_at` and logged `status="indexed"`.

The document was gone from search and every dashboard said the ingest was
healthy. Both halves are asserted here, plus the reproduction end to end.

Collaborators are stubbed; no MySQL, no Qdrant, no network.
"""

from __future__ import annotations

import pytest

from app.catalog.models import StateRecord
from app.core.clients import vector_store
from app.core.models import CanonicalDocument, CanonicalSection
from app.ingestion import pipeline
from app.ingestion.change_detection import ChangeRecord, ChangeStatus
from app.ingestion.chunking import Chunk


# --------------------------------------------------------------------------- #
# The vector-store guard.
# --------------------------------------------------------------------------- #

class _FakeQdrant:
    """Records deletes instead of performing them."""

    def __init__(self, *, exists: bool = True) -> None:
        self.exists = exists
        self.deletes: list[object] = []

    def collection_exists(self, collection_name: str) -> bool:
        return self.exists

    def delete(self, collection_name: str, points_selector: object) -> None:
        self.deletes.append(points_selector)


@pytest.fixture
def qdrant(monkeypatch) -> _FakeQdrant:
    client = _FakeQdrant()
    monkeypatch.setattr(vector_store, "get_qdrant_client", lambda: client)
    return client


def test_an_empty_keep_list_is_refused(qdrant):
    """The whole bug in one call: `keep_ids=[]` meant "spare nothing"."""
    with pytest.raises(ValueError) as excinfo:
        vector_store.delete_document("doc-1", keep_ids=[])

    assert "doc-1" in str(excinfo.value)
    assert "keep_ids=None" in str(excinfo.value), "the deliberate form is named"
    assert not qdrant.deletes, "nothing may be deleted on the way to raising"


def test_deleting_a_document_outright_still_works(qdrant):
    """`keep_ids=None` is the delete path and the orphan collector; unchanged."""
    vector_store.delete_document("doc-1")

    assert len(qdrant.deletes) == 1
    assert qdrant.deletes[0].filter.must_not is None


def test_a_populated_keep_list_spares_those_points(qdrant):
    vector_store.delete_document("doc-1", keep_ids=["a", "b"])

    must_not = qdrant.deletes[0].filter.must_not
    assert must_not is not None and must_not[0].has_id == ["a", "b"]


def test_an_empty_document_id_is_refused(qdrant):
    with pytest.raises(ValueError):
        vector_store.delete_document("")
    assert not qdrant.deletes


# --------------------------------------------------------------------------- #
# The pipeline guard.
# --------------------------------------------------------------------------- #

def _record(**kwargs) -> ChangeRecord:
    defaults = dict(
        status=ChangeStatus.CHANGED,
        document_id="doc-1",
        source_type="website",
        source_key="https://example.org/brief",
        fingerprint="2026-02-01",
        bundle="policy_brief",
        changed_mark=1234,
        prior=StateRecord(
            document_id="doc-1",
            source_type="website",
            source_key="https://example.org/brief",
            fingerprint="2026-01-01",
            content_hash="old-hash",
            doc_version=3,
            bundle="policy_brief",
        ),
    )
    defaults.update(kwargs)
    return ChangeRecord(**defaults)


def _doc(body: str) -> CanonicalDocument:
    return CanonicalDocument(
        document_id="doc-1",
        source_type="website",
        title="A brief",
        sections=[CanonicalSection(text=body, order=0)] if body else [],
    )


class _World:
    """What the pipeline wrote — or, on the guarded path, did not."""

    def __init__(self) -> None:
        self.points: set[str] = set()
        self.deleted: list[tuple[str, object]] = []
        self.indexed: list[list[Chunk]] = []
        self.upserts: list[tuple[StateRecord, bool]] = []
        self.logs: list[dict] = []
        self.retries: list[dict] = []


@pytest.fixture
def world(monkeypatch, qdrant) -> _World:
    """The pipeline's collaborators, with the *real* delete guard in the middle.

    `delete_document` is not stubbed away: it is the function under test on the
    store side, so the pipeline reaches it exactly as it does in production and
    a `keep_ids=[]` call would raise here too.
    """
    w = _World()

    def index_chunks(chunks):
        chunks = list(chunks)
        w.indexed.append(chunks)
        w.points.update(c.chunk_id for c in chunks)
        return len(chunks)

    def delete_document(document_id, *, keep_ids=None):
        vector_store.delete_document(document_id, keep_ids=keep_ids)
        w.deleted.append((document_id, keep_ids))
        w.points.intersection_update(set(keep_ids or ()))

    monkeypatch.setattr(pipeline, "index_chunks", index_chunks)
    monkeypatch.setattr(pipeline, "delete_document", delete_document)
    monkeypatch.setattr(
        pipeline.state, "upsert", lambda rec, mark_indexed: w.upserts.append((rec, mark_indexed))
    )
    monkeypatch.setattr(pipeline.state, "attachment_ids_for", lambda doc_id: [])
    monkeypatch.setattr(pipeline.state, "orphaned_attachments", lambda ids: [])
    monkeypatch.setattr(pipeline.ingest_log, "record", lambda entry: w.logs.append(vars(entry)))
    monkeypatch.setattr(
        pipeline.retries, "record",
        lambda doc_id, **kw: w.retries.append({"document_id": doc_id, **kw}),
    )
    monkeypatch.setattr(pipeline.retries, "clear", lambda ids: 0)
    monkeypatch.setattr(pipeline, "_enrich", lambda doc, content_hash: "off")
    return w


@pytest.mark.parametrize(
    "body,label",
    [("", "an empty body"), ("   \n\t    ", "a whitespace-only body")],
)
def test_an_empty_extraction_is_an_error_not_a_success(world, body, label):
    outcome = pipeline._handle(_record(), build_doc=lambda r: _doc(body))

    assert outcome == "error", label
    assert world.deleted == [], "the previous version's points must survive"
    assert world.upserts == [], "nothing may claim the document was indexed"
    assert world.logs[-1]["status"] == "error"
    assert world.logs[-1]["chunks_indexed"] == 0


def test_the_error_explains_itself(world):
    pipeline._handle(_record(), build_doc=lambda r: _doc(""))

    message = world.logs[-1]["error_message"]
    assert "no indexable content" in message
    assert "keeping version 3" in message, "the version being protected is named"


def test_the_outcome_writes_a_retry_marker_carrying_the_reason(world):
    """`error` is an unresolved outcome, so the crawl floor pulls the window back
    to it — and the row now says why, which is what makes the retry queue
    triageable rather than a list of ids."""
    record = _record()
    reason: list[str] = []
    outcome = pipeline._handle(
        record, build_doc=lambda r: _doc(""), fail=reason.append
    )
    pipeline._track_retry(record, outcome, frozenset(), error=reason[0])

    assert len(world.retries) == 1
    row = world.retries[0]
    assert row["document_id"] == "doc-1" and row["outcome"] == "error"
    assert row["changed_mark"] == 1234, "the floor needs a crawl position"
    assert "no indexable content" in row["error"]


def test_a_skipped_document_records_why_it_was_skipped(world):
    """A build that returns None (a 404 download, an unreadable file) is the
    other unresolved outcome, and it used to leave `error` NULL too."""
    reason: list[str] = []
    outcome = pipeline._handle(_record(), build_doc=lambda r: None, fail=reason.append)

    assert outcome == "skipped"
    assert "could not be built" in reason[0]
    assert "could not be built" in world.logs[-1]["error_message"]


def test_a_document_with_content_still_indexes(world):
    """The guard must not fire on the healthy path."""
    outcome = pipeline._handle(
        _record(),
        build_doc=lambda r: _doc("Coastal erosion rose along the northern shoreline."),
    )

    assert outcome == "indexed"
    assert world.indexed and world.indexed[0], "chunks reached the indexer"
    document_id, keep_ids = world.deleted[0]
    assert document_id == "doc-1"
    assert keep_ids, "the swap spares the points it just wrote"
    assert world.upserts[0][1] is True, "and only then marks the document indexed"


# --------------------------------------------------------------------------- #
# The original failure, reproduced end to end.
# --------------------------------------------------------------------------- #

def test_reproduction_a_blanked_body_no_longer_wipes_the_document(world):
    """Pass 1 indexes real content; pass 2 finds the body blanked at source.

    Before the fix, pass 2 left zero points and logged `indexed`. The count of
    surviving points is the assertion, not the calls that produced it.
    """
    first = pipeline._handle(
        _record(),
        build_doc=lambda r: _doc("Groundwater salinity rose across the eastern wards."),
    )
    assert first == "indexed" and world.points, "pass 1 must leave the document indexed"
    before = set(world.points)

    second = pipeline._handle(_record(), build_doc=lambda r: _doc(""))

    assert second == "error"
    assert world.points == before, "the blanked re-ingest left the indexed version alone"
    assert [log["status"] for log in world.logs] == ["indexed", "error"]
