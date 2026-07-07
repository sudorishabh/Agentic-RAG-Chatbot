from __future__ import annotations

import logging
from typing import Any, Literal, Sequence

import requests
from pydantic import BaseModel, Field

from app.config import get_settings
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
    "- limit: how many items to return for list/lookup (default 10)."
)


class StructuredQuery(BaseModel):
    operation: Operation = "list"
    bundle: str | None = None
    title_contains: str | None = None
    author: str | None = None
    year: int | None = None
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


def _bundles_for(sq: StructuredQuery) -> tuple[str, ...]:
    if sq.bundle and sq.bundle in DEFAULT_BUNDLES:
        return (sq.bundle,)
    if sq.bundle:
        return (sq.bundle,)
    return DEFAULT_BUNDLES


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


def _count(session: requests.Session, bundle: str, filters: dict[str, Any], published_only: bool) -> int:
    settings = get_settings()
    base = settings.drupal_jsonapi_base.rstrip("/")
    params: dict[str, Any] = {
        "page[limit]": settings.drupal_page_size,
        f"fields[node--{bundle}]": "drupal_internal__nid",
    }
    if published_only:
        params["filter[status]"] = 1
    params.update(filters)
    total = 0
    for data, _ in _iter_pages(session, f"{base}/node/{bundle}", params, settings.drupal_request_timeout):
        total += len(data)
    return total


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


def answer_structured(
    question: str,
    history: Sequence[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    sq = parse_structured(question, history)
    if sq is None:
        return None

    settings = get_settings()
    filters = _filter_params(sq)
    session = _build_session(settings.drupal_max_retries)
    try:
        if sq.operation == "count":
            total = 0
            for bundle in _bundles_for(sq):
                try:
                    total += _count(session, bundle, filters, True)
                except requests.RequestException:
                    logger.warning("Count failed for node/%s; skipping.", bundle, exc_info=True)
            scope = sq.bundle or "items"
            year = f" in {sq.year}" if sq.year else ""
            return {
                "answer": f"There are {total} {scope}{year} matching your query.",
                "citations": [], "intent": "structured",
                "used_chunks": 0, "conflict": False, "cached": False,
            }

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
