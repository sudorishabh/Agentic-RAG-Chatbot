"""PyMuPDF (fitz) page classification + local text extraction.

This module owns the *local* side of the hybrid router (see ``pdf_extractor``):

* ``classify_document`` inspects every page with PyMuPDF and reports, per page,
  whether it looks scanned or carries a table — the signals the document-level
  router uses to decide between the local path and Azure.
* ``extract_local`` extracts a born-digital document as text only and emits the
  same canonical ``ExtractionResult`` the rest of the pipeline already expects.

Tables are never *kept* from the local path. Detection here is used purely to
route: if any page needs Azure, the whole document goes to Azure (which owns
every table). The local path handles text-only documents.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass

from app.config import get_settings

# Reuse the frozen public types so both extraction paths emit one structure.
from app.ingestion.extractors.pdf_extractor import (
    ExtractedVia,
    ExtractionResult,
    PageContent,
)

logger = logging.getLogger(__name__)

__all__ = [
    "PageSignal",
    "classify_document",
    "document_needs_azure",
    "extract_local",
]


@dataclass
class PageSignal:
    """Per-page routing signals derived with PyMuPDF."""

    page_number: int
    char_count: int
    scanned: bool
    has_table: bool

    @property
    def needs_azure(self) -> bool:
        return self.scanned or self.has_table


def _open(content: bytes):
    import fitz  # PyMuPDF

    return fitz.open(stream=content, filetype="pdf")


def _page_text(page) -> str:
    return (page.get_text("text") or "").strip()


def _drawing_line_count(page) -> int:
    """Count ruling-line / rectangle segments on the page (table grid signal)."""
    count = 0
    for drawing in page.get_drawings():
        for item in drawing.get("items", ()):
            op = item[0] if item else ""
            if op == "l":  # straight line segment
                count += 1
            elif op == "re":  # rectangle = 4 ruling lines
                count += 4
    return count


def _has_aligned_columns(page, min_rows: int) -> bool:
    """Borderless-table heuristic: several lines share >=2 word-start columns."""
    words = page.get_text("words")
    if not words:
        return False

    lines: dict[tuple, list[int]] = defaultdict(list)
    for w in words:
        x0 = int(round(w[0] / 5.0)) * 5  # quantize x-start to a 5pt grid
        block_no, line_no = w[5], w[6]
        lines[(block_no, line_no)].append(x0)

    column_positions: Counter = Counter()
    multi_column_lines = 0
    for xs in lines.values():
        distinct = sorted(set(xs))
        if len(distinct) >= 2:  # a line spanning multiple columns
            multi_column_lines += 1
            for x in distinct:
                column_positions[x] += 1

    if multi_column_lines < min_rows:
        return False
    # At least two column positions each shared by >= min_rows lines.
    shared = [x for x, c in column_positions.items() if c >= min_rows]
    return len(shared) >= 2


def _page_has_table(page, settings) -> bool:
    # (a) PyMuPDF's own table finder.
    try:
        finder = page.find_tables()
        if getattr(finder, "tables", None):
            return True
    except Exception:
        logger.debug("find_tables failed on a page; ignoring.", exc_info=True)

    # (b) Dense ruling-line / rectangle grid.
    try:
        if _drawing_line_count(page) >= settings.pdf_table_drawing_threshold:
            return True
    except Exception:
        logger.debug("get_drawings failed on a page; ignoring.", exc_info=True)

    # (c) Optional borderless-table detection via whitespace-column alignment.
    if settings.pdf_detect_borderless_tables:
        try:
            if _has_aligned_columns(page, settings.pdf_borderless_min_aligned_rows):
                return True
        except Exception:
            logger.debug("borderless detection failed on a page; ignoring.", exc_info=True)

    return False


def classify_document(content: bytes) -> list[PageSignal]:
    """Classify every page; pages drive the document-level routing decision."""
    settings = get_settings()
    signals: list[PageSignal] = []
    doc = _open(content)
    try:
        for i, page in enumerate(doc, start=1):
            text = _page_text(page)
            scanned = len(text) < settings.pdf_scanned_char_threshold
            has_table = _page_has_table(page, settings)
            signals.append(
                PageSignal(
                    page_number=i,
                    char_count=len(text),
                    scanned=scanned,
                    has_table=has_table,
                )
            )
    finally:
        doc.close()
    return signals


def document_needs_azure(signals: list[PageSignal]) -> bool:
    """A document needs Azure if ANY page is scanned or carries a table."""
    return any(s.needs_azure for s in signals)


def extract_local(content: bytes, filename: str) -> ExtractionResult:
    """Extract a born-digital document as text only (no tables kept)."""
    pages: list[PageContent] = []
    doc = _open(content)
    try:
        for i, page in enumerate(doc, start=1):
            text = _page_text(page)
            via = ExtractedVia.TEXT if text else ExtractedVia.EMPTY
            pages.append(
                PageContent(page_number=i, text=text, extracted_via=via, tables=[])
            )
    finally:
        doc.close()
    return ExtractionResult(
        source=filename, pages=pages, metadata={"engine": "pymupdf"}
    )
