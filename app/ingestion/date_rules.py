"""Deterministic half of PDF date resolution: keep the page date, or ask the LLM.

**This module can no longer propose a date change.** It returns either
``keep_page_date`` or ``needs_llm``. Every override in the system now originates
from :mod:`app.ingestion.date_llm`, and only from an explicit publication
statement in the document itself.

That is a deliberate narrowing after manual review. The previous version treated
a late upload as a publication date, which conflates two different facts: when a
file was *put on the server* and when the document was *released*. Drupal's
``file.created``, a ``/files/YYYY-MM/`` path, a PDF ``CreationDate``, a year in a
filename, a reporting period, an event date, a notification date and an
effective date are all evidence of something — but none of them is, by itself,
a publication date.

Upload timing keeps a job: it decides **where it is worth spending money**. A
PDF that Drupal recorded arriving long after its page is a good candidate for
having its own publication date, so it is routed to the LLM to look for one.
If the LLM finds nothing explicit, the page date stands. The upload facts are
carried on the decision as ``supporting_evidence`` so a reviewer can see what
triggered the look, but nothing acts on them.

What survives from the earlier analysis:

- **Single-PDF pages** default to the page date. Measured on the 439 attachments
  whose file arrived days-to-weeks after the node, 76% were authored within 30
  days of the node and 89% read as "written and posted together".
- **The 2017-2018 migration cohort** is real and must never be read as upload
  timing: 1406 of 1545 pre-cutoff files share four timestamps, one of them
  covering 397 files whose nodes span 13.5 years.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from app.ingestion.date_evidence import PdfEvidence, month_start, parse_dt

__all__ = [
    "DateDecision",
    "MIGRATION_END",
    "MIGRATION_START",
    "decide",
    "in_migration_cohort",
]

# The 2017-2018 content migration. `file.created` inside this window is an import
# timestamp, not an upload. Equivalent to fid <= 3760 on this site (verified zero
# overlap with post-cutoff fids), so either test identifies the same cohort.
MIGRATION_START = datetime(2017, 12, 1, tzinfo=timezone.utc)
MIGRATION_END = datetime(2018, 6, 1, tzinfo=timezone.utc)

# Upload divergence large enough to be worth an LLM look on a multi-PDF page.
# Below it the file is part of the page's own publication (measured median 14
# days between page creation and attachment).
SEPARATION_DAYS = 90

# On a single-PDF page the bar for even looking is a year: one PDF on a page is
# overwhelmingly that page's own document.
SINGLE_PDF_LOOK_DAYS = 365

# `decide` only ever returns the first three. "propose_override" exists because
# the LLM path builds a DateDecision from an interpreted verdict — it is the one
# action no deterministic rule can produce.
Action = Literal[
    "keep_page_date", "needs_llm", "needs_manual_review", "propose_override",
]
DateType = Literal[
    "publication", "upload", "authoring", "edition", "event",
    "notification", "effective", "unknown",
]


def in_migration_cohort(file_created: str | None) -> bool:
    """Is this file entity a 2017-2018 migration import rather than an upload?"""
    parsed = parse_dt(file_created)
    return parsed is not None and parsed < MIGRATION_END


@dataclass
class DateDecision:
    """A proposed outcome for one PDF. Never applied by this module."""

    document_id: str
    action: Action
    candidate_start_date: str | None = None
    date_type: DateType = "unknown"
    edition_label: str | None = None
    source: str = "node_effective_date"
    confidence: float = 0.0
    evidence: str = ""
    rule: str = ""
    decided_by: Literal["deterministic", "llm"] = "deterministic"
    #: Facts that justified *looking*, never a date change on their own.
    supporting_evidence: str = ""
    used: list[str] = field(default_factory=list)

    @property
    def would_move(self) -> bool:
        return self.action == "propose_override" and bool(self.candidate_start_date)


def _days(later: datetime | None, earlier: datetime | None) -> int | None:
    if later is None or earlier is None:
        return None
    return (later - earlier).days


def decide(evidence: PdfEvidence) -> DateDecision:
    """Keep the page date, or route to the LLM. Never proposes a change."""
    page = evidence.page
    node_dt = parse_dt(page.node_created)
    file_dt = parse_dt(evidence.file_created)
    pdf_dt = parse_dt(evidence.pdf_created)
    upload_dt = month_start(evidence.upload_month)

    base = {
        "document_id": evidence.document_id,
        "edition_label": evidence.edition,
        "date_type": "publication",
        # The page's *resolved* date, not its creation stamp: that is what a
        # kept decision actually assigns, so it is what the audit row has to
        # record. `node_dt` above stays the creation stamp because the upload-gap
        # arithmetic below is a question about when the page was made.
        "candidate_start_date": page.effective_date,
        "source": "node_effective_date",
    }

    if page.effective_date is None:
        return DateDecision(
            **base, action="needs_manual_review", confidence=0.0,
            rule="no_page_date", used=["drupal"],
            evidence="The page carries no date to fall back on.",
        )

    # ------------------------------------------------------------------ #
    # Case 0 — the page's bundle states its date in a CMS field.
    #
    # An attached file's date is its parent page's date. Where that date is one
    # the CMS states about this content type — a research paper's year, a press
    # release's date — the page is authoritative and there is nothing to look
    # for: reading the file could only produce a *different* date, which is
    # precisely what must not happen. Checked before every upload heuristic
    # because those exist to decide whether a weak page date is worth
    # questioning, and this page date is not weak.
    #
    # It is also what stops the file's own timestamps mattering: DocInfo,
    # `file.created` and the `/files/YYYY-MM/` month are never read on this path.
    # ------------------------------------------------------------------ #
    if page.date_from_bundle_field:
        return DateDecision(
            **base, action="keep_page_date", confidence=1.0,
            rule="parent_bundle_date_field", used=["drupal"],
            evidence=(
                f"The parent {page.bundle} page states its date in "
                f"{page.date_field} ({page.date_field_value!r}); an attached "
                f"file carries its page's date."
            ),
            supporting_evidence=(
                "File timestamps, upload month and PDF metadata were not read: "
                "the page's own field is authoritative."
            ),
        )

    # Upload divergence: recorded as context, never as a reason to change a date.
    upload_gap = _days(file_dt, node_dt)
    if upload_gap is None and upload_dt is not None:
        upload_gap = _days(upload_dt, node_dt)
    migrated = in_migration_cohort(evidence.file_created)
    if migrated:
        support = ("Drupal file date falls in the 2017-2018 migration import, so it "
                   "records the import, not an upload.")
    elif upload_gap is not None:
        where = "Drupal" if file_dt is not None else "the /files/YYYY-MM/ path"
        support = (f"{where} records the file arriving {upload_gap} days "
                   f"{'after' if upload_gap >= 0 else 'before'} the page was created.")
    else:
        support = "No upload record for this file (in-body link)."

    def keep(rule: str, why: str, confidence: float = 0.9) -> DateDecision:
        return DateDecision(
            **base, action="keep_page_date", confidence=confidence, rule=rule,
            evidence=why, supporting_evidence=support, used=["drupal"],
        )

    def look(rule: str, why: str) -> DateDecision:
        return DateDecision(
            **base, action="needs_llm", confidence=0.0, rule=rule,
            evidence=why, supporting_evidence=support, used=["drupal", "pdf_meta"],
        )

    # ------------------------------------------------------------------ #
    # Case 1 — single-PDF page.
    # ------------------------------------------------------------------ #
    if not page.is_multi_pdf:
        # A very late upload is worth *looking* at, but the page date stands
        # unless the document itself states a publication date.
        if (
            file_dt is not None
            and not migrated
            and (upload_gap or 0) > SINGLE_PDF_LOOK_DAYS
        ):
            return look(
                "single_pdf_late_upload_review",
                "Only PDF on the page, but it was uploaded more than a year later; "
                "checking the document for an explicit publication date.",
            )
        return keep(
            "single_pdf_page",
            "The page holds exactly one PDF, so the document is part of the page's "
            "own publication.",
        )

    # ------------------------------------------------------------------ #
    # Case 2 — multi-PDF page. Several PDFs does NOT by itself mean each has
    # its own publication date; it only makes that possible.
    # ------------------------------------------------------------------ #
    if file_dt is not None and not migrated:
        if (upload_gap or 0) > SEPARATION_DAYS:
            return look(
                "multi_pdf_late_upload_review",
                f"One of {page.pdf_count} PDFs on the page, uploaded well after it; "
                "checking the document for its own publication date.",
            )
        return keep(
            "multi_pdf_uploaded_with_page",
            f"One of {page.pdf_count} PDFs, uploaded within {SEPARATION_DAYS} days "
            "of the page — part of the page's own publication.",
            confidence=0.85,
        )

    if file_dt is None and upload_dt is not None:
        if (upload_gap or 0) > SEPARATION_DAYS:
            return look(
                "multi_pdf_url_month_review",
                "In-body PDF whose managed path shows it stored well after the page; "
                "checking the document for its own publication date.",
            )
        return keep(
            "multi_pdf_url_month_matches",
            f"Stored under /files/{evidence.upload_month}/, close to the page's date.",
            confidence=0.8,
        )

    if migrated:
        if pdf_dt is None and not evidence.head_text:
            return keep(
                "migration_cohort_no_evidence",
                "File date is a migration import and the PDF offers no readable "
                "evidence; nothing better than the page date.",
                confidence=0.5,
            )
        return look(
            "migration_cohort_review",
            "File date is a migration import, so only the document's own content "
            "could date it.",
        )

    # In-body PDF with no upload signal — the annual-report shape. Every edition
    # shares one page date and the only per-file evidence is textual.
    if pdf_dt is not None or evidence.head_text or evidence.edition or evidence.text_years:
        return look(
            "multi_pdf_textual_only",
            f"One of {page.pdf_count} PDFs with no Drupal upload record; the only "
            "per-document evidence is textual.",
        )

    return keep(
        "multi_pdf_no_evidence",
        "No per-document evidence of any kind; the page date stands.",
        confidence=0.5,
    )
