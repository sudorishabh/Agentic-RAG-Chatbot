"""Unit tests for the attached-PDF supplementation pull.

Covers the trigger conditions (detailed format only, website blocks present,
unrepresented attachments), the single bounded extra pull with union rerank
and context rebuild, and fail-open on errors. Catalog, Qdrant, rerank, and
context build are all stubbed; no network.
"""

from __future__ import annotations

import app.rag as rag
from app.retrieval import catalog, scoped_retrieval
from app.retrieval.context_builder import ContextBlock
from app.retrieval.hybrid_search import Candidate


def _block(n=1, doc_id="w1", source_type="website", linked_pdf_id=None):
    payload = {"document_id": doc_id, "source_type": source_type}
    if linked_pdf_id:
        payload["linked_pdf_id"] = linked_pdf_id
    return ContextBlock(n=n, text=f"text {doc_id}", payload=payload)


def _cand(id="c1"):
    return Candidate(id=id, score=0.9, payload={"document_id": id})


def _attachment(file_uuid="f1"):
    return {"file_uuid": file_uuid, "origin": "attachment",
            "url": f"https://t/{file_uuid}.pdf", "filename": f"{file_uuid}.pdf"}


def _supplement(blocks, ranked, **overrides):
    kw = dict(search_query="q", query_vector=[0.1], tenant_id="default",
              user_groups=["public"], n=5, segregate=False)
    kw.update(overrides)
    return rag._supplement_attachments(blocks, ranked, **kw)


# --------------------------------------------------------------------------- #
# Skip conditions — no extra pull unless every trigger holds.
# --------------------------------------------------------------------------- #

def test_no_website_blocks_skips_catalog(monkeypatch):
    def no_catalog(ids):
        raise AssertionError("catalog must not be queried")

    monkeypatch.setattr(catalog, "attachments_for", no_catalog)
    blocks = [_block(doc_id="p1", source_type="pdf")]
    assert _supplement(blocks, [_cand()]) is blocks


def test_no_attachments_skips_search(monkeypatch):
    monkeypatch.setattr(catalog, "attachments_for", lambda ids: {})

    def no_search(*a, **k):
        raise AssertionError("qdrant must not be queried")

    monkeypatch.setattr(scoped_retrieval, "search_within_documents", no_search)
    blocks = [_block()]
    assert _supplement(blocks, [_cand()]) is blocks


def test_represented_attachments_skip_search(monkeypatch):
    monkeypatch.setattr(
        catalog, "attachments_for", lambda ids: {"w1": [_attachment("f1")]}
    )

    def no_search(*a, **k):
        raise AssertionError("qdrant must not be queried")

    monkeypatch.setattr(scoped_retrieval, "search_within_documents", no_search)
    # Represented two ways: a block linking to the pdf, or the pdf's own block.
    linked = [_block(linked_pdf_id="f1")]
    assert _supplement(linked, [_cand()]) is linked
    own = [_block(), _block(n=2, doc_id="f1", source_type="pdf_attachment")]
    assert _supplement(own, [_cand()]) is own


# --------------------------------------------------------------------------- #
# The supplementation pull — one scoped search, union rerank, rebuild.
# --------------------------------------------------------------------------- #

def test_unrepresented_attachment_triggers_one_pull(monkeypatch):
    monkeypatch.setattr(
        catalog, "attachments_for",
        lambda ids: {"w1": [_attachment("f1"), _attachment("f1")]},  # duplicate uuid
    )
    searches: list = []

    def fake_search(vector, ids, *, limit, **kw):
        searches.append((list(ids), limit))
        return [_cand("extra1")]

    monkeypatch.setattr(scoped_retrieval, "search_within_documents", fake_search)
    reranked_input: list = []
    monkeypatch.setattr(
        rag, "rerank", lambda q, cands, **kw: reranked_input.extend(cands) or cands
    )
    rebuilt = [_block(), _block(n=2, doc_id="f1", source_type="pdf_attachment")]
    monkeypatch.setattr(rag, "build_context", lambda ranked, *, limit, segregate: rebuilt)

    out = _supplement([_block()], [_cand("c1")])

    assert out is rebuilt
    assert searches == [(["f1"], 10)]  # deduped uuids, one bounded pull
    assert [c.id for c in reranked_input] == ["c1", "extra1"]  # union, no dupes


def test_already_ranked_candidates_short_circuit(monkeypatch):
    monkeypatch.setattr(
        catalog, "attachments_for", lambda ids: {"w1": [_attachment("f1")]}
    )
    # The pull returns only chunks already in the ranked pool -> nothing new.
    monkeypatch.setattr(
        scoped_retrieval, "search_within_documents", lambda *a, **k: [_cand("c1")]
    )

    def no_rerank(*a, **k):
        raise AssertionError("rerank must not run when the pull adds nothing")

    monkeypatch.setattr(rag, "rerank", no_rerank)
    blocks = [_block()]
    assert _supplement(blocks, [_cand("c1")]) is blocks


def test_failure_keeps_original_blocks(monkeypatch):
    def boom(ids):
        raise RuntimeError("mysql down")

    monkeypatch.setattr(catalog, "attachments_for", boom)
    blocks = [_block()]
    assert _supplement(blocks, [_cand()]) is blocks


# --------------------------------------------------------------------------- #
# retrieve() gating — only the detailed format triggers the pull.
# --------------------------------------------------------------------------- #

def test_retrieve_supplements_only_detailed(monkeypatch):
    blocks = [_block()]
    monkeypatch.setattr(rag, "search", lambda *a, **k: [_cand()])
    monkeypatch.setattr(rag, "rerank", lambda q, cands, **kw: cands)
    monkeypatch.setattr(rag, "build_context", lambda ranked, *, limit, segregate: blocks)
    calls: list = []
    monkeypatch.setattr(
        rag, "_supplement_attachments",
        lambda b, r, **kw: calls.append(kw["n"]) or b,
    )

    rag.retrieve("q", query_vector=[0.1], answer_format="detailed")
    assert len(calls) == 1
    rag.retrieve("q", query_vector=[0.1], answer_format="default")
    rag.retrieve("q", query_vector=[0.1], answer_format="table")
    assert len(calls) == 1  # unchanged: only detailed triggered the pull
