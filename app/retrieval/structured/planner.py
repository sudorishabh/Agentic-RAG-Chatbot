"""Database Planner: turn extracted query slots into a validated tool plan.

v1 is deterministic — it maps the operation + facets the intent layer already
extracted onto a single tool call. The interface is ready for a v2 LLM planner
that emits several calls; `execute` already runs a plan's independent calls in
parallel. See docs/database-planner-architecture.md.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.retrieval.structured.tools import (
    aggregate_records,
    count_records,
    list_records,
    lookup_record,
)
from app.retrieval.structured.types import DatabasePlan, RecordFilters, ToolCall, ToolResult

logger = logging.getLogger(__name__)


def _year_dates(year: Any) -> tuple[str | None, str | None]:
    """Calendar-year bounds for the parse fallback's `year` shorthand (the unified
    analysis emits explicit dates, but parse_structured may set only a year)."""
    try:
        y = int(year)
    except (TypeError, ValueError):
        return None, None
    return f"{y:04d}-01-01", f"{y + 1:04d}-01-01"


def _tool_call(slots: Any, output_format: str) -> ToolCall:
    """Map a slots object (analysis or StructuredQuery — duck-typed on operation,
    bundle, theme, author, title_contains, group_by, date_from, date_to, limit,
    and optionally year) to one tool call."""
    date_from = getattr(slots, "date_from", None)
    date_to = getattr(slots, "date_to", None)
    if not date_from and not date_to:
        date_from, date_to = _year_dates(getattr(slots, "year", None))
    filters = RecordFilters(
        theme=getattr(slots, "theme", None),
        author=getattr(slots, "author", None),
        title_contains=getattr(slots, "title_contains", None),
        date_from=date_from,
        date_to=date_to,
    )
    operation = getattr(slots, "operation", None) or "list"
    bundle = getattr(slots, "bundle", None)
    limit = getattr(slots, "limit", 10) or 10
    if operation == "count":
        return ToolCall(tool="count_records", entity=bundle, filters=filters,
                        output_format=output_format)
    if operation == "distribution":
        return ToolCall(tool="aggregate_records", entity=bundle, filters=filters,
                        group_by=getattr(slots, "group_by", None),
                        output_format=output_format)
    if operation == "lookup":
        return ToolCall(tool="lookup_record", entity=bundle, filters=filters,
                        title=getattr(slots, "title_contains", None), limit=limit,
                        output_format=output_format)
    return ToolCall(tool="list_records", entity=bundle, filters=filters, limit=limit,
                    output_format=output_format)


def plan(slots: Any, *, output_format: str = "default") -> DatabasePlan:
    """v1 deterministic plan: one tool call derived from the extracted slots."""
    call = _tool_call(slots, output_format)
    return DatabasePlan(
        calls=[call], rationale=f"{call.tool} for {call.entity or 'all content'}"
    )


def _run(call: ToolCall, question: str | None) -> ToolResult:
    if call.tool == "count_records":
        return count_records(call.entity, call.filters)
    if call.tool == "list_records":
        return list_records(call.entity, call.filters, sort=call.sort,
                            limit=call.limit, output_format=call.output_format)
    if call.tool == "lookup_record":
        return lookup_record(call.entity, call.title, call.filters, limit=call.limit,
                             output_format=call.output_format, question=question)
    if call.tool == "aggregate_records":
        return aggregate_records(call.entity, call.group_by, call.filters,
                                 aggregation=call.aggregation,
                                 output_format=call.output_format)
    return ToolResult(tool=call.tool, entity=call.entity, ok=False,
                      error=f"unknown tool {call.tool!r}")


def execute(db_plan: DatabasePlan, *, question: str | None = None) -> list[ToolResult]:
    """Execute a plan's tool calls; independent calls run in parallel. Each tool is
    fail-open, so partial failures surface as ok=False results, never raises."""
    calls = db_plan.calls
    if not calls:
        return []
    if len(calls) == 1:
        return [_run(calls[0], question)]
    with ThreadPoolExecutor(max_workers=min(len(calls), 4)) as pool:
        return list(pool.map(lambda call: _run(call, question), calls))
