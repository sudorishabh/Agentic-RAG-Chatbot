"""Non-substantive section detection: tables of contents, glossaries and
bibliographies extract cleanly but pollute retrieval. They are flagged by
their line *shape* (extraction routinely garbles their headings, so content
is more reliable) so search can exclude them."""
from __future__ import annotations

import re

_DOT_LEADER = re.compile(r"\.{4,}\s*\d*\s*$")          # "Conclusions ........ 44"
_URL_RE = re.compile(r"https?://")
# A standalone citation year — "(2020)", "(2020a)". Inline prose citations like
# "(Hall, Spencer & Kumar, 2020)" don't match: the paren opens on a name, not a digit.
_CITE_YEAR = re.compile(r"\(\d{4}[a-z]?\)")
_GLOSSARY_LINE = re.compile(r"^[A-Z][A-Za-z0-9/.\-]{0,7}\s+[–\-]\s+\S")


def _is_citation_line(line: str) -> bool:
    return bool(_URL_RE.search(line) or _CITE_YEAR.search(line)) or "Retrieved from" in line


def classify_section(text: str) -> str | None:
    """Return 'toc' | 'references' | 'glossary' for a non-substantive chunk, else None."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    n = len(lines)
    if n < 4:
        return None
    dots = sum(1 for ln in lines if _DOT_LEADER.search(ln))
    if dots >= 3 and dots / n >= 0.3:
        return "toc"
    cites = sum(1 for ln in lines if _is_citation_line(ln))
    if cites >= 4 and cites / n >= 0.4:
        return "references"
    gloss = sum(1 for ln in lines if _GLOSSARY_LINE.match(ln))
    if gloss >= 5 and gloss / n >= 0.4:
        return "glossary"
    return None
