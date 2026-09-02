"""The bundle -> date-field mapping, and what happens when a field disappoints.

The mapping is the whole design: one table, and a resolution algorithm that
names no bundle. So the tests come in two halves — one case per bundle pinning
the table itself (a mapping edited by accident is a corpus silently re-dated),
and the fallback ladder, which is where every interesting failure lives.

Field shapes here are the ones the live JSON:API actually returns, sampled
2026-09-02: `field_rpaper_year` is an **int**, `field_report_date` carries a
`+05:30` offset and a real clock time, and everything else is IST midnight
expressed as `+00:00`.
"""

from __future__ import annotations

import pytest

from app.ingestion.bundle_dates import (
    BUNDLE_DATE_FIELDS,
    EffectiveDate,
    describe,
    field_for,
    inherited,
    resolve,
)

CREATED = "2018-01-11T06:29:59+00:00"

#: The supplied business mapping, verbatim. Written out rather than imported so
#: an edit to the source table has to be made twice, deliberately.
REQUIRED_MAPPING = {
    "article": "created",
    "page": "created",
    "research_papers": "field_rpaper_year",
    "completed_projects": "field_completed_start_date",
    "feature_articles": "created",
    "ongoing_projects": "field_ongoing_start_date",
    "news": "field_news_date",
    "events": "field_event_start_date",
    "press_release": "field_pressrelease_date",
    "policy_brief": "created",
    "videos": "created",
    "infographics": "created",
    "report": "field_report_date",
    "people": "created",
}


# --------------------------------------------------------------------------- #
# The mapping
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bundle,field", sorted(REQUIRED_MAPPING.items()))
def test_every_bundle_maps_to_its_required_field(bundle, field):
    assert field_for(bundle).field == field


def test_the_mapping_covers_every_bundle_the_crawl_attempts():
    """A crawled bundle nobody has classified is a bundle whose dates nobody has
    thought about. `services` is the case this catches: it is crawled, it is not
    in the supplied mapping, and it carries no date-like field at all."""
    from app.core.corpus import DEFAULT_BUNDLES

    missing = [b for b in DEFAULT_BUNDLES if b not in BUNDLE_DATE_FIELDS]
    assert missing == [], f"crawled bundles with no declared date field: {missing}"


def test_the_mapping_adds_nothing_the_crawl_does_not_fetch():
    from app.core.corpus import DEFAULT_BUNDLES

    extra = sorted(set(BUNDLE_DATE_FIELDS) - set(DEFAULT_BUNDLES))
    assert extra == []


def test_only_the_year_field_is_year_precision():
    """A year-precision value is stored as 1 January as a marker. Marking a
    full-date field that way would make every reader render 1 January."""
    year_fields = {b for b, f in BUNDLE_DATE_FIELDS.items() if f.precision == "year"}
    assert year_fields == {"research_papers"}


# --------------------------------------------------------------------------- #
# Resolution, one case per bundle
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bundle", sorted(
    b for b, f in REQUIRED_MAPPING.items() if f == "created"))
def test_a_created_bundle_resolves_to_its_creation_stamp(bundle):
    got = resolve(bundle, CREATED, {})
    assert (got.value, got.source, got.precision) == (CREATED, "created", "day")
    assert got.rule == "bundle_created"


@pytest.mark.parametrize("bundle,field,raw,expected", [
    ("research_papers", "field_rpaper_year", 2022, "2022-01-01T00:00:00+00:00"),
    ("completed_projects", "field_completed_start_date",
     "2004-06-28T18:30:00+00:00", "2004-06-29T00:00:00+00:00"),
    ("ongoing_projects", "field_ongoing_start_date",
     "2011-04-07T18:30:00+00:00", "2011-04-08T00:00:00+00:00"),
    ("news", "field_news_date",
     "2013-01-23T18:30:00+00:00", "2013-01-24T00:00:00+00:00"),
    ("events", "field_event_start_date",
     "2018-03-11T18:30:00+00:00", "2018-03-12T00:00:00+00:00"),
    ("press_release", "field_pressrelease_date",
     "2012-01-29T18:30:00+00:00", "2012-01-30T00:00:00+00:00"),
    ("report", "field_report_date",
     "2019-02-13T09:30:00+05:30", "2019-02-13T00:00:00+00:00"),
])
def test_a_field_bundle_resolves_to_its_configured_field(bundle, field, raw, expected):
    got = resolve(bundle, CREATED, {field: raw})
    assert got.value == expected
    assert (got.source, got.field, got.rule) == \
        ("cms_field", field, "bundle_date_field")
    assert got.raw_value == raw


def test_a_year_only_field_takes_an_int_as_readily_as_a_string():
    """Live records return `field_rpaper_year` as a JSON number."""
    assert resolve("research_papers", CREATED, {"field_rpaper_year": 2022}).value \
        == resolve("research_papers", CREATED, {"field_rpaper_year": "2022"}).value


def test_a_report_date_keeps_its_indian_calendar_day():
    """`+05:30` with a real clock time is the shape only `report` uses. A naive
    UTC read of `2018-03-06T00:00:00+05:30` would land on 5 March."""
    assert resolve("report", CREATED,
                   {"field_report_date": "2018-03-06T00:00:00+05:30"}).value \
        == "2018-03-06T00:00:00+00:00"


def test_the_field_classification_travels_with_the_decision():
    """A project start applied as a document's date is still a project start.
    Erasing that would leave an auditor unable to tell the two cases apart."""
    assert resolve("news", CREATED,
                   {"field_news_date": "2013-01-23T18:30:00+00:00"}).kind \
        == "publication"
    assert resolve("completed_projects", CREATED,
                   {"field_completed_start_date": "2004-06-28T18:30:00+00:00"}).kind \
        == "period"
    assert resolve("events", CREATED,
                   {"field_event_start_date": "2018-03-11T18:30:00+00:00"}).kind \
        == "event"


# --------------------------------------------------------------------------- #
# The fallback ladder
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw", [None, "", [], {}])
def test_an_empty_field_falls_back_to_the_creation_stamp(raw):
    got = resolve("news", CREATED, {"field_news_date": raw})
    assert (got.value, got.source, got.rule) == (CREATED, "created", "field_empty")
    assert got.field == "field_news_date", "the field consulted is still named"


def test_a_field_absent_from_the_record_falls_back_the_same_way():
    got = resolve("report", CREATED, {})
    assert (got.value, got.rule) == (CREATED, "field_empty")


@pytest.mark.parametrize("raw", [
    "not a date", "1970-01-01T00:00:00+00:00", "0001-01-01T00:00:00+00:00",
    "31/12/2019", True,
])
def test_an_unusable_value_falls_back_to_the_creation_stamp(raw):
    """Includes the two plausibility bounds: a zero timestamp read as a date
    lands in 1970, and a parse accident can land centuries away. Both are
    rejected here rather than downstream, because a date that is merely *stored*
    is already acting on ranking."""
    got = resolve("news", CREATED, {"field_news_date": raw})
    assert (got.value, got.source, got.rule) == (CREATED, "created", "field_invalid")
    assert got.raw_value == raw, "the offending value is kept for the audit row"


def test_a_bare_year_in_a_full_date_field_is_kept_at_year_precision():
    """`to_ist_date` reads "2021" as 1 January, which is the right value and the
    wrong precision. Storing it as a day would claim a day the source never gave
    — so the value stands and the precision is downgraded to what it supports.
    One `field_rpaper_publisher` value on this site is literally "2021", which is
    how bad CMS data of exactly this shape is known to exist."""
    got = resolve("news", CREATED, {"field_news_date": "2021"})
    assert got.value == "2021-01-01T00:00:00+00:00"
    assert got.precision == "year"
    assert got.rule == "bundle_date_field_year_only"
    assert got.from_bundle_field, "it is still the bundle's own field"


def test_a_far_future_date_is_not_usable():
    got = resolve("events", CREATED, {"field_event_start_date": "2099-01-01"})
    assert got.rule == "field_invalid"


def test_a_year_only_field_out_of_range_is_not_usable():
    assert resolve("research_papers", CREATED,
                   {"field_rpaper_year": 1899}).rule == "field_invalid"


def test_a_multi_value_field_uses_its_first_value():
    """No mapped field is multi-valued on this site, but Drupal permits it and a
    list must not silently stringify into an unparseable value."""
    got = resolve("news", CREATED, {"field_news_date": [
        "2013-01-23T18:30:00+00:00", "2014-01-23T18:30:00+00:00"]})
    assert got.value == "2013-01-24T00:00:00+00:00"
    assert got.rule == "bundle_date_field"


def test_an_unmapped_bundle_keeps_the_creation_stamp():
    """The safe direction, and exactly the historical behaviour: a CMS that grows
    a new content type cannot silently start moving dates."""
    got = resolve("brand_new_bundle", CREATED,
                  {"field_brand_new_date": "2001-01-01T00:00:00+00:00"})
    assert (got.value, got.source, got.rule) == \
        (CREATED, "created", "bundle_unmapped")


def test_no_bundle_at_all_keeps_the_creation_stamp():
    got = resolve(None, CREATED, {"field_news_date": "2013-01-23T18:30:00+00:00"})
    assert (got.value, got.source, got.rule) == (CREATED, "created", "no_bundle")


def test_a_record_with_neither_a_field_value_nor_a_stamp_is_undated():
    """Nothing is invented. The pipeline flags and counts this; a fabricated date
    would be worse than none."""
    got = resolve("news", None, {})
    assert got.value is None
    assert got.rule == "no_date"


def test_no_metadata_at_all_is_not_an_error():
    assert resolve("news", CREATED, None).value == CREATED


def test_a_creation_stamp_is_passed_through_verbatim():
    """Not re-normalised to midnight: the intra-day clock reading is the only
    thing separating the hundreds of records that share one import date."""
    stamp = "2017-12-28T08:23:05+00:00"
    assert resolve("article", stamp, {}).value == stamp


# --------------------------------------------------------------------------- #
# Inheritance
# --------------------------------------------------------------------------- #

def test_inheriting_carries_the_value_the_precision_and_the_evidence():
    parent = resolve("research_papers", CREATED, {"field_rpaper_year": 2022})
    child = inherited(parent)
    assert child.value == parent.value
    assert child.precision == "year", "a file on a paper is year-precision too"
    assert child.field == "field_rpaper_year"
    assert child.raw_value == 2022
    assert child.bundle == "research_papers"
    assert (child.source, child.rule) == ("parent_page", "inherited_from_parent")


def test_inheriting_is_pure():
    """Every PDF on a page is handed the same parent resolution; one of them
    mutating it would re-date the rest."""
    parent = resolve("news", CREATED, {"field_news_date": "2013-01-23T18:30:00+00:00"})
    before = parent.value
    for _ in range(3):
        inherited(parent)
    assert parent.value == before


def test_from_bundle_field_is_true_only_for_a_value_the_field_supplied():
    supplied = resolve("news", CREATED, {"field_news_date": "2013-01-23T18:30:00+00:00"})
    empty = resolve("news", CREATED, {})
    stamp = resolve("article", CREATED, {})
    assert supplied.from_bundle_field
    assert not empty.from_bundle_field
    assert not stamp.from_bundle_field


# --------------------------------------------------------------------------- #
# Provenance prose
# --------------------------------------------------------------------------- #

def test_the_evidence_sentence_names_bundle_field_and_value():
    """"Why does this document have the date 2022?" has to be answerable from
    the stored row alone."""
    got = describe(resolve("research_papers", CREATED, {"field_rpaper_year": 2022}),
                   title="A paper", url="https://teriin.org/p")
    assert "research_papers" in got
    assert "field_rpaper_year" in got
    assert "2022" in got


def test_an_attachments_sentence_names_the_page_it_came_from():
    parent = resolve("research_papers", CREATED, {"field_rpaper_year": 2022})
    got = describe(parent, title="A paper",
                   url="https://teriin.org/p", for_attachment=True)
    assert got.startswith("Inherited from")
    assert "A paper" in got and "https://teriin.org/p" in got
    assert "field_rpaper_year" in got and "2022" in got


def test_a_non_publication_field_says_so_in_the_evidence():
    """The one place the semantic change is visible to a reader of the audit
    trail: this date is what the content is about, not a stated publication."""
    got = describe(resolve("completed_projects", CREATED,
                           {"field_completed_start_date": "2004-06-28T18:30:00+00:00"}))
    assert "period" in got


@pytest.mark.parametrize("rule,metadata,bundle", [
    ("field_empty", {}, "news"),
    ("field_invalid", {"field_news_date": "nonsense"}, "news"),
    ("bundle_created", {}, "article"),
    ("bundle_unmapped", {}, "unknown_bundle"),
])
def test_every_fallback_rung_produces_a_readable_sentence(rule, metadata, bundle):
    resolved = resolve(bundle, CREATED, metadata)
    assert resolved.rule == rule
    sentence = describe(resolved)
    assert sentence.endswith(".") and len(sentence) > 20


def test_an_undated_record_says_why_it_is_undated():
    assert "undated" in describe(resolve("news", None, {}))


# --------------------------------------------------------------------------- #
# Shape
# --------------------------------------------------------------------------- #

def test_the_result_is_immutable():
    """It is passed to the document, to the audit row and to every attachment on
    the page; a mutable one would let any of them re-date the others."""
    got = resolve("article", CREATED, {})
    with pytest.raises(Exception):
        got.value = "2020-01-01T00:00:00+00:00"


def test_the_source_vocabulary_fits_the_column_that_stores_it():
    """`documents.published_at_source` is VARCHAR(16)."""
    for source in ("created", "cms_field", "parent_page", "document_text"):
        assert len(source) <= 16


def test_every_rule_fits_the_column_that_stores_it():
    """`{state}_date_decision.rule` is VARCHAR(48)."""
    rules = {"bundle_date_field", "bundle_created", "field_empty", "field_invalid",
             "bundle_unmapped", "no_bundle", "no_date", "inherited_from_parent",
             "parent_bundle_date_field", "bundle_field_empty",
             "bundle_field_invalid", "bundle_field_matches_created"}
    assert all(len(rule) <= 48 for rule in rules)


def test_every_configured_field_name_fits_the_candidate_source_column():
    """`{state}_date_decision.candidate_source` is VARCHAR(32)."""
    assert all(len(f.field) <= 32 for f in BUNDLE_DATE_FIELDS.values())


def test_an_effective_date_can_be_built_directly_for_a_caller_that_knows():
    """The dataclass is part of the contract: the backfill and the attachment
    path both construct and pass one around."""
    got = EffectiveDate(value=CREATED, source="created", precision="day",
                        rule="bundle_created", bundle="article")
    assert not got.from_bundle_field
