"""The date audit's judgements, tested without a database.

The audit is the instrument every later date change is measured against, so its
readings have to be right before they are trusted. Each judgement it makes is a
pure function over one row's worth of data; those are what is tested here. The
I/O — one set of SELECTs and one Qdrant scroll — is deliberately not.

``compare`` is tested too, and matters as much as the checks: it is what turns
"we changed some dates" into "these counts moved by these amounts, and none of
the defect counts rose".
"""

from __future__ import annotations

from datetime import date

import pytest

from scripts.audit_dates import (
    Check,
    compare,
    date_ish_keys,
    fiscal_year_conflict,
    is_plausible,
    plain_year_conflict,
    snapshot,
    strip_percent_encoding,
    to_ist_date,
)


# --------------------------------------------------------------------------- #
# Percent-encoding: the phantom-year source
# --------------------------------------------------------------------------- #

def test_percent_escapes_are_blanked_not_decoded():
    assert strip_percent_encoding("Policy%20Brief%20Biodiesel.pdf") == \
        "Policy Brief Biodiesel.pdf"


def test_a_percent_escape_cannot_manufacture_a_year():
    """``%20`` followed by ``24`` reads as the four digits 2024 to any year
    pattern. This is the real case that made a COP-27 agenda look like 2027."""
    name = "Draft%20Agenda%20COP%2027%20-%20India.pdf"
    assert "2027" in name
    assert "2027" not in strip_percent_encoding(name)


def test_a_real_year_survives_stripping():
    assert "2024" in strip_percent_encoding("Auditor-Report-2024-25.pdf")


# --------------------------------------------------------------------------- #
# The IST boundary
# --------------------------------------------------------------------------- #

def test_ist_midnight_stored_as_utc_reads_as_the_next_day():
    """The whole class of off-by-one-day errors. The CMS stores a date-only
    field as IST midnight expressed in UTC, so 17 April 18:30Z *is* 18 April in
    Delhi — and 18 April is what the site displays."""
    assert to_ist_date("2012-04-17T18:30:00+00:00") == date(2012, 4, 18)
    assert to_ist_date("2015-11-03T18:30:00+00:00") == date(2015, 11, 4)


def test_a_timestamp_already_in_ist_is_not_shifted_again():
    assert to_ist_date("2020-05-08T22:00:00+05:30") == date(2020, 5, 8)


def test_a_naive_timestamp_is_read_as_utc():
    assert to_ist_date("2023-02-27T11:30:03") == date(2023, 2, 27)


def test_a_bare_year_becomes_january_as_a_marker():
    """``field_rpaper_year`` holds ``2014``. January is a placeholder for the
    year, never an assertion about the month — which is why precision has to be
    tracked separately rather than inferred from the value."""
    assert to_ist_date("2014") == date(2014, 1, 1)


@pytest.mark.parametrize("value", [None, "", "not a date", "N/A", "0000-00-00", []])
def test_unusable_values_yield_nothing(value):
    assert to_ist_date(value) is None


@pytest.mark.parametrize("value", ["1970-01-01T00:00:00+00:00", "1899", "1889-01-01"])
def test_implausible_values_are_rejected(value):
    assert not is_plausible(to_ist_date(value))


def test_a_plausible_value_is_accepted():
    assert is_plausible(to_ist_date("2019-06-01T00:00:00+00:00"))


# --------------------------------------------------------------------------- #
# A document dated before the period it reports on
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "filename,published_year,expected",
    [
        ("Auditor-Report-2024-25.pdf", 2018, 6),
        ("Balance_Sheet_2023_24.pdf", 2018, 5),
        ("TERI-Annual-Report-2024-25.pdf", 2022, 2),
        ("receipts-payments_20-21.pdf", 2018, 2),
    ],
)
def test_a_report_cannot_predate_its_own_fiscal_year(filename, published_year, expected):
    assert fiscal_year_conflict(filename, published_year) == expected


@pytest.mark.parametrize(
    "filename,published_year",
    [
        ("TAR_2015-16.pdf", 2018),            # published after the period: fine
        ("Auditor-Report-2024-25.pdf", 2025),  # inside the period: fine
        ("brochure.pdf", 2018),                # no period named
        ("Report-2019-2024.pdf", 2018),        # a range, not an edition
    ],
)
def test_no_conflict_is_reported_without_one(filename, published_year):
    assert fiscal_year_conflict(filename, published_year) is None


def test_a_percent_encoded_name_does_not_fake_a_fiscal_conflict():
    assert fiscal_year_conflict("Net%20Zero%20Report%20_24-5-2024.pdf", 2018) is None


# --------------------------------------------------------------------------- #
# The weaker plain-year signal
# --------------------------------------------------------------------------- #

def test_a_plain_year_later_than_the_date_is_flagged():
    assert plain_year_conflict("RFQ_WSDS_2024_New.pdf", 2018) == 6


@pytest.mark.parametrize(
    "name",
    [
        "Strong policies needed to clean Delhi NCR air by 2025",
        "Chennai's water needs to touch 22365 MLD by 2025",
        "Net Zero pathway to 2070",
        "India's vision 2030 for renewables",
        "Roadmap to 2047",
    ],
)
def test_a_forward_looking_title_is_not_a_contradiction(name):
    """A document about a 2030 target is not published in 2030. Without this the
    check drowns in false positives from ordinary news headlines."""
    assert plain_year_conflict(name, 2018) is None


@pytest.mark.parametrize(
    "name,published_year",
    [
        # Both confirmed against the rendered pages during the source-date
        # backfill: the awards launch was 8 Nov 2016 and the bulletins 9 Jul 2014.
        ("Frost & Sullivan and TERI launch the Sustainability 4.0 Awards 2017", 2016),
        ("Post-2015 Development Agenda Bulletin and launch of TERI Yearbook", 2014),
        # The general patterns those two are instances of.
        ("Nominations open for the Green Award 2025", 2024),
        ("Shaping the post-2020 biodiversity framework", 2019),
    ],
)
def test_an_ordinary_forward_reference_is_not_a_contradiction(name, published_year):
    """The published year here is *earlier* than the year in the name, so the
    conflict would fire but for the filter. Parameterising the year matters: with
    a later published year the arithmetic alone suppresses the flag and the test
    passes without exercising the filter at all."""
    assert plain_year_conflict(name, published_year) is None


def test_an_earlier_year_in_the_name_is_not_a_conflict():
    """A 2015 report posted in 2018 is an ordinary late upload, not an error."""
    assert plain_year_conflict("renewables2015_India.pdf", 2018) is None


# --------------------------------------------------------------------------- #
# Which source-metadata fields get measured
# --------------------------------------------------------------------------- #

def test_date_ish_keys_are_selected_by_name():
    meta = {
        "field_news_date": "2015-08-26T18:30:00+00:00",
        "field_event_start_date": "2017-11-05T18:30:00+00:00",
        "field_rpaper_year": "2016",
        "title": "irrelevant",
        "field_sponsors": ["someone"],
    }
    picked = date_ish_keys(meta)
    assert set(picked) == {"field_news_date", "field_event_start_date", "field_rpaper_year"}


def test_empty_values_are_skipped():
    assert date_ish_keys({"field_news_date": None, "field_report_date": "",
                          "field_event_date": []}) == {}


def test_a_list_valued_field_is_unwrapped_to_its_first_entry():
    assert date_ish_keys({"field_news_date": ["2015-08-26", "x"]})["field_news_date"] \
        == "2015-08-26"


def test_the_audit_does_not_decide_which_fields_are_publication_dates():
    """Event and project-period fields are *measured* here and classified
    elsewhere. Collapsing the two would bake ~3,285 unusable dates into a number
    that looks like a fix."""
    picked = date_ish_keys({"field_completed_start_date": "2004-06-28T18:30:00+00:00"})
    assert "field_completed_start_date" in picked


def test_no_metadata_is_not_an_error():
    assert date_ish_keys({}) == {}


# --------------------------------------------------------------------------- #
# Comparing two runs
# --------------------------------------------------------------------------- #

def _snap(**counts) -> dict:
    return snapshot([Check(name, n, "", is_defect=defect)
                     for name, (n, defect) in counts.items()], {})


def test_an_unchanged_run_reports_no_regression():
    base = _snap(no_effective_start_date=(0, True), migration=(3409, False))
    assert compare(base, base) == 0


def test_a_rising_defect_count_is_a_regression():
    before = _snap(no_effective_start_date=(0, True))
    after = _snap(no_effective_start_date=(7, True))
    assert compare(after, before) == 1


def test_a_falling_defect_count_is_not_a_regression():
    before = _snap(dated_before_its_reporting_period=(30, True))
    after = _snap(dated_before_its_reporting_period=(1, True))
    assert compare(after, before) == 0


def test_a_descriptive_count_may_move_freely():
    """"3409 documents are migration-dated" is a description, not a defect. A
    fix is *expected* to move it, in either direction, without failing a run."""
    before = _snap(documents_in_migration_window=(3409, False))
    after = _snap(documents_in_migration_window=(4000, False))
    assert compare(after, before) == 0


def test_a_new_or_removed_check_does_not_crash_the_comparison():
    before = _snap(old_check=(1, True))
    after = _snap(new_check=(2, True))
    assert compare(after, before) == 0


def test_the_snapshot_round_trips_through_json():
    import json

    snap = _snap(no_effective_start_date=(0, True))
    assert json.loads(json.dumps(snap)) == snap
