"""Deterministic redundancy filtering of the PDF answer block.

The PDF block is supplementary, so it earns its place only by saying something
the website answer does not. These cover the measurement itself, the granularity
it removes at, and — more importantly — the cases where it must keep quiet: the
filter runs on every mixed-source answer, so a false positive silently deletes
information the reader asked for. No network.
"""

from __future__ import annotations

import pytest

from app.generation.redundancy import (
    DEFAULT_COVERAGE,
    content_tokens,
    coverage,
    filter_pdf_text,
    is_covered,
    reference_sentences,
)

WEBSITE = "Product X supports SSO. Product X integrates with Slack."


def _bullets(*lines: str) -> str:
    return "\n".join(f"- {line}" for line in lines)


# --------------------------------------------------------------------------- #
# The three cases the feature is specified by.


def test_a_fully_duplicated_pdf_block_is_removed_entirely():
    pdf = _bullets("Product X supports SSO.", "Product X integrates with Slack.")
    assert filter_pdf_text(pdf, WEBSITE) == ""


def test_b_only_the_repeated_bullets_are_removed():
    pdf = _bullets(
        "Product X supports SSO.",
        "Enterprise customers can configure SAML attributes.",
        "The maximum session timeout is 24 hours.",
    )
    assert filter_pdf_text(pdf, WEBSITE) == _bullets(
        "Enterprise customers can configure SAML attributes.",
        "The maximum session timeout is 24 hours.",
    )


def test_c_a_fully_additive_pdf_block_survives_untouched():
    pdf = _bullets(
        "Internal implementation details.",
        "Troubleshooting guidance.",
        "Configuration examples.",
    )
    assert filter_pdf_text(pdf, "A general product overview.") == pdf


# --------------------------------------------------------------------------- #
# What counts as "already said".


def test_citations_and_markdown_are_not_content():
    # The same claim, one side dressed in a citation, bold and a link.
    pdf = "- **Product X** supports [SSO](https://example.com/sso) [2]."
    assert filter_pdf_text(pdf, "Product X supports SSO [1].") == ""


def test_plural_and_verb_forms_read_as_the_same_claim():
    assert filter_pdf_text("- Product X supports SSO.", "Product X support for SSO.") == ""


def test_a_negation_is_not_a_restatement_of_the_claim_it_denies():
    # Stripping "not" as a function word would collapse these onto one token set
    # and delete the contradiction instead of the repeat.
    pdf = "- Product X does not support SAML."
    assert filter_pdf_text(pdf, "Product X supports SAML.") == pdf


def test_a_sentence_is_measured_against_one_website_sentence_not_all_of_them():
    # Every word here appears somewhere in WEBSITE, but no single sentence says
    # it — pooling the website's vocabulary would delete a genuinely new claim.
    pdf = "- SSO integrates with the Slack product."
    assert filter_pdf_text(pdf, WEBSITE) == pdf


def test_partial_overlap_below_the_threshold_survives():
    pdf = "- Product X supports SSO through an external identity provider broker."
    assert filter_pdf_text(pdf, WEBSITE) == pdf


# --------------------------------------------------------------------------- #
# Granularity: what a removal takes with it.


def test_prose_is_all_or_nothing_rather_than_cut_mid_paragraph():
    # The second sentence repeats the website; excising it would leave "It also
    # means" pointing at text that is no longer there.
    pdf = "Product X supports SSO. It also means audit logs are retained for 90 days."
    assert filter_pdf_text(pdf, WEBSITE) == pdf


def test_a_paragraph_whose_every_sentence_is_covered_is_dropped():
    pdf = "Product X supports SSO. Product X integrates with Slack."
    assert filter_pdf_text(pdf, WEBSITE) == ""


def test_only_the_redundant_paragraph_is_dropped():
    pdf = "Product X supports SSO.\n\nSession timeout maxes out at 24 hours."
    assert filter_pdf_text(pdf, WEBSITE) == "Session timeout maxes out at 24 hours."


def test_a_dropped_item_takes_its_wrapped_continuation_line_with_it():
    # Ungrouped, the wrapped "SSO." line would read as structure and survive the
    # removal of the item it belongs to, stranding half a sentence.
    pdf = "- Product X supports\n  SSO.\n- Timeouts cap at 24 hours."
    assert filter_pdf_text(pdf, WEBSITE) == "- Timeouts cap at 24 hours."


def test_a_continuation_that_adds_content_keeps_its_item():
    # The wrapped clause carries words the website sentence does not, so the
    # item is no longer a restatement of it.
    pdf = "- Product X supports SSO,\n  brokered through Okta or Entra ID."
    assert filter_pdf_text(pdf, WEBSITE) == pdf


def test_emptying_every_item_takes_the_lists_lead_in_too():
    pdf = "Key points:\n" + _bullets(
        "Product X supports SSO.", "Product X integrates with Slack."
    )
    assert filter_pdf_text(pdf, WEBSITE) == ""


def test_a_lead_in_survives_alongside_the_items_that_remain():
    pdf = "Key points:\n" + _bullets(
        "Product X supports SSO.", "Timeouts cap at 24 hours."
    )
    assert filter_pdf_text(pdf, WEBSITE) == "Key points:\n- Timeouts cap at 24 hours."


def test_numbered_items_filter_like_bulleted_ones():
    pdf = "1. Product X supports SSO.\n2. Timeouts cap at 24 hours."
    assert filter_pdf_text(pdf, WEBSITE) == "2. Timeouts cap at 24 hours."


# --------------------------------------------------------------------------- #
# Degenerate input: the filter runs on every mixed answer, so it must never
# throw and never delete what it cannot measure.


@pytest.mark.parametrize("pdf", ["", "   ", "\n\n"])
def test_empty_pdf_text_filters_to_nothing(pdf):
    assert filter_pdf_text(pdf, WEBSITE) == ""


@pytest.mark.parametrize("website", ["", "   ", "[1]", "**"])
def test_without_a_measurable_website_answer_the_pdf_text_is_left_alone(website):
    pdf = "- Product X supports SSO."
    assert filter_pdf_text(pdf, website) == pdf


def test_structural_text_is_never_covered_on_its_own():
    assert not is_covered("---", reference_sentences(WEBSITE))
    assert not is_covered("**Note**", reference_sentences(WEBSITE))


def test_a_table_is_kept_rather_than_measured_as_prose():
    pdf = "| Setting | Value |\n| --- | --- |\n| Timeout | 24h |"
    assert filter_pdf_text(pdf, WEBSITE) == pdf


# --------------------------------------------------------------------------- #
# The measurement primitives.


def test_coverage_is_asymmetric_toward_the_measured_sentence():
    # A short restatement is fully covered by a long sentence that contains it;
    # the long one is not covered by the short. Symmetric overlap would score
    # both low and keep the repeat.
    short = content_tokens("Product X supports SSO.")
    long = content_tokens("Product X supports SSO for enterprise tenants worldwide.")
    assert coverage(short, [long]) == 1.0
    assert coverage(long, [short]) < 1.0


def test_coverage_of_nothing_is_zero_rather_than_a_division_error():
    assert coverage(content_tokens("---"), reference_sentences(WEBSITE)) == 0.0
    assert coverage(content_tokens("anything"), []) == 0.0


def test_the_threshold_is_honoured():
    pdf = "- Product X supports SSO through an external broker."
    assert filter_pdf_text(pdf, WEBSITE, threshold=0.5) == ""
    assert filter_pdf_text(pdf, WEBSITE, threshold=DEFAULT_COVERAGE) == pdf
