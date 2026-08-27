"""Regression tests: one source, one type name.

Citations were built by two functions that disagreed. ``_citation_from_block``
passed the payload's ``source_type`` through (``pdf_attachment``), while
``_source_from_payload`` — which builds the ``also_available`` entries —
hardcoded ``pdf``. The same document therefore carried one type name as a
primary citation and another as an alternate format of a neighbouring block.

The invariant enforced here: the citation type is a function of the payload
alone, so the same payload cannot produce two names, whichever slot it lands in.
The vocabulary is ingestion's own — ``website`` and ``pdf_attachment`` — with
the pre-rename ``article`` alias folded into ``website``; no second vocabulary
is introduced.
"""

from __future__ import annotations

import pytest

from app.core.models.context import ContextBlock
from app.retrieval.citations import build_citations

# Exactly what ingestion writes: app/ingestion/canonical.py (`website`,
# `pdf_attachment`) and app/ingestion/change_detection/drupal.py.
INGESTED_SOURCE_TYPES = ("website", "pdf_attachment")


def _payload(source_type, **extra):
    payload = {
        "document_id": f"doc-{source_type}",
        "source_type": source_type,
        "title": "Annual Report",
        "chunk_text": "body",
        "source_url": "https://example.org/page",
        "file_url": "https://example.org/report.pdf",
    }
    payload.update(extra)
    return payload


def _block(payload, also=()):
    return ContextBlock(n=1, text="body", payload=payload, also_available=list(also))


# --------------------------------------------------------------------------- #
# The defect: one payload, two names.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("source_type", INGESTED_SOURCE_TYPES)
def test_same_payload_yields_one_type_in_both_slots(source_type):
    """The identical payload cited directly and listed as an alternate must
    carry the same type name."""
    payload = _payload(source_type)
    citation = build_citations([_block(payload, also=[payload])])[0]
    assert citation.type == citation.also_available[0].type


@pytest.mark.parametrize("source_type", INGESTED_SOURCE_TYPES)
def test_citation_type_is_the_ingested_source_type(source_type):
    payload = _payload(source_type)
    citation = build_citations([_block(payload, also=[payload])])[0]
    assert citation.type == source_type
    assert citation.also_available[0].type == source_type


def test_website_and_its_attached_pdf_keep_their_own_types():
    """The real ``also_available`` case: a website block whose near-duplicate is
    its own attached PDF. Two sources, two types, each named once."""
    website = _payload("website", document_id="node-1", linked_pdf_id="file-1")
    attachment = _payload("pdf_attachment", document_id="file-1", page_number=3)
    citation = build_citations([_block(website, also=[attachment])])[0]

    assert citation.type == "website"
    assert [s.type for s in citation.also_available] == ["pdf_attachment"]


def test_no_citation_uses_a_type_outside_the_ingested_vocabulary():
    blocks = [
        _block(_payload("website"), also=[_payload("pdf_attachment")]),
        _block(_payload("pdf_attachment"), also=[_payload("website")]),
    ]
    names = {c.type for c in build_citations(blocks)}
    names |= {s.type for c in build_citations(blocks) for s in c.also_available}
    assert names <= set(INGESTED_SOURCE_TYPES)


# --------------------------------------------------------------------------- #
# The legacy alias folds into the canonical name, in both slots.
# --------------------------------------------------------------------------- #

def test_legacy_article_normalizes_to_website_everywhere():
    """Points indexed before the rename carry ``article``; both builders already
    treated it as a website, and they must keep agreeing on the name."""
    payload = _payload("article")
    citation = build_citations([_block(payload, also=[payload])])[0]
    assert citation.type == "website"
    assert citation.also_available[0].type == "website"


# --------------------------------------------------------------------------- #
# Everything else about a citation is unchanged.
# --------------------------------------------------------------------------- #

def test_website_citation_still_links_to_its_page():
    citation = build_citations([_block(_payload("website"))])[0]
    assert citation.url == "https://example.org/page"
    assert citation.document_id == "doc-website"


def test_pdf_citation_still_links_to_the_file_with_its_page_anchor():
    citation = build_citations([_block(_payload("pdf_attachment", page_number=3))])[0]
    assert citation.url == "https://example.org/report.pdf#page=3"
    assert (citation.page, citation.page_end) == (3, 3)
