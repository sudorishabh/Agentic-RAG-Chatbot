"""Tests for heading-detection rejection of extraction artifacts."""

from __future__ import annotations

import pytest

from app.ingestion.chunking.segmenter import line_heading_level


def _is_heading(s: str) -> bool:
    return line_heading_level(s, at_block_start=True) is not None


# --- rejects extraction artifacts ------------------------------------------ #

def test_rejects_toc_dotted_leader():
    assert not _is_heading("5.9 Implement a carbon border tariff..............41")


def test_rejects_list_of_figures_entry():
    assert not _is_heading("Model Indian Ship)....34 — Overall Conclusions...60 — References")


def test_rejects_html_comment_fragment():
    assert not _is_heading("<!-- PageBreak")


def test_rejects_pipe_formula_row():
    assert not _is_heading("GFIattained — Energytotal — Σ΄ ΕΙ|XEnergy]")


def test_rejects_ocr_symbol_soup():
    assert not _is_heading("ĐỒ (GR S)] — JO (68 106)")


def test_rejects_large_number_fragment():
    assert not _is_heading("250 MtCO2 (about 10% of total")


def test_rejects_decimal_measurement_fragment():
    assert not _is_heading("0.35 MT (2030)")


# --- still accepts real headings ------------------------------------------- #

def test_accepts_numbered_heading():
    assert _is_heading("4.1 Alternative Fuel Cost Comparison")


def test_accepts_deep_numbered_heading():
    assert _is_heading("1.3.2 Digitalisation")


def test_accepts_allcaps_heading():
    assert _is_heading("EXECUTIVE SUMMARY")


def test_accepts_titlecase_heading():
    assert _is_heading("Transition Pathway")


# --- rejects URLs ---------------------------------------------------------- #

def test_rejects_footnote_url_numbered_like_a_heading():
    assert not _is_heading(
        "1 http://jnnurm.nic.in/wp-content/uploads/2010/12/panaji_Chapter-3.pdf"
    )


def test_rejects_bare_url():
    assert not _is_heading("www.teriin.org/policy-brief")


def test_atx_heading_may_still_contain_a_url():
    """Authored `##` is an explicit signal and outranks the URL veto."""
    assert line_heading_level("## See http://teriin.org for detail", at_block_start=True) == 2


# --- rejects list markers -------------------------------------------------- #

@pytest.mark.parametrize(
    "line",
    [
        "iv) WasteWater Treatment Plants",
        "i) Sewerage Zones",
        "ii) Transport",
        "a) Water Supply",
        "b) Sewerage and Drainage",
        "1) Introduction",
        "2) Methodology",
        "(3) Discharge Points",
    ],
)
def test_rejects_list_marker(line):
    assert not _is_heading(line)


# --- rejects a bare number opening prose ----------------------------------- #

def test_rejects_bare_number_before_lowercase_prose():
    assert not _is_heading("4 way segregation centres")


def test_accepts_bare_number_before_a_capitalised_title():
    assert line_heading_level("4 Transition Pathway", at_block_start=True) == 1


# --- accepts Title Case containing lowercase function words ----------------- #

@pytest.mark.parametrize(
    "line",
    [
        "Scope of the Study",
        "Analysis of Energy Consumption",
        "Impact of Climate Change on Water Supply",
        "Methodology for the Study",
        "Relevance of Development Goals",
    ],
)
def test_accepts_titlecase_heading_with_function_words(line):
    assert line_heading_level(line, at_block_start=True) == 3


def test_still_rejects_prose_that_only_capitalises_its_first_word():
    assert not _is_heading("The study assessed vulnerability of coastal areas")


def test_rejects_a_line_of_only_minor_words():
    assert not _is_heading("of the and")


@pytest.mark.parametrize("line", ["Preface", "Recommendations", "Conclusion", "Abstract"])
def test_accepts_single_word_heading(line):
    """Single-word section headings are common in reports; requiring two
    content words to qualify would silently drop them."""
    assert line_heading_level(line, at_block_start=True) == 3


def test_rejects_titlecase_line_with_an_uncapitalised_content_word():
    assert not _is_heading("Alternative fuels Pathway")


# --- numbered section levels ----------------------------------------------- #

@pytest.mark.parametrize(
    ("line", "level"),
    [
        ("1. Introduction", 1),
        ("2. Methodology", 1),
        ("3. Results", 1),
        ("3.1 Energy Savings", 2),
        ("4.1 Alternative Fuel Cost Comparison", 2),
        ("1.3.2 Digitalisation", 3),
    ],
)
def test_numbered_heading_level(line, level):
    assert line_heading_level(line, at_block_start=True) == level
