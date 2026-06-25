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


# --- chart/axis number-soup --------------------------------------------- #

def test_drops_axis_number_soup():
    assert normalize_page_text("2020     2030     2040     2050") == ""
    assert normalize_page_text("200 100 2020 2030 2040 2050") == ""


def test_keeps_numbers_inside_prose():
    line = "In 2020 the sector emitted 200 Mt of CO2."
    assert normalize_page_text(line) == line


def test_keeps_short_numeric_runs():
    assert normalize_page_text("200 100 0") == "200 100 0"  # < 4 tokens


def test_number_soup_can_be_disabled():
    soup = "2020 2030 2040 2050"
    assert normalize_page_text(soup, drop_number_soup=False) == soup


def test_drops_vertical_axis_number_runs():
    chart = "Body sentence.\n600\n2020\n2030\n2040\n2050\n2060\nMore body."
    out = normalize_page_text(chart)
    assert "2020" not in out and "600" not in out
    assert "Body sentence." in out and "More body." in out


def test_keeps_short_vertical_number_run():
    assert normalize_page_text("100\n200\n300") == "100\n200\n300"  # < 4 lines
