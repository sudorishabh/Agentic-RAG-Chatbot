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


def _source_type(payload: dict[str, Any]) -> str:
    """The citation's type name: ingestion's own ``source_type`` vocabulary.

    Ingestion writes exactly two values — ``website`` and ``pdf_attachment`` —
    so those are the names a citation carries; the pre-rename ``article`` alias
    folds into ``website``. There is deliberately no second vocabulary to
    translate into, which is how the same PDF used to come back as
    ``pdf_attachment`` in one slot and ``pdf`` in another.
    """
    source_type = payload.get("source_type")
    if source_type in _WEBSITE_TYPES:
        return "website"
    return source_type or "pdf_attachment"


def _source_from_payload(payload: dict[str, Any]) -> CitationSource:
    """The single description of one source.

    Both the primary citation and the ``also_available`` alternates are built
    from this, so a payload cannot describe itself two ways depending on which
    slot it lands in. Website payloads simply carry no page fields, so the one
    shape covers both kinds without a branch.
    """
    start, end = page_span(payload)
    return CitationSource(
        type=_source_type(payload),
        title=payload.get("title"),
        url=_primary_url(payload),
        page=start,
        page_end=end,
        section=payload.get("section_heading"),
    )


def _citation_from_block(block: ContextBlock) -> Citation:
    """A numbered citation, described by exactly the same rules as the
    alternates listed beneath it — the block only adds its number and the
    document the answer should resolve to."""
    source = _source_from_payload(block.payload)
    return Citation(
        n=block.n,
        type=source.type,
        title=source.title,
        url=source.url,
        page=source.page,
        page_end=source.page_end,
        section=source.section,
        document_id=block.payload.get("document_id"),
        also_available=[_source_from_payload(alt) for alt in block.also_available],
    )


def build_citations(blocks: list[ContextBlock]) -> list[Citation]:
    return [_citation_from_block(block) for block in blocks]
