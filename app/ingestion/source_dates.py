"""What each date in a CMS record *means* — declared, not inferred.

A source record carries several dates and only some of them are the document's
publication date. On this corpus, thirteen fields have date-like names and four
of them are publication dates; the rest describe when a project ran or when an
event happened. Reading any of those as a publication date is the same mistake
:mod:`app.ingestion.date_rules` exists to prevent on the PDF side, where a
reporting period, an event date and an upload time all look publishable and none
of them is.

So the meaning of a field is **data, declared once** in :data:`FIELD_KINDS`, and
anything not declared is ignored. Three consequences worth stating:

* **Ignoring is the default.** An unknown field cannot become a date, so a CMS
  that grows a new field does not silently start moving dates.
* **Only ``publication`` is actionable.** The other kinds are recorded so a
  reviewer can see what was found and rejected, exactly as the PDF path records
  the model's non-publication verdicts.
* **Supporting another site means adding rows, not branching code.** There is no
  algorithm that can know ``field_news_date`` is a publication date and
  ``field_event_start_date`` is not; what matters is that the knowledge sits in
  one table that defaults to safe.

Nothing here decides anything or writes anything. It reads one record's metadata
and reports what it found.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

logger = logging.getLogger(__name__)

__all__ = [
    "ACTIONABLE_PRECISIONS",
    "FIELD_KINDS",
    "IST",
    "Kind",
    "Precision",
    "SourceDate",
    "as_published_at",
    "classify",
    "is_plausible",
    "publication_date",
    "to_ist_date",
]

#: India Standard Time. The CMS stores a date-only field as IST midnight
#: expressed in UTC — ``2012-04-17T18:30:00+00:00`` is 18 April in Delhi, and 18
#: April is the date the site itself displays. Reading the UTC calendar date puts
#: every one of these a day early, so the conversion is not optional.
IST = timezone(timedelta(hours=5, minutes=30))

#: Outside this, a value is not a date this corpus could carry. Same bounds the
#: model's date validator uses, for the same reason.
MIN_YEAR = 1990

#: What kind of date a field holds. The first eight are the vocabulary
#: :data:`app.ingestion.date_rules.DateType` already defines, so a decision
#: recorded from a CMS field and one recorded from a PDF are comparable.
#: ``period`` is added here: a project's start and end describe how long the
#: *work* ran, which is neither the document's publication nor a single event.
Kind = Literal[
    "publication", "upload", "authoring", "edition", "event",
    "notification", "effective", "unknown", "period",
]

#: How precise a value is. A field holding ``2014`` supports the year and
#: nothing finer, so turning it into 1 January would invent a month and a day —
#: the same refusal ``DateInterpretation.statement_is_year_only`` makes.
Precision = Literal["year", "month", "day"]

#: ``field name -> (kind, precision)``. Order is meaningful: where a record
#: carries more than one publication field, the first declared wins, so the
#: outcome does not depend on dict iteration order in the source data.
#:
#: Every entry below was measured on the live corpus (``scripts.audit_dates``),
#: and the non-publication entries are declared rather than omitted so that the
#: reason they are unusable is written down instead of implied by absence.
FIELD_KINDS: dict[str, tuple[Kind, Precision]] = {
    # ---- publication: the publisher's own statement of when this went out ----
    # Verified against the rendered pages: the site displays exactly this value
    # as the item's date (30/30 sampled).
    "field_news_date": ("publication", "day"),
    "field_pressrelease_date": ("publication", "day"),
    "field_report_date": ("publication", "day"),
    # A year and nothing finer. Actionable, but only at year precision.
    "field_rpaper_year": ("publication", "year"),

    # ---- event: when something happened, not when it was written about ----
    # An agenda for a November conference is not published in November, and the
    # page for it is typically written weeks earlier or years later.
    "field_event_start_date": ("event", "day"),
    "field_event_end_date": ("event", "day"),
    # A sort key the site uses to order events, not a date about the document.
    "field_enddate_forlatestfirst": ("event", "day"),

    # ---- period: how long the work ran ----
    # A completed project spanning 2004-2005 has a page written in 2017. These
    # are the largest date fields in the corpus (~2,100 values) and the most
    # tempting to misread, which is why they are named explicitly.
    "field_completed_start_date": ("period", "day"),
    "field_completed_end_date": ("period", "day"),
    "field_ongoing_start_date": ("period", "day"),
}


#: Which precisions a caller may act on today. ``year`` is recognised and
#: recorded but deliberately not applied yet: 617 research papers carry a year
#: and 228 of them already sit in the right year with a real timestamp, so
#: rewriting those to 1 January would lose precision for no correctness gain —
#: and the answer layer has no way yet to render "2016" rather than "1 January
#: 2016". Adding ``"year"`` here is the whole of that change, once both are
#: settled. Keeping it in one constant is what stops ingestion and the backfill
#: from staging differently and leaving the corpus half-converted.
ACTIONABLE_PRECISIONS: frozenset[str] = frozenset({"day", "month"})


@dataclass(frozen=True)
class SourceDate:
    """One date found in a record's metadata, and what it is."""

    value: date
    field: str
    kind: Kind
    precision: Precision

    @property
    def is_publication(self) -> bool:
        return self.kind == "publication"

    @property
    def is_actionable(self) -> bool:
        return self.is_publication and self.precision in ACTIONABLE_PRECISIONS


def as_published_at(value: date) -> str:
    """``value`` as the string the catalogue and the chunk payload store.

    **Midnight UTC, not midnight IST.** ``app.catalog.state._to_datetime``
    normalises to naive UTC, so ``2012-04-18T00:00:00+05:30`` would land in the
    column as ``2012-04-17 18:30`` and the calendar date every consumer reads
    would be a day early — precisely the error this whole change exists to
    correct. The date has already been resolved *to* the Indian calendar day by
    :func:`to_ist_date`; this only has to preserve it.
    """
    return f"{value.isoformat()}T00:00:00+00:00"


def classify(field: str) -> Kind:
    """What kind of date this field holds. ``unknown`` for anything undeclared."""
    entry = FIELD_KINDS.get(field)
    return entry[0] if entry else "unknown"


def to_ist_date(value: Any) -> date | None:
    """A CMS value as the calendar date a reader in India sees, or None.

    Accepts a bare four-digit year too, which is what ``field_rpaper_year``
    holds. That returns 1 January **as a marker for the year**; the caller must
    read :attr:`SourceDate.precision` rather than the day.
    """
    if value is None:
        return None
    if isinstance(value, list):
        value = value[0] if value else None
        if value is None:
            return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) == 4 and text.isdigit():
        year = int(text)
        return date(year, 1, 1) if MIN_YEAR <= year <= _next_year() else None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(IST).date()


def _next_year() -> int:
    return datetime.now(timezone.utc).year + 1


def is_plausible(value: date | None) -> bool:
    """Could this be a publication date for this corpus at all?

    A zero timestamp read as a date lands in 1970 and a parse accident can land
    centuries away. Both are rejected here rather than downstream, because a
    date that is merely *stored* is already acting on ranking.
    """
    return value is not None and MIN_YEAR <= value.year <= _next_year()


def publication_date(metadata: dict[str, Any] | None) -> SourceDate | None:
    """The publication date this record's metadata states, or None.

    Only fields declared ``publication`` in :data:`FIELD_KINDS` are considered,
    and an implausible value is discarded rather than returned — so the caller
    can treat a result as usable without re-checking it.

    Returns None when the record states nothing, which is the common case and
    means "keep whatever the caller was going to use".
    """
    if not metadata:
        return None
    for field, (kind, precision) in FIELD_KINDS.items():
        if kind != "publication":
            continue
        raw = metadata.get(field)
        if raw in (None, "", [], {}):
            continue
        value = to_ist_date(raw)
        if not is_plausible(value):
            if value is not None:
                logger.info(
                    "Discarding implausible %s value %r on a source record.",
                    field, raw,
                )
            continue
        return SourceDate(value=value, field=field, kind="publication",
                          precision=precision)
    return None


def found_dates(metadata: dict[str, Any] | None) -> list[SourceDate]:
    """Every declared date in the record, publication or not.

    For the audit trail and the review queue: "what did this record actually
    offer, and why was none of it used" is only answerable if the rejected
    candidates were recorded too.
    """
    out: list[SourceDate] = []
    for field, (kind, precision) in FIELD_KINDS.items():
        raw = (metadata or {}).get(field)
        if raw in (None, "", [], {}):
            continue
        value = to_ist_date(raw)
        if not is_plausible(value):
            continue
        out.append(SourceDate(value=value, field=field, kind=kind,
                              precision=precision))
    return out
