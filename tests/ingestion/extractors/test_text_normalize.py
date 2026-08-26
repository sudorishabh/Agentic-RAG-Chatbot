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


def test_strips_dangling_open_comment():
    out = normalize_page_text('Body text stays.\n<!-- PageFooter="Advanced Green Fuels for Marit')
    assert "PageFooter" not in out and "<!--" not in out
    assert "Body text stays." in out


def test_strips_dangling_close_comment():
    out = normalize_page_text('ime Application- Road Map for India (Part A)" -->\nReal body here.')
    assert "-->" not in out and "Application" not in out
    assert "Real body here." in out


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


def test_strips_footer_fragmented_mid_word():
    # Same footer, split at a different point on each page (OCR variance).
    pages = [
        "Body of page one here.\nAdvanced Green Fuels for Ma\nritime Application-",
        "Body of page two here.\nAdvanced Green Fuels for M\naritime Application-",
        "Body of page three here.\nAdvanced Green Fuels for Mar\nitime Application-",
        "Body of page four here.\nAdvanced Green Fuels for Ma\nritime Application-",
    ]
    out = strip_running_lines(pages)
    assert all("aritime" not in p and "ritime" not in p for p in out)
    assert all(p.startswith("Body of page") for p in out)


# --- recto/verso running heads ------------------------------------------ #
#
# Print layouts routinely put a running head on one side only. A recto-only
# footer cannot reach half of *all* pages — an 8-page booklet has 4 recto pages
# against a threshold of 4 — so it is measured against its own side instead, and
# only when it never appears on the other side.


# Bodies must differ by *letters*: `_running_key` strips digits, so pages that
# vary only by a number collapse to one key and look like furniture themselves.
_BODIES = [
    "Coastal erosion reshaped the northern shoreline considerably.",
    "Groundwater salinity rose across the eastern wards this decade.",
    "Sewerage capacity remained unchanged despite population growth.",
    "Tourist arrivals peaked during the winter festival season.",
    "Mangrove cover declined near the estuary mouth.",
    "Road drainage failed repeatedly under monsoon loading.",
    "Heritage precincts require separate conservation funding.",
    "Solid waste collection routes were consolidated last year.",
    "Energy demand tracked commercial floor space closely.",
    "Ferry services absorbed most cross-river commuter traffic.",
    "Schools reported flooding on low-lying approach roads.",
    "Hospital access routes need elevation above surge level.",
]


def _booklet(footer: str, n: int = 8, *, on_recto: bool = True) -> list[str]:
    """n pages, `footer` printed on one side only (page 1 is recto)."""
    pages = []
    for i in range(n):
        recto = i % 2 == 0
        body = _BODIES[i % len(_BODIES)]
        pages.append(f"{body}\n{footer}" if recto == on_recto else body)
    return pages


def test_strips_a_recto_only_running_footer():
    """H2: a footer on odd pages only, which never reaches half of all pages."""
    pages = _booklet("Case study brief: Panaji (goa, india)")
    out = strip_running_lines(pages)
    assert all("Case study brief" not in p for p in out)
    assert all(_BODIES[i % len(_BODIES)] in p for i, p in enumerate(out))


def test_strips_a_verso_only_running_header():
    """H1: the same, printed on even pages instead."""
    pages = _booklet("City Development Plan 2021", on_recto=False)
    out = strip_running_lines(pages)
    assert all("City Development Plan" not in p for p in out)
    assert all(_BODIES[i % len(_BODIES)] in p for i, p in enumerate(out))


def test_page_number_beside_the_footer_goes_with_it():
    """The number and the footer are one piece of furniture: the window join
    spans both, so neither is left stranded in the body text."""
    pages = []
    for i in range(8):
        body = _BODIES[i]
        pages.append(f"{body}\n{i + 1}\nCase study brief: Panaji (goa, india)" if i % 2 == 0 else body)
    out = strip_running_lines(pages)
    assert all("Case study brief" not in p for p in out)
    for i, page in enumerate(out):
        assert page.strip() == _BODIES[i]


def test_repeated_content_on_both_sides_is_kept():
    """H3: a label repeating on both recto and verso is content, not furniture.

    It sits under the all-pages threshold, and because it appears on both sides
    the recto/verso rule must not rescue it into the boilerplate set.
    """
    pages = []
    for i in range(12):
        body = _BODIES[i % len(_BODIES)]
        # pages 1, 2 and 5 — mixed parity, 3/12 of the document
        pages.append(f"{body}\nEcologically Sensitive Areas" if i in (0, 1, 4) else body)
    out = strip_running_lines(pages)
    assert sum("Ecologically Sensitive Areas" in p for p in out) == 3
    assert all(_BODIES[i % len(_BODIES)] in p for i, p in enumerate(out))


def test_one_sided_content_below_the_side_threshold_is_kept():
    """H3: appearing on one side is not enough — it must dominate that side."""
    pages = []
    for i in range(12):  # 6 recto pages; put the line on only 2 of them
        body = _BODIES[i % len(_BODIES)]
        pages.append(f"{body}\nWater Supply" if i in (0, 2) else body)
    out = strip_running_lines(pages)
    assert sum("Water Supply" in p for p in out) == 2
    assert all(_BODIES[i % len(_BODIES)] in p for i, p in enumerate(out))


def test_a_line_appearing_once_is_never_stripped():
    """H4: one occurrence is not a running head."""
    pages = [f"Body unique to page {i + 1}." for i in range(8)]
    pages[0] += "\nCase study brief: Panaji (goa, india)"
    out = strip_running_lines(pages)
    assert "Case study brief" in out[0]


def test_side_rule_respects_the_absolute_minimum_count():
    """Two occurrences never qualify, however one-sided they look."""
    pages = [_BODIES[i] for i in range(4)]
    for i in (0, 2):
        pages[i] += "\nSome Repeated Label Here"
    out = strip_running_lines(pages)
    assert sum("Some Repeated Label Here" in p for p in out) == 2


def test_stripping_preserves_page_count_and_order():
    """H5: page furniture removal must not disturb which page text sits on —
    page attribution downstream is derived from that position."""
    pages = _booklet("Case study brief: Panaji (goa, india)", n=10)
    out = strip_running_lines(pages)
    assert len(out) == len(pages)
    for i, page in enumerate(out):
        assert _BODIES[i % len(_BODIES)] in page


def test_keeps_short_repeated_real_heading_is_acceptable_loss():
    # Sanity: long body sentences (> max_line_words) are never candidates.
    long_line = "This is a genuinely long body sentence that recurs but must never be stripped as a header."
    pages = [f"{long_line}\nunique {i}" for i in range(4)]
    out = strip_running_lines(pages)
    assert all(long_line in p for p in out)


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


def test_drops_interleaved_chart_data():
    chart = (
        "Intro line that is real.\n"
        "200\n100\nJapan, South Korea\n1,500\n1,000\n500\nChina\n600\n400\nIndia\n"
        "Closing real sentence here."
    )
    out = normalize_page_text(chart)
    assert "Japan, South Korea" not in out and "China" not in out and "1,500" not in out
    assert "Intro line that is real." in out and "Closing real sentence here." in out


def test_keeps_short_label_list_without_numbers():
    text = "Sintering\nCokemaking\nIronmaking\nSteelmaking"
    assert normalize_page_text(text) == text  # short labels but no numbers — kept


# --- degenerate / infographic tables --------------------------------------- #

def test_drops_sparse_wide_infographic_table():
    head = "|  | " + " | ".join(["TOTAL STEEL"] * 4 + ["PROJECTS"] * 11) + " |"
    sep = "| " + " | ".join(["---"] * 16) + " |"
    row1 = "|  |  |  | JFE | JFE | TBC | TBC |  |  |  |  |  |  |  |  |  |"
    row2 = "|  |  |  | US Steel | US Steel |  |  |  |  |  |  |  |  |  |  |"
    table = f"Real intro sentence.\n{head}\n{sep}\n{row1}\n{row2}\nReal outro sentence."
    out = normalize_page_text(table)
    assert "JFE" not in out and "US Steel" not in out and "TOTAL STEEL" not in out
    assert "Real intro sentence." in out and "Real outro sentence." in out


def test_keeps_normal_narrow_table():
    table = (
        "| Technology | TRL | Suitability |\n"
        "| --- | --- | --- |\n"
        "| BF-BOF CCUS | 5 | Limited cost-effectiveness |"
    )
    assert normalize_page_text(table) == table


def test_keeps_wide_table_with_real_data():
    head = "| Year | 2020 | 2030 | 2040 | 2050 | 2060 | 2070 |"
    sep = "| --- | --- | --- | --- | --- | --- | --- |"
    row = "| Demand | 120 | 180 | 250 | 295 | 340 | 360 |"
    table = f"{head}\n{sep}\n{row}"
    assert normalize_page_text(table) == table  # wide but dense + varied — kept


# --- ligature repair ------------------------------------------------------- #

def test_repairs_unicode_ligatures():
    assert normalize_page_text("eﬃcient ﬂow") == "efficient flow"


def test_repairs_dropped_ffi_gap():
    assert normalize_page_text("Ine cient plants are costly.") == "Inefficient plants are costly."
    assert normalize_page_text("energy e cient routes") == "energy efficient routes"
    assert normalize_page_text("a signi cant share") == "a significant share"


def test_ligature_repair_preserves_correct_text():
    s = "The efficient and significant gains were specific to India."
    assert normalize_page_text(s) == s
