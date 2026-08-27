"""Page boundaries are block boundaries, and paragraphs are not stitched across them.

`chunk_pages` blockifies one page at a time, so a paragraph broken by a page
break becomes two blocks joined by a blank line — indistinguishable from a real
paragraph break. Stitching them is *not* implemented, deliberately.

Why not
-------
Measured over the sample corpus (45 page boundaries) at the time of this decision:

    genuine prose continuations ....  ~2
    hyphenated word splits .........   0
    already-complete paragraphs ....   8
    heading on the next page .......   4
    table on one side ..............  18
    page furniture / captions ......  the remainder

The signal a stitcher would key on — "the previous page did not end in
punctuation" — is dominated by page furniture and figure captions, which sit
exactly at the boundary where it looks:

    '…Figure 1: Location map of Panaji, Goa'  ->  '3'
    '…the authority'                          ->  'Figure 6: Snapshots from DBMS…'

A rule firing on ~2 real cases while risking merging captions and page numbers
into prose is not worth it, and with zero hyphenation cases in the corpus a
dehyphenation rule would have nothing to validate against. Those figures are
evidence for the decision, not a runtime rule; nothing here asserts them.

What these tests pin
--------------------
That the boundary is handled *safely*: nothing is lost, page attribution spans
both pages, and headings, tables, lists, code and reference entries are never
absorbed into neighbouring prose.
"""

from __future__ import annotations

from app.ingestion.chunking import DocumentMeta, chunk_pages
from app.ingestion.chunking.config import ChunkingConfig
from app.ingestion.chunking.segmenter import blocks_from_text

META = DocumentMeta(document_id="d", source_type="pdf", title="Panaji Case Study")

CONFIG = ChunkingConfig(
    child_target_tokens=400, child_max_tokens=512, child_min_tokens=20,
    child_overlap_tokens=20, parent_target_tokens=100_000, parent_max_tokens=100_000,
)

BODY = "The study assessed vulnerability of coastal infrastructure in Panaji."


def _children(pages):
    return [c for c in chunk_pages(pages, META, config=CONFIG) if not c.is_parent]


def _blocks(pages):
    return [b for page, text in pages for b in blocks_from_text(text, page)]


# --- P1/P2: a continuation and a completed paragraph are indistinguishable --- #

def test_sentence_continuation_survives_but_is_not_stitched():
    """P1: both halves are kept and stay in order — they are simply not joined."""
    pages = [
        (1, "The city experienced rapid population growth and"),
        (2, "this placed increasing pressure on the water supply."),
    ]
    children = _children(pages)
    assert len(children) == 1
    text = children[0].text
    assert "rapid population growth and" in text
    assert "this placed increasing pressure" in text
    assert text.index("growth and") < text.index("this placed")
    # The documented limitation: a blank line, not a space, separates them.
    assert "growth and\n\nthis placed" in text


def test_completed_paragraph_reads_identically():
    """P2: the pipeline cannot currently tell P1 and P2 apart — both become two
    blocks joined by a blank line. This is the limitation, pinned."""
    pages = [
        (1, "The city experienced rapid population growth."),
        (2, "Water supply was subsequently expanded."),
    ]
    text = _children(pages)[0].text
    assert "growth.\n\nWater supply was subsequently expanded." in text


def test_page_attribution_spans_both_pages():
    """P1-6 still holds when one chunk holds content from two pages."""
    pages = [
        (1, "The city experienced rapid population growth and"),
        (2, "this placed increasing pressure on the water supply."),
    ]
    child = _children(pages)[0]
    assert child.page_range == (1, 2)
    assert child.page_number == 1


# --- P3: a heading on the next page stays a heading ------------------------- #

def test_heading_on_the_next_page_is_not_absorbed():
    pages = [(1, f"{BODY * 4} The previous paragraph ends here."),
             (2, f"Scope of the Study\n\n{BODY * 4}")]
    children = _children(pages)
    headings = {c.section_heading for c in children}
    assert "Scope of the Study" in headings
    # The heading text is not left sitting inside the previous paragraph.
    first = next(c for c in children if c.section_heading is None)
    assert "Scope of the Study" not in first.text


def test_a_heading_too_small_to_own_a_section_is_still_kept_as_text():
    """When the trailing section is under `child_min_tokens` it folds into the
    previous one and its heading becomes body text. Attribution is lost, the
    text is not — P0-1 holds either way."""
    pages = [(1, f"{BODY} The previous paragraph ends here."), (2, f"Scope of the Study\n\n{BODY}")]
    children = _children(pages)
    assert {c.section_heading for c in children} == {None}
    assert any("Scope of the Study" in c.text for c in children)


# --- P4/P5/P6: structured blocks are never merged into prose ---------------- #

def test_table_on_the_next_page_stays_a_table_block():
    pages = [(1, "Prose paragraph ending the previous page."),
             (2, "| Zone | Risk |\n| --- | --- |\n| Altinho | High |")]
    kinds = [b.kind for b in _blocks(pages)]
    assert kinds == ["text", "table"]
    child = _children(pages)[0]
    assert child.has_table
    assert "| Zone | Risk |" in child.table_markdown


def test_list_items_on_the_next_page_are_not_merged_into_the_paragraph():
    pages = [(1, "Prose paragraph ending the previous page."),
             (2, "i) Sewerage Zones\nii) Pumping Stations\niii) Discharge Points")]
    blocks = _blocks(pages)
    # List markers are not headings (P0-2) and stay separate from the prose block.
    assert [b.kind for b in blocks] == ["text", "text"]
    assert blocks[0].page == 1 and blocks[1].page == 2
    assert "i) Sewerage Zones" in blocks[1].text


def test_code_block_on_the_next_page_stays_code():
    pages = [(1, "Prose paragraph ending the previous page."),
             (2, "```\nfor zone in zones:\n    assess(zone)\n```")]
    blocks = _blocks(pages)
    assert [b.kind for b in blocks] == ["text", "code"]


# --- P7/P8: hyphenation is not repaired ------------------------------------- #

def test_a_word_split_by_the_page_break_is_left_as_extracted():
    """P7: no dehyphenation is attempted. The corpus contains no instance of
    this, so a repair rule would have nothing to validate against."""
    pages = [(1, "Sea level rise threatens the coastal environ-"), (2, "ment of the city.")]
    text = _children(pages)[0].text
    assert "environ-" in text
    assert "environment" not in text


def test_a_legitimate_hyphenated_compound_is_untouched():
    """P8: the corollary — because nothing is rewritten, a real compound is safe."""
    pages = [(1, "The scheme is well-established across the district."),
             (2, "Funding continues under the current plan.")]
    text = _children(pages)[0].text
    assert "well-established" in text


# --- P1-9: reference entries are not joined across a page break ------------- #

def test_reference_entries_are_not_joined_across_a_page_break():
    pages = [
        (1, "Brenkert AL and Malone EL. 2005. Modelling Vulnerability and Resilience."),
        (2, "Byravan Sujatha et al. 2010. Impact on Major Infrastructure and Land."),
    ]
    text = _children(pages)[0].text
    assert "Resilience.\n\nByravan Sujatha" in text


# --- P0-1: nothing is lost at a page boundary ------------------------------- #

def test_no_block_is_lost_at_a_page_boundary():
    pages = [
        (1, "The city experienced rapid population growth and"),
        (2, "this placed increasing pressure on the water supply.\n\nScope of the Study"),
        (3, f"{BODY}\n\n| Zone | Risk |\n| --- | --- |\n| Altinho | High |"),
    ]
    chunks = chunk_pages(pages, META, config=CONFIG)
    surface = " ".join(f"{c.section_heading or ''} {c.text}" for c in chunks)
    flat = " ".join(surface.split())
    for block in _blocks(pages):
        assert " ".join(block.text.split()) in flat
