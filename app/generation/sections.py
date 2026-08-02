"""The two-block answer structure.

Answers grounded in a mixed context come back wrapped in the ``<website_answer>``
/ ``<pdf_answer>`` tags that :mod:`app.generation.prompts` demands, so the
frontend can style website-sourced and PDF-sourced content as distinct blocks.
A single-kind context is prompted for one untagged answer instead, and any block
the model emits against that is demoted here — the split only means something
when there are two kinds of source to divide.

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

from app.generation.prompts import PDF_LABEL, PDF_TAG, WEBSITE_TAG

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
# The bold lead opening a PDF block. Read only when the block is demoted: the
# label it carries is a caption for a supplement, and there is nothing to
# supplement. A trailing colon lands inside or outside the bold depending on the
# model, so both are matched.
_PDF_LEAD_LINE = re.compile(
    rf"^\s*\*\*\s*{re.escape(PDF_LABEL)}\s*:?\s*\*\*\s*:?\s*(?:\r?\n|$)",
    re.IGNORECASE,
)


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

    A PDF block with no website block beside it is demoted to plain prose: the
    split exists to set a supplement apart from the answer it supplements, and
    with nothing above it the block *is* the answer. Left as a PDF section it
    would render as a captioned aside wrapped around the whole reply.
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

    website_text = _clean("\n\n".join(grouped[WEBSITE]))
    pdf_text = _clean("\n\n".join(grouped[PDF]))
    pdf_kind = PDF
    if not website_text:
        # Standing alone, the PDF block is the answer: demote it, and drop the
        # lead-in that only read as a label under the caption it no longer gets.
        pdf_kind = PLAIN
        pdf_text = _PDF_LEAD_LINE.sub("", pdf_text).strip()

    sections = []
    for kind, text in (
        (PLAIN, _clean("\n\n".join(leading))),
        (WEBSITE, website_text),
        (pdf_kind, pdf_text),
        (PLAIN, _clean("\n\n".join(trailing))),
    ):
        if text:
            sections.append(Section(kind, text))
    return sections
