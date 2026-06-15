"""PDF text extraction.

Primary path uses PyMuPDF to read the embedded text layer page by page.
When a page has no usable text layer (typically a scanned/image-only page),
it falls back to Azure Document Intelligence OCR on a rendered image of that
page. Chunking and embedding happen elsewhere; this module only produces text.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

import fitz  # PyMuPDF

from app.config import get_settings

logger = logging.getLogger(__name__)

# A page whose stripped text layer is shorter than this is treated as
# "no real text" and routed to the OCR fallback.
MIN_TEXT_CHARS = 10
# Resolution used when rendering a page to an image for OCR. Higher DPI
# improves OCR accuracy at the cost of a larger payload.
OCR_RENDER_DPI = 300
# Document Intelligence model for plain OCR (text + layout, no field extraction).
OCR_MODEL_ID = "prebuilt-read"


class ExtractedVia(str, Enum):
    TEXT = "text"  # read from the PDF text layer
    OCR = "ocr"  # recovered via Azure OCR fallback
    EMPTY = "empty"  # no text layer and OCR unavailable/empty


@dataclass
class PageContent:
    page_number: int  # 1-based
    text: str
    extracted_via: ExtractedVia

@dataclass
class ExtractionResult:
    source: str  # original filename
    pages: list[PageContent]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        """All page text joined in reading order."""
        return "\n\n".join(page.text for page in self.pages if page.text)

    @property
    def ocr_page_numbers(self) -> list[int]:
        return [p.page_number for p in self.pages if p.extracted_via is ExtractedVia.OCR]


def extract_pdf(content: bytes, filename: str) -> ExtractionResult:
    """Extract text from a PDF, one entry per page, with OCR fallback."""
    pages: list[PageContent] = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            # PyMuPDF's default extraction follows the page's content stream,
            # which preserves reading order for well-formed (incl. multi-column)
            # PDFs. We deliberately avoid sort=True, which interleaves columns.
            text = page.get_text("text").strip()
            if len(text) >= MIN_TEXT_CHARS:
                via = ExtractedVia.TEXT
            else:
                text = _ocr_page(page)
                via = ExtractedVia.OCR if text else ExtractedVia.EMPTY
            pages.append(
                PageContent(page_number=page.number + 1, text=text, extracted_via=via)
            )

    result = ExtractionResult(source=filename, pages=pages)
    if result.ocr_page_numbers:
        logger.info(
            "OCR fallback used for %s on pages %s",
            filename,
            result.ocr_page_numbers,
        )
    return result


def _ocr_page(page: fitz.Page) -> str:
    """Render a page to an image and OCR it via Azure Document Intelligence.

    Returns an empty string if OCR is not configured or finds no text.
    """
    client = _get_ocr_client()
    if client is None:
        logger.warning(
            "Page %s has no text layer but Azure OCR is not configured; skipping.",
            page.number + 1,
        )
        return ""

    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

    image_bytes = page.get_pixmap(dpi=OCR_RENDER_DPI).tobytes("png")
    poller = client.begin_analyze_document(
        OCR_MODEL_ID, body=AnalyzeDocumentRequest(bytes_source=image_bytes)
    )
    return (poller.result().content or "").strip()


@lru_cache
def _get_ocr_client():
    """Build the Document Intelligence client, or None if OCR is not configured."""
    settings = get_settings()
    if not (
        settings.azure_document_intelligence_endpoint
        and settings.azure_document_intelligence_key
    ):
        return None

    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    return DocumentIntelligenceClient(
        endpoint=settings.azure_document_intelligence_endpoint,
        credential=AzureKeyCredential(settings.azure_document_intelligence_key),
    )
