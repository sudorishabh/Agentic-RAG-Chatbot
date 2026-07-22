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
_NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s+(.+)$")
_LABELED = re.compile(
    r"^(section|chapter|article|clause|appendix|annex|part)\b", re.IGNORECASE
)
_TERMINAL = (".", "!", "?", ",", ";", ":")

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

    if _is_junk_heading(s):
        return None

    words = s.split()
    if len(words) > _MAX_HEADING_WORDS:
        return None

    m = _NUMBERED.match(s)
    if m and not s.endswith(_TERMINAL) and _plausible_section_number(m.group(1)):
        title = m.group(2).strip()
        if title and title[0].isalpha() and len(title.split()) <= 8 and not _looks_like_prose(title):
            return min(m.group(1).count(".") + 1, 6)

    if _LABELED.match(s) and not s.endswith(_TERMINAL) and not _looks_like_prose(s):
        return 2

    if not at_block_start:
        return None

    letters = [c for c in s if c.isalpha()]
    if letters and len(words) <= 8 and sum(c.isupper() for c in letters) / len(letters) > 0.85:
        return 2

    if (
        len(words) <= 8
        and not s.endswith(_TERMINAL)
        and not _looks_like_prose(s)
        and sum(w[:1].isupper() for w in words if w[:1].isalpha()) >= max(1, len(words) - 1)
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
    sections: list[Section] = []
    current = Section(heading=None, level=0)

    for block in blocks:
        if block.kind == "heading":
            if not current.blocks:
                if current.heading:
                    current.heading = f"{current.heading} — {block.text}"
                else:
                    current.heading, current.level = block.text, block.level
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
