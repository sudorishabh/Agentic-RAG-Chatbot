"""End-to-end PDF extraction test over the ./pdf_examples corpus.

Runs the full extraction flow for every sample PDF:

    extract_pdf(bytes, name)  ->  ExtractionResult
    chunk_pdf(result)         ->  list[Chunk]   (canonical + chunking)

and writes a categorised result folder per PDF, **entirely inside this
directory** (``app/local_tests/pdf_extraction_test/results/<pdf-slug>/``):

    00_summary.txt    headline stats + route breakdown
    00_summary.json   the same stats, machine-readable
    01_pages.md       page-by-page extracted text
    02_tables.md      every table (markdown) with page + caption
    03_images.md      every figure: class, caption, description, saved path
    04_chunks.md      canonical chunking output (parents + children)
    full_text.md      the full concatenated extracted text

A top-level ``results/_index.md`` + ``results/_index.json`` summarise the
whole run across all PDFs.

Usage
-----
    # all PDFs in ./pdf_examples
    python -m app.local_tests.pdf_extraction_test.run

    # only specific files (names within pdf_examples, or full paths)
    python -m app.local_tests.pdf_extraction_test.run managing-water.pdf
    python -m app.local_tests.pdf_extraction_test.run C:\\some\\other.pdf
"""

from __future__ import annotations

import json
import re
import sys
import time
import traceback
from pathlib import Path

# --- make the repo importable and keep Windows stdout from choking on text ---
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
    pass

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
EXAMPLES = _REPO_ROOT / "pdf_examples"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "document"


def _resolve_pdfs(argv: list[str]) -> list[Path]:
    if argv:
        out: list[Path] = []
        for arg in argv:
            p = Path(arg)
            if not p.is_file():
                p = EXAMPLES / arg
            if p.is_file() and p.suffix.lower() == ".pdf":
                out.append(p)
            else:
                print(f"  ! skipping (not a .pdf file): {arg}")
        return out
    if EXAMPLES.is_dir():
        return sorted(EXAMPLES.glob("*.pdf"))
    return []


def _preview(text: str, limit: int) -> str:
    snippet = (text or "").strip()
    if len(snippet) > limit:
        return snippet[:limit] + f"\n\n… [+{len(snippet) - limit} more chars]"
    return snippet


def _route_counts(result) -> dict[str, int]:
    counts: dict[str, int] = {}
    for page in result.pages:
        key = page.extracted_via.value
        counts[key] = counts.get(key, 0) + 1
    return counts


# --------------------------------------------------------------------------- #
# Per-PDF report writers — each writes one categorised file.
# --------------------------------------------------------------------------- #

def _write_summary(out_dir: Path, name: str, result, chunks, elapsed: float) -> dict:
    routes = _route_counts(result)
    digital = routes.get("docling", 0) + routes.get("text", 0)
    scanned = routes.get("ocr", 0)
    empty = routes.get("empty", 0)
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    child_tokens = [c.token_count for c in children]

    stats = {
        "pdf": name,
        "elapsed_seconds": round(elapsed, 2),
        "page_count": result.page_count,
        "table_count": result.table_count,
        "char_count": len(result.text),
        "routes": routes,
        "digital_pages": digital,
        "scanned_ocr_pages": scanned,
        "empty_pages": empty,
        "ocr_page_numbers": result.ocr_page_numbers,
        "chunks_total": len(chunks),
        "parent_chunks": len(parents),
        "child_chunks": len(children),
        "child_token_min": min(child_tokens) if child_tokens else 0,
        "child_token_max": max(child_tokens) if child_tokens else 0,
        "child_token_avg": sum(child_tokens) // len(child_tokens) if child_tokens else 0,
    }
    (out_dir / "00_summary.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        f"PDF EXTRACTION SUMMARY — {name}",
        "=" * 78,
        f"  elapsed            : {stats['elapsed_seconds']}s",
        f"  pages              : {stats['page_count']}",
        f"  tables             : {stats['table_count']}",
        f"  extracted chars    : {stats['char_count']:,}",
        "",
        f"  pages by route     : {routes}",
        f"  digital vs scanned : {digital} digital / {scanned} scanned (OCR) / {empty} empty",
        f"  OCR page numbers   : {stats['ocr_page_numbers'] or '—'}",
        "",
        f"  chunks (total)     : {stats['chunks_total']}",
        f"  parent chunks      : {stats['parent_chunks']}",
        f"  child chunks       : {stats['child_chunks']}",
        f"  child tokens       : min={stats['child_token_min']} "
        f"max={stats['child_token_max']} avg={stats['child_token_avg']}",
        "",
    ]
    (out_dir / "00_summary.txt").write_text("\n".join(lines), encoding="utf-8")
    return stats


def _write_pages(out_dir: Path, name: str, result) -> None:
    lines = [f"# Pages — {name}", ""]
    for page in result.pages:
        lines.append(
            f"## Page {page.page_number} · via `{page.extracted_via.value}` "
            f"· {len(page.tables)} table(s), {len(page.images)} image(s)"
        )
        lines.append("")
        body = page.text.strip()
        lines.append(body if body else "_(no text on this page)_")
        lines.append("")
    (out_dir / "01_pages.md").write_text("\n".join(lines), encoding="utf-8")


def _write_tables(out_dir: Path, name: str, result) -> None:
    lines = [f"# Tables — {name}", "", f"Total tables: **{result.table_count}**", ""]
    if not result.tables:
        lines.append("_(no tables extracted)_")
    for i, t in enumerate(result.tables, start=1):
        lines.append(
            f"## Table {i} · page {t.page_number} · {t.rows}×{t.cols} "
            f"· caption: {t.caption!r}"
        )
        lines.append("")
        lines.append(t.markdown.strip() or "_(empty)_")
        lines.append("")
    (out_dir / "02_tables.md").write_text("\n".join(lines), encoding="utf-8")


def _write_images(out_dir: Path, name: str, result) -> None:
    lines = [f"# Images / Figures — {name}", "", f"Total images: **{result.image_count}**", ""]
    if not result.images:
        lines.append("_(no images extracted)_")
    for img in result.images:
        size = f" · {img.width}×{img.height}" if img.width else ""
        lines.append(f"## Figure {img.index} · page {img.page_number}{size}")
        lines.append("")
        lines.append(f"- **classification**: {img.classification!r}")
        lines.append(f"- **caption**: {img.caption!r}")
        lines.append(f"- **saved path**: {img.path or '(not saved)'}")
        if img.description:
            lines.append(f"- **description**: {img.description}")
        lines.append("")
    (out_dir / "03_images.md").write_text("\n".join(lines), encoding="utf-8")


def _write_chunks(out_dir: Path, name: str, chunks) -> None:
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    lines = [
        f"# Chunking (chunk_pdf) — {name}",
        "",
        f"- parents: **{len(parents)}**",
        f"- children: **{len(children)}**",
        "",
        "---",
        "",
        "## Parent chunks",
        "",
    ]
    for c in parents:
        lines.append(
            f"### Parent · section={c.section_heading!r} · pages={c.page_range} "
            f"· {c.token_count} tok"
        )
        lines.append("")
        lines.append(_preview(c.text, 1200))
        lines.append("")
    lines += ["---", "", "## Child chunks", ""]
    for c in children:
        lines.append(
            f"### Child {c.chunk_index} · section={c.section_heading!r} "
            f"· page={c.page_number} · {c.token_count} tok"
        )
        lines.append("")
        lines.append(_preview(c.text, 800))
        lines.append("")
    (out_dir / "04_chunks.md").write_text("\n".join(lines), encoding="utf-8")


def _write_full_text(out_dir: Path, name: str, result) -> None:
    (out_dir / "full_text.md").write_text(
        f"# Full extracted text — {name}\n\n{result.text}\n", encoding="utf-8"
    )


# --------------------------------------------------------------------------- #
# Per-PDF driver
# --------------------------------------------------------------------------- #

def _process_one(pdf_path: Path) -> dict:
    from app.ingestion.chunker import chunk_pdf
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    out_dir = RESULTS / _slugify(pdf_path.stem)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n• {pdf_path.name}")
    start = time.perf_counter()
    try:
        result = extract_pdf(pdf_path.read_bytes(), pdf_path.name)
        chunks = chunk_pdf(result)
    except Exception as exc:  # one bad PDF must not sink the whole run
        elapsed = time.perf_counter() - start
        (out_dir / "ERROR.txt").write_text(
            f"Extraction/chunking failed for {pdf_path.name}\n\n"
            f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}\n"
            "(Often an optional dependency or Azure config is missing.)\n",
            encoding="utf-8",
        )
        print(f"  ✗ FAILED: {type(exc).__name__}: {exc}")
        return {"pdf": pdf_path.name, "error": f"{type(exc).__name__}: {exc}",
                "elapsed_seconds": round(elapsed, 2)}

    elapsed = time.perf_counter() - start
    stats = _write_summary(out_dir, pdf_path.name, result, chunks, elapsed)
    _write_pages(out_dir, pdf_path.name, result)
    _write_tables(out_dir, pdf_path.name, result)
    _write_images(out_dir, pdf_path.name, result)
    _write_chunks(out_dir, pdf_path.name, chunks)
    _write_full_text(out_dir, pdf_path.name, result)

    print(
        f"  ✓ {stats['page_count']} pages "
        f"({stats['digital_pages']} digital / {stats['scanned_ocr_pages']} OCR), "
        f"{stats['table_count']} tables, {stats['image_count']} images, "
        f"{stats['child_chunks']} child chunks · {stats['elapsed_seconds']}s "
        f"-> {out_dir.relative_to(HERE)}"
    )
    return stats


def _write_index(all_stats: list[dict]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "_index.json").write_text(
        json.dumps(all_stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    ok = [s for s in all_stats if "error" not in s]
    failed = [s for s in all_stats if "error" in s]

    lines = [
        "# PDF extraction test — run index",
        "",
        f"- PDFs processed: **{len(all_stats)}** "
        f"({len(ok)} ok, {len(failed)} failed)",
        f"- total pages: **{sum(s.get('page_count', 0) for s in ok)}**",
        f"- total tables: **{sum(s.get('table_count', 0) for s in ok)}**",
        f"- total images: **{sum(s.get('image_count', 0) for s in ok)}**",
        f"- total child chunks: **{sum(s.get('child_chunks', 0) for s in ok)}**",
        "",
        "| PDF | pages | digital/OCR | tables | images | chunks | sec | result |",
        "| --- | ----: | ----------- | -----: | -----: | -----: | --: | ------ |",
    ]
    for s in all_stats:
        slug = _slugify(Path(s["pdf"]).stem)
        if "error" in s:
            lines.append(
                f"| {s['pdf']} | — | — | — | — | — | {s.get('elapsed_seconds', '?')} "
                f"| ⚠ {s['error']} |"
            )
            continue
        lines.append(
            f"| {s['pdf']} | {s['page_count']} "
            f"| {s['digital_pages']}/{s['scanned_ocr_pages']} "
            f"| {s['table_count']} | {s['image_count']} | {s['child_chunks']} "
            f"| {s['elapsed_seconds']} | [{slug}/](./{slug}/) |"
        )
    (RESULTS / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    pdfs = _resolve_pdfs(argv)
    if not pdfs:
        print("No PDFs to process.")
        print(f"  Drop .pdf files into {EXAMPLES} or pass file paths as arguments.")
        return 1

    print(f"Running PDF extraction flow over {len(pdfs)} PDF(s)")
    print(f"  source : {EXAMPLES}")
    print(f"  results: {RESULTS}")

    run_start = time.perf_counter()
    all_stats = [_process_one(pdf) for pdf in pdfs]
    _write_index(all_stats)

    ok = sum(1 for s in all_stats if "error" not in s)
    print(
        f"\nDone in {time.perf_counter() - run_start:.1f}s — "
        f"{ok}/{len(all_stats)} ok. See {RESULTS / '_index.md'}"
    )
    return 0 if ok == len(all_stats) else 2


if __name__ == "__main__":
    raise SystemExit(main())
