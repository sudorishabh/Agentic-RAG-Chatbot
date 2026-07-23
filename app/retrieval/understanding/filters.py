"""Query facet → Qdrant filter construction.

Translates the scope fields of a resolved ``QueryAnalysis`` (theme, author,
tags, source type, language, date range) into Qdrant ``FieldCondition`` /
``Filter`` objects for the qa retrieval path.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.retrieval.query_processor import QueryAnalysis

logger = logging.getLogger(__name__)


def _parse_bound(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _theme_condition(theme: str) -> Any:
    """Filter for a theme scope: term UUIDs (rename-proof) OR display names —
    the name leg matches points indexed before term_ids existed. Term lookup
    failure degrades to the name-only filter rather than failing retrieval."""
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    names = {theme, theme.title()}
    uuids: list[str] = []
    try:
        from app.catalog import terms

        for row in terms.resolve_terms(theme):
            uuids.append(row["term_uuid"])
            names.add(row["name"])
    except Exception:
        logger.debug("Term resolution unavailable; theme filter by name only.",
                     exc_info=True)

    should: list[Any] = []
    if uuids:
        should.append(FieldCondition(key="theme_ids", match=MatchAny(any=uuids)))
    should.append(FieldCondition(key="categories", match=MatchAny(any=sorted(names))))
    return Filter(should=should)


def _facet_filters(analysis: "QueryAnalysis") -> list[Any]:
    from qdrant_client.models import FieldCondition, MatchAny, MatchValue

    conditions: list[Any] = []
    if analysis.theme:
        conditions.append(_theme_condition(analysis.theme))
    # `analysis.author` is intentionally NOT applied as a filter here. The stored
    # `authors` field is a KEYWORD index (exact-value match, no substring) that is
    # populated on only ~20% of chunks and holds full display names ("Ms Meena
    # Sehgal", "TERI Web Desk"). The understanding LLM extracts a loose form
    # ("TERI", "Sharma") that almost never equals a stored value, so as a hard AND
    # condition it excludes the ~80% of the corpus that has no author at all and
    # then misses the rest — turning strong matches into false refusals. Author
    # scoping stays on `analysis.author` for the structured/catalog path (which
    # LIKE-matches the MySQL facet table); the qa path relies on semantic search,
    # where author names in titles/text already surface author-relevant content.
    if analysis.tags:
        conditions.append(
            FieldCondition(key="tags", match=MatchAny(any=list(analysis.tags)))
        )
    if analysis.source_type == "pdf":
        # "PDFs" includes documents attached to web articles.
        conditions.append(
            FieldCondition(key="source_type", match=MatchAny(any=["pdf", "pdf_attachment"]))
        )
    elif analysis.source_type in ("website", "article"):
        # "website" is canonical; "article" accepted from the LLM and matched in
        # storage for points indexed before the rename.
        conditions.append(
            FieldCondition(key="source_type", match=MatchAny(any=["website", "article"]))
        )
    if analysis.language:
        conditions.append(
            FieldCondition(key="language", match=MatchValue(value=analysis.language))
        )
    lo, hi = _parse_bound(analysis.date_from), _parse_bound(analysis.date_to)
    if lo is not None or hi is not None:
        from qdrant_client.models import DatetimeRange

        conditions.append(
            FieldCondition(key="published_at", range=DatetimeRange(gte=lo, lt=hi))
        )
    return conditions
