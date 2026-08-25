"""What a CMS record's dates mean, and which of them may set a publication date.

The failure this module exists to prevent: the corpus holds ~2,100 project
duration values and ~2,800 event values, all with date-like field names, all
plausible-looking, and every one of them wrong as a publication date. A
completed project that ran 2004-2005 has a page written in 2017. Using the
project's start date would look like a fix and would corrupt 1,069 documents.

So the tests below are weighted toward what must be *refused*. The positive
cases are the four fields verified against the live site; everything else has to
come back empty.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.ingestion.source_dates import (
    FIELD_KINDS,
    classify,
    found_dates,
    is_plausible,
    publication_date,
    to_ist_date,
)


# --------------------------------------------------------------------------- #
# The declaration itself
# --------------------------------------------------------------------------- #

def test_only_four_fields_are_declared_publication_dates():
    """A guard on the table, not on the code. Widening this set is a decision
    that should have to change a test."""
    publication = {f for f, (kind, _) in FIELD_KINDS.items() if kind == "publication"}
    assert publication == {
        "field_news_date", "field_pressrelease_date",
        "field_report_date", "field_rpaper_year",
    }


@pytest.mark.parametrize(
    "field,kind",
    [
        ("field_news_date", "publication"),
        ("field_pressrelease_date", "publication"),
        ("field_rpaper_year", "publication"),
        ("field_event_start_date", "event"),
        ("field_event_end_date", "event"),
        ("field_enddate_forlatestfirst", "event"),
        ("field_completed_start_date", "period"),
        ("field_completed_end_date", "period"),
        ("field_ongoing_start_date", "period"),
    ],
)
def test_each_measured_field_is_classified(field, kind):
    assert classify(field) == kind


def test_an_undeclared_field_is_unknown():
    assert classify("field_something_new_date") == "unknown"


def test_only_the_year_field_carries_year_precision():
    year_only = {f for f, (_, precision) in FIELD_KINDS.items() if precision == "year"}
    assert year_only == {"field_rpaper_year"}


# --------------------------------------------------------------------------- #
# The refusals — the whole point
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "field,value",
    [
        ("field_event_start_date", "2017-11-05T18:30:00+00:00"),
        ("field_event_end_date", "2017-11-13T18:30:00+00:00"),
        ("field_enddate_forlatestfirst", "2020-05-08T22:00:00+05:30"),
        ("field_completed_start_date", "2004-06-28T18:30:00+00:00"),
        ("field_completed_end_date", "2005-06-30T18:30:00+00:00"),
        ("field_ongoing_start_date", "2019-10-24T10:35:27+00:00"),
    ],
)
def test_an_event_or_project_date_is_never_a_publication_date(field, value):
    assert publication_date({field: value}) is None


def test_an_undeclared_date_field_cannot_set_a_date():
    """Ignoring by default is what stops a new CMS field silently moving dates."""
    assert publication_date({"field_brand_new_date": "2020-01-01T00:00:00+00:00"}) is None


def test_a_journal_name_is_not_a_date():
    """``field_article_published_in`` and ``field_rpaper_published_in`` hold
    publication *venues* — 2,149 values whose names contain "published"."""
    assert publication_date({"field_rpaper_published_in": "ScienceDirect"}) is None
    assert publication_date({"field_article_published_in": "Journal of X"}) is None


def test_an_empty_or_absent_record_states_nothing():
    for metadata in ({}, None, {"field_news_date": None}, {"field_news_date": ""},
                     {"field_news_date": []}):
        assert publication_date(metadata) is None


@pytest.mark.parametrize("value", ["1970-01-01T00:00:00+00:00", "1889", "1900-01-01",
                                   "not a date", "0000-00-00"])
def test_an_implausible_value_is_discarded_rather_than_returned(value):
    assert publication_date({"field_news_date": value}) is None


# --------------------------------------------------------------------------- #
# The acceptances
# --------------------------------------------------------------------------- #

def test_a_news_date_is_read_as_the_publication_date():
    found = publication_date({"field_news_date": "2015-08-26T18:30:00+00:00"})
    assert found is not None
    assert found.value == date(2015, 8, 27)
    assert found.field == "field_news_date"
    assert found.precision == "day"
    assert found.is_publication


def test_the_verified_press_release_cases_resolve_to_the_displayed_date():
    """Both checked against the live page: the site shows 18 April 2012 and
    4 November 2015 respectively."""
    assert publication_date(
        {"field_pressrelease_date": "2012-04-17T18:30:00+00:00"}).value \
        == date(2012, 4, 18)
    assert publication_date(
        {"field_pressrelease_date": "2015-11-03T18:30:00+00:00"}).value \
        == date(2015, 11, 4)


def test_a_research_paper_year_is_publication_but_only_to_the_year():
    found = publication_date({"field_rpaper_year": "2016"})
    assert found is not None
    assert found.value.year == 2016
    assert found.precision == "year"


def test_january_on_a_year_precision_value_is_a_marker_not_a_claim():
    """The value has to be *some* date to be stored, so it is 1 January — and
    the precision field is the only thing that says so. A caller that reads the
    day without reading the precision invents a January publication."""
    found = publication_date({"field_rpaper_year": "2016"})
    assert (found.value.month, found.value.day) == (1, 1)
    assert found.precision == "year"


# --------------------------------------------------------------------------- #
# Determinism when a record offers several
# --------------------------------------------------------------------------- #

def test_the_first_declared_publication_field_wins():
    """Declaration order decides, so the outcome cannot depend on how the source
    happened to serialise its keys."""
    both = {
        "field_pressrelease_date": "2013-01-01T00:00:00+00:00",
        "field_news_date": "2012-01-01T00:00:00+00:00",
    }
    assert publication_date(both).field == "field_news_date"
    assert publication_date(dict(reversed(list(both.items())))).field == "field_news_date"


def test_a_publication_field_wins_over_event_and_period_fields_present_too():
    found = publication_date({
        "field_completed_start_date": "2004-06-28T18:30:00+00:00",
        "field_event_start_date": "2017-11-05T18:30:00+00:00",
        "field_news_date": "2015-08-26T18:30:00+00:00",
    })
    assert found.field == "field_news_date"


def test_an_implausible_publication_field_does_not_fall_through_to_an_event_date():
    """Failing over to a lower-kind field would be exactly the bug: a broken
    news date must mean "we know nothing", not "use the event date"."""
    assert publication_date({
        "field_news_date": "1970-01-01T00:00:00+00:00",
        "field_event_start_date": "2017-11-05T18:30:00+00:00",
    }) is None


# --------------------------------------------------------------------------- #
# The audit trail
# --------------------------------------------------------------------------- #

def test_found_dates_reports_the_rejected_candidates_too():
    """"Why was none of it used" is only answerable if what was on offer was
    recorded, which is the same reason the PDF path stores non-publication
    verdicts."""
    found = found_dates({
        "field_completed_start_date": "2004-06-28T18:30:00+00:00",
        "field_completed_end_date": "2005-06-30T18:30:00+00:00",
        "field_news_date": "2015-08-26T18:30:00+00:00",
        "field_unknown_thing": "2001-01-01T00:00:00+00:00",
    })
    assert {(f.field, f.kind) for f in found} == {
        ("field_news_date", "publication"),
        ("field_completed_start_date", "period"),
        ("field_completed_end_date", "period"),
    }


def test_found_dates_is_empty_for_a_record_with_nothing_declared():
    assert found_dates({"title": "x", "field_sponsors": ["a"]}) == []


# --------------------------------------------------------------------------- #
# Timezone handling, shared with the audit
# --------------------------------------------------------------------------- #

def test_ist_midnight_in_utc_is_the_next_calendar_day():
    assert to_ist_date("2012-04-17T18:30:00+00:00") == date(2012, 4, 18)


def test_an_explicit_ist_offset_is_not_shifted_twice():
    assert to_ist_date("2020-05-08T22:00:00+05:30") == date(2020, 5, 8)


def test_a_naive_value_is_read_as_utc():
    assert to_ist_date("2023-02-27T11:30:03") == date(2023, 2, 27)


def test_a_list_value_uses_its_first_entry():
    assert to_ist_date(["2015-08-26T18:30:00+00:00"]) == date(2015, 8, 27)


def test_plausibility_bounds():
    assert is_plausible(date(2019, 6, 1))
    assert not is_plausible(date(1970, 1, 1))
    assert not is_plausible(None)


def test_the_audit_and_the_resolver_share_one_implementation():
    """Two readers of the same ambiguous timestamp format would drift, and the
    drift would be invisible: the audit would report a different number than the
    fix produced."""
    from scripts import audit_dates

    assert audit_dates.to_ist_date is to_ist_date
    assert audit_dates.is_plausible is is_plausible
