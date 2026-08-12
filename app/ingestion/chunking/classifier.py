"""Non-substantive section detection: tables of contents, glossaries and
bibliographies extract cleanly but pollute retrieval. They are flagged by
their line *shape* (extraction routinely garbles their headings, so content
is more reliable) so search can exclude them.

Content, not the heading, decides: a chunk filed under a "References" heading can
still be ordinary prose that bled in past a missed heading, and flagging it on the
heading alone would hide real content from every search.

Nothing is dropped here — a flagged chunk is still stored and still embedded; only
`hybrid_search.build_filter` excludes it from normal retrieval."""
from __future__ import annotations

import re

_DOT_LEADER = re.compile(r"\.{4,}\s*\d*\s*$")          # "Conclusions ........ 44"
_URL_RE = re.compile(r"https?://")
# A standalone citation year — "(2020)", "(2020a)". Inline prose citations like
# "(Hall, Spencer & Kumar, 2020)" don't match: the paren opens on a name, not a digit.
_CITE_YEAR = re.compile(r"\(\d{4}[a-z]?\)")
# A bare year in bibliographic position — "Brenkert AL and Malone EL. 2005. Modelling…",
# "…India Report, 2015, Ministry of…". The year has to be delimited by a full stop or
# comma on *both* sides, which prose carrying a year ("rose in 2015, then fell") and an
# inline citation ("(NSP, 2017)", closed by a paren) never satisfy.
_ENTRY_YEAR = re.compile(r"(?<=[.,])\s*(?:19|20)\d{2}[a-z]?\s*[.,]")
_GLOSSARY_LINE = re.compile(r"^[A-Z][A-Za-z0-9/.\-]{0,7}\s+[–\-]\s+\S")

# Citations per 100 words that marks a bibliography rather than prose carrying the odd
# reference. Density is used rather than a per-line ratio because PDF text is
# hard-wrapped: one entry spans two or three lines whose continuations ("and Other
# India Bookstore") carry no citation marker, which drags any per-line ratio below a
# usable threshold. Measured over the sample corpus, body chunks peak at 0.94 and real
# bibliographies start at 2.45, so the gate sits in that gap.
_CITE_DENSITY = 1.5


def _is_citation_line(line: str) -> bool:
    return (
        bool(_URL_RE.search(line) or _CITE_YEAR.search(line) or _ENTRY_YEAR.search(line))
        or "Retrieved from" in line
    )


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
    if cites >= 4 and 100 * cites / max(len(text.split()), 1) >= _CITE_DENSITY:
        return "references"
    gloss = sum(1 for ln in lines if _GLOSSARY_LINE.match(ln))
    if gloss >= 5 and gloss / n >= 0.4:
        return "glossary"
    return None
