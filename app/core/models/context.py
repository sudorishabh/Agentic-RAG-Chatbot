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
