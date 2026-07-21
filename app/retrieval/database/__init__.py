"""Database capability: parameterized, operation-level catalog tools driven by
the Database Planner. See docs/database-tool-registry.md.

Phase 1 ships the infrastructure only (contracts, entity registry, scope
resolver); tools and the planner arrive in later phases.
"""

from app.retrieval.database.entities import (
    Entity,
    entity_label,
    get_entity,
    is_known,
    normalize_entity,
)
from app.retrieval.database.filters import ResolvedScope, resolve_filters, resolve_theme
from app.retrieval.database.planner import execute, plan
from app.retrieval.database.tools import (
    aggregate_records,
    count_records,
    list_records,
    lookup_record,
)
from app.retrieval.database.types import (
    DatabasePlan,
    RecordFilters,
    ToolCall,
    ToolResult,
)

__all__ = [
    "Entity",
    "entity_label",
    "get_entity",
    "is_known",
    "normalize_entity",
    "ResolvedScope",
    "resolve_filters",
    "resolve_theme",
    "aggregate_records",
    "count_records",
    "list_records",
    "lookup_record",
    "execute",
    "plan",
    "DatabasePlan",
    "RecordFilters",
    "ToolCall",
    "ToolResult",
]
