"""Which date each Drupal bundle *means* — declared once, per bundle.

A Drupal record carries several dates and the one that matters depends entirely
on what kind of content it is. A news item's date is ``field_news_date``; a
completed project's is when the project started; a research paper states only a
year; an article has nothing but its creation stamp. There is no algorithm that
can work that out, so the knowledge is **data, declared once** in
:data:`BUNDLE_DATE_FIELDS`, and the resolution logic below is generic:

    bundle -> configured field -> extract -> normalise -> effective date

Adding a bundle is one row in that table. No branch in this module, and none in
the ingestion pipeline, names a bundle.

**What "effective date" means here.** It is the date the *content* is about, as
the CMS declares it per content type — not a claim that the publisher stated a
publication date on that day. For ``news``, ``press_release``, ``report`` and
``research_papers`` the two coincide. For ``completed_projects``,
``ongoing_projects`` and ``events`` the configured field is a project start or an
event date, which the site treats as that item's date and which this module
therefore applies. :mod:`app.ingestion.source_dates` still records what each
field *is* (:data:`~app.ingestion.source_dates.FIELD_KINDS`), and that
classification travels with the decision so an auditor can see which of the two
cases a given document is.

**Nothing is invented.** A record either carries a date its source states, or it
carries no date at all and is flagged and counted as such by the pipeline. The
one fallback is the record's own ``created`` stamp, which is a real date the
source states about the record and is what this column has always held.

The parallel module for the other half of the problem is
:mod:`app.ingestion.date_resolution`, which decides an attached PDF's date. It
does not re-derive anything: it inherits the value this module produced for the
PDF's parent page. One resolution, propagated — never two.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from app.ingestion.source_dates import (
    Precision,
    as_published_at,
    classify,
    is_plausible,
    to_ist_date,
)

logger = logging.getLogger(__name__)

__all__ = [
    "BUNDLE_DATE_FIELDS",
    "CREATED",
    "BundleDateField",
    "EffectiveDate",
    "Source",
    "describe",
    "field_for",
    "inherited",
    "resolve",
]

#: The sentinel a bundle maps to when its own creation stamp is the answer. Not
#: a real Drupal field name, and deliberately spelled the same as the JSON:API
#: attribute it stands for so the mapping reads as the business rule does.
CREATED = "created"

#: Where a resolved date came from. These are the values that reach
#: ``documents.published_at_source`` (VARCHAR(16)).
#:
#: ``created``       the record's own creation stamp — its bundle maps to
#:                   ``created``, or the configured field had nothing usable.
#: ``cms_field``     the bundle's configured date field stated it.
#: ``parent_page``   an attachment inheriting its Drupal page's resolved date.
#: ``document_text`` a publication statement quoted and verified inside a PDF
#:                   (set by :mod:`app.ingestion.date_resolution`, not here).
Source = Literal["created", "cms_field", "parent_page", "document_text"]


@dataclass(frozen=True)
class BundleDateField:
    """The field a bundle takes its date from, and how precise that field is.

    ``precision`` is a property of the *field*, not of any one value: a field
    holding ``2022`` supports the year and nothing finer, so rendering its day
    would invent a January publication. It is carried to the chunk payload for
    exactly that reason.
    """

    field: str
    precision: Precision = "day"

    @property
    def is_created(self) -> bool:
        return self.field == CREATED


#: ``bundle -> the field that carries its effective date``.
#:
#: This is the supplied business mapping, verbatim, plus ``services`` (see
#: below). Every bundle and every field here was verified against the live
#: JSON:API: the bundle exists, the attribute exists on its records, and its
#: values are single-valued scalars of the shape declared.
#:
#: ``services`` is not in the supplied mapping but *is* crawled
#: (:data:`app.core.corpus.DEFAULT_BUNDLES`) and carries no date-like field at
#: all. It is declared as ``created`` rather than omitted so that
#: "a crawled bundle nobody has classified" stays a meaningful alarm
#: (``reconcile.date_checks.unmapped_bundle_dates``) instead of firing on the
#: same bundle forever — the same reason ``FIELD_KINDS`` declares the fields it
#: refuses.
#:
#: ``block_content:basic`` is crawled too and is deliberately absent: it is not
#: a node bundle, it has no ``created`` attribute, and
#: ``drupal_extractor._created_at`` already resolves it to ``revision_created``.
#: It resolves through the unmapped default, which is that same stamp.
BUNDLE_DATE_FIELDS: dict[str, BundleDateField] = {
    # ---- the record's own creation stamp is the date the site displays ----
    "article": BundleDateField(CREATED),
    "page": BundleDateField(CREATED),
    "feature_articles": BundleDateField(CREATED),
    "policy_brief": BundleDateField(CREATED),
    "videos": BundleDateField(CREATED),
    "infographics": BundleDateField(CREATED),
    "people": BundleDateField(CREATED),
    "services": BundleDateField(CREATED),  # not in the supplied map; see above

    # ---- a stated publication date ----
    "news": BundleDateField("field_news_date"),
    "press_release": BundleDateField("field_pressrelease_date"),
    # Live values carry +05:30 offsets and real clock times, unlike the
    # +00:00 IST-midnight shape every other date field uses. `to_ist_date`
    # normalises both. Null on 2 of the 8 live records, which is what makes the
    # empty-field fallback load-bearing rather than defensive.
    "report": BundleDateField("field_report_date"),
    # An integer year on the wire (2012-2019 observed), not a string. Year
    # precision: stored as 1 January *as a marker*, and every reader is expected
    # to check `published_at_precision` before rendering the day.
    "research_papers": BundleDateField("field_rpaper_year", "year"),

    # ---- the date the content is about, which this site treats as its date ----
    # These three are classified `period`/`event` in `source_dates.FIELD_KINDS`:
    # a project's start and a conference's date are not statements about when a
    # page was written. The business requirement is that they are nevertheless
    # the effective date for their bundles, so they are applied here — and the
    # classification travels on the decision (`EffectiveDate.kind`) so the
    # distinction stays visible to an auditor rather than being erased.
    "completed_projects": BundleDateField("field_completed_start_date"),
    "ongoing_projects": BundleDateField("field_ongoing_start_date"),
    "events": BundleDateField("field_event_start_date"),
}

#: Bundles already logged as unmapped, so a corpus-wide crawl of an unknown
#: bundle costs one line rather than one per document.
_warned_unmapped: set[str] = set()


@dataclass(frozen=True)
class EffectiveDate:
    """One document's date, and everything needed to explain it.

    ``value`` is the only field that reaches ``published_at``. The rest is
    provenance: it answers "why does this document carry this date?" without a
    reader having to re-derive anything.
    """

    #: The stored string — midnight UTC on the resolved calendar day — or None
    #: when the source offered nothing at all.
    value: str | None
    source: Source
    precision: Precision
    #: Which rule produced this outcome. One of: ``bundle_date_field``,
    #: ``bundle_date_field_year_only``, ``bundle_created``, ``field_empty``,
    #: ``field_invalid``, ``bundle_unmapped``, ``no_bundle``, ``no_date``,
    #: ``inherited_from_parent``.
    rule: str
    bundle: str | None = None
    #: The configured field consulted, or ``created``. Never None for a mapped
    #: bundle, so the audit row can name it even when it held nothing.
    field: str | None = None
    #: What that field actually contained, verbatim, for the audit trail.
    raw_value: Any = None
    #: What :mod:`app.ingestion.source_dates` says that field *is* —
    #: ``publication``, ``period``, ``event``, ``unknown``. Recorded, never acted
    #: on: the mapping decides, this only reports.
    kind: str = "unknown"

    @property
    def from_bundle_field(self) -> bool:
        """Did the bundle's configured field actually supply this date?

        The question the PDF path asks: when the page's date is a value the CMS
        states about that content type, the page is authoritative and there is
        nothing for the document-reading resolver to improve on.
        """
        return self.source == "cms_field" and self.rule.startswith("bundle_date_field")


def field_for(bundle: str | None) -> BundleDateField | None:
    """The configured date field for ``bundle``, or None if it has none."""
    return BUNDLE_DATE_FIELDS.get(bundle or "")


def resolve(
    bundle: str | None,
    created: str | None,
    metadata: dict[str, Any] | None,
) -> EffectiveDate:
    """**The single decision.** One record's effective date, and why.

    Ingestion, the attachment path and the backfill all call this, because two
    copies of a conditional rule drift — a re-ingested document would then get a
    different date than the backfill gave it.

    The fallback ladder is deliberate and exhaustive; see
    ``docs/ingestion/bundle-date-capture-plan.md`` §8. Every rung that is not the
    happy path falls back to ``created``, which is a real date the source states
    about the record and is what this column has always held. The alternative —
    no date — makes a document invisible to every date filter rather than merely
    mis-ordered, which is strictly worse.
    """
    configured = field_for(bundle)

    if configured is None:
        if bundle and bundle not in _warned_unmapped:
            _warned_unmapped.add(bundle)
            logger.info(
                "Bundle %r has no configured date field; its records keep their "
                "created stamp. Declare it in "
                "app.ingestion.bundle_dates.BUNDLE_DATE_FIELDS if it should use "
                "one.", bundle,
            )
        return _from_created(bundle, created, None,
                            rule="bundle_unmapped" if bundle else "no_bundle")

    if configured.is_created:
        return _from_created(bundle, created, CREATED, rule="bundle_created")

    raw = (metadata or {}).get(configured.field)
    if raw in (None, "", [], {}):
        logger.info(
            "Bundle %r states its date in %s, which is empty on this record; "
            "keeping the created stamp.", bundle, configured.field,
        )
        return _from_created(bundle, created, configured.field, rule="field_empty",
                             raw_value=raw)

    value = to_ist_date(raw)
    if not is_plausible(value):
        logger.warning(
            "Bundle %r states its date in %s, whose value %r is not a usable "
            "date; keeping the created stamp.", bundle, configured.field, raw,
        )
        return _from_created(bundle, created, configured.field,
                             rule="field_invalid", raw_value=raw)

    # A bare year in a field declared to hold full dates. `to_ist_date` reads it
    # as 1 January, which is the right *value* and the wrong *precision*: storing
    # it as a day would claim a day the source never gave, which is the one thing
    # every other guard in this system exists to prevent. So the value stands and
    # the precision is downgraded to what the source actually supports. Not
    # discarded — a stated year is real evidence, and 1 January marked `year` is
    # exactly how this codebase already represents one.
    year_only = configured.precision == "day" and _is_bare_year(raw)
    if year_only:
        logger.info(
            "Bundle %r states its date in %s, which holds only the year %r; "
            "recording it at year precision.", bundle, configured.field, raw,
        )

    return EffectiveDate(
        value=as_published_at(value),
        source="cms_field",
        precision="year" if year_only else configured.precision,
        rule="bundle_date_field_year_only" if year_only else "bundle_date_field",
        bundle=bundle,
        field=configured.field,
        raw_value=raw,
        kind=classify(configured.field),
    )


def _is_bare_year(raw: Any) -> bool:
    """Is this value a four-digit year and nothing more?

    ``True``/``False`` are excluded explicitly: ``bool`` is a subclass of ``int``
    in Python, and ``str(True)`` is not four digits — but the guard is written
    down rather than relied on, because a CMS boolean reaching a date field is
    exactly the kind of bad data this corpus already holds.
    """
    if isinstance(raw, bool):
        return False
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    text = str(raw if not isinstance(raw, float) else int(raw)).strip()
    return len(text) == 4 and text.isdigit()


def _from_created(
    bundle: str | None,
    created: str | None,
    field: str | None,
    *,
    rule: str,
    raw_value: Any = None,
) -> EffectiveDate:
    """The fallback rung. ``created`` is passed through **verbatim**.

    Not re-normalised through ``to_ist_date``/``as_published_at``: a creation
    stamp is a real point in time with a real clock reading, and flattening it to
    midnight would throw away the intra-day ordering that is the only thing
    separating the 646 completed projects sharing one import date. That is also
    exactly what this column held before this module existed, so a bundle mapped
    to ``created`` is bit-for-bit unchanged.
    """
    return EffectiveDate(
        value=created,
        source="created",
        precision="day",
        rule="no_date" if not created else rule,
        bundle=bundle,
        field=field,
        raw_value=raw_value,
        kind=classify(field or ""),
    )


def inherited(parent: EffectiveDate) -> EffectiveDate:
    """``parent``'s date as an attached file's own.

    The value and the precision carry over unchanged — a PDF hanging off a
    research paper is a year-precision document too, and rendering its 1 January
    as a day would invent a January publication just as surely on the file as on
    the page. Only the source changes, to say where it came from.

    Every PDF on a page gets this same object, whether the page holds one or
    twelve: the parent's date is resolved once and propagated, never
    recalculated per file.
    """
    return EffectiveDate(
        value=parent.value,
        source="parent_page",
        precision=parent.precision,
        rule="inherited_from_parent",
        bundle=parent.bundle,
        field=parent.field,
        raw_value=parent.raw_value,
        kind=parent.kind,
    )


def describe(
    resolved: EffectiveDate,
    *,
    title: str | None = None,
    url: str | None = None,
    for_attachment: bool = False,
) -> str:
    """A sentence explaining this date, for the decision table's evidence column.

    The point of the whole provenance chain: asked "why does this PDF have the
    date 2022?", the stored row has to answer "because it is attached to the
    research_papers page 'X', whose field_rpaper_year is 2022" — without anyone
    re-running ingestion to find out.

    ``for_attachment`` expects the **parent page's** resolution, not the
    attachment's own: the sentence describes where the date came from, and the
    inherited copy has by construction had that answer replaced with "from its
    parent". ``title`` and ``url`` are the parent's.
    """
    where = f" ({url})" if url else ""
    page = f"the {resolved.bundle or 'unknown'} page {title!r}{where}" if title \
        else f"its {resolved.bundle or 'unknown'} page{where}"
    lead = f"Inherited from {page}, whose " if for_attachment else "The "

    if resolved.from_bundle_field:
        body = (f"{resolved.bundle} bundle states its date in "
                f"{resolved.field} ({resolved.raw_value!r})")
        if for_attachment:
            body = f"{resolved.field} is {resolved.raw_value!r}"
        note = ("" if resolved.kind == "publication"
                else f" That field is classified {resolved.kind!r}: it is the "
                     f"date the content is about, not a stated publication date.")
        return f"{lead}{body}; the effective date is {str(resolved.value)[:10]}.{note}"

    reasons = {
        "bundle_created": (f"{resolved.bundle} bundle takes its date from the "
                           f"record's created stamp"),
        "field_empty": (f"{resolved.bundle} bundle states its date in "
                        f"{resolved.field}, which is empty on this record, so "
                        f"the created stamp stands"),
        "field_invalid": (f"{resolved.bundle} bundle states its date in "
                          f"{resolved.field}, whose value "
                          f"{resolved.raw_value!r} is not a usable date, so the "
                          f"created stamp stands"),
        "bundle_unmapped": (f"{resolved.bundle} bundle has no configured date "
                            f"field, so the created stamp stands"),
        "no_bundle": "The record has no bundle, so the created stamp stands",
        "no_date": (f"{resolved.bundle} bundle offered no date and the record "
                    f"has no created stamp, so it is undated"),
    }
    body = reasons.get(resolved.rule, f"date was resolved by {resolved.rule}")
    if for_attachment:
        return f"Inherited from {page}, where {body[0].lower()}{body[1:]}."
    return f"The {body}."
