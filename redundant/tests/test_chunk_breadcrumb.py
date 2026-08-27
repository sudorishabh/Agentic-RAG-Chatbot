"""The document/section breadcrumb reaches the embedder without disturbing the
stored chunk text (what citations quote and content_hash covers)."""

from __future__ import annotations

from app.ingestion.chunking import DocumentMeta, chunk_pages
from app.ingestion.chunking.config import ChunkingConfig

META = DocumentMeta(document_id="d", source_type="pdf", title="Maritime Outlook")

BODY = "Alternative fuels need port infrastructure to scale. " * 8


def _children(chunks):
    return [c for c in chunks if not c.is_parent]


def test_breadcrumb_prefixes_embed_text_only():
    children = _children(chunk_pages([(1, f"4 Transition Pathway\n\n{BODY}")], META))
    assert children
    child = children[0]
    assert child.embed_text == f"Maritime Outlook › 4 Transition Pathway\n\n{child.text}"
    # The stored text is untouched: citations quote it and content_hash covers it.
    assert not child.text.startswith("Maritime Outlook")


def test_breadcrumb_falls_back_to_the_title_when_there_is_no_heading():
    children = _children(chunk_pages([(1, "Plain prose carrying no heading. " * 8)], META))
    assert children
    assert children[0].embed_text == f"Maritime Outlook\n\n{children[0].text}"


def test_breadcrumb_omitted_when_there_is_nothing_to_state():
    meta = DocumentMeta(document_id="d", source_type="pdf", title=None)
    children = _children(chunk_pages([(1, "Prose with no title and no heading. " * 8)], meta))
    assert children
    assert children[0].embed_text == children[0].text


def test_breadcrumb_is_truncated_to_the_token_cap():
    meta = DocumentMeta(document_id="d", source_type="pdf", title="Very Long Title " * 40)
    children = _children(
        chunk_pages([(1, BODY)], meta, config=ChunkingConfig(breadcrumb_max_tokens=8))
    )
    assert children
    crumb = children[0].embed_text.split("\n\n")[0]
    assert 0 < len(crumb) < len(meta.title)


def test_parents_are_not_given_embed_text():
    body = "Maritime decarbonisation needs alternative fuels and infrastructure. " * 120
    chunks = chunk_pages([(1, f"4 Transition Pathway\n\n{body}")], META)
    parents = [c for c in chunks if c.is_parent]
    assert parents
    assert all(not c.embed_text for c in parents)
