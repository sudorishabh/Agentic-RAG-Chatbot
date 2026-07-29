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


def _scope_phrase(filters: RecordFilters) -> str:
    """Human phrase naming every active filter (author, theme, tag, title,
    period) — so an answer states its own interpretation rather than a bare
    number a wrong match could hide behind. Kept in step with
    `_applied_filters`, which echoes the same set structurally.

    The bundle/content-type itself is already named as the sentence's noun (see
    `entity_label`), so it is not repeated here. Callers pass `scope.effective`,
    whose author/theme are the canonical names resolution matched — so the
    phrase names the entity actually filtered on, not the user's spelling."""
    parts = []
    if filters.author:
        parts.append(f" by {filters.author}")
    if filters.theme:
        parts.append(f" on '{filters.theme}'")
    if filters.tag:
        parts.append(f" tagged '{filters.tag}'")
    if filters.title_contains:
        parts.append(f" with '{filters.title_contains}' in the title")
    parts.append(_period_label(filters))
    return "".join(parts)


def _unresolved_miss(tool: str, entity: str | None, kind: str, value: str | None) -> ToolResult:
    """The terminal "no <kind> matching X found" result.

    Checked *after* querying, never before: a name that matching could not place
    is still used as a filter, so the query may well find rows anyway — matching
    works from the names documents carry, and it being unsure is not proof of
    absence. Only an empty result leaves "unknown name" and "genuinely no
    documents" indistinguishable, and then the miss is the honest answer."""
    return ToolResult(
        tool=tool, entity=entity, ok=False,
        error=f"{kind} did not resolve to a known entity", error_kind="unresolved",
        rendered=f"No {kind} matching '{value}' found.",
    )


def _ambiguous_result(tool: str, entity: str | None, scope: Any) -> ToolResult:
    """The terminal clarification for a filter name that matched several catalog
    entities too closely to choose between — asked, never guessed (§4)."""
    amb = scope.ambiguous
    options = "\n".join(f"{i}. {name}" for i, name in enumerate(amb.candidates, start=1))
    return ToolResult(
        tool=tool, entity=entity, ok=False,
        error=f"ambiguous {amb.kind}", error_kind="ambiguous",
        rendered=(
            f"'{amb.query}' matches more than one {amb.kind}:\n{options}\n"
            "Which did you mean?"
        ),
    )


def _scope_guard(tool: str, entity: str | None, scope: Any) -> ToolResult | None:
    """The one pre-query guard shared by the filtered tools: a name that matched
    several entities too closely to choose between. Returns None to proceed."""
    if scope.ambiguous is not None:
        return _ambiguous_result(tool, entity, scope)
    return None


def _empty_result_miss(tool: str, entity: str | None, scope: Any) -> ToolResult | None:
    """Post-query: whether an empty result should be reported as an unresolved
    name rather than a genuine zero. Returns None when every name placed, leaving
    the caller to answer an honest zero.

    Author, theme and tag are treated identically — each has its own facet table,
    so each filters by name and each can only be judged a miss once the query
    comes back empty."""
    for kind in ("author", "theme", "tag"):
        if getattr(scope, f"{kind}_missed", False):
            return _unresolved_miss(tool, entity, kind, getattr(scope.effective, kind))
    return None


def _applied_filters(bundle: str | None, filters: RecordFilters) -> dict[str, str]:
    """The filters actually in effect, keyed by name — the structured
    counterpart to `_scope_phrase`, so a caller can check the interpretation
    programmatically rather than only by reading prose. Unset filters are
    omitted rather than included as null."""
    applied = {
        "entity": bundle,
        "author": filters.author,
        "theme": filters.theme,
        "tag": filters.tag,
        "title_contains": filters.title_contains,
        "date_from": filters.date_from,
        "date_to": filters.date_to,
    }
    return {key: value for key, value in applied.items() if value}


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
    """One block of a theme listing. An empty `label` renders the bare list, for
    the case where the surrounding sentence already names what these are."""
    if output_format == "table":
        rows = "\n".join(["| theme |", "| --- |"] + [f"| {_md_cell(n)} |" for n in names])
        return f"**{label}**\n{rows}" if label else rows
    body = "\n".join(f"- {n}" for n in names)
    return f"{label}:\n{body}" if label else body


def _project_fields(
    records: list[dict[str, Any]], fields: Sequence[str] | None
) -> list[dict[str, Any]]:
    """Keep only the requested metadata keys per record. Projects the structured
    payload only — `rendered` is a natural-language answer already shaped by
    `output_format`, not a strict field projection, so a field list narrows what
    a caller reads from `data` without changing the human-readable text.

    Unknown keys are dropped rather than honored, and a list naming *only*
    unknown keys projects nothing away: an LLM-supplied field name that does not
    exist should cost the caller some extra keys, not silently empty every
    record."""
    if not fields or not records:
        return records
    allowed = {f for f in fields if f in records[0]}
    if not allowed:
        logger.warning("Ignoring unknown list_records fields %s.", sorted(set(fields)))
        return records
    return [{k: v for k, v in r.items() if k in allowed} for r in records]


# --------------------------------------------------------------------------- #
# Tools.
# --------------------------------------------------------------------------- #

def count_records(entity: str | None, filters: RecordFilters) -> ToolResult:
    """How many catalog documents match. Unknown entity returns ok=False (fall
    through, never a misleading zero). Names are canonicalized first, so the
    answer states the entity actually filtered on; a name too ambiguous to pick
    or a tag that resolves to nothing stops before querying, and an unresolved
    author/theme becomes a miss only if the query then comes back empty. A
    resolved filter matching no rows is an honest 0."""
    ent = get_entity(entity) if entity else None
    if entity and ent is None:
        return ToolResult(tool="count_records", entity=entity, ok=False,
                          error=f"unknown entity {entity!r}")
    scope = resolve_filters(filters)
    guarded = _scope_guard("count_records", entity, scope)
    if guarded is not None:
        return guarded
    bundle = ent.name if ent else None
    try:
        total = state.count_documents(
            source_type=ent.source_type if ent else "website",
            bundle=bundle,
            entity_type=ent.entity_type if ent else "node",
            title_contains=scope.title_contains,
            **scope.as_kwargs(),
        )
    except Exception:
        logger.warning("count_records query failed.", exc_info=True)
        return ToolResult(tool="count_records", entity=bundle, ok=False, error="query failed")
    if not total:
        missed = _empty_result_miss("count_records", bundle, scope)
        if missed is not None:
            return missed
    phrase = _scope_phrase(scope.effective)
    verb = "is" if total == 1 else "are"
    rendered = (
        f"There {verb} {total} {entity_label(bundle or 'items', total)}{phrase} "
        "matching your query."
    )
    return ToolResult(tool="count_records", entity=bundle, ok=True,
                      data={"count": total, "applied": _applied_filters(bundle, scope.effective)},
                      rendered=rendered)


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
    Empty result returns ok=False. Filter-resolution semantics match
    `count_records` (see `_scope_guard` / `_empty_result_miss`). `fields` narrows
    the metadata keys in `data["records"]`; `rendered` is unaffected (see
    `_project_fields`)."""
    ent = get_entity(entity) if entity else None
    if entity and ent is None:
        return ToolResult(tool="list_records", entity=entity, ok=False,
                          error=f"unknown entity {entity!r}")
    scope = resolve_filters(filters)
    guarded = _scope_guard("list_records", entity, scope)
    if guarded is not None:
        return guarded
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
        missed = _empty_result_miss("list_records", bundle, scope)
        if missed is not None:
            return missed
        return ToolResult(tool="list_records", entity=bundle, ok=False,
                          error="no matching records")
    rendered, data, citations = _render_records(records, output_format)
    return ToolResult(
        tool="list_records", entity=bundle, ok=True,
        data={"records": _project_fields(data, fields),
              "applied": _applied_filters(bundle, scope.effective)},
        citations=citations, rendered=rendered,
    )


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
    'count' aggregation is backed today. Filter-resolution semantics match
    `count_records` (see `_scope_guard` / `_empty_result_miss`)."""
    dimension, label = _GROUP_DIMENSIONS.get(group_by or "theme", ("theme", "theme"))
    ent = get_entity(entity) if entity else None
    if entity and ent is None:
        return ToolResult(tool="aggregate_records", entity=entity, ok=False,
                          error=f"unknown entity {entity!r}")
    scope = resolve_filters(filters)
    guarded = _scope_guard("aggregate_records", entity, scope)
    if guarded is not None:
        return guarded
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
        missed = _empty_result_miss("aggregate_records", bundle, scope)
        if missed is not None:
            return missed
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
        f"Distribution of {entity_label(bundle or 'items', 2)}{_scope_phrase(scope.effective)} "
        f"by {label}:\n" + body
    )
    return ToolResult(
        tool="aggregate_records", entity=bundle, ok=True,
        data={"groups": [[value, n] for value, n in rows],
              "applied": _applied_filters(bundle, scope.effective)},
        rendered=rendered,
    )


# How many themes a vocabulary enumeration may return. Deliberately NOT the
# list/lookup row limit (`ToolCall.limit`, default 10): that one answers "how
# many items should I show", while this one has to cover the whole vocabulary or
# "how many themes are there?" reports a truncated count as if it were the total.
# Callers pass this explicitly rather than relying on the default (see
# planner._tool_call) so the two limits can never be confused again.
THEME_VOCABULARY_LIMIT = 200


def list_themes(
    *,
    children: bool = False,
    parent: str | None = None,
    limit: int = THEME_VOCABULARY_LIMIT,
    output_format: str = "default",
) -> ToolResult:
    """Enumerate the collection's themes.

    Two shapes, because "theme" and "sub-theme" are different questions:

    * default — the **top-level themes only** (`theme_type='primary'`), split
      into Main themes then Other themes per the `theme_group` column. Answers
      "what themes do you cover?" / "how many themes are there?". Sub-themes are
      deliberately excluded: mixing "Air" and "Waste" in with "Climate Change"
      and "Energy" both overstates the count and flattens the hierarchy the
      taxonomy exists to express.
    * `children=True` — the **sub-themes only**, grouped under the theme each
      hangs off. `parent` narrows to one theme's children.

    Reads `documents_theme`, so it lists what documents actually carry. A theme
    whose group was never classified (`NULL`) lists under Other rather than being
    dropped. An empty result or a query failure returns ok=False so the caller can
    fall through to semantic search."""
    try:
        rows = state.theme_vocabulary(limit=limit)
    except Exception:
        logger.warning("list_themes query failed.", exc_info=True)
        return ToolResult(tool="list_themes", ok=False, error="query failed")
    if not rows:
        return ToolResult(tool="list_themes", ok=False, error="no themes found")

    if children:
        return _list_sub_themes(rows, parent, output_format)

    primary = [r for r in rows if r["theme_type"] == "primary"]
    if not primary:
        return ToolResult(tool="list_themes", ok=False, error="no themes found")
    main = [r["theme"] for r in primary if r["theme_group"] == "main"]
    other = [r["theme"] for r in primary if r["theme_group"] != "main"]
    sections = [("Main themes", main)] if main else []
    if other:
        sections.append(("Other themes", other))
    total = len(main) + len(other)
    rendered = f"The collection covers {total} themes:\n\n" + "\n\n".join(
        _theme_section(label, group_names, output_format) for label, group_names in sections
    )
    return ToolResult(
        tool="list_themes", ok=True,
        data={"themes": main + other, "main_themes": main, "other_themes": other},
        rendered=rendered,
    )


def _list_sub_themes(
    rows: list[dict[str, Any]], parent: str | None, output_format: str
) -> ToolResult:
    """The `children=True` shape of `list_themes`: sub-themes grouped by the
    theme they hang off, optionally narrowed to one parent.

    A named parent that exists but has no children answers so plainly ("Climate
    Change has no sub-themes") rather than falling through — the theme is real
    and the answer is correct, so handing the turn to semantic search would
    replace a true statement with a vague one. A parent that is not a theme at
    all is a miss, which is a different thing."""
    subs = [r for r in rows if r["theme_type"] == "sub" and r["parent"]]

    if parent:
        wanted = parent.casefold()
        mine = [r for r in subs if (r["parent"] or "").casefold() == wanted]
        if not mine:
            known = next(
                (r["theme"] for r in rows if r["theme"].casefold() == wanted), None
            )
            if known is None:
                return _unresolved_miss("list_themes", None, "theme", parent)
            return ToolResult(
                tool="list_themes", ok=True,
                data={"parent": known, "sub_themes": [], "by_parent": {}},
                rendered=f"{known} has no sub-themes.",
            )
        names = [r["theme"] for r in mine]
        body = _theme_section("", names, output_format)
        rendered = f"{mine[0]['parent']} has {len(names)} sub-themes:\n{body}"
        return ToolResult(
            tool="list_themes", ok=True,
            data={"parent": mine[0]["parent"], "sub_themes": names,
                  "by_parent": {mine[0]["parent"]: names}},
            rendered=rendered,
        )

    if not subs:
        return ToolResult(tool="list_themes", ok=False, error="no sub-themes found")
    by_parent: dict[str, list[str]] = {}
    for row in subs:
        by_parent.setdefault(row["parent"], []).append(row["theme"])
    names = [name for group in by_parent.values() for name in group]
    rendered = f"The collection covers {len(names)} sub-themes:\n\n" + "\n\n".join(
        _theme_section(theme, children, output_format)
        for theme, children in by_parent.items()
    )
    return ToolResult(
        tool="list_themes", ok=True,
        data={"sub_themes": names, "by_parent": by_parent, "parent": None},
        rendered=rendered,
    )


def resolve_entity(query: str | None, type: str | None = None) -> ToolResult:
    """Resolve a free-text name to a ranked catalog entity. A confident top
    match accepts; a genuine near-tie asks the user to pick rather than
    silently choosing one (§4 — never guess on ambiguity); nothing plausible is
    reported explicitly as a miss, never as a misleading zero. See
    `app.retrieval.structured.resolve` for the scoring and banding this wraps."""
    from app.retrieval.structured import resolve

    if not query or not query.strip():
        # `ToolCall.query` defaults to None, so a planned call that omits it
        # reaches here — fall through rather than rendering the missing value
        # into a user-facing "No entity matching 'None' found."
        return ToolResult(tool="resolve_entity", entity=type, ok=False,
                          error="no query to resolve")
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
        shown = resolve.plausible(candidates)
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
