"""Where a document's ``published_at`` comes from when it is built.

Before this, ``published_at`` was the source record's *creation* stamp and
nothing else — which is why 646 completed projects, 369 events and 367 news
items each share one timestamp to the second. Where the source separately states
when the document was published, that statement now wins.

The tests are weighted toward what must **not** change. A record whose only
dates are an event or a project period keeps its created stamp: reading those as
publication dates would move ~5,500 documents to dates nobody asserted, and it
is the single most tempting wrong fix available here.
"""

from __future__ import annotations

import pytest

from app.ingestion.canonical import _published_at_for, from_drupal_record

CREATED = "2018-01-11T06:29:59+00:00"


class _Record:
    """The shape `from_drupal_record` reads. Deliberately not a mock — the point
    is that the real builder is exercised."""

    def __init__(self, metadata: dict, created: str | None = CREATED):
        self.body = "some body text"
        self.title = "A document"
        self.url = "https://teriin.org/press-release/x"
        self.uuid = "uuid-1"
        self.bundle = "press_release"
        self.nid = 7
        self.created = created
        self.changed = created
        self.metadata = metadata
        self.refs = []
        self.pdf_url = None


# --------------------------------------------------------------------------- #
# The default: nothing stated, nothing changes
# --------------------------------------------------------------------------- #

def test_a_record_stating_nothing_keeps_its_created_stamp():
    assert _published_at_for(CREATED, {}) == (CREATED, "created", "day")


def test_a_record_with_no_metadata_at_all_keeps_its_created_stamp():
    assert _published_at_for(CREATED, {})[0] == CREATED


def test_a_missing_created_stamp_stays_missing():
    """No invention: a source with no date and no statement has no date."""
    assert _published_at_for(None, {}) == (None, "created", "day")


# --------------------------------------------------------------------------- #
# The refusals — dates that exist and must not be used
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
def test_an_event_or_project_date_never_becomes_the_publication_date(field, value):
    assert _published_at_for(CREATED, {field: value}) == (CREATED, "created", "day")


def test_an_undeclared_date_field_cannot_move_the_date():
    assert _published_at_for(
        CREATED, {"field_newly_added_date": "2001-01-01T00:00:00+00:00"}
    ) == (CREATED, "created", "day")


def test_an_implausible_stated_date_leaves_the_created_stamp_alone():
    assert _published_at_for(
        CREATED, {"field_news_date": "1970-01-01T00:00:00+00:00"}
    ) == (CREATED, "created", "day")


# --------------------------------------------------------------------------- #
# The correction
# --------------------------------------------------------------------------- #

def test_a_stated_news_date_wins_over_the_created_stamp():
    published, source, precision = _published_at_for(
        CREATED, {"field_news_date": "2015-08-26T18:30:00+00:00"})
    assert published == "2015-08-27T00:00:00+00:00"
    assert (source, precision) == ("cms_field", "day")


def test_the_stored_string_is_utc_midnight_on_the_indian_calendar_day():
    """The whole off-by-one class. ``state._to_datetime`` normalises to naive
    UTC, so an IST-midnight string would land a day early in the column and
    every consumer would read the wrong calendar date."""
    published, _, _ = _published_at_for(
        CREATED, {"field_pressrelease_date": "2012-04-17T18:30:00+00:00"})
    assert published == "2012-04-18T00:00:00+00:00"
    assert not published.endswith("+05:30")


def test_the_two_live_verified_cases_resolve_to_the_displayed_date():
    """Checked against the rendered pages: the site shows 18 April 2012 and
    4 November 2015."""
    for value, expected in (("2012-04-17T18:30:00+00:00", "2012-04-18"),
                            ("2015-11-03T18:30:00+00:00", "2015-11-04")):
        published, _, _ = _published_at_for(CREATED, {"field_pressrelease_date": value})
        assert published.startswith(expected)


def test_a_publication_field_wins_even_when_event_and_period_fields_are_present():
    published, source, _ = _published_at_for(CREATED, {
        "field_completed_start_date": "2004-06-28T18:30:00+00:00",
        "field_event_start_date": "2017-11-05T18:30:00+00:00",
        "field_news_date": "2015-08-26T18:30:00+00:00",
    })
    assert published.startswith("2015-08-27")
    assert source == "cms_field"


# --------------------------------------------------------------------------- #
# A year-only source, and the one case where it must NOT win
# --------------------------------------------------------------------------- #

def test_a_stated_year_wins_when_the_record_sits_in_the_wrong_one():
    """389 research papers were 1 to 5 years out. The stated year is the only
    evidence there is, so it is applied — as 1 January, marked year precision."""
    published, source, precision = _published_at_for(
        CREATED, {"field_rpaper_year": "2016"})
    assert published == "2016-01-01T00:00:00+00:00"
    assert (source, precision) == ("cms_field", "year")


def test_a_stated_year_the_record_already_sits_in_changes_nothing():
    """The other 228. Their stamp is already inside the right year and carries a
    real day; 1 January would collapse every paper of that year onto one date
    and lose what ordering they had."""
    assert _published_at_for("2016-03-15T10:00:00+00:00",
                             {"field_rpaper_year": "2016"}) \
        == ("2016-03-15T10:00:00+00:00", "created", "day")


def test_an_unreadable_created_stamp_lets_the_stated_year_win():
    """The safe direction: keeping a stamp we could not verify over a statement
    we could would be the wrong way round."""
    published, source, _ = _published_at_for(None, {"field_rpaper_year": "2016"})
    assert published == "2016-01-01T00:00:00+00:00"
    assert source == "cms_field"


def test_a_year_precision_value_is_stored_as_january_first():
    """The marker the precision field refers to. Anything else would mean the
    value and its precision disagree about what is known."""
    published, _, precision = _published_at_for(CREATED, {"field_rpaper_year": "2016"})
    assert precision == "year"
    assert published.startswith("2016-01-01")


def test_one_function_governs_the_decision_for_ingestion_and_the_backfill():
    """The rule is conditional now, and two copies of a conditional rule drift —
    a re-ingested document would get a different date than the backfill gave
    it."""
    import inspect

    from app.ingestion import canonical
    from scripts import backfill_source_dates

    assert "resolve_published_at" in inspect.getsource(canonical._published_at_for)
    assert "resolve_published_at" in inspect.getsource(backfill_source_dates.candidates)


# --------------------------------------------------------------------------- #
# Through the real document builder
# --------------------------------------------------------------------------- #

def test_the_builder_carries_the_correction_and_its_provenance():
    doc = from_drupal_record(
        _Record({"field_pressrelease_date": "2012-04-17T18:30:00+00:00"}))
    assert doc.published_at == "2012-04-18T00:00:00+00:00"
    assert doc.published_at_source == "cms_field"
    assert doc.published_at_precision == "day"


def test_the_builder_leaves_an_unstated_record_exactly_as_before():
    doc = from_drupal_record(_Record({}))
    assert doc.published_at == CREATED
    assert doc.published_at_source == "created"


def test_the_correction_does_not_disturb_anything_else_on_the_document():
    """A date change must not quietly alter identity, content or facets — the
    content hash is what re-indexing keys on."""
    plain = from_drupal_record(_Record({}))
    corrected = from_drupal_record(
        _Record({"field_pressrelease_date": "2012-04-17T18:30:00+00:00"}))
    assert corrected.document_id == plain.document_id
    assert corrected.content_hash == plain.content_hash
    assert corrected.title == plain.title
    assert corrected.categories == plain.categories
    assert corrected.raw_meta != plain.raw_meta  # only because the input differed


def test_the_raw_metadata_is_still_carried_verbatim():
    """The source values have to survive, or the audit loses its evidence."""
    meta = {"field_pressrelease_date": "2012-04-17T18:30:00+00:00",
            "field_event_start_date": "2017-11-05T18:30:00+00:00"}
    doc = from_drupal_record(_Record(meta))
    assert doc.raw_meta["field_pressrelease_date"] == meta["field_pressrelease_date"]
    assert doc.raw_meta["field_event_start_date"] == meta["field_event_start_date"]


# --------------------------------------------------------------------------- #
# The PDF path records provenance too
# --------------------------------------------------------------------------- #

def test_a_pdf_keeping_its_page_date_records_that_source():
    import inspect

    from app.ingestion.extractors import attachment

    src = inspect.getsource(attachment.build_attachment_doc)
    assert 'published_at_source=("document_text" if resolved.overridden else "created")' in src


def test_an_override_is_the_only_thing_that_earns_document_text():
    """`overridden` is true only for a verified, quoted publication statement,
    which is exactly what the label claims."""
    from app.ingestion.date_resolution import ResolvedDate
    from app.ingestion.date_rules import DateDecision

    keep = ResolvedDate(published_at="2018-01-09T00:00:00+00:00",
                        decision=DateDecision(document_id="d", action="keep_page_date"))
    override = ResolvedDate(published_at="2013-12-23T00:00:00+00:00",
                            decision=DateDecision(document_id="d",
                                                  action="propose_override",
                                                  candidate_date="2013-12-23"))
    review = ResolvedDate(published_at="2018-01-09T00:00:00+00:00",
                          decision=DateDecision(document_id="d",
                                                action="needs_manual_review"))
    assert not keep.overridden
    assert override.overridden
    assert not review.overridden
