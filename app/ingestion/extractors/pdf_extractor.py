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


def _local_extract(content: bytes, filename: str, *, mode: str, route: str) -> ExtractionResult:
    """Text-only PyMuPDF extraction (never keeps tables)."""
    from app.ingestion.extractors.pymupdf_local import extract_local

    result = extract_local(content, filename)
    result.metadata.update({"extraction_mode": mode, "route": route})
    return result


def _azure_extract(content: bytes, filename: str) -> ExtractionResult | None:
    """Send the WHOLE document to Azure Layout; None if Azure is unavailable.

    Used by EXTRACTION_MODE=azure_only and as the hybrid fallback when page
    classification itself fails.
    """
    pages_map = _ocr_pdf(content, None)
    if not pages_map:
        return None
    pages = [pages_map[n] for n in sorted(pages_map)]
    return ExtractionResult(source=filename, pages=pages)


def _azure_with_fallback(content: bytes, filename: str, *, mode: str) -> ExtractionResult:
    """Azure whole-document extraction, falling back to local text if Azure fails."""
    result = _azure_extract(content, filename)
    if result is not None:
        result.metadata.update({"extraction_mode": mode, "route": "azure"})
        return result
    logger.warning(
        "%s routed to Azure but Azure is unavailable; falling back to local "
        "PyMuPDF text (tables on this document will degrade to plain text).",
        filename,
    )
    return _local_extract(content, filename, mode=mode, route="azure_unavailable_local_fallback")


def _signal_summary(signals: list) -> dict[str, Any]:
    return {
        "pages": len(signals),
        "scanned": sorted(s.page_number for s in signals if s.scanned),
        "table": sorted(s.page_number for s in signals if s.has_table),
        "needs_azure": sorted(s.page_number for s in signals if s.needs_azure),
    }


def _hybrid_extract(content: bytes, filename: str, *, mode: str) -> ExtractionResult:
    """Classify each page, then route PER PAGE and stitch the result in order.

    Clean born-digital pages extract locally with PyMuPDF; scanned/table pages
    go to Azure (which owns every table). If classification fails entirely we
    bias to Azure for the whole document.

    STEP 5 (optional, OFF — ``settings.extraction_azure_page_ranges``): a table
    spanning a page break can be split if only one of the two pages is flagged.
    When enabled we would expand each table page to include its neighbours so
    the whole table reaches Azure intact. Not wired up yet.
    """
    from app.ingestion.extractors.pymupdf_local import classify_document, extract_local_pages

    try:
        signals = classify_document(content)
    except Exception:
        logger.exception(
            "Page classification failed for %s; sending whole document to Azure.", filename
        )
        return _azure_with_fallback(content, filename, mode=mode)

    total = len(signals)
    azure_pages = [s.page_number for s in signals if s.needs_azure]
    local_pages = [s.page_number for s in signals if not s.needs_azure]

    pages_map: dict[int, PageContent] = {}
    route = "local"
    if azure_pages:
        di = _ocr_pdf(content, azure_pages)
        if di:
            pages_map.update(di)
            route = "per_page"
        else:
            logger.warning(
                "Azure unavailable for %s; %d flagged page(s) fall back to local "
                "PyMuPDF text (tables on those pages degrade to plain text).",
                filename,
                len(azure_pages),
            )
            local_pages = [s.page_number for s in signals]  # everything local
            route = "azure_unavailable_local_fallback"

    if local_pages:
        pages_map.update(extract_local_pages(content, local_pages))

    pages = [
        pages_map.get(n, PageContent(page_number=n, text="", extracted_via=ExtractedVia.EMPTY))
        for n in range(1, total + 1)
    ]
    result = ExtractionResult(source=filename, pages=pages)
    result.metadata.update({"extraction_mode": mode, "route": route})
    result.metadata["page_signals"] = _signal_summary(signals)
    return result


def extract_pdf(content: bytes, filename: str) -> ExtractionResult:
    settings = get_settings()
    mode = (settings.extraction_mode or "hybrid").strip().lower()
    if mode not in ("hybrid", "azure_only", "local_only"):
        logger.warning("Unknown EXTRACTION_MODE %r; using 'hybrid'.", mode)
        mode = "hybrid"

    if mode == "local_only":
        result = _local_extract(content, filename, mode=mode, route="local")
    elif mode == "azure_only":
        result = _azure_with_fallback(content, filename, mode=mode)
    else:  # hybrid
        result = _hybrid_extract(content, filename, mode=mode)

    _normalize_result(result)
    _log_summary(result, filename)
    return result


def _normalize_result(result: ExtractionResult) -> None:
    """Strip layout boilerplate from every page's text (in place)."""
    from app.ingestion.extractors.text_normalize import normalize_page_text

    for page in result.pages:
        page.text = normalize_page_text(page.text)


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
