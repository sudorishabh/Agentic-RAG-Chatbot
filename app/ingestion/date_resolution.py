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
``/files/YYYY-MM/`` path, carrying a later PDF ``CreationDate``, naming a year
in its filename, or sharing a page with other PDFs are all *supporting signals*:
they decide whether a document is worth reading closely, and never set a date.

**An override needs the document to say so.** Two paths can propose one, and
both require the document's own text. :mod:`app.ingestion.date_llm` proposes a
*day* when its verdict survives every gate — a quoted publication statement,
that statement present in the PDF's own text, the statement carrying the
proposed date, publication linkage, a stated day, and confidence at or above
the threshold. :func:`copyright_override`, the one deterministic override,
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

#: The deterministic pass outcome that means "nothing Drupal-side to go on".
#: Only this outcome earns a free read of the file for the copyright rule.
_NO_EVIDENCE_RULE = "multi_pdf_no_evidence"


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


def resolve(evidence: PdfEvidence, content: bytes | None = None) -> ResolvedDate:
    """Decide this PDF's ``effective_start_date``.

    Fails closed: any unexpected error leaves the page date in place, because a
    stale date is recoverable and a wrong one is not.
    """
    page_date = evidence.page.effective_date
    try:
        decision = decide(evidence)
        used = list(decision.used)

        # Nothing Drupal-side to go on, and the bytes are in hand: read them
        # once (PyMuPDF, no model) for the one deterministic override. When it
        # does not fire the original decision stands unchanged — this branch
        # deliberately does not re-run `decide`, which would now see a DocInfo
        # date and route the file to the model. That routing is not this
        # rule's to widen.
        if decision.rule == _NO_EVIDENCE_RULE and content:
            _read_pdf_signals(evidence, content)
            override = copyright_override(evidence)
            if override is not None:
                decision = override
            else:
                decision = replace(
                    decision,
                    supporting_evidence=(
                        f"{decision.supporting_evidence} The file was read; it "
                        "carries no copyright statement corroborated by its "
                        "DocInfo date."
                    ).strip(),
                    used=[*decision.used, "pdf_meta", "pdf_text"],
                )
            used = list(decision.used)

        if decision.action == "needs_llm":
            if content:
                _read_pdf_signals(evidence, content)
            # Reading the document may itself settle the case — an unreadable
            # PDF has nothing to say — so re-run the deterministic pass before
            # paying for a model call.
            decision = decide(evidence)
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
    mapped = {
        "override": "propose_override",
        "review": "needs_manual_review",
        "keep_page_date": "keep_page_date",
    }[action]
    return (
        DateDecision(
            document_id=evidence.document_id,
            action=mapped,
            candidate_start_date=(verdict.candidate_start_date if action == "override"
                            else page_date),
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
