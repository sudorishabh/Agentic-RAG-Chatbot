"""Page attribution must describe the text a child actually carries.

A child's text is `overlap carry + own content`, but `page_range` is derived from
the child's own blocks alone. When the carry comes from an earlier page, nothing
recorded that — the leading text was silently attributed to this chunk's page.

`page_number` and `page_range` keep describing the OWN content, so a citation
still resolves to where the substance is (`citations.py` turns `page_number` into
`Citation.page` and the `#page=N` fragment). `overlap_page_range` is the addition
that discloses where the carried opening came from.
"""

from __future__ import annotations

from app.ingestion.chunking import DocumentMeta, chunk_pages
from app.ingestion.chunking.config import ChunkingConfig

META = DocumentMeta(document_id="d", source_type="pdf", title="Panaji Case Study")

# Small windows so overlap is forced without needing huge fixtures.
CONFIG = ChunkingConfig(
    child_target_tokens=60, child_max_tokens=80, child_min_tokens=20,
    child_overlap_tokens=20, parent_target_tokens=100_000, parent_max_tokens=100_000,
)

# Capitalised sentences, so `overlap_carry` has boundaries it can advance to
# (`_SENTENCE_BOUNDARY` needs an upper-case follow).
def _prose(marker: str, n: int = 12) -> str:
    return " ".join(
        f"{marker.capitalize()} sentence {i} about coastal infrastructure." for i in range(n)
    )


def _children(chunks):
    return [c for c in chunks if not c.is_parent]


def test_same_page_overlap_keeps_the_page():
    """Overlap within one page must not disturb attribution."""
    children = _children(chunk_pages([(2, _prose("alpha", 30))], META, config=CONFIG))
    assert len(children) > 1, "fixture must produce overlapping children"
    assert all(c.page_number == 2 for c in children)
    assert all(c.page_range == (2, 2) for c in children)
    # The carry also came from page 2, so it is not a cross-page carry.
    assert all(
        c.overlap_page_range in (None, (2, 2)) for c in children
    ), [c.overlap_page_range for c in children]


def test_cross_page_overlap_records_the_carry_source():
    """The reported case: own content on page 3, carried opening from page 2."""
    children = _children(
        chunk_pages([(2, _prose("alpha", 14)), (3, _prose("bravo", 14))], META, config=CONFIG)
    )
    crossing = [
        c for c in children
        if c.overlap_page_range and c.page_range
        and c.overlap_page_range[0] < c.page_range[0]
    ]
    assert crossing, [(c.page_range, c.overlap_page_range) for c in children]

    child = crossing[0]
    # Own content still drives the citation, so the page link stays truthful.
    assert child.page_range == (3, 3)
    assert child.page_number == 3
    # ...and the carry's origin is now recorded rather than implied.
    assert child.overlap_page_range == (2, 2)
    # The text really does open with page-2 content and continue into page 3.
    assert "Alpha" in child.text and "Bravo" in child.text
    assert child.text.index("Alpha") < child.text.index("Bravo")


def test_no_overlap_leaves_page_metadata_untouched():
    """A single child has no carry, so nothing is recorded."""
    children = _children(chunk_pages([(5, _prose("alpha", 6))], META, config=CONFIG))
    assert len(children) == 1
    assert children[0].page_number == 5
    assert children[0].page_range == (5, 5)
    assert children[0].overlap_page_range is None


def test_first_child_never_has_an_overlap_range():
    children = _children(chunk_pages([(2, _prose("alpha", 30))], META, config=CONFIG))
    assert children[0].overlap_page_range is None


def test_multi_page_own_content_keeps_its_full_range():
    """Own content spanning pages 4-6 must not collapse to the first page."""
    pages = [(4, _prose("alpha", 3)), (5, _prose("bravo", 3)), (6, _prose("charlie", 3))]
    config = ChunkingConfig(
        child_target_tokens=400, child_max_tokens=512, child_min_tokens=20,
        child_overlap_tokens=20, parent_target_tokens=100_000, parent_max_tokens=100_000,
    )
    children = _children(chunk_pages(pages, META, config=config))
    assert len(children) == 1, "fixture must pack all three pages into one child"
    assert children[0].page_range == (4, 6)
    assert children[0].page_number == 4


def test_overlap_page_range_reaches_the_payload():
    children = _children(
        chunk_pages([(2, _prose("alpha", 14)), (3, _prose("bravo", 14))], META, config=CONFIG)
    )
    crossing = [c for c in children if c.overlap_page_range]
    assert crossing
    payload = crossing[0].to_payload()
    assert payload["overlap_page_range"] == list(crossing[0].overlap_page_range)
    # The citation fields keep their existing meaning.
    assert payload["page_number"] == crossing[0].page_range[0]


def test_payload_omits_overlap_range_when_there_is_none():
    child = _children(chunk_pages([(5, _prose("alpha", 6))], META, config=CONFIG))[0]
    assert "overlap_page_range" not in child.to_payload()
