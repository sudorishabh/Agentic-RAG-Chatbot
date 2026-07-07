from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal, Sequence

import requests
from pydantic import BaseModel, Field

from app.config import get_settings
from app.ingestion import state
from app.ingestion.extractors.drupal_extractor import (
    DEFAULT_BUNDLES,
    DrupalRecord,
    _build_record,
    _build_session,
    _discover_relationship_fields,
    _iter_pages,
    _site_base,
)
from app.schemas.query import Citation

logger = logging.getLogger(__name__)

Operation = Literal["lookup", "list", "count"]

_PARSE_SYSTEM = (
    "Extract structured-query parameters from the user's request about a content "
    "repository of news, articles, reports, projects, events and research papers.\n"
    "- operation: 'count' for how-many/aggregate; 'lookup' for a single specific "
    "item; 'list' for browse/enumerate.\n"
    "- bundle: the content type if implied, one of: " + ", ".join(DEFAULT_BUNDLES) +
    "; else null.\n"
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


def _bundles_for(sq: StructuredQuery) -> tuple[str, ...]:
    return (sq.bundle,) if sq.bundle else DEFAULT_BUNDLES


def _filter_params(sq: StructuredQuery) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if sq.title_contains:
        params["filter[t][condition][path]"] = "title"
        params["filter[t][condition][operator]"] = "CONTAINS"
        params["filter[t][condition][value]"] = sq.title_contains
    if sq.year:
        params["filter[ge][condition][path]"] = "created"
        params["filter[ge][condition][operator]"] = ">="
        params["filter[ge][condition][value]"] = f"{sq.year}-01-01T00:00:00"
        params["filter[lt][condition][path]"] = "created"
        params["filter[lt][condition][operator]"] = "<"
        params["filter[lt][condition][value]"] = f"{sq.year + 1}-01-01T00:00:00"
    return params


def _author_match(record: DrupalRecord, author: str) -> bool:
    needle = author.lower()
    for key, value in (record.metadata or {}).items():
        if "author" not in key.lower() and "people" not in key.lower():
            continue
        values = value if isinstance(value, (list, tuple)) else [value]
        if any(needle in str(v).lower() for v in values):
            return True
    return False


def _fetch(session: requests.Session, bundle: str, filters: dict[str, Any], *, published_only: bool, limit: int) -> list[DrupalRecord]:
    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    site = _site_base(base)
    fields = _discover_relationship_fields(session, base, bundle, published_only)
    params: dict[str, Any] = {"page[limit]": settings.drupal_page_size, "sort": "-changed"}
    if fields:
        params["include"] = ",".join(fields)
    if published_only:
        params["filter[status]"] = 1
    params.update(filters)

    out: list[DrupalRecord] = []
    for data, included in _iter_pages(session, f"{base}/node/{bundle}", params, settings.drupal_request_timeout):
        for node in data:
            out.append(_build_record(node, included, bundle, site))
            if len(out) >= limit:
                return out
    return out


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


def _answer_count(sq: StructuredQuery) -> dict[str, Any] | None:
    """Count documents from the ingested catalog by bundle, author and date."""
    lo, hi = _date_range(sq)
    try:
        total = state.count_documents(
            source_type="website",
            bundle=sq.bundle,
            author=sq.author,
            published_from=lo,
            published_to=hi,
        )
    except Exception:
        logger.warning("Catalog count failed.", exc_info=True)
        return None
    return _count_result(total, sq.bundle or "items", _period_label(sq))


def answer_structured(
    question: str,
    history: Sequence[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    sq = parse_structured(question, history)
    if sq is None:
        return None
    sq.bundle = _normalize_bundle(sq.bundle)

    settings = get_settings()
    filters = _filter_params(sq)
    session = _build_session(settings.drupal_max_retries)
    try:
        if sq.operation == "count":
            return _answer_count(sq)

        records: list[DrupalRecord] = []
        for bundle in _bundles_for(sq):
            try:
                records.extend(_fetch(session, bundle, filters, published_only=True, limit=sq.limit))
            except requests.RequestException:
                logger.warning("Fetch failed for node/%s; skipping.", bundle, exc_info=True)
            if len(records) >= sq.limit:
                break
    finally:
        session.close()

    if sq.author:
        records = [r for r in records if _author_match(r, sq.author)]
    records = records[: sq.limit]
    if not records:
        return None

    lines = [f"- {r.title} ({r.url})" if r.url else f"- {r.title}" for r in records]
    citations = [
        Citation(n=i, type="website", title=r.title, url=r.url, document_id=r.uuid or None)
        for i, r in enumerate(records, start=1)
    ]
    return {
        "answer": "Here is what I found:\n" + "\n".join(lines),
        "citations": [c.model_dump() for c in citations],
        "intent": "structured",
        "used_chunks": len(records),
        "conflict": False,
        "cached": False,
    }
