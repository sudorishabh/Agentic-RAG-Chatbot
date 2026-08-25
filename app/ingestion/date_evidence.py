"""Evidence about when one PDF was published — gathered cheapest-first.

The unit of analysis is a *page and its PDFs*, not a PDF alone, because the
question "does this PDF have its own date?" is unanswerable without knowing
whether the page holds one document or a shelf of them. :class:`PageContext`
carries that count; :class:`PdfEvidence` carries everything known about one file.

Cost ladder, cheapest first (see the Phase 0 report in ``reports/phase0``):

1. Drupal metadata already in the crawl payload — node date, file entity date,
   fid, bundle. Free.
2. String signals — filename, anchor text, URL path month. Free.
3. PDF DocInfo via PyMuPDF. One HTTP GET, no extraction.
4. First-page text via PyMuPDF. Same GET, ``page.get_text`` only.

Document Intelligence is never reachable from here: nothing in this module
imports :mod:`app.ingestion.extractors.pdf_extractor`.

Nothing here decides anything — see :mod:`app.ingestion.date_rules`.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.editions import EDITION_RE as _EDITION_RE
from app.core.editions import normalise_edition

logger = logging.getLogger(__name__)

__all__ = [
    "EDITION_RE",
    "PageContext",
    "PdfEvidence",
    "edition_label",
    "path_month",
    "read_pdf_head",
    "years_in",
]

# A fiscal/edition span: "2024-25", "2024-2025", "2024_25", "20-21". Re-exported
# from `app.core.editions`, which owns the rule so retrieval can apply the same
# one without importing ingestion internals.
EDITION_RE = _EDITION_RE
YEAR_RE = re.compile(r"(?<!\d)(19[89]\d|20[0-2]\d)(?!\d)")
# Drupal's managed upload directory carries the upload month in the path.
PATH_MONTH_RE = re.compile(r"/sites/default/files/(\d{4})-(\d{2})/")

# How much first-page text the LLM ever sees. A cover page states the title,
# edition and often a publication month well inside this; more would just be
# paying for a table of contents.
HEAD_CHARS = 2_500
HEAD_PAGES = 2


def years_in(*texts: str | None) -> set[int]:
    """Four-digit years mentioned in any of ``texts``."""
    found: set[int] = set()
    for text in texts:
        for match in YEAR_RE.findall(text or ""):
            found.add(int(match))
    return found


def edition_label(*texts: str | None) -> str | None:
    """A reporting-period label like ``2024-25``, if one of ``texts`` names one.

    Only consecutive spans count: "2024-25" is an edition, "2019-2024" is a
    range and "Report 2 - 3" is nothing. This deliberately produces a *label*
    and never a date — an annual report for 2024-25 was not published on any
    particular day that the label implies.

    The spelling rule itself lives in :func:`app.core.editions.normalise_edition`
    so that retrieval applies the identical one; this function adds only the
    "first of several fields wins" precedence.
    """
    for text in texts:
        label = normalise_edition(text)
        if label is not None:
            return label
    return None


def path_month(url: str | None) -> str | None:
    """``YYYY-MM`` upload month encoded in a managed Drupal file path."""
    match = PATH_MONTH_RE.search(url or "")
    return f"{match.group(1)}-{match.group(2)}" if match else None


def read_pdf_head(content: bytes) -> tuple[str, str | None]:
    """``(first-pages text, DocInfo title)`` using PyMuPDF only.

    ``page.get_text`` is the same local call the extraction pipeline's cheapest
    route uses. No OCR, no Azure, no table detection — a scanned PDF simply
    returns empty text here, which is the correct answer for "what can we read
    for free".
    """
    if not content:
        return "", None
    try:
        import fitz  # PyMuPDF

        parts: list[str] = []
        with fitz.open(stream=content, filetype="pdf") as doc:
            title = (doc.metadata or {}).get("title") or None
            for index in range(min(HEAD_PAGES, doc.page_count)):
                parts.append(doc[index].get_text("text") or "")
        text = " ".join(" ".join(parts).split())
        return text[:HEAD_CHARS], (title.strip() or None if title else None)
    except Exception:
        logger.debug("Could not read PDF head text.", exc_info=True)
        return "", None


@dataclass
class PageContext:
    """The Drupal page a PDF hangs on, and how many PDFs it holds.

    ``pdf_count`` is the whole point: one PDF means the file is almost certainly
    part of the page's own publication, several means the page may be a shelf
    that accreted documents over years. Counted across both origins, deduped by
    URL, because a container page mixes field attachments and in-body links.
    """

    node_uuid: str
    node_title: str = ""
    node_created: str | None = None
    bundle: str | None = None
    url: str | None = None
    pdf_count: int = 1
    #: Distinct upload months across the page's PDFs, where known. More than one
    #: is direct evidence the page accreted rather than being published at once.
    distinct_upload_months: int = 1

    @property
    def is_multi_pdf(self) -> bool:
        return self.pdf_count > 1


@dataclass
class PdfEvidence:
    """Everything known about one PDF, with the expensive fields optional."""

    document_id: str
    origin: str                       # "attachment" | "inbody"
    url: str | None = None
    filename: str | None = None
    anchor: str | None = None
    current_published_at: str | None = None

    # Tier 1-2: free.
    file_created: str | None = None   # None for in-body PDFs
    fid: int | None = None
    # Tier 3-4: one GET, PyMuPDF only.
    pdf_created: str | None = None
    pdf_modified: str | None = None
    pdf_title: str | None = None
    head_text: str = ""

    page: PageContext = field(default_factory=lambda: PageContext(node_uuid=""))

    # ------------------------------------------------------------------ #

    @property
    def upload_month(self) -> str | None:
        return path_month(self.url)

    @property
    def edition(self) -> str | None:
        """Reporting period named by the link text, filename or PDF title.

        Anchor text first: Phase 0 found it names the edition for 10/10 annual
        reports including the one whose filename carries no year at all.
        """
        return edition_label(self.anchor, self.filename, self.pdf_title)

    @property
    def text_years(self) -> set[int]:
        return years_in(self.anchor, self.filename, self.pdf_title)

    def evidence_dict(self) -> dict[str, object]:
        """The compact evidence bundle handed to the LLM.

        Metadata and a short text head — never the whole PDF. Keys are spelled
        out because the model is asked to reason about *which kind* of date each
        one is, and an unlabelled date soup makes that impossible.
        """
        return {
            "filename": self.filename,
            "link_text": self.anchor or None,
            "pdf_internal_title": self.pdf_title,
            "page_title": self.page.node_title or None,
            "page_created": self.page.node_created,
            "pdfs_on_this_page": self.page.pdf_count,
            "drupal_file_uploaded": self.file_created,
            "upload_month_from_url": self.upload_month,
            "pdf_creation_date": self.pdf_created,
            "pdf_modified_date": self.pdf_modified,
            "first_page_text": self.head_text or None,
        }


def parse_dt(value: str | None) -> datetime | None:
    """Tolerant ISO parse to aware UTC, or None."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def month_start(month: str | None) -> datetime | None:
    """``YYYY-MM`` -> the 15th of that month, aware UTC.

    Mid-month rather than the 1st: the value is only accurate to a month, and
    anchoring at the midpoint halves the worst-case error either way.
    """
    if not month:
        return None
    try:
        year, mon = month.split("-")
        return datetime(int(year), int(mon), 15, tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None
