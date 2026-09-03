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
``field_event_start_date`` is read from MySQL ``documents.raw_meta``, so it
cannot be a pre-filter on the vector search. It is therefore applied as a
post-retrieval gate: the
candidates come back as usual, and for an ``UPCOMING`` question the event blocks
whose start date has already passed are dropped. One indexed MySQL read per
query over the candidate document ids.

The gate is deliberately narrow:

* it only ever *removes* blocks, so it cannot invent an answer;
* it only touches documents that actually carry an event start date, so a page,
  a policy brief or a project is never affected;

Note that an ``events`` document's ``effective_start_date`` *is* its event start
date now that bundles name the field they are dated by, so the payload could
serve this gate directly. Reading ``raw_meta`` predates that and is left alone:
switching would change which blocks survive, which is a retrieval decision rather
than a consequence of renaming anything.
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
from datetime import date, datetime, timezone
from typing import Any, Iterable, Sequence

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


def event_start_dates(document_ids: Iterable[str]) -> dict[str, date]:
    """Event start date per document, for those documents that have one.

    Reads ``documents.raw_meta`` — the authoritative CMS copy — because the field
    is not projected into the Qdrant payload. Absent, unparseable and non-event
    documents are simply missing from the result, which the caller treats as "not
    an event, leave it alone".
    """
    ids = [d for d in dict.fromkeys(document_ids) if d]
    if not ids:
        return {}
    try:
        from app.catalog import state
    except Exception:  # pragma: no cover - defence in depth
        return {}
    try:
        rows = state.event_start_dates(ids)
    except Exception:
        logger.warning("Event start-date lookup failed; not gating.", exc_info=True)
        return {}
    out: dict[str, date] = {}
    for document_id, raw in (rows or {}).items():
        parsed = _parse(raw)
        if parsed is not None:
            out[document_id] = parsed
    return out


def _reference_date(reference: date | None) -> date:
    return reference or datetime.now(timezone.utc).date()


def gate_upcoming(
    blocks: Sequence[Any], *, reference: date | None = None
) -> list[Any]:
    """Drop blocks for events that have already started.

    Returns the list unchanged when there is nothing to gate, when no block
    carries an event date, or when gating would leave nothing — the caller must
    always get a context it can reason about.
    """
    if not blocks:
        return list(blocks)
    today = _reference_date(reference)
    ids = [str(b.payload.get("document_id") or "") for b in blocks]
    starts = event_start_dates(ids)
    if not starts:
        return list(blocks)

    kept, dropped = [], []
    for block in blocks:
        start = starts.get(str(block.payload.get("document_id") or ""))
        if start is not None and start < today:
            dropped.append(block)
        else:
            kept.append(block)
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
