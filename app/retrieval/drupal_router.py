from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Sequence

from pydantic import BaseModel, Field

from app.ingestion import state, terms
from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES
from app.schemas.query import Citation

if TYPE_CHECKING:
    from app.retrieval.query_processor import QueryAnalysis

logger = logging.getLogger(__name__)

Operation = Literal["lookup", "list", "count", "distribution"]
GroupBy = Literal["theme", "content_type", "author", "year"]

_PARSE_SYSTEM = (
    "Extract structured-query parameters from the user's request about a content "
    "repository of news, articles, reports, projects, events and research papers.\n"
    "- operation: 'count' for how-many/aggregate; 'distribution' for a breakdown "
    "per group ('how many per theme', 'spread across content types'); 'lookup' "
    "for a single specific item; 'list' for browse/enumerate.\n"
    "- bundle: the content type if implied, one of: " + ", ".join(DEFAULT_BUNDLES) +
    "; else null.\n"
    "- theme: the thematic area / topic / category name if the request is scoped "
    "to one (e.g. 'under the Climate theme', 'in the Energy area'); else null.\n"
    "- group_by: for 'distribution' only — the dimension to break down by: "
    "'theme', 'content_type', 'author', or 'year'; else null.\n"
    "- title_contains: a title keyword if the user names/quotes a title; else null.\n"
    "- author: an author/person name if specified; else null.\n"
    "- year: a four-digit year if a specific year is referenced; else null.\n"
    "- date_from / date_to: an inclusive start and exclusive end ISO date "
    "(YYYY-MM-DD) bounding any date or period mentioned. For a single day set "
    "date_from to that day and date_to to the next day; for a month or year span "
    "it; for 'since'/'after' set only date_from; for 'before'/'until' set only "
    "date_to; else both null.\n"
    "- limit: how many items to return for list/lookup (default 10)."
)


class StructuredQuery(BaseModel):
    operation: Operation = "list"
    bundle: str | None = None
    theme: str | None = None
    group_by: GroupBy | None = None
    title_contains: str | None = None
    author: str | None = None
    year: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    limit: int = 10


def parse_structured(question: str, history: Sequence[dict[str, str]] | None = None) -> StructuredQuery | None:
    from app.generation.llm_client import get_structured_llm

    convo = ""
    if history:
        convo = "\n".join(f"{t.get('role')}: {t.get('content')}" for t in list(history)[-4:])
    try:
        model = get_structured_llm().with_structured_output(StructuredQuery)
        return model.invoke(
            [
                ("system", _PARSE_SYSTEM),
                ("human", f"Conversation:\n{convo}\n\nRequest: {question}"),
            ]
        )
    except Exception:
        logger.warning("Structured-query parse failed.", exc_info=True)
        return None


# Free-text content types the LLM may emit that regular plural/singular matching
# won't map to a known bundle (e.g. "person" -> "people").
_BUNDLE_SYNONYMS: dict[str, str] = {
    "person": "people",
    "paper": "research_papers",
    "policy": "policy_brief",
    "brief": "policy_brief",
    "news_article": "news",
    "press": "press_release",
}


def _normalize_bundle(raw: str | None) -> str | None:
    """Map a free-text content type ('event', 'press release') to a known bundle.
    Falls back to the cleaned key so an unknown type counts as zero, not as all."""
    if not raw:
        return None
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in DEFAULT_BUNDLES:
        return key
    for variant in (f"{key}s", key.rstrip("s")):
        if variant in DEFAULT_BUNDLES:
            return variant
    return _BUNDLE_SYNONYMS.get(key) or _BUNDLE_SYNONYMS.get(key.rstrip("s"), key)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _date_range(sq: StructuredQuery) -> tuple[datetime | None, datetime | None]:
    """Half-open ``[from, to)`` bounds from explicit dates, falling back to the
    whole calendar year when only ``year`` is given."""
    lo, hi = _parse_date(sq.date_from), _parse_date(sq.date_to)
    if lo is None and hi is None and sq.year:
        return datetime(sq.year, 1, 1), datetime(sq.year + 1, 1, 1)
    return lo, hi


def _period_label(sq: StructuredQuery) -> str:
    lo, hi = _parse_date(sq.date_from), _parse_date(sq.date_to)
    # A whole-calendar-year range reads better as "in YYYY" than as raw bounds
    # (the LLM often expands "in 2024" to 2024-01-01 .. 2025-01-01).
    if lo and hi and (lo.month, lo.day) == (1, 1) and hi == datetime(lo.year + 1, 1, 1):
        return f" in {lo.year}"
    if sq.year and not sq.date_from and not sq.date_to:
        return f" in {sq.year}"
    if sq.date_from and sq.date_to:
        return f" between {sq.date_from} and {sq.date_to}"
    if sq.date_from:
        return f" since {sq.date_from}"
    if sq.date_to:
        return f" before {sq.date_to}"
    return ""


# Display (singular, plural) forms for the count answer. Bundle names are
# inconsistently pluralized ("events" vs "report" vs "news"), so map the known
# ones; anything else gets a humanized best-effort.
_BUNDLE_LABELS: dict[str, tuple[str, str]] = {
    "news": ("news item", "news items"),
    "events": ("event", "events"),
    "feature_articles": ("feature article", "feature articles"),
    "completed_projects": ("completed project", "completed projects"),
    "ongoing_projects": ("ongoing project", "ongoing projects"),
    "press_release": ("press release", "press releases"),
    "research_papers": ("research paper", "research papers"),
    "policy_brief": ("policy brief", "policy briefs"),
    "videos": ("video", "videos"),
    "infographics": ("infographic", "infographics"),
    "services": ("service", "services"),
    "people": ("person", "people"),
    "article": ("article", "articles"),
    "report": ("report", "reports"),
    "page": ("page", "pages"),
    "carousel": ("carousel", "carousels"),
    "items": ("item", "items"),
}


def _scope_label(scope: str, n: int) -> str:
    forms = _BUNDLE_LABELS.get(scope)
    if forms:
        return forms[0] if n == 1 else forms[1]
    human = scope.replace("_", " ")
    if n == 1:
        return human[:-1] if human.endswith("s") else human
    return human if human.endswith("s") else f"{human}s"


def _count_result(total: int, scope: str, period: str) -> dict[str, Any]:
    verb = "is" if total == 1 else "are"
    return {
        "answer": f"There {verb} {total} {_scope_label(scope, total)}{period} matching your query.",
        "citations": [],
        "intent": "structured",
        "used_chunks": 0,
        "conflict": False,
        "cached": False,
    }


def _theme_scope(sq: StructuredQuery) -> dict[str, Any]:
    """Catalog filter kwargs for a theme scope. Term UUIDs when the term
    catalog resolves the name (rename/alias-proof); otherwise the display-name
    category fallback covers documents ingested before the term catalog."""
    if not sq.theme:
        return {}
    try:
        rows = terms.resolve_terms(sq.theme)
    except Exception:
        logger.warning("Theme resolution failed; using name fallback.", exc_info=True)
        rows = []
    if rows:
        return {"term_uuids": [r["term_uuid"] for r in rows]}
    return {"category": sq.theme}


def _answer_count(sq: StructuredQuery) -> dict[str, Any] | None:
    """Count documents from the ingested catalog by bundle, theme, author, date.

    Guards against misrouted content questions: an unknown content type or a
    theme the term catalog cannot resolve would count as a misleading "0 items",
    so those return None and fall through to semantic search instead. A count
    with no dimensions at all is a genuine corpus-size question and still
    answers the total.
    """
    if sq.bundle and sq.bundle not in DEFAULT_BUNDLES:
        return None
    scope = _theme_scope(sq)
    if sq.theme and not scope.get("term_uuids"):
        return None
    lo, hi = _date_range(sq)
    try:
        total = state.count_documents(
            source_type="website",
            bundle=sq.bundle,
            entity_type="node",  # facet terms/blocks are not content documents
            author=sq.author,
            published_from=lo,
            published_to=hi,
            **scope,
        )
    except Exception:
        logger.warning("Catalog count failed.", exc_info=True)
        return None
    scope = f" on '{sq.theme}'" if sq.theme else ""
    return _count_result(total, sq.bundle or "items", scope + _period_label(sq))


def _md_cell(text: str) -> str:
    """'|' inside a value would break the markdown table row."""
    return text.replace("|", "\\|")


def _render_list_table(records: Sequence[state.StateRecord]) -> str:
    lines = ["| Title | Published | Type |", "| --- | --- | --- |"]
    for r in records:
        title = _md_cell(r.title or r.document_id)
        cell = f"[{title}]({r.url})" if r.url else title
        lines.append(f"| {cell} | {(r.published_at or '')[:10]} | {r.bundle or ''} |")
    return "\n".join(lines)


def _render_list_timeline(records: Sequence[state.StateRecord]) -> str:
    """Year-grouped chronology. Expects records already sorted newest-first;
    ISO published_at strings slice cleanly: [:4] year, [:7] YYYY-MM."""
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


def _answer_list(sq: StructuredQuery, answer_format: str = "default") -> dict[str, Any] | None:
    """Answer a list/lookup from the ingested catalog (no live site fetch)."""
    lo, hi = _date_range(sq)
    try:
        records = state.list_documents(
            source_type="website",
            bundle=sq.bundle,
            entity_type="node",
            title_contains=sq.title_contains,
            author=sq.author,
            published_from=lo,
            published_to=hi,
            limit=sq.limit,
            **_theme_scope(sq),
        )
    except Exception:
        logger.warning("Catalog list failed.", exc_info=True)
        return None
    if not records:
        return None

    if answer_format == "timeline":
        # ISO dates order lexicographically; undated rows sink to the end.
        # Citations below follow the same rendered order.
        records = sorted(records, key=lambda r: r.published_at or "", reverse=True)
        body = _render_list_timeline(records)
    elif answer_format == "table":
        body = _render_list_table(records)
    else:
        body = "\n".join(
            f"- {r.title} ({r.url})" if r.url else f"- {r.title or r.document_id}"
            for r in records
        )
    citations = [
        Citation(n=i, type="website", title=r.title, url=r.url, document_id=r.document_id or None)
        for i, r in enumerate(records, start=1)
    ]
    return {
        "answer": "Here is what I found:\n" + body,
        "citations": [c.model_dump() for c in citations],
        "intent": "structured",
        "used_chunks": len(records),
        "conflict": False,
        "cached": False,
    }


# StructuredQuery.group_by -> state.distribution dimension and answer label.
_GROUP_DIMENSIONS: dict[str, tuple[str, str]] = {
    "theme": ("category", "theme"),
    "content_type": ("bundle", "content type"),
    "author": ("author", "author"),
    "year": ("year", "year"),
}


def _answer_distribution(
    sq: StructuredQuery, answer_format: str = "default"
) -> dict[str, Any] | None:
    """Break down catalog counts per theme/content type/author/year."""
    dimension, label = _GROUP_DIMENSIONS[sq.group_by or "theme"]
    lo, hi = _date_range(sq)
    try:
        rows = state.distribution(
            dimension,
            source_type="website",
            bundle=sq.bundle,
            entity_type="node",
            published_from=lo,
            published_to=hi,
        )
    except Exception:
        logger.warning("Catalog distribution failed.", exc_info=True)
        return None
    if not rows:
        return None

    if answer_format == "table":
        body = "\n".join(
            [f"| {label} | count |", "| --- | --- |"]
            + [f"| {_md_cell(str(value))} | {n} |" for value, n in rows]
        )
    else:
        body = "\n".join(f"- {value}: {n}" for value, n in rows)
    scope = _scope_label(sq.bundle or "items", 2)
    return {
        "answer": f"Distribution of {scope}{_period_label(sq)} by {label}:\n" + body,
        "citations": [],
        "intent": "structured",
        "used_chunks": 0,
        "conflict": False,
        "cached": False,
    }


def _query_from_analysis(analysis: QueryAnalysis) -> StructuredQuery:
    """Map the unified analysis onto the router's query model. The unified
    prompt emits explicit date bounds, so ``year`` stays unset (the field is
    kept on StructuredQuery for direct ``parse_structured`` callers)."""
    return StructuredQuery(
        operation=analysis.operation or "list",
        bundle=analysis.bundle,
        theme=analysis.theme,
        group_by=analysis.group_by,
        title_contains=analysis.title_contains,
        author=analysis.author,
        date_from=analysis.date_from,
        date_to=analysis.date_to,
        limit=analysis.limit,
    )


# Words signalling the user wants what a document SAYS, not just its catalog
# entry ("show/find the article titled X" browses; "what does X say" reads).
_CONTENT_QUESTION = re.compile(
    r"\b(what|how|why|when|where|who|does|do|did|is|are|was|were"
    r"|explain|describe|summar\w*|tell)\b",
    re.IGNORECASE,
)


def resolve_lookup_document(
    analysis: QueryAnalysis | None, question: str
) -> str | None:
    """Document id for a title lookup that should chain into content QA.

    Chains only when the lookup names a title, the question asks about
    content (summary/detailed format or an interrogative in the question),
    and the catalog matches exactly one document — ambiguity or errors fall
    back to the plain lookup-list behavior (None).
    """
    if analysis is None or analysis.operation != "lookup" or not analysis.title_contains:
        return None
    if analysis.answer_format not in ("summary", "detailed") and not _CONTENT_QUESTION.search(question):
        return None
    try:
        records = state.list_documents(
            source_type="website",
            entity_type="node",
            title_contains=analysis.title_contains,
            limit=3,
        )
    except Exception:
        logger.warning("Lookup resolution failed.", exc_info=True)
        return None
    if len(records) != 1 or not records[0].document_id:
        return None
    return records[0].document_id


def answer_structured(
    question: str,
    history: Sequence[dict[str, str]] | None = None,
    *,
    analysis: QueryAnalysis | None = None,
) -> dict[str, Any] | None:
    # The unified analysis already extracted the structured slots — reuse it
    # instead of a second LLM parse; parse only when no usable analysis came.
    if analysis is not None and analysis.operation:
        sq = _query_from_analysis(analysis)
    else:
        sq = parse_structured(question, history)
    if sq is None:
        return None
    answer_format = analysis.answer_format if analysis is not None else "default"
    sq.bundle = _normalize_bundle(sq.bundle)
    if sq.operation == "count":
        return _answer_count(sq)
    if sq.operation == "distribution":
        return _answer_distribution(sq, answer_format)
    return _answer_list(sq, answer_format)
