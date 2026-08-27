"""Tolerant ISO-date handling for LLM-supplied bounds (app.core.dates)."""

from datetime import date, datetime, timezone

import pytest
from pydantic import BaseModel

from app.core import dates as core_dates
from app.core.dates import (
    IsoDate,
    clean_iso_date,
    current_date_directive,
    exclusive_end,
    inclusive_end,
    parse_iso_date,
    today_utc,
)


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


# --------------------------------------------------------------------------- #
# Inclusive ends -> half-open bounds.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "last_day,bound",
    [
        ("2021-12-31", "2022-01-01"),   # year rollover
        ("2024-02-29", "2024-03-01"),   # leap day
        ("2023-02-28", "2023-03-01"),   # non-leap February
        ("2020-06-30", "2020-07-01"),   # month rollover
        ("2020-02-12", "2020-02-13"),   # ordinary day
    ],
)
def test_an_inclusive_end_becomes_the_next_day(last_day, bound):
    """The rollovers the model got wrong when it was asked to do this itself."""
    assert exclusive_end(last_day) == bound


def test_inclusive_end_is_the_inverse():
    assert inclusive_end("2022-01-01") == "2021-12-31"
    assert inclusive_end(exclusive_end("2021-12-31")) == "2021-12-31"


def test_a_single_day_range_is_not_empty():
    """from == to as an exclusive pair matches nothing; as an inclusive end it
    is the one day the user asked for."""
    assert exclusive_end("2020-02-12") == "2020-02-13"


@pytest.mark.parametrize("bad", [None, "", "not-a-date", "2024"])
def test_unusable_ends_yield_no_bound(bad):
    assert exclusive_end(bad) is None
    assert inclusive_end(bad) is None


def test_a_mangled_inclusive_end_is_salvaged_then_converted():
    """Both defences compose: strip the JSON junk, then add the day."""
    assert exclusive_end('2021-12-31},') == "2022-01-01"


# --------------------------------------------------------------------------- #
# current_date_directive — anchoring relative dates to the real today.
# --------------------------------------------------------------------------- #

@pytest.fixture
def frozen(monkeypatch):
    """Pin the directive's notion of today. `current_date_directive` looks
    `today_utc` up in module globals at call time, so patching it here reaches
    the internal call."""
    def _freeze(value: date) -> date:
        monkeypatch.setattr(core_dates, "today_utc", lambda: value)
        return value

    return _freeze


def test_directive_states_today(frozen):
    frozen(date(2026, 7, 30))
    text = current_date_directive()
    assert "2026-07-30" in text
    assert "Thursday" in text


def test_directive_supplies_year_anchors(frozen):
    """Year bounds are precomputed rather than left to the model: date arithmetic
    is exactly what it gets wrong, and these two windows are the common ones.
    Stated as inclusive ends, matching the field the model fills."""
    frozen(date(2026, 7, 30))
    text = current_date_directive()
    assert "This year runs 2026-01-01 to 2026-12-31" in text
    assert "Last year runs 2025-01-01 to 2025-12-31" in text


def test_directive_ends_an_open_period_at_today_not_tomorrow(frozen):
    """date_to_inclusive is the last day to include, so 'up to now' is today —
    the +1 day belongs to `exclusive_end`, not the model."""
    frozen(date(2026, 12, 31))
    text = current_date_directive()
    assert "ends 2026-12-31" in text
    assert "2027-01-01" not in text


def test_directive_is_recomputed_each_call(frozen):
    """The regression this guards: a date folded into a module-level prompt
    constant is captured at import, so a long-lived API process drifts further
    from reality every day it stays up."""
    frozen(date(2026, 7, 30))
    first = current_date_directive()
    frozen(date(2027, 3, 1))
    second = current_date_directive()
    assert "2026-07-30" in first and "2027-03-01" in second


def test_directive_forbids_defaulting_to_the_current_year(frozen):
    """Without this the model starts inventing a date scope for questions that
    named no period, narrowing answers the user expected to span everything."""
    frozen(date(2026, 7, 30))
    assert "leave both dates null" in current_date_directive()


def test_today_utc_is_a_date():
    assert isinstance(today_utc(), date)


# --------------------------------------------------------------------------- #
# The directive reaches every prompt that extracts dates.
# --------------------------------------------------------------------------- #

def test_understanding_prompt_carries_the_directive(frozen):
    from app.retrieval.understanding.query_processor import _understanding_messages

    frozen(date(2026, 7, 30))
    role, system = _understanding_messages("how many reports last month", None)[0]
    assert role == "system"
    assert "Today is Thursday, 2026-07-30" in system


def test_parse_fallback_prompt_carries_the_directive(frozen, monkeypatch):
    from app.retrieval.structured import answerer

    frozen(date(2026, 7, 30))
    seen: list[str] = []

    class _Fake:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            seen.append(messages[0][1])
            return answerer.StructuredQuery()

    monkeypatch.setattr("app.core.clients.llm.get_structured_llm", lambda: _Fake())
    answerer.parse_structured("how many reports last month")
    assert "2026-07-30" in seen[0]


def test_multi_planner_prompt_carries_the_directive(frozen, monkeypatch):
    from app.retrieval.structured import planner

    frozen(date(2026, 7, 30))
    seen: list[str] = []

    class _Fake:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            seen.append(messages[0][1])
            return planner._MultiPlan(
                calls=[planner._PlannedCall(tool="count_records")]
            )

    monkeypatch.setattr("app.core.clients.llm.get_structured_llm", lambda: _Fake())
    planner.plan_multi("reports last month vs this month")
    assert "2026-07-30" in seen[0]


# --------------------------------------------------------------------------- #
# The LLM-facing models expose an exclusive bound derived from the inclusive one.
# --------------------------------------------------------------------------- #

def test_query_scope_derives_the_exclusive_bound():
    from app.retrieval.understanding.query_processor import QueryScope

    scope = QueryScope(date_from="2020-01-01", date_to_inclusive="2021-12-31")
    assert scope.date_to == "2022-01-01"


def test_structured_query_derives_the_exclusive_bound():
    from app.retrieval.structured.answerer import StructuredQuery

    assert StructuredQuery(date_to_inclusive="2021-12-31").date_to == "2022-01-01"


def test_planned_call_derives_the_exclusive_bound():
    from app.retrieval.structured.planner import _PlannedCall

    call = _PlannedCall(tool="count_records", date_to_inclusive="2021-12-31")
    assert call.date_to == "2022-01-01"


def test_the_derived_bound_stays_out_of_the_llm_schema():
    """`date_to` is a property, not a field: if it were in the schema the model
    could fill it directly and reintroduce the arithmetic this removes."""
    from app.retrieval.understanding.query_processor import QueryScope

    fields = QueryScope.model_json_schema()["properties"]
    assert "date_to_inclusive" in fields
    assert "date_to" not in fields


def test_a_single_day_scope_survives_to_sql():
    """End to end: the model copies one date into both ends, and the query still
    covers that day instead of matching nothing."""
    from app.retrieval.understanding.query_processor import QueryScope
    from app.retrieval.structured.filters import resolve_filters
    from app.retrieval.structured.types import RecordFilters

    scope = QueryScope(date_from="2020-02-12", date_to_inclusive="2020-02-12")
    resolved = resolve_filters(
        RecordFilters(date_from=scope.date_from, date_to=scope.date_to)
    )
    assert resolved.published_from == datetime(2020, 2, 12)
    assert resolved.published_to == datetime(2020, 2, 13)


def test_static_prompt_prefix_stays_stable(frozen):
    """The directive is appended, not interpolated into the body, so the long
    static prefix remains byte-identical and prompt-cacheable across requests."""
    from app.retrieval.understanding.query_processor import _UNDERSTANDING_SYSTEM
    from app.retrieval.understanding.query_processor import _understanding_messages

    frozen(date(2026, 7, 30))
    _, system = _understanding_messages("q", None)[0]
    assert system.startswith(_UNDERSTANDING_SYSTEM)
