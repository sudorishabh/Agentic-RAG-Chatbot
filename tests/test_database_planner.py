"""Phase 3: the Database Planner — slot mapping and plan execution/routing."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.retrieval.database import planner
from app.retrieval.database.types import DatabasePlan, ToolCall, ToolResult


def _slots(**kw):
    base = dict(
        operation=None, bundle=None, theme=None, author=None, title_contains=None,
        group_by=None, date_from=None, date_to=None, limit=10,
    )
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.mark.parametrize(
    "operation, tool",
    [
        ("count", "count_records"),
        ("distribution", "aggregate_records"),
        ("lookup", "lookup_record"),
        ("list", "list_records"),
        (None, "list_records"),   # default
    ],
)
def test_plan_maps_operation_to_tool(operation, tool):
    call = planner.plan(_slots(operation=operation, bundle="news")).calls[0]
    assert call.tool == tool
    assert call.entity == "news"


def test_plan_carries_filters_and_format():
    call = planner.plan(
        _slots(operation="count", theme="Climate", author="Sharma",
               date_from="2024-01-01", date_to="2025-01-01"),
        output_format="table",
    ).calls[0]
    assert call.output_format == "table"
    assert call.filters.theme == "Climate"
    assert call.filters.author == "Sharma"
    assert call.filters.date_from == "2024-01-01"


def test_plan_expands_year_shorthand():
    # parse_structured may set only `year`; the planner expands it to a range.
    call = planner.plan(_slots(operation="list", year=2023)).calls[0]
    assert (call.filters.date_from, call.filters.date_to) == ("2023-01-01", "2024-01-01")


def test_plan_explicit_dates_win_over_year():
    call = planner.plan(
        _slots(operation="count", year=2023, date_from="2020-06-01", date_to="2020-07-01")
    ).calls[0]
    assert (call.filters.date_from, call.filters.date_to) == ("2020-06-01", "2020-07-01")


def test_execute_routes_to_tool(monkeypatch):
    monkeypatch.setattr(
        planner, "count_records",
        lambda entity, filters: ToolResult(tool="count_records", entity=entity, data={"count": 7}),
    )
    results = planner.execute(DatabasePlan(calls=[ToolCall(tool="count_records", entity="news")]))
    assert len(results) == 1
    assert results[0].tool == "count_records" and results[0].data == {"count": 7}


def test_execute_runs_multiple_calls(monkeypatch):
    monkeypatch.setattr(planner, "count_records",
                        lambda entity, filters: ToolResult(tool="count_records", entity=entity))
    monkeypatch.setattr(
        planner, "aggregate_records",
        lambda entity, group_by, filters, aggregation="count", output_format="default":
            ToolResult(tool="aggregate_records", entity=entity),
    )
    plan_obj = DatabasePlan(calls=[
        ToolCall(tool="count_records", entity="a"),
        ToolCall(tool="aggregate_records", entity="b", group_by="theme"),
    ])
    results = planner.execute(plan_obj)
    assert {r.tool for r in results} == {"count_records", "aggregate_records"}


def test_execute_passes_question_to_lookup(monkeypatch):
    seen = {}

    def fake_lookup(entity, title, filters, *, limit, output_format, question):
        seen["question"] = question
        seen["title"] = title
        return ToolResult(tool="lookup_record", entity=entity)

    monkeypatch.setattr(planner, "lookup_record", fake_lookup)
    planner.execute(
        DatabasePlan(calls=[ToolCall(tool="lookup_record", entity="report", title="T")]),
        question="what does it say?",
    )
    assert seen == {"question": "what does it say?", "title": "T"}


def test_execute_empty_plan():
    assert planner.execute(DatabasePlan(calls=[])) == []
