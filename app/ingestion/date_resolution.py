"""The one place a PDF's ``published_at`` is decided.

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

**An override needs the document to say so.** Only
:mod:`app.ingestion.date_llm` can propose one, and only when its verdict
survives every gate — a quoted publication statement, that statement present in
the PDF's own text, the statement carrying the proposed date, publication
linkage, a stated day, and confidence at or above the threshold. Anything short
of that keeps the page date and, where a date was seen, leaves a review row.

Cost follows the same routing that was measured: the deterministic pass settles
the large majority for free, only the routed remainder has its text read, and
the model is called only for what survives that. Nothing here downloads
anything — the caller already holds the PDF bytes — and Document Intelligence is
unreachable, because this module does not import
:mod:`app.ingestion.extractors.pdf_extractor`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.ingestion.date_evidence import PageContext, PdfEvidence, read_pdf_head
from app.ingestion.date_rules import DateDecision, decide

logger = logging.getLogger(__name__)

__all__ = ["ResolvedDate", "build_evidence", "resolve"]


@dataclass
class ResolvedDate:
    """What ingestion should use, plus why.

    ``published_at`` is the only field that reaches the document. ``decision``
    carries the provenance for the shadow decision table and the review queue;
    it is deliberately not part of the document payload.
    """

    published_at: str | None
    #: The date the DOCUMENT states it was published, when one was verified.
    #: None otherwise - never an edition label, a PDF CreationDate or an
    #: upload time. Distinct from ``published_at`` above, whose meaning and
    #: assignment this change deliberately leaves untouched.
    document_published_at: str | None = None
    #: Precision of :attr:`published_at`. Inherited from the parent page, so a
    #: file hanging off a research paper is year-precision too and no reader
    #: renders its 1 January as a day. ``day`` for an override, which by
    #: definition quoted a stated day.
    precision: str = "day"
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
    from app.ingestion.bundle_dates import resolve

    files = getattr(node, "files", None) or []
    count = page_pdf_count if page_pdf_count is not None else max(1, len(files))
    if parent_date is None:
        parent_date = resolve(
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
            node_published_at=parent_date.value,
            node_precision=parent_date.precision,
            date_field=parent_date.field,
            date_field_value=parent_date.raw_value,
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


def resolve(evidence: PdfEvidence, content: bytes | None = None) -> ResolvedDate:
    """Decide this PDF's ``published_at``.

    Fails closed: any unexpected error leaves the page date in place, because a
    stale date is recoverable and a wrong one is not.
    """
    page_date = evidence.page.effective_date
    try:
        decision = decide(evidence)
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
        published_at = decision.candidate_date if overridden else page_date
        return ResolvedDate(
            published_at=published_at,
            precision=("day" if overridden else evidence.page.node_precision),
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
        return ResolvedDate(published_at=page_date,
                            precision=evidence.page.node_precision,
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
                candidate_date=page_date, date_type="unknown",
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
            candidate_date=(verdict.candidate_date if action == "override"
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
