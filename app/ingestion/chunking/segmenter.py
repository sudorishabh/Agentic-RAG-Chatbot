"""Structure-aware segmentation: a small markdown/heading parser that turns raw
page text into typed blocks (text/code/table/heading), then assembles those
into sections a heading owns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

_MAX_HEADING_WORDS = 12


@dataclass
class Block:
    kind: str
    text: str
    level: int
    page: int | None


@dataclass
class Section:
    heading: str | None
    level: int
    blocks: list[Block] = field(default_factory=list)


_FENCE = re.compile(r"^(```|~~~)")
_ATX = re.compile(r"^(#{1,6})\s+(.+?)\s*#*$")
# A section number: "1", "1.", "4.1", "1.3.2". A closing paren ("1)") marks an
# enumerated list item, not a section, so it is deliberately not accepted here.
_NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")
_LABELED = re.compile(
    r"^(section|chapter|article|clause|appendix|annex|part)\b", re.IGNORECASE
)
_TERMINAL = (".", "!", "?", ",", ";", ":")

# A list marker opening the line — "i)", "iv)", "a)", "1)", "(2)". These label
# items within a section; they never introduce one.
_LIST_MARKER = re.compile(r"^\(?(?:\d{1,2}|[ivxlcdm]{1,5}|[a-z])\)", re.IGNORECASE)

# A URL is content (a footnote, a citation), never a heading. PDF footnote
# markers make "1 http://host/paper.pdf" look exactly like a numbered heading.
_URL = re.compile(r"https?://|www\.", re.IGNORECASE)

# Words that carry no capitalization signal in a Title Case heading, so they
# must not count against it. Kept separate from `_STOPWORD_END`, which is the
# broader set of words a heading cannot *end* on (it includes verbs and
# pronouns — those do signal prose mid-heading).
_TITLE_MINOR_WORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "at", "from", "as", "into", "over", "under", "per", "via", "vs", "but",
    "nor", "so", "than", "upon", "within", "between", "across",
})

_STOPWORD_END = frozenset({
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "is", "are", "was", "were", "be", "as", "at", "from", "that", "this", "which",
    "but", "nor", "so", "than", "into", "via", "per", "had", "has", "we", "it",
})
_MID_PUNCT = re.compile(r"[.,;:]\s")

# A run of >= 4 dots — a table-of-contents / list-of-figures dot leader, never a heading.
_DOT_LEADER_RUN = re.compile(r"\.{4,}")


def _looks_like_prose(s: str) -> bool:
    if _MID_PUNCT.search(s):
        return True
    tokens = s.rstrip(".,;:)]}").split()
    return bool(tokens) and tokens[-1].lower() in _STOPWORD_END


def _is_junk_heading(s: str) -> bool:
    """Reject extraction artifacts that should never be treated as a heading:
    ToC/LoF/LoT dot leaders, HTML-comment fragments, table/formula rows with a
    pipe, and OCR symbol-soup (too few letters among the non-space characters).
    """
    if _DOT_LEADER_RUN.search(s) or "|" in s:
        return True
    if s.startswith("<!--") or s.startswith("-->"):
        return True
    non_space = sum(1 for c in s if not c.isspace())
    letters = sum(1 for c in s if c.isalpha())
    return bool(non_space) and letters / non_space < 0.55


def _plausible_section_number(num: str) -> bool:
    """A real section number ("1", "4.1", "1.3.2") — not a measurement ("0.35") or
    a stray figure/page value ("250") that a numbered-heading match would swallow."""
    head = num.split(".")[0]
    return num.count(".") <= 3 and not num.startswith("0") and head.isdigit() and int(head) < 100


def _is_table_line(line: str) -> bool:
    return line.count("|") >= 2


def _clean_heading(line: str) -> str:
    m = _ATX.match(line)
    if m:
        return m.group(2).strip()
    return line.strip()


def line_heading_level(line: str, *, at_block_start: bool) -> int | None:
    s = line.strip()
    if not s:
        return None

    m = _ATX.match(s)
    if m:
        return len(m.group(1))

    # Negative signals that outrank every heuristic below. Checked after ATX so
    # an authored "## See http://host for detail" still stands as a heading.
    if _is_junk_heading(s) or _URL.search(s) or _LIST_MARKER.match(s):
        return None

    words = s.split()
    if len(words) > _MAX_HEADING_WORDS:
        return None

    m = _NUMBERED.match(s)
    if m and not s.endswith(_TERMINAL) and _plausible_section_number(m.group(1)):
        title = m.group(2).strip()
        # A numbered heading titles something ("4 Transition Pathway"); a bare
        # number opening a sentence does not ("4 way segregation centres").
        if title[:1].isupper() and len(title.split()) <= 8 and not _looks_like_prose(title):
            return min(m.group(1).count(".") + 1, 6)

    if _LABELED.match(s) and not s.endswith(_TERMINAL) and not _looks_like_prose(s):
        return 2

    if not at_block_start:
        return None

    letters = [c for c in s if c.isalpha()]
    if letters and len(words) <= 8 and sum(c.isupper() for c in letters) / len(letters) > 0.85:
        return 2

    # Title Case: every *content* word capitalised. Minor words are skipped
    # rather than counted against the line, so "Scope of the Study" qualifies
    # while ordinary prose — which capitalises only its first word — does not.
    content = [w for w in words if w.strip(".,;:()").lower() not in _TITLE_MINOR_WORDS]
    if (
        len(words) <= 8
        and content  # a line of only minor words titles nothing
        and all(w[:1].isupper() for w in content)
        and not s.endswith(_TERMINAL)
        and not _looks_like_prose(s)
    ):
        return 3

    return None


def blocks_from_text(text: str, page: int | None) -> list[Block]:
    if not text or not text.strip():
        return []

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[Block] = []
    buf: list[str] = []

    def flush_text() -> None:
        joined = "\n".join(buf).strip()
        buf.clear()
        if joined:
            blocks.append(Block("text", joined, 0, page))

    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if _FENCE.match(stripped):
            flush_text()
            fence = stripped[:3]
            code = [line]
            i += 1
            while i < n and not lines[i].strip().startswith(fence):
                code.append(lines[i])
                i += 1
            if i < n:
                code.append(lines[i])
                i += 1
            blocks.append(Block("code", "\n".join(code).strip(), 0, page))
            continue

        if not stripped:
            flush_text()
            i += 1
            continue

        if _is_table_line(line) and i + 1 < n and _is_table_line(lines[i + 1]):
            flush_text()
            tbl: list[str] = []
            while i < n and _is_table_line(lines[i]):
                tbl.append(lines[i])
                i += 1
            blocks.append(Block("table", "\n".join(tbl).strip(), 0, page))
            continue

        level = line_heading_level(stripped, at_block_start=not buf)
        if level is not None:
            flush_text()
            blocks.append(Block("heading", _clean_heading(stripped), level, page))
            i += 1
            continue

        buf.append(line)
        i += 1

    flush_text()
    return blocks


def assemble_sections(blocks: Iterable[Block]) -> list[Section]:
    """Group blocks into the sections their headings own.

    Heading detection is a heuristic, so a run of short lines — an extracted
    table column, a bare list — can arrive as consecutive heading blocks. Only
    the first titles the section; the rest are demoted to body text. Folding
    them into the heading string instead kept them out of every chunk's *text*,
    and left a section with no body at all, which packs to zero chunks and drops
    the text entirely.
    """
    sections: list[Section] = []
    current = Section(heading=None, level=0)

    for block in blocks:
        if block.kind == "heading":
            if current.heading is None and not current.blocks:
                current.heading, current.level = block.text, block.level
            elif not current.blocks:
                # Heading-classified but nothing to title: keep it as content
                # rather than trusting the classification and losing the line.
                current.blocks.append(Block("text", block.text, 0, block.page))
            else:
                sections.append(current)
                current = Section(heading=block.text, level=block.level)
        else:
            current.blocks.append(block)

    if current.heading or current.blocks:
        sections.append(current)
    return sections


def heading_block(text: str) -> Block:
    return Block("text", text, 0, None)


def join_blocks(blocks: Sequence[Block]) -> str:
    return "\n\n".join(b.text for b in blocks if b.text).strip()


def section_plain_text(section: Section) -> str:
    body = join_blocks(section.blocks)
    if section.heading and body:
        return f"{section.heading}\n\n{body}"
    return section.heading or body


def page_range(blocks: Sequence[Block]) -> tuple[int, int] | None:
    pages = [b.page for b in blocks if b.page is not None]
    return (min(pages), max(pages)) if pages else None


def table_markdown(blocks: Sequence[Block]) -> str:
    """Verbatim text of any table blocks in this window, kept separately so
    retrieval can surface the table without re-deriving it from chunk_text."""
    return "\n\n".join(b.text for b in blocks if b.kind == "table" and b.text.strip())


def merge_small_sections(
    sections: list[Section], min_tokens: int, enc
) -> list[Section]:
    merged: list[Section] = []
    for sec in sections:
        if merged and enc.count(section_plain_text(sec)) < min_tokens:
            prev = merged[-1]
            if sec.heading:
                prev.blocks.append(heading_block(sec.heading))
            prev.blocks.extend(sec.blocks)
        else:
            merged.append(sec)

    if len(merged) >= 2 and enc.count(section_plain_text(merged[0])) < min_tokens:
        first = merged.pop(0)
        lead = ([heading_block(first.heading)] if first.heading else []) + first.blocks
        merged[0].blocks = lead + merged[0].blocks
    return merged
