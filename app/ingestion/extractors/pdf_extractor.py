from __future__ import annotations
import io
import logging
import re
from collections import defaultdict
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
    "PageContent",
    "ExtractionResult",
    "extract_pdf",
]

class ExtractedVia(str, Enum):

    OCR = "ocr"
    TEXT = "text"
    EMPTY = "empty"

@dataclass
class TableData:
    markdown: str
    page_number: int | None = None
    rows: int = 0
    cols: int = 0
    caption: str | None = None
    cells: list[list[str]] | None = None


@dataclass
class PageContent:

    page_number: int
    text: str
    extracted_via: ExtractedVia
    tables: list[TableData] = field(default_factory=list)


@dataclass
class ExtractionResult:

    source: str
    pages: list[PageContent]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text)

    @property
    def tables(self) -> list[TableData]:
        return [t for page in self.pages for t in page.tables]

    @property
    def table_count(self) -> int:
        return sum(len(page.tables) for page in self.pages)

    @property
    def ocr_page_numbers(self) -> list[int]:
        return [p.page_number for p in self.pages if p.extracted_via is ExtractedVia.OCR]


def _rows_to_markdown(rows: list[list[str]]) -> str:
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
    if "<table" not in text.lower():
        return text
    return _TABLE_RE.sub(
        lambda m: "\n\n" + _html_table_to_markdown(m.group(0)) + "\n\n", text
    )


def _page_count(content: bytes) -> int:
    try:
        from pypdf import PdfReader

        return len(PdfReader(io.BytesIO(content)).pages)
    except Exception:
        logger.warning("pypdf unavailable; page count derived from partition output.")
        return 0


def _partition_digital_text(content: bytes) -> dict[int, str]:
    try:
        from unstructured.partition.pdf import partition_pdf
    except Exception:
        logger.warning("unstructured unavailable; digital pages skipped.")
        return {}

    try:
        elements = partition_pdf(file=io.BytesIO(content), strategy="fast")
    except Exception:
        logger.exception("unstructured partition failed; digital pages skipped.")
        return {}

    by_page: dict[int, list[str]] = defaultdict(list)
    for el in elements:
        page_no = getattr(getattr(el, "metadata", None), "page_number", None)
        text = (getattr(el, "text", None) or "").strip()
        if page_no is not None and text:
            by_page[page_no].append(text)
    return {pn: "\n\n".join(parts).strip() for pn, parts in by_page.items()}


def _pypdf_pages_text(content: bytes) -> dict[int, str]:
    try:
        from pypdf import PdfReader
    except Exception:
        logger.warning("pypdf unavailable; digital fallback skipped.")
        return {}
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception:
        logger.exception("pypdf could not open document; digital fallback skipped.")
        return {}

    out: dict[int, str] = {}
    for i, page in enumerate(reader.pages, start=1):
        try:
            out[i] = (page.extract_text() or "").strip()
        except Exception:
            out[i] = ""
    return out


@lru_cache
def _di_client():
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
    parts: list[str] = []
    for span in getattr(page, "spans", None) or []:
        offset = int(getattr(span, "offset", 0) or 0)
        length = int(getattr(span, "length", 0) or 0)
        parts.append(content[offset : offset + length])
    return "".join(parts)


def _pages_from_di(result: Any, requested_pages: list[int] | None) -> dict[int, PageContent]:
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
            text = content
        text = _html_tables_to_pipe(text).strip()

        ptables = tables_by_page.get(page_no, [])
        via = ExtractedVia.OCR if (text or ptables) else ExtractedVia.EMPTY
        out[page_no] = PageContent(
            page_number=page_no, text=text, extracted_via=via, tables=ptables
        )
    return out


def _ocr_pdf(content: bytes, page_numbers: list[int] | None = None) -> dict[int, PageContent]:
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


# Standard ligature glyphs (Alphabetic Presentation Forms, U+FB00-FB06) carry
# meaning identical to their ASCII expansion but break embedding/keyword search
# because e.g. "conﬁrmed" != "confirmed". Expand them to plain ASCII.
_LIGATURES = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
    "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st",
}
_LIGATURE_RE = re.compile("[" + "".join(_LIGATURES) + "]")


def _normalize_text(text: str) -> str:
    if not text:
        return text
    return _LIGATURE_RE.sub(lambda m: _LIGATURES[m.group(0)], text)


def _finalize(filename: str, pages: list[PageContent]) -> ExtractionResult:
    for page in pages:
        page.text = _normalize_text(page.text)
        for table in page.tables:
            table.markdown = _normalize_text(table.markdown)
    result = ExtractionResult(source=filename, pages=pages)
    _log_summary(result, filename)
    return result


def extract_pdf(content: bytes, filename: str) -> ExtractionResult:
    settings = get_settings()
    text_by_page = _partition_digital_text(content)
    total_pages = _page_count(content) or (max(text_by_page) if text_by_page else 0)

    if total_pages == 0:
        pages_map = _ocr_pdf(content, None)
        pages = [pages_map[n] for n in sorted(pages_map)]
        return _finalize(filename, pages)

    pages_map: dict[int, PageContent] = {}
    scanned_page_numbers: list[int] = []
    pypdf_by_page: dict[int, str] | None = None
    for n in range(1, total_pages + 1):
        text = text_by_page.get(n, "")
        if len(text) < settings.pdf_scanned_char_threshold:
            if pypdf_by_page is None:
                pypdf_by_page = _pypdf_pages_text(content)
            fallback = pypdf_by_page.get(n, "")
            if len(fallback) > len(text):
                text = fallback
        if len(text) < settings.pdf_scanned_char_threshold:
            scanned_page_numbers.append(n)
        else:
            pages_map[n] = PageContent(
                page_number=n, text=text, extracted_via=ExtractedVia.TEXT
            )

    if scanned_page_numbers:
        pages_map.update(_ocr_pdf(content, scanned_page_numbers))

    pages = [
        pages_map.get(
            n, PageContent(page_number=n, text="", extracted_via=ExtractedVia.EMPTY)
        )
        for n in range(1, total_pages + 1)
    ]
    return _finalize(filename, pages)


def _log_summary(result: ExtractionResult, filename: str) -> None:
    ocr_pages = result.ocr_page_numbers
    logger.info(
        "Extracted %s: %d page(s), %d table(s)%s",
        filename,
        result.page_count,
        result.table_count,
        f"; OCR on page(s) {ocr_pages}" if ocr_pages else "",
    )


def _main(argv: list[str] | None = None) -> int:
    import argparse
    import sys
    from pathlib import Path

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Extract a PDF to structured Markdown.")
    parser.add_argument("path", help="Path to a .pdf file.")
    parser.add_argument("-n", "--pages", type=int, default=2, help="Pages to print (default: 2).")
    parser.add_argument("--full", action="store_true", help="Print full page text.")
    parser.add_argument("--chunk", action="store_true", help="Also run chunk_pdf and report counts.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    path = Path(args.path)
    result = extract_pdf(path.read_bytes(), path.name)

    by_source: dict[str, int] = {}
    for page in result.pages:
        by_source[page.extracted_via.value] = by_source.get(page.extracted_via.value, 0) + 1
    print(
        f"{path.name}: {result.page_count} page(s), {result.table_count} table(s) "
        f"· pages by source: {by_source}"
    )
    if result.ocr_page_numbers:
        print(f"  OCR pages: {result.ocr_page_numbers}")

    for page in result.pages[: args.pages]:
        print(
            f"\n=== page {page.page_number} via {page.extracted_via.value} "
            f"· {len(page.tables)} table(s) ==="
        )
        body = page.text if args.full else page.text[:1000] + ("…" if len(page.text) > 1000 else "")
        print(body)

    if args.chunk:
        from app.ingestion.chunker import chunk_pdf

        chunks = chunk_pdf(result)
        parents = sum(c.is_parent for c in chunks)
        print(f"\nchunks: {len(chunks)} ({parents} parents, {len(chunks) - parents} children)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
