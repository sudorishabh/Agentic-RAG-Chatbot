"""Query facet → Qdrant filter construction.

Translates the scope fields of a resolved ``QueryAnalysis`` (theme, author,
tags, source type, language, date range) into Qdrant ``FieldCondition`` /
``Filter`` objects for the qa retrieval path.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.core.dates import parse_iso_date

if TYPE_CHECKING:
    from app.retrieval.query_processor import QueryAnalysis

logger = logging.getLogger(__name__)


def _parse_bound(value: str | None, *, field: str = "date") -> datetime | None:
    """A Qdrant date bound: UTC-aware, unlike the naive datetimes the MySQL
    catalog takes. `DatetimeRange` compares against tz-aware payload values, so
    the zone has to be attached here."""
    parsed = parse_iso_date(value, field=field)
    return parsed.replace(tzinfo=timezone.utc) if parsed else None


def _theme_condition(theme: str) -> Any:
    """Filter for a theme scope, by display name.

    Qdrant payloads carry `categories` (theme names) alongside `theme_ids`; the
    catalog is keyed by name now, so the name leg is the whole filter — there is
    no MySQL term table to translate a name into UUIDs. Casing variants are
    ORed because payloads store whatever the CMS supplied."""
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    names = sorted({theme, theme.title(), theme.strip()})
    return Filter(should=[FieldCondition(key="categories", match=MatchAny(any=names))])


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
    lo = _parse_bound(analysis.date_from, field="date_from")
    hi = _parse_bound(analysis.date_to, field="date_to")
    if lo is not None or hi is not None:
        from qdrant_client.models import DatetimeRange

        conditions.append(
            FieldCondition(key="published_at", range=DatetimeRange(gte=lo, lt=hi))
        )
    return conditions
