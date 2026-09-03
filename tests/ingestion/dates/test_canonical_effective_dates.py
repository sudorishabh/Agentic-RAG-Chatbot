"""Where a document's ``effective_start_date`` comes from when it is built.

The date a Drupal record carries is a property of its **bundle**: ``news`` takes
``field_news_date``, ``completed_projects`` takes the project's start,
``article`` takes its creation stamp. :mod:`app.ingestion.bundle_dates` declares
that mapping; these tests exercise it through the real document builder, which is
where a wiring mistake would actually show up.

The mapping itself and its edge cases are covered by ``test_bundle_dates.py``.
What is here is what the *builder* must do with the result: apply the value, its
precision and its provenance, carry the evidence for the audit row, and disturb
nothing else on the document.
"""

from __future__ import annotations

import pytest

from app.ingestion.canonical import _effective_dates_for, from_drupal_record

CREATED = "2018-01-11T06:29:59+00:00"


class _Record:
    """The shape `from_drupal_record` reads. Deliberately not a mock — the point
    is that the real builder is exercised."""

    def __init__(self, metadata: dict, created: str | None = CREATED,
                 bundle: str = "press_release"):
        self.body = "some body text"
        self.title = "A document"
        self.url = "https://teriin.org/press-release/x"
        self.uuid = "uuid-1"
        self.bundle = bundle
        self.nid = 7
        self.created = created
        self.changed = created
        self.metadata = metadata
        self.refs = []
        self.pdf_url = None


def _resolve(bundle, created, metadata):
    """`(value, source, precision)` — the three fields the builder applies."""
    got = _effective_dates_for(bundle, created, metadata)
    return got.start_value, got.source, got.start_precision


# --------------------------------------------------------------------------- #
# Bundles that take the record's own creation stamp
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bundle", [
    "article", "page", "feature_articles", "policy_brief",
    "videos", "infographics", "people", "services",
])
def test_a_created_bundle_keeps_its_creation_stamp(bundle):
    assert _resolve(bundle, CREATED, {}) == (CREATED, "created", "day")


def test_a_created_bundle_ignores_date_fields_it_is_not_mapped_to():
    """`article` maps to `created`, so a stray date field on the record cannot
    move it. The mapping decides, not what happens to be present."""
    assert _resolve("article", CREATED,
                    {"field_news_date": "2015-08-26T18:30:00+00:00"}) \
        == (CREATED, "created", "day")


def test_a_missing_created_stamp_stays_missing():
    """No invention: a source with no date and no mapped field has no date."""
    assert _resolve("article", None, {}) == (None, "created", "day")


# --------------------------------------------------------------------------- #
# Bundles that take a configured CMS field
# --------------------------------------------------------------------------- #

def test_a_news_date_becomes_the_effective_date():
    assert _resolve("news", CREATED, {"field_news_date": "2015-08-26T18:30:00+00:00"}) \
        == ("2015-08-27T00:00:00+00:00", "cms_field", "day")


def test_the_stored_string_is_utc_midnight_on_the_indian_calendar_day():
    """The whole off-by-one class. ``state._to_datetime`` normalises to naive
    UTC, so an IST-midnight string would land a day early in the column and
    every consumer would read the wrong calendar date."""
    published, _, _ = _resolve(
        "press_release", CREATED,
        {"field_pressrelease_date": "2012-04-17T18:30:00+00:00"})
    assert published == "2012-04-18T00:00:00+00:00"
    assert not published.endswith("+05:30")


def test_the_two_live_verified_cases_resolve_to_the_displayed_date():
    """Checked against the rendered pages: the site shows 18 April 2012 and
    4 November 2015."""
    for value, expected in (("2012-04-17T18:30:00+00:00", "2012-04-18"),
                            ("2015-11-03T18:30:00+00:00", "2015-11-04")):
        published, _, _ = _resolve("press_release", CREATED,
                                   {"field_pressrelease_date": value})
        assert published.startswith(expected)


def test_only_the_bundles_own_field_is_read():
    """A record carrying several date fields uses the one its bundle names, and
    is not swayed by the others being present."""
    published, source, _ = _resolve("events", CREATED, {
        "field_completed_start_date": "2004-06-28T18:30:00+00:00",
        "field_news_date": "2015-08-26T18:30:00+00:00",
        "field_event_start_date": "2017-11-05T18:30:00+00:00",
    })
    assert published.startswith("2017-11-06")
    assert source == "cms_field"


# --------------------------------------------------------------------------- #
# A year-only source
# --------------------------------------------------------------------------- #

def test_a_stated_year_is_applied_and_marked_year_precision():
    """Stored as 1 January *as a marker*. `start_precision` is what keeps
    it from being read as a January publication, and it reaches the payload."""
    assert _resolve("research_papers", CREATED, {"field_rpaper_year": 2016}) \
        == ("2016-01-01T00:00:00+00:00", "cms_field", "year")


def test_a_stated_year_wins_even_when_the_record_sits_in_that_year():
    """A change from the field-keyed design, which declined this case to keep the
    real day the stamp carried. The bundle mapping is unconditional: the field is
    what this content type is dated by, so it applies whatever `created` says.
    The cost — intra-year ordering for the ~228 papers already in the right year
    — is recorded in the plan's risk list."""
    assert _resolve("research_papers", "2016-03-15T10:00:00+00:00",
                    {"field_rpaper_year": 2016}) \
        == ("2016-01-01T00:00:00+00:00", "cms_field", "year")


# --------------------------------------------------------------------------- #
# One function governs every path
# --------------------------------------------------------------------------- #

def test_one_function_governs_the_decision_for_ingestion_and_the_backfill():
    """Two copies of this rule would drift, and a re-ingested document would then
    get a different date than the backfill gave it."""
    import inspect

    from app.ingestion import canonical
    from app.ingestion.extractors import attachment
    from scripts import backfill_bundle_dates

    assert "bundle_dates" in inspect.getsource(canonical._effective_dates_for)
    assert "bundle_dates" in inspect.getsource(attachment.resolve_parent_date)
    assert backfill_bundle_dates.resolve_effective_dates.__module__ == "app.ingestion.bundle_dates"
    assert "resolve_effective_dates(" in inspect.getsource(backfill_bundle_dates.page_moves), \
        "the backfill must call the shared resolver, not re-implement the rule"


# --------------------------------------------------------------------------- #
# Through the real document builder
# --------------------------------------------------------------------------- #

def test_the_builder_carries_the_value_and_its_provenance():
    doc = from_drupal_record(
        _Record({"field_pressrelease_date": "2012-04-17T18:30:00+00:00"}))
    assert doc.effective_start_date == "2012-04-18T00:00:00+00:00"
    assert doc.date_source == "cms_field"
    assert doc.start_precision == "day"


def test_the_builder_leaves_a_created_bundle_exactly_as_before():
    doc = from_drupal_record(_Record({}, bundle="article"))
    assert doc.effective_start_date == CREATED
    assert doc.date_source == "created"


def test_the_builder_carries_the_evidence_for_the_audit_row():
    """The pipeline writes the decision row from this rather than re-reading the
    metadata, so a row cannot disagree with the value on the document."""
    doc = from_drupal_record(
        _Record({"field_pressrelease_date": "2012-04-17T18:30:00+00:00"}))
    assert doc.date_evidence.start_field == "field_pressrelease_date"
    assert doc.date_evidence.start_raw == "2012-04-17T18:30:00+00:00"
    assert doc.date_evidence.bundle == "press_release"
    assert doc.date_evidence.rule == "bundle_date_field"


def test_the_evidence_never_reaches_a_chunk_payload():
    """`build_payload` does `payload.update(m.extra)`, so provenance parked in
    `extra` would be replicated into every point in the collection."""
    doc = from_drupal_record(
        _Record({"field_pressrelease_date": "2012-04-17T18:30:00+00:00"}))
    assert "date_evidence" not in doc.extra
    assert not any(k.startswith("date_") for k in doc.extra)


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
    assert 'date_source=("document_text" if resolved.overridden' in src
    assert 'else "parent_page")' in src


def test_an_override_is_the_only_thing_that_earns_document_text():
    """`overridden` is true only for a verified, quoted publication statement,
    which is exactly what the label claims."""
    from app.ingestion.date_resolution import ResolvedDate
    from app.ingestion.date_rules import DateDecision

    keep = ResolvedDate(start_value="2018-01-09T00:00:00+00:00",
                        decision=DateDecision(document_id="d", action="keep_page_date"))
    override = ResolvedDate(start_value="2013-12-23T00:00:00+00:00",
                            decision=DateDecision(document_id="d",
                                                  action="propose_override",
                                                  candidate_start_date="2013-12-23"))
    review = ResolvedDate(start_value="2018-01-09T00:00:00+00:00",
                          decision=DateDecision(document_id="d",
                                                action="needs_manual_review"))
    assert not keep.overridden
    assert override.overridden
    assert not review.overridden
