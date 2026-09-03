"""A page's date must never be reported as a document's publication date.

Every TERI annual report edition hangs off one Drupal page, so all ten carry
``effective_start_date = 2022-02-09``. Turning that into "Annual Report 2024-25 was
published on 9 February 2022" is a false claim assembled from two true ones,
and it is the specific failure these tests exist to prevent.

The deterministic tests pin what the prompt and the block header tell the model.
:func:`conflates_page_date` is the detector used by both those tests and the
live-model test at the bottom, so the same definition of the failure is applied
in both places.
"""

from __future__ import annotations

import re

import pytest

from app.generation.prompts import GROUNDED_SYSTEM_PROMPT, _source_hint

PAGE_DATE = "2022-02-09T06:59:06+00:00"

# The forbidden claim: an edition (or a report) said to be published on the
# page's date, in any of the ways a model might phrase that date.
_PAGE_DATE_FORMS = (
    r"2022-02-09", r"9 february 2022", r"february 9,? 2022",
    r"feb(?:ruary)? 2022", r"09[/.-]02[/.-]2022", r"02[/.-]09[/.-]2022",
)
_PUBLISHED_VERB = r"(?:was |were |is |been )?publish(?:ed|ing)?|publication date|released"


def conflates_page_date(answer: str) -> bool:
    """Does this answer claim the report was published on the page's date?

    Works on the *subject* of the publication verb, not on keyword presence. A
    correct answer mentions both the page date and publication in the same
    breath ("the page carrying it was published on 2022-02-09"), so a keyword
    test flags it; what distinguishes the failure is that the thing said to be
    published is the report rather than the page.
    """
    for sentence in re.split(r"[.\n;]", answer.lower()):
        if not any(re.search(form, sentence) for form in _PAGE_DATE_FORMS):
            continue
        verb = re.search(_PUBLISHED_VERB, sentence)
        if verb is None:
            continue
        subject = sentence[: verb.start()]
        # Publication attributed to the page is the wording we are asking for.
        if "page" in subject:
            continue
        # Attributed to the document, with the page's date: the false claim.
        if re.search(r"report|edition|20\d{2}[-/]\d{2}", subject):
            return True
    return False


def _annual(edition: str = "2024-25") -> dict:
    return {
        "source_type": "pdf_attachment",
        "title": f"Annual Report {edition[:4]}-20{edition[-2:]}",
        "edition_label": edition,
        "effective_start_date": PAGE_DATE,
        "page_number": 3,
    }


# --------------------------------------------------------------------------- #
# The detector itself
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "answer",
    [
        "The Annual Report 2024-25 was published on 9 February 2022.",
        "Annual Report 2024-25 was published on 2022-02-09.",
        "The 2024-25 report has a publication date of February 9, 2022.",
        "The report was released on 09/02/2022.",
    ],
)
def test_the_detector_catches_the_conflation(answer):
    assert conflates_page_date(answer) is True


@pytest.mark.parametrize(
    "answer",
    [
        # The shape asked for: three labelled parts.
        "Report edition: 2024-25. Page publication date: 2022-02-09. "
        "Report publication date: not stated in the available sources.",
        "The report covers 2024-25. The page carrying it was published on "
        "2022-02-09; the report's own publication date is not stated.",
        "I don't have information on that in the available sources.",
        "The Annual Report 2024-25 covers the financial year 2024-25.",
    ],
)
def test_the_detector_accepts_a_correctly_separated_answer(answer):
    assert conflates_page_date(answer) is False


# --------------------------------------------------------------------------- #
# What the model is told
# --------------------------------------------------------------------------- #

def _flat_prompt() -> str:
    """The prompt with runs of whitespace collapsed.

    The rule text is hard-wrapped for readability, so a phrase can straddle a
    line break. Normalising means a reflow cannot fail these tests while the
    wording is unchanged.
    """
    return " ".join(GROUNDED_SYSTEM_PROMPT.split())


def test_the_prompt_forbids_dating_a_document_by_its_page():
    assert "Never write that a document was published on a page date" in _flat_prompt()


def test_the_prompt_closes_the_qualifier_loophole():
    """The observed failure: the model asserted the false date, then qualified it
    in the next sentence. Saying it at all is the problem."""
    assert "Adding a qualifier afterwards does not repair it" in _flat_prompt()


def test_the_prompt_gives_the_worked_counter_example():
    flat = _flat_prompt()
    assert "Annual Report 2024-25 was published on 9 February 2022" in flat
    assert "false statement assembled out of two true ones" in flat


def test_the_prompt_specifies_the_three_labelled_parts():
    flat = _flat_prompt()
    assert "report edition:" in flat
    assert "page publication date:" in flat
    assert "report publication date: not stated in the available sources" in flat


def test_only_the_document_text_may_supply_a_report_publication_date():
    assert "Only the document's own text may supply a report publication date" \
        in _flat_prompt()


def test_the_conflict_rule_names_the_label_the_header_actually_uses():
    """Rule 9 orders blocks by the header's date, so it must name the real label."""
    assert "later 'page date'" in GROUNDED_SYSTEM_PROMPT
    assert "later 'published' date" not in GROUNDED_SYSTEM_PROMPT


# --------------------------------------------------------------------------- #
# What the model is shown
# --------------------------------------------------------------------------- #

def test_the_header_keeps_the_two_facts_apart():
    header = _source_hint(_annual())
    assert "edition 2024-25" in header
    assert "page date 2022-02-09" in header


def test_the_header_never_presents_the_page_date_as_the_editions():
    assert conflates_page_date(_source_hint(_annual())) is False


@pytest.mark.parametrize("edition", ["2024-25", "2015-16", "2020-21"])
def test_no_edition_is_dated_by_the_page(edition):
    assert conflates_page_date(_source_hint(_annual(edition))) is False


# --------------------------------------------------------------------------- #
# The live model
# --------------------------------------------------------------------------- #

@pytest.mark.llm
@pytest.mark.xfail(
    reason=(
        "Measures the RAW token stream, which is deliberately unguarded. The "
        "publication-date guard corrects post-hoc and emits a `correction` "
        "event that replaces the draft (app/generation/date_claims.py); the "
        "DELIVERED answer is asserted clean in tests/test_date_claim_guard.py. "
        "This test is kept as the standing record that the draft itself still "
        "conflates in roughly 2 of 8 samples."
    ),
    strict=False,
)
def test_the_model_does_not_date_the_report_by_its_page():
    """End-to-end against the configured deployment, sampled.

    One sample is not evidence here - the failure is intermittent, and a
    single-run version of this test passed by luck while the behaviour was still
    wrong two times in three. Several samples must all be clean.
    """
    from app.config import get_settings

    settings = get_settings()
    if not (settings.azure_openai_endpoint and settings.azure_openai_model):
        pytest.skip("no LLM deployment configured")
    from app.pipeline.query_pipeline import stream_answer

    offenders = []
    for _ in range(3):
        answer = ""
        for event in stream_answer("When was the 2024-25 annual report published?"):
            if isinstance(event, dict) and event.get("type") == "token":
                answer += event.get("text") or ""
        assert answer.strip(), "the model returned nothing"
        if conflates_page_date(answer):
            offenders.append(answer.strip()[:200])
    assert not offenders, (
        f"{len(offenders)}/3 samples dated the report by its page:\n"
        + "\n---\n".join(offenders)
    )
