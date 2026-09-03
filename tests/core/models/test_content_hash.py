"""The content hash covers body text only, so metadata that could later be
derived (an LLM-read title) can never destabilise change detection."""

from __future__ import annotations

from app.core.models import CanonicalDocument, CanonicalSection


def _doc(title: str | None, body: str, **kwargs) -> CanonicalDocument:
    return CanonicalDocument(
        document_id="d",
        source_type="pdf",
        title=title,
        sections=[CanonicalSection(text=body, order=0)],
        **kwargs,
    )


def test_title_does_not_affect_the_content_hash():
    body = "The programme added 1.2 GW of rooftop capacity in 2023."
    assert (
        _doc("Rooftop solar in Delhi", body).compute_content_hash()
        == _doc("Rooftop Solar In Delhi (2023 edition)", body).compute_content_hash()
    )
    assert _doc(None, body).compute_content_hash() == _doc("Any", body).compute_content_hash()


def test_body_still_drives_the_content_hash():
    assert (
        _doc("T", "Capacity reached 1.2 GW.").compute_content_hash()
        != _doc("T", "Capacity reached 2.4 GW.").compute_content_hash()
    )


def test_metadata_does_not_affect_the_content_hash():
    body = "Shared body text."
    bare = _doc("T", body)
    enriched = _doc(
        "T", body, authors=["A. Author"], categories=["Energy"], effective_start_date="2024-01-01"
    )
    assert bare.compute_content_hash() == enriched.compute_content_hash()


def test_section_headings_are_part_of_the_body():
    with_heading = CanonicalDocument(
        document_id="d",
        source_type="pdf",
        sections=[CanonicalSection(heading="Findings", text="Body.", order=0)],
    )
    without = CanonicalDocument(
        document_id="d",
        source_type="pdf",
        sections=[CanonicalSection(text="Body.", order=0)],
    )
    assert with_heading.compute_content_hash() != without.compute_content_hash()


def test_ensure_content_hash_is_cached_and_idempotent():
    doc = _doc("T", "Body.")
    first = doc.ensure_content_hash()
    doc.title = "A completely different title"
    assert doc.ensure_content_hash() == first
