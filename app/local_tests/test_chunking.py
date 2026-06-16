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

    items = json.loads((SAMPLES / "sample_article.json").read_text(encoding="utf-8"))
    article_doc = from_drupal_export(items[0])
    rep.rule("=", "DOCUMENT 2 — Drupal article (sample_article.json[0])")
    _dump_chunks(rep, chunk_canonical(article_doc))

    rep.write()


if __name__ == "__main__":
    main()
