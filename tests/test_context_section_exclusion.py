"""Regression tests: excluded sections must not re-enter through the parent.

``build_filter`` keeps toc / references / glossary chunks out of every search,
but that decision was made about the *child* that matched. ``_admit`` then
substituted the parent's text, and nothing re-checked the parent — so a body
child sitting inside a bibliography window pulled the whole bibliography into
the prompt, past a filter that had already excluded exactly that content.

The invariant enforced here is about the text that reaches the model, not the
candidate that carried it:

    if the text admitted into a block belongs to an excluded section,
    it is not admitted at all.

A child inside an allowed parent is the one case that still expands: the
classifier reads content rather than headings (see
``app.ingestion.chunking.classifier``), so a citation-dense run inside a
substantive section is a fragment of that section, not a bibliography.
"""

from __future__ import annotations

import pytest

from app.retrieval import context_builder
from app.retrieval.context_builder import build_context
from app.retrieval.hybrid_search import _NON_SEARCHABLE_SECTIONS, Candidate

BODY_CHILD = "Body child: the measured emissions fell by a fifth over the decade."
BODY_PARENT = (
    "Findings. Body child: the measured emissions fell by a fifth over the "
    "decade. The reduction held across every sector surveyed."
)
REFS_CHILD = "Sharma A. 2019. Air quality in Delhi. Retrieved from https://x.example"
REFS_PARENT = (
    "References. Sharma A. 2019. Air quality in Delhi. "
    "Brenkert AL and Malone EL. 2005. Modelling vulnerability. "
    "Kumar S. 2021. Urban transport. Retrieved from https://y.example"
)


def _cand(cid, text, *, parent=None, section_type=None):
    payload = {
        "chunk_id": cid,
        "document_id": "doc1",
        "source_type": "pdf_attachment",
        "chunk_text": text,
    }
    if parent:
        payload["parent_chunk_id"] = parent
    if section_type:
        payload["section_type"] = section_type
    return Candidate(id=cid, score=0.9, payload=payload, semantic_score=0.9)


def _parents(monkeypatch, store):
    monkeypatch.setattr(
        context_builder, "_fetch_parents",
        lambda ids: {p: store[p] for p in dict.fromkeys(ids) if p in store},
    )


def _parent(text, section_type=None):
    payload = {"chunk_text": text, "is_parent": True}
    if section_type:
        payload["section_type"] = section_type
    return payload


def _context(monkeypatch, cands, store):
    _parents(monkeypatch, store)
    return build_context(cands, limit=6, token_budget=9000)


# --------------------------------------------------------------------------- #
# The leak: an allowed child whose parent is a bibliography.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("section_type", _NON_SEARCHABLE_SECTIONS)
def test_allowed_child_with_excluded_parent_keeps_the_child_text(
    monkeypatch, section_type
):
    blocks = _context(
        monkeypatch,
        [_cand("c1", BODY_CHILD, parent="p1")],
        {"p1": _parent(REFS_PARENT, section_type)},
    )
    assert len(blocks) == 1
    assert blocks[0].text == BODY_CHILD
    assert REFS_PARENT not in blocks[0].text
    assert "Brenkert" not in blocks[0].text  # nothing from the excluded window


@pytest.mark.parametrize("section_type", _NON_SEARCHABLE_SECTIONS)
def test_excluded_text_never_reaches_any_block(monkeypatch, section_type):
    """Stated over the whole context rather than one block: the excluded
    window's content is absent from everything handed to the model."""
    blocks = _context(
        monkeypatch,
        [
            _cand("c1", BODY_CHILD, parent="p1"),
            _cand("c2", "Second body child, on a different section.", parent="p2"),
        ],
        {
            "p1": _parent(REFS_PARENT, section_type),
            "p2": _parent("Discussion. Second body child, on a different section."),
        },
    )
    joined = "\n".join(b.text for b in blocks)
    assert "Brenkert" not in joined and "Retrieved from" not in joined
    assert BODY_CHILD in joined


# --------------------------------------------------------------------------- #
# An excluded child is dropped when nothing substantive backs it.
# --------------------------------------------------------------------------- #

def test_excluded_child_with_excluded_parent_is_dropped(monkeypatch):
    blocks = _context(
        monkeypatch,
        [_cand("c1", REFS_CHILD, parent="p1", section_type="references")],
        {"p1": _parent(REFS_PARENT, "references")},
    )
    assert blocks == []


def test_excluded_orphan_is_dropped(monkeypatch):
    """No parent to fall back on, and its own text is excluded."""
    blocks = _context(
        monkeypatch, [_cand("c1", REFS_CHILD, section_type="references")], {}
    )
    assert blocks == []


def test_excluded_child_with_missing_parent_is_dropped(monkeypatch):
    """A dangling parent id must not become a way in."""
    blocks = _context(
        monkeypatch,
        [_cand("c1", REFS_CHILD, parent="gone", section_type="glossary")],
        {},
    )
    assert blocks == []


# --------------------------------------------------------------------------- #
# An excluded child inside a substantive parent still expands.
# --------------------------------------------------------------------------- #

def test_excluded_child_with_allowed_parent_expands(monkeypatch):
    """The classifier reads content, not headings: a citation-dense run inside a
    findings section is a fragment of that section, and the section is what the
    block carries."""
    blocks = _context(
        monkeypatch,
        [_cand("c1", REFS_CHILD, parent="p1", section_type="references")],
        {"p1": _parent(BODY_PARENT)},
    )
    assert len(blocks) == 1
    assert blocks[0].text == BODY_PARENT


# --------------------------------------------------------------------------- #
# Ordinary content is untouched.
# --------------------------------------------------------------------------- #

def test_normal_body_text_still_expands_to_its_parent(monkeypatch):
    blocks = _context(
        monkeypatch,
        [_cand("c1", BODY_CHILD, parent="p1")],
        {"p1": _parent(BODY_PARENT)},
    )
    assert [b.text for b in blocks] == [BODY_PARENT]


def test_normal_orphan_is_kept(monkeypatch):
    blocks = _context(monkeypatch, [_cand("c1", BODY_CHILD)], {})
    assert [b.text for b in blocks] == [BODY_CHILD]


def test_mixed_set_keeps_only_the_admissible_text(monkeypatch):
    blocks = _context(
        monkeypatch,
        [
            _cand("c1", BODY_CHILD, parent="p-body"),
            _cand("c2", REFS_CHILD, parent="p-refs", section_type="references"),
            _cand("c3", "A glossary line - meaning.", section_type="glossary"),
        ],
        {
            "p-body": _parent(BODY_PARENT),
            "p-refs": _parent(REFS_PARENT, "references"),
        },
    )
    assert [b.text for b in blocks] == [BODY_PARENT]
    assert [b.n for b in blocks] == [1]


# --------------------------------------------------------------------------- #
# Falling back to the child keeps the child's provenance (Priority 3 contract).
# --------------------------------------------------------------------------- #

def test_child_fallback_keeps_the_child_page(monkeypatch):
    cand = _cand("c1", BODY_CHILD, parent="p1")
    cand.payload["page_number"] = 7
    cand.payload["page_range"] = [7, 7]
    blocks = _context(
        monkeypatch, [cand],
        {"p1": _parent(REFS_PARENT, "references") | {"page_range": [4, 9]}},
    )
    assert blocks[0].text == BODY_CHILD
    assert blocks[0].payload["page_range"] == [7, 7]
