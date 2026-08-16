"""Camelot table extraction for born-digital table pages.

The hybrid router (see ``pdf_extractor``) sends born-digital pages that carry a
table here; scanned/image pages still go to Azure OCR. Camelot reads ruled
("lattice") and borderless ("stream") tables straight from the PDF vector layer,
and each table is rendered to the same ``TableData`` markdown the rest of the
pipeline already expects.

Camelot needs a file path, so the page content is written to a temp file --
re-saved through PyMuPDF to drop any permission flags that would otherwise make
Camelot's backend refuse the document. If Camelot is not installed or finds
nothing on a page, the router falls back to PyMuPDF text for that page (the
table degrades to plain text).
"""

from __future__ import annotations

import gc
import logging
import os
import tempfile
import threading

from app.config import get_settings
from app.ingestion.extractors.pdf_extractor import (
    TableData,
    _page_range_str,
    _rows_to_markdown,
)

logger = logging.getLogger(__name__)

__all__ = ["extract_tables"]

# Camelot's PDF backend is pypdfium2, which keeps its open-document bookkeeping
# in module-level state -- an `ObjectTracker` dict, plus a `_kids` set per
# object -- and takes no lock over any of it (pypdfium2/internal/bases.py:81-88,
# 151-180). Two worker threads inside `read_pdf` therefore race that
# bookkeeping. Measured under `ingest_workers` > 1: "Some kids weakrefs have not
# been cleaned up", an AssertionError raised from the object finalizer, and --
# once the underlying PDFium objects are freed twice -- an intermittent hard
# crash of the whole process with STATUS_HEAP_CORRUPTION (0xC0000374). Seen at
# 2 and 4 workers, never at 1, and the frequency scales with the worker count.
#
# `_remove_temp_pdf`'s `gc.collect()` compounds it: running the finalizers is
# exactly what trips the race.
#
# Serializing table extraction is the smallest change that makes
# `ingest_workers > 1` safe. Everything else in the per-document path --
# download, Azure OCR, embedding, upsert, catalog writes -- stays concurrent,
# and Camelot holds the GIL throughout anyway, so almost no parallelism is
# given up. Module-level, because the state being guarded is the library's own.
_camelot_lock = threading.Lock()


def _table_to_data(table) -> TableData | None:
    rows = [
        ["" if cell is None else str(cell) for cell in row]
        for row in table.df.values.tolist()
    ]
    n_cols = max((len(r) for r in rows), default=0)
    # A real table is a grid: drop degenerate 1-row / 1-col matches, which the
    # borderless "stream" flavor produces from ordinary prose.
    if len(rows) < 2 or n_cols < 2:
        return None
    markdown = _rows_to_markdown(rows)
    if not markdown:
        return None
    page_no = int(getattr(table, "page", 0) or 0) or None
    return TableData(
        markdown=markdown,
        page_number=page_no,
        rows=len(rows),
        cols=n_cols,
        cells=rows or None,
    )


def _is_extraction_forbidden(exc: BaseException) -> bool:
    """True if the PDF's permission flags blocked Camelot's backend outright."""
    try:
        from playa.exceptions import PDFTextExtractionNotAllowed
    except Exception:
        return False
    return isinstance(exc, PDFTextExtractionNotAllowed)


def _write_pdf(content: bytes, path: str) -> None:
    """Write the PDF to ``path`` with any permission flags stripped.

    Plenty of PDFs ship with an owner password that clears the "extract
    content" bit. PyMuPDF ignores that flag -- which is why classification still
    yields text -- but Camelot's backend enforces it and refuses the whole
    document. Re-saving through PyMuPDF drops the encryption dictionary so the
    tables stay reachable. Falls back to the raw bytes if the re-save fails.
    """
    try:
        import fitz  # PyMuPDF

        with fitz.open(stream=content, filetype="pdf") as doc:
            doc.save(path, encryption=fitz.PDF_ENCRYPT_NONE)
        return
    except Exception:
        logger.debug("Could not re-save PDF without encryption.", exc_info=True)
    with open(path, "wb") as fh:
        fh.write(content)


def _remove_temp_pdf(path: str) -> None:
    """Delete the temp PDF, collecting Camelot's stragglers first if we must.

    On Windows the first ``remove`` loses to WinError 32: Camelot's PDF backend
    leaves a document object holding an open handle, and it only releases on
    finalization. A ``gc.collect()`` runs those finalizers, after which the
    delete succeeds -- without it every extracted page leaks a PDF into the temp
    dir. POSIX unlinks an open file happily, so the retry never runs there.
    """
    if not os.path.exists(path):
        return
    try:
        os.remove(path)
        return
    except OSError:
        gc.collect()
    try:
        os.remove(path)
    except OSError:
        logger.debug("Could not remove temp PDF %s", path, exc_info=True)


def _run_flavor(path: str, pages_arg: str, flavor: str) -> dict[int, list[TableData]]:
    import camelot

    out: dict[int, list[TableData]] = {}
    try:
        tables = camelot.read_pdf(path, pages=pages_arg, flavor=flavor, suppress_stdout=True)
    except Exception as exc:
        if _is_extraction_forbidden(exc):
            logger.warning(
                "Camelot %s: the PDF forbids text extraction, so these pages fall "
                "back to local text (their tables degrade to plain text).",
                flavor,
            )
        else:
            logger.exception("Camelot %s extraction failed.", flavor)
        return out
    for table in tables:
        td = _table_to_data(table)
        if td is None:
            continue
        out.setdefault(td.page_number or 0, []).append(td)
    return out


def extract_tables(
    content: bytes, page_numbers: list[int] | None = None
) -> dict[int, list[TableData]]:
    """Extract tables from the given pages (1-based; None => all) with Camelot.

    Returns a ``{page_number: [TableData, ...]}`` map. Empty dict if Camelot is
    unavailable or finds no table — the router then falls back to local text.
    """
    try:
        import camelot  # noqa: F401
    except Exception:
        logger.warning("Camelot is not installed; table pages fall back to local text.")
        return {}

    settings = get_settings()
    primary = (settings.camelot_flavor or "lattice").strip().lower()
    pages_arg = _page_range_str(page_numbers) if page_numbers else "all"

    # Held across the temp file's whole life, not just `read_pdf`: the backend's
    # objects outlive the call and are torn down by the finalizers that
    # `_remove_temp_pdf` forces, so the cleanup races too.
    with _camelot_lock:
        tmp_path: str | None = None
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            _write_pdf(content, tmp_path)

            by_page = _run_flavor(tmp_path, pages_arg, primary)

            # Pages that produced nothing under "lattice" (no ruled borders) get a
            # second pass with the borderless "stream" flavor.
            if primary == "lattice" and page_numbers:
                missing = [n for n in page_numbers if n not in by_page]
                if missing:
                    by_page.update(_run_flavor(tmp_path, _page_range_str(missing), "stream"))
            return by_page
        finally:
            if tmp_path:
                _remove_temp_pdf(tmp_path)
