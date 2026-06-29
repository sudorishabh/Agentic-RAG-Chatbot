"""End-to-end PDF extraction test over the ./pdf_examples corpus.

Runs the full extraction flow for every sample PDF:

    extract_pdf(bytes, name)  ->  ExtractionResult
    chunk_pdf(result)         ->  list[Chunk]            (canonical + chunking)
    -> id + vector + payload points                      (exactly what Qdrant gets)

and writes a categorised result folder per PDF, **entirely inside this
directory** (``app/local_tests/pdf_extraction_test/results/<pdf-slug>/``):

    00_summary.txt         headline stats + route breakdown
    00_summary.json        the same stats, machine-readable
    01_pages.md            page-by-page extracted text
    02_tables.md           every table (markdown) with page + caption
    03_chunks.md           canonical chunking output (parents + children)
    04_metadata.md         native PDF metadata (title/author/dates) + route info
    04_metadata.json       the same metadata, machine-readable
    05_qdrant_points.json  the exact id+vector+payload points upserted to Qdrant
    05_qdrant_points.md    readable preview of those points (vectors truncated)
    full_text.md           the full concatenated extracted text

A top-level ``results/_index.md`` + ``results/_index.json`` summarise the
whole run across all PDFs.

Usage
-----
    # all PDFs in ./pdf_examples
    python -m app.local_tests.pdf_extraction_test.run

    # only specific files (names within pdf_examples, or full paths)
    python -m app.local_tests.pdf_extraction_test.run managing-water.pdf
    python -m app.local_tests.pdf_extraction_test.run C:\\some\\other.pdf

    # skip embedding (05_qdrant_points.json keeps payloads, vectors left null)
    python -m app.local_tests.pdf_extraction_test.run managing-water.pdf --no-embed

``05_qdrant_points.json`` mirrors ``index_chunks``: each child carries its real
embedding vector, each parent a zero vector, and the payload is exactly
``Chunk.to_payload()`` plus created_at / updated_at. Embedding is best-effort —
without the Azure OpenAI embedding config the vectors are left ``null`` so the
payloads are still inspectable.
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


def _parse_pdf_date(value: str | None) -> str | None:
    """Turn a PDF date string (``D:20210204153000+05'30'``) into readable text."""
    if not value:
        return None
    s = value.strip()
    if s.startswith("D:"):
        s = s[2:]
    m = re.match(r"(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?", s)
    if not m:
        return value
    y, mo, d, hh, mm, ss = (g or "" for g in m.groups())
    out = f"{y}-{mo or '01'}-{d or '01'}"
    if hh:
        out += f" {hh}:{mm or '00'}:{ss or '00'}"
    tz = s[m.end():].replace("'", "").strip()
    if tz == "Z":
        out += " UTC"
    elif tz:
        out += f" {tz}"
    return out


def _pdf_document_metadata(content: bytes) -> dict:
    """Read the PDF's own document info directly with PyMuPDF.

    This is independent of the extraction route: it reads the native PDF info
    dictionary (title/author/dates/producer …) plus a couple of structural
    facts (encryption, page count). Best-effort — never raises.
    """
    try:
        import fitz  # PyMuPDF
    except Exception as exc:  # pragma: no cover - optional dependency
        return {"_error": f"PyMuPDF not available: {exc}"}

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        return {"_error": f"could not open PDF: {type(exc).__name__}: {exc}"}

    try:
        raw = dict(doc.metadata or {})
        return {
            "title": raw.get("title") or None,
            "author": raw.get("author") or None,
            "subject": raw.get("subject") or None,
            "keywords": raw.get("keywords") or None,
            "creator": raw.get("creator") or None,
            "producer": raw.get("producer") or None,
            "creation_date": _parse_pdf_date(raw.get("creationDate")),
            "modification_date": _parse_pdf_date(raw.get("modDate")),
            "creation_date_raw": raw.get("creationDate") or None,
            "modification_date_raw": raw.get("modDate") or None,
            "format": raw.get("format") or None,
            "trapped": raw.get("trapped") or None,
            "encrypted": bool(getattr(doc, "is_encrypted", False)),
            "page_count": doc.page_count,
        }
    finally:
        doc.close()


# --------------------------------------------------------------------------- #
# Per-PDF report writers — each writes one categorised file.
# --------------------------------------------------------------------------- #

def _write_summary(out_dir: Path, name: str, result, chunks, elapsed: float) -> dict:
    routes = _route_counts(result)  # by extracted_via: text / ocr / empty
    digital = routes.get("text", 0)
    scanned = routes.get("ocr", 0)
    empty = routes.get("empty", 0)
    # Per-page extractor routing (hybrid mode): azure / camelot / local.
    signals = result.metadata.get("page_signals") or {}
    page_routes = {
        "azure": len(signals.get("azure", [])),
        "camelot": len(signals.get("camelot", [])),
        "local": len(signals.get("local", [])),
    }
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    child_tokens = [c.token_count for c in children]

    stats = {
        "pdf": name,
        "elapsed_seconds": round(elapsed, 2),
        "page_count": result.page_count,
        "table_count": result.table_count,
        "char_count": len(result.text),
        "route": result.metadata.get("route"),
        "routes": routes,
        "page_routes": page_routes,
        "camelot_pages": page_routes["camelot"],
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
        f"  extraction route   : {stats['route'] or '—'}",
        f"  pages by extractor : azure={page_routes['azure']} "
        f"camelot={page_routes['camelot']} local={page_routes['local']}",
        f"  pages by source    : {routes}",
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
            f"· {len(page.tables)} table(s)"
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
    (out_dir / "03_chunks.md").write_text("\n".join(lines), encoding="utf-8")


def _write_metadata(out_dir: Path, name: str, doc_meta: dict, result) -> dict:
    extraction_meta = dict(result.metadata) if result is not None else {}
    payload = {"pdf": name, "document": doc_meta, "extraction": extraction_meta}
    (out_dir / "04_metadata.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    def _cell(v) -> str:
        if v is None or v == "" or v == [] or v == {}:
            return "—"
        return str(v).replace("|", r"\|").replace("\n", " ")

    lines = [f"# Metadata — {name}", "", "## Document metadata (native PDF)", ""]
    if not doc_meta or doc_meta.get("_error"):
        reason = doc_meta.get("_error", "no metadata available") if doc_meta else \
            "no metadata available"
        lines += [f"_Could not read native PDF metadata: {reason}_", ""]
    else:
        lines += ["| field | value |", "| --- | --- |"]
        for key in (
            "title", "author", "subject", "keywords", "creator", "producer",
            "creation_date", "modification_date", "format", "trapped",
            "encrypted", "page_count",
        ):
            lines.append(f"| {key} | {_cell(doc_meta.get(key))} |")
        lines.append("")

    lines += ["## Extraction metadata (pipeline)", ""]
    if extraction_meta:
        lines += ["| key | value |", "| --- | --- |"]
        for key in sorted(extraction_meta):
            lines.append(f"| {key} | {_cell(extraction_meta[key])} |")
    else:
        lines.append("_(extraction did not complete)_")
    lines.append("")

    (out_dir / "04_metadata.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def _build_qdrant_points(chunks, *, embed: bool) -> tuple[list[dict], dict]:
    """Assemble the points ``index_chunks`` would upsert, as plain dicts.

    Mirrors ``app.ingestion.indexer._build_points``: each child carries its
    embedding vector, each parent a zero vector, and every payload is
    ``Chunk.to_payload()`` stamped with created_at / updated_at. Embedding is
    best-effort — if the Azure OpenAI embedding config is missing the vectors
    are left ``None`` so the payloads are still inspectable.
    """
    from datetime import datetime, timezone

    children = [c for c in chunks if not c.is_parent]
    info: dict = {
        "embedded": False,
        "vector_dim": 0,
        "embedding_model": None,
        "embed_error": None,
    }
    vec_by_id: dict[str, list[float]] = {}
    dim = 0
    if embed and children:
        try:
            # Reuse the production embedding path so batching matches the real run.
            from app.config import get_settings
            from app.ingestion.indexer import _embed_children

            vectors = _embed_children([c.text for c in children], 128)
            vec_by_id = {c.chunk_id: v for c, v in zip(children, vectors)}
            dim = len(vectors[0]) if vectors else 0
            info.update(
                embedded=True,
                vector_dim=dim,
                embedding_model=get_settings().azure_openai_embedding_model,
            )
        except Exception as exc:  # no Azure embedding config / network — payloads only
            info["embed_error"] = f"{type(exc).__name__}: {exc}"

    timestamp = datetime.now(timezone.utc).isoformat()
    zero = [0.0] * dim
    points: list[dict] = []
    for c in chunks:
        payload = c.to_payload()
        payload.setdefault("created_at", timestamp)
        payload["updated_at"] = timestamp
        if c.is_parent:
            vector = zero if dim else None
        else:
            vector = vec_by_id.get(c.chunk_id)
        points.append({"id": c.chunk_id, "vector": vector, "payload": payload})
    return points, info


def _write_qdrant_points(out_dir: Path, name: str, chunks, *, embed: bool) -> dict:
    points, info = _build_qdrant_points(chunks, embed=embed)

    (out_dir / "05_qdrant_points.json").write_text(
        json.dumps(
            {"pdf": name, "point_count": len(points), **info, "points": points},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def _vec_preview(v) -> str:
        if v is None:
            return "_(not embedded)_"
        head = ", ".join(f"{x:.4f}" for x in v[:8])
        return f"dim={len(v)} · [{head}, …]"

    lines = [
        f"# Qdrant points — {name}",
        "",
        f"- points (rows upserted): **{len(points)}**",
        f"- embedded: **{info['embedded']}**"
        + (
            f" · model `{info['embedding_model']}` · dim {info['vector_dim']}"
            if info["embedded"]
            else ""
        ),
    ]
    if info["embed_error"]:
        lines.append(f"- embedding skipped: _{info['embed_error']}_")
    lines += [
        "",
        "Each point is `{id, vector, payload}` exactly as `index_chunks` upserts "
        "it. Children carry their embedding; parents carry a zero vector and are "
        "reached through their children. Below, vectors are truncated and "
        "`chunk_text` is clipped — see `05_qdrant_points.json` for the full data.",
        "",
        "---",
        "",
    ]
    for p in points:
        pl = dict(p["payload"])
        is_parent = pl.get("is_parent", False)
        pl["chunk_text"] = _preview(pl.get("chunk_text", ""), 600)
        lines.append(f"## {'Parent' if is_parent else 'Child'} · `{p['id']}`")
        lines.append("")
        lines.append(f"- vector: {_vec_preview(p['vector'])}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(pl, indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")
    (out_dir / "05_qdrant_points.md").write_text("\n".join(lines), encoding="utf-8")
    return info


def _write_full_text(out_dir: Path, name: str, result) -> None:
    (out_dir / "full_text.md").write_text(
        f"# Full extracted text — {name}\n\n{result.text}\n", encoding="utf-8"
    )


# --------------------------------------------------------------------------- #
# Per-PDF driver
# --------------------------------------------------------------------------- #

def _process_one(pdf_path: Path, *, embed: bool = True) -> dict:
    from app.ingestion.chunker import chunk_pdf
    from app.ingestion.extractors.pdf_extractor import extract_pdf

    out_dir = RESULTS / _slugify(pdf_path.stem)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n• {pdf_path.name}")
    start = time.perf_counter()
    doc_meta: dict = {}
    try:
        content = pdf_path.read_bytes()
        doc_meta = _pdf_document_metadata(content)
        result = extract_pdf(content, pdf_path.name)
        chunks = chunk_pdf(result)
    except Exception as exc:  # one bad PDF must not sink the whole run
        elapsed = time.perf_counter() - start
        (out_dir / "ERROR.txt").write_text(
            f"Extraction/chunking failed for {pdf_path.name}\n\n"
            f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}\n"
            "(Often an optional dependency or Azure config is missing.)\n",
            encoding="utf-8",
        )
        _write_metadata(out_dir, pdf_path.name, doc_meta, None)
        print(f"  ✗ FAILED: {type(exc).__name__}: {exc}")
        return {"pdf": pdf_path.name, "error": f"{type(exc).__name__}: {exc}",
                "elapsed_seconds": round(elapsed, 2)}

    elapsed = time.perf_counter() - start
    stats = _write_summary(out_dir, pdf_path.name, result, chunks, elapsed)
    _write_pages(out_dir, pdf_path.name, result)
    _write_tables(out_dir, pdf_path.name, result)
    _write_chunks(out_dir, pdf_path.name, chunks)
    _write_metadata(out_dir, pdf_path.name, doc_meta, result)
    point_info = _write_qdrant_points(out_dir, pdf_path.name, chunks, embed=embed)
    _write_full_text(out_dir, pdf_path.name, result)

    vec_note = (
        f", embedded dim {point_info['vector_dim']}"
        if point_info["embedded"]
        else " (vectors skipped)"
    )
    print(
        f"  ✓ {stats['page_count']} pages "
        f"({stats['digital_pages']} digital, {stats['camelot_pages']} via camelot / "
        f"{stats['scanned_ocr_pages']} OCR), "
        f"{stats['table_count']} tables, "
        f"{stats['child_chunks']} child chunks{vec_note} · {stats['elapsed_seconds']}s "
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
        f"- total child chunks: **{sum(s.get('child_chunks', 0) for s in ok)}**",
        "",
        "| PDF | pages | digital/OCR | camelot | tables | chunks | sec | result |",
        "| --- | ----: | ----------- | ------: | -----: | -----: | --: | ------ |",
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
            f"| {s.get('camelot_pages', 0)} "
            f"| {s['table_count']} | {s['child_chunks']} "
            f"| {s['elapsed_seconds']} | [{slug}/](./{slug}/) |"
        )
    (RESULTS / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    embed = "--no-embed" not in argv
    pdfs = _resolve_pdfs([a for a in argv if not a.startswith("--")])
    if not pdfs:
        print("No PDFs to process.")
        print(f"  Drop .pdf files into {EXAMPLES} or pass file paths as arguments.")
        return 1

    print(f"Running PDF extraction flow over {len(pdfs)} PDF(s)")
    print(f"  source : {EXAMPLES}")
    print(f"  results: {RESULTS}")
    print(f"  embed  : {'on' if embed else 'off (--no-embed)'}")

    run_start = time.perf_counter()
    all_stats = [_process_one(pdf, embed=embed) for pdf in pdfs]
    _write_index(all_stats)

    ok = sum(1 for s in all_stats if "error" not in s)
    print(
        f"\nDone in {time.perf_counter() - run_start:.1f}s — "
        f"{ok}/{len(all_stats)} ok. See {RESULTS / '_index.md'}"
    )
    return 0 if ok == len(all_stats) else 2


if __name__ == "__main__":
    raise SystemExit(main())
