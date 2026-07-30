"""The two-block answer structure.

Grounded answers come back wrapped in the ``<website_answer>`` /
``<pdf_answer>`` tags that :mod:`app.generation.prompts` demands, so the
frontend can style website-sourced and PDF-sourced content as distinct blocks.
This module is the only reader of that structure: the pipeline strips the tags
before the verification passes (which reason about claims, not presentation),
and the frontend parses the same sections out of the answer it renders.

Parsing stays tolerant. The tags come from a model, not from code, and a stream
can be cut mid-tag — so a malformed or absent wrapper degrades to plain text
rather than losing the answer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.generation.prompts import PDF_TAG, WEBSITE_TAG

WEBSITE = "website"
PDF = "pdf"
# Text outside any block: a refusal, a chit-chat reply, a scoped summary, or the
# deterministic catalog prefix that rides above a combined answer.
PLAIN = "plain"

# A block body: to its matching close tag, or to the end of a truncated answer.
_BLOCK = re.compile(
    rf"<({WEBSITE_TAG}|{PDF_TAG})\s*>(.*?)(?:</\1\s*>|\Z)",
    re.DOTALL | re.IGNORECASE,
)
# Stray wrappers left over after the blocks are consumed (an unpaired close tag,
# a nested repeat) are presentation debris — never shown, never verified.
_ANY_TAG = re.compile(rf"</?(?:{WEBSITE_TAG}|{PDF_TAG})\s*>", re.IGNORECASE)


@dataclass(frozen=True)
class Section:
    kind: str  # WEBSITE, PDF, or PLAIN
    text: str


def _clean(text: str) -> str:
    """Tag-free text with the blank-line runs left behind by removal collapsed."""
    return re.sub(r"\n{3,}", "\n\n", _ANY_TAG.sub("", text)).strip()


def strip_tags(answer: str) -> str:
    """The answer without its block wrappers, for the faithfulness and numeric
    checks — tag text is presentation, not a claim to verify."""
    return _clean(answer)


def split_sections(answer: str) -> list[Section]:
    """Parse an answer into the sections to render, in display order.

    Website content always precedes PDF content, whichever order the model
    emitted the blocks in, and repeated blocks of one kind merge into a single
    section. Untagged text keeps its position relative to the blocks, so the
    catalog prefix stays on top and trailing remarks stay at the bottom.
    Sections that clean up to nothing are dropped, so an empty block the model
    emitted against instructions never reaches the frontend as a bare
    container.
    """
    leading: list[str] = []
    trailing: list[str] = []
    grouped: dict[str, list[str]] = {WEBSITE: [], PDF: []}
    cursor = 0
    seen_block = False

    for match in _BLOCK.finditer(answer):
        (trailing if seen_block else leading).append(answer[cursor : match.start()])
        kind = WEBSITE if match.group(1).lower() == WEBSITE_TAG else PDF
        grouped[kind].append(match.group(2))
        cursor = match.end()
        seen_block = True
    (trailing if seen_block else leading).append(answer[cursor:])

    sections = []
    for kind, parts in (
        (PLAIN, leading),
        (WEBSITE, grouped[WEBSITE]),
        (PDF, grouped[PDF]),
        (PLAIN, trailing),
    ):
        text = _clean("\n\n".join(parts))
        if text:
            sections.append(Section(kind, text))
    return sections
