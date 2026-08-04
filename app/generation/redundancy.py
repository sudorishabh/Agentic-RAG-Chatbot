"""Deterministic redundancy filtering for the PDF answer block.

The grounded prompt already asks the model to drop a PDF block that only
restates the website answer (see :mod:`app.generation.prompts`), but that is a
judgement call left to the model, and a model that hedges keeps the block. This
module decides it in code instead: it measures how much of the PDF text is
already stated by the website text and removes the parts that add nothing.

Everything here is pure and offline — no embeddings, no model call, no I/O — so
the same answer always filters the same way and the pass costs nothing
measurable. Token overlap is a coarser signal than a vector similarity would be,
so every rule leans the same direction: **keep when unsure**. Dropping a
sentence the reader needed is a worse failure than leaving a mild repeat on
screen.

Two measurement choices follow from that bias:

* Coverage is *asymmetric* — the share of the PDF sentence's own content words
  that the website sentence also has. Symmetric overlap (Jaccard) would score a
  short restatement against a long website paragraph as barely similar and keep
  the repeat, because the website's extra words count against the score.
* Each PDF sentence is scored against website sentences *one at a time*, never
  against the union of all of them. Pooling the website's vocabulary lets a
  genuinely new sentence look covered because its words happen to be scattered
  across unrelated website sentences.
"""
from __future__ import annotations

import re
from typing import Sequence

# Share of a PDF sentence's content words that must already appear in one
# website sentence before it counts as a restatement. High enough that a
# sentence carrying any real detail of its own survives.
DEFAULT_COVERAGE = 0.8

# Function words carry no information about *what* is being said, so they would
# inflate every comparison. Negations are deliberately absent: dropping "not"
# collapses "X supports SSO" and "X does not support SSO" onto the same tokens,
# and the filter would silently delete the contradiction rather than the repeat.
_STOPWORDS = frozenset(
    """
    a an the and or but if then than that this these those of in on at to for
    from by with as is are was were be been being am it they them their there
    here can could may might must shall should will would do does did have has
    had also more most other such only same so very just about into over under
    between each per any all both some when while which who whom whose what
    how why our your his her use used using including include includes
    """.split()
)

_CITATION = re.compile(r"\[\d+(?:\s*[,;]\s*\d+)*\]")
# A markdown link contributes its label; the URL is machinery, not content.
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
# Emphasis, code ticks, heading hashes, quote markers — styling around the words.
_MD_NOISE = re.compile(r"[*_`#>~]+")
# Words, keeping decimals ("1.2") and hyphenated compounds ("single-sign-on")
# whole so a figure or a compound term is not split into meaningless pieces.
_WORD = re.compile(r"[a-z0-9]+(?:[.\-][a-z0-9]+)*")
# Sentence boundary: terminal punctuation followed by whitespace. A bullet with
# no full stop is simply one sentence.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# Bullet or numbered list item, with the marker to strip before comparing.
_LIST_ITEM = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")
# A blank line (optionally holding whitespace) separates markdown blocks.
_BLOCK_SPLIT = re.compile(r"\n\s*\n")


def _fold(token: str) -> str:
    """Fold a trailing plural/third-person 's' so "supports" and "support for"
    read as the same claim. Deliberately the only morphology handled: anything
    heavier starts merging words that mean different things."""
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def content_tokens(text: str) -> frozenset[str]:
    """The content words of a passage, as a set: citations, markdown and
    function words removed, plurals folded. A set rather than a count because
    saying a thing twice does not make it a different claim."""
    plain = _MD_LINK.sub(r"\1", _CITATION.sub(" ", text))
    plain = _MD_NOISE.sub(" ", plain).lower()
    return frozenset(
        folded
        for word in _WORD.findall(plain)
        if (folded := _fold(word)) not in _STOPWORDS
    )


def _sentences(text: str) -> list[str]:
    return [part for part in _SENTENCE_SPLIT.split(text.strip()) if part.strip()]


def reference_sentences(website_text: str) -> list[frozenset[str]]:
    """The website answer as one token set per sentence — the yardstick a PDF
    sentence is measured against. Sentence-level so a PDF bullet can match the
    one website sentence that states it, wherever it sits in the paragraph."""
    return [tokens for s in _sentences(website_text) if (tokens := content_tokens(s))]


def coverage(tokens: frozenset[str], references: Sequence[frozenset[str]]) -> float:
    """Largest share of `tokens` that any single reference sentence also holds."""
    if not tokens:
        return 0.0
    return max(
        (len(tokens & reference) / len(tokens) for reference in references),
        default=0.0,
    )


def is_covered(
    text: str,
    references: Sequence[frozenset[str]],
    *,
    threshold: float = DEFAULT_COVERAGE,
) -> bool:
    """True when every sentence in `text` restates some reference sentence.

    All-or-nothing on purpose: a passage keeps its shape unless the whole of it
    is already on screen. Text with no measurable content (a rule, a bare
    caption) is never "covered" — it is structural, and is dropped only by
    whatever it was structuring going away.
    """
    scored = [tokens for s in _sentences(text) if (tokens := content_tokens(s))]
    if not scored:
        return False
    return all(coverage(tokens, references) >= threshold for tokens in scored)


def _list_units(lines: list[str]) -> list[list[str]]:
    """A list block grouped into runs, each starting at an item marker.

    Wrapped continuation lines join the item above them, so dropping an item
    takes the rest of its text with it instead of orphaning half a sentence. A
    lead-in line before the first marker ("Key points:") becomes its own
    non-item run and is kept as structure.
    """
    units: list[list[str]] = []
    for line in lines:
        if _LIST_ITEM.match(line) or not units:
            units.append([line])
        else:
            units[-1].append(line)
    return units


def _is_item(unit: list[str]) -> bool:
    return bool(_LIST_ITEM.match(unit[0]))


def _has_items(block: str) -> bool:
    """Whether a block is a list. Checked line by line: the item pattern is
    anchored, so searching the joined block would only ever see its first line."""
    return any(_LIST_ITEM.match(line) for line in block.splitlines())


def _filter_list(
    block: str, references: Sequence[frozenset[str]], *, threshold: float
) -> str:
    """Drop the restated items of a list, keep the rest. Emptying every item
    takes the whole block, lead-in included — a heading over nothing reads as a
    section that lost its content."""
    kept: list[list[str]] = []
    for unit in _list_units(block.splitlines()):
        if _is_item(unit):
            item = _LIST_ITEM.sub("", "\n".join(unit))
            if is_covered(item, references, threshold=threshold):
                continue
        kept.append(unit)
    if not any(_is_item(unit) for unit in kept):
        return ""
    return "\n".join(line for unit in kept for line in unit)


def filter_pdf_text(
    pdf_text: str,
    website_text: str,
    *,
    threshold: float = DEFAULT_COVERAGE,
) -> str:
    """The PDF text with everything the website answer already states removed.

    Returns "" when nothing additive survives, which is the caller's signal to
    drop the PDF block entirely.

    Filtering happens per markdown block, and within a list per item, so a
    partly-redundant list loses only the items that repeat. Prose is all-or-
    nothing: excising sentences from the middle of a paragraph leaves dangling
    references ("This also means…") pointing at text that is no longer there.
    """
    if not pdf_text.strip():
        return ""
    references = reference_sentences(website_text)
    if not references:
        # No website answer to be redundant against — every PDF sentence is the
        # only place the reader can get it.
        return pdf_text.strip()

    kept: list[str] = []
    for block in _BLOCK_SPLIT.split(pdf_text.strip()):
        if not block.strip():
            continue
        if _has_items(block):
            filtered = _filter_list(block, references, threshold=threshold)
        else:
            filtered = (
                "" if is_covered(block, references, threshold=threshold) else block
            )
        if filtered.strip():
            kept.append(filtered.strip("\n"))
    return "\n\n".join(kept)
