"""Chunking must not drop extracted text.

A run of short lines — an extracted table column, a bare list — is classified as
consecutive headings. Folding those into the section heading left the section
with no body, which packed to zero chunks and lost every line.
"""

from __future__ import annotations

import re
from collections import Counter

import pytest

from app.ingestion.chunking import DocumentMeta, chunk_document, chunk_pages
from app.ingestion.chunking.config import config_for
from app.ingestion.chunking.packer import get_encoder
from app.ingestion.chunking.segmenter import blocks_from_text

META = DocumentMeta(document_id="d", source_type="pdf", title="Panaji Case Study")

# The real corpus shape: a vulnerability table extracted one cell per line.
ZONE_TABLE = [
    "Zone Vulnerabilities",
    "Ecologically Sensitive Areas",
    "Water Supply",
    "Transport",
    "Altinho",
    "SLR",
    "Flood prone",
]

# The minimal shape: every line is classified as a heading, no body text at all.
ALL_HEADINGS = ["Water Supply", "Transport", "Energy"]


def _surface(chunks) -> str:
    """Where a source line may legitimately survive: a chunk's text, or the
    heading a chunk is filed under (indexed as `section_heading`, and embedded
    via the breadcrumb). Overlap makes chunk text intentionally repetitive, so
    coverage is "present at least once", never an equality check.
    """
    return "\n".join(f"{c.section_heading or ''}\n{c.text}" for c in chunks)


def test_zone_table_is_not_dropped():
    chunks = chunk_document("\n".join(ZONE_TABLE) + "\n", META)
    assert chunks, "a table extracted as heading-like lines produced zero chunks"
    surface = _surface(chunks)
    missing = [line for line in ZONE_TABLE if line not in surface]
    assert not missing, f"source lines absent from every chunk: {missing}"


def test_all_heading_lines_with_no_body_still_chunk():
    chunks = chunk_document("\n".join(ALL_HEADINGS) + "\n", META)
    assert chunks, "a body-less run of headings produced zero chunks"
    surface = _surface(chunks)
    missing = [line for line in ALL_HEADINGS if line not in surface]
    assert not missing, f"source lines absent from every chunk: {missing}"


def test_demoted_heading_lines_reach_chunk_text_not_only_the_heading():
    """The lines must be retrievable, i.e. in the text a child embeds — not
    parked in a heading string that the breadcrumb truncates."""
    chunks = chunk_document("\n".join(ZONE_TABLE) + "\n", META)
    body = "\n".join(c.text for c in chunks if not c.is_parent)
    # The first line may legitimately title the section; the rest are content.
    for line in ZONE_TABLE[1:]:
        assert line in body, f"{line!r} never reached any child chunk's text"


def test_lone_heading_document_still_chunks():
    """A section with no body packs to zero windows. `merge_small_sections`
    folds it into a sibling when one exists — but a document that is *only* a
    heading line has no sibling, so chunk creation must not skip it."""
    for source in ("Water Supply", "EXECUTIVE SUMMARY", "4.1 Alternative Fuel Cost"):
        chunks = chunk_document(source + "\n", META)
        assert chunks, f"{source!r} produced zero chunks"
        assert source in _surface(chunks)


def test_lone_heading_child_stands_alone_without_a_parent():
    chunks = chunk_document("EXECUTIVE SUMMARY\n", META)
    assert [c.is_parent for c in chunks] == [False]
    assert chunks[0].parent_chunk_id is None


def test_heading_still_titles_its_section_when_a_body_follows():
    """The fix must not stop real headings from owning their section."""
    text = "4 Transition Pathway\n\n" + "Alternative fuels need port infrastructure. " * 8
    children = [c for c in chunk_document(text, META) if not c.is_parent]
    assert children
    assert children[0].section_heading == "4 Transition Pathway"
    assert "Transition Pathway" not in children[0].text


# --- general losslessness invariant ---------------------------------------- #

# Threading block IDs from `blocks_from_text` through to `Chunk` would be the
# stronger assertion, but `apply_overlap` reduces windows to plain strings, so
# block identity is already gone by the time chunks exist. Until that is
# reworked, coverage is asserted on normalized text.

_WORD = re.compile(r"[^\W_]+")
ENC = get_encoder("cl100k_base")


def _words(text: str) -> Counter:
    return Counter(w.lower() for w in _WORD.findall(text))


def _flat(text: str) -> str:
    return " ".join(text.split())


def assert_lossless(pages, *, config=None) -> None:
    """Every block `blocks_from_text` produced must reach at least one chunk.

    Overlap makes chunk text deliberately repetitive, so this is containment,
    never equality: the output may repeat the source, but must not lose it.
    """
    blocks = [b for page, text in pages for b in blocks_from_text(text, page)]
    assert blocks, "fixture produced no source blocks"
    surface = _surface(chunk_pages(pages, META, config=config))

    # Splitting an oversized block consumes the separator it split on, so
    # compare words rather than punctuation: no word may go missing anywhere.
    lost = _words("\n".join(b.text for b in blocks)) - _words(surface)
    assert not lost, f"words dropped: {dict(lost)}"

    # A block under the child target is never split, so it must survive whole.
    cap = (config or config_for(META.source_type)).child_target_tokens
    flat_surface = _flat(surface)
    for block in blocks:
        if ENC.count(block.text) <= cap:
            assert _flat(block.text) in flat_surface, (
                f"{block.kind} block absent from every chunk: {block.text[:80]!r}"
            )


PROSE = "Coastal infrastructure needs sustained adaptation investment. " * 10

# Shapes drawn from the failure patterns seen in the extracted corpus.
SHAPES = {
    "heading_run_only": "\n".join(ZONE_TABLE) + "\n",
    "all_headings_no_body": "\n".join(ALL_HEADINGS) + "\n",
    "lone_heading": "Water Supply\n",
    "prose_without_heading": PROSE,
    "heading_then_prose": f"3.1 Interventions Proposed\n\n{PROSE}",
    "heading_run_then_prose": "\n".join(ZONE_TABLE) + f"\n\n{PROSE}",
    "trailing_heading": f"{PROSE}\n\nReferences\n",
    "atx_markdown": f"## Scope of the Study\n\n{PROSE}\n\n### Key Findings\n\n{PROSE}",
    "markdown_table": (
        "Parameters | Case I | Case II\n"
        "--- | --- | ---\n"
        "Capacity kWp | 10 | 25\n"
        "Annual units | 14000 | 35000\n"
    ),
    "code_fence": "```\nfor zone in zones:\n    assess(zone)\n```\n",
    "toc_dot_leaders": (
        "Contents\n"
        "Introduction ........ 4\n"
        "Methodology ......... 9\n"
        "Recommendations .... 21\n"
        "References ......... 44\n"
    ),
    "roman_numeral_list": "i) Sewerage Zones\nii) Pumping Stations\niii) Discharge Points\n",
    "allcaps_run": "EXECUTIVE SUMMARY\nKEY FINDINGS\nRECOMMENDATIONS\n",
    "oversized_block_is_split": PROSE * 6,
}


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_no_source_block_is_lost(shape):
    assert_lossless([(1, SHAPES[shape])])


def test_no_source_block_is_lost_across_pages():
    """Blocks are cut per page, so the page seam is its own loss risk."""
    assert_lossless(
        [
            (1, "INTRODUCTION: PANAJI\n\nPanaji has been identified as one of the coastal"),
            (2, f"cities vulnerable to flooding.\n\nScope of the Study\n\n{PROSE}"),
            (3, "Zone Vulnerabilities\nWater Supply\nTransport\n"),
        ]
    )


def test_no_source_block_is_lost_in_a_whole_document():
    """The shapes interleaved, as they arrive in a real report."""
    assert_lossless(
        [
            (1, f"EXECUTIVE SUMMARY\n\n{PROSE}"),
            (2, SHAPES["toc_dot_leaders"]),
            (3, "\n".join(ZONE_TABLE) + f"\n\n{PROSE}"),
            (4, SHAPES["markdown_table"] + f"\n{PROSE}"),
            (5, f"3.2 Estimated Energy Savings\n\n{PROSE * 4}"),
            (6, "References\n"),
        ]
    )
