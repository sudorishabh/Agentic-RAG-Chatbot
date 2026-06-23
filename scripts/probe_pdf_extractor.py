"""Temporary manual probe for the PDF extractor.

This script is intentionally separate from the app. Use it to inspect how a PDF
is extracted, tune thresholds, then delete it when the extractor feels right.

Usage:
    python scripts/probe_pdf_extractor.py path/to/file.pdf
    python scripts/probe_pdf_extractor.py path/to/file.pdf --show-text --show-tables
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.ingestion.extractors.pdf_extractor import (
    ExtractedVia,
    ExtractionResult,
    extract_pdf,
)


def main() -> int:
    args = _parse_args()
    _configure_logging(args.verbose_logs)
    pdf_path = args.pdf_path
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1
    if not pdf_path.is_file():
        print(f"Path is not a file: {pdf_path}", file=sys.stderr)
        return 1

    result = extract_pdf(pdf_path.read_bytes(), pdf_path.name)
    _print_result(result, args)
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect extraction diagnostics for a single PDF."
    )
    parser.add_argument("pdf_path", type=Path, help="Path to the PDF to inspect.")
    parser.add_argument(
        "--show-text",
        action="store_true",
        help="Print extracted page text samples.",
    )
    parser.add_argument(
        "--show-tables",
        action="store_true",
        help="Print Markdown table previews.",
    )
    parser.add_argument(
        "--sample-chars",
        type=int,
        default=700,
        help="Characters to print per page/table preview. Default: 700.",
    )
    parser.add_argument(
        "--pages",
        type=str,
        default="",
        help="Comma-separated page numbers to print. Empty means all pages.",
    )
    parser.add_argument(
        "--verbose-logs",
        action="store_true",
        help="Show extractor logging, including exception stack traces.",
    )
    return parser.parse_args()


def _configure_logging(verbose_logs: bool) -> None:
    if verbose_logs:
        logging.basicConfig(level=logging.INFO)
        return
    logging.getLogger("app.ingestion.extractors.pdf_extractor").setLevel(
        logging.CRITICAL
    )


def _print_result(result: ExtractionResult, args: argparse.Namespace) -> None:
    selected_pages = _selected_pages(args.pages)
    pages = [
        page
        for page in result.pages
        if selected_pages is None or page.page_number in selected_pages
    ]

    empty_pages = [
        page.page_number
        for page in result.pages
        if page.extracted_via is ExtractedVia.EMPTY
    ]
    print(f"Source: {result.source}")
    print(f"Pages: {result.page_count}")
    print(f"Tables: {result.table_count}")
    print(f"OCR pages: {result.ocr_page_numbers or []}")
    print(f"Empty pages: {empty_pages or []}")
    print()

    for page in pages:
        print(f"Page {page.page_number}")
        print(f"  extracted_via: {page.extracted_via.value}")
        print(f"  text_chars: {len(page.text)}")
        print(f"  word_count: {len(page.text.split())}")
        print(f"  tables: {len(page.tables)}")

        if args.show_text:
            print("  text sample:")
            print(_indent(_preview(page.text, args.sample_chars), "    "))

        if args.show_tables and page.tables:
            print("  table previews:")
            for index, table in enumerate(page.tables, start=1):
                print(
                    f"    table {index} "
                    f"{table.rows}x{table.cols} caption={table.caption!r}"
                )
                print(_indent(_preview(table.markdown, args.sample_chars), "      "))
        print()


def _selected_pages(raw_pages: str) -> set[int] | None:
    if not raw_pages.strip():
        return None

    pages: set[int] = set()
    for part in raw_pages.split(","):
        value = part.strip()
        if not value:
            continue
        pages.add(int(value))
    return pages


def _preview(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text or "(empty)"
    return text[:max_chars].rstrip() + "\n..."


def _indent(text: str, prefix: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())
