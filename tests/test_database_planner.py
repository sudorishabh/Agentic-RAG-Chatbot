"""Phase 3: the Database Planner — slot mapping and plan execution/routing."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.retrieval.structured import planner
from app.retrieval.structured.types import DatabasePlan, ToolCall, ToolResult


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


def test_execute_routes_to_list_themes(monkeypatch):
    monkeypatch.setattr(
        planner, "list_themes",
        lambda *, limit, output_format: ToolResult(
            tool="list_themes", data={"themes": ["Climate"]}
        ),
    )
    results = planner.execute(DatabasePlan(calls=[ToolCall(tool="list_themes")]))
    assert len(results) == 1
    assert results[0].tool == "list_themes" and results[0].data == {"themes": ["Climate"]}


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


# --------------------------------------------------------------------------- #
# plan_multi — the v2 LLM planner (LLM stubbed; no network).
# --------------------------------------------------------------------------- #

class _FakePlannerLLM:
    def __init__(self, plan):
        self._plan = plan

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        return self._plan


def test_plan_multi_builds_calls_from_llm(monkeypatch):
    fake = planner._MultiPlan(
        calls=[
            planner._PlannedCall(tool="count_records", entity="report",
                                 date_from="2023-01-01", date_to="2024-01-01"),
            planner._PlannedCall(tool="count_records", entity="report",
                                 date_from="2024-01-01", date_to="2025-01-01"),
        ],
        rationale="2023 vs 2024",
    )
    monkeypatch.setattr(
        "app.core.clients.llm.get_structured_llm", lambda: _FakePlannerLLM(fake)
    )
    plan_obj = planner.plan_multi("reports in 2023 vs 2024", output_format="table")

    assert [c.tool for c in plan_obj.calls] == ["count_records", "count_records"]
    assert plan_obj.calls[0].filters.date_from == "2023-01-01"
    assert plan_obj.calls[1].filters.date_to == "2025-01-01"
    assert all(c.output_format == "table" for c in plan_obj.calls)


def test_plan_multi_caps_calls(monkeypatch):
    fake = planner._MultiPlan(
        calls=[planner._PlannedCall(tool="list_records") for _ in range(10)]
    )
    monkeypatch.setattr(
        "app.core.clients.llm.get_structured_llm", lambda: _FakePlannerLLM(fake)
    )
    assert len(planner.plan_multi("q").calls) == planner._MAX_CALLS


def test_plan_multi_empty_is_none(monkeypatch):
    monkeypatch.setattr(
        "app.core.clients.llm.get_structured_llm",
        lambda: _FakePlannerLLM(planner._MultiPlan(calls=[])),
    )
    assert planner.plan_multi("q") is None


def test_plan_multi_falls_back_on_error(monkeypatch):
    def boom():
        raise RuntimeError("llm down")

    monkeypatch.setattr("app.core.clients.llm.get_structured_llm", boom)
    assert planner.plan_multi("q") is None
