"""Token-aware packing: the tokenizer abstraction plus the windowing / overlap /
coalesce algorithm that turns a flat block sequence into sized chunk windows."""
from __future__ import annotations

import logging
import math
import re
from functools import lru_cache
from typing import Sequence

from app.ingestion.chunking.segmenter import Block, join_blocks

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4


class Encoder:

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
def get_encoder(name: str) -> Encoder:
    return Encoder(name)


def _split_text_recursive(
    text: str, max_tokens: int, enc: Encoder, seps: tuple[str, ...] = ("\n\n", "\n", ". ", " ")
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
    blocks: Sequence[Block], *, soft_cap: int, hard_cap: int, enc: Encoder
) -> list[Block]:
    out: list[Block] = []
    for block in blocks:
        cap = hard_cap if block.kind in ("code", "table") else soft_cap
        if enc.count(block.text) <= cap:
            out.append(block)
            continue
        for piece in _split_text_recursive(block.text, cap, enc):
            out.append(Block(block.kind, piece, block.level, block.page))
    return out


def pack(
    blocks: Sequence[Block], *, target: int, max_tokens: int, min_fill: int, enc: Encoder
) -> list[list[Block]]:
    atoms = _expand_atoms(blocks, soft_cap=target, hard_cap=max_tokens, enc=enc)
    windows: list[list[Block]] = []
    cur: list[Block] = []
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


def coalesce_windows(
    windows: list[list[Block]], min_tokens: int, max_tokens: int, enc: Encoder
) -> list[list[Block]]:
    sizes = [enc.count(join_blocks(w)) for w in windows]
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
        sizes[lo] = enc.count(join_blocks(windows[lo]))
        del windows[hi], sizes[hi]
        # Resume at the merged window, not 0: every window before `lo` is already
        # >= min_tokens and untouched by this merge, so rescanning them from the
        # start (the old O(n^2) behaviour) can never find a new merge.
        i = lo
    return windows


# Sentence boundary: whitespace after .!? and before an opening capital / "(".
# Lower-case follow (e.g. "et. al,") is intentionally not a boundary.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def overlap_carry(prev: str, overlap: int, enc: Encoder) -> str:
    """Last ~overlap tokens of prev, advanced to the next sentence boundary so the
    carried context — and the child it prefixes — starts on a whole sentence."""
    carry = enc.tail(prev, overlap).strip()
    if not carry:
        return ""
    m = _SENTENCE_BOUNDARY.search(carry)
    return carry[m.end():] if m else carry


def apply_overlap(texts: list[str], overlap: int, enc: Encoder) -> list[str]:
    if overlap <= 0 or len(texts) < 2:
        return texts
    out = [texts[0]]
    for prev, text in zip(texts, texts[1:]):
        carry = overlap_carry(prev, overlap, enc)
        out.append(f"{carry} {text}".strip() if carry else text)
    return out
