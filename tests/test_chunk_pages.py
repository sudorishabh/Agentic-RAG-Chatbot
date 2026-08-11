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
from app.ingestion.chunking.packer import get_encoder, window_texts
from app.ingestion.chunking.segmenter import Block, join_blocks

ENC = get_encoder("cl100k_base")

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


# --- interaction with the P1-5 split ---------------------------------------- #
#
# `window_texts` may emit several children per window. Each must describe the
# text it actually holds, not the whole window's span.


def test_a_split_window_gives_each_child_its_own_pages():
    """One window spanning pages 4-7 must not label every piece (4, 7)."""
    blocks = [Block("text", _prose(f"page{page}", 12), 0, page) for page in (4, 5, 6, 7)]
    out = window_texts([blocks], overlap=0, max_tokens=200, enc=ENC)

    assert len(out) > 1, "the fixture must force a split"
    for child in out:
        pages = {b.page for b in child.blocks}
        # The text is exactly the join of the blocks recorded beside it.
        assert child.text == join_blocks(child.blocks)
        # ...so every page marker present belongs to a block this child owns.
        for page in (4, 5, 6, 7):
            assert (f"Page{page}" in child.text) == (page in pages)


def test_a_split_window_never_spans_more_pages_than_its_text():
    blocks = [Block("text", _prose(f"page{page}", 12), 0, page) for page in (4, 5, 6, 7)]
    out = window_texts([blocks], overlap=0, max_tokens=200, enc=ENC)
    spans = [(min(b.page for b in c.blocks), max(b.page for b in c.blocks)) for c in out]
    assert spans != [(4, 7)] * len(out), "pieces must not all inherit the window span"
    assert spans == sorted(spans), spans


def test_every_child_text_is_accounted_for_by_its_page_metadata():
    """The end-to-end invariant: a child's text may only contain content from
    pages named by `page_range` or `overlap_page_range` — nothing unattributed."""
    pages = [(page, _prose(f"page{page}", 10)) for page in (2, 3, 4, 5)]
    children = _children(chunk_pages(pages, META, config=CONFIG))
    assert len(children) > 4, "fixture must produce several overlapping children"

    for child in children:
        owned = set(range(child.page_range[0], child.page_range[1] + 1))
        if child.overlap_page_range:
            lo, hi = child.overlap_page_range
            owned |= set(range(lo, hi + 1))
        present = {page for page in (2, 3, 4, 5) if f"Page{page}" in child.text}
        assert present <= owned, (
            f"child {child.chunk_index} holds text from {sorted(present - owned)} "
            f"but is attributed to page_range={child.page_range} "
            f"overlap_page_range={child.overlap_page_range}"
        )
