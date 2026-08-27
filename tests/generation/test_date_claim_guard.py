"""The publication-date guard: a page date must never be reported as a document's.

Instruction alone did not achieve this. With the prompt rule and the header
caveat both in place, four of six sampled answers to "When was the 2024-25
annual report published?" still said "published on 9 February 2022". So the
claim is detected after generation and either regenerated or rewritten.

The fixtures mirror the real context that produced those failures: an FCRA
Financials block dated 2018-04-04 and an annual-report block whose page date is
2022-02-09. Every observed failure quoted the second date while citing the
first, so citation-awareness is tested explicitly.
"""

from __future__ import annotations

import pytest

from app.core.models.context import ContextBlock
from app.generation.date_claims import (
    SAFE_TEMPLATE,
    safe_rewrite,
    verify_date_claims,
)

PAGE_DATE = "2022-02-09T06:59:06+00:00"
FCRA_DATE = "2018-04-04T10:13:35+00:00"


def _blocks() -> list[ContextBlock]:
    """The three-block context the live failures came from."""
    return [
        ContextBlock(n=1, text="", payload={
            "title": "FCRA Financials", "source_type": "pdf_attachment",
            "published_at": FCRA_DATE,
        }),
        ContextBlock(n=3, text="", payload={
            "title": "Annual Report 2024-2025", "source_type": "pdf_attachment",
            "edition_label": "2024-25", "published_at": PAGE_DATE,
        }),
        ContextBlock(n=5, text="", payload={
            "title": "Some news page", "source_type": "website",
            "published_at": "2024-05-01T00:00:00+00:00",
        }),
    ]


# --------------------------------------------------------------------------- #
# 1. A correct page-date statement must pass
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "answer",
    [
        "The page carrying it was published on 2022-02-09 [3].",
        "The web page was published on 9 February 2022 [3].",
        "This listing page was published on 2022-02-09; the report itself gives "
        "no publication date [3].",
        SAFE_TEMPLATE.format(edition="2024-25", page_date="2022-02-09"),
    ],
)
def test_a_page_date_attributed_to_the_page_is_allowed(answer):
    assert verify_date_claims(answer, _blocks()).clean


def test_saying_the_date_is_not_stated_is_allowed():
    answer = ("The report publication date is not stated in the available "
              "sources [3].")
    assert verify_date_claims(answer, _blocks()).clean


# --------------------------------------------------------------------------- #
# 2. An incorrect report-date statement must be caught
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "answer",
    [
        "The 2024-25 annual report was published on 2022-02-09 [3].",
        "The Annual Report 2024-2025 was published on 9 February 2022 [3].",
        "The report has a publication date of February 9, 2022 [3].",
        "This edition was released on 09/02/2022 [3].",
        "The document was issued on 2022-02-09 [3].",
    ],
)
def test_dating_the_report_by_the_page_is_caught(answer):
    report = verify_date_claims(answer, _blocks())
    assert not report.clean
    assert report.offenders[0].claimed_date.isoformat() == "2022-02-09"


def test_a_trailing_qualifier_does_not_rescue_the_claim():
    """The exact shape observed live: assert it, then hedge in the next sentence."""
    answer = ("The 2024-25 annual report was published on 9 February 2022 [3]. "
              "However, the specific publication date is not stated in the sources.")
    assert not verify_date_claims(answer, _blocks()).clean


# --------------------------------------------------------------------------- #
# 3. Cross-block mis-attribution
# --------------------------------------------------------------------------- #

def test_a_citation_that_does_not_carry_the_date_is_named_as_misattribution():
    """The live failure: the date came from [3], the citation pointed at [1].

    [1] is dated 2018-04-04, so it cannot support a 2022-02-09 claim. A
    citation-blind check would have let this through.
    """
    answer = "The **2024-25 annual report** was published on **9 February 2022** [1]."
    report = verify_date_claims(answer, _blocks())
    assert not report.clean
    assert report.offenders[0].reason == "mis-attributed citation"
    assert report.offenders[0].citations == (1,)


def test_citing_the_block_that_holds_the_date_is_still_a_conflation():
    """Correct citation, wrong claim - flagged, but described differently."""
    answer = "The 2024-25 annual report was published on 2022-02-09 [3]."
    report = verify_date_claims(answer, _blocks())
    assert report.offenders[0].reason == "conflation"


def test_the_reason_appears_in_the_correction_note():
    answer = "The 2024-25 annual report was published on 9 February 2022 [1]."
    note = verify_date_claims(answer, _blocks()).correction_note()
    assert "mis-attributed citation" in note
    assert "2022-02-09" in note
    assert "report publication date: not stated in the available sources" in note


# --------------------------------------------------------------------------- #
# 4. ISO and natural-language date formats
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "spelling",
    ["2022-02-09", "9 February 2022", "9th February 2022", "February 9, 2022",
     "Feb 9, 2022", "09/02/2022", "9-2-2022", "2022/02/09"],
)
def test_every_spelling_of_the_page_date_is_recognised(spelling):
    answer = f"The 2024-25 report was published on {spelling} [3]."
    assert not verify_date_claims(answer, _blocks()).clean


# --------------------------------------------------------------------------- #
# 5. A report that genuinely states its own publication date
# --------------------------------------------------------------------------- #

def test_a_real_publication_date_from_the_document_is_not_touched():
    """Only the page date is forbidden. A date the document itself states is
    exactly what the pipeline is meant to surface."""
    answer = ("The report states it was published on 21 November 2025 [3], and "
              "covers the 2024-25 financial year.")
    assert verify_date_claims(answer, _blocks()).clean


def test_a_website_pages_own_date_is_not_forbidden():
    answer = "That news page was published on 2024-05-01 [5]."
    assert verify_date_claims(answer, _blocks()).clean


# --------------------------------------------------------------------------- #
# 6. No over-triggering on unrelated documents
# --------------------------------------------------------------------------- #

def test_an_unrelated_financial_document_date_is_left_alone():
    answer = "The FCRA financial statements were published on 2018-04-04 [1]."
    assert verify_date_claims(answer, _blocks()).clean


def test_a_context_without_any_edition_is_never_flagged():
    """No edition-bearing block means no page date in the sense that matters."""
    blocks = [ContextBlock(n=1, text="", payload={
        "title": "A report", "published_at": PAGE_DATE})]
    answer = "The report was published on 2022-02-09 [1]."
    assert verify_date_claims(answer, blocks).clean


def test_prose_mentioning_the_date_without_a_publication_claim_is_fine():
    answer = ("The 2024-25 report describes work carried out from 2022-02-09 "
              "onwards [3].")
    assert verify_date_claims(answer, _blocks()).clean


def test_an_edition_label_alone_is_not_a_date_claim():
    answer = "The Annual Report 2024-2025 covers the 2024-25 financial year [3]."
    assert verify_date_claims(answer, _blocks()).clean


# --------------------------------------------------------------------------- #
# The fallback rewrite
# --------------------------------------------------------------------------- #

def test_the_fallback_replaces_the_offending_sentence():
    answer = ("The 2024-25 annual report was published on 9 February 2022 [1]. "
              "It covers TERI activities for that year.")
    report = verify_date_claims(answer, _blocks())
    rewritten = safe_rewrite(answer, report)
    assert "published on 9 February 2022" not in rewritten
    assert "report edition: 2024-25" in rewritten
    assert "page publication date: 2022-02-09" in rewritten
    assert "report publication date: not stated in the available sources" in rewritten
    # Everything else survives.
    assert "It covers TERI activities for that year." in rewritten


def test_the_rewritten_answer_passes_the_check():
    """The fallback must not leave a claim the guard would flag again."""
    answer = "The 2024-25 annual report was published on 9 February 2022 [1]."
    report = verify_date_claims(answer, _blocks())
    assert verify_date_claims(safe_rewrite(answer, report), _blocks()).clean


def test_a_clean_answer_is_returned_untouched():
    answer = "The report publication date is not stated [3]."
    report = verify_date_claims(answer, _blocks())
    assert safe_rewrite(answer, report) == answer


# --------------------------------------------------------------------------- #
# Integration: the exact query that failed, sampled
# --------------------------------------------------------------------------- #

@pytest.mark.llm
def test_the_delivered_answer_never_dates_the_report_by_its_page():
    """The acceptance criterion, sampled rather than run once.

    Before the guard, four of six samples of this query dated the 2024-25 report
    to the page date. One sample proves nothing here, so several must all be
    clean. The answer checked is the delivered one: whatever a correction event
    replaced the stream with, since that is what a reader sees.
    """
    from app.config import get_settings

    settings = get_settings()
    if not (settings.azure_openai_endpoint and settings.azure_openai_model):
        pytest.skip("no LLM deployment configured")

    from app.generation.sections import strip_tags
    from app.pipeline.query_pipeline import search_blocks, stream_answer

    question = "When was the 2024-25 annual report published?"
    blocks = search_blocks(question)
    offenders: list[str] = []
    fallbacks = 0
    for _ in range(4):
        tokens, delivered, reason = "", None, None
        for event in stream_answer(question):
            if not isinstance(event, dict):
                continue
            if event.get("type") == "token":
                tokens += event.get("text") or ""
            elif event.get("type") == "correction":
                delivered, reason = event.get("text"), event.get("reason")
        if reason == "publication_date_fallback":
            fallbacks += 1
        answer = strip_tags(delivered if delivered is not None else tokens)
        assert answer.strip(), "the model returned nothing"
        report = verify_date_claims(answer, blocks)
        if not report.clean:
            offenders.append(report.offenders[0].describe())
    assert not offenders, (
        f"{len(offenders)}/4 delivered answers dated the report by its page:\n"
        + "\n".join(offenders)
    )
    # Recorded rather than asserted: a fallback means the retry failed too, which
    # is safe but worth seeing in the log.
    print(f"mechanical fallbacks used: {fallbacks}/4")
