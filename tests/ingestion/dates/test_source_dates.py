"""What each date-like CMS field *is*, and the primitives for reading one.

``FIELD_ROLES`` describes the **source field**, never the application's date
model. The system stores one thing — a document's effective start date, and
where its bundle declares one, an effective end date — and this table exists so
that an auditor looking at such a date can see whether it came from a date the
CMS states outright or from one end of a period.

The old vocabulary (`publication` / `event` / `period` / `unknown`) is gone with
the concept it named. What replaced it earns its place by controlling something:

* ``date`` vs ``range_start`` / ``range_end`` — what the provenance sentence says,
  and it mirrors the ``(start, end)`` ordering `BUNDLE_DATE_FIELDS` relies on.
* ``sort_key`` — a real timestamp that describes nothing; no bundle may map to it.
* ``not_a_date`` — declared so `undeclared_source_date_field` stops firing on
  three fields forever.

Behaviour is unchanged by the rename: the precision column, the IST conversion
and the plausibility bounds all do exactly what they did.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.ingestion.source_dates import (
    FIELD_ROLES,
    as_stored_date,
    classify,
    found_dates,
    is_plausible,
    to_ist_date,
)


# --------------------------------------------------------------------------- #
# The table
# --------------------------------------------------------------------------- #

#: Every field, and what it is. Written out rather than derived, so a change to
#: the table has to be made twice — deliberately.
EXPECTED_ROLES = {
    "field_news_date": "date",
    "field_pressrelease_date": "date",
    "field_report_date": "date",
    "field_rpaper_year": "date",
    "field_completed_start_date": "range_start",
    "field_completed_end_date": "range_end",
    "field_ongoing_start_date": "range_start",
    "field_event_start_date": "range_start",
    "field_event_end_date": "range_end",
    "field_enddate_forlatestfirst": "sort_key",
    "field_article_published_in": "not_a_date",
    "field_rpaper_published_in": "not_a_date",
    "field_rpaper_publisher": "not_a_date",
}


@pytest.mark.parametrize("field,role", sorted(EXPECTED_ROLES.items()))
def test_each_measured_field_has_its_role(field, role):
    assert classify(field) == role
    assert FIELD_ROLES[field][0] == role


def test_the_table_holds_exactly_the_measured_fields():
    assert set(FIELD_ROLES) == set(EXPECTED_ROLES)


def test_the_vocabulary_has_no_publication_concept():
    """The point of the rename. A role answers "what is this Drupal field?",
    never "is the resulting date a publication?" — the system does not store
    publication dates."""
    roles = {role for role, _ in FIELD_ROLES.values()}
    assert roles == {"date", "range_start", "range_end", "sort_key", "not_a_date"}
    assert not any("publication" in role or "published" in role for role in roles)


def test_the_creation_stamp_has_a_role_of_its_own():
    """`created` is not a declared CMS field, so it is not in the table — but it
    is a real date the source states, and the value most bundles fall back to.
    Letting `classify` call it `not_a_date` would put a self-contradicting
    sentence in the audit row of every `article` and `page`."""
    from app.ingestion.bundle_dates import describe, resolve_effective_dates

    resolved = resolve_effective_dates("article", "2018-01-20T05:51:02+00:00", {})
    assert resolved.field_role == "created_stamp"
    assert "not a date field" not in describe(resolved)


def test_a_field_that_gave_nothing_still_reports_its_own_role():
    """It is the *field* that disappointed, and the audit row has to say which
    one — so the role stays the field's, not the fallback's."""
    from app.ingestion.bundle_dates import resolve_effective_dates

    resolved = resolve_effective_dates(
        "news", "2018-01-20T05:51:02+00:00", {"field_news_date": None})
    assert resolved.field_role == "date"


def test_an_undeclared_field_is_not_a_date():
    """The safe reading: nothing may date a document by a field nobody has
    classified, and the reconciliation check is what surfaces one."""
    assert classify("field_brand_new_date") == "not_a_date"
    assert classify("") == "not_a_date"


def test_range_ends_are_distinguishable_from_range_starts():
    """`BUNDLE_DATE_FIELDS` is ordered `(start, end)`; collapsing the two roles
    would remove the only independent check that a pair is the right way round."""
    starts = {f for f, (r, _) in FIELD_ROLES.items() if r == "range_start"}
    ends = {f for f, (r, _) in FIELD_ROLES.items() if r == "range_end"}
    assert starts and ends and not (starts & ends)
    assert all("start" in f for f in starts)
    assert all("end" in f for f in ends)


def test_every_bundle_mapped_field_is_declared_here():
    """A bundle cannot be dated by a field this table says nothing about."""
    from app.ingestion.bundle_dates import BUNDLE_DATE_FIELDS

    for bundle, fields in BUNDLE_DATE_FIELDS.items():
        for field in fields:
            if field == "created":
                continue
            assert field in FIELD_ROLES, f"{bundle} -> {field}"


def test_no_bundle_is_dated_by_a_sort_key_or_a_non_date():
    """`field_enddate_forlatestfirst` orders a listing and describes nothing."""
    from app.ingestion.bundle_dates import BUNDLE_DATE_FIELDS

    for bundle, fields in BUNDLE_DATE_FIELDS.items():
        for field in fields:
            if field == "created":
                continue
            assert FIELD_ROLES[field][0] in ("date", "range_start", "range_end"), (
                f"{bundle} is dated by {field}, which is a "
                f"{FIELD_ROLES[field][0]}"
            )


# --------------------------------------------------------------------------- #
# Precision — the other column, unchanged by the rename
# --------------------------------------------------------------------------- #

def test_only_the_year_field_carries_year_precision():
    year_only = {f for f, (_, precision) in FIELD_ROLES.items()
                 if precision == "year"}
    assert year_only == {"field_rpaper_year"}


def test_precision_is_read_from_this_table_and_nowhere_else():
    from app.ingestion.bundle_dates import precision_of

    for field, (_, precision) in FIELD_ROLES.items():
        assert precision_of(field) == precision
    assert precision_of("created") == "day"
    assert precision_of("field_unknown") == "day"


# --------------------------------------------------------------------------- #
# The value-reading primitives — behaviour must be identical
# --------------------------------------------------------------------------- #

def test_ist_midnight_in_utc_is_the_next_calendar_day():
    assert to_ist_date("2012-04-17T18:30:00+00:00") == date(2012, 4, 18)


def test_an_explicit_ist_offset_is_not_shifted_twice():
    assert to_ist_date("2018-03-06T00:00:00+05:30") == date(2018, 3, 6)


def test_a_naive_value_is_read_as_utc():
    assert to_ist_date("2015-08-26T18:30:00") == date(2015, 8, 27)


def test_a_bare_year_is_read_as_a_january_marker():
    assert to_ist_date("2016") == date(2016, 1, 1)
    assert to_ist_date(2016) == date(2016, 1, 1)


def test_a_list_value_uses_its_first_entry():
    assert to_ist_date(["2015-08-26T18:30:00+00:00", "x"]) == date(2015, 8, 27)


@pytest.mark.parametrize("value", [None, "", [], "not a date", "31/12/2019"])
def test_an_unreadable_value_is_none(value):
    assert to_ist_date(value) is None


def test_plausibility_bounds():
    assert not is_plausible(date(1970, 1, 1))
    assert not is_plausible(date(1989, 12, 31))
    assert is_plausible(date(1990, 1, 1))
    assert not is_plausible(None)


def test_a_stored_date_is_utc_midnight_on_the_resolved_day():
    assert as_stored_date(date(2012, 4, 18)) == "2012-04-18T00:00:00+00:00"


# --------------------------------------------------------------------------- #
# found_dates
# --------------------------------------------------------------------------- #

def test_found_dates_reports_every_usable_value_with_its_role():
    found = found_dates({
        "field_news_date": "2015-08-26T18:30:00+00:00",
        "field_event_start_date": "2017-11-05T18:30:00+00:00",
        "field_completed_end_date": "2005-06-30T18:30:00+00:00",
        "title": "not a date field",
    })
    assert {(f.field, f.role) for f in found} == {
        ("field_news_date", "date"),
        ("field_event_start_date", "range_start"),
        ("field_completed_end_date", "range_end"),
    }


def test_found_dates_skips_values_that_are_not_usable_dates():
    """A `not_a_date` field holding the literal string "2021" — real data on this
    site — must not be reported as a date this record offered."""
    assert found_dates({"field_rpaper_publisher": "TERI Press"}) == []
    assert found_dates({"field_news_date": "1970-01-01T00:00:00+00:00"}) == []


def test_found_dates_is_empty_for_a_record_with_nothing_declared():
    assert found_dates({"title": "x", "field_sponsors": ["a"]}) == []
    assert found_dates(None) == []


# --------------------------------------------------------------------------- #
# The rule that used to live here is gone
# --------------------------------------------------------------------------- #

def test_the_old_publication_rule_is_not_reachable():
    """`publication_date()` answered "which of these fields is *the* publication
    date". The system does not ask that any more — a bundle names the field it is
    dated by — and a dead adapter is how the old model creeps back."""
    import app.ingestion.source_dates as module

    for gone in ("publication_date", "is_publication", "FIELD_KINDS", "Kind",
                 "ACTIONABLE_PRECISIONS"):
        assert not hasattr(module, gone), gone
