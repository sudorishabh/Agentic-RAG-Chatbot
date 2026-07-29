"""Structured (catalog / database-intent) query capability.

Parameterized, operation-level catalog tools driven by the Database Planner,
plus the thin `answerer` adapter the query pipeline calls for the
database-intent route. See docs/database-tool-registry.md.
"""

from app.retrieval.structured.answerer import answer_structured, parse_structured
from app.retrieval.structured.entities import (
    Entity,
    entity_label,
    get_entity,
    is_known,
    normalize_entity,
)
from app.retrieval.structured.filters import (
    ResolvedScope,
    resolve_filters,
    resolve_tag,
    resolve_theme,
)
from app.retrieval.structured.planner import execute, plan
from app.retrieval.structured.tools import (
    aggregate_records,
    count_records,
    list_records,
    list_themes,
    lookup_record,
    resolve_entity,
    resolve_lookup_chain,
)
from app.retrieval.structured.types import (
    DatabasePlan,
    RecordFilters,
    ToolCall,
    ToolResult,
)

__all__ = [
    "answer_structured",
    "parse_structured",
    "Entity",
    "entity_label",
    "get_entity",
    "is_known",
    "normalize_entity",
    "ResolvedScope",
    "resolve_filters",
    "resolve_tag",
    "resolve_theme",
    "aggregate_records",
    "count_records",
    "list_records",
    "list_themes",
    "lookup_record",
    "resolve_entity",
    "resolve_lookup_chain",
    "execute",
    "plan",
    "DatabasePlan",
    "RecordFilters",
    "ToolCall",
    "ToolResult",
]
