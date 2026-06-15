"""Local test: extract a PDF and (optionally) chunk it.

Run it:

    python -m app.local_tests.test_pdf_extraction path/to/file.pdf
    # or drop PDFs in ./pdf_examples and just run:
    python -m app.local_tests.test_pdf_extraction

Runs the real extractor (Docling for digital pages, Azure OCR for scanned ones),
then writes a report to ``outputs/pdf_extraction_result.txt`` covering: page
count, how each page's text was recovered, a text preview, tables, and figures
(caption / classification / AI description). It then runs ``chunk_pdf`` so you
can see how extraction feeds chunking end-to-end.

Note: extraction pulls heavy/optional deps (docling, pypdfium2, azure-*). If one
is missing or Azure isn't configured, the report records the error instead of
crashing.
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.local_tests._util import Reporter

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _find_pdf(argv: list[str]) -> Path | None:
    if argv:
        candidate = Path(argv[0])
        return candidate if candidate.is_file() else None
    examples = _REPO_ROOT / "pdf_examples"
    if examples.is_dir():
        pdfs = sorted(examples.glob("*.pdf"))
        if pdfs:
            return pdfs[0]
    return None


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    rep = Reporter("PDF EXTRACTION TEST", "pdf_extraction_result.txt")

    pdf_path = _find_pdf(argv)
    if pdf_path is None:
        rep.line("No PDF found.")
        rep.line()
        rep.line("Provide one of:")
        rep.line("  • a path argument:  python -m app.local_tests.test_pdf_extraction myfile.pdf")
        rep.line("  • or drop a .pdf into the ./pdf_examples folder and re-run.")
        rep.write()
        return

    rep.kv("pdf", pdf_path)
    try:
        from app.ingestion.extractors.pdf_extractor import extract_pdf

        result = extract_pdf(pdf_path.read_bytes(), pdf_path.name)
    except Exception as exc:  # missing dep / Azure not configured / parse error
        rep.line()
        rep.line(f"Extraction failed: {type(exc).__name__}: {exc}")
        rep.line("(This usually means an optional dependency or Azure config is missing.)")
        rep.write()
        return

    rep.kv("page_count", result.page_count)
    rep.kv("tables (total)", len(result.tables))
    rep.kv("images (total)", len(result.images))
    rep.kv("ocr pages", result.ocr_page_numbers)
    rep.line()

    for page in result.pages:
        rep.rule("-", f"page {page.page_number} · via={page.extracted_via.value}")
        rep.preview(page.text, limit=500)
        for t in page.tables:
            rep.line()
            rep.line(f"  [table] {t.rows}x{t.cols} caption={t.caption!r}")
            rep.preview(t.markdown, limit=300)
        for img in page.images:
            rep.line()
            rep.line(
                f"  [figure #{img.index}] class={img.classification!r} "
                f"caption={img.caption!r}"
            )
            if img.description:
                rep.line(f"     description: {img.description[:200]}")
        rep.line()

    # End-to-end: extraction → chunking.
    from app.ingestion.chunker import chunk_pdf

    chunks = chunk_pdf(result)
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    rep.rule("=", "CHUNKING (chunk_pdf)")
    rep.kv("parents", len(parents))
    rep.kv("children", len(children))
    if children:
        sizes = [c.token_count for c in children]
        rep.kv("child tokens", f"min={min(sizes)} max={max(sizes)} avg={sum(sizes)//len(sizes)}")
        rep.line()
        for c in children[:4]:
            rep.line(
                f"[child {c.chunk_index}] {c.token_count} tok "
                f"· section={c.section_heading!r} · page={c.page_number}"
            )
            rep.preview(c.text, limit=240)
            rep.line()

    rep.write()


if __name__ == "__main__":
    main()
