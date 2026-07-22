"""Tests for heading-detection rejection of extraction artifacts."""

from __future__ import annotations

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
