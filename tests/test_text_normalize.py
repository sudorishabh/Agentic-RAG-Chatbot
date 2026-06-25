"""Tests for extraction-layer page-text boilerplate stripping."""

from __future__ import annotations

from app.ingestion.extractors.text_normalize import normalize_page_text

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
