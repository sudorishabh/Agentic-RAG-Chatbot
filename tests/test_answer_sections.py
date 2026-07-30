"""The two-block answer structure: parsing and tag stripping.

Covers what the frontend renders and what the verification passes see. The tags
come from a model, so the malformed cases matter as much as the happy path. No
network.
"""

from __future__ import annotations

from app.generation.prompts import PDF_LEAD, PDF_TAG, WEBSITE_TAG
from app.generation.sections import (
    PDF,
    PLAIN,
    WEBSITE,
    split_sections,
    strip_tags,
)


def _web(body):
    return f"<{WEBSITE_TAG}>\n{body}\n</{WEBSITE_TAG}>"


def _pdf(body):
    return f"<{PDF_TAG}>\n{PDF_LEAD}\n{body}\n</{PDF_TAG}>"


def _kinds(answer):
    return [s.kind for s in split_sections(answer)]


# --------------------------------------------------------------------------- #
# split_sections — the shapes the prompt asks for.


def test_both_blocks_parse_in_order():
    sections = split_sections(_web("Grew 1.2 GW [1].") + "\n" + _pdf("60% commercial [2]."))
    assert [s.kind for s in sections] == [WEBSITE, PDF]
    assert sections[0].text == "Grew 1.2 GW [1]."
    assert sections[1].text == f"{PDF_LEAD}\n60% commercial [2]."


def test_website_only_yields_one_section():
    assert _kinds(_web("Grew 1.2 GW [1].")) == [WEBSITE]


def test_pdf_only_yields_one_section():
    assert _kinds(_pdf("60% commercial [2].")) == [PDF]


def test_untagged_answer_is_a_single_plain_section():
    sections = split_sections("I don't have information on that.")
    assert [s.kind for s in sections] == [PLAIN]
    assert sections[0].text == "I don't have information on that."


def test_empty_answer_yields_no_sections():
    assert split_sections("") == []
    assert split_sections("   \n\n  ") == []


# --------------------------------------------------------------------------- #
# split_sections — model non-compliance and truncated streams.


def test_pdf_block_emitted_first_is_reordered_behind_website():
    # The prompt forbids this ordering; the parser enforces it regardless.
    assert _kinds(_pdf("60% commercial [2].") + _web("Grew 1.2 GW [1].")) == [
        WEBSITE,
        PDF,
    ]


def test_repeated_blocks_of_one_kind_merge():
    sections = split_sections(_web("First [1].") + _web("Second [2]."))
    assert [s.kind for s in sections] == [WEBSITE]
    assert sections[0].text == "First [1].\n\nSecond [2]."


def test_unterminated_block_runs_to_the_end():
    sections = split_sections(f"<{WEBSITE_TAG}>\nGrew 1.2 GW [1].")
    assert [s.kind for s in sections] == [WEBSITE]
    assert sections[0].text == "Grew 1.2 GW [1]."


def test_empty_block_is_dropped_rather_than_rendered():
    assert _kinds(_web("Grew 1.2 GW [1].") + f"<{PDF_TAG}>\n\n</{PDF_TAG}>") == [WEBSITE]


def test_unpaired_close_tag_never_reaches_the_output():
    sections = split_sections(f"Plain text.</{PDF_TAG}>")
    assert [s.kind for s in sections] == [PLAIN]
    assert sections[0].text == "Plain text."


def test_tag_casing_and_inner_whitespace_are_tolerated():
    answer = f"<{WEBSITE_TAG.upper()} >\nGrew 1.2 GW [1].\n</{WEBSITE_TAG} >"
    assert _kinds(answer) == [WEBSITE]


# --------------------------------------------------------------------------- #
# split_sections — untagged text keeps its position around the blocks.


def test_catalog_prefix_stays_above_the_blocks():
    answer = "We hold 4 reports.\n\n" + _web("Grew 1.2 GW [1].")
    sections = split_sections(answer)
    assert [s.kind for s in sections] == [PLAIN, WEBSITE]
    assert sections[0].text == "We hold 4 reports."


def test_trailing_remark_stays_below_the_blocks():
    sections = split_sections(_web("Grew 1.2 GW [1].") + "\nAsk me for more.")
    assert [s.kind for s in sections] == [WEBSITE, PLAIN]
    assert sections[-1].text == "Ask me for more."


# --------------------------------------------------------------------------- #
# strip_tags — what the faithfulness and numeric checks see.


def test_strip_tags_removes_wrappers_and_keeps_content():
    stripped = strip_tags(_web("Grew 1.2 GW [1].") + "\n" + _pdf("60% commercial [2]."))
    assert WEBSITE_TAG not in stripped
    assert PDF_TAG not in stripped
    assert "Grew 1.2 GW [1]." in stripped
    assert "60% commercial [2]." in stripped


def test_strip_tags_collapses_the_gaps_left_by_removal():
    assert "\n\n\n" not in strip_tags(_web("A [1].") + "\n\n" + _pdf("B [2]."))


def test_strip_tags_leaves_an_untagged_answer_alone():
    assert strip_tags("I don't have information on that.") == (
        "I don't have information on that."
    )
