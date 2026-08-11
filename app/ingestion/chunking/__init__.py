"""Structure-aware parent/child chunking.

Turns canonical/PDF text into parent/child chunks: :mod:`.segmenter` parses
markdown-ish structure into typed blocks and sections, :mod:`.packer` sizes and
overlaps them into token-bounded windows, :mod:`.classifier` flags
non-substantive sections (toc/references/glossary), and this module wires the
whole pipeline together plus the canonical-document adapter and CLI.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Sequence

from app.core.models import CanonicalDocument, CanonicalSection
from app.ingestion.chunking.classifier import classify_section
from app.ingestion.chunking.config import ChunkingConfig, config_for
from app.ingestion.chunking.models import Chunk, DocumentMeta
from app.ingestion.chunking.packer import (
    ChildText,
    Encoder,
    coalesce_windows,
    get_encoder,
    pack,
    window_texts,
)
from app.ingestion.chunking.segmenter import (
    Block,
    Section,
    assemble_sections,
    blocks_from_text,
    join_blocks,
    merge_small_sections,
    page_range,
    table_markdown,
)
from app.ingestion.textutil import slugify

logger = logging.getLogger(__name__)

__all__ = [
    "ChunkingConfig",
    "config_for",
    "DocumentMeta",
    "Chunk",
    "chunk_pages",
    "chunk_document",
    "chunk_canonical",
]

_NAMESPACE = uuid.UUID("6f2a1d3e-8b4c-4a9f-9e7d-2c5b1a0f3e64")


def _uuid(meta: DocumentMeta, suffix: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, f"{meta.document_id}|v{meta.doc_version}|{suffix}"))


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_BREADCRUMB_SEP = " › "


def _breadcrumb(
    meta: DocumentMeta, heading: str | None, max_tokens: int, enc: Encoder
) -> str:
    """The "title › heading" trail prefixed to a child's *embedded* text.

    Headings are lifted out of the block stream into ``Section.heading`` and only
    ever rejoined onto parent text — and parents are stored as zero vectors, so
    without this a heading reaches no vector at all and contributes nothing to
    retrieval. Returns "" when there is neither a title nor a heading to state.
    """
    parts = [p.strip() for p in (meta.title, heading) if p and p.strip()]
    if not parts:
        return ""
    return enc.head(_BREADCRUMB_SEP.join(parts), max_tokens)


def _parent_text(heading: str | None, blocks: Sequence[Block], part: int) -> str:
    body = join_blocks(blocks)
    if not heading:
        return body
    prefix = heading if part == 0 else f"{heading} (cont.)"
    return f"{prefix}\n\n{body}" if body else prefix


def _build_chunks(
    sections: Sequence[Section], meta: DocumentMeta, config: ChunkingConfig, enc: Encoder
) -> list[Chunk]:
    chunks: list[Chunk] = []
    child_index = 0

    for section_idx, section in enumerate(sections):
        heading = section.heading
        body = section.blocks
        crumb = _breadcrumb(meta, heading, config.breadcrumb_max_tokens, enc)
        heading_tokens = enc.count(heading) if heading else 0
        body_tokens = sum(enc.count(b.text) for b in body)

        if body_tokens + heading_tokens <= config.parent_max_tokens:
            parent_windows = [list(body)]
        else:
            parent_windows = pack(
                body, target=config.parent_target_tokens,
                max_tokens=config.parent_max_tokens,
                min_fill=config.child_min_tokens, enc=enc,
            )
            parent_windows = coalesce_windows(
                parent_windows, config.child_min_tokens, config.parent_max_tokens, enc
            )

        for part, parent_blocks in enumerate(parent_windows):
            parent_id = _uuid(meta, f"parent|{section_idx}.{part}")
            ptext = _parent_text(heading, parent_blocks, part)
            if not ptext.strip():
                continue

            child_windows = pack(
                parent_blocks, target=config.child_target_tokens,
                max_tokens=config.child_max_tokens,
                min_fill=config.child_min_tokens, enc=enc,
            )
            child_windows = coalesce_windows(
                child_windows, config.child_min_tokens, config.child_max_tokens, enc
            )
            children = window_texts(
                child_windows, overlap=config.child_overlap_tokens,
                max_tokens=config.child_max_tokens, enc=enc,
            )
            if not children:
                # Nothing packed, so this section is a heading with no body to
                # window. Emit the heading as its own child: an empty result is
                # the last point at which extracted text can silently vanish.
                children = [ChildText([], ptext)]

            # A parent with a single child is a near-duplicate of it: skip the
            # parent and let the child stand alone (context falls back to child
            # text when there is no parent).
            emit_parent = len(children) > 1
            if emit_parent:
                parent_tables = table_markdown(parent_blocks)
                chunks.append(
                    Chunk(
                        chunk_id=parent_id, text=ptext, is_parent=True, meta=meta,
                        section_heading=heading, section_type=classify_section(ptext),
                        page_range=page_range(parent_blocks),
                        token_count=enc.count(ptext), content_hash=_hash(ptext),
                        has_table=bool(parent_tables), table_markdown=parent_tables,
                    )
                )

            for child in children:
                ctext = child.text
                pages = page_range(child.blocks)
                child_tables = table_markdown(child.blocks)
                tokens = enc.count(ctext)
                if tokens > config.child_max_tokens:  # pragma: no cover
                    # window_texts caps every text it returns, so this is a
                    # tripwire for a future regression in packing, not a
                    # reachable branch. Content is kept either way.
                    logger.warning(
                        "Child %d of %s is %d tokens, over the %d-token limit.",
                        child_index, meta.document_id, tokens, config.child_max_tokens,
                    )
                chunks.append(
                    Chunk(
                        chunk_id=_uuid(meta, f"child|{child_index}"),
                        text=ctext, is_parent=False, meta=meta,
                        embed_text=f"{crumb}\n\n{ctext}" if crumb else ctext,
                        section_heading=heading, section_type=classify_section(ctext),
                        parent_chunk_id=parent_id if emit_parent else None,
                        chunk_index=child_index,
                        page_number=pages[0] if pages else None,
                        page_range=pages,
                        overlap_page_range=child.overlap_pages,
                        token_count=tokens,
                        content_hash=_hash(ctext),
                        has_table=bool(child_tables), table_markdown=child_tables,
                    )
                )
                child_index += 1

    return chunks


def chunk_pages(
    pages: Sequence[tuple[int | None, str]],
    meta: DocumentMeta,
    *,
    config: ChunkingConfig | None = None,
) -> list[Chunk]:
    config = config or config_for(meta.source_type)
    enc = get_encoder(config.encoding_name)

    blocks: list[Block] = []
    for page_number, text in pages:
        blocks.extend(blocks_from_text(text, page_number))

    sections = assemble_sections(blocks)
    sections = merge_small_sections(sections, config.child_min_tokens, enc)
    return _build_chunks(sections, meta, config, enc)


def chunk_document(
    text: str, meta: DocumentMeta, *, config: ChunkingConfig | None = None
) -> list[Chunk]:
    return chunk_pages([(None, text)], meta, config=config)


def _meta_from_canonical(doc: CanonicalDocument) -> DocumentMeta:
    from app.ingestion.canonical import CATEGORY_VOCABULARIES

    term_ids = [r.uuid for r in doc.entity_refs if r.vocabulary]
    theme_ids = [
        r.uuid for r in doc.entity_refs if r.vocabulary in CATEGORY_VOCABULARIES
    ]
    return DocumentMeta(
        document_id=doc.document_id,
        source_type=doc.source_type,
        title=doc.title,
        source_url=doc.source_url,
        file_url=doc.file_url,
        pdf_id=doc.pdf_id,
        pdf_path=doc.pdf_path,
        article_uuid=doc.article_uuid,
        linked_pdf_id=doc.linked_pdf_id,
        linked_article_uuid=doc.linked_article_uuid,
        tags=list(doc.tags),
        categories=list(doc.categories),
        authors=list(doc.authors),
        term_ids=list(dict.fromkeys(term_ids)),
        theme_ids=list(dict.fromkeys(theme_ids)),
        language=doc.language,
        tenant_id=doc.tenant_id,
        acl=list(doc.acl),
        doc_version=doc.doc_version,
        is_current=doc.is_current,
        published_at=doc.published_at,
        extra=dict(doc.extra),
    )


def _canonical_page_text(section: CanonicalSection) -> str:
    if section.heading and section.text:
        return f"{section.heading}\n\n{section.text}"
    return section.heading or section.text


def chunk_canonical(
    doc: CanonicalDocument,
    *,
    config: ChunkingConfig | None = None,
    small_doc_pages: int = 10,
) -> list[Chunk]:
    meta = _meta_from_canonical(doc)
    paginated = doc.is_paginated

    if config is None:
        if paginated:
            n_pages = sum(1 for s in doc.sections if s.page_start is not None)
            config = config_for("small_pdf" if n_pages <= small_doc_pages else doc.source_type)
        else:
            config = config_for(doc.extra.get("bundle") or doc.source_type)

    if paginated:
        pages = [
            (s.page_start, _canonical_page_text(s))
            for s in doc.sections
            if _canonical_page_text(s).strip()
        ]
        return chunk_pages(pages, meta, config=config)
    return chunk_document(doc.full_text(), meta, config=config)


def _main(argv: list[str] | None = None) -> int:
    import argparse
    import sys
    from pathlib import Path

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Inspect chunking of a file.")
    parser.add_argument("path", help="A .txt/.md file, or a .pdf to extract+chunk.")
    parser.add_argument("-n", "--show", type=int, default=3, help="Children to print (default: 3).")
    parser.add_argument("--full", action="store_true", help="Print full chunk text.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    path = Path(args.path)
    if path.suffix.lower() == ".pdf":
        from app.ingestion.canonical import from_pdf
        from app.ingestion.extractors.pdf_extractor import extract_pdf

        doc = from_pdf(extract_pdf(path.read_bytes(), path.name))
        chunks = chunk_canonical(doc)
    else:
        meta = DocumentMeta(
            document_id=slugify(path.stem), source_type="pdf_attachment", title=path.name
        )
        chunks = chunk_document(path.read_text(encoding="utf-8", errors="ignore"), meta)

    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    print(f"{path.name}: {len(parents)} parents, {len(children)} children")
    if children:
        sizes = [c.token_count for c in children]
        print(f"  child tokens: min={min(sizes)} max={max(sizes)} avg={sum(sizes) // len(sizes)}")
    for child in children[: args.show]:
        print(f"\n[child {child.chunk_index}] {child.token_count} tok "
              f"· section={child.section_heading!r} · parent={child.parent_chunk_id}")
        text = child.text if args.full else child.text[:280] + ("…" if len(child.text) > 280 else "")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
