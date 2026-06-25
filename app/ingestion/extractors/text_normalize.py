"""Page-text normalization for extracted PDFs.

Strips boilerplate that Azure Document Intelligence's Layout markdown (and, to a
lesser extent, local extraction) leaves in page text: HTML layout comments,
``<figure>`` wrappers, and single-cell page-number bars. Cleaning happens in the
extraction layer so the downstream chunker / embedder / payload are untouched.
"""

from __future__ import annotations

import re

__all__ = ["normalize_page_text"]

# <!-- PageBreak -->, <!-- PageNumber="22" -->, <!-- PageHeader=... -->, ...
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# <figure>...</figure> — unwrap to inner content (empty ones disappear).
_FIGURE_BLOCK = re.compile(r"<figure>\s*(.*?)\s*</figure>", re.DOTALL | re.IGNORECASE)
_FIGURE_TAG = re.compile(r"</?figure>", re.IGNORECASE)

# A standalone page-number bar: "|  ii  |", "| 14 |" — a single cell holding only
# a page number (roman or arabic). Real multi-cell table rows are left alone.
_PAGE_NUMBER_BAR = re.compile(r"^\s*\|\s*[ivxlcdm\d]+\s*\|\s*$", re.IGNORECASE)

_BLANK_RUNS = re.compile(r"\n{3,}")


def _strip_figures(text: str) -> str:
    text = _FIGURE_BLOCK.sub(lambda m: m.group(1).strip(), text)
    return _FIGURE_TAG.sub("", text)  # drop any unmatched stray tags


def normalize_page_text(text: str) -> str:
    """Remove layout boilerplate from a single page's text."""
    if not text:
        return text
    text = _HTML_COMMENT.sub("", text)
    text = _strip_figures(text)
    lines = [ln for ln in text.splitlines() if not _PAGE_NUMBER_BAR.match(ln)]
    text = _BLANK_RUNS.sub("\n\n", "\n".join(lines))
    return text.strip()
