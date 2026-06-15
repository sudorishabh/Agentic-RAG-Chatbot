"""Local test: chunk a canonical document into parent/child chunks.

Run it:

    python -m app.local_tests.test_chunking
    # or: python app/local_tests/test_chunking.py

Chunks two things and reports both to ``outputs/chunking_result.txt``:

1. ``samples/sample_document.md`` — a structured, multi-section handbook fed in
   as a synthetic 1-page "PDF", to show heading-aware parent/child splitting,
   token sizing, overlap, and the section table kept atomic.
2. The first record of ``samples/sample_article.json`` — to show the Drupal
   (article) path.

For each, it prints parent/child counts, per-child token stats, the section
heading + parent link each child carries, a text preview, and one full Qdrant
payload so you can see exactly what would be upserted.
"""

from __future__ import annotations

import json

from app.local_tests._util import SAMPLES, Reporter


def _dump_chunks(rep: Reporter, chunks, *, show: int = 6) -> None:
    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    rep.kv("parents", len(parents))
    rep.kv("children", len(children))
    if children:
        sizes = [c.token_count for c in children]
        rep.kv("child tokens", f"min={min(sizes)} max={max(sizes)} avg={sum(sizes)//len(sizes)}")
    rep.line()

    for c in children[:show]:
        rep.line(
            f"[child {c.chunk_index}] {c.token_count} tok "
            f"· section={c.section_heading!r} "
            f"· page={c.page_number} range={c.page_range}"
        )
        rep.line(f"   parent_chunk_id = {c.parent_chunk_id}")
        rep.preview(c.text, limit=320)
        rep.line()

    if children:
        rep.line("full Qdrant payload (first child):")
        rep.line(json.dumps(children[0].to_payload(), indent=2, ensure_ascii=False))
    if parents:
        rep.line()
        rep.line("full Qdrant payload (first parent):")
        rep.line(json.dumps(parents[0].to_payload(), indent=2, ensure_ascii=False))


def main() -> None:
    from app.core.models import CanonicalDocument, CanonicalSection
    from app.ingestion.canonical import from_drupal_export
    from app.ingestion.chunker import chunk_canonical

    rep = Reporter("CHUNKING TEST", "chunking_result.txt")

    # 1) Structured markdown handbook as a single-page PDF-like document.
    md = (SAMPLES / "sample_document.md").read_text(encoding="utf-8")
    pdf_doc = CanonicalDocument(
        document_id="sample_handbook",
        source_type="pdf",
        title="Decentralised Renewable Energy: A Field Handbook",
        sections=[CanonicalSection(text=md, page_start=1, page_end=1, order=0)],
        pdf_id="sample_handbook",
        pdf_path="samples/sample_document.md",
    )
    rep.rule("=", "DOCUMENT 1 — structured PDF-style (sample_document.md)")
    _dump_chunks(rep, chunk_canonical(pdf_doc))
    rep.line()

    # 2) Drupal article path.
    items = json.loads((SAMPLES / "sample_article.json").read_text(encoding="utf-8"))
    article_doc = from_drupal_export(items[0])
    rep.rule("=", "DOCUMENT 2 — Drupal article (sample_article.json[0])")
    _dump_chunks(rep, chunk_canonical(article_doc))

    rep.write()


if __name__ == "__main__":
    main()
