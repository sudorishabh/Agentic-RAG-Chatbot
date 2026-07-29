"""Scope resolver: normalized RecordFilters -> catalog backing kwargs.

Holds the application's structured-scope business rules in one place (previously
duplicated across state, catalog, the structured answerer, and query_processor):

- free-text author/theme names are canonicalized by fuzzy matching (see
  `_resolve_name`) before any lookup, so a misspelling filters on the name the
  catalog actually stores;
- theme names resolve to taxonomy term UUIDs (rename-proof, alias-aware via
  terms.resolve_terms), with a display-name theme fallback for documents
  ingested before the term catalog;
- dates are a half-open [from, to) interval;
- resolution failures degrade rather than raise.

Canonicalization happens **here**, not in a separate planner step, because the
plan's tool calls execute in parallel with no data flow between them — a
`resolve_entity` call could never hand its result to a sibling `count_records`.
Resolving on the way to SQL instead means every tool benefits regardless of how
the plan is shaped. `tools.resolve_entity` remains for the one thing this path
cannot do: asking the user which of several close matches they meant.

The resolver produces kwargs the existing `state.*` catalog readers already accept,
so it consolidates the rules without touching the frozen ingestion module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from app.config import get_settings
from app.retrieval.structured.types import RecordFilters

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AmbiguousFilter:
    """A filter whose name matched several catalog entities closely enough that
    picking one would be a guess. Surfaced by the tools as a clarification
    question instead of being silently resolved to the top hit (§4)."""

    kind: str
    query: str
    candidates: list[str]


def _resolve_name(kind: str, value: str | None) -> tuple[str | None, str | None, AmbiguousFilter | None]:
    """Canonicalize a free-text entity name against what the catalog stores.

    Returns ``(name to filter on, band, ambiguity)``. The name degrades to the
    user's own string on anything but a confident single match, so filtering
    still happens — a fuzzy miss is not the same as no filter, and the caller
    decides what an empty result then means. ``band`` is None when resolution
    was skipped (feature disabled or the lookup failed), which callers treat as
    "no opinion" rather than as a miss.
    """
    if not value:
        return None, None, None
    if not get_settings().entity_resolution_enabled:
        return value, None, None
    from app.retrieval.structured import resolve

    try:
        candidates = resolve.resolve_entity(value, kind)
    except Exception:
        logger.warning(
            "%s name resolution failed; filtering on the name as typed.", kind, exc_info=True
        )
        return value, None, None
    if not candidates:
        return value, resolve.MISS, None
    top = candidates[0]
    runner_up = candidates[1].score if len(candidates) > 1 else 0.0
    band = resolve.classify_band(top.score, runner_up)
    if band == resolve.ACCEPT:
        return top.canonical_name, band, None
    if band == resolve.AMBIGUOUS:
        return value, band, AmbiguousFilter(
            kind=kind, query=value,
            candidates=[c.canonical_name for c in resolve.plausible(candidates)],
        )
    return value, band, None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def resolve_tag(tag: str | None) -> dict[str, Any]:
    """Tag scope: term UUIDs when the taxonomy resolves the name, else the
    display-name fallback. Unlike themes, tags have no free-text facet table and
    no subtree to expand — the `tags` vocabulary is a flat, freeform CMS list
    (see docs/database-retrieval-redesign.md §4.1/§5), so a name that does not
    resolve degrades to the display-name dict same as `resolve_theme`, but that
    fallback has no matching column to filter on until a taxonomy-scoped crawl
    populates `terms`. Resolution failure degrades to the name fallback rather
    than raising."""
    if not tag:
        return {}
    try:
        from app.catalog import terms
        from app.catalog.schema import TAG_VOCABULARY

        rows = terms.resolve_terms(tag, vocabulary=TAG_VOCABULARY)
    except Exception:
        logger.warning("Tag resolution failed; using name fallback.", exc_info=True)
        return {"tag": tag}
    if not rows:
        return {"tag": tag}
    return {"tag_uuids": [row["term_uuid"] for row in rows]}


def resolve_theme(theme: str | None) -> dict[str, Any]:
    """Theme scope: term UUIDs when the taxonomy resolves the name (rename/
    alias-proof), expanded to descendant sub-themes so a parent theme also
    counts documents tagged only with a child; else the display-name theme
    fallback. Resolution failure degrades to the name fallback rather than
    raising."""
    if not theme:
        return {}
    try:
        from app.catalog import terms

        rows = terms.resolve_terms(theme)
    except Exception:
        logger.warning("Theme resolution failed; using name fallback.", exc_info=True)
        return {"theme": theme}
    if not rows:
        return {"theme": theme}
    uuids = [row["term_uuid"] for row in rows]
    try:
        uuids = terms.descendant_uuids(uuids)
    except Exception:
        logger.warning(
            "Theme descendant expansion failed; scoping to matched terms only.",
            exc_info=True,
        )
    return {"term_uuids": uuids}


@dataclass
class ResolvedScope:
    """Backing kwargs for the state.* catalog readers, plus resolution flags.

    `theme_requested` with `theme_resolved` False means the theme matched no
    taxonomy term, so only the display-name fallback filtered the query — the
    tools treat an *empty* result in that state as a miss (a non-empty one is a
    real answer). `tag_requested`/`tag_resolved` are the tag equivalent, but
    tags have no display-name fallback table (see resolve_tag), so an unresolved
    tag is guarded before querying at all.

    `effective` is the same filter set with canonical names substituted for what
    the user typed — the tools render and echo from it, so an answer states the
    entity it actually filtered on rather than the misspelling. `ambiguous` is
    set when a name matched several entities too closely to choose between;
    `author_missed` when fuzzy matching found nothing plausible for an author.
    """

    author: str | None = None
    title_contains: str | None = None
    term_uuids: list[str] | None = None
    theme: str | None = None
    tag_uuids: list[str] | None = None
    tag: str | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    theme_requested: bool = False
    tag_requested: bool = False
    effective: RecordFilters = field(default_factory=RecordFilters)
    ambiguous: AmbiguousFilter | None = None
    author_missed: bool = False

    @property
    def theme_resolved(self) -> bool:
        return bool(self.term_uuids)

    @property
    def tag_resolved(self) -> bool:
        return bool(self.tag_uuids)

    def as_kwargs(self) -> dict[str, Any]:
        """Filter kwargs shared by count_documents / list_documents / distribution
        (author, theme, tag, dates). `title_contains` is passed separately by the
        tools that use it. `tag` (the unresolved display name) never appears here
        — unlike theme, there is no facet column to filter tag on by name, so a
        caller must guard on `tag_requested and not tag_resolved` before querying
        at all (see docs/database-retrieval-redesign.md §4.1)."""
        kwargs: dict[str, Any] = {
            "author": self.author,
            "published_from": self.published_from,
            "published_to": self.published_to,
        }
        if self.term_uuids:
            kwargs["term_uuids"] = self.term_uuids
        elif self.theme:
            kwargs["theme"] = self.theme
        if self.tag_uuids:
            kwargs["tag_uuids"] = self.tag_uuids
        return {key: value for key, value in kwargs.items() if value is not None}


def resolve_filters(filters: RecordFilters) -> ResolvedScope:
    """Turn user-facing RecordFilters into catalog backing kwargs: canonicalize
    the author and theme names, resolve theme/tag to taxonomy UUIDs, parse dates.

    Author and theme are canonicalized first so the lookups below run against the
    name the catalog stores rather than the user's spelling. Tags are not — they
    are matched exactly (see `resolve_tag` and
    docs/database-retrieval-redesign.md §3 on why tag is not fuzzy-resolved).
    """
    from app.retrieval.structured import resolve as _resolve

    author, author_band, author_ambiguous = _resolve_name(_resolve.AUTHOR, filters.author)
    theme_name, _theme_band, theme_ambiguous = _resolve_name(_resolve.THEME, filters.theme)
    theme = resolve_theme(theme_name)
    tag = resolve_tag(filters.tag)
    return ResolvedScope(
        author=author,
        title_contains=filters.title_contains or None,
        term_uuids=theme.get("term_uuids"),
        theme=theme.get("theme"),
        tag_uuids=tag.get("tag_uuids"),
        tag=tag.get("tag"),
        published_from=_parse_date(filters.date_from),
        published_to=_parse_date(filters.date_to),
        theme_requested=bool(filters.theme),
        tag_requested=bool(filters.tag),
        effective=replace(filters, author=author, theme=theme_name),
        # Only one clarification is asked at a time; author first because a
        # person's name is the more common source of a genuine near-tie.
        ambiguous=author_ambiguous or theme_ambiguous,
        author_missed=author_band == _resolve.MISS,
    )
