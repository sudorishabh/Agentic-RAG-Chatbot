from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextBlock:
    """One numbered passage handed to answer generation.

    The shared contract between retrieval (which produces the ordered list via
    ``context_builder.build_context``) and generation (which formats and cites
    it). Lives in the neutral core layer so generation never has to import a
    retrieval implementation module.
    """

    n: int
    text: str
    payload: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    conflict: bool = False
    also_available: list[dict[str, Any]] = field(default_factory=list)


def page_span(payload: dict[str, Any]) -> tuple[int | None, int | None]:
    """The (first, last) page the payload's text covers, or (None, None).

    One definition, because the prompt header and the citation must never
    disagree about which pages a block is standing on. ``page_range`` is
    authoritative when present — the context builder rewrites it to describe the
    text it actually admitted — and a lone ``page_number`` reads as a one-page
    span. Nothing is inferred when neither is set: an unpaginated source has no
    page, and inventing one is worse than showing none.
    """
    span = payload.get("page_range")
    if isinstance(span, (list, tuple)) and len(span) == 2:
        try:
            return int(span[0]), int(span[1])
        except (TypeError, ValueError):
            pass
    page = payload.get("page_number")
    if isinstance(page, int):
        return page, page
    return None, None
