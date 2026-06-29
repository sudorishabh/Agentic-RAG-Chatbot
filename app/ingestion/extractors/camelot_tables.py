"""Camelot table extraction for born-digital table pages.

The hybrid router (see ``pdf_extractor``) sends born-digital pages that carry a
table here; scanned/image pages still go to Azure OCR. Camelot reads ruled
("lattice") and borderless ("stream") tables straight from the PDF vector layer,
and each table is rendered to the same ``TableData`` markdown the rest of the
pipeline already expects.

Camelot needs a file path, so the page content is written to a temp file. If
Camelot is not installed or finds nothing on a page, the router falls back to
PyMuPDF text for that page (the table degrades to plain text).
"""

from __future__ import annotations

import logging
import os
import tempfile

from app.config import get_settings
from app.ingestion.extractors.pdf_extractor import (
    TableData,
    _page_range_str,
    _rows_to_markdown,
)

logger = logging.getLogger(__name__)

__all__ = ["extract_tables"]


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


def _run_flavor(path: str, pages_arg: str, flavor: str) -> dict[int, list[TableData]]:
    import camelot

    out: dict[int, list[TableData]] = {}
    try:
        tables = camelot.read_pdf(path, pages=pages_arg, flavor=flavor, suppress_stdout=True)
    except Exception:
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

    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)

        by_page = _run_flavor(tmp_path, pages_arg, primary)

        # Pages that produced nothing under "lattice" (no ruled borders) get a
        # second pass with the borderless "stream" flavor.
        if primary == "lattice" and page_numbers:
            missing = [n for n in page_numbers if n not in by_page]
            if missing:
                by_page.update(_run_flavor(tmp_path, _page_range_str(missing), "stream"))
        return by_page
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                logger.debug("Could not remove temp PDF %s", tmp_path, exc_info=True)
