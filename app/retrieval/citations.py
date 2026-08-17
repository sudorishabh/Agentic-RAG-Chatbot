from __future__ import annotations

from typing import Any

from app.core.models.context import page_span
from app.retrieval.context_builder import ContextBlock
from app.schemas.query import Citation, CitationSource


def _with_page(url: str | None, payload: dict[str, Any]) -> str | None:
    """Anchor the link at the first page of the evidence, so opening it lands
    where the quoted passage begins rather than somewhere inside it."""
    page = page_span(payload)[0]
    return f"{url}#page={page}" if (url and page) else url


# Canonical source_type for Drupal content is "website"; "article" still appears
# on points indexed before the rename (until the migration script runs).
_WEBSITE_TYPES = ("website", "article")


def _primary_url(payload: dict[str, Any]) -> str | None:
    """The best openable link for a source. A website node links to its own page
    (a node may carry a file_url for an attached PDF, but that attachment is its
    own citation in the PDFs group — the page must not resolve to it, or it reads
    as a PDF under Web pages). A PDF links to the attachment it was downloaded
    from; every ingested PDF carries that URL, so None means there is genuinely
    nothing to open."""
    if payload.get("source_type") in _WEBSITE_TYPES:
        return payload.get("source_url") or _with_page(payload.get("file_url"), payload)
    return _with_page(payload.get("file_url"), payload)


def _source_from_payload(payload: dict[str, Any]) -> CitationSource:
    if payload.get("source_type") in _WEBSITE_TYPES:
        return CitationSource(
            type="website",
            title=payload.get("title"),
            url=_primary_url(payload),
            section=payload.get("section_heading"),
        )
    start, end = page_span(payload)
    return CitationSource(
        type="pdf",
        title=payload.get("title"),
        url=_primary_url(payload),
        page=start,
        page_end=end,
        section=payload.get("section_heading"),
    )


def _citation_from_block(block: ContextBlock) -> Citation:
    p = block.payload
    also = [_source_from_payload(alt) for alt in block.also_available]
    if p.get("source_type") in _WEBSITE_TYPES:
        return Citation(
            n=block.n,
            type="website",
            title=p.get("title"),
            url=_primary_url(p),
            section=p.get("section_heading"),
            document_id=p.get("document_id"),
            also_available=also,
        )
    start, end = page_span(p)
    return Citation(
        n=block.n,
        type=p.get("source_type") or "pdf",
        title=p.get("title"),
        url=_primary_url(p),
        page=start,
        page_end=end,
        section=p.get("section_heading"),
        document_id=p.get("document_id"),
        also_available=also,
    )


def build_citations(blocks: list[ContextBlock]) -> list[Citation]:
    return [_citation_from_block(block) for block in blocks]
