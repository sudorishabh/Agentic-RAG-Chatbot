"""What each date-like CMS field *is*, and the primitives for reading one.

A source record carries several date-like fields. What each one is — a date the
content is stated with, one end of a period, a sort key, a publisher's name that
merely looks temporal — is knowledge no algorithm can derive from the value, so
it is **data, declared once** in :data:`FIELD_ROLES`.

**This describes the source field, not the application's date model.** The system
stores one thing: a document's ``effective_start_date``, and where its bundle
declares one, an ``effective_end_date``. It does not store, rank on, or reason
about a "publication date", and this taxonomy deliberately no longer uses that
word — a role here answers "what is this Drupal field?", never "is the resulting
date a publication?".

**Which field a document takes its date from is decided elsewhere.**
:mod:`app.ingestion.bundle_dates` owns that, keyed by bundle, because the answer
depends on the content type rather than on which date-like fields happen to be
present. This module supplies the vocabulary and the value-reading primitives
that both paths share:

* :data:`FIELD_ROLES` / :func:`classify` — what a field is, and how precise its
  values are. The role travels on every decision as provenance, so a date taken
  from the opening of a project period is visibly that.
* :func:`to_ist_date` — the CMS's date-only encoding, read as the calendar day
  the site itself displays.
* :func:`is_plausible` — could this be a date for this corpus at all.
* :func:`as_stored_date` — the string the catalogue and the chunk payload store.
* :func:`found_dates` — every declared date on a record, for tooling and audit.

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
    "FIELD_ROLES",
    "FieldRole",
    "IST",
    "Precision",
    "SourceDate",
    "as_stored_date",
    "classify",
    "found_dates",
    "is_plausible",
    "resolve_effective_dates",
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

#: What a date-like CMS field *is*. Five roles, each earning its place by
#: controlling something: how the field is described in the audit trail, and
#: whether the reconciliation checks may ignore it.
#:
#: ``date``        a single date the CMS states about the content. What
#:                 ``news``, ``press_release``, ``report`` and
#:                 ``research_papers`` are dated with.
#: ``range_start`` the opening of a period the content covers — a project's
#:                 start, an event's first day.
#: ``range_end``   the close of that period. Distinct from ``range_start``
#:                 because :data:`app.ingestion.bundle_dates.BUNDLE_DATE_FIELDS`
#:                 is ordered ``(start, end)`` and swapping them would date every
#:                 project by its finish.
#: ``sort_key``    a date-typed field the site uses only to order a listing. It
#:                 says nothing about the content and must never be read as its
#:                 date.
#: ``not_a_date``  a field whose *name* looks temporal and whose values are not
#:                 dates. Declared rather than omitted, so
#:                 ``reconcile.date_checks.undeclared_source_date_field`` stops
#:                 firing on them forever. Also what :func:`classify` returns for
#:                 an *undeclared* field — the safe reading, since nothing may
#:                 date a document by a field nobody has looked at.
#: ``created_stamp`` the record's own ``created`` attribute. Not a declared CMS
#:                 field and not in :data:`FIELD_ROLES`, but a real date the
#:                 source states about the record, and the value most bundles
#:                 fall back to — so it needs a role of its own rather than
#:                 reading as "not a date".
#:
#: Deliberately **not** a publication/notification/effective vocabulary. That
#: distinction belongs to :data:`app.ingestion.date_rules.DateType`, which
#: classifies a date the model found *inside a PDF's text* — a different
#: question, asked of a different thing, and the one place the word "publication"
#: still earns its keep.
FieldRole = Literal[
    "date", "range_start", "range_end", "sort_key", "not_a_date",
    "created_stamp",
]

#: How precise a value is. A field holding ``2014`` supports the year and
#: nothing finer, so turning it into 1 January would invent a month and a day —
#: the same refusal ``DateInterpretation.statement_is_year_only`` makes.
Precision = Literal["year", "month", "day"]

#: ``field name -> (role, precision)``. What each date-like field in this CMS is,
#: and how precise its values are.
#:
#: This does not decide which field a document uses —
#: :data:`app.ingestion.bundle_dates.BUNDLE_DATE_FIELDS` does, per bundle. Two
#: things read it: :func:`app.ingestion.bundle_dates.precision_of` takes the
#: precision, and the role travels onto every decision as provenance so an
#: auditor can see that a document's date came from the opening of a period
#: rather than from a date the CMS states outright.
#:
#: Every entry was measured on the live corpus (``scripts.audit_dates``), and the
#: fields that are *not* usable dates are declared rather than omitted so that
#: what they are is written down instead of implied by absence.
FIELD_ROLES: dict[str, tuple[FieldRole, Precision]] = {
    # ---- date: the single date the CMS states about this content ----
    # Verified against the rendered pages: the site displays exactly this value
    # as the item's date (30/30 sampled).
    "field_news_date": ("date", "day"),
    "field_pressrelease_date": ("date", "day"),
    "field_report_date": ("date", "day"),
    # A year and nothing finer, so `research_papers` resolves at year precision
    # and its value is stored as 1 January *as a marker*.
    "field_rpaper_year": ("date", "year"),

    # ---- range_start / range_end: the period the content covers ----
    # A completed project spanning 2004-2005 has a page written in 2017. These
    # are the largest date fields in the corpus (~2,100 values) and the most
    # tempting to misread, which is why they are named explicitly. The
    # start/end split is load-bearing: `BUNDLE_DATE_FIELDS` is ordered
    # `(start, end)` and reversing a pair would date every project by its finish.
    "field_completed_start_date": ("range_start", "day"),
    "field_completed_end_date": ("range_end", "day"),
    "field_ongoing_start_date": ("range_start", "day"),
    # An agenda for a November conference is not written in November, and the
    # page for it is typically made weeks earlier or years later. The site still
    # dates the event by these, which is why the `events` bundle maps to them.
    "field_event_start_date": ("range_start", "day"),
    "field_event_end_date": ("range_end", "day"),

    # ---- sort_key: ordering machinery, not a fact about the content ----
    # The site uses this to sort event listings newest-first. It is a real
    # timestamp and it describes nothing, so no bundle may ever map to it.
    "field_enddate_forlatestfirst": ("sort_key", "day"),

    # ---- not_a_date: looked at, and not dates at all ----
    # Publication *venues* and publisher names — 2,539 values whose field names
    # contain "publish". Declared rather than omitted so that "a date-like field
    # nobody has classified" stays a meaningful alarm (see
    # ``reconcile.date_checks``) instead of firing on these three forever. One
    # ``field_rpaper_publisher`` value is literally "2021", which is bad data in
    # the CMS and would otherwise parse as a date.
    "field_article_published_in": ("not_a_date", "day"),
    "field_rpaper_published_in": ("not_a_date", "day"),
    "field_rpaper_publisher": ("not_a_date", "day"),
}


@dataclass(frozen=True)
class SourceDate:
    """One date found in a record's metadata, and what its field is.

    Reporting only. Whether a date is *used* is decided by
    :data:`app.ingestion.bundle_dates.BUNDLE_DATE_FIELDS`, which is keyed by
    bundle — so there is no "is this the one?" question to answer here, and the
    helpers that used to answer it are gone rather than left to drift out of
    agreement with the mapping.
    """

    value: date
    field: str
    role: FieldRole
    precision: Precision


def as_stored_date(value: date) -> str:
    """``value`` as the string the catalogue and the chunk payload store.

    **Midnight UTC, not midnight IST.** ``app.catalog.state._to_datetime``
    normalises to naive UTC, so ``2012-04-18T00:00:00+05:30`` would land in the
    column as ``2012-04-17 18:30`` and the calendar date every consumer reads
    would be a day early — precisely the error this whole change exists to
    correct. The date has already been resolved *to* the Indian calendar day by
    :func:`to_ist_date`; this only has to preserve it.
    """
    return f"{value.isoformat()}T00:00:00+00:00"


def classify(field: str) -> FieldRole:
    """What this field is. ``not_a_date`` for anything undeclared.

    An undeclared field is reported as ``not_a_date`` rather than as a date of
    unknown role, because that is the safe reading: nothing may date a document
    by a field nobody has classified, and
    ``reconcile.date_checks.undeclared_source_date_field`` is what surfaces one
    so a person can declare it.
    """
    entry = FIELD_ROLES.get(field)
    return entry[0] if entry else "not_a_date"


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
    """Could this be a date this corpus carries at all?

    A zero timestamp read as a date lands in 1970 and a parse accident can land
    centuries away. Both are rejected here rather than downstream, because a
    date that is merely *stored* is already acting on ranking.
    """
    return value is not None and MIN_YEAR <= value.year <= _next_year()


def resolve_effective_dates(
    created: str | None,
    metadata: dict[str, Any] | None,
    *,
    bundle: str | None = None,
) -> tuple[str | None, str, str]:
    """``(effective_start_date, source, precision)`` for one source record.

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
    from app.ingestion.bundle_dates import resolve_effective_dates

    resolved = resolve_effective_dates(bundle, created, metadata)
    return resolved.start_value, resolved.source, resolved.start_precision


def found_dates(metadata: dict[str, Any] | None) -> list[SourceDate]:
    """Every declared, usable date in the record, whatever its field's role.

    For tooling and the review queue: "what did this record actually offer, and
    why was none of it used" is only answerable if the values the bundle mapping
    did not reach were listed too.
    """
    out: list[SourceDate] = []
    for field, (role, precision) in FIELD_ROLES.items():
        raw = (metadata or {}).get(field)
        if raw in (None, "", [], {}):
            continue
        value = to_ist_date(raw)
        if not is_plausible(value):
            continue
        out.append(SourceDate(value=value, field=field, role=role,
                              precision=precision))
    return out
