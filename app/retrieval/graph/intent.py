"""What a question asks of the graph: which relationship, and over what time.

Split out of the router because the two questions are independent. *Which
predicate* a question is about is a matter of vocabulary; *when* it is asking
about is a matter of tense and dates. The router used to answer both at once
with one regex table mapping question shapes straight onto template ids, which
is why adding a predicate meant adding a route.

Here, both answers are values:

    "who led Project X in 2015"  ->  Relational(LED_BY)  Temporal(as_of, 2015)
    "who currently funds X"      ->  Relational(FUNDED_BY) Temporal(current)
    "TERI's partners since 2010" ->  Relational(PARTNER_OF) Temporal(since 2010)

Neither reaches Cypher. The predicate is looked up in the closed vocabulary and
travels as a bound ``$predicate`` *value*; the window travels as two bound ISO
date strings. Nothing here can name a label or a relationship type.

Predicate cues
--------------
Each approved predicate declares the words this corpus actually uses for it.
The cues live beside the vocabulary rather than in a route table, so an approved
predicate becomes askable by declaring how people say it — not by adding a
branch to a router.

Temporal reading
----------------
Five readings, in the order they are tried. The order is precedence, not
convenience: an explicit interval is a stronger statement of intent than a bare
tense, so "who has historically led X since 2010" is a range question.

``range``        an explicit interval: "between 2017 and 2019", "since 2010",
                 "before 2015", "after 2018".
``as_of``        a single instant: "in 2015", "as of 2015-06-03".
``history``      the past, or the whole sequence: "used to", "leadership history".
``current``      the present: "currently", "now", "the current leader".
``unspecified``  no temporal language at all.

``unspecified`` is deliberately its own reading rather than being folded into
either ``current`` or ``history``. See :mod:`app.retrieval.graph.plans` for what
is done with it, and why guessing either way would be wrong.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Temporal readings
# --------------------------------------------------------------------------- #

TEMPORAL_CURRENT = "current"
TEMPORAL_AS_OF = "as_of"
TEMPORAL_RANGE = "range"
TEMPORAL_HISTORY = "history"
TEMPORAL_UNSPECIFIED = "unspecified"

TEMPORAL_KINDS = (
    TEMPORAL_CURRENT, TEMPORAL_AS_OF, TEMPORAL_RANGE,
    TEMPORAL_HISTORY, TEMPORAL_UNSPECIFIED,
)

# A year in a question. 1800-2099, which is wide enough that no relationship
# this corpus could record is out of reach and narrow enough that a bare
# four-digit quantity ("1030 projects") is not read as a date.
#
# This is a bound on what a *question* can express, never on what a *claim* may
# assert. There is deliberately no floor below which a relationship is
# considered too old to retrieve; see the module note in `plans`.
_YEAR = r"(?:18|19|20)\d{2}"
_ISO = r"\d{4}-\d{2}-\d{2}"


@dataclass(frozen=True)
class TemporalIntent:
    """When a question is asking about, as a half-open ``[start, end)`` window.

    ``None`` on either bound means unbounded on that side. Both ``None`` means
    no temporal filter at all — every claim about the subject, whenever it held.
    """

    kind: str = TEMPORAL_UNSPECIFIED
    window_start: str | None = None
    window_end: str | None = None
    phrase: str = ""

    @property
    def is_current(self) -> bool:
        return self.kind == TEMPORAL_CURRENT

    @property
    def is_bounded(self) -> bool:
        return self.window_start is not None or self.window_end is not None

    def describe(self) -> str:
        if not self.is_bounded:
            return self.kind
        return f"{self.kind}[{self.window_start or '-'}..{self.window_end or '-'})"


def _year_start(year: int) -> str:
    return f"{year:04d}-01-01"


def _day_after(value: str) -> str:
    """The day after an ISO date, so a point in time becomes a half-open day."""
    try:
        return (date.fromisoformat(value) + timedelta(days=1)).isoformat()
    except ValueError:  # pragma: no cover - the regex already constrains this
        return value


# --- explicit intervals ---------------------------------------------------- #
# Tried in order. Each yields a half-open [start, end) window.

_BETWEEN = re.compile(
    rf"\bbetween\s+({_YEAR})\s+(?:and|to|-|–)\s+({_YEAR})\b", re.IGNORECASE
)
_FROM_TO = re.compile(
    rf"\bfrom\s+({_YEAR})\s*(?:to|until|till|through|-|–|—)\s*({_YEAR})\b",
    re.IGNORECASE,
)
_BARE_RANGE = re.compile(rf"\b({_YEAR})\s*(?:-|–|—|to)\s*({_YEAR})\b")
_AFTER = re.compile(rf"\bafter\s+({_YEAR})\b", re.IGNORECASE)
_SINCE = re.compile(
    rf"\b(?:since|from)\s+({_YEAR})\b(?!\s*(?:to|until|till|through|-|–|—))",
    re.IGNORECASE,
)
_BEFORE = re.compile(
    rf"\b(?:before|prior to|earlier than)\s+({_YEAR})\b", re.IGNORECASE
)
_UNTIL = re.compile(
    rf"\b(?:until|till|up to|through)\s+({_YEAR})\b", re.IGNORECASE
)

# --- single instants ------------------------------------------------------- #

_AS_OF_DATE = re.compile(rf"\bas of\s+({_ISO})\b", re.IGNORECASE)
_ON_DATE = re.compile(rf"\bon\s+({_ISO})\b", re.IGNORECASE)
_AS_OF_YEAR = re.compile(rf"\bas of\s+({_YEAR})\b", re.IGNORECASE)
_IN_YEAR = re.compile(
    rf"\b(?:in|during|for|throughout|in the year)\s+({_YEAR})\b", re.IGNORECASE
)

# --- tense ----------------------------------------------------------------- #

# Checked before `current`: a question that asks for both the present and the
# past is a history question, and history is the superset.
_HISTORY = re.compile(
    r"\b(?:history|historical(?:ly)?|timeline|over time|over the years|"
    r"previously|formerly|used to|in the past|past|former|earlier|"
    r"ever|so far|to date|succession|all the (?:people|persons)|"
    r"everyone who|every person who|who else|at any point)\b",
    re.IGNORECASE,
)
_CURRENT = re.compile(
    r"\b(?:currently|current|now|nowadays|today|at present|presently|"
    r"present-day|right now|these days|at the moment|as of (?:today|now))\b",
    re.IGNORECASE,
)


def read_temporal(question: str, *, today: str | None = None) -> TemporalIntent:
    """The temporal reading of a question. Never raises."""
    text = question or ""
    if not text.strip():
        return TemporalIntent()

    for pattern in (_BETWEEN, _FROM_TO, _BARE_RANGE):
        match = pattern.search(text)
        if match:
            first, second = int(match.group(1)), int(match.group(2))
            if first > second:
                first, second = second, first
            return TemporalIntent(
                TEMPORAL_RANGE, _year_start(first), _year_start(second + 1),
                match.group(0),
            )

    match = _AFTER.search(text)
    if match:
        # "after 2018" excludes 2018 itself: a relationship that ended within
        # 2018 is not an answer to what happened after it.
        return TemporalIntent(
            TEMPORAL_RANGE, _year_start(int(match.group(1)) + 1), None,
            match.group(0),
        )
    match = _SINCE.search(text)
    if match:
        return TemporalIntent(
            TEMPORAL_RANGE, _year_start(int(match.group(1))), None, match.group(0)
        )
    match = _BEFORE.search(text)
    if match:
        return TemporalIntent(
            TEMPORAL_RANGE, None, _year_start(int(match.group(1))), match.group(0)
        )
    match = _UNTIL.search(text)
    if match:
        return TemporalIntent(
            TEMPORAL_RANGE, None, _year_start(int(match.group(1)) + 1),
            match.group(0),
        )

    for pattern in (_AS_OF_DATE, _ON_DATE):
        match = pattern.search(text)
        if match:
            moment = match.group(1)
            return TemporalIntent(
                TEMPORAL_AS_OF, moment, _day_after(moment), match.group(0)
            )
    for pattern in (_AS_OF_YEAR, _IN_YEAR):
        match = pattern.search(text)
        if match:
            year = int(match.group(1))
            return TemporalIntent(
                TEMPORAL_AS_OF, _year_start(year), _year_start(year + 1),
                match.group(0),
            )

    match = _HISTORY.search(text)
    if match:
        return TemporalIntent(TEMPORAL_HISTORY, None, None, match.group(0))

    match = _CURRENT.search(text)
    if match:
        moment = today or date.today().isoformat()
        return TemporalIntent(
            TEMPORAL_CURRENT, moment, _day_after(moment), match.group(0)
        )

    return TemporalIntent()

# --------------------------------------------------------------------------- #
# Relational readings
#
# Moved to `app.retrieval.understanding.relational`: reading a predicate cue out
# of a question is query understanding, and three layers need it — this router,
# the facet builder (relationship validity vs the document's effective date) and
# intent classification. Keeping it here would have meant importing
# `app.retrieval.graph` from the general retrieval path, which the one-doorway
# guard in tests/test_graph_retrieval.py rightly forbids.
#
# Re-exported so `intent.read_relational`, `intent.PREDICATE_CUES` and
# `intent.RelationalIntent` keep meaning exactly what they meant.
# --------------------------------------------------------------------------- #

from app.retrieval.understanding.relational import (  # noqa: E402
    PREDICATE_CUES,
    RelationalIntent,
    _cue_positions,
    read_relational,
)

__all__ = [
    "TEMPORAL_CURRENT", "TEMPORAL_AS_OF", "TEMPORAL_RANGE", "TEMPORAL_HISTORY",
    "TEMPORAL_UNSPECIFIED", "TEMPORAL_KINDS", "TemporalIntent", "read_temporal",
    "PREDICATE_CUES", "RelationalIntent", "read_relational", "_cue_positions",
]
