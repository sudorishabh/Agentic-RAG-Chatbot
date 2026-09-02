"""What each date in a CMS record *means*, and the primitives for reading one.

A source record carries several dates. On this corpus thirteen fields have
date-like names, and what each one *is* — a publication date, a project period, a
conference — is knowledge no algorithm can derive, so it is **data, declared
once** in :data:`FIELD_KINDS`.

**Which field a document takes its date from is decided elsewhere.**
:mod:`app.ingestion.bundle_dates` owns that, keyed by bundle, because the answer
depends on the content type rather than on which date-like fields happen to be
present. This module supplies the vocabulary and the value-reading primitives
that both paths share:

* :data:`FIELD_KINDS` / :func:`classify` — what a field is. Carried on every
  decision as provenance, so a date taken from a project-start field is
  recognisable as such rather than silently reading like a publication date.
* :func:`to_ist_date` — the CMS's date-only encoding, read as the calendar day
  the site itself displays.
* :func:`is_plausible` — could this be a date for this corpus at all.
* :func:`as_published_at` — the string the catalogue and the chunk payload store.
* :func:`found_dates` — every declared date on a record, for the audit trail.

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
    "FIELD_KINDS",
    "IST",
    "Kind",
    "Precision",
    "SourceDate",
    "as_published_at",
    "classify",
    "is_plausible",
    "publication_date",
    "resolve_published_at",
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

#: ``field name -> (kind, precision)``. What each field *is*. This no longer
#: decides which field a document uses — :data:`app.ingestion.bundle_dates.
#: BUNDLE_DATE_FIELDS` does, per bundle — but the classification still travels
#: with every decision, so a date taken from a project-start or event field is
#: visibly that rather than passing as a stated publication date.
#:
#: Order is meaningful for :func:`publication_date`: where a record carries more
#: than one publication field the first declared wins, so the outcome does not
#: depend on dict iteration order in the source data.
#:
#: Every entry below was measured on the live corpus (``scripts.audit_dates``),
#: and entries that are not publication dates are declared rather than omitted so
#: that what they are is written down instead of implied by absence.
FIELD_KINDS: dict[str, tuple[Kind, Precision]] = {
    # ---- publication: the publisher's own statement of when this went out ----
    # Verified against the rendered pages: the site displays exactly this value
    # as the item's date (30/30 sampled).
    "field_news_date": ("publication", "day"),
    "field_pressrelease_date": ("publication", "day"),
    "field_report_date": ("publication", "day"),
    # A year and nothing finer, so `research_papers` maps to it at year
    # precision and its value is stored as 1 January *as a marker*.
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

    # ---- looked at, and not dates at all ----
    # Publication *venues* and publisher names — 2,539 values whose field names
    # contain "publish". Declared rather than omitted so that "a date-like field
    # nobody has classified" stays a meaningful alarm (see
    # ``reconcile.date_checks``) instead of firing on these three forever. One
    # ``field_rpaper_publisher`` value is literally "2021", which is bad data in
    # the CMS and would otherwise parse as a date.
    "field_article_published_in": ("unknown", "day"),
    "field_rpaper_published_in": ("unknown", "day"),
    "field_rpaper_publisher": ("unknown", "day"),
}


@dataclass(frozen=True)
class SourceDate:
    """One date found in a record's metadata, and what it is.

    Reporting only. Whether a date is *used* is decided by
    :data:`app.ingestion.bundle_dates.BUNDLE_DATE_FIELDS`, which is keyed by
    bundle — so there is no "is this actionable?" question to answer here, and
    the constant that used to answer it is gone rather than left to drift out of
    agreement with the mapping.
    """

    value: date
    field: str
    kind: Kind
    precision: Precision

    @property
    def is_publication(self) -> bool:
        return self.kind == "publication"


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


def resolve_published_at(
    created: str | None,
    metadata: dict[str, Any] | None,
    *,
    bundle: str | None = None,
) -> tuple[str | None, str, str]:
    """``(published_at, source, precision)`` for one source record.

    A thin adapter over :func:`app.ingestion.bundle_dates.resolve`, which owns
    the decision. It exists so the several read-only callers that only want the
    three values — the backfills, the reconciliation checks, the site-scrape
    comparison — do not each have to unpack an :class:`~.bundle_dates.
    EffectiveDate`, and so the decision itself lives in exactly one place.

    **Which date a record carries is a property of its bundle**, not of which
    date-like fields happen to be present: ``news`` takes ``field_news_date``,
    ``completed_projects`` takes the project's start, ``article`` takes its
    creation stamp. A caller that does not know the bundle gets the creation
    stamp, which is the safe default and exactly the historical behaviour — an
    unrecognised content type can never silently start moving dates.

    Imported inside the function because :mod:`app.ingestion.bundle_dates`
    imports this module's primitives at module level.
    """
    from app.ingestion.bundle_dates import resolve

    resolved = resolve(bundle, created, metadata)
    return resolved.value, resolved.source, resolved.precision


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
