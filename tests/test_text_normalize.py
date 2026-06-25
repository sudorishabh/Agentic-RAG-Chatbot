"""Tests for extraction-layer page-text boilerplate stripping."""

from __future__ import annotations

from app.ingestion.extractors.text_normalize import normalize_page_text, strip_running_lines

DIRTY = """ACHIEVING GREEN STEEL: ROADMAP TO A NET ZERO STEEL SECTOR IN INDIA
|  ii  |
<!-- PageBreak -->
<!-- PageNumber="22" -->
<figure>

teri
THE ENERGY AND RESOURCES INSTITUTE

</figure>

<figure></figure>

Real body text that should stay.

| 14 |
"""


def test_strips_html_comments():
    out = normalize_page_text(DIRTY)
    assert "<!--" not in out and "PageBreak" not in out and "PageNumber" not in out


def test_unwraps_figures_and_drops_empty_ones():
    out = normalize_page_text(DIRTY)
    assert "<figure>" not in out and "</figure>" not in out
    assert "teri" in out  # non-empty figure content is kept, just unwrapped


def test_removes_page_number_bars():
    out = normalize_page_text(DIRTY)
    assert "|  ii  |" not in out
    assert "| 14 |" not in out


def test_keeps_real_body_text():
    out = normalize_page_text(DIRTY)
    assert "Real body text that should stay." in out


def test_keeps_real_table_rows():
    row = "| Parameter | Value | Unit |"
    assert normalize_page_text(row) == row


def test_empty_input():
    assert normalize_page_text("") == ""


# --- running header/footer stripping --------------------------------------- #

def _pages(body):
    # 4 pages, each = a repeated running header + unique body line
    return [f"REPORT TITLE — RUNNING HEADER\n{line}" for line in body]


def test_strips_line_repeated_across_pages():
    pages = _pages(["alpha body", "beta body", "gamma body", "delta body"])
    out = strip_running_lines(pages)
    assert all("RUNNING HEADER" not in p for p in out)
    assert "alpha body" in out[0] and "delta body" in out[3]


def test_keeps_lines_unique_to_one_page():
    pages = ["only here", "page two", "page three", "page four"]
    assert strip_running_lines(pages) == pages


def test_noop_for_short_documents():
    pages = ["HEADER\nx", "HEADER\ny"]  # 2 pages < min_pages
    assert strip_running_lines(pages) == pages


def test_never_strips_table_rows():
    pages = ["| H | dr |\nrow a", "| H | dr |\nrow b", "| H | dr |\nrow c", "| H | dr |\nrow d"]
    out = strip_running_lines(pages)
    assert all("| H | dr |" in p for p in out)  # repeated table header preserved


def test_disabled_when_fraction_zero():
    pages = _pages(["a", "b", "c", "d"])
    assert strip_running_lines(pages, min_fraction=0) == pages
