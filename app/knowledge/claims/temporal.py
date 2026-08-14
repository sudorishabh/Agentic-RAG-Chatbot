"""Temporal normalization: when a claim was true, and how we know.

Three clocks, kept apart on purpose
-----------------------------------
``valid_from`` / ``valid_until``  when the fact was true **in the world**.
``asserted_at``                   when the system learned it.
``created_at``                    when the row was written.

Conflating the first with either of the others is the classic knowledge-graph
error: a 2024 news article describing a 2019 partnership does not make the
partnership start in 2024.

Open-ended validity, i.e. "present"
-----------------------------------
``valid_until = None`` **with** a ``valid_from`` means *open-ended*: true from
that date onward, with no stated end. It does not mean "true forever" and it
does not mean "unknown" — the source simply never stated an end.

``valid_from = None`` **and** ``valid_until = None`` means no temporal
information at all. The two are distinguishable, and conflict detection treats
them differently: an open-ended interval overlaps everything after its start,
while an unknown one overlaps nothing (there is nothing to compare).

This corpus makes the distinction concrete. A ``completed_projects`` node
carries both a start and an end date (1,030 of them), so its relationships are
closed intervals. An ``ongoing_projects`` node carries a start and **no** end
(593), so its relationships are open-ended — which is the corpus's own way of
saying "current".

Where validity may come from
----------------------------
``stated``          the source states the relationship's own dates.
``subject_period``  taken from the subject's CMS-stated period — a project's
                    own start and end. An **explicit, documented rule**, not a
                    guess: the CMS states when the project ran, and a funding
                    relationship to that project is scoped by it. Recorded as
                    its own basis so it is never mistaken for the source having
                    stated the relationship's dates.
``document``        inferred from the document's publication date. **Not used.**
                    No rule approves it, and it is exactly the inference that
                    turns "reported in 2024" into "true from 2024".
``unknown``         nothing known.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.knowledge.claims import types as t

logger = logging.getLogger(__name__)

# Words a source uses to mean "no stated end". Matched only inside an explicit
# temporal phrase, never on their own — "current" appears constantly in prose
# about current affairs and means nothing there.
_PRESENT_WORDS = frozenset(
    {"present", "current", "currently", "ongoing", "date", "now", "today"}
)

# "since 2019", "from March 2019", "with effect from 2019-04-01"
_SINCE = re.compile(
    r"\b(?:since|from|w\.e\.f\.?|with effect from|starting(?: in| from)?)\s+"
    r"(?P<value>[A-Za-z]{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{4}-\d{2}|\d{4})",
    re.IGNORECASE,
)
# "until 2021", "till March 2021", "up to 2021"
_UNTIL = re.compile(
    r"\b(?:until|untill|till|up to|through|ending(?: in)?)\s+"
    r"(?P<value>[A-Za-z]{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{4}-\d{2}|\d{4}|"
    r"present|current|date|now|today)",
    re.IGNORECASE,
)
# "2019-2021", "2019 to 2021", "between 2019 and 2021"
_RANGE = re.compile(
    r"\b(?:between\s+)?(?P<start>\d{4})\s*(?:-|–|—|to|and|until)\s*"
    r"(?P<end>\d{4}|present|current|date|now)\b",
    re.IGNORECASE,
)

_MONTHS = {
    m: i
    for i, m in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun",
         "jul", "aug", "sep", "oct", "nov", "dec"),
        start=1,
    )
}


@dataclass(frozen=True)
class Window:
    """A validity interval and how it was established."""

    valid_from: str | None = None
    valid_until: str | None = None
    basis: str = t.BASIS_UNKNOWN

    @property
    def is_open_ended(self) -> bool:
        """Stated start, no stated end — the corpus's "current"."""
        return self.valid_from is not None and self.valid_until is None

    @property
    def is_unknown(self) -> bool:
        return self.valid_from is None and self.valid_until is None

    @property
    def is_closed(self) -> bool:
        return self.valid_from is not None and self.valid_until is not None


UNKNOWN = Window()


def _iso(value: str | None) -> str | None:
    """Normalize one date token to ``YYYY-MM-DD``, or None."""
    from app.knowledge.claims.validate import parse_iso_date

    if not value:
        return None
    text = value.strip()
    if text.lower() in _PRESENT_WORDS:
        return None
    match = re.match(r"^([A-Za-z]{3,9})\s+(\d{4})$", text)
    if match:
        month = _MONTHS.get(match.group(1)[:3].lower())
        if month is None:
            return None
        return parse_iso_date(f"{match.group(2)}-{month:02d}")
    return parse_iso_date(text)


def _is_present(value: str | None) -> bool:
    return bool(value) and value.strip().lower() in _PRESENT_WORDS


def parse_temporal_phrase(text: str) -> Window:
    """Read an explicit validity phrase out of source language.

    Deliberately conservative: it fires only on the constructions that actually
    state a period ("since 2019", "2019-2021", "until March 2021"). A bare year
    in a sentence is not a validity claim — this corpus is full of years that
    are citations, measurements and targets — so nothing is inferred from one.
    """
    if not text:
        return UNKNOWN

    ranged = _RANGE.search(text)
    if ranged:
        start = _iso(ranged.group("start"))
        end_raw = ranged.group("end")
        if start:
            if _is_present(end_raw):
                # "2019 to present": open-ended, and the source said so.
                return Window(start, None, t.BASIS_STATED)
            end = _iso(end_raw)
            if end and end >= start:
                return Window(start, end, t.BASIS_STATED)

    since = _SINCE.search(text)
    until = _UNTIL.search(text)
    valid_from = _iso(since.group("value")) if since else None
    valid_until = None
    if until and not _is_present(until.group("value")):
        valid_until = _iso(until.group("value"))

    if valid_from or valid_until:
        if valid_from and valid_until and valid_from > valid_until:
            # An inverted window is not a window. Refuse rather than reorder:
            # reordering would invent a reading the source did not have.
            return UNKNOWN
        return Window(valid_from, valid_until, t.BASIS_STATED)
    return UNKNOWN


def _from_cms_datetime(value: Any) -> str | None:
    """A Drupal datetime field to ``YYYY-MM-DD``."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        from app.knowledge.claims.validate import parse_iso_date

        return parse_iso_date(text[:10])


def subject_period(meta: dict[str, Any]) -> Window:
    """The subject's own CMS-stated period, as a validity window.

    The explicit rule referred to in the module docstring, and the only
    inference permitted anywhere in the claim layer:

        a relationship to a project is scoped by the period the CMS states that
        project ran.

    A completed project has a start and an end, giving a closed interval. An
    ongoing project has a start and no end, giving an open-ended one — which is
    how this corpus says "current". Basis is ``subject_period``, never
    ``stated``, so nothing later mistakes it for the source having dated the
    relationship itself.
    """
    start = _from_cms_datetime(
        meta.get("field_completed_start_date") or meta.get("field_ongoing_start_date")
    )
    end = _from_cms_datetime(
        meta.get("field_completed_end_date") or meta.get("field_ongoing_end_date")
    )
    if start and end and start > end:
        logger.debug("Ignoring inverted CMS project period %s..%s", start, end)
        return UNKNOWN
    if not start and not end:
        return UNKNOWN
    return Window(start, end, t.BASIS_SUBJECT_PERIOD)


# --------------------------------------------------------------------------- #
# Interval arithmetic, used by conflict detection
# --------------------------------------------------------------------------- #

_MIN = date.min.isoformat()
_MAX = date.max.isoformat()


def _bounds(window: Window) -> tuple[str, str]:
    """Half-open bounds for comparison. An absent end is open to the far
    future; an absent start is open to the far past."""
    return (window.valid_from or _MIN, window.valid_until or _MAX)


def overlaps(a: Window, b: Window) -> bool:
    """Whether two validity windows cover any instant in common.

    An unknown window overlaps nothing: with no dates at all there is nothing to
    compare, and treating it as "always" would make every undated claim conflict
    with every other. That is the difference between *undated* and *current*,
    and it is why the two are represented distinctly.

    Adjacent intervals do not overlap. "Bob until 2026-03" then "Alice from
    2026-03" is a succession, not a contradiction — the boundary belongs to the
    later claim.
    """
    if a.is_unknown or b.is_unknown:
        return False
    a_start, a_end = _bounds(a)
    b_start, b_end = _bounds(b)
    return a_start < b_end and b_start < a_end


def as_iso(value: Any) -> str | None:
    """Coerce a date to ``YYYY-MM-DD``, whatever shape it arrived in.

    MySQL hands back ``datetime.date`` for a DATE column while extraction
    produces strings, and every comparison in this module is lexical. Without
    one coercion point the two meet and raise, which is exactly what happened
    the first time a staged claim was read back for conflict detection.
    """
    if value is None or value == "":
        return None
    if isinstance(value, (date, datetime)):
        return (value.date() if isinstance(value, datetime) else value).isoformat()
    return str(value)[:10]


def window_of(assertion: Any) -> Window:
    """The validity window recorded on a staged assertion."""
    basis = getattr(assertion, "temporal_basis", None) or t.BASIS_UNKNOWN
    return Window(
        as_iso(getattr(assertion, "valid_from", None)),
        as_iso(getattr(assertion, "valid_until", None)),
        basis,
    )


def precedes(a: Window, b: Window) -> bool:
    """Whether ``a`` ends no later than ``b`` starts — a clean succession."""
    if a.is_unknown or b.is_unknown:
        return False
    return _bounds(a)[1] <= _bounds(b)[0]
