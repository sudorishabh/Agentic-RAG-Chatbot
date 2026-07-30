"""Tolerant ISO-date handling for LLM-supplied bounds (app.core.dates)."""

from datetime import datetime, timezone

import pytest
from pydantic import BaseModel

from app.core.dates import IsoDate, clean_iso_date, parse_iso_date


class _Scope(BaseModel):
    date_from: IsoDate = None
    date_to: IsoDate = None


# The observed production failure: the model writes the closing brace and comma
# of the JSON object *inside* the string literal, and the lenient parser hands
# the value through rather than raising.
@pytest.mark.parametrize(
    "raw",
    ['2022-01-01},', '2022-01-01}," \n', '2022-01-01"}', '2022-01-01,', ' 2022-01-01 '],
)
def test_trailing_json_punctuation_is_stripped(raw):
    assert clean_iso_date(raw) == "2022-01-01"


def test_a_clean_date_is_left_alone():
    assert clean_iso_date("2022-01-01") == "2022-01-01"


def test_time_and_offset_survive():
    assert clean_iso_date("2022-01-01T06:30:00Z") == "2022-01-01T06:30:00Z"
    assert parse_iso_date("2022-01-01T06:30:00Z") == datetime(2022, 1, 1, 6, 30)


def test_an_offset_is_normalized_to_naive_utc():
    """published_at is a DATETIME storing UTC with no zone, so a bound carrying
    an offset has to be converted rather than compared as-is."""
    assert parse_iso_date("2022-01-01T12:00:00+05:30") == datetime(2022, 1, 1, 6, 30)
    assert parse_iso_date("2022-01-01").tzinfo is None


@pytest.mark.parametrize("raw", ["not-a-date", "", None, "last 6 months", "01/02/2022"])
def test_junk_yields_nothing(raw):
    assert clean_iso_date(raw) is None
    assert parse_iso_date(raw) is None


def test_a_bare_year_is_rejected_rather_than_guessed():
    """`fromisoformat` reads "2024" as 2024-01-01 on 3.11+, which silently turns
    an upper bound into the *start* of the year. The planner has an explicit
    `year` slot for that; a bound must be a full date."""
    assert clean_iso_date("2024") is None
    assert clean_iso_date("2024-01") is None


def test_an_unreadable_bound_is_logged(caplog):
    """A dropped bound widens the query, so it must leave a trace."""
    with caplog.at_level("WARNING"):
        assert parse_iso_date("nonsense", field="date_to") is None
    assert "date_to" in caplog.text


def test_a_salvageable_bound_is_not_logged(caplog):
    with caplog.at_level("WARNING"):
        assert parse_iso_date("2022-01-01},") == datetime(2022, 1, 1)
    assert caplog.text == ""


def test_the_model_boundary_sanitizes():
    """Cleaning at the boundary, not at each use site, is what keeps the value
    the user sees echoed back in step with the value that reaches SQL."""
    scope = _Scope(date_from="2020-01-01", date_to='2022-01-01},')
    assert (scope.date_from, scope.date_to) == ("2020-01-01", "2022-01-01")


def test_the_model_boundary_drops_junk():
    assert _Scope(date_to="not-a-date").date_to is None


def test_a_datetime_passes_through_the_boundary():
    assert _Scope(date_from=datetime(2020, 1, 1)).date_from == "2020-01-01T00:00:00"


def test_qdrant_bounds_are_utc_aware():
    """The Qdrant path needs tz-aware bounds; the MySQL path needs naive ones."""
    from app.retrieval.understanding.filters import _parse_bound

    assert _parse_bound("2022-01-01},") == datetime(2022, 1, 1, tzinfo=timezone.utc)
    assert _parse_bound("junk") is None
