"""Tests that single-child sections don't emit a redundant near-duplicate parent."""

from __future__ import annotations

from app.ingestion.chunker import DocumentMeta, chunk_pages

META = DocumentMeta(document_id="d", source_type="pdf", title="T")


def test_single_child_section_has_no_redundant_parent():
    text = "1.3 Macro-trends\n\n" + "The sector faces development and decarbonisation pressure. " * 6
    chunks = chunk_pages([(1, text)], META)
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    assert len(children) == 1
    assert len(parents) == 0
    assert children[0].parent_chunk_id is None


def test_large_section_keeps_parent_with_children():
    body = "Maritime decarbonisation requires alternative fuels and new infrastructure. " * 120
    chunks = chunk_pages([(1, f"4 Transition Pathway\n\n{body}")], META)
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    assert len(parents) >= 1
    assert len(children) >= 2
    assert all(c.parent_chunk_id for c in children)
