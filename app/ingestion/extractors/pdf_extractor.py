"""PDF extraction → structured Markdown for the chunker.

Each PDF is routed by content type, page by page:

* **Digital** pages (a real, extractable text layer) → **Docling**: layout
  analysis, reading order, TableFormer table structure and figure crops,
  exported as Markdown.
* **Scanned** pages (image-only) → **Azure Document Intelligence**
  (``prebuilt-layout``): OCR plus table structure, returned as Markdown.

Tables are emitted as GitHub-flavoured Markdown and figures as captioned
placeholders — both of which the Markdown-aware
:mod:`app.ingestion.chunker` keeps intact (so a scanned table still lands in
one chunk, and a figure's caption is searchable). The public entry point is
:func:`extract_pdf`, returning an :class:`ExtractionResult` that
``chunk_pdf`` consumes directly.

Heavy/optional dependencies (``pypdfium2``, ``azure-ai-documentintelligence``,
``docling``) are imported lazily so importing this module stays cheap and the
core degrades gracefully when one of them is missing.

Build status: this step implements the data model, the page classifier and the
Azure OCR path. The digital path currently uses a pypdfium2 plain-text fallback;
Docling (tables, figures, layout) and AI figure captions are layered on next.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from html.parser import HTMLParser
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

__all__ = [
    "ExtractedVia",
    "TableData",
    "ImageData",
    "PageContent",
    "ExtractionResult",
    "extract_pdf",
]


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
class ExtractedVia(str, Enum):
    """How a page's text was recovered."""

    DOCLING = "docling"  # digital text layer via Docling (layout + tables + figures)
    OCR = "ocr"  # recovered via Azure Document Intelligence OCR
    TEXT = "text"  # plain text layer via pypdfium2 (fallback when Docling is off)
    EMPTY = "empty"  # no text could be recovered


@dataclass
class TableData:
    """One extracted table, kept both as Markdown (for chunking/retrieval) and,
    when available, as a structured cell grid (for downstream/metadata use)."""

    markdown: str  # GitHub-flavoured pipe table: "| a | b |\n| --- | --- |\n..."
    page_number: int | None = None
    rows: int = 0
    cols: int = 0
    caption: str | None = None
    cells: list[list[str]] | None = None  # row-major, if the source exposed it


@dataclass
class ImageData:
    """One extracted figure/picture. Image bytes are written to disk by the
    figure step; this record carries the reference plus any caption/description."""

    page_number: int | None = None
    index: int = 0  # ordinal within the document
    path: str | None = None  # saved image file, if extracted
    caption: str | None = None  # caption text from the document, if any
    classification: str | None = None  # Docling picture class (chart, logo, ...)
    description: str | None = None  # AI/VLM-generated description (searchable)
    width: int | None = None
    height: int | None = None


@dataclass
class PageContent:
    """One page's content as Markdown, plus its structured tables/figures."""

    page_number: int  # 1-based
    text: str
    extracted_via: ExtractedVia
    tables: list[TableData] = field(default_factory=list)
    images: list[ImageData] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """The full result of extracting one PDF. Duck-compatible with
    ``chunk_pdf`` (which reads ``source``, ``pages[].page_number``,
    ``pages[].text`` and ``page_count``)."""

    source: str  # original filename
    pages: list[PageContent]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        """All page text joined in reading order."""
        return "\n\n".join(page.text for page in self.pages if page.text)

    @property
    def tables(self) -> list[TableData]:
        return [t for page in self.pages for t in page.tables]

    @property
    def images(self) -> list[ImageData]:
        return [im for page in self.pages for im in page.images]

    @property
    def table_count(self) -> int:
        return sum(len(page.tables) for page in self.pages)

    @property
    def image_count(self) -> int:
        return sum(len(page.images) for page in self.pages)

    @property
    def ocr_page_numbers(self) -> list[int]:
        return [p.page_number for p in self.pages if p.extracted_via is ExtractedVia.OCR]


# --------------------------------------------------------------------------- #
# Markdown table helpers (shared by the OCR and, later, the Docling path)
# --------------------------------------------------------------------------- #
def _rows_to_markdown(rows: list[list[str]]) -> str:
    """Render a row-major cell grid as a GitHub-flavoured pipe table. The first
    row is treated as the header (what the chunker keys on to keep it atomic)."""
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]

    def esc(cell: str) -> str:
        return " ".join(cell.split()).replace("|", r"\|")

    lines = ["| " + " | ".join(esc(c) for c in rows[0]) + " |"]
    lines.append("| " + " | ".join(["---"] * width) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(esc(c) for c in row) + " |")
    return "\n".join(lines)


class _HTMLTableParser(HTMLParser):
    """Collect ``<table>`` cell text into a row-major grid. Azure's Markdown
    output renders tables as HTML to preserve merged cells; we flatten that to a
    pipe table the chunker understands. ``colspan`` is honoured by repeating the
    cell so column alignment is preserved; ``rowspan`` is not back-filled."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._buf: list[str] | None = None
        self._span = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._buf = []
            self._span = 1
            for name, value in attrs:
                if name.lower() == "colspan" and value and value.isdigit():
                    self._span = max(1, int(value))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in ("td", "th") and self._row is not None and self._buf is not None:
            text = " ".join("".join(self._buf).split())
            self._row.extend([text] * self._span)
            self._buf = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data: str) -> None:
        if self._buf is not None:
            self._buf.append(data)


_TABLE_RE = re.compile(r"<table\b.*?</table>", re.IGNORECASE | re.DOTALL)


def _html_table_to_markdown(html: str) -> str:
    parser = _HTMLTableParser()
    parser.feed(html)
    return _rows_to_markdown(parser.rows)


def _html_tables_to_pipe(text: str) -> str:
    """Replace any HTML ``<table>`` blocks in ``text`` with pipe tables, leaving
    the surrounding Markdown untouched."""
    if "<table" not in text.lower():
        return text
    return _TABLE_RE.sub(
        lambda m: "\n\n" + _html_table_to_markdown(m.group(0)) + "\n\n", text
    )


# --------------------------------------------------------------------------- #
# Page classification (pypdfium2)
# --------------------------------------------------------------------------- #
def _classify_pages(content: bytes, scanned_char_threshold: int) -> list[bool]:
    """Return a per-page list where ``True`` means the page is *scanned*
    (text layer shorter than ``scanned_char_threshold`` characters → route to
    OCR). Returns ``[]`` if pypdfium2 is unavailable, so the caller can fall
    back to whole-document OCR."""
    try:
        import pypdfium2 as pdfium
    except Exception:
        logger.warning(
            "pypdfium2 unavailable; cannot classify pages (will rely on OCR)."
        )
        return []

    flags: list[bool] = []
    pdf = pdfium.PdfDocument(content)
    try:
        for i in range(len(pdf)):
            page = pdf[i]
            textpage = page.get_textpage()
            try:
                text = textpage.get_text_range() or ""
            finally:
                textpage.close()
                page.close()
            flags.append(len(text.strip()) < scanned_char_threshold)
    finally:
        pdf.close()
    return flags


# --------------------------------------------------------------------------- #
# Digital path — interim pypdfium2 plain text (Docling lands next step)
# --------------------------------------------------------------------------- #
def _extract_digital_text(content: bytes, page_indices: list[int]) -> dict[int, PageContent]:
    """Extract the given 0-based pages' text layer with pypdfium2.

    This is the fallback digital extractor — Docling becomes the primary digital
    engine (adding tables, figures and layout) in the next step, with this kept
    for when Docling is unavailable or errors on a document. Returns
    ``{page_number(1-based): PageContent}``.
    """
    try:
        import pypdfium2 as pdfium
    except Exception:
        logger.warning("pypdfium2 unavailable; digital pages skipped.")
        return {}

    out: dict[int, PageContent] = {}
    pdf = pdfium.PdfDocument(content)
    try:
        for i in page_indices:
            page = pdf[i]
            textpage = page.get_textpage()
            try:
                text = (textpage.get_text_range() or "").strip()
            finally:
                textpage.close()
                page.close()
            via = ExtractedVia.TEXT if text else ExtractedVia.EMPTY
            out[i + 1] = PageContent(page_number=i + 1, text=text, extracted_via=via)
    finally:
        pdf.close()
    return out


# --------------------------------------------------------------------------- #
# Scanned path — Azure Document Intelligence
# --------------------------------------------------------------------------- #
@lru_cache
def _di_client():
    """Build the Document Intelligence client, or ``None`` if it isn't configured."""
    settings = get_settings()
    if not (
        settings.azure_document_intelligence_endpoint
        and settings.azure_document_intelligence_key
    ):
        return None

    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    return DocumentIntelligenceClient(
        endpoint=settings.azure_document_intelligence_endpoint,
        credential=AzureKeyCredential(settings.azure_document_intelligence_key),
    )


def _page_range_str(page_numbers: list[int]) -> str:
    """Compact a sorted page list into Azure's ``pages`` syntax, e.g. ``"1-3,5"``."""
    nums = sorted(set(page_numbers))
    parts: list[str] = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        parts.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = n
    parts.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ",".join(parts)


def _di_table_to_data(table: Any) -> TableData:
    """Convert an Azure ``DocumentTable`` into a :class:`TableData`."""
    n_rows = int(getattr(table, "row_count", 0) or 0)
    n_cols = int(getattr(table, "column_count", 0) or 0)
    grid = [["" for _ in range(n_cols)] for _ in range(n_rows)]
    for cell in getattr(table, "cells", None) or []:
        r = int(getattr(cell, "row_index", 0) or 0)
        c = int(getattr(cell, "column_index", 0) or 0)
        if 0 <= r < n_rows and 0 <= c < n_cols:
            grid[r][c] = " ".join((getattr(cell, "content", "") or "").split())

    page_no = None
    regions = getattr(table, "bounding_regions", None) or []
    if regions:
        page_no = getattr(regions[0], "page_number", None)

    return TableData(
        markdown=_rows_to_markdown(grid),
        page_number=page_no,
        rows=n_rows,
        cols=n_cols,
        cells=grid or None,
    )


def _slice_page_text(content: str, page: Any) -> str:
    """Slice a page's portion out of the full ``result.content`` using its spans."""
    parts: list[str] = []
    for span in getattr(page, "spans", None) or []:
        offset = int(getattr(span, "offset", 0) or 0)
        length = int(getattr(span, "length", 0) or 0)
        parts.append(content[offset : offset + length])
    return "".join(parts)


def _pages_from_di(result: Any, requested_pages: list[int] | None) -> dict[int, PageContent]:
    """Turn an Azure ``AnalyzeResult`` into ``{page_number: PageContent}``."""
    content = getattr(result, "content", "") or ""
    di_pages = list(getattr(result, "pages", None) or [])

    tables_by_page: dict[int, list[TableData]] = {}
    for table in getattr(result, "tables", None) or []:
        td = _di_table_to_data(table)
        tables_by_page.setdefault(td.page_number or 0, []).append(td)

    out: dict[int, PageContent] = {}
    for i, page in enumerate(di_pages):
        page_no = getattr(page, "page_number", None)
        if page_no is None:
            page_no = requested_pages[i] if requested_pages and i < len(requested_pages) else i + 1

        text = _slice_page_text(content, page)
        if not text and len(di_pages) == 1:
            # Single-page analysis without spans → the whole content is this page.
            text = content
        text = _html_tables_to_pipe(text).strip()

        ptables = tables_by_page.get(page_no, [])
        via = ExtractedVia.OCR if (text or ptables) else ExtractedVia.EMPTY
        out[page_no] = PageContent(
            page_number=page_no, text=text, extracted_via=via, tables=ptables
        )
    return out


def _ocr_pdf(content: bytes, page_numbers: list[int] | None = None) -> dict[int, PageContent]:
    """OCR the given 1-based pages (all pages if ``None``) via Azure Document
    Intelligence. Returns ``{}`` (and logs) when DI isn't configured."""
    client = _di_client()
    if client is None:
        logger.warning(
            "Azure Document Intelligence is not configured; %s scanned page(s) skipped.",
            len(page_numbers) if page_numbers else "all",
        )
        return {}

    settings = get_settings()
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

    kwargs: dict[str, Any] = {"body": AnalyzeDocumentRequest(bytes_source=content)}
    if page_numbers:
        kwargs["pages"] = _page_range_str(page_numbers)
    # Prefer Markdown output (preserves headings/tables); harmless to skip if the
    # installed SDK predates the option.
    try:
        from azure.ai.documentintelligence.models import DocumentContentFormat

        kwargs["output_content_format"] = DocumentContentFormat.MARKDOWN
    except Exception:
        pass

    try:
        poller = client.begin_analyze_document(
            settings.azure_document_intelligence_model, **kwargs
        )
        result = poller.result()
    except Exception:
        logger.exception("Azure Document Intelligence OCR failed; scanned pages skipped.")
        return {}

    return _pages_from_di(result, page_numbers)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def extract_pdf(content: bytes, filename: str) -> ExtractionResult:
    """Extract a PDF into per-page Markdown with tables (and, later, figures).

    Digital pages go through the text path; image-only pages go through Azure
    OCR. The two are merged back into page order so downstream chunking and
    citations keep correct page numbers.
    """
    settings = get_settings()
    scanned_flags = _classify_pages(content, settings.pdf_scanned_char_threshold)

    pages_map: dict[int, PageContent] = {}

    if not scanned_flags:
        # Classification unavailable (no pypdfium2 / unreadable) → whole-doc OCR.
        pages_map = _ocr_pdf(content, None)
        pages = [pages_map[n] for n in sorted(pages_map)]
        result = ExtractionResult(source=filename, pages=pages)
        _log_summary(result, filename)
        return result

    digital_indices = [i for i, scanned in enumerate(scanned_flags) if not scanned]
    scanned_page_numbers = [i + 1 for i, scanned in enumerate(scanned_flags) if scanned]

    if digital_indices:
        pages_map.update(_extract_digital_text(content, digital_indices))
    if scanned_page_numbers:
        pages_map.update(_ocr_pdf(content, scanned_page_numbers))

    pages = [
        pages_map.get(
            n, PageContent(page_number=n, text="", extracted_via=ExtractedVia.EMPTY)
        )
        for n in range(1, len(scanned_flags) + 1)
    ]
    result = ExtractionResult(source=filename, pages=pages)
    _log_summary(result, filename)
    return result


def _log_summary(result: ExtractionResult, filename: str) -> None:
    ocr_pages = result.ocr_page_numbers
    logger.info(
        "Extracted %s: %d page(s), %d table(s), %d image(s)%s",
        filename,
        result.page_count,
        result.table_count,
        result.image_count,
        f"; OCR on page(s) {ocr_pages}" if ocr_pages else "",
    )
