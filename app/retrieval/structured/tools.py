"""The catalog tools the Database Planner invokes.

Each tool wraps an existing read function in `app.catalog.queries` and renders
a uniform `ToolResult`. An unknown entity, an unresolvable theme or tag, or an
empty result yields `ok=False` so the caller can fall through to semantic
search. `resolve_entity` is the exception: it wraps
`app.retrieval.structured.resolve` (fuzzy name matching), not a catalog read.

See docs/database-tool-registry.md.
"""

from __future__ import annotations

import logging
import re
from dataclasses import replace
from datetime import datetime
from typing import Any, Sequence

from app.catalog import queries as state
from app.catalog.models import StateRecord
from app.retrieval.structured.entities import entity_label, get_entity
from app.retrieval.structured.filters import _parse_date, resolve_filters
from app.retrieval.structured.types import GroupBy, RecordFilters, ToolResult
from app.schemas.query import Citation

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Rendering helpers.
# --------------------------------------------------------------------------- #

def _md_cell(text: str) -> str:
    """'|' inside a value would break a markdown table row."""
    return text.replace("|", "\\|")


def _period_label(filters: RecordFilters) -> str:
    """Human phrase for a date scope. A whole-calendar-year range reads as
    'in YYYY' rather than raw bounds."""
    df, dt = filters.date_from, filters.date_to
    lo, hi = _parse_date(df), _parse_date(dt)
    if lo and hi and (lo.month, lo.day) == (1, 1) and hi == datetime(lo.year + 1, 1, 1):
        return f" in {lo.year}"
    if df and dt:
        return f" between {df} and {dt}"
    if df:
        return f" since {df}"
    if dt:
        return f" before {dt}"
    return ""


def _render_list_table(records: Sequence[StateRecord]) -> str:
    lines = ["| Title | Published | Type |", "| --- | --- | --- |"]
    for r in records:
        title = _md_cell(r.title or r.document_id)
        cell = f"[{title}]({r.url})" if r.url else title
        lines.append(f"| {cell} | {(r.published_at or '')[:10]} | {r.bundle or ''} |")
    return "\n".join(lines)


def _render_list_timeline(records: Sequence[StateRecord]) -> str:
    """Year-grouped chronology; expects records already sorted newest-first."""
    lines: list[str] = []
    year = ""
    for r in records:
        y = (r.published_at or "")[:4] or "Undated"
        if y != year:
            if lines:
                lines.append("")
            lines.append(f"{y}:")
            year = y
        label = (r.published_at or "")[:7] or "n.d."
        title = r.title or r.document_id
        lines.append(f"- {label}: {title} ({r.url})" if r.url else f"- {label}: {title}")
    return "\n".join(lines)


def _render_records(
    records: Sequence[StateRecord], output_format: str
) -> tuple[str, list[dict], list[dict]]:
    """Body + structured records + citations, in one consistent order (timeline
    sorts newest-first; citations follow the rendered order)."""
    if output_format == "timeline":
        ordered = sorted(records, key=lambda r: r.published_at or "", reverse=True)
        body = _render_list_timeline(ordered)
    elif output_format == "table":
        ordered = list(records)
        body = _render_list_table(ordered)
    else:
        ordered = list(records)
        body = "\n".join(
            f"- {r.title} ({r.url})" if r.url else f"- {r.title or r.document_id}"
            for r in ordered
        )
    citations = [
        Citation(
            n=i, type="website", title=r.title, url=r.url,
            document_id=r.document_id or None,
        ).model_dump()
        for i, r in enumerate(ordered, start=1)
    ]
    data = [
        {
            "document_id": r.document_id, "title": r.title, "url": r.url,
            "published_at": r.published_at, "bundle": r.bundle,
        }
        for r in ordered
    ]
    return "Here is what I found:\n" + body, data, citations


def _theme_section(label: str, names: list[str], output_format: str) -> str:
    """One labelled block of the theme listing (Main themes / Other themes)."""
    if output_format == "table":
        rows = "\n".join(["| theme |", "| --- |"] + [f"| {_md_cell(n)} |" for n in names])
        return f"**{label}**\n{rows}"
    return f"{label}:\n" + "\n".join(f"- {n}" for n in names)


def _project_fields(
    records: list[dict[str, Any]], fields: Sequence[str] | None
) -> list[dict[str, Any]]:
    """Keep only the requested metadata keys per record. Projects the structured
    payload only — `rendered` is a natural-language answer already shaped by
    `output_format`, not a strict field projection, so a field list narrows what
    a caller reads from `data` without changing the human-readable text."""
    if not fields:
        return records
    allowed = set(fields)
    return [{k: v for k, v in r.items() if k in allowed} for r in records]


# --------------------------------------------------------------------------- #
# Tools.
# --------------------------------------------------------------------------- #

def count_records(entity: str | None, filters: RecordFilters) -> ToolResult:
    """How many catalog documents match. Unknown entity returns ok=False (fall
    through, never a misleading zero). A theme/tag that resolves to no term is
    a terminal miss (error_kind="unresolved") — the filter was understood but
    could not be honored, which is a different situation from finding nothing
    to fall through from, so it is reported explicitly rather than guessed at
    via semantic search."""
    ent = get_entity(entity) if entity else None
    if entity and ent is None:
        return ToolResult(tool="count_records", entity=entity, ok=False,
                          error=f"unknown entity {entity!r}")
    scope = resolve_filters(filters)
    if scope.theme_requested and not scope.theme_resolved:
        return ToolResult(tool="count_records", entity=entity, ok=False,
                          error="theme did not resolve to a known term", error_kind="unresolved",
                          rendered=f"No theme matching '{filters.theme}' found.")
    if scope.tag_requested and not scope.tag_resolved:
        return ToolResult(tool="count_records", entity=entity, ok=False,
                          error="tag did not resolve to a known term", error_kind="unresolved",
                          rendered=f"No tag matching '{filters.tag}' found.")
    bundle = ent.name if ent else None
    try:
        total = state.count_documents(
            source_type=ent.source_type if ent else "website",
            bundle=bundle,
            entity_type=ent.entity_type if ent else "node",
            **scope.as_kwargs(),
        )
    except Exception:
        logger.warning("count_records query failed.", exc_info=True)
        return ToolResult(tool="count_records", entity=bundle, ok=False, error="query failed")
    phrase = (f" on '{filters.theme}'" if filters.theme else "") + _period_label(filters)
    verb = "is" if total == 1 else "are"
    rendered = (
        f"There {verb} {total} {entity_label(bundle or 'items', total)}{phrase} "
        "matching your query."
    )
    return ToolResult(tool="count_records", entity=bundle, ok=True,
                      data={"count": total}, rendered=rendered)


def list_records(
    entity: str | None,
    filters: RecordFilters,
    *,
    sort: str = "recent",
    limit: int = 10,
    offset: int = 0,
    output_format: str = "default",
    fields: Sequence[str] | None = None,
) -> ToolResult:
    """List matching documents, most recent first (the only backing sort today).
    Empty result returns ok=False. Unlike an unresolved theme (which still has a
    free-text facet to fall back on), an unresolved tag has no column to filter
    on at all, so it is guarded here rather than silently listing unfiltered
    results. `fields` narrows the metadata keys in `data["records"]`; `rendered`
    is unaffected (see `_project_fields`)."""
    ent = get_entity(entity) if entity else None
    if entity and ent is None:
        return ToolResult(tool="list_records", entity=entity, ok=False,
                          error=f"unknown entity {entity!r}")
    scope = resolve_filters(filters)
    if scope.tag_requested and not scope.tag_resolved:
        return ToolResult(tool="list_records", entity=entity, ok=False,
                          error="tag did not resolve to a known term", error_kind="unresolved",
                          rendered=f"No tag matching '{filters.tag}' found.")
    bundle = ent.name if ent else None
    try:
        records = state.list_documents(
            source_type=ent.source_type if ent else "website",
            bundle=bundle,
            entity_type=ent.entity_type if ent else "node",
            title_contains=scope.title_contains,
            limit=limit,
            offset=offset,
            **scope.as_kwargs(),
        )
    except Exception:
        logger.warning("list_records query failed.", exc_info=True)
        return ToolResult(tool="list_records", entity=bundle, ok=False, error="query failed")
    if not records:
        return ToolResult(tool="list_records", entity=bundle, ok=False,
                          error="no matching records")
    rendered, data, citations = _render_records(records, output_format)
    return ToolResult(tool="list_records", entity=bundle, ok=True,
                      data={"records": _project_fields(data, fields)},
                      citations=citations, rendered=rendered)


# Words signalling the user wants what a document SAYS, not just its catalog entry
# ("what does X say" reads; "show the article titled X" browses).
_CONTENT_QUESTION = re.compile(
    r"\b(what|how|why|when|where|who|does|do|did|is|are|was|were"
    r"|explain|describe|summar\w*|tell)\b",
    re.IGNORECASE,
)


def _resolve_chain(title: str | None, question: str | None, output_format: str) -> str | None:
    """Document id for a title lookup that should chain into content QA: a content
    question (or summary/detailed shape) naming a title that matches exactly one
    catalog document."""
    if not title:
        return None
    is_content = output_format in ("summary", "detailed") or bool(
        question and _CONTENT_QUESTION.search(question)
    )
    if not is_content:
        return None
    try:
        records = state.list_documents(
            source_type="website", entity_type="node", title_contains=title, limit=3,
        )
    except Exception:
        logger.warning("lookup chain resolution failed.", exc_info=True)
        return None
    if len(records) == 1 and records[0].document_id:
        return records[0].document_id
    return None


def lookup_record(
    entity: str | None,
    title: str | None,
    filters: RecordFilters,
    *,
    limit: int = 10,
    output_format: str = "default",
    question: str | None = None,
) -> ToolResult:
    """Find a specific document by title. Returns the list rendering AND a
    `chain_document_id` when the lookup uniquely identifies a document for a
    content question (the caller may then route into the QA path)."""
    chain_id = _resolve_chain(title, question, output_format)
    scoped = replace(filters, title_contains=title or filters.title_contains)
    result = list_records(entity, scoped, limit=limit, output_format=output_format)
    return ToolResult(
        tool="lookup_record",
        entity=result.entity,
        ok=result.ok,
        data={**result.data, "chain_document_id": chain_id},
        citations=result.citations,
        rendered=result.rendered,
        error=result.error,
    )


def resolve_lookup_chain(analysis: Any, question: str) -> str | None:
    """The lookup->content-QA chain decision used by the query pipeline: the
    document id when `analysis` is a lookup naming a title that a content
    question matches to exactly one catalog document, else None. Duck-typed on
    operation / title_contains / answer_format."""
    if analysis is None or getattr(analysis, "operation", None) != "lookup":
        return None
    return _resolve_chain(
        getattr(analysis, "title_contains", None),
        question,
        getattr(analysis, "answer_format", "default"),
    )


# aggregate group_by -> (catalog dimension, display label).
_GROUP_DIMENSIONS: dict[str, tuple[str, str]] = {
    "theme": ("theme", "theme"),
    "content_type": ("bundle", "content type"),
    "author": ("author", "author"),
    "year": ("year", "year"),
}


def aggregate_records(
    entity: str | None,
    group_by: GroupBy | None,
    filters: RecordFilters,
    *,
    aggregation: str = "count",
    output_format: str = "default",
) -> ToolResult:
    """Grouped counts (per theme / content type / author / year). Only the
    'count' aggregation is backed today."""
    dimension, label = _GROUP_DIMENSIONS.get(group_by or "theme", ("theme", "theme"))
    ent = get_entity(entity) if entity else None
    if entity and ent is None:
        return ToolResult(tool="aggregate_records", entity=entity, ok=False,
                          error=f"unknown entity {entity!r}")
    scope = resolve_filters(filters)
    if scope.theme_requested and not scope.theme_resolved:
        return ToolResult(tool="aggregate_records", entity=entity, ok=False,
                          error="theme did not resolve to a known term", error_kind="unresolved",
                          rendered=f"No theme matching '{filters.theme}' found.")
    if scope.tag_requested and not scope.tag_resolved:
        return ToolResult(tool="aggregate_records", entity=entity, ok=False,
                          error="tag did not resolve to a known term", error_kind="unresolved",
                          rendered=f"No tag matching '{filters.tag}' found.")
    bundle = ent.name if ent else None
    try:
        rows = state.distribution(
            dimension,
            source_type="website",
            bundle=bundle,
            entity_type="node",
            title_contains=scope.title_contains,
            **scope.as_kwargs(),
        )
    except Exception:
        logger.warning("aggregate_records query failed.", exc_info=True)
        return ToolResult(tool="aggregate_records", entity=bundle, ok=False, error="query failed")
    if not rows:
        return ToolResult(tool="aggregate_records", entity=bundle, ok=False,
                          error="no matching records")
    if output_format == "table":
        body = "\n".join(
            [f"| {label} | count |", "| --- | --- |"]
            + [f"| {_md_cell(str(value))} | {n} |" for value, n in rows]
        )
    else:
        body = "\n".join(f"- {value}: {n}" for value, n in rows)
    rendered = (
        f"Distribution of {entity_label(bundle or 'items', 2)}{_period_label(filters)} "
        f"by {label}:\n" + body
    )
    return ToolResult(tool="aggregate_records", entity=bundle, ok=True,
                      data={"groups": [[value, n] for value, n in rows]}, rendered=rendered)


def list_themes(*, limit: int = 200, output_format: str = "default") -> ToolResult:
    """Enumerate the themes the collection covers, from the canonical taxonomy
    (not the free-text facet), split into Main themes and Other themes (main
    first) per app/data.json's top-level buckets. A theme the map does not know
    about (added in the CMS since) lists under Other rather than being dropped.
    Answers 'what themes/topics do you cover?' / 'how many themes are there?'.
    An empty vocabulary or a query failure returns ok=False so the caller can
    fall through to semantic search."""
    try:
        from app.catalog import terms, theme_taxonomy

        rows = terms.list_themes(limit=limit)
    except Exception:
        logger.warning("list_themes query failed.", exc_info=True)
        return ToolResult(tool="list_themes", ok=False, error="query failed")
    if not rows:
        return ToolResult(tool="list_themes", ok=False, error="no themes found")
    names = [r["name"] for r in rows]
    main = [n for n in names if theme_taxonomy.group_of(n) == theme_taxonomy.MAIN]
    other = [n for n in names if n not in main]
    sections = [("Main themes", main)] if main else []
    if other:
        sections.append(("Other themes", other))
    rendered = f"The collection covers {len(names)} themes:\n\n" + "\n\n".join(
        _theme_section(label, group_names, output_format) for label, group_names in sections
    )
    return ToolResult(
        tool="list_themes", ok=True,
        data={"themes": names, "main_themes": main, "other_themes": other},
        rendered=rendered,
    )


# Candidates shown in an ambiguous clarification — enough to cover a genuine
# near-tie without dumping the whole ranked list on the user.
_AMBIGUOUS_DISPLAY_LIMIT = 3


def resolve_entity(query: str, type: str | None = None) -> ToolResult:
    """Resolve a free-text name to a ranked catalog entity. A confident top
    match accepts; a genuine near-tie asks the user to pick rather than
    silently choosing one (§4 — never guess on ambiguity); nothing plausible is
    reported explicitly as a miss, never as a misleading zero. See
    `app.retrieval.structured.resolve` for the scoring and banding this wraps."""
    from app.retrieval.structured import resolve

    try:
        candidates = resolve.resolve_entity(query, type)
    except ValueError as exc:
        return ToolResult(tool="resolve_entity", entity=type, ok=False, error=str(exc))
    except Exception:
        logger.warning("resolve_entity query failed.", exc_info=True)
        return ToolResult(tool="resolve_entity", entity=type, ok=False, error="query failed")

    label = type or "entity"
    data: dict[str, Any] = {
        "candidates": [
            {"id": c.id, "canonical_name": c.canonical_name, "type": c.type,
             "score": round(c.score, 3)}
            for c in candidates
        ]
    }
    if not candidates:
        return ToolResult(tool="resolve_entity", entity=type, ok=False, data=data,
                          error="no matching entity", error_kind="unresolved",
                          rendered=f"No {label} matching '{query}' found.")

    top = candidates[0]
    runner_up_score = candidates[1].score if len(candidates) > 1 else 0.0
    band = resolve.classify_band(top.score, runner_up_score)

    if band == resolve.MISS:
        return ToolResult(tool="resolve_entity", entity=type, ok=False, data=data,
                          error="no confident match", error_kind="unresolved",
                          rendered=f"No {label} matching '{query}' found.")

    if band == resolve.AMBIGUOUS:
        shown = candidates[:_AMBIGUOUS_DISPLAY_LIMIT]
        options = "\n".join(f"{i}. {c.canonical_name}" for i, c in enumerate(shown, start=1))
        return ToolResult(
            tool="resolve_entity", entity=type, ok=False, data=data,
            error="ambiguous match", error_kind="ambiguous",
            rendered=f"'{query}' matches more than one {label}:\n{options}\nWhich did you mean?",
        )

    data["resolved"] = {"id": top.id, "canonical_name": top.canonical_name,
                        "type": top.type, "score": round(top.score, 3)}
    return ToolResult(
        tool="resolve_entity", entity=type, ok=True, data=data,
        rendered=f"'{query}' resolves to {top.canonical_name} ({top.type}).",
    )
