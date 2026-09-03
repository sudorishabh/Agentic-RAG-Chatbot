"""Which annual-report edition is this question asking for?

"Give me the latest annual report" cannot be answered by ranking, and the reason
is structural rather than a tuning problem. Every edition of the series is an
in-body attachment on one Drupal page, so all ten carry that page's
``effective_start_date`` — 2022-02-09. So:

* **relevance cannot separate them** — ten near-identical documents, and the
  breadcrumb the embedder saw names the page ("Annual Reports"), not the edition;
* **recency cannot separate them either** — "newest by date" is a ten-way tie,
  so the reranker's tie-break has nothing to break. The observed failure was
  page 148 of the 2020-21 edition, chosen by a hair of cosine noise.

The edition label is the only field that distinguishes them, and nothing read
it at query time. This module does, resolving the question to specific documents
*before* retrieval so the newest edition cannot simply be absent from the
candidate set.

Three properties keep it from disturbing anything else:

**It fails silent and returns ``[]``.** Every question that does not name the
series, or names it without saying *which* edition, resolves to ``None`` and
leaves retrieval byte-identical — including annual-report *content* questions
("what does the annual report say about solar"), which are about the series
rather than one edition of it.

**It never guesses.** An edition the corpus does not hold, a question naming
both ends ("first and latest"), or two competing series all resolve to ``None``.
A wrong scope is worse than no scope: it would answer confidently out of the
wrong document.

**A miss cannot starve retrieval.** The condition is a facet, not a date scope,
so ``retriever.retrieve`` drops it and retries unfiltered when it matches
nothing (see ``date_conditions``). The worst case is the behaviour that exists
today.

Filtering is by ``document_id`` rather than by ``edition_label``, deliberately:
the ids come from the catalogue, so the filter cannot be defeated by a label
spelled ``2023-2024`` in one store and ``2023-24`` in another.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any

from app.core.editions import EDITION_RE, find_editions, normalise_edition

logger = logging.getLogger(__name__)

__all__ = ["EditionResolution", "conditions_for", "reset_cache", "resolve"]

# The question has to name the series itself. "TERI's latest report" is not this,
# and scoping it to an annual report would answer the wrong question.
_SERIES = re.compile(r"\bannual\s+reports?\b", re.IGNORECASE)

# Asks for the single oldest edition. Distinct from the "older/past" cues in
# `_WHOLE_SERIES`: "the oldest annual report" names one document, "older annual
# reports" does not.
_EARLIEST = re.compile(r"\b(?:earliest|oldest|first)\b", re.IGNORECASE)

# Asks for the newest edition explicitly. Resolves identically to the default —
# this only decides which `kind` is recorded, so a trace distinguishes "the user
# asked for the latest" from "the user did not say and we assumed it".
_LATEST = re.compile(
    r"\b(?:latest|newest|most\s+recent|recent-?most|current|this\s+year'?s?)\b",
    re.IGNORECASE,
)

# Asks about the series as a whole — a count, a list, a trend, or older editions
# without saying which. Narrowing any of these to one edition would answer a
# different question than the one asked, so they stay unfiltered.
_WHOLE_SERIES = re.compile(
    r"\b(?:all|every|each|both|list|listing|enumerate|how\s+many|count|"
    r"number\s+of|across|throughout|over\s+the\s+years|over\s+time|trend|"
    r"trends|evolution|timeline|history|historical|year[-\s]on[-\s]year|"
    r"year[-\s]over[-\s]year|since|compare|comparison|"
    r"older|previous|prior|past|earlier|archive|archived)\b",
    re.IGNORECASE,
)

# A bare year is only read as an edition when it sits against the series name —
# "annual report 2018", "2018 annual report". Anywhere else in the sentence it is
# far more likely to be part of the subject ("what the annual report says about
# the 2015 Paris Agreement"), and reading that as an edition would silently
# answer out of the wrong document.
_YEAR_AFTER = re.compile(
    r"\bannual\s+reports?\b(?:\s+(?:for|of|from|in))?\s+(20\d{2})\b", re.IGNORECASE
)
_YEAR_BEFORE = re.compile(r"\b(20\d{2})\s+annual\s+reports?\b", re.IGNORECASE)

# How a single edition is titled in the catalogue. The title is the anchor text
# the page uses for each link ("Annual Report 2024-2025"), which is the only
# place one edition's identity exists at all — the PDFs share a page, a date and
# (for several of them) a filename that names no year.
_TITLE_PREFIX = "Annual Report%"

# The series changes only when ingestion runs, so a per-question catalogue read
# would be waste. Short enough that a newly ingested edition appears without a
# restart.
_CACHE_TTL_SECONDS = 300.0

_cache: tuple[float, dict[str, tuple[str, ...]]] | None = None


@dataclass(frozen=True)
class EditionResolution:
    """One resolved edition, and enough context to explain the choice in a log."""

    #: Canonical ``YYYY-YY``, or several joined by "+" when the question named
    #: more than one (a comparison).
    edition: str
    #: The catalogued documents for those editions.
    document_ids: tuple[str, ...]
    #: How it was chosen. ``default_latest`` is kept distinct from ``latest`` so
    #: a log line says whether the user asked for the newest edition or simply
    #: did not say which one they wanted.
    kind: str
    #: Every edition the series holds, for the log line.
    available: tuple[str, ...] = ()

    def describe(self) -> str:
        return (
            f"{self.kind} -> {self.edition} "
            f"({len(self.document_ids)} document(s); series holds "
            f"{len(self.available)}: {', '.join(self.available)})"
        )


def reset_cache() -> None:
    """Forget the cached series.

    For tests. Production does not need it: the TTL is what picks up a newly
    ingested edition, so no ingestion path has to know this cache exists.
    """
    global _cache
    _cache = None


def _read_series_rows() -> list[dict[str, Any]]:
    """Catalogued attachments whose title names an annual-report edition.

    A seam: the only function here that touches a store, so the resolution logic
    is testable without a database.

    Reads the catalogue rather than the decision table on purpose.
    ``documents_date_decision`` holds confidence scores and model verdicts and is
    documented as never being read back into retrieval; the catalogue's title is
    the same fact without the baggage.
    """
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, title, url FROM `{state_table()}` "
            "WHERE source_type = 'pdf_attachment' AND title LIKE %s",
            (_TITLE_PREFIX,),
        )
        return list(cur.fetchall())


def _series() -> dict[str, tuple[str, ...]]:
    """``{canonical edition: document ids}`` for the annual-report series.

    Grouped by the page each attachment hangs off, because "the series" is a
    page holding several editions — and the corpus contains unrelated documents
    whose titles begin the same way. The page holding the most editions wins,
    and only if it wins outright: a tie means two plausible series and no way to
    tell which one "the latest annual report" means, so nothing is resolved.
    """
    global _cache
    if _cache is not None and (time.monotonic() - _cache[0]) < _CACHE_TTL_SECONDS:
        return _cache[1]

    try:
        rows = _read_series_rows()
    except Exception:
        logger.warning(
            "Could not read the annual-report series; retrieval proceeds "
            "unfiltered.", exc_info=True,
        )
        return {}

    by_page: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        edition = normalise_edition(row.get("title"))
        if edition is None:
            continue
        page = str(row.get("url") or "")
        by_page.setdefault(page, {}).setdefault(edition, []).append(
            str(row["document_id"])
        )

    series: dict[str, tuple[str, ...]] = {}
    if by_page:
        ranked = sorted(by_page.values(), key=len, reverse=True)
        if len(ranked) == 1 or len(ranked[0]) > len(ranked[1]):
            series = {e: tuple(sorted(ids)) for e, ids in ranked[0].items()}
        else:
            logger.info(
                "Two or more pages hold %d annual-report editions each; the "
                "series is ambiguous, so no edition is resolved.", len(ranked[0]),
            )

    _cache = (time.monotonic(), series)
    return series


def _requested(
    text: str, series: dict[str, tuple[str, ...]]
) -> tuple[list[str], bool]:
    """``(editions the series holds, whether one was pointed at)``.

    The second value is what stops a silent substitution. A question naming an
    edition the corpus does not have must leave retrieval alone, not fall
    through to the newest — answering "the 2012-13 annual report" out of the
    2024-25 edition is the worst outcome available here.

    Three ways a question points at an edition, in precedence order:

    1. a canonical span — "2024-25", "2019-2020", "2020/21";
    2. a **span shape that maps to no single edition** — "2019-2024" is a period
       and "2031-32" is outside the corpus. Both point at something specific
       that is not one edition, so neither may be narrowed or defaulted;
    3. a bare year against the series name — "annual report 2018". Only here,
       never elsewhere in the sentence (see :data:`_YEAR_AFTER`).
    """
    spans = find_editions(text)
    if spans:
        return [e for e in spans if e in series], True
    if EDITION_RE.search(text) is not None:
        return [], True
    years = dict.fromkeys(_YEAR_AFTER.findall(text) + _YEAR_BEFORE.findall(text))
    if years:
        return [e for year in years
                for e in series if e.startswith(f"{year}-")], True
    return [], False


def resolve(question: str) -> EditionResolution | None:
    """The edition(s) this question is about, or None to leave retrieval alone.

    **An unqualified "annual report" resolves to the newest edition.** That is
    the intended default, and it is a correction rather than a preference: the
    editions share a title and a date, so leaving the question unscoped does not
    search them even-handedly — it lets whichever chunk scores a hair higher
    decide, which is how "the latest annual report" answered out of the 2020-21
    edition. When a user says "the annual report" they mean the current one, and
    when they mean an older one they say so.

    The question therefore has to *earn* an unfiltered search, by asking about
    the series as a whole (a count, a list, a trend, or older editions without
    naming one). Those cues are listed in :data:`_WHOLE_SERIES`.

    Lexical and deterministic throughout. This is a scope decision applied
    before search, so it must be reproducible and free — an LLM call here would
    add latency and variance to every question that mentions the series.
    """
    text = question or ""
    if not _SERIES.search(text):
        return None

    series = _series()
    if not series:
        return None

    named, pointed = _requested(text, series)
    if pointed:
        if not named:
            logger.info(
                "Question points at an annual-report edition the series does "
                "not hold as a single edition (%s); retrieval stays unfiltered "
                "rather than answering out of another one.", ", ".join(sorted(series)),
            )
            return None
        return EditionResolution(
            edition="+".join(named),
            document_ids=tuple(i for e in named for i in series[e]),
            kind="named",
            available=tuple(sorted(series)),
        )

    # No edition named. A question about the series as a whole must not be
    # narrowed to one of them; anything else defaults to the newest.
    whole = _WHOLE_SERIES.search(text)
    if whole is not None:
        logger.info(
            "Question is about the annual-report series as a whole (%r); "
            "retrieval stays unfiltered.", whole.group(0),
        )
        return None

    if _EARLIEST.search(text) is not None:
        edition, kind = min(series), "earliest"
    else:
        edition = max(series)
        kind = "latest" if _LATEST.search(text) else "default_latest"

    return EditionResolution(
        edition=edition,
        document_ids=series[edition],
        kind=kind,
        available=tuple(sorted(series)),
    )


def conditions_for(resolution: EditionResolution | None) -> list[Any]:
    """Qdrant conditions scoping retrieval to the resolved edition.

    By ``document_id``, so the scope holds regardless of how a label happens to
    be spelled in the payload. The parent page is deliberately excluded: it
    lists every edition, so admitting it re-introduces exactly the confusion the
    filter exists to remove.
    """
    if resolution is None or not resolution.document_ids:
        return []
    from qdrant_client.models import FieldCondition, MatchAny

    return [
        FieldCondition(
            key="document_id", match=MatchAny(any=list(resolution.document_ids))
        )
    ]
