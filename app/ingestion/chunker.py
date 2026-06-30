from __future__ import annotations

import hashlib
import logging
import math
import re
import uuid
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterable, Sequence

from app.core.models import CanonicalDocument, CanonicalSection

logger = logging.getLogger(__name__)

_NAMESPACE = uuid.UUID("6f2a1d3e-8b4c-4a9f-9e7d-2c5b1a0f3e64")

_CHARS_PER_TOKEN = 4

_MAX_HEADING_WORDS = 12


@dataclass(frozen=True)
class ChunkingConfig:

    child_target_tokens: int = 400
    child_max_tokens: int = 512
    child_min_tokens: int = 120
    child_overlap_tokens: int = 60
    parent_target_tokens: int = 1800
    parent_max_tokens: int = 2400
    encoding_name: str = "cl100k_base"


_BASE = ChunkingConfig()

_PRESETS: dict[str, ChunkingConfig] = {
    "pdf": ChunkingConfig(
        child_target_tokens=450, child_max_tokens=560, child_overlap_tokens=60,
        parent_target_tokens=2000, parent_max_tokens=2600,
    ),
    "manual": ChunkingConfig(
        child_target_tokens=450, child_max_tokens=560, child_overlap_tokens=60,
        parent_target_tokens=2000, parent_max_tokens=2600,
    ),
    "research_paper": ChunkingConfig(
        child_target_tokens=480, child_max_tokens=560, child_overlap_tokens=48,
        parent_target_tokens=2000, parent_max_tokens=2600,
    ),
    "research_papers": ChunkingConfig(
        child_target_tokens=480, child_max_tokens=560, child_overlap_tokens=48,
        parent_target_tokens=2000, parent_max_tokens=2600,
    ),
    "policy": ChunkingConfig(
        child_target_tokens=400, child_max_tokens=512, child_overlap_tokens=60,
        parent_target_tokens=1800, parent_max_tokens=2400,
    ),
    "policy_brief": ChunkingConfig(
        child_target_tokens=400, child_max_tokens=512, child_overlap_tokens=60,
        parent_target_tokens=1800, parent_max_tokens=2400,
    ),
    "report": ChunkingConfig(
        child_target_tokens=420, child_max_tokens=540, child_overlap_tokens=60,
        parent_target_tokens=1900, parent_max_tokens=2500,
    ),
    "article": ChunkingConfig(
        child_target_tokens=380, child_max_tokens=480, child_overlap_tokens=40,
        parent_target_tokens=1600, parent_max_tokens=2200,
    ),
    "small_pdf": ChunkingConfig(
        child_target_tokens=400, child_max_tokens=512, child_overlap_tokens=50,
        parent_target_tokens=100_000, parent_max_tokens=100_000,
    ),
}

for _bundle in (
    "news", "feature_articles", "events", "press_release", "videos",
    "infographics", "services", "people", "page", "completed_projects",
    "ongoing_projects",
):
    _PRESETS.setdefault(_bundle, _PRESETS["article"])

# PDFs attached to Drupal nodes chunk like any other PDF.
_PRESETS.setdefault("pdf_attachment", _PRESETS["pdf"])


def config_for(key: str | None) -> ChunkingConfig:
    if not key:
        return _BASE
    return _PRESETS.get(key.strip().lower(), _BASE)


@dataclass
class DocumentMeta:

    document_id: str
    source_type: str
    title: str | None = None
    source_url: str | None = None
    file_url: str | None = None
    pdf_id: str | None = None
    pdf_path: str | None = None
    article_uuid: str | None = None
    linked_pdf_id: str | None = None
    linked_article_uuid: str | None = None
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    authors: list[str] = field(default_factory=list)
    language: str | None = "en"
    tenant_id: str | None = None
    acl: list[str] = field(default_factory=list)
    doc_version: int = 1
    is_current: bool = True
    published_at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:

    chunk_id: str
    text: str
    is_parent: bool
    meta: DocumentMeta
    section_heading: str | None = None
    section_type: str | None = None
    parent_chunk_id: str | None = None
    chunk_index: int | None = None
    page_number: int | None = None
    page_range: tuple[int, int] | None = None
    token_count: int = 0
    content_hash: str = ""
    has_table: bool = False
    table_markdown: str = ""

    def to_payload(self) -> dict[str, Any]:
        m = self.meta
        payload: dict[str, Any] = {
            "chunk_id": self.chunk_id,
            "document_id": m.document_id,
            "is_parent": self.is_parent,
            "source_type": m.source_type,
            "title": m.title,
            "section_heading": self.section_heading,
            "section_type": self.section_type,
            "chunk_text": self.text,
            "content_hash": self.content_hash,
            "token_count": self.token_count,
            "has_table": self.has_table or None,
            "table_markdown": self.table_markdown,
            "doc_version": m.doc_version,
            "is_current": m.is_current,
            "tenant_id": m.tenant_id,
            "acl": m.acl,
            "tags": m.tags,
            "categories": m.categories,
            "authors": m.authors,
            "language": m.language,
            "source_url": m.source_url,
            "file_url": m.file_url,
            "published_at": m.published_at,
            "pdf_id": m.pdf_id,
            "pdf_path": m.pdf_path,
            "article_uuid": m.article_uuid,
            "linked_pdf_id": m.linked_pdf_id,
            "linked_article_uuid": m.linked_article_uuid,
        }
        if not self.is_parent:
            payload["parent_chunk_id"] = self.parent_chunk_id
            payload["chunk_index"] = self.chunk_index
            payload["page_number"] = self.page_number
        if self.page_range is not None:
            payload["page_range"] = list(self.page_range)
        payload.update(m.extra)
        return {k: v for k, v in payload.items() if v not in (None, "", [])}


class _Encoder:

    def __init__(self, name: str) -> None:
        self._enc = None
        try:
            import tiktoken

            self._enc = tiktoken.get_encoding(name)
        except Exception:  # pragma: no cover - offline / missing model
            logger.warning(
                "tiktoken encoding %r unavailable; falling back to a "
                "~%d-chars/token heuristic for chunk sizing.",
                name, _CHARS_PER_TOKEN,
            )

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._enc is not None:
            return len(self._enc.encode(text))
        return max(1, math.ceil(len(text) / _CHARS_PER_TOKEN))

    def split_to_token_limit(self, text: str, max_tokens: int) -> list[str]:
        if self._enc is not None:
            ids = self._enc.encode(text)
            return [
                self._enc.decode(ids[i : i + max_tokens])
                for i in range(0, len(ids), max_tokens)
            ]
        size = max(1, max_tokens * _CHARS_PER_TOKEN)
        return [text[i : i + size] for i in range(0, len(text), size)]

    def tail(self, text: str, n: int) -> str:
        if n <= 0 or not text:
            return ""
        if self._enc is not None:
            ids = self._enc.encode(text)
            return self._enc.decode(ids[-n:]) if len(ids) > n else text
        size = n * _CHARS_PER_TOKEN
        return text[-size:] if len(text) > size else text


@lru_cache(maxsize=4)
def _get_encoder(name: str) -> _Encoder:
    return _Encoder(name)


@dataclass
class _Block:
    kind: str
    text: str
    level: int
    page: int | None


@dataclass
class _Section:
    heading: str | None
    level: int
    blocks: list[_Block] = field(default_factory=list)


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


def _line_heading_level(line: str, *, at_block_start: bool) -> int | None:
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


def _blocks_from_text(text: str, page: int | None) -> list[_Block]:
    if not text or not text.strip():
        return []

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[_Block] = []
    buf: list[str] = []

    def flush_text() -> None:
        joined = "\n".join(buf).strip()
        buf.clear()
        if joined:
            blocks.append(_Block("text", joined, 0, page))

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
            blocks.append(_Block("code", "\n".join(code).strip(), 0, page))
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
            blocks.append(_Block("table", "\n".join(tbl).strip(), 0, page))
            continue

        level = _line_heading_level(stripped, at_block_start=not buf)
        if level is not None:
            flush_text()
            blocks.append(_Block("heading", _clean_heading(stripped), level, page))
            i += 1
            continue

        buf.append(line)
        i += 1

    flush_text()
    return blocks


def _assemble_sections(blocks: Iterable[_Block]) -> list[_Section]:
    sections: list[_Section] = []
    current = _Section(heading=None, level=0)

    for block in blocks:
        if block.kind == "heading":
            if not current.blocks:
                if current.heading:
                    current.heading = f"{current.heading} — {block.text}"
                else:
                    current.heading, current.level = block.text, block.level
            else:
                sections.append(current)
                current = _Section(heading=block.text, level=block.level)
        else:
            current.blocks.append(block)

    if current.heading or current.blocks:
        sections.append(current)
    return sections


def _heading_block(text: str) -> _Block:
    return _Block("text", text, 0, None)


def _join_blocks(blocks: Sequence[_Block]) -> str:
    return "\n\n".join(b.text for b in blocks if b.text).strip()


def _section_plain_text(section: _Section) -> str:
    body = _join_blocks(section.blocks)
    if section.heading and body:
        return f"{section.heading}\n\n{body}"
    return section.heading or body


def _page_range(blocks: Sequence[_Block]) -> tuple[int, int] | None:
    pages = [b.page for b in blocks if b.page is not None]
    return (min(pages), max(pages)) if pages else None


def _table_markdown(blocks: Sequence[_Block]) -> str:
    """Verbatim text of any table blocks in this window, kept separately so
    retrieval can surface the table without re-deriving it from chunk_text."""
    return "\n\n".join(b.text for b in blocks if b.kind == "table" and b.text.strip())


def _split_text_recursive(
    text: str, max_tokens: int, enc: _Encoder, seps: tuple[str, ...] = ("\n\n", "\n", ". ", " ")
) -> list[str]:
    if enc.count(text) <= max_tokens:
        return [text]
    for i, sep in enumerate(seps):
        if sep and sep in text.strip():
            out: list[str] = []
            cur = ""
            for piece in text.split(sep):
                cand = piece if not cur else f"{cur}{sep}{piece}"
                if enc.count(cand) <= max_tokens:
                    cur = cand
                    continue
                if cur:
                    out.append(cur)
                    cur = ""
                if enc.count(piece) > max_tokens:
                    out.extend(_split_text_recursive(piece, max_tokens, enc, seps[i + 1 :]))
                else:
                    cur = piece
            if cur:
                out.append(cur)
            return out
    return enc.split_to_token_limit(text, max_tokens)


def _expand_atoms(
    blocks: Sequence[_Block], *, soft_cap: int, hard_cap: int, enc: _Encoder
) -> list[_Block]:
    out: list[_Block] = []
    for block in blocks:
        cap = hard_cap if block.kind in ("code", "table") else soft_cap
        if enc.count(block.text) <= cap:
            out.append(block)
            continue
        for piece in _split_text_recursive(block.text, cap, enc):
            out.append(_Block(block.kind, piece, block.level, block.page))
    return out


def _pack(
    blocks: Sequence[_Block], *, target: int, max_tokens: int, min_fill: int, enc: _Encoder
) -> list[list[_Block]]:
    atoms = _expand_atoms(blocks, soft_cap=target, hard_cap=max_tokens, enc=enc)
    windows: list[list[_Block]] = []
    cur: list[_Block] = []
    cur_tokens = 0

    for atom in atoms:
        atom_tokens = enc.count(atom.text)
        if cur and (
            (cur_tokens + atom_tokens > target and cur_tokens >= min_fill)
            or cur_tokens + atom_tokens > max_tokens
        ):
            windows.append(cur)
            cur, cur_tokens = [], 0
        cur.append(atom)
        cur_tokens += atom_tokens

    if cur:
        windows.append(cur)
    return windows


def _coalesce_windows(
    windows: list[list[_Block]], min_tokens: int, max_tokens: int, enc: _Encoder
) -> list[list[_Block]]:
    sizes = [enc.count(_join_blocks(w)) for w in windows]
    i = 0
    while i < len(windows):
        if len(windows) == 1 or sizes[i] >= min_tokens:
            i += 1
            continue
        candidates = sorted(
            (sizes[i] + sizes[j] > max_tokens, sizes[i] + sizes[j], j)
            for j in (i - 1, i + 1)
            if 0 <= j < len(windows)
        )
        j = candidates[0][2]
        lo, hi = sorted((i, j))
        windows[lo] = windows[lo] + windows[hi]
        sizes[lo] = enc.count(_join_blocks(windows[lo]))
        del windows[hi], sizes[hi]
        i = 0
    return windows


# Sentence boundary: whitespace after .!? and before an opening capital / "(".
# Lower-case follow (e.g. "et. al,") is intentionally not a boundary.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def _overlap_carry(prev: str, overlap: int, enc: _Encoder) -> str:
    """Last ~overlap tokens of prev, advanced to the next sentence boundary so the
    carried context — and the child it prefixes — starts on a whole sentence."""
    carry = enc.tail(prev, overlap).strip()
    if not carry:
        return ""
    m = _SENTENCE_BOUNDARY.search(carry)
    return carry[m.end():] if m else carry


def _apply_overlap(texts: list[str], overlap: int, enc: _Encoder) -> list[str]:
    if overlap <= 0 or len(texts) < 2:
        return texts
    out = [texts[0]]
    for prev, text in zip(texts, texts[1:]):
        carry = _overlap_carry(prev, overlap, enc)
        out.append(f"{carry} {text}".strip() if carry else text)
    return out


def _merge_small_sections(
    sections: list[_Section], min_tokens: int, enc: _Encoder
) -> list[_Section]:
    merged: list[_Section] = []
    for sec in sections:
        if merged and enc.count(_section_plain_text(sec)) < min_tokens:
            prev = merged[-1]
            if sec.heading:
                prev.blocks.append(_heading_block(sec.heading))
            prev.blocks.extend(sec.blocks)
        else:
            merged.append(sec)

    if len(merged) >= 2 and enc.count(_section_plain_text(merged[0])) < min_tokens:
        first = merged.pop(0)
        lead = ([_heading_block(first.heading)] if first.heading else []) + first.blocks
        merged[0].blocks = lead + merged[0].blocks
    return merged


def _uuid(meta: DocumentMeta, suffix: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, f"{meta.document_id}|v{meta.doc_version}|{suffix}"))


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parent_text(heading: str | None, blocks: Sequence[_Block], part: int) -> str:
    body = _join_blocks(blocks)
    if not heading:
        return body
    prefix = heading if part == 0 else f"{heading} (cont.)"
    return f"{prefix}\n\n{body}" if body else prefix


# --- non-substantive section detection ------------------------------------- #
# Tables of contents, glossaries and bibliographies extract cleanly but pollute
# retrieval. They are flagged by their line *shape* (extraction routinely garbles
# their headings, so content is more reliable) so search can exclude them.

_DOT_LEADER = re.compile(r"\.{4,}\s*\d*\s*$")          # "Conclusions ........ 44"
_URL_RE = re.compile(r"https?://")
# A standalone citation year — "(2020)", "(2020a)". Inline prose citations like
# "(Hall, Spencer & Kumar, 2020)" don't match: the paren opens on a name, not a digit.
_CITE_YEAR = re.compile(r"\(\d{4}[a-z]?\)")
_GLOSSARY_LINE = re.compile(r"^[A-Z][A-Za-z0-9/.\-]{0,7}\s+[–\-]\s+\S")


def _is_citation_line(line: str) -> bool:
    return bool(_URL_RE.search(line) or _CITE_YEAR.search(line)) or "Retrieved from" in line


def _classify_section(text: str) -> str | None:
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


def _build_chunks(
    sections: Sequence[_Section], meta: DocumentMeta, config: ChunkingConfig, enc: _Encoder
) -> list[Chunk]:
    chunks: list[Chunk] = []
    child_index = 0

    for section_idx, section in enumerate(sections):
        heading = section.heading
        body = section.blocks
        heading_tokens = enc.count(heading) if heading else 0
        body_tokens = sum(enc.count(b.text) for b in body)

        if body_tokens + heading_tokens <= config.parent_max_tokens:
            parent_windows = [list(body)]
        else:
            parent_windows = _pack(
                body, target=config.parent_target_tokens,
                max_tokens=config.parent_max_tokens,
                min_fill=config.child_min_tokens, enc=enc,
            )
            parent_windows = _coalesce_windows(
                parent_windows, config.child_min_tokens, config.parent_max_tokens, enc
            )

        for part, parent_blocks in enumerate(parent_windows):
            parent_id = _uuid(meta, f"parent|{section_idx}.{part}")
            ptext = _parent_text(heading, parent_blocks, part)
            if not ptext.strip():
                continue

            child_windows = _pack(
                parent_blocks, target=config.child_target_tokens,
                max_tokens=config.child_max_tokens,
                min_fill=config.child_min_tokens, enc=enc,
            )
            child_windows = _coalesce_windows(
                child_windows, config.child_min_tokens, config.child_max_tokens, enc
            )
            texts = _apply_overlap(
                [_join_blocks(w) for w in child_windows], config.child_overlap_tokens, enc
            )
            pairs = [(w, t) for w, t in zip(child_windows, texts) if t.strip()]
            if not pairs:
                continue

            # A parent with a single child is a near-duplicate of it: skip the
            # parent and let the child stand alone (context falls back to child
            # text when there is no parent).
            emit_parent = len(pairs) > 1
            if emit_parent:
                parent_tables = _table_markdown(parent_blocks)
                chunks.append(
                    Chunk(
                        chunk_id=parent_id, text=ptext, is_parent=True, meta=meta,
                        section_heading=heading, section_type=_classify_section(ptext),
                        page_range=_page_range(parent_blocks),
                        token_count=enc.count(ptext), content_hash=_hash(ptext),
                        has_table=bool(parent_tables), table_markdown=parent_tables,
                    )
                )

            for window, ctext in pairs:
                pages = _page_range(window)
                child_tables = _table_markdown(window)
                chunks.append(
                    Chunk(
                        chunk_id=_uuid(meta, f"child|{child_index}"),
                        text=ctext, is_parent=False, meta=meta,
                        section_heading=heading, section_type=_classify_section(ctext),
                        parent_chunk_id=parent_id if emit_parent else None,
                        chunk_index=child_index,
                        page_number=pages[0] if pages else None,
                        page_range=pages, token_count=enc.count(ctext),
                        content_hash=_hash(ctext),
                        has_table=bool(child_tables), table_markdown=child_tables,
                    )
                )
                child_index += 1

    return chunks


def chunk_pages(
    pages: Sequence[tuple[int | None, str]],
    meta: DocumentMeta,
    *,
    config: ChunkingConfig | None = None,
) -> list[Chunk]:
    config = config or config_for(meta.source_type)
    enc = _get_encoder(config.encoding_name)

    blocks: list[_Block] = []
    for page_number, text in pages:
        blocks.extend(_blocks_from_text(text, page_number))

    sections = _assemble_sections(blocks)
    sections = _merge_small_sections(sections, config.child_min_tokens, enc)
    return _build_chunks(sections, meta, config, enc)


def chunk_document(
    text: str, meta: DocumentMeta, *, config: ChunkingConfig | None = None
) -> list[Chunk]:
    return chunk_pages([(None, text)], meta, config=config)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "document"


def _meta_from_canonical(doc: CanonicalDocument) -> DocumentMeta:
    return DocumentMeta(
        document_id=doc.document_id,
        source_type=doc.source_type,
        title=doc.title,
        source_url=doc.source_url,
        file_url=doc.file_url,
        pdf_id=doc.pdf_id,
        pdf_path=doc.pdf_path,
        article_uuid=doc.article_uuid,
        linked_pdf_id=doc.linked_pdf_id,
        linked_article_uuid=doc.linked_article_uuid,
        tags=list(doc.tags),
        categories=list(doc.categories),
        authors=list(doc.authors),
        language=doc.language,
        tenant_id=doc.tenant_id,
        acl=list(doc.acl),
        doc_version=doc.doc_version,
        is_current=doc.is_current,
        published_at=doc.published_at,
        extra=dict(doc.extra),
    )


def _canonical_page_text(section: CanonicalSection) -> str:
    if section.heading and section.text:
        return f"{section.heading}\n\n{section.text}"
    return section.heading or section.text


def chunk_canonical(
    doc: CanonicalDocument,
    *,
    config: ChunkingConfig | None = None,
    small_doc_pages: int = 10,
) -> list[Chunk]:
    meta = _meta_from_canonical(doc)
    paginated = doc.is_paginated

    if config is None:
        if paginated:
            n_pages = sum(1 for s in doc.sections if s.page_start is not None)
            config = config_for("small_pdf" if n_pages <= small_doc_pages else doc.source_type)
        else:
            config = config_for(doc.extra.get("bundle") or doc.source_type)

    if paginated:
        pages = [
            (s.page_start, _canonical_page_text(s))
            for s in doc.sections
            if _canonical_page_text(s).strip()
        ]
        return chunk_pages(pages, meta, config=config)
    return chunk_document(doc.full_text(), meta, config=config)


def chunk_pdf(
    result: "ExtractionResult",  # noqa: F821 - extractors.pdf_extractor.ExtractionResult
    *,
    document_id: str | None = None,
    config: ChunkingConfig | None = None,
    small_doc_pages: int = 10,
    **meta_overrides: Any,
) -> list[Chunk]:
    from app.ingestion.canonical import from_pdf

    source_type = meta_overrides.pop("source_type", "pdf")
    doc = from_pdf(result, document_id=document_id, source_type=source_type, **meta_overrides)
    return chunk_canonical(doc, config=config, small_doc_pages=small_doc_pages)


def chunk_drupal_record(
    record: "DrupalRecord",  # noqa: F821 - extractors.drupal_extractor.DrupalRecord
    *,
    config: ChunkingConfig | None = None,
) -> list[Chunk]:
    from app.ingestion.canonical import from_drupal_record

    return chunk_canonical(from_drupal_record(record), config=config)


def _main(argv: list[str] | None = None) -> int:
    import argparse
    import sys
    from pathlib import Path

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Inspect chunking of a file.")
    parser.add_argument("path", help="A .txt/.md file, or a .pdf to extract+chunk.")
    parser.add_argument("-n", "--show", type=int, default=3, help="Children to print (default: 3).")
    parser.add_argument("--full", action="store_true", help="Print full chunk text.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    path = Path(args.path)
    if path.suffix.lower() == ".pdf":
        from app.ingestion.extractors.pdf_extractor import extract_pdf

        chunks = chunk_pdf(extract_pdf(path.read_bytes(), path.name))
    else:
        meta = DocumentMeta(document_id=_slugify(path.stem), source_type="pdf", title=path.name)
        chunks = chunk_document(path.read_text(encoding="utf-8", errors="ignore"), meta)

    parents = [c for c in chunks if c.is_parent]
    children = [c for c in chunks if not c.is_parent]
    print(f"{path.name}: {len(parents)} parents, {len(children)} children")
    if children:
        sizes = [c.token_count for c in children]
        print(f"  child tokens: min={min(sizes)} max={max(sizes)} avg={sum(sizes) // len(sizes)}")
    for child in children[: args.show]:
        print(f"\n[child {child.chunk_index}] {child.token_count} tok "
              f"· section={child.section_heading!r} · parent={child.parent_chunk_id}")
        text = child.text if args.full else child.text[:280] + ("…" if len(child.text) > 280 else "")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
