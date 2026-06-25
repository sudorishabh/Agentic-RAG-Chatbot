"""Unit tests for the per-page PDF extraction router.

Covers the routing decisions — clean pages extract locally, scanned/table pages
go to Azure, pages are stitched back in order — plus the EXTRACTION_MODE values
and the Azure-unavailable fallback.

The dispatch tests stub PyMuPDF classification and both extractors, so they need
neither PyMuPDF nor Azure. Two extra tests exercise the real PyMuPDF classifier
(born-digital text vs. a ruled grid) and are skipped when PyMuPDF is absent.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ingestion.extractors import pdf_extractor, pymupdf_local
from app.ingestion.extractors.pdf_extractor import (
    ExtractedVia,
    ExtractionResult,
    PageContent,
)
from app.ingestion.extractors.pymupdf_local import PageSignal, document_needs_azure


def _sig(page: int, *, scanned: bool = False, has_table: bool = False, chars: int = 500) -> PageSignal:
    return PageSignal(page_number=page, char_count=chars, scanned=scanned, has_table=has_table)


# --------------------------------------------------------------------------- #
# Pure decision function — no PyMuPDF / Azure needed.
# --------------------------------------------------------------------------- #

def test_text_only_document_does_not_need_azure():
    assert document_needs_azure([_sig(1), _sig(2), _sig(3)]) is False


def test_table_page_makes_document_need_azure():
    assert document_needs_azure([_sig(1), _sig(2, has_table=True), _sig(3)]) is True


def test_scanned_page_makes_document_need_azure():
    assert document_needs_azure([_sig(1, scanned=True), _sig(2)]) is True


# --------------------------------------------------------------------------- #
# Router dispatch — stub classification + extractors, assert which page went where.
# --------------------------------------------------------------------------- #

@pytest.fixture
def router(monkeypatch):
    calls = {"local_pages": None, "azure_pages": None, "local_full": 0}

    def fake_extract_local_pages(content, page_numbers=None):
        calls["local_pages"] = list(page_numbers) if page_numbers is not None else "ALL"
        nums = page_numbers if page_numbers is not None else [1]
        return {n: PageContent(page_number=n, text=f"local {n}", extracted_via=ExtractedVia.TEXT) for n in nums}

    def fake_extract_local(content, filename):  # whole-doc: local_only + fallback
        calls["local_full"] += 1
        return ExtractionResult(
            source=filename,
            pages=[PageContent(page_number=1, text="local", extracted_via=ExtractedVia.TEXT)],
            metadata={"engine": "pymupdf"},
        )

    def fake_ocr_pdf(content, page_numbers=None):
        calls["azure_pages"] = list(page_numbers) if page_numbers is not None else "ALL"
        nums = page_numbers if page_numbers is not None else [1]
        return {n: PageContent(page_number=n, text=f"azure {n}", extracted_via=ExtractedVia.OCR) for n in nums}

    monkeypatch.setattr(pymupdf_local, "extract_local_pages", fake_extract_local_pages)
    monkeypatch.setattr(pymupdf_local, "extract_local", fake_extract_local)
    monkeypatch.setattr(pdf_extractor, "_ocr_pdf", fake_ocr_pdf)

    def set_signals(signals):
        monkeypatch.setattr(pymupdf_local, "classify_document", lambda content: signals)

    def set_mode(mode):
        fake = SimpleNamespace(
            extraction_mode=mode,
            pdf_running_header_min_fraction=0.5,
            pdf_drop_number_soup=True,
        )
        monkeypatch.setattr(pdf_extractor, "get_settings", lambda: fake)

    return calls, set_signals, set_mode


def test_hybrid_text_only_routes_all_local(router):
    calls, set_signals, set_mode = router
    set_mode("hybrid")
    set_signals([_sig(1), _sig(2)])

    result = pdf_extractor.extract_pdf(b"%PDF-1.4", "doc.pdf")

    assert calls["local_pages"] == [1, 2]
    assert calls["azure_pages"] is None  # Azure never called
    assert result.metadata["route"] == "local"


def test_hybrid_mixed_splits_pages_and_stitches_in_order(router):
    calls, set_signals, set_mode = router
    set_mode("hybrid")
    set_signals([_sig(1), _sig(2, has_table=True), _sig(3, scanned=True)])

    result = pdf_extractor.extract_pdf(b"%PDF-1.4", "doc.pdf")

    assert calls["local_pages"] == [1]
    assert calls["azure_pages"] == [2, 3]
    assert result.metadata["route"] == "per_page"
    # stitched in page order: local page first, then the two Azure pages
    assert [p.page_number for p in result.pages] == [1, 2, 3]
    assert result.pages[0].extracted_via is ExtractedVia.TEXT
    assert result.pages[1].extracted_via is ExtractedVia.OCR
    assert result.pages[2].extracted_via is ExtractedVia.OCR


def test_hybrid_all_table_pages_route_azure(router):
    calls, set_signals, set_mode = router
    set_mode("hybrid")
    set_signals([_sig(1, has_table=True), _sig(2, scanned=True)])

    result = pdf_extractor.extract_pdf(b"%PDF-1.4", "doc.pdf")

    assert calls["azure_pages"] == [1, 2]
    assert calls["local_pages"] is None
    assert result.metadata["route"] == "per_page"


def test_local_only_never_calls_azure(router):
    calls, _set_signals, set_mode = router
    set_mode("local_only")

    result = pdf_extractor.extract_pdf(b"%PDF", "doc.pdf")

    assert calls["local_full"] == 1
    assert calls["azure_pages"] is None
    assert result.metadata["route"] == "local"


def test_azure_only_routes_whole_doc_to_azure(router):
    calls, _set_signals, set_mode = router
    set_mode("azure_only")

    result = pdf_extractor.extract_pdf(b"%PDF", "doc.pdf")

    assert calls["azure_pages"] == "ALL"  # whole document
    assert result.metadata["route"] == "azure"


def test_azure_only_unavailable_falls_back_to_local(router, monkeypatch):
    calls, _set_signals, set_mode = router
    set_mode("azure_only")
    monkeypatch.setattr(pdf_extractor, "_ocr_pdf", lambda content, page_numbers=None: {})

    result = pdf_extractor.extract_pdf(b"%PDF", "doc.pdf")

    assert calls["local_full"] == 1
    assert result.metadata["route"] == "azure_unavailable_local_fallback"


def test_hybrid_azure_unavailable_falls_back_to_local_text(router, monkeypatch):
    calls, set_signals, set_mode = router
    set_mode("hybrid")
    set_signals([_sig(1), _sig(2, has_table=True)])
    monkeypatch.setattr(pdf_extractor, "_ocr_pdf", lambda content, page_numbers=None: {})

    result = pdf_extractor.extract_pdf(b"%PDF", "doc.pdf")

    # flagged pages couldn't reach Azure, so every page falls back to local text
    assert calls["local_pages"] == [1, 2]
    assert result.metadata["route"] == "azure_unavailable_local_fallback"


# --------------------------------------------------------------------------- #
# Real PyMuPDF classifier (skipped when PyMuPDF is not installed).
# --------------------------------------------------------------------------- #

def test_real_born_digital_text_routes_local():
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "This is a normal paragraph of born digital text. " * 30, fontsize=11)
    content = doc.tobytes()
    doc.close()

    signals = pymupdf_local.classify_document(content)
    assert document_needs_azure(signals) is False  # no false-positive table flag

    result = pymupdf_local.extract_local(content, "born.pdf")
    assert result.pages
    assert "born digital text" in result.text


def test_real_ruled_grid_is_detected_as_table():
    fitz = pytest.importorskip("fitz")
    from app.ingestion.extractors.pymupdf_local import _grid_line_counts

    doc = fitz.open()
    page = doc.new_page()
    x0, y0, step = 100, 100, 40
    for k in range(5):  # 5 horizontal + 5 vertical lines => a 4x4 ruled grid
        y = y0 + k * step
        page.draw_line(fitz.Point(x0, y), fitz.Point(x0 + 4 * step, y))
        x = x0 + k * step
        page.draw_line(fitz.Point(x, y0), fitz.Point(x, y0 + 4 * step))
    content = doc.tobytes()
    doc.close()

    reopened = fitz.open(stream=content, filetype="pdf")
    h_lines, v_lines = _grid_line_counts(reopened[0])
    reopened.close()
    assert h_lines >= 3 and v_lines >= 3
