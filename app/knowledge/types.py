"""Knowledge-layer value types.

A ``Mention`` is a *sighting*: this span of this chunk looks like a name of this
type. It deliberately carries no ``entity_id``. Deciding which canonical entity
a mention denotes is resolution's job, a separate phase with its own audit
trail, and keeping identity out of this type is what stops extraction from
quietly inventing it.
"""
from __future__ import annotations

from dataclasses import dataclass

# The closed entity vocabulary. Matches app.knowledge.graph.schema.ENTITY_LABELS
# (upper-cased); a type outside this set is dropped rather than stored, so no
# extractor — least of all a model — can widen the vocabulary at runtime.
ENTITY_TYPES: tuple[str, ...] = ("PERSON", "ORGANIZATION", "PROJECT")

# How a mention was found, cheapest and most trustworthy first. The order is
# meaningful: when two methods find the same span, the earlier one wins.
EXTRACTION_METHODS: tuple[str, ...] = (
    "cms_field",   # a name this document's own CMS metadata asserts
    "identifier",  # a coded identifier matched by an exact pattern
    "gazetteer",   # a name known corpus-wide from CMS metadata
    "pattern",     # a deterministic textual pattern
    "llm",         # model-proposed, span-verified; last resort, gated off
)


@dataclass(frozen=True)
class Mention:
    """One occurrence of a name in one chunk.

    Offsets are **chunk-relative** and index into ``chunk.text`` as stored.
    Document-relative offsets would not survive the corpus: a website body is
    one blob while a PDF is paginated sections, so there is no single text a
    document-level offset could index into. Chunk-relative offsets are also
    verifiable — ``surface_text`` must equal ``chunk_text[start:end]``, which is
    the check that keeps a model from inventing a span.
    """

    chunk_id: str
    document_id: str
    start_offset: int
    end_offset: int
    surface_text: str
    normalized_text: str
    entity_type: str
    extraction_method: str
    extractor_version: str
    confidence: float

    def __post_init__(self) -> None:
        if self.entity_type not in ENTITY_TYPES:
            raise ValueError(f"unknown entity_type: {self.entity_type!r}")
        if self.extraction_method not in EXTRACTION_METHODS:
            raise ValueError(f"unknown extraction_method: {self.extraction_method!r}")
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise ValueError(
                f"invalid span [{self.start_offset}, {self.end_offset})"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence out of range: {self.confidence}")

    @property
    def span(self) -> tuple[int, int]:
        return (self.start_offset, self.end_offset)

    def verify_against(self, chunk_text: str) -> bool:
        """Whether this mention's span really holds its surface text.

        Every extractor's output passes through here before it is stored. For
        the deterministic passes it is a cheap assertion; for the model pass it
        is the entire defence — offsets a model reports are never trusted.
        """
        return chunk_text[self.start_offset : self.end_offset] == self.surface_text
