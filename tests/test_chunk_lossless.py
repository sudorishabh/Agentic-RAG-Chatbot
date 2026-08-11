"""Chunking must not drop extracted text.

A run of short lines — an extracted table column, a bare list — is classified as
consecutive headings. Folding those into the section heading left the section
with no body, which packed to zero chunks and lost every line.
"""

from __future__ import annotations

from app.ingestion.chunking import DocumentMeta, chunk_document

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


def test_heading_still_titles_its_section_when_a_body_follows():
    """The fix must not stop real headings from owning their section."""
    text = "4 Transition Pathway\n\n" + "Alternative fuels need port infrastructure. " * 8
    children = [c for c in chunk_document(text, META) if not c.is_parent]
    assert children
    assert children[0].section_heading == "4 Transition Pathway"
    assert "Transition Pathway" not in children[0].text
