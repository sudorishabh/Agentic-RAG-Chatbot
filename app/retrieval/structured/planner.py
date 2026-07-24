"""Database Planner: turn extracted query slots into a validated tool plan.

v1 is deterministic — it maps the operation + facets the intent layer already
extracted onto a single tool call. The interface is ready for a v2 LLM planner
that emits several calls; `execute` already runs a plan's independent calls in
parallel. See docs/database-planner-architecture.md.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES
from app.retrieval.structured.tools import (
    aggregate_records,
    count_records,
    list_records,
    list_themes,
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
    if operation == "list_themes":
        # Vocabulary-wide: no entity/filter scoping.
        return ToolCall(tool="list_themes", filters=filters, limit=limit,
                        output_format=output_format)
    return ToolCall(tool="list_records", entity=bundle, filters=filters, limit=limit,
                    output_format=output_format)


def plan(slots: Any, *, output_format: str = "default") -> DatabasePlan:
    """v1 deterministic plan: one tool call derived from the extracted slots."""
    call = _tool_call(slots, output_format)
    return DatabasePlan(
        calls=[call], rationale=f"{call.tool} for {call.entity or 'all content'}"
    )


# ── v2: LLM multi-call planner ───────────────────────────────────────────────
# Opt-in via settings.database_multi_call_enabled. Decomposes a compound catalog
# question into several tool calls; any failure returns None so answer_structured
# falls back to the deterministic v1 `plan` above. `execute` already runs the
# calls in parallel.

_MAX_CALLS = 4


class _PlannedCall(BaseModel):
    """One LLM-planned tool call. Mirrors the fields of `ToolCall` that a planner
    can set from natural language; unset fields fall back to tool defaults."""

    tool: Literal[
        "count_records", "list_records", "lookup_record", "aggregate_records", "list_themes"
    ]
    entity: str | None = Field(
        default=None, description="Content type / bundle, or null to span all content."
    )
    theme: str | None = None
    author: str | None = None
    title_contains: str | None = None
    date_from: str | None = Field(default=None, description="Inclusive ISO start (YYYY-MM-DD).")
    date_to: str | None = Field(default=None, description="Exclusive ISO end (YYYY-MM-DD).")
    group_by: Literal["theme", "content_type", "author", "year"] | None = None
    title: str | None = None
    limit: int = 10


class _MultiPlan(BaseModel):
    calls: list[_PlannedCall] = Field(default_factory=list)
    rationale: str = ""


_PLANNER_SYSTEM = (
    "You plan database queries over a content repository of "
    + ", ".join(DEFAULT_BUNDLES) + ".\n"
    "Decompose the request into one or more catalog tool calls. Emit MULTIPLE "
    "calls ONLY for genuinely compound requests — a comparison across periods, "
    "themes, or content types ('reports in 2023 vs 2024'), or a count paired "
    "with a list. A simple request is a single call.\n"
    "Tools:\n"
    "- count_records: how many items match.\n"
    "- list_records: list matching items (most recent first).\n"
    "- lookup_record: find one item by title.\n"
    "- aggregate_records: counts grouped by group_by "
    "(theme / content_type / author / year).\n"
    "- list_themes: list the themes/topics the collection covers (takes no filters).\n"
    "Set only the fields that apply. Dates are a half-open [date_from, date_to) "
    "ISO range. entity is one of the listed content types, or null for all — leave "
    "it null for a generic collective word ('publications', 'works') so the result "
    "spans every type rather than collapsing onto research_papers."
)


def _to_tool_call(call: _PlannedCall, output_format: str) -> ToolCall:
    return ToolCall(
        tool=call.tool,
        entity=call.entity,
        filters=RecordFilters(
            theme=call.theme,
            author=call.author,
            title_contains=call.title_contains,
            date_from=call.date_from,
            date_to=call.date_to,
        ),
        group_by=call.group_by,
        title=call.title or call.title_contains,
        limit=call.limit or 10,
        output_format=output_format,
    )


def plan_multi(question: str, *, output_format: str = "default") -> DatabasePlan | None:
    """v2 LLM planner: decompose a question into up to ``_MAX_CALLS`` tool calls.

    Returns None on any failure or an empty plan so the caller can fall back to
    the deterministic :func:`plan`."""
    from app.core.clients.llm import get_structured_llm

    try:
        model = get_structured_llm().with_structured_output(_MultiPlan)
        result: _MultiPlan = model.invoke(
            [("system", _PLANNER_SYSTEM), ("human", question)]
        )
    except Exception:
        logger.warning("Multi-call planning failed; falling back to v1.", exc_info=True)
        return None
    calls = [_to_tool_call(c, output_format) for c in result.calls[:_MAX_CALLS]]
    if not calls:
        return None
    return DatabasePlan(calls=calls, rationale=result.rationale or "multi-call plan")


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
    if call.tool == "list_themes":
        return list_themes(limit=call.limit, output_format=call.output_format)
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
