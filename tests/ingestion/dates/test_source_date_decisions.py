"""The date audit trail covers website documents, not only PDFs.

``{state}_date_decision`` is both the audit trail ("why does this document carry
this date?") and the review queue. It held PDF rows only, so the question was
unanswerable for the thousands of documents dated from the CMS record itself —
which is where the large errors are.

Two shaping constraints, both tested below:

**A row is written when the document's bundle maps to a real CMS date field.**
For a bundle mapped to ``created`` there is nothing a row would add:
``documents.bundle`` plus ``published_at_source='created'`` already says "this
content type takes its creation stamp", and a row per document saying so would
cost an INSERT and a commit each across thousands of documents.

**The review queue must not be swamped.** A field that is simply empty is a
*fallback*, not something a person has to settle. Only a field holding something
that is not a date reaches the queue — the CMS says this content type is dated by
that field, and the field holds nonsense.
"""

from __future__ import annotations

import pytest

from app.catalog.date_decisions import from_effective_date
from app.ingestion.bundle_dates import resolve

CREATED = "2018-01-11T06:29:59+00:00"


def _row(bundle: str, metadata: dict, created: str | None = CREATED):
    resolved = resolve(bundle, created, metadata)
    return from_effective_date(
        document_id="uuid-1", url="https://teriin.org/news/x",
        created=created, resolved=resolved, title="A document",
    )


# --------------------------------------------------------------------------- #
# When nothing is written
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bundle", ["article", "page", "videos", "people"])
def test_a_bundle_dated_by_its_creation_stamp_gets_no_row(bundle):
    """`documents.bundle` plus `published_at_source` is the whole answer."""
    assert _row(bundle, {}) is None


def test_an_unmapped_bundle_gets_no_row():
    assert _row("brand_new_bundle", {"field_x_date": "2019-01-01"}) is None


def test_a_missing_resolution_is_not_an_error():
    assert from_effective_date(document_id="d", url=None, created=None,
                               resolved=None) is None


def test_a_date_field_the_bundle_is_not_mapped_to_gets_no_row():
    """`article` maps to `created`, so a stray date field on the record is not a
    decision anyone made and there is nothing to explain."""
    assert _row("article", {"field_news_date": "2015-08-26T18:30:00+00:00"}) is None


# --------------------------------------------------------------------------- #
# When the field supplied the date
# --------------------------------------------------------------------------- #

def test_an_applied_field_date_is_recorded_as_an_override():
    row = _row("news", {"field_news_date": "2015-08-26T18:30:00+00:00"})
    assert row.action == "propose_override"
    assert row.rule == "bundle_date_field"
    assert row.candidate_source == "field_news_date"
    assert row.confidence == 1.0


def test_a_field_date_matching_the_creation_stamp_is_recorded_as_a_keep():
    row = _row("news", {"field_news_date": "2018-01-10T18:30:00+00:00"})
    assert row.action == "keep_page_date"
    assert row.rule == "bundle_field_matches_created"


def test_the_row_reads_as_would_have_been_x_assigned_y():
    row = _row("news", {"field_news_date": "2015-08-26T18:30:00+00:00"})
    assert row.current_published_at == CREATED
    assert row.candidate_date.startswith("2015-08-27")


def test_the_evidence_names_the_bundle_the_field_and_the_value():
    row = _row("research_papers", {"field_rpaper_year": 2022})
    assert "research_papers" in row.evidence
    assert "field_rpaper_year" in row.evidence
    assert "2022" in row.evidence


def test_the_row_records_what_kind_of_date_the_field_holds():
    """A project start applied as a document's date is still a project start.
    Recording it as "publication" would erase the one thing an auditor needs."""
    assert _row("news", {"field_news_date": "2015-08-26T18:30:00+00:00"}).date_type \
        == "publication"
    assert _row("completed_projects",
                {"field_completed_start_date": "2004-06-28T18:30:00+00:00"}).date_type \
        == "period"
    assert _row("events",
                {"field_event_start_date": "2017-11-05T18:30:00+00:00"}).date_type \
        == "event"


# --------------------------------------------------------------------------- #
# When the field disappointed
# --------------------------------------------------------------------------- #

def test_an_empty_field_is_recorded_but_not_queued_for_review():
    """A fallback is a known outcome, not a case a person has to settle."""
    row = _row("news", {"field_news_date": None})
    assert row.action == "keep_page_date"
    assert row.rule == "bundle_field_empty"
    assert row.candidate_date == CREATED


def test_a_field_absent_from_the_record_is_recorded_the_same_way():
    assert _row("report", {}).rule == "bundle_field_empty"


def test_an_unusable_value_does_reach_the_review_queue():
    """The CMS says this content type is dated by that field and the field holds
    something that is not a date. Nobody can fix that from here."""
    row = _row("news", {"field_news_date": "not a date"})
    assert row.action == "needs_manual_review"
    assert row.rule == "bundle_field_invalid"
    assert "not a date" in row.evidence


def test_a_disappointing_field_is_not_credited_as_the_source():
    """`candidate_source` must not name a field that supplied nothing."""
    for metadata in ({"field_news_date": None}, {"field_news_date": "nonsense"}):
        assert _row("news", metadata).candidate_source == "node_effective_date"


# --------------------------------------------------------------------------- #
# Shape
# --------------------------------------------------------------------------- #

def test_the_row_is_a_page_not_a_file():
    row = _row("news", {"field_news_date": "2015-08-26T18:30:00+00:00"})
    assert row.origin == "website"
    # A source record is its own page, so the join every report makes on
    # node_uuid resolves rather than dangling.
    assert row.node_uuid == "uuid-1"
    assert row.page_pdf_count == 1
    assert row.decided_by == "deterministic"


def test_the_bundle_is_carried_from_the_resolution():
    assert _row("press_release",
                {"field_pressrelease_date": "2012-04-17T18:30:00+00:00"}).bundle \
        == "press_release"


def test_every_written_value_fits_its_column():
    """`date_type` is VARCHAR(16), `candidate_source` VARCHAR(32), `rule`
    VARCHAR(48), `action` VARCHAR(24)."""
    cases = [
        ("news", {"field_news_date": "2015-08-26T18:30:00+00:00"}),
        ("news", {"field_news_date": None}),
        ("news", {"field_news_date": "nonsense"}),
        ("completed_projects",
         {"field_completed_start_date": "2004-06-28T18:30:00+00:00"}),
        ("research_papers", {"field_rpaper_year": 2022}),
    ]
    for bundle, metadata in cases:
        row = _row(bundle, metadata)
        assert len(row.date_type) <= 16
        assert len(row.candidate_source) <= 32
        assert len(row.rule) <= 48
        assert len(row.action) <= 24
        assert len(row.origin) <= 16
