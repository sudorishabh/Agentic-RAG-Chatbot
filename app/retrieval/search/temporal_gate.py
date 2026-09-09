"""Temporal scope of a question, and the one filter retrieval can honour today.

Why this exists
---------------
The 86-question benchmark asked "Are there any upcoming TERI training
programmes?" and the system returned six *past* programmes (TERI-DST and
TERI-ITEC cycles from 2013-15) and then refused. Nothing on the retrieval path
distinguished "upcoming" from "ever", and ranking by date alone puts the *most
recent past* event first — close to the opposite of the answer.

What this can and cannot do
---------------------------
Applied as a post-retrieval gate rather than a pre-filter: the candidates come
back as usual, and for an ``UPCOMING`` question the event blocks whose date has
already passed are dropped.

Everything it needs is in the block's own payload. An ``events`` document's
``effective_start_date`` **is** its event start date, because the bundle names
the field it is dated by, and ``effective_end_date`` carries the end of a
multi-day event. This used to read ``field_event_start_date`` out of
``documents.raw_meta`` over a MySQL round trip per query — the last place the
read path knew a Drupal field name. The canonical fields say the same thing,
cost nothing, and mean retrieval no longer depends on how the CMS happens to
spell a bundle's date field.

The gate is deliberately narrow:

* it only ever *removes* blocks, so it cannot invent an answer;
* it only touches bundles whose date is a scheduled occurrence
  (``app.core.corpus.SCHEDULED_BUNDLES``), so a page, a policy brief or a
  project is never affected. Scoping by bundle is what replaced "carries an
  event date": every document has an ``effective_start_date``, so without the
  scope the gate would drop most of the corpus for any future-tense question;
* it respects precision. An event stated as a month is not past until that
  month is, and one stated as a year is not past until the year is — the same
  refusal to read 1 January as a day that the answer layer makes.
* it declines to filter at all when that would empty the context, because
  answering from stale events is bad and answering from nothing is worse — the
  generator is told what it has and can say no upcoming ones are listed.

Modes
-----
``PAST``, ``UPCOMING``, ``CURRENT``, ``POINT_IN_TIME``, ``DATE_RANGE``, ``NONE``.
Only ``UPCOMING`` currently changes retrieval; the rest are classified so the
distinction is explicit and testable, and so document-date questions keep using
``effective_start_date`` and relationship-history questions keep using claim
validity, exactly as before.
"""
from __future__ import annotations

import logging
import re
from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Any, Sequence

from app.core.dates import parse_iso_date

logger = logging.getLogger(__name__)

PAST = "past"
UPCOMING = "upcoming"
CURRENT = "current"
POINT_IN_TIME = "point_in_time"
DATE_RANGE = "date_range"
NONE = "none"

# Word-boundary patterns, most specific first: "as of 2019" is a point in time
# even though it contains no tense, and "since 2019" is a range even though it
# reads as current. Order therefore matters and the first match wins.
_PATTERNS: tuple[tuple[str, str], ...] = (
    (DATE_RANGE, r"\bbetween\s+\d{4}\b|\bfrom\s+\d{4}\b|\bsince\s+\d{4}\b"
                 r"|\b\d{4}\s*(?:-|–|to)\s*\d{4}\b|\bover the (?:last|past)\b"),
    (POINT_IN_TIME, r"\bas of\b|\bat the (?:time|end) of\b|\bin \d{4}\b"),
    (UPCOMING, r"\bupcoming\b|\bforthcoming\b|\bscheduled\b|\bwill (?:be )?(?:take place|happen|run|host)"
               r"|\bnext (?:week|month|year|session|summit|conference|event)\b"
               r"|\bany (?:planned|future)\b|\bplanned\b|\bfuture\b(?!\s+of\b)"),
    (PAST, r"\bpast\b|\bprevious(?:ly)?\b|\bformer\b|\bused to\b|\bhistor(?:y|ical)\b"
           r"|\bearlier\b|\bonce\b|\bcompleted\b"),
    (CURRENT, r"\bcurrent(?:ly)?\b|\bright now\b|\bat present\b|\bpresently\b"
              r"|\bongoing\b|\bunderway\b|\bactive\b|\btoday\b|\blatest\b"),
)


def detect_mode(question: str) -> str:
    """The temporal scope a question asks for. Deterministic; no model call."""
    text = (question or "").lower()
    if not text.strip():
        return NONE
    for mode, pattern in _PATTERNS:
        if re.search(pattern, text):
            return mode
    return NONE


def _parse(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        pass
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _reference_date(reference: date | None) -> date:
    return reference or datetime.now(timezone.utc).date()


def period_end(payload: Any) -> date | None:
    """The last day this document's period covers, or None if it has no date.

    Read entirely from the canonical fields. ``effective_end_date`` when the
    document states a period; otherwise the end of whatever
    ``effective_start_date`` establishes, which is where precision matters: a
    date stated as "September 2007" covers until the 30th, and one stated as
    "2007" until 31 December. Treating the stored 1st as the whole answer would
    call a month-long event past on its second day.
    """
    end = _as_date(payload.get("effective_end_date"))
    if end is not None:
        return _period_last_day(end, payload.get("end_precision"))
    start = _as_date(payload.get("effective_start_date"))
    if start is None:
        return None
    return _period_last_day(start, payload.get("start_precision"))


def _as_date(value: Any) -> date | None:
    """A stored timestamp as the calendar day it names, or None.

    The columns and the payload hold a full timestamp; every comparison here is
    between calendar days, so the time is dropped rather than compared.
    """
    parsed = parse_iso_date(value)
    return parsed.date() if parsed is not None else None


def _period_last_day(value: date, precision: Any) -> date:
    """The last day of the period ``value`` opens at ``precision``."""
    if precision == "year":
        return date(value.year, 12, 31)
    if precision == "month":
        return date(value.year, value.month, monthrange(value.year, value.month)[1])
    return value


def _is_scheduled(payload: Any) -> bool:
    """Whether "upcoming" means anything for this document's bundle."""
    from app.core.corpus import SCHEDULED_BUNDLES

    return str(payload.get("bundle") or "") in SCHEDULED_BUNDLES


def gate_upcoming(
    blocks: Sequence[Any], *, reference: date | None = None
) -> list[Any]:
    """Drop blocks for scheduled occurrences that are already over.

    Returns the list unchanged when there is nothing to gate, when no block is a
    scheduled bundle, or when gating would leave nothing — the caller must
    always get a context it can reason about.
    """
    if not blocks:
        return list(blocks)
    today = _reference_date(reference)

    kept, dropped = [], []
    for block in blocks:
        payload = block.payload or {}
        end = period_end(payload) if _is_scheduled(payload) else None
        if end is not None and end < today:
            dropped.append(block)
        else:
            kept.append(block)
    if not dropped:
        return list(blocks)
    if not kept:
        logger.info(
            "Upcoming gate would empty the context (%d stale event blocks); "
            "keeping them so the answer can say none are upcoming.", len(dropped),
        )
        return list(blocks)
    if dropped:
        logger.info("Upcoming gate dropped %d block(s) for events already started.",
                    len(dropped))
        for i, block in enumerate(kept, start=1):
            block.n = i
    return kept
