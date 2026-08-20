"""The edition must reach the model and the citation, and the page's date must
not read as the document's own.

All ten TERI annual reports are in-body attachments on a single Drupal page, so
they share a title *and* a ``published_at`` (2022-02-09). The only thing that
tells them apart is ``edition_label``, recovered at ingest. These tests pin the
read-side contract that surfaces it — no re-ingestion is involved, the label is
already on the chunk payload.
"""

from __future__ import annotations

import pytest

from app.generation.prompts import _source_hint
from app.retrieval.citations import _source_from_payload

# One real payload per edition, as they exist in Qdrant today.
PAGE_DATE = "2022-02-09T06:59:06"


def _annual(edition: str | None, page: int = 12, title: str = "Annual Reports") -> dict:
    return {
        "source_type": "pdf_attachment",
        "title": title,
        "edition_label": edition,
        "published_at": PAGE_DATE,
        "page_number": page,
    }


# --------------------------------------------------------------------------- #
# "What is the annual report for 2024-25?"  -> the edition must be visible
# --------------------------------------------------------------------------- #

def test_the_edition_appears_in_the_block_header():
    header = _source_hint(_annual("2024-25"))
    assert "edition 2024-25" in header


def test_editions_of_one_series_are_distinguishable():
    """Without the edition every block header is byte-identical."""
    headers = {_source_hint(_annual(e)) for e in
               ("2024-25", "2023-24", "2022-23", "2021-22", "2015-16")}
    assert len(headers) == 5


# --------------------------------------------------------------------------- #
# "When was the 2024-25 annual report published?"  -> the page date must be
# labelled as the page's, not the report's
# --------------------------------------------------------------------------- #

def test_the_page_date_is_labelled_as_the_pages():
    header = _source_hint(_annual("2024-25"))
    assert "page published 2022-02-09" in header
    # The bare word must not appear on its own; that is what invited the model
    # to report 2022 as the report's publication date.
    assert "· published 2022" not in header


def test_the_edition_is_not_presented_as_a_date():
    """"2024-25" is a reporting period, so it must not be emitted as a date."""
    header = _source_hint(_annual("2024-25"))
    assert "published 2024-25" not in header
    assert "page published 2022-02-09" in header


# --------------------------------------------------------------------------- #
# "What year is the latest annual report?" / "What annual reports are
# available?"  -> every edition must carry its own label through to citations
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "edition",
    ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21",
     "2019-20", "2018-19", "2017-18", "2016-17", "2015-16"],
)
def test_every_edition_reaches_the_citation(edition):
    source = _source_from_payload(_annual(edition))
    assert source.edition == edition
    assert source.title == "Annual Reports"


def test_the_full_series_is_enumerable_from_headers():
    """The evidence a "what is available?" answer would be built from."""
    editions = [f"{y}-{str(y + 1)[2:]}" for y in range(2015, 2025)]
    rendered = [_source_hint(_annual(e)) for e in editions]
    for edition, header in zip(editions, rendered):
        assert f"edition {edition}" in header
    assert len({*rendered}) == len(editions)


# --------------------------------------------------------------------------- #
# Nothing regresses for documents without an edition
# --------------------------------------------------------------------------- #

def test_a_document_with_no_edition_is_unchanged_apart_from_the_label():
    header = _source_hint(_annual(None, page=3))
    assert "edition" not in header
    assert "page published 2022-02-09" in header


def test_a_website_page_still_reports_its_own_date():
    header = _source_hint({
        "source_type": "website", "title": "TERI launches report",
        "published_at": "2024-05-01T00:00:00",
    })
    assert "page published 2024-05-01" in header
    assert "edition" not in header


def test_an_edition_free_citation_carries_no_edition():
    assert _source_from_payload(_annual(None)).edition is None


# --------------------------------------------------------------------------- #
# The summariser path presents the same two facts the same way
# --------------------------------------------------------------------------- #

def test_the_summariser_list_separates_edition_from_page_date():
    from app.pipeline.summarize import _Doc, _numbered_line

    docs = [
        _Doc(document_id="a", title="Annual Reports", url=None,
             published="2022-02-09", text="…", edition="2024-25"),
        _Doc(document_id="b", title="Annual Reports", url=None,
             published="2022-02-09", text="…", edition="2015-16"),
    ]
    rendered = chr(10).join(_numbered_line(i, d) for i, d in enumerate(docs, start=1))
    assert "edition 2024-25" in rendered
    assert "edition 2015-16" in rendered
    assert "page published 2022-02-09" in rendered


def test_the_summariser_reads_the_edition_from_a_chunk_payload():
    from app.pipeline.summarize import _doc_from_payload

    doc = _doc_from_payload("d1", {
        "title": "Annual Reports", "published_at": PAGE_DATE,
        "edition_label": "2024-25", "chunk_text": "…",
    })
    assert doc.edition == "2024-25"
    assert doc.published == "2022-02-09"
