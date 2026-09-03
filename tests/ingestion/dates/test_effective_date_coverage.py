"""A document with no publication date is invisible, not merely ranked low.

Date-range filters and the recency tie-break both compare `published_at`, so a
document without one is excluded from every date-filtered query outright. 109
were: 78 `block_content` blocks and the 31 PDFs hanging off them.

The cause was one missing field name. Nodes expose `created`; `block_content`
does not expose it at all — only `changed` and `revision_created` — and the
extractor read `created` alone.

What is *not* done here matters as much: no date is synthesised. A record that
states neither field stays undated, and the pipeline says so rather than filling
the gap with the crawl time.
"""

from __future__ import annotations

import pytest

from app.core.models import CanonicalDocument, CanonicalSection
from app.ingestion import pipeline
from app.ingestion.change_detection import ChangeRecord, ChangeStatus
from app.ingestion.extractors.drupal_extractor import _created_at

NODE_CREATED = "2018-01-11T11:44:54+00:00"
REVISION_CREATED = "2018-01-12T06:36:40+00:00"
CHANGED = "2023-08-01T06:17:39+00:00"


# --------------------------------------------------------------------------- #
# Which field the date comes from.
# --------------------------------------------------------------------------- #

def test_a_node_uses_its_created_date():
    assert _created_at({"created": NODE_CREATED, "changed": CHANGED}) == NODE_CREATED


def test_a_block_falls_back_to_its_revision_timestamp():
    """block_content carries no `created`; this is what the site does state
    about when the record came into being."""
    assert _created_at(
        {"revision_created": REVISION_CREATED, "changed": CHANGED}
    ) == REVISION_CREATED


def test_created_wins_when_both_are_present():
    assert _created_at(
        {"created": NODE_CREATED, "revision_created": REVISION_CREATED}
    ) == NODE_CREATED


def test_changed_is_never_used_as_a_publication_date():
    """It moves on every edit, so it describes the document's last touch rather
    than its origin — a 2018 block edited in 2023 would claim 2023."""
    assert _created_at({"changed": CHANGED}) is None


def test_a_record_stating_no_date_stays_undated():
    """The one thing that must not happen is a date appearing from nowhere."""
    assert _created_at({}) is None
    assert _created_at({"created": None, "revision_created": None}) is None


def test_an_empty_string_is_not_a_date():
    assert _created_at({"created": "", "revision_created": REVISION_CREATED}) == (
        REVISION_CREATED
    )


# --------------------------------------------------------------------------- #
# Detection: an undated document must not pass silently.
# --------------------------------------------------------------------------- #

def _record(**kwargs) -> ChangeRecord:
    defaults = dict(
        status=ChangeStatus.NEW,
        document_id="doc-1",
        source_type="website",
        source_key="https://teriin.org/block",
        fingerprint="f",
        bundle="basic",
    )
    defaults.update(kwargs)
    return ChangeRecord(**defaults)


def _doc(published_at: str | None) -> CanonicalDocument:
    return CanonicalDocument(
        document_id="doc-1",
        source_type="website",
        title="A block",
        sections=[CanonicalSection(text="Body text worth indexing.", order=0)],
        published_at=published_at,
    )


@pytest.fixture
def world(monkeypatch):
    from types import SimpleNamespace

    state: dict = {"upserts": []}
    monkeypatch.setattr(
        pipeline, "chunk_canonical",
        lambda doc: [SimpleNamespace(chunk_id="c-1", text="Body.", is_parent=False)],
    )
    monkeypatch.setattr(pipeline, "index_chunks", lambda chunks: len(chunks))
    monkeypatch.setattr(pipeline, "delete_document", lambda doc_id, keep_ids=None: None)
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "_enrich", lambda doc, content_hash: "off")
    monkeypatch.setattr(pipeline.state, "attachment_ids_for", lambda doc_id: [])
    monkeypatch.setattr(
        pipeline.state, "upsert",
        lambda rec, mark_indexed: state["upserts"].append(rec),
    )
    return state


def test_indexing_without_a_date_is_flagged(world):
    flagged: list[str] = []

    outcome = pipeline._handle(_record(), build_doc=lambda r: _doc(None), flag=flagged.append)

    assert outcome == "indexed", "it is still indexed — this is not a failure"
    assert flagged == ["undated"]


def test_a_dated_document_flags_nothing(world):
    flagged: list[str] = []

    pipeline._handle(_record(), build_doc=lambda r: _doc(NODE_CREATED), flag=flagged.append)

    assert flagged == []


def test_the_date_reaches_the_catalog(world):
    pipeline._handle(_record(), build_doc=lambda r: _doc(NODE_CREATED))

    assert world["upserts"][0].published_at == NODE_CREATED


def test_the_flag_is_optional(world):
    """`_handle` is called directly by the CLI and by tests; counting is opt-in,
    like the enrichment note beside it."""
    assert pipeline._handle(_record(), build_doc=lambda r: _doc(None)) == "indexed"


def test_the_run_counts_undated_documents(monkeypatch):
    """The count belongs on the run line: one warning per document is noise at
    corpus scale, and a total is what says whether it is 3 or 3,000."""
    from types import SimpleNamespace

    settings = SimpleNamespace(
        ingest_max_docs_per_run=0, ingest_batch_size=0,
        ingest_batch_pause_seconds=0.0, ingest_workers=1, enrichment_enabled=False,
    )
    monkeypatch.setattr(pipeline, "get_settings", lambda: settings)
    monkeypatch.setattr(pipeline.state, "ensure_table", lambda: None)
    monkeypatch.setattr(pipeline.ingest_log, "ensure_table", lambda: None)
    monkeypatch.setattr(pipeline, "_pending_retries", frozenset)
    monkeypatch.setattr(pipeline, "_track_retry", lambda *a, **k: None)
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)

    def handle(record, build_doc, run_id, note=None, fail=None, flag=None):
        if flag is not None and record.document_id == "undated-1":
            flag("undated")
        return "indexed"

    monkeypatch.setattr(pipeline, "_handle", handle)

    tally = pipeline._run(
        iter([_record(document_id="dated-1"), _record(document_id="undated-1")]),
        build_doc=lambda r: None,
    )

    assert tally["undated"] == 1
    assert tally["indexed"] == 2, "both are indexed; one is merely dateless"
