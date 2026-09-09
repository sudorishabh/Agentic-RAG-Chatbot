"""The one place a PDF's ``effective_start_date`` is decided.

This is the canonical entry point for the date-resolution behaviour validated in
Phase 0 (see ``reports/phase0/full_corpus_v3_final_report.md``). Every
ingestion path that builds a PDF document calls :func:`resolve`; the rules
themselves live in :mod:`app.ingestion.date_rules` and
:mod:`app.ingestion.date_llm` and are not duplicated anywhere.

The contract, unchanged from the validated design:

**The page's date is the default and the fallback.** A PDF keeps its parent
node's date unless the document itself states when it was published. Being
uploaded later, having a later ``file.created``, sitting under a later
``/files/YYYY-MM/`` path, carrying a later PDF ``CreationDate`` or naming a year
in its filename are all *supporting signals*: they decide whether a document is
worth reading closely, and never set a date.

**Sharing a page is different.** One PDF on a page is part of that page's
publication and inherits its date unopened. Several PDFs on one page are several
documents — a shelf accretes editions and reports published years apart — so
each one is read and gets its own document-level decision, with the page's date
as its fallback rather than its answer. That is the only thing the PDF count
changes: it does not lower any bar for what may set a date.

**An override needs the document to say so.** Two paths can propose one, and
both require the document's own text. :mod:`app.ingestion.date_llm` proposes a
*date at the precision its evidence supports* when the verdict survives every
gate — a quoted publication statement, that statement present in the PDF's own
text, the statement carrying the proposed date, publication linkage, and
confidence at or above the threshold. A statement naming a day gives a day; one
naming a month gives that month; one naming only a year gives that year. The
value stored is the first day of the established period and the precision says
how much is known, so nothing is invented in either direction. :func:`copyright_override`, the one deterministic override,
proposes a *year* (stored as 1 January with ``candidate_precision="year"``)
when the front matter carries a copyright statement **and** the PDF's own
DocInfo creation date names the same year — two independent facts agreeing,
and neither of them a Drupal timestamp. It runs only where the deterministic
pass found nothing at all to go on (``multi_pdf_no_evidence``: an in-body file
with no upload record, whose page is dated by its creation stamp), which is the
shelf-page shape where a book published years earlier was inheriting the day
someone typed the page. Anything short of that keeps the page date and, where
a date was seen, leaves a review row.

Cost follows the same routing that was measured: the deterministic pass settles
the large majority for free, only the routed remainder has its text read, and
the model is called only for what survives that. Nothing here downloads
anything — the caller already holds the PDF bytes — and Document Intelligence is
unreachable, because this module does not import
:mod:`app.ingestion.extractors.pdf_extractor`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from typing import Any

from app.ingestion.date_evidence import (
    PageContext,
    PdfEvidence,
    copyright_statement,
    read_pdf_front_matter,
    read_pdf_head,
)
from app.ingestion.date_rules import DateDecision, decide

logger = logging.getLogger(__name__)

__all__ = ["ResolvedDate", "build_evidence", "copyright_override", "resolve"]


@dataclass
class ResolvedDate:
    """What ingestion should use for one attached file, plus why.

    The four date fields are named exactly as
    :class:`app.ingestion.bundle_dates.EffectiveDate`'s, because they mean the
    same things and a caller holding either should read the same way. Only
    ``start_value`` and ``end_value`` reach the document; ``decision`` carries
    the provenance for the decision table and the review queue and is
    deliberately not part of the chunk payload.
    """

    #: The document's primary date — the parent page's effective start date,
    #: or a day the file's own text states and verified.
    start_value: str | None
    #: Precision of :attr:`start_value`. Inherited from the parent page, so a
    #: file hanging off a research paper is year-precision too and no reader
    #: renders its 1 January as a day. For an override it is the decision's
    #: own: ``day`` from the LLM path, which quotes a stated day, ``year`` from
    #: the copyright rule, which quotes a stated year.
    start_precision: str = "day"
    #: The end of the period the parent page's content covers, inherited whole.
    #: None for a single-date page, and None for an override — a quoted
    #: statement gives a day, never a period.
    end_value: str | None = None
    end_precision: str | None = None
    edition_label: str | None = None
    decision: DateDecision | None = None
    #: The model's raw verdict, when one was obtained, for the audit trail.
    llm_raw: dict[str, Any] | None = None
    #: Evidence tiers actually used, for cost accounting.
    used: list[str] = field(default_factory=list)

    @property
    def overridden(self) -> bool:
        return bool(self.decision and self.decision.action == "propose_override")

    @property
    def canonical_source(self) -> str:
        """The value ``documents.date_source`` should carry for this outcome.

        Two vocabularies meet here and neither is wrong. ``DateDecision.source``
        is *provenance*: it names the field, rule or model that produced the
        verdict, and the decision table records it verbatim. ``date_source`` on
        the document is the *canonical* four-then-five value vocabulary the
        query layer reads, and it must never carry a Drupal field name or a
        rule name.

        This is the map between them, and it lives here because this class is
        what the caller holds. An inherited date is ``parent_page``. A quoted
        publication statement is ``document_text``. A corroborated copyright
        year is ``document_copyright`` — which used to be recorded as
        ``document_text``, claiming a verified publication statement for a
        document that had only stated a year.
        """
        if not self.overridden:
            return "parent_page"
        if (self.decision.source or "") == "document_copyright":
            return "document_copyright"
        return "document_text"

    @property
    def needs_review(self) -> bool:
        return bool(self.decision and self.decision.action == "needs_manual_review")


def build_evidence(
    *,
    document_id: str,
    node: Any,
    file: Any,
    page_pdf_count: int | None = None,
    parent_date: Any = None,
) -> PdfEvidence:
    """Adapt a Drupal ``(record, file)`` pair into the evidence model.

    ``page_pdf_count`` is what tells a single-document page from a shelf that
    accreted documents over years. It defaults to the number of files the node
    carries, which is exactly what the crawl already resolved for it.

    ``parent_date`` is the page's :class:`app.ingestion.bundle_dates.
    EffectiveDate`, resolved **once** by the caller and passed in rather than
    re-derived here. That is what makes "every PDF on a page carries the page's
    date" true by construction for a page holding one file or twelve: there is
    only ever one resolution to disagree with. Resolved here when the caller did
    not, so a test or a tool that has a node and a file needs nothing else.
    """
    from app.ingestion.bundle_dates import resolve_effective_dates

    files = getattr(node, "files", None) or []
    count = page_pdf_count if page_pdf_count is not None else max(1, len(files))
    if parent_date is None:
        parent_date = resolve_effective_dates(
            getattr(node, "bundle", None),
            getattr(node, "created", None),
            getattr(node, "metadata", None),
        )
    return PdfEvidence(
        document_id=document_id,
        origin=getattr(file, "origin", "attachment"),
        url=getattr(file, "url", None),
        filename=getattr(file, "filename", None),
        anchor=getattr(file, "description", None) or None,
        file_created=getattr(file, "created", None),
        page=PageContext(
            node_uuid=getattr(node, "uuid", "") or "",
            node_title=getattr(node, "title", "") or "",
            node_created=getattr(node, "created", None),
            node_start_date=parent_date.start_value,
            node_start_precision=parent_date.start_precision,
            node_end_date=parent_date.end_value,
            node_end_precision=parent_date.end_precision,
            date_field=parent_date.start_field,
            date_field_value=parent_date.start_raw,
            end_date_field=parent_date.end_field,
            end_date_field_value=parent_date.end_raw,
            date_source=parent_date.source,
            bundle=getattr(node, "bundle", None),
            url=getattr(node, "url", None),
            pdf_count=count,
        ),
    )


def _read_pdf_signals(evidence: PdfEvidence, content: bytes) -> None:
    """Fill DocInfo and head text from bytes already in hand. PyMuPDF only."""
    from app.ingestion.date_candidates import read_pdf_docinfo

    created, modified = read_pdf_docinfo(content)
    text, title = read_pdf_head(content)
    evidence.pdf_created = created
    evidence.pdf_modified = modified
    evidence.pdf_title = title
    evidence.head_text = text
    evidence.front_text = read_pdf_front_matter(content)


def copyright_override(evidence: PdfEvidence) -> DateDecision | None:
    """A year-precision override from a corroborated copyright statement, or None.

    Fires only when every one of these holds:

    * the front matter names a copyright year (``© … 2020``, ``Ⓒ … 2020``,
      ``(c) 2020``, ``Copyright 2020``);
    * the PDF's DocInfo creation date names the **same** year — a second,
      independent statement by the document about itself. A statement alone
      is the LLM path's business (and a bare year is refused there as
      day-precision); a DocInfo date alone never moves anything
      (``test_a_pdf_creation_date_alone_never_moves_the_page_date``);
    * the year is plausible for this corpus;
    * the year differs from the page's own — agreeing with the page changes
      nothing, and the page's day is the finer value.

    The result is a *year*: 1 January as a marker, ``candidate_precision="year"``,
    exactly how ``research_papers`` store ``field_rpaper_year``. Nothing here
    invents a day, and nothing here reads a Drupal timestamp.

    Applies to any file whose bytes were read — see
    :func:`_wants_document_evidence` — which is every PDF sharing its page and
    every routed one. It is one deterministic rule inside the resolution model,
    not the model itself: a file it cannot settle falls back to the page's date
    or goes on to the interpreter, exactly as before.
    """
    from datetime import date

    from app.ingestion.date_evidence import parse_dt
    from app.ingestion.source_dates import as_stored_date, is_plausible

    found = copyright_statement(evidence.front_text)
    if found is None:
        return None
    statement, year = found
    created = parse_dt(evidence.pdf_created)
    if created is None or created.year != year:
        return None
    if not is_plausible(date(year, 1, 1)):
        return None
    page_date = parse_dt(evidence.page.effective_date)
    if page_date is not None and page_date.year == year:
        return None
    return DateDecision(
        document_id=evidence.document_id,
        action="propose_override",
        candidate_start_date=as_stored_date(date(year, 1, 1)),
        candidate_precision="year",
        date_type="publication",
        edition_label=evidence.edition,
        source="document_copyright",
        confidence=0.9,
        evidence=(
            f"The document's front matter states {statement!r} and its DocInfo "
            f"creation date is {evidence.pdf_created}; both name {year}, which "
            f"differs from the page's {str(evidence.page.effective_date)[:10]}. "
            f"Year precision: 1 January is a marker, not a day."
        ),
        rule="copyright_statement_corroborated",
        decided_by="deterministic",
        supporting_evidence=(
            "In-body file with no Drupal upload record on a page dated by its "
            "creation stamp; the file itself was the only evidence available."
        ),
        used=["drupal", "pdf_meta", "pdf_text"],
    )


def _document_was_read(decision: DateDecision, evidence: PdfEvidence) -> DateDecision:
    """Mark a decision as one taken with the file's own bytes in hand.

    Two things, and an audit needs both.

    The evidence tiers actually used are extended, so the read is not lost when a
    routed decision is re-taken after reading — ``decide`` builds a fresh
    decision each time and would otherwise report ``["drupal"]`` for a file whose
    first page the interpreter has just been shown.

    And where the outcome is still the page's date, the record says the document
    was consulted and stated nothing verifiable. ``evidence`` is the column that
    is persisted, so "why does this file carry its page's date?" has to be
    answerable from it rather than from silence. Only for a file that shares its
    page: a single-PDF branch already gives its own reason, and "one of 1 PDFs"
    would be nonsense.
    """
    used = [*decision.used,
            *(tier for tier in ("pdf_meta", "pdf_text") if tier not in decision.used)]
    already = "read for a date of its own" in (decision.evidence or "")
    if (
        decision.action != "keep_page_date"
        or already
        or not evidence.page.is_multi_pdf
    ):
        return replace(decision, used=used)
    return replace(
        decision,
        evidence=(
            f"{decision.evidence} One of {evidence.page.pdf_count} PDFs on this "
            f"page, so it was read for a date of its own; it states none that "
            f"could be verified, and the page's date stands as this file's "
            f"fallback."
        ).strip(),
        used=used,
    )


def _wants_document_evidence(decision: DateDecision, evidence: PdfEvidence) -> bool:
    """Whether this file's own bytes should be read before its date is settled.

    Two independent reasons, and they are different questions.

    ``needs_llm`` means the deterministic pass has already concluded the document
    is worth reading closely — a late upload, a migration import, a year in the
    link text.

    A **multi-PDF page** is the other, and it is a property of the file's
    situation rather than of any signal about it. Several PDFs on one page are
    several documents, so the page's date is this file's fallback and not its
    answer, and the deterministic rules are entitled to look first.

    A single-PDF page is deliberately absent from both. Its file is part of the
    page's own publication, inherits the page's date without being opened, and
    every single-PDF branch already says so.
    """
    return decision.action == "needs_llm" or evidence.page.is_multi_pdf


def resolve(evidence: PdfEvidence, content: bytes | None = None) -> ResolvedDate:
    """Decide this PDF's ``effective_start_date``.

    Fails closed: any unexpected error leaves the page date in place, because a
    stale date is recoverable and a wrong one is not.
    """
    page_date = evidence.page.effective_date
    try:
        decision = decide(evidence)
        used = list(decision.used)

        # Read the bytes at most once, and only where they are owed: a routed
        # decision, or a file that shares its page. PyMuPDF only — no OCR, no
        # Document Intelligence, no model.
        read = False
        if content and _wants_document_evidence(decision, evidence):
            _read_pdf_signals(evidence, content)
            read = True
            # Deterministic before paid. The copyright rule costs nothing and
            # its verdict is reproducible, so the interpreter is only ever asked
            # about what the rules could not settle.
            override = copyright_override(evidence)
            decision = override if override is not None else _document_was_read(
                decision, evidence
            )
            used = list(decision.used)

        if decision.action == "needs_llm":
            if content and not read:
                _read_pdf_signals(evidence, content)
                read = True
            # Reading the document may itself settle the case — an unreadable
            # PDF has nothing to say — so re-run the deterministic pass before
            # paying for a model call.
            decision = decide(evidence)
            if read:
                decision = _document_was_read(decision, evidence)
            used = list(decision.used)

        llm_raw: dict[str, Any] | None = None
        if decision.action == "needs_llm":
            decision, llm_raw = _interpret(evidence, decision)
            used.append("llm")

        # Only an override may move the date. Every other outcome — including a
        # review — keeps the page's own date on the document.
        overridden = decision.action == "propose_override"
        effective_start_date = decision.candidate_start_date if overridden else page_date
        return ResolvedDate(
            start_value=effective_start_date,
            start_precision=(decision.candidate_precision if overridden
                             else evidence.page.node_start_precision),
            # An override replaces the page's date with a day the document
            # itself states, which says nothing about a period — so the
            # inherited end goes with the date it belonged to.
            end_value=(None if overridden else evidence.page.effective_end),
            end_precision=(None if overridden
                                       else evidence.page.node_end_precision),
            edition_label=decision.edition_label,
            decision=decision,
            llm_raw=llm_raw,
            used=used,
        )
    except Exception:
        logger.warning(
            "Date resolution failed for %s; keeping the page date.",
            evidence.document_id, exc_info=True,
        )
        return ResolvedDate(start_value=page_date,
                            start_precision=evidence.page.node_start_precision,
                            end_value=evidence.page.effective_end,
                            end_precision=evidence.page.node_end_precision,
                            edition_label=evidence.edition)


def _interpret(
    evidence: PdfEvidence, deferred: DateDecision
) -> tuple[DateDecision, dict[str, Any] | None]:
    """Ask the model, then apply the validated gates to its verdict."""
    from app.ingestion.date_llm import interpret

    page_date = evidence.page.effective_date
    verdict = interpret(evidence)
    if verdict is None:
        # A model outage must never change a date.
        return (
            DateDecision(
                document_id=evidence.document_id, action="keep_page_date",
                candidate_start_date=page_date, date_type="unknown",
                edition_label=evidence.edition, source="node_effective_date",
                confidence=0.0, rule="llm_unavailable", decided_by="llm",
                evidence="Interpretation call failed; the page date was kept.",
                supporting_evidence=deferred.supporting_evidence,
                used=[*deferred.used, "llm"],
            ),
            None,
        )

    action = verdict.safe_action()
    precision = verdict.supported_precision() or "day"
    candidate = verdict.normalized_start_date()

    # A year-only verdict that agrees with the page's own year buys nothing and
    # costs the day the page states. The same guard `copyright_override` applies,
    # for the same reason: replacing 2019-01-11 with "2019, year precision" makes
    # the record vaguer without making it truer. A verdict naming a *different*
    # year is exactly the case worth acting on.
    if action == "override" and precision == "year":
        page_year = str(page_date or "")[:4]
        if candidate and page_year and candidate[:4] == page_year:
            logger.info(
                "Year-only verdict %s matches the page's own year; keeping the "
                "page date, which is more precise.", candidate,
            )
            action = "keep_page_date"

    mapped = {
        "override": "propose_override",
        "review": "needs_manual_review",
        "keep_page_date": "keep_page_date",
    }[action]
    return (
        DateDecision(
            document_id=evidence.document_id,
            action=mapped,
            candidate_start_date=(candidate if action == "override" else page_date),
            candidate_precision=(precision if action == "override" else "day"),
            date_type=verdict.date_type,
            edition_label=verdict.edition_label or evidence.edition,
            source=("llm_publication" if action == "override"
                    else "node_effective_date"),
            confidence=verdict.confidence,
            evidence=verdict.evidence,
            rule="llm_interpreted",
            decided_by="llm",
            supporting_evidence=(verdict.publication_statement or ""),
            used=[*deferred.used, "llm"],
        ),
        verdict.model_dump(),
    )
