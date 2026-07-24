"""Scope resolver: normalized RecordFilters -> catalog backing kwargs.

Holds the application's structured-scope business rules in one place (previously
duplicated across state, catalog, the structured answerer, and query_processor):

- theme names resolve to taxonomy term UUIDs (rename-proof, alias-aware via
  terms.resolve_terms), with a display-name theme fallback for documents
  ingested before the term catalog;
- dates are a half-open [from, to) interval;
- resolution failures degrade rather than raise.

The resolver produces kwargs the existing `state.*` catalog readers already accept,
so it consolidates the rules without touching the frozen ingestion module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.retrieval.structured.types import RecordFilters

logger = logging.getLogger(__name__)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def resolve_theme(theme: str | None) -> dict[str, Any]:
    """Theme scope: term UUIDs when the taxonomy resolves the name (rename/
    alias-proof), else the display-name theme fallback. Resolution failure
    degrades to the name fallback rather than raising."""
    if not theme:
        return {}
    try:
        from app.catalog import terms

        rows = terms.resolve_terms(theme)
    except Exception:
        logger.warning("Theme resolution failed; using name fallback.", exc_info=True)
        rows = []
    if rows:
        return {"term_uuids": [row["term_uuid"] for row in rows]}
    return {"theme": theme}


@dataclass
class ResolvedScope:
    """Backing kwargs for the state.* catalog readers, plus theme-resolution flags.

    `theme_requested` with `theme_resolved` False means the theme matched no
    taxonomy term (only the display-name fallback is available) — the count tool
    guards on this so an unresolvable theme falls through to semantic search
    instead of answering a misleading zero.
    """

    author: str | None = None
    title_contains: str | None = None
    term_uuids: list[str] | None = None
    theme: str | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    theme_requested: bool = False

    @property
    def theme_resolved(self) -> bool:
        return bool(self.term_uuids)

    def as_kwargs(self) -> dict[str, Any]:
        """Filter kwargs shared by count_documents / list_documents / distribution
        (author, theme, dates). `title_contains` is passed separately by the tools
        that use it."""
        kwargs: dict[str, Any] = {
            "author": self.author,
            "published_from": self.published_from,
            "published_to": self.published_to,
        }
        if self.term_uuids:
            kwargs["term_uuids"] = self.term_uuids
        elif self.theme:
            kwargs["theme"] = self.theme
        return {key: value for key, value in kwargs.items() if value is not None}


def resolve_filters(filters: RecordFilters) -> ResolvedScope:
    """Turn user-facing RecordFilters into catalog backing kwargs, resolving the
    theme name and parsing dates."""
    theme = resolve_theme(filters.theme)
    return ResolvedScope(
        author=filters.author or None,
        title_contains=filters.title_contains or None,
        term_uuids=theme.get("term_uuids"),
        theme=theme.get("theme"),
        published_from=_parse_date(filters.date_from),
        published_to=_parse_date(filters.date_to),
        theme_requested=bool(filters.theme),
    )
