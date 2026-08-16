"""Unit tests for the pipeline -> catalog wiring.

Covers what flows from a built document into the state upsert (facets, attachment
links, raw_meta), the persist ordering, and DELETED cleanup. Collaborators are
stubbed; no MySQL, Qdrant, or network.
"""

from __future__ import annotations

from app.core.models import CanonicalDocument, EntityRef, FileLink
from app.ingestion import pipeline
from app.ingestion.change_detection import ChangeRecord, ChangeStatus, _parse_bundle_spec
from app.catalog.models import AttachmentLink, StateRecord


def test_parse_bundle_spec():
    """Parsing only. Whether a parsed source may be crawled is decided later,
    by `_searchable_sources` — see tests/test_searchable_sources.py — so an
    entity type the crawl refuses still parses cleanly here."""
    assert _parse_bundle_spec("report") == ("node", "report", True)
    assert _parse_bundle_spec("block_content:basic") == ("block_content", "basic", False)
    assert _parse_bundle_spec("taxonomy_term:themes") == ("taxonomy_term", "themes", False)


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


def _chunk(chunk_id: str = "chunk-1", text: str = "Body text worth indexing."):
    """The smallest thing the swap accepts: an id to spare, and real text."""
    from types import SimpleNamespace

    return SimpleNamespace(chunk_id=chunk_id, text=text, is_parent=False)


# --------------------------------------------------------------------------- #
# _save_state — doc fields land on the StateRecord.
# --------------------------------------------------------------------------- #

def test_save_state_maps_links_and_raw_meta(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        pipeline.state, "upsert", lambda rec, mark_indexed: captured.update(rec=rec)
    )

    doc = _doc(
        categories=["Climate Change"],
        tags=["Coal", "Solar"],
        authors=["Jane Doe"],
        file_links=[FileLink("f1", "attachment", url="https://x/a.pdf", filename="a.pdf")],
        raw_meta={"field_isbn": "978-81-7993"},
    )
    pipeline._save_state(_record(entity_type="node"), doc, "hash", 1, indexed=True)

    rec = captured["rec"]
    assert rec.entity_type == "node"
    # Facets are carried by name — themes, tags and authors each get their own
    # child table; there is no UUID link row any more.
    assert rec.categories == ["Climate Change"]
    assert rec.tags == ["Coal", "Solar"]
    assert rec.authors == ["Jane Doe"]
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
    assert rec.categories == [] and rec.tags == [] and rec.attachments == []
    assert rec.raw_meta is None






# --------------------------------------------------------------------------- #
# _handle — the content record is persisted before any theme/term data.
# --------------------------------------------------------------------------- #

def _patch_persist_order(monkeypatch, order: list[str]):
    monkeypatch.setattr(
        pipeline, "_save_state", lambda *a, **k: order.append("save_state")
    )
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    # Holds the "no Qdrant, no network" invariant on the unchanged_content path,
    # which refreshes a drifted payload title. Tests that care re-patch it.
    monkeypatch.setattr(pipeline, "refresh_document_title", lambda *a, **k: None)
    # Same for enrichment: it is off by default, but these tests must not depend
    # on a deployment's .env for that. See test_pipeline_enrichment.py.
    monkeypatch.setattr(pipeline, "_enrich", lambda doc, content_hash: "off")
    # A document that already exists has its links read before they are replaced,
    # so that a PDF it drops can be released. Covered by
    # tests/test_attachment_orphans.py; here it must reach no catalog.
    monkeypatch.setattr(pipeline.state, "attachment_ids_for", lambda doc_id: [])


def test_handle_saves_the_content_record(monkeypatch):
    """The document row is the FK target every facet row hangs off, so it is
    written before anything derived from it."""
    order: list[str] = []
    _patch_persist_order(monkeypatch, order)
    # One real chunk, not zero: a document that chunks to nothing is an error
    # outcome now (tests/test_empty_extraction.py), and this test is about the
    # write ordering on the path that succeeds.
    monkeypatch.setattr(pipeline, "chunk_canonical", lambda doc: [_chunk()])
    monkeypatch.setattr(pipeline, "index_chunks", lambda chunks: len(chunks))
    monkeypatch.setattr(pipeline, "delete_document", lambda doc_id, keep_ids=None: None)

    record = _record(document_id="n-air", bundle="research_papers", entity_type="node")
    doc = _doc(document_id="n-air", title="Air quality in Indian cities")

    assert pipeline._handle(record, build_doc=lambda r: doc) == "indexed"
    assert order == ["save_state"]


def test_handle_unchanged_content_keeps_the_same_order(monkeypatch):
    """The fingerprint-refresh path returns early, so it needs the ordering in
    its own right — it is the branch a re-crawl takes most often."""
    order: list[str] = []
    _patch_persist_order(monkeypatch, order)

    doc = _doc(document_id="n-air", title="Air quality in Indian cities")
    prior = StateRecord(
        document_id="n-air",
        source_type="website",
        source_key="https://example.org/research/air",
        fingerprint="2024-01-01",
        content_hash=doc.ensure_content_hash(),  # unchanged content
        doc_version=3,
    )
    record = _record(
        document_id="n-air", bundle="research_papers", entity_type="node", prior=prior
    )

    assert pipeline._handle(record, build_doc=lambda r: doc) == "unchanged_content"
    assert order == ["save_state"]


def _unchanged_content_prior(doc: CanonicalDocument, title: str | None) -> StateRecord:
    return StateRecord(
        document_id="doc-1",
        source_type="website",
        source_key="https://example.org/brief",
        fingerprint="2024-01-01",
        content_hash=doc.ensure_content_hash(),  # unchanged content
        doc_version=3,
        title=title,
    )


def test_unchanged_content_refreshes_a_drifted_payload_title(monkeypatch):
    """A title-only edit no longer re-indexes (the hash covers body text only),
    so the payload title has to be carried over without a re-embed."""
    _patch_persist_order(monkeypatch, [])
    calls: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        pipeline, "refresh_document_title",
        lambda doc_id, title: calls.append((doc_id, title)),
    )

    doc = _doc(title="A brief, retitled")
    record = _record(prior=_unchanged_content_prior(doc, "A brief"))

    assert pipeline._handle(record, build_doc=lambda r: doc) == "unchanged_content"
    assert calls == [("doc-1", "A brief, retitled")]


def test_unchanged_content_leaves_an_unchanged_title_alone(monkeypatch):
    _patch_persist_order(monkeypatch, [])
    calls: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        pipeline, "refresh_document_title",
        lambda doc_id, title: calls.append((doc_id, title)),
    )

    doc = _doc(title="A brief")
    record = _record(prior=_unchanged_content_prior(doc, "A brief"))

    assert pipeline._handle(record, build_doc=lambda r: doc) == "unchanged_content"
    assert calls == []


def test_handle_skips_both_when_no_document_is_built(monkeypatch):
    order: list[str] = []
    _patch_persist_order(monkeypatch, order)

    assert pipeline._handle(_record(), build_doc=lambda r: None) == "skipped"
    assert order == []


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

    from app.ingestion.extractors import attachment, pdf_extractor

    monkeypatch.setattr(attachment, "fetch_attachment", lambda s, url, t: (b"%PDF-", url))
    monkeypatch.setattr(pdf_extractor, "extract_pdf", lambda content, name: _FakePdfResult())
    # Recording the date decision is orthogonal to what this test asserts, and
    # it writes to MySQL; silence it so the test stays offline.
    monkeypatch.setattr(attachment, "_record_date_decision", lambda *a, **k: None)

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

    doc = attachment.build_attachment_doc(record, session=None)

    assert doc.source_type == "pdf_attachment"
    assert doc.linked_article_uuid == "node-1"
    # Inherited from the node: refs (-> term_ids/theme_ids + catalog links)
    # and display facets, so theme-scoped retrieval reaches the PDF.
    assert [r.uuid for r in doc.entity_refs] == ["t-energy"]
    assert doc.categories == ["Energy"]
    assert doc.tags == ["Coal"]


# --------------------------------------------------------------------------- #
# DELETED — the document row and its vectors go; facet rows cascade.
# --------------------------------------------------------------------------- #

def test_handle_deleted_removes_vectors_and_state(monkeypatch):
    calls: dict = {}
    monkeypatch.setattr(
        pipeline, "delete_document", lambda doc_id, keep_ids=None: calls.update(qdrant=doc_id)
    )
    monkeypatch.setattr(pipeline.state, "delete", lambda ids: calls.update(state=list(ids)))
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    # A document with no attachments: orphan cleanup has its own tests
    # (tests/test_attachment_orphans.py) and reaches no catalog here.
    monkeypatch.setattr(pipeline.state, "attachment_ids_for", lambda doc_id: [])

    record = _record(status=ChangeStatus.DELETED, document_id="d-1", entity_type="node")
    assert pipeline._handle(record, build_doc=lambda r: None) == "deleted"
    # Facet rows need no explicit delete: ON DELETE CASCADE handles them.
    assert calls == {"qdrant": "d-1", "state": ["d-1"]}
