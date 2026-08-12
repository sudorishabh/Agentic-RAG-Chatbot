"""What the stored payload carries, and why.

Every key here costs storage on every point, so each one is pinned to the
consumer that reads it. The one field removed — `table_markdown` — was a
verbatim duplicate of table rows already present in `chunk_text`, with no reader
anywhere in the repository.

Measured over the sample corpus (94 points, 323,205 payload bytes) at the time
of the decision:

    chunk_text ......... 75.0%   required
    table_markdown ..... 10.1%   removed (duplicate, no reader)
    content_hash ........ 2.4%   retained for upcoming incremental re-index
    token_count ......... 0.5%   retained (ops/debug)
    page_range .......... 0.4%   retained (P1-6 own-content semantics)
    overlap_page_range .. 0.4%   retained (P1-6 overlap provenance)

Those figures are evidence, not a runtime rule; nothing here asserts them.
"""

from __future__ import annotations

import pytest

from app.ingestion.chunking import DocumentMeta, chunk_pages
from app.ingestion.chunking.config import ChunkingConfig

META = DocumentMeta(
    document_id="doc-1", source_type="pdf_attachment", title="Panaji Case Study",
    tenant_id="default", acl=["public"],
)

CONFIG = ChunkingConfig(
    child_target_tokens=120, child_max_tokens=200, child_min_tokens=20,
    child_overlap_tokens=20, parent_target_tokens=100_000, parent_max_tokens=100_000,
)

BODY = "The study assessed vulnerability of coastal infrastructure in Panaji. "
TABLE = "| Zone | Risk |\n| --- | --- |\n| Altinho | High |\n| Miramar | Medium |"


def _chunks(pages=None):
    pages = pages or [(3, f"3.1 Zone Vulnerabilities\n\n{BODY * 6}\n\n{TABLE}\n\n{BODY * 6}")]
    return chunk_pages(pages, META, config=CONFIG)


def _children(pages=None):
    return [c for c in _chunks(pages) if not c.is_parent]


# --- the removed field ------------------------------------------------------ #

def test_table_markdown_is_not_stored_in_the_payload():
    chunks = _chunks()
    assert any(c.has_table for c in chunks), "fixture must produce a table chunk"
    assert all("table_markdown" not in c.to_payload() for c in chunks)


def test_table_rows_are_still_in_chunk_text():
    """Removing the field loses nothing: every row is already in the text."""
    chunks = [c for c in _chunks() if c.has_table]
    assert chunks
    for chunk in chunks:
        for row in [ln for ln in chunk.table_markdown.splitlines() if ln.strip()]:
            assert row in chunk.to_payload()["chunk_text"]


def test_has_table_survives_and_still_flags_the_chunk():
    """`prompts.py` and the rerank table boost read this, so it must remain."""
    payloads = [c.to_payload() for c in _chunks()]
    assert any(p.get("has_table") for p in payloads)
    # Chunks without a table omit it rather than storing False.
    assert all("has_table" not in p or p["has_table"] is True for p in payloads)


def test_the_chunk_object_still_carries_the_markdown_for_tooling():
    assert any(c.table_markdown for c in _chunks())


# --- fields that must keep being stored ------------------------------------- #

@pytest.mark.parametrize(
    "field",
    [
        "chunk_id", "document_id", "is_parent", "source_type", "title",
        "chunk_text", "is_current", "tenant_id", "acl", "doc_version",
    ],
)
def test_required_field_is_present_on_every_chunk(field):
    for chunk in _chunks():
        assert field in chunk.to_payload(), f"{field} missing"


def test_is_current_is_stored_even_though_it_is_always_true():
    """`hybrid_search.build_filter` matches on it; dropping it would make every
    search return nothing."""
    assert all(c.to_payload()["is_current"] is True for c in _chunks())


def test_child_only_fields_are_stored_on_children():
    child = _children()[0]
    payload = child.to_payload()
    assert payload["chunk_index"] == child.chunk_index      # enrich_backfill ordering
    assert payload["page_number"] == child.page_number      # citations + #page= link
    assert payload["chunk_text"] == child.text              # retrieval + context


def test_section_heading_and_page_number_reach_the_payload():
    """Both are read by citations.py and prompts.py."""
    child = next(c for c in _children() if c.section_heading)
    payload = child.to_payload()
    assert payload["section_heading"] == "3.1 Zone Vulnerabilities"
    assert payload["page_number"] == 3


def test_section_type_is_stored_when_set_so_the_reference_filter_works():
    refs = "\n".join(
        f"Author {i} AB and Other CD. 200{i}. A bibliography entry title here."
        for i in range(5)
    )
    child = next(c for c in _children([(9, refs)]) if c.section_type)
    assert child.to_payload()["section_type"] == "references"


def test_page_ranges_stay_distinguishable():
    """P1-6: own-content pages and carried-overlap pages are separate keys."""
    pages = [(2, BODY * 12), (3, BODY * 12)]
    carried = [c for c in _children(pages) if c.overlap_page_range]
    assert carried
    payload = carried[0].to_payload()
    assert payload["page_range"] == list(carried[0].page_range)
    assert payload["overlap_page_range"] == list(carried[0].overlap_page_range)
    assert payload["page_number"] == payload["page_range"][0]


def test_parent_payload_keeps_what_context_expansion_needs():
    parents = [c for c in _chunks() if c.is_parent]
    assert parents
    payload = parents[0].to_payload()
    assert payload["is_parent"] is True
    assert payload["chunk_text"].strip()          # substituted by _admit
    assert "parent_chunk_id" not in payload       # parents have no parent
    assert "chunk_index" not in payload


def test_children_point_at_their_parent():
    parents = [c for c in _chunks() if c.is_parent]
    children = _children()
    assert parents
    assert {c.to_payload()["parent_chunk_id"] for c in children} == {parents[0].chunk_id}


def test_empty_values_are_omitted_rather_than_stored():
    """build_payload drops None/""/[] so absent metadata costs nothing."""
    meta = DocumentMeta(document_id="d", source_type="pdf", title=None)
    payload = chunk_pages([(1, BODY * 6)], meta, config=CONFIG)[0].to_payload()
    assert "title" not in payload
    assert "section_type" not in payload
    assert all(v not in (None, "", []) for v in payload.values())
