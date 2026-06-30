from __future__ import annotations

from typing import Any

from app.retrieval.context_builder import ContextBlock
from app.schemas.query import Citation, CitationSource


def _pdf_link(payload: dict[str, Any]) -> str | None:
    pdf_id = payload.get("pdf_id") or payload.get("document_id")
    if not pdf_id:
        return None
    page = payload.get("page_number")
    anchor = f"#page={page}" if page else ""
    return f"/source/{pdf_id}{anchor}"


def _source_from_payload(payload: dict[str, Any]) -> CitationSource:
    if payload.get("source_type") == "article":
        return CitationSource(
            type="article",
            title=payload.get("title"),
            url=payload.get("source_url"),
            section=payload.get("section_heading"),
        )
    return CitationSource(
        type="pdf",
        title=payload.get("title"),
        url=_pdf_link(payload),
        page=payload.get("page_number"),
        section=payload.get("section_heading"),
    )


def _citation_from_block(block: ContextBlock) -> Citation:
    p = block.payload
    also = [_source_from_payload(alt) for alt in block.also_available]
    if p.get("source_type") == "article":
        return Citation(
            n=block.n,
            type="article",
            title=p.get("title"),
            url=p.get("source_url"),
            section=p.get("section_heading"),
            document_id=p.get("document_id"),
            also_available=also,
        )
    return Citation(
        n=block.n,
        type=p.get("source_type") or "pdf",
        title=p.get("title"),
        url=_pdf_link(p),
        page=p.get("page_number"),
        section=p.get("section_heading"),
        document_id=p.get("document_id"),
        also_available=also,
    )


def build_citations(blocks: list[ContextBlock]) -> list[Citation]:
    return [_citation_from_block(block) for block in blocks]
