"""Unit tests for the document-level PDF extraction router.

Covers the three required routing decisions — a text-only document goes local,
a document with a table page goes to Azure, a scanned document goes to Azure —
plus the explicit EXTRACTION_MODE values and the Azure-unavailable fallback.

The router dispatch tests stub out PyMuPDF classification and both extractors,
so they need neither PyMuPDF nor Azure. One extra test exercises the real
PyMuPDF classifier on a synthetic born-digital PDF and is skipped when PyMuPDF
is not installed.
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
# Router dispatch — stub classification + both extractors, assert the path.
# --------------------------------------------------------------------------- #

@pytest.fixture
def router(monkeypatch):
    calls = {"local": 0, "azure": 0}

    def fake_extract_local(content, filename):
        calls["local"] += 1
        return ExtractionResult(
            source=filename,
            pages=[PageContent(page_number=1, text="local text", extracted_via=ExtractedVia.TEXT)],
            metadata={"engine": "pymupdf"},
        )

    def fake_ocr_pdf(content, page_numbers=None):
        calls["azure"] += 1
        return {1: PageContent(page_number=1, text="azure text", extracted_via=ExtractedVia.OCR)}

    monkeypatch.setattr(pymupdf_local, "extract_local", fake_extract_local)
    monkeypatch.setattr(pdf_extractor, "_ocr_pdf", fake_ocr_pdf)

    def set_signals(signals):
        monkeypatch.setattr(pymupdf_local, "classify_document", lambda content: signals)

    def set_mode(mode):
        monkeypatch.setattr(pdf_extractor, "get_settings", lambda: SimpleNamespace(extraction_mode=mode))

    return calls, set_signals, set_mode


def test_hybrid_text_only_routes_local(router):
    calls, set_signals, set_mode = router
    set_mode("hybrid")
    set_signals([_sig(1), _sig(2)])

    result = pdf_extractor.extract_pdf(b"%PDF-1.4", "doc.pdf")

    assert calls == {"local": 1, "azure": 0}
    assert result.metadata["route"] == "local"


def test_hybrid_table_page_routes_azure(router):
    calls, set_signals, set_mode = router
    set_mode("hybrid")
    set_signals([_sig(1), _sig(2, has_table=True)])

    result = pdf_extractor.extract_pdf(b"%PDF-1.4", "doc.pdf")

    assert calls == {"local": 0, "azure": 1}
    assert result.metadata["route"] == "azure"


def test_hybrid_scanned_page_routes_azure(router):
    calls, set_signals, set_mode = router
    set_mode("hybrid")
    set_signals([_sig(1, scanned=True), _sig(2)])

    result = pdf_extractor.extract_pdf(b"%PDF-1.4", "doc.pdf")

    assert calls == {"local": 0, "azure": 1}
    assert result.metadata["route"] == "azure"


def test_local_only_never_calls_azure(router):
    calls, _set_signals, set_mode = router
    set_mode("local_only")

    result = pdf_extractor.extract_pdf(b"%PDF", "doc.pdf")

    assert calls == {"local": 1, "azure": 0}
    assert result.metadata["route"] == "local"


def test_azure_only_routes_azure(router):
    calls, _set_signals, set_mode = router
    set_mode("azure_only")

    result = pdf_extractor.extract_pdf(b"%PDF", "doc.pdf")

    assert calls == {"local": 0, "azure": 1}
    assert result.metadata["route"] == "azure"


def test_azure_unavailable_falls_back_to_local(router, monkeypatch):
    calls, _set_signals, set_mode = router
    set_mode("azure_only")
    monkeypatch.setattr(pdf_extractor, "_ocr_pdf", lambda content, page_numbers=None: {})

    result = pdf_extractor.extract_pdf(b"%PDF", "doc.pdf")

    assert calls["local"] == 1
    assert result.metadata["route"] == "azure_unavailable_local_fallback"


# --------------------------------------------------------------------------- #
# Real PyMuPDF classifier on a synthetic born-digital PDF (skipped without it).
# --------------------------------------------------------------------------- #

def test_real_born_digital_pdf_classifies_local():
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "This is a normal paragraph of born digital text. " * 30, fontsize=11)
    content = doc.tobytes()
    doc.close()

    signals = pymupdf_local.classify_document(content)
    assert document_needs_azure(signals) is False

    result = pymupdf_local.extract_local(content, "born.pdf")
    assert result.pages
    assert "born digital text" in result.text
