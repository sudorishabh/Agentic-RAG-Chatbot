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
    end_field_for,
    fields_for,
    inherited,
    precision_of,
    resolve_effective_dates,
)

CREATED = "2018-01-11T06:29:59+00:00"

#: The supplied business mapping, verbatim. Written out rather than imported so
#: an edit to the source table has to be made twice, deliberately.
#:
#: `ongoing_projects` is single-field: `field_ongoing_end_date` was in the
#: supplied mapping, does not exist in Drupal (a filter on it is rejected with
#: "the field does not exist" and the attribute is absent from all 595 published
#: records), and was confirmed with the requester as a mistake.
REQUIRED_MAPPING = {
    "article": ["created"],
    "page": ["created"],
    "research_papers": ["field_rpaper_year"],
    "completed_projects": ["field_completed_start_date",
                           "field_completed_end_date"],
    "feature_articles": ["created"],
    "ongoing_projects": ["field_ongoing_start_date"],
    "news": ["field_news_date"],
    "events": ["field_event_start_date", "field_event_end_date"],
    "press_release": ["field_pressrelease_date"],
    "policy_brief": ["created"],
    "videos": ["created"],
    "infographics": ["created"],
    "report": ["field_report_date"],
    "people": ["created"],
}

#: The bundles whose content covers a period.
RANGE_BUNDLES = {"completed_projects", "events"}


# --------------------------------------------------------------------------- #
# The mapping
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bundle,expected", sorted(REQUIRED_MAPPING.items()))
def test_every_bundle_maps_to_its_required_fields(bundle, expected):
    assert list(fields_for(bundle)) == expected


@pytest.mark.parametrize("bundle", sorted(RANGE_BUNDLES))
def test_a_range_bundle_names_its_start_first_and_its_end_second(bundle):
    """Order is the whole contract: [start, end]. Reversing it would silently
    date every project by its finish."""
    start, end = fields_for(bundle)
    assert "start" in start and "end" in end


@pytest.mark.parametrize("bundle,expected", [
    ("completed_projects", "field_completed_end_date"),
    ("events", "field_event_end_date"),
    ("ongoing_projects", None),
    ("news", None),
    ("article", None),
    ("brand_new_bundle", None),
])
def test_the_end_field_is_answerable_from_the_mapping_alone(bundle, expected):
    """Without resolving a record: the reconciliation checks and the backfill's
    reporting both need to know which bundles carry a period."""
    assert end_field_for(bundle) == expected


def test_ongoing_projects_has_no_end_field():
    """Drupal does not have one — verified against the live API — and an
    *ongoing* project has not ended, so this is also the right answer."""
    assert fields_for("ongoing_projects") == ("field_ongoing_start_date",)


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
    year_fields = {f for fields in BUNDLE_DATE_FIELDS.values() for f in fields
                   if precision_of(f) == "year"}
    assert year_fields == {"field_rpaper_year"}


def test_precision_is_declared_once_and_read_from_the_field():
    """Precision is a property of the field, not of the bundle that points at
    it. Restating it per bundle would be two facts that can disagree."""
    from app.ingestion.source_dates import FIELD_ROLES

    for fields in BUNDLE_DATE_FIELDS.values():
        for field in fields:
            if field == "created":
                continue
            assert precision_of(field) == FIELD_ROLES[field][1]


# --------------------------------------------------------------------------- #
# Resolution, one case per bundle
# --------------------------------------------------------------------------- #

#: Bundles whose only configured field is the creation stamp.
CREATED_BUNDLES = sorted(
    b for b, fields in REQUIRED_MAPPING.items() if fields == ["created"])


def test_the_created_bundle_list_is_not_empty():
    """The list is derived from the mapping, and a mapping whose shape
    changed once already turned this into an empty parameter set that
    silently stopped testing anything."""
    assert len(CREATED_BUNDLES) == 7


@pytest.mark.parametrize("bundle", CREATED_BUNDLES)
def test_a_created_bundle_resolves_to_its_creation_stamp(bundle):
    got = resolve_effective_dates(bundle, CREATED, {})
    assert (got.start_value, got.source, got.start_precision) == (CREATED, "created", "day")
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
    got = resolve_effective_dates(bundle, CREATED, {field: raw})
    assert got.start_value == expected
    assert (got.source, got.start_field, got.rule) == \
        ("cms_field", field, "bundle_date_field")
    assert got.start_raw == raw


def test_a_year_only_field_takes_an_int_as_readily_as_a_string():
    """Live records return `field_rpaper_year` as a JSON number."""
    assert resolve_effective_dates("research_papers", CREATED, {"field_rpaper_year": 2022}).start_value \
        == resolve_effective_dates("research_papers", CREATED, {"field_rpaper_year": "2022"}).start_value


def test_a_report_date_keeps_its_indian_calendar_day():
    """`+05:30` with a real clock time is the shape only `report` uses. A naive
    UTC read of `2018-03-06T00:00:00+05:30` would land on 5 March."""
    assert resolve_effective_dates("report", CREATED,
                   {"field_report_date": "2018-03-06T00:00:00+05:30"}).start_value \
        == "2018-03-06T00:00:00+00:00"


def test_the_field_role_travels_with_the_decision():
    """A project start applied as a document's date came out of a `range_start`
    field, and stays visibly that. Erasing the role would leave an auditor unable
    to tell "the CMS states this date" from "this is when the work began"."""
    assert resolve_effective_dates(
        "news", CREATED,
        {"field_news_date": "2013-01-23T18:30:00+00:00"}).field_role == "date"
    assert resolve_effective_dates(
        "completed_projects", CREATED,
        {"field_completed_start_date": "2004-06-28T18:30:00+00:00"}
    ).field_role == "range_start"
    assert resolve_effective_dates(
        "events", CREATED,
        {"field_event_start_date": "2018-03-11T18:30:00+00:00"}
    ).field_role == "range_start"

# --------------------------------------------------------------------------- #
# The fallback ladder
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw", [None, "", [], {}])
def test_an_empty_field_falls_back_to_the_creation_stamp(raw):
    got = resolve_effective_dates("news", CREATED, {"field_news_date": raw})
    assert (got.start_value, got.source, got.rule) == (CREATED, "created", "field_empty")
    assert got.start_field == "field_news_date", "the field consulted is named"


def test_a_field_absent_from_the_record_falls_back_the_same_way():
    got = resolve_effective_dates("report", CREATED, {})
    assert (got.start_value, got.rule) == (CREATED, "field_empty")


@pytest.mark.parametrize("raw", [
    "not a date", "1970-01-01T00:00:00+00:00", "0001-01-01T00:00:00+00:00",
    "31/12/2019", True,
])
def test_an_unusable_value_falls_back_to_the_creation_stamp(raw):
    """Includes the two plausibility bounds: a zero timestamp read as a date
    lands in 1970, and a parse accident can land centuries away. Both are
    rejected here rather than downstream, because a date that is merely *stored*
    is already acting on ranking."""
    got = resolve_effective_dates("news", CREATED, {"field_news_date": raw})
    assert (got.start_value, got.source, got.rule) == (CREATED, "created", "field_invalid")
    assert got.start_raw == raw, "the offending value is kept for the audit row"


def test_a_bare_year_in_a_full_date_field_is_kept_at_year_precision():
    """`to_ist_date` reads "2021" as 1 January, which is the right value and the
    wrong precision. Storing it as a day would claim a day the source never gave
    — so the value stands and the precision is downgraded to what it supports.
    One `field_rpaper_publisher` value on this site is literally "2021", which is
    how bad CMS data of exactly this shape is known to exist."""
    got = resolve_effective_dates("news", CREATED, {"field_news_date": "2021"})
    assert got.start_value == "2021-01-01T00:00:00+00:00"
    assert got.start_precision == "year"
    assert got.rule == "bundle_date_field_year_only"
    assert got.from_bundle_field, "it is still the bundle's own field"


def test_a_far_future_date_is_not_usable():
    got = resolve_effective_dates("events", CREATED, {"field_event_start_date": "2099-01-01"})
    assert got.rule == "field_invalid"


def test_a_year_only_field_out_of_range_is_not_usable():
    assert resolve_effective_dates("research_papers", CREATED,
                   {"field_rpaper_year": 1899}).rule == "field_invalid"


def test_a_multi_value_field_uses_its_first_value():
    """No mapped field is multi-valued on this site, but Drupal permits it and a
    list must not silently stringify into an unparseable value."""
    got = resolve_effective_dates("news", CREATED, {"field_news_date": [
        "2013-01-23T18:30:00+00:00", "2014-01-23T18:30:00+00:00"]})
    assert got.start_value == "2013-01-24T00:00:00+00:00"
    assert got.rule == "bundle_date_field"


def test_an_unmapped_bundle_keeps_the_creation_stamp():
    """The safe direction, and exactly the historical behaviour: a CMS that grows
    a new content type cannot silently start moving dates."""
    got = resolve_effective_dates("brand_new_bundle", CREATED,
                  {"field_brand_new_date": "2001-01-01T00:00:00+00:00"})
    assert (got.start_value, got.source, got.rule) == \
        (CREATED, "created", "bundle_unmapped")


def test_no_bundle_at_all_keeps_the_creation_stamp():
    got = resolve_effective_dates(None, CREATED, {"field_news_date": "2013-01-23T18:30:00+00:00"})
    assert (got.start_value, got.source, got.rule) == (CREATED, "created", "no_bundle")


def test_a_record_with_neither_a_field_value_nor_a_stamp_is_undated():
    """Nothing is invented. The pipeline flags and counts this; a fabricated date
    would be worse than none."""
    got = resolve_effective_dates("news", None, {})
    assert got.start_value is None
    assert got.rule == "no_date"


def test_no_metadata_at_all_is_not_an_error():
    assert resolve_effective_dates("news", CREATED, None).start_value == CREATED


def test_a_creation_stamp_is_passed_through_verbatim():
    """Not re-normalised to midnight: the intra-day clock reading is the only
    thing separating the hundreds of records that share one import date."""
    stamp = "2017-12-28T08:23:05+00:00"
    assert resolve_effective_dates("article", stamp, {}).start_value == stamp


# --------------------------------------------------------------------------- #
# Date ranges
#
# Field shapes are the live ones: IST-midnight encoded `+00:00` strings, so a
# raw 2020-01-01T18:30 resolves to the 2nd. Measured on the full published
# corpus: completed_projects is 1,148 ordered / 11 same-day / 2 inverted, and
# events is 308 ordered / 784 same-day / 2 inverted.
# --------------------------------------------------------------------------- #

START_RAW = "2020-01-01T18:30:00+00:00"
END_RAW = "2022-12-30T18:30:00+00:00"
START = "2020-01-02T00:00:00+00:00"
END = "2022-12-31T00:00:00+00:00"


def _project(start=START_RAW, end=END_RAW):
    metadata = {}
    if start is not None:
        metadata["field_completed_start_date"] = start
    if end is not None:
        metadata["field_completed_end_date"] = end
    return resolve_effective_dates("completed_projects", CREATED, metadata)


def test_a_range_bundle_resolves_both_ends():
    got = _project()
    assert (got.start_value, got.end_value) == (START, END)
    assert (got.start_precision, got.end_precision) == ("day", "day")
    assert got.has_range
    assert got.range_issue is None


def test_both_fields_and_both_raw_values_are_kept_in_order():
    """`fields` and `raw_values` are parallel and configured-order, so a bundle
    that one day carries a third date needs no new attributes."""
    got = _project()
    assert got.fields == ("field_completed_start_date", "field_completed_end_date")
    assert got.raw_values == (START_RAW, END_RAW)
    assert got.start_field == "field_completed_start_date"
    assert got.end_field == "field_completed_end_date"
    assert got.start_raw == START_RAW
    assert got.end_raw == END_RAW


def test_an_event_resolves_its_own_pair():
    got = resolve_effective_dates("events", CREATED, {
        "field_event_start_date": "2018-03-11T18:30:00+00:00",
        "field_event_end_date": "2018-03-28T18:30:00+00:00"})
    assert (got.start_value, got.end_value) == ("2018-03-12T00:00:00+00:00",
                                          "2018-03-29T00:00:00+00:00")


def test_a_one_day_event_is_a_valid_range_not_a_defect():
    """784 of 1,094 published events have start == end. `start <= end`, not
    `start < end`."""
    same = "2025-03-05T04:30:00+00:00"
    got = resolve_effective_dates("events", CREATED,
                  {"field_event_start_date": same, "field_event_end_date": same})
    assert got.start_value == got.end_value
    assert got.range_issue is None
    assert got.has_range


def test_a_range_is_compared_after_normalisation_not_by_raw_value():
    """The finding that shaped this: by raw string 13 events look inverted, and
    after `to_ist_date` only 2 are — the rest differ solely in the time
    component and land on the same Indian calendar day."""
    got = resolve_effective_dates("events", CREATED, {
        "field_event_start_date": "2025-03-05T10:00:00+00:00",
        "field_event_end_date": "2025-03-05T04:30:00+00:00"})
    assert got.range_issue is None, "same calendar day, not an inversion"
    assert got.start_value == got.end_value


@pytest.mark.parametrize("bundle", sorted(set(REQUIRED_MAPPING) - RANGE_BUNDLES))
def test_a_single_date_bundle_never_produces_an_end(bundle):
    """An end date is never manufactured. A bundle with one field has one date."""
    metadata = {f: "2019-06-01T18:30:00+00:00" for f in fields_for(bundle)
                if f != "created"}
    got = resolve_effective_dates(bundle, CREATED, metadata)
    assert got.end_value is None
    assert got.end_precision is None
    assert not got.has_range
    assert not got.end_missing, "no end field is declared, so none is missing"


# ---- the ladder, one rung at a time ---------------------------------------- #

@pytest.mark.parametrize("end", [None, "", [], {}])
def test_a_start_without_an_end_is_a_valid_partial_range(end):
    """3 completed projects. A project with a start and no recorded finish is
    not an error."""
    got = _project(end=end)
    assert got.start_value == START
    assert got.end_value is None
    assert got.range_issue is None
    assert got.end_missing, "the bundle declares an end field and it gave nothing"
    assert got.end_field == "field_completed_end_date", "still named for the audit"


def test_an_unusable_end_is_dropped_and_flagged():
    """3 completed projects hold `1970-01-01`, the zero timestamp."""
    got = _project(end="1970-01-01T00:00:00+00:00")
    assert got.start_value == START, "the start is unaffected"
    assert got.end_value is None
    assert got.range_issue == "end_invalid"
    assert got.end_raw == "1970-01-01T00:00:00+00:00", "kept for debugging"


def test_a_non_date_end_is_dropped_and_flagged():
    got = _project(end="whenever")
    assert got.range_issue == "end_invalid"
    assert got.end_value is None


def test_an_inverted_range_is_never_swapped():
    """2 completed projects and 2 events. Guessing which of the two dates is
    wrong would bury a real CMS defect."""
    got = _project(start=END_RAW, end=START_RAW)
    assert got.start_value == END, "the start field still supplies the start"
    assert got.end_value is None
    assert got.range_issue == "inverted"
    assert got.raw_values == (END_RAW, START_RAW), "both raws kept for debugging"


def test_an_end_without_a_usable_start_keeps_the_end_and_says_so():
    """4 completed projects. The end is the only thing the source stated, so it
    is preserved; the start falls back and the range is marked incomplete."""
    got = _project(start=None)
    assert got.start_value == CREATED, "the start falls back to the creation stamp"
    assert got.source == "created"
    assert got.end_value == END, "the end is preserved, not discarded"
    assert got.range_issue == "end_without_start"


def test_an_end_before_the_fallback_start_is_not_stored():
    """The fallback start is the record's *creation* stamp — usually 2017 on this
    corpus, while the project it describes ended in 2000. Storing both would put
    a backwards range in the column, which `reconcile.inverted_date_range` would
    then report as "something else wrote this". The review row and the raw value
    still carry the end, so a reviewer loses nothing."""
    got = _project(start=None, end="1999-11-24T18:30:00+00:00")
    assert got.start_value == CREATED, "the start still falls back"
    assert got.end_value is None, "a backwards range is never stored"
    assert got.range_issue == "end_without_start", "and it still reaches review"
    assert got.end_raw == "1999-11-24T18:30:00+00:00", "kept for the reviewer"


def test_an_end_after_the_fallback_start_is_still_preserved():
    """The rule is "only where the stored range reads forwards", not "never"."""
    got = _project(start=None, end="2024-06-30T18:30:00+00:00")
    assert got.end_value.startswith("2024-07-01")
    assert got.range_issue == "end_without_start"


def test_an_end_before_the_fallback_start_is_not_called_inverted():
    """The two defects stay distinct even though both end with no end stored.

    `inverted` means the source stated two dates that contradict each other —
    a real CMS defect someone has to fix. `end_without_start` means the source
    stated only an end, and the start we fell back to happens to be the
    record's creation stamp. A creation stamp is not a range endpoint, so
    calling the second one "inverted" would blame the CMS for something it never
    asserted — and every completed project's end predates its 2017 import stamp,
    so it would blame it about a thousand times."""
    got = _project(start=None, end="2005-01-01T18:30:00+00:00")
    assert got.start_value == CREATED
    assert got.range_issue == "end_without_start", "not 'inverted'"
    assert got.end_value is None, "still not stored — see the test above"

    inverted = _project(start=END_RAW, end=START_RAW)
    assert inverted.range_issue == "inverted"
    assert inverted.start_value == END, "the start field still supplies the start"


def test_both_fields_missing_falls_back_exactly_as_a_single_date_bundle_would():
    got = _project(start=None, end=None)
    assert (got.start_value, got.source, got.rule) == (CREATED, "created", "field_empty")
    assert got.end_value is None
    assert got.range_issue is None, "nothing was stated, so nothing is wrong"


def test_an_invalid_start_with_no_end_is_the_plain_fallback():
    got = _project(start="nonsense", end=None)
    assert (got.start_value, got.rule) == (CREATED, "field_invalid")
    assert got.range_issue is None


def test_a_year_only_end_keeps_its_own_precision():
    """Mixed precision: the start states a day and the end states only a year.
    Each end carries the precision its own value supports."""
    got = _project(end="2022")
    assert got.start_precision == "day"
    assert got.end_precision == "year"
    assert got.end_value == "2022-01-01T00:00:00+00:00"


def test_a_multi_value_end_uses_its_first_value():
    got = _project(end=[END_RAW, "2024-01-01T18:30:00+00:00"])
    assert got.end_value == END


def test_a_range_is_recorded_as_the_role_its_start_field_has():
    assert _project().field_role == "range_start"


# ---- the range survives every hop ------------------------------------------ #

def test_a_range_is_carried_through_inheritance():
    child = inherited(_project())
    assert (child.start_value, child.end_value) == (START, END)
    assert (child.start_precision, child.end_precision) == ("day", "day")
    assert child.fields == ("field_completed_start_date",
                            "field_completed_end_date")
    assert child.source == "parent_page"


def test_an_inherited_range_carries_its_issue_too():
    """A file must not look cleaner than the page it hangs on."""
    child = inherited(_project(start=END_RAW, end=START_RAW))
    assert child.range_issue == "inverted"
    assert child.end_value is None


def test_the_evidence_names_the_end_field_and_its_value_separately():
    got = describe(_project(), title="A project", url="https://teriin.org/p")
    assert "field_completed_start_date" in got
    assert "field_completed_end_date" in got
    assert END_RAW in got
    assert "2022-12-31" in got


@pytest.mark.parametrize("kwargs,expected", [
    ({"end": None}, "empty"),
    ({"end": "1970-01-01T00:00:00+00:00"}, "not\n    a usable date".replace("\n    ", " ")),
    ({"start": END_RAW, "end": START_RAW}, "before"),
    ({"start": None}, "usable and has been kept"),
])
def test_every_range_outcome_is_explained_in_the_evidence(kwargs, expected):
    sentence = describe(_project(**kwargs))
    assert expected in sentence
    assert sentence.endswith(".")


def test_an_attachments_evidence_explains_the_period_too():
    got = describe(_project(), title="A project", url="https://teriin.org/p",
                   for_attachment=True)
    assert got.startswith("Inherited from")
    assert "field_completed_end_date" in got


def test_the_range_issue_vocabulary_fits_the_column_that_stores_it():
    """`{state}_date_decision.range_issue` is VARCHAR(24)."""
    for issue in ("inverted", "end_invalid", "end_without_start"):
        assert len(issue) <= 24


# --------------------------------------------------------------------------- #
# Inheritance
# --------------------------------------------------------------------------- #

def test_inheriting_carries_the_value_the_precision_and_the_evidence():
    parent = resolve_effective_dates("research_papers", CREATED, {"field_rpaper_year": 2022})
    child = inherited(parent)
    assert child.start_value == parent.start_value
    assert child.start_precision == "year", "a file on a paper is year-precision too"
    assert child.start_field == "field_rpaper_year"
    assert child.start_raw == 2022
    assert child.bundle == "research_papers"
    assert (child.source, child.rule) == ("parent_page", "inherited_from_parent")


def test_inheriting_is_pure():
    """Every PDF on a page is handed the same parent resolution; one of them
    mutating it would re-date the rest."""
    parent = resolve_effective_dates("news", CREATED, {"field_news_date": "2013-01-23T18:30:00+00:00"})
    before = parent.start_value
    for _ in range(3):
        inherited(parent)
    assert parent.start_value == before


def test_from_bundle_field_is_true_only_for_a_value_the_field_supplied():
    supplied = resolve_effective_dates("news", CREATED, {"field_news_date": "2013-01-23T18:30:00+00:00"})
    empty = resolve_effective_dates("news", CREATED, {})
    stamp = resolve_effective_dates("article", CREATED, {})
    assert supplied.from_bundle_field
    assert not empty.from_bundle_field
    assert not stamp.from_bundle_field


# --------------------------------------------------------------------------- #
# Provenance prose
# --------------------------------------------------------------------------- #

def test_the_evidence_sentence_names_bundle_field_and_value():
    """"Why does this document have the date 2022?" has to be answerable from
    the stored row alone."""
    got = describe(resolve_effective_dates("research_papers", CREATED, {"field_rpaper_year": 2022}),
                   title="A paper", url="https://teriin.org/p")
    assert "research_papers" in got
    assert "field_rpaper_year" in got
    assert "2022" in got


def test_an_attachments_sentence_names_the_page_it_came_from():
    parent = resolve_effective_dates("research_papers", CREATED, {"field_rpaper_year": 2022})
    got = describe(parent, title="A paper",
                   url="https://teriin.org/p", for_attachment=True)
    assert got.startswith("Inherited from")
    assert "A paper" in got and "https://teriin.org/p" in got
    assert "field_rpaper_year" in got and "2022" in got


def test_a_range_field_says_so_in_the_evidence():
    """The one place the distinction is visible to a reader of the audit trail:
    this date opens a period rather than being a date the CMS states outright."""
    got = describe(resolve_effective_dates(
        "completed_projects", CREATED,
        {"field_completed_start_date": "2004-06-28T18:30:00+00:00"}))
    assert "opens the period" in got


def test_a_plain_date_field_needs_no_gloss():
    """A `date` field is the CMS stating the content's date outright; adding a
    clause about it would be noise in every news row."""
    got = describe(resolve_effective_dates(
        "news", CREATED, {"field_news_date": "2013-01-23T18:30:00+00:00"}))
    assert "opens the period" not in got and "closes the period" not in got


@pytest.mark.parametrize("rule,metadata,bundle", [
    ("field_empty", {}, "news"),
    ("field_invalid", {"field_news_date": "nonsense"}, "news"),
    ("bundle_created", {}, "article"),
    ("bundle_unmapped", {}, "unknown_bundle"),
])
def test_every_fallback_rung_produces_a_readable_sentence(rule, metadata, bundle):
    resolved = resolve_effective_dates(bundle, CREATED, metadata)
    assert resolved.rule == rule
    sentence = describe(resolved)
    assert sentence.endswith(".") and len(sentence) > 20


def test_an_undated_record_says_why_it_is_undated():
    assert "undated" in describe(resolve_effective_dates("news", None, {}))


# --------------------------------------------------------------------------- #
# Shape
# --------------------------------------------------------------------------- #

def test_the_result_is_immutable():
    """It is passed to the document, to the audit row and to every attachment on
    the page; a mutable one would let any of them re-date the others."""
    got = resolve_effective_dates("article", CREATED, {})
    with pytest.raises(Exception):
        got.start_value = "2020-01-01T00:00:00+00:00"


def test_the_source_vocabulary_fits_the_column_that_stores_it():
    """`documents.date_source` is VARCHAR(16)."""
    for source in ("created", "cms_field", "parent_page", "document_text"):
        assert len(source) <= 16


def test_every_rule_fits_the_column_that_stores_it():
    """`{state}_date_decision.rule` is VARCHAR(48)."""
    rules = {"bundle_date_field", "bundle_created", "field_empty", "field_invalid",
             "bundle_unmapped", "no_bundle", "no_date", "inherited_from_parent",
             "parent_bundle_date_field", "bundle_field_empty",
             "bundle_field_invalid", "bundle_field_matches_created"}
    assert all(len(rule) <= 48 for rule in rules)


def test_every_configured_field_name_fits_the_date_source_column():
    """`{state}_date_decision.date_source` is VARCHAR(32)."""
    assert all(len(f) <= 32 for fields in BUNDLE_DATE_FIELDS.values()
               for f in fields)


def test_an_effective_date_can_be_built_directly_for_a_caller_that_knows():
    """The dataclass is part of the contract: the backfill and the attachment
    path both construct and pass one around."""
    got = EffectiveDate(start_value=CREATED, source="created",
                        start_precision="day",
                        rule="bundle_created", bundle="article")
    assert not got.from_bundle_field
