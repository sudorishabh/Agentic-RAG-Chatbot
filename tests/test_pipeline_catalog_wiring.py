"""Unit tests for the pipeline -> catalog wiring.

Covers what flows from a built document into the state upsert (term links
from taxonomy refs only, attachment links, raw_meta), the taxonomy-term
mirror (_sync_term with parent resolution), and term-row cleanup on DELETED
records. Collaborators are stubbed; no MySQL, Qdrant, or network.
"""

from __future__ import annotations

from app.core.models import CanonicalDocument, EntityRef, FileLink
from app.ingestion import pipeline
from app.ingestion.change_detection import ChangeRecord, ChangeStatus, _parse_bundle_spec
from app.ingestion.state import AttachmentLink, TermLink


def test_parse_bundle_spec():
    assert _parse_bundle_spec("report") == ("node", "report", True)
    assert _parse_bundle_spec("taxonomy_term:themes") == ("taxonomy_term", "themes", False)
    assert _parse_bundle_spec("block_content:basic") == ("block_content", "basic", False)


def _record(**kwargs) -> ChangeRecord:
    defaults = dict(
        status=ChangeStatus.NEW,
        document_id="doc-1",
        source_type="website",
        source_key="https://example.org/brief",
        fingerprint="2024-02-01",
        bundle="policy_brief",
        changed_mark=1234,
    )
    defaults.update(kwargs)
    return ChangeRecord(**defaults)


def _doc(**kwargs) -> CanonicalDocument:
    defaults = dict(document_id="doc-1", source_type="website", title="A brief")
    defaults.update(kwargs)
    return CanonicalDocument(**defaults)


# --------------------------------------------------------------------------- #
# _save_state — doc fields land on the StateRecord.
# --------------------------------------------------------------------------- #

def test_save_state_maps_links_and_raw_meta(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        pipeline.state, "upsert", lambda rec, mark_indexed: captured.update(rec=rec)
    )

    doc = _doc(
        entity_refs=[
            EntityRef("field_focus", "t-climate", "taxonomy_term--themes", "Climate"),
            EntityRef("parent", "t-env", "taxonomy_term--themes", "Environment"),
            EntityRef("field_author", "p-jane", "node--people", "Jane Doe"),
        ],
        file_links=[FileLink("f1", "attachment", url="https://x/a.pdf", filename="a.pdf")],
        raw_meta={"field_isbn": "978-81-7993"},
    )
    pipeline._save_state(_record(entity_type="node"), doc, "hash", 1, indexed=True)

    rec = captured["rec"]
    assert rec.entity_type == "node"
    # Taxonomy refs (including parent) become term links; people refs do not.
    assert rec.term_links == [
        TermLink("t-climate", "field_focus"),
        TermLink("t-env", "parent"),
    ]
    assert rec.attachments == [
        AttachmentLink("f1", "attachment", url="https://x/a.pdf", filename="a.pdf")
    ]
    assert rec.raw_meta == {"field_isbn": "978-81-7993"}


def test_save_state_empty_doc_stays_lean(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        pipeline.state, "upsert", lambda rec, mark_indexed: captured.update(rec=rec)
    )
    pipeline._save_state(_record(), _doc(), "hash", 1, indexed=False)
    rec = captured["rec"]
    assert rec.term_links == [] and rec.attachments == [] and rec.raw_meta is None


# --------------------------------------------------------------------------- #
# _sync_term — taxonomy records mirror into the term catalog.
# --------------------------------------------------------------------------- #

def test_sync_term_upserts_with_parent(monkeypatch):
    captured = {}

    def fake_upsert(term_uuid, vocabulary, name, *, parent_uuid=None, changed_mark=None):
        captured.update(
            uuid=term_uuid, vocab=vocabulary, name=name,
            parent=parent_uuid, mark=changed_mark,
        )
        return False

    monkeypatch.setattr(pipeline.terms, "upsert_term", fake_upsert)

    record = _record(document_id="t-air", bundle="themes", entity_type="taxonomy_term")
    doc = _doc(
        document_id="t-air",
        title="Air",
        entity_refs=[EntityRef("parent", "t-env", "taxonomy_term--themes", "Environment")],
    )
    pipeline._sync_term(record, doc)

    assert captured == {
        "uuid": "t-air", "vocab": "themes", "name": "Air",
        "parent": "t-env", "mark": 1234,
    }


def test_sync_term_rename_triggers_payload_refresh(monkeypatch):
    refreshed = {}
    monkeypatch.setattr(
        pipeline.terms, "upsert_term", lambda *a, **k: "Climate"  # rename detected
    )
    monkeypatch.setattr(
        pipeline.payload_refresh,
        "refresh_renamed_term",
        lambda uuid, old, new: refreshed.update(uuid=uuid, old=old, new=new) or 1,
    )

    record = _record(document_id="t1", bundle="themes", entity_type="taxonomy_term")
    pipeline._sync_term(record, _doc(document_id="t1", title="Climate Action"))

    assert refreshed == {"uuid": "t1", "old": "Climate", "new": "Climate Action"}


def test_sync_term_refresh_failure_does_not_abort_ingest(monkeypatch):
    monkeypatch.setattr(pipeline.terms, "upsert_term", lambda *a, **k: "Climate")
    monkeypatch.setattr(
        pipeline.payload_refresh,
        "refresh_renamed_term",
        lambda *a: (_ for _ in ()).throw(RuntimeError("qdrant down")),
    )
    record = _record(document_id="t1", bundle="themes", entity_type="taxonomy_term")
    pipeline._sync_term(record, _doc(document_id="t1", title="Climate Action"))  # no raise


def test_sync_term_ignores_non_taxonomy_records(monkeypatch):
    monkeypatch.setattr(
        pipeline.terms, "upsert_term",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not be called")),
    )
    pipeline._sync_term(_record(entity_type="node"), _doc())
    pipeline._sync_term(_record(entity_type=None), _doc())


# --------------------------------------------------------------------------- #
# Attachment docs inherit the node's refs and facets.
# --------------------------------------------------------------------------- #

class _FakePage:
    def __init__(self, n: int, text: str):
        self.page_number = n
        self.text = text


class _FakePdfResult:
    source = "a.pdf"
    pages = [_FakePage(1, "PDF body text about climate policy.")]


def test_attachment_doc_inherits_node_refs_and_facets(monkeypatch):
    from types import SimpleNamespace

    from app.ingestion.extractors import pdf_extractor

    monkeypatch.setattr(pipeline, "_fetch_attachment", lambda s, url, t: (b"%PDF-", url))
    monkeypatch.setattr(pdf_extractor, "extract_pdf", lambda content, name: _FakePdfResult())

    node = SimpleNamespace(
        uuid="node-1",
        title="A report",
        url="https://example.org/report",
        created="2024-01-01T00:00:00+00:00",
        bundle="report",
        metadata={"field_report_tags": ["Coal"]},
        refs=[EntityRef("field_report_theme", "t-energy", "taxonomy_term--themes", "Energy")],
    )
    file = SimpleNamespace(
        uuid="f1", url="https://example.org/a.pdf", filename="a.pdf",
        description=None, origin="attachment",
    )
    record = _record(
        document_id="f1", source_type="pdf_attachment", payload=(node, file)
    )

    doc = pipeline._build_attachment_doc(record, session=None)

    assert doc.source_type == "pdf_attachment"
    assert doc.linked_article_uuid == "node-1"
    # Inherited from the node: refs (-> term_ids/theme_ids + catalog links)
    # and display facets, so theme-scoped retrieval reaches the PDF.
    assert [r.uuid for r in doc.entity_refs] == ["t-energy"]
    assert doc.categories == ["Energy"]
    assert doc.tags == ["Coal"]


# --------------------------------------------------------------------------- #
# DELETED — taxonomy terms are removed from the term catalog too.
# --------------------------------------------------------------------------- #

def _patch_delete_path(monkeypatch, calls: dict):
    monkeypatch.setattr(
        pipeline, "delete_document", lambda doc_id, keep_ids=None: calls.update(qdrant=doc_id)
    )
    monkeypatch.setattr(pipeline.state, "delete", lambda ids: calls.update(state=list(ids)))
    monkeypatch.setattr(
        pipeline.terms, "delete_terms", lambda ids: calls.update(terms=list(ids))
    )
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)


def test_handle_deleted_taxonomy_term_removes_term_row(monkeypatch):
    calls: dict = {}
    _patch_delete_path(monkeypatch, calls)

    record = _record(
        status=ChangeStatus.DELETED, document_id="t-air",
        bundle="themes", entity_type="taxonomy_term",
    )
    assert pipeline._handle(record, build_doc=lambda r: None) == "deleted"
    assert calls == {"qdrant": "t-air", "state": ["t-air"], "terms": ["t-air"]}


def test_handle_deleted_node_leaves_term_catalog_alone(monkeypatch):
    calls: dict = {}
    _patch_delete_path(monkeypatch, calls)

    record = _record(status=ChangeStatus.DELETED, entity_type="node")
    assert pipeline._handle(record, build_doc=lambda r: None) == "deleted"
    assert "terms" not in calls
