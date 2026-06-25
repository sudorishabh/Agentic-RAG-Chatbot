"""Page-text normalization for extracted PDFs.

Strips boilerplate that Azure Document Intelligence's Layout markdown (and, to a
lesser extent, local extraction) leaves in page text: HTML layout comments,
``<figure>`` wrappers, and single-cell page-number bars. Cleaning happens in the
extraction layer so the downstream chunker / embedder / payload are untouched.
"""

from __future__ import annotations

import math
import re
from collections import Counter

__all__ = ["normalize_page_text", "strip_running_lines"]

# <!-- PageBreak -->, <!-- PageNumber="22" -->, <!-- PageHeader=... -->, ...
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# <figure>...</figure> — unwrap to inner content (empty ones disappear).
_FIGURE_BLOCK = re.compile(r"<figure>\s*(.*?)\s*</figure>", re.DOTALL | re.IGNORECASE)
_FIGURE_TAG = re.compile(r"</?figure>", re.IGNORECASE)

# A standalone page-number bar: "|  ii  |", "| 14 |" — a single cell holding only
# a page number (roman or arabic). Real multi-cell table rows are left alone.
_PAGE_NUMBER_BAR = re.compile(r"^\s*\|\s*[ivxlcdm\d]+\s*\|\s*$", re.IGNORECASE)

# A "number token": digits plus number punctuation (e.g. "2,020", "-12.5%", "(3)").
_NUM_TOKEN = re.compile(r"^[\d.,%+\-–—()]+$")

# A line ending like a sentence — never treated as a chart label.
_SENTENCE_END = re.compile(r"[.:;!?]$")

_BLANK_RUNS = re.compile(r"\n{3,}")


def _is_number_soup(line: str) -> bool:
    """A bare numeric run on one line (chart axis/data labels), no semantic content."""
    toks = line.split()
    if len(toks) < 4:
        return False
    numeric = sum(1 for t in toks if _NUM_TOKEN.match(t))
    return numeric / len(toks) >= 0.7


def _is_bare_number(line: str) -> bool:
    s = line.strip()
    return bool(s) and bool(_NUM_TOKEN.match(s)) and any(c.isdigit() for c in s)


def _is_chart_label(line: str) -> bool:
    """A short chart axis/category label — a few words, no sentence punctuation
    (e.g. "China", "Japan, South Korea", "RoW"). Table rows are never labels."""
    s = line.strip()
    if not s or s.startswith("|") or _SENTENCE_END.search(s):
        return False
    return len(s) <= 28 and len(s.split()) <= 4


def _drop_number_runs(lines: list[str], min_nums: int = 4) -> list[str]:
    """Drop chart data regions: contiguous blocks of bare-number lines, possibly
    interleaved with short category labels (vertical bar/line chart axes + data).

    A block is dropped when it holds >= ``min_nums`` bare numbers and is at least
    40% numeric, so number-dominated chart soup goes while real short lists (which
    carry few or no bare numbers) are kept.
    """
    out: list[str] = []
    i = 0
    while i < len(lines):
        j = i
        nums = 0
        while j < len(lines) and (_is_bare_number(lines[j]) or _is_chart_label(lines[j])):
            if _is_bare_number(lines[j]):
                nums += 1
            j += 1
        run = j - i
        if run and nums >= min_nums and nums / run >= 0.4:
            i = j  # numeric-dominated block — drop the whole chart region
        elif j > i:
            out.extend(lines[i:j])  # not chart-like enough — keep
            i = j
        else:
            out.append(lines[i])
            i += 1
    return out


def _strip_figures(text: str) -> str:
    text = _FIGURE_BLOCK.sub(lambda m: m.group(1).strip(), text)
    return _FIGURE_TAG.sub("", text)  # drop any unmatched stray tags


def normalize_page_text(text: str, *, drop_number_soup: bool = True) -> str:
    """Remove layout boilerplate from a single page's text."""
    if not text:
        return text
    text = _HTML_COMMENT.sub("", text)
    text = _strip_figures(text)
    lines = []
    for ln in text.splitlines():
        if _PAGE_NUMBER_BAR.match(ln):
            continue
        if drop_number_soup and _is_number_soup(ln):
            continue
        lines.append(ln)
    if drop_number_soup:
        lines = _drop_number_runs(lines)
    text = _BLANK_RUNS.sub("\n\n", "\n".join(lines))
    return text.strip()


def _line_key(line: str) -> str:
    """Comparison key for a line; '' for lines never treated as running boilerplate."""
    s = " ".join(line.split()).lower()
    if not s or s.startswith("|"):  # blank, or a table row (content — never strip)
        return ""
    return s


def strip_running_lines(
    pages: list[str],
    *,
    min_fraction: float = 0.5,
    min_pages: int = 4,
    min_count: int = 3,
) -> list[str]:
    """Remove running headers/footers: lines repeated across most of the pages.

    A line counted once per page; if it appears on >= the page-count threshold it
    is dropped from every page. No-op for short documents or min_fraction <= 0.
    """
    n = len(pages)
    if n < min_pages or min_fraction <= 0:
        return pages

    page_counts: Counter = Counter()
    for text in pages:
        seen = {_line_key(ln) for ln in text.splitlines()}
        seen.discard("")
        page_counts.update(seen)

    threshold = max(min_count, math.ceil(min_fraction * n))
    boilerplate = {key for key, c in page_counts.items() if c >= threshold}
    if not boilerplate:
        return pages

    out: list[str] = []
    for text in pages:
        kept = [ln for ln in text.splitlines() if _line_key(ln) not in boilerplate]
        out.append(_BLANK_RUNS.sub("\n\n", "\n".join(kept)).strip())
    return out
