"""Data contracts for the Database Planner and its tools.

The planner emits a `DatabasePlan` (a list of `ToolCall`s); executing each call
produces a `ToolResult`. `RecordFilters` is the normalized, entity-agnostic filter
set the Scope Resolver (see filters.py) turns into catalog query kwargs. See
docs/database-tool-registry.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ToolName = Literal[
    "count_records", "list_records", "lookup_record", "aggregate_records", "list_themes",
    "resolve_entity",
]

# resolve_entity's advertised entity kinds — author | bundle | theme, not tag
# (see app.retrieval.structured.resolve for why).
ResolveType = Literal["author", "bundle", "theme"]

# Grouping dimensions for aggregate_records (mapped to catalog columns/facets by
# the tool: theme->theme, content_type->bundle, author, year).
GroupBy = Literal["theme", "content_type", "author", "year"]


@dataclass
class RecordFilters:
    """Normalized filter scope — only the columns the catalog actually supports.

    `theme` and `tag` are display names resolved to taxonomy UUIDs by the Scope
    Resolver; dates are a half-open [from, to) interval over published_at.
    """

    theme: str | None = None
    tag: str | None = None
    author: str | None = None
    title_contains: str | None = None
    date_from: str | None = None
    date_to: str | None = None


@dataclass
class ToolCall:
    """One planned catalog operation. `entity` is a canonical bundle name (or None
    to span all content); operation-specific fields are ignored by tools that
    don't use them."""

    tool: ToolName
    entity: str | None = None
    filters: RecordFilters = field(default_factory=RecordFilters)
    # aggregate_records
    group_by: GroupBy | None = None
    aggregation: str = "count"
    # lookup_record
    title: str | None = None
    # list_records / lookup_record
    sort: str = "recent"
    limit: int = 10
    # list_records: page offset, and the metadata keys to keep in the returned
    # records (None keeps them all).
    offset: int = 0
    fields: list[str] | None = None
    # rendering shape for list/aggregate output (table/timeline/list/default)
    output_format: str = "default"
    # resolve_entity
    query: str | None = None
    resolve_type: ResolveType | None = None


@dataclass
class DatabasePlan:
    """An ordered set of tool calls for one query. Independent calls execute in
    parallel; `rationale` is for logging/debugging."""

    calls: list[ToolCall] = field(default_factory=list)
    rationale: str = ""


@dataclass
class ToolResult:
    """A tool's structured output plus a deterministic rendering.

    `data` holds the shape for the tool: {"count": int} | {"records": [...]} |
    {"groups": [[value, count], ...]}. `rendered` is the LLM-free answer for the
    single-capability path; `data` + `citations` are the evidence for multi-label
    synthesis. `ok=False` signals a guarded no-answer (e.g. unknown entity) so the
    caller can fall through to semantic search — unless `error_kind` marks it
    terminal (see below), in which case `rendered` is the answer instead.
    """

    tool: str
    entity: str | None = None
    ok: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    citations: list[dict[str, Any]] = field(default_factory=list)
    rendered: str = ""
    error: str | None = None
    # "unresolved" | "ambiguous" -> terminal: a filter was understood but could
    # not be answered honestly, so `rendered` is shown as the answer rather than
    # a cue to fall through to semantic search.
    # "no_records" | "unknown_entity" | "query_failed" | None -> today's
    # behaviour: ok=False here still means "fall through".
    error_kind: str | None = None
