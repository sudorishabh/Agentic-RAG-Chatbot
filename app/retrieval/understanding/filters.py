"""Query facet → Qdrant filter construction.

Translates the scope fields of a resolved ``QueryAnalysis`` (theme, author,
tags, source type, language, date range) into Qdrant ``FieldCondition`` /
``Filter`` objects for the qa retrieval path.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Sequence

from app.core.dates import parse_iso_date

if TYPE_CHECKING:
    from app.retrieval.query_processor import QueryAnalysis

logger = logging.getLogger(__name__)

# The payload field every date scope is expressed over. Named once so the
# condition builder and `date_conditions` cannot drift apart.
_DATE_FIELD = "published_at"

# Words that make a date phrase about *documents* rather than about a
# relationship. "Reports published between 2005 and 2010" is a publication-date
# scope; "what did X fund between 2005 and 2010" is not.
_PUBLICATION_LANGUAGE = re.compile(
    r"\b(?:publish(?:ed|ing)?|publication|issued|released|"
    r"(?:document|report|paper|article|study|studies|publication)s?\s+"
    r"(?:from|in|of|between|dated)|dated)\b",
    re.IGNORECASE,
)


def _is_relationship_time(analysis: "QueryAnalysis") -> bool:
    """Whether this query's dates bound a *relationship*, not a publication date.

    Both readings arrive here as the same two slots. Applying the document
    reading to the other one is not a near miss: `published_at` is a fact about
    when a page was posted, and on this corpus it holds no value before 2010 at
    all, so scoping "what did the Department of Biotechnology fund between 2005
    and 2010" by it selects almost nothing. It also carries a second cost — a
    scope no graph template expresses makes graph routing fail closed
    (`graph.scope`), so the one path that *can* answer a validity question by
    interval overlap is the path the misreading shuts off. Measured: every
    year-range relational question in the benchmark reached
    `scope_unsupported`.

    The test is deterministic and narrow: the question names an approved
    predicate, and says nothing about publishing. A predicate cue is what makes
    "between 2005 and 2010" modify a relationship — there is one to modify.
    Anything else keeps the existing document scope exactly as it was, which is
    why "which documents were published between 2005 and 2010" is untouched.
    """
    from app.retrieval.understanding.relational import read_relational

    question = getattr(analysis, "search_query", "") or ""
    if not question or _PUBLICATION_LANGUAGE.search(question):
        return False
    return read_relational(question).is_relational


def _parse_bound(value: str | None, *, field: str = "date") -> datetime | None:
    """A Qdrant date bound: UTC-aware, unlike the naive datetimes the MySQL
    catalog takes. `DatetimeRange` compares against tz-aware payload values, so
    the zone has to be attached here."""
    parsed = parse_iso_date(value, field=field)
    return parsed.replace(tzinfo=timezone.utc) if parsed else None


def _theme_condition(theme: str) -> Any:
    """Filter for a theme scope, by display name.

    Qdrant payloads carry `categories` (theme names); the catalog is keyed by
    name, so the name leg is the whole filter — there is no MySQL term table to
    translate a name into UUIDs. Casing variants are ORed because payloads store
    whatever the CMS supplied."""
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
    if (lo is not None or hi is not None) and not _is_relationship_time(analysis):
        from qdrant_client.models import DatetimeRange

        conditions.append(
            FieldCondition(key=_DATE_FIELD, range=DatetimeRange(gte=lo, lt=hi))
        )
    return conditions


def date_conditions(filters: Sequence[Any] | None) -> list[Any]:
    """The subset of ``filters`` that bounds the publication date.

    Lets ``retriever.retrieve`` hold the date scope while dropping the rest on a
    total miss. The distinction is who chose the constraint: theme, author and
    source_type are the understanding LLM's guesses at how the corpus happens to
    be labelled, so discarding them recovers from a bad guess. A period is what
    the user actually asked for, and widening it answers about years they did not
    ask about — silently, because the retry is recorded on the trace span and the
    log, never in the answer text.

    Tolerates entries that aren't ``FieldCondition``s (a nested ``Filter``, as
    ``_theme_condition`` returns) by matching on the attribute rather than the
    type."""
    return [c for c in filters or [] if getattr(c, "key", None) == _DATE_FIELD]
