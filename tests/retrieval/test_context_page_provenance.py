"""Regression tests: a citation must not claim a narrower page than its text.

``_admit`` substitutes the *parent* chunk's text into the block — that is the
point of parent expansion — but the block kept the *child's* payload, so a block
holding pages 6-9 was cited as "p.7" and the prompt header said the same. The
model then attributed anything in those four pages to the one page the child
happened to start on.

The invariant enforced here: the page provenance on a block describes the text
that block actually carries. A single page is still cited as a single page, a
multi-page parent is cited as a range, and where the pages are unknown nothing
is claimed at all — no page is ever invented.
"""

from __future__ import annotations

import pytest

from app.generation.prompts import _source_hint
from app.retrieval import context_builder
from app.retrieval.citations import build_citations
from app.retrieval.context_builder import build_context
from app.retrieval.hybrid_search import Candidate

CHILD_TEXT = "The child chunk body, which starts partway down its first page."
PARENT_TEXT = (
    "Section heading. Opening paragraph on the earlier page. "
    "The child chunk body, which starts partway down its first page. "
    "A sibling paragraph that runs on to the pages after it."
)


def _child(cid="c1", *, parent=None, page=None, page_range=None, source="pdf_attachment"):
    payload = {
        "chunk_id": cid,
        "document_id": "doc1",
        "source_type": source,
        "chunk_text": CHILD_TEXT,
        "title": "Annual Report",
        "file_url": "https://example.org/report.pdf",
    }
    if parent:
        payload["parent_chunk_id"] = parent
    if page is not None:
        payload["page_number"] = page
    if page_range is not None:
        payload["page_range"] = list(page_range)
    return Candidate(id=cid, score=0.9, payload=payload, semantic_score=0.9)


def _parents(monkeypatch, store):
    monkeypatch.setattr(
        context_builder, "_fetch_parents",
        lambda ids: {p: store[p] for p in dict.fromkeys(ids) if p in store},
    )


def _parent(text=PARENT_TEXT, page_range=None):
    payload = {"chunk_text": text, "is_parent": True}
    if page_range is not None:
        payload["page_range"] = list(page_range)
    return payload


def _one_block(monkeypatch, cand, parent_store):
    _parents(monkeypatch, parent_store)
    blocks = build_context([cand], limit=6, token_budget=9000)
    assert len(blocks) == 1
    return blocks[0]


# --------------------------------------------------------------------------- #
# Child and parent on the same page: nothing changes.
# --------------------------------------------------------------------------- #

def test_single_page_parent_cites_that_page(monkeypatch):
    block = _one_block(
        monkeypatch,
        _child(parent="p1", page=7, page_range=(7, 7)),
        {"p1": _parent(page_range=(7, 7))},
    )
    assert block.text == PARENT_TEXT
    assert block.payload["page_number"] == 7

    citation = build_citations([block])[0]
    assert (citation.page, citation.page_end) == (7, 7)
    assert citation.url == "https://example.org/report.pdf#page=7"


def test_orphan_keeps_its_own_page(monkeypatch):
    """No parent to expand into: the child's own page is exactly right."""
    block = _one_block(monkeypatch, _child(page=7, page_range=(7, 7)), {})
    assert block.text == CHILD_TEXT
    citation = build_citations([block])[0]
    assert (citation.page, citation.page_end) == (7, 7)


# --------------------------------------------------------------------------- #
# The defect: a parent spanning several pages, cited as one.
# --------------------------------------------------------------------------- #

def test_multi_page_parent_cites_the_full_range(monkeypatch):
    block = _one_block(
        monkeypatch,
        _child(parent="p1", page=7, page_range=(7, 7)),
        {"p1": _parent(page_range=(6, 9))},
    )
    assert block.text == PARENT_TEXT
    citation = build_citations([block])[0]
    assert (citation.page, citation.page_end) == (6, 9)


def test_citation_never_narrower_than_the_evidence(monkeypatch):
    """The general property, stated directly: the cited span must contain the
    whole of the text the block carries."""
    parent_range = (6, 9)
    block = _one_block(
        monkeypatch,
        _child(parent="p1", page=7, page_range=(7, 7)),
        {"p1": _parent(page_range=parent_range)},
    )
    citation = build_citations([block])[0]
    assert citation.page <= parent_range[0]
    assert citation.page_end >= parent_range[1]


def test_child_page_outside_the_parent_range_is_not_used(monkeypatch):
    """A child starting on page 9 of a parent that runs 6-9 must not shrink the
    citation to page 9."""
    block = _one_block(
        monkeypatch,
        _child(parent="p1", page=9, page_range=(9, 9)),
        {"p1": _parent(page_range=(6, 9))},
    )
    citation = build_citations([block])[0]
    assert (citation.page, citation.page_end) == (6, 9)
    assert citation.url == "https://example.org/report.pdf#page=6"


def test_falling_back_to_child_text_keeps_the_child_page(monkeypatch):
    """A dangling parent id means the child's own text is shown, so the child's
    own page is the honest provenance."""
    block = _one_block(
        monkeypatch, _child(parent="missing", page=7, page_range=(7, 7)), {}
    )
    assert block.text == CHILD_TEXT
    citation = build_citations([block])[0]
    assert (citation.page, citation.page_end) == (7, 7)


# --------------------------------------------------------------------------- #
# Never invent a page.
# --------------------------------------------------------------------------- #

def test_parent_without_pages_claims_no_page(monkeypatch):
    """An unpaginated parent cannot be located, so the child's page is dropped
    rather than stretched over text it does not describe."""
    block = _one_block(
        monkeypatch,
        _child(parent="p1", page=7, page_range=(7, 7)),
        {"p1": _parent(page_range=None)},
    )
    assert block.text == PARENT_TEXT
    citation = build_citations([block])[0]
    assert citation.page is None and citation.page_end is None
    assert citation.url == "https://example.org/report.pdf"  # no #page anchor


def test_website_block_has_no_pages(monkeypatch):
    block = _one_block(
        monkeypatch,
        _child(parent="p1", source="website"),
        {"p1": _parent(page_range=None)},
    )
    citation = build_citations([block])[0]
    assert citation.page is None and citation.page_end is None


# --------------------------------------------------------------------------- #
# What the model is told has to match what it is shown.
# --------------------------------------------------------------------------- #

def test_prompt_header_shows_the_range(monkeypatch):
    block = _one_block(
        monkeypatch,
        _child(parent="p1", page=7, page_range=(7, 7)),
        {"p1": _parent(page_range=(6, 9))},
    )
    hint = _source_hint(block.payload)
    assert "pp.6-9" in hint
    assert "p.7" not in hint


def test_prompt_header_shows_a_single_page_as_one_page(monkeypatch):
    block = _one_block(
        monkeypatch,
        _child(parent="p1", page=7, page_range=(7, 7)),
        {"p1": _parent(page_range=(7, 7))},
    )
    assert "p.7" in _source_hint(block.payload)


# --------------------------------------------------------------------------- #
# Identity is untouched: citations still resolve to the chunk that was hit.
# --------------------------------------------------------------------------- #

def test_expansion_keeps_the_hit_chunk_identity(monkeypatch):
    block = _one_block(
        monkeypatch,
        _child(cid="c-hit", parent="p1", page=7, page_range=(7, 7)),
        {"p1": _parent(page_range=(6, 9))},
    )
    assert block.payload["chunk_id"] == "c-hit"
    assert block.payload["document_id"] == "doc1"
    assert build_citations([block])[0].document_id == "doc1"


@pytest.mark.parametrize("page_range", [(6, 9), (7, 7)])
def test_block_page_fields_describe_the_block_text(monkeypatch, page_range):
    """The payload the rest of the app reads (search API, prompt, citations)
    agrees with the text in the block."""
    block = _one_block(
        monkeypatch,
        _child(parent="p1", page=7, page_range=(7, 7)),
        {"p1": _parent(page_range=page_range)},
    )
    assert block.payload["page_range"] == list(page_range)
    assert block.payload["page_number"] == page_range[0]
