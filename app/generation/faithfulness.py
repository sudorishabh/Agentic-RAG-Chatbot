"""Post-generation faithfulness verification (§10.6.4) + marker hygiene (§8.5).

Two guards applied after generation:

1. **Marker validation** (always, free) — strip any ``[n]`` marker the LLM emitted
   that does not map to a real context block, so a citation marker never dangles.
2. **Faithfulness check** (optional, ``faithfulness_check``) — a cheap LLM/NLI pass
   that confirms every claim is entailed by the cited context; surfaces the
   unsupported claims so the orchestrator can regenerate once before answering.

This module only *judges*; regeneration is driven by the orchestrator so this
stays free of a dependency on the generation flow.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.retrieval.context_builder import ContextBlock

logger = logging.getLogger(__name__)

_MARKER = re.compile(r"\[(\d+)\]")


def extract_markers(text: str) -> set[int]:
    return {int(m) for m in _MARKER.findall(text)}


def validate_markers(answer: str, n_blocks: int) -> str:
    """Drop citation markers that point past the real blocks (§8.5)."""

    def _keep(match: re.Match) -> str:
        n = int(match.group(1))
        return match.group(0) if 1 <= n <= n_blocks else ""

    return _MARKER.sub(_keep, answer).replace("  ", " ").strip()


@dataclass
class FaithfulnessReport:
    faithful: bool = True
    unsupported: list[str] = field(default_factory=list)

    def correction_note(self) -> str:
        joined = "; ".join(self.unsupported) or "some claims were not supported"
        return (
            "A prior draft made claims the context does not support "
            f"({joined}). Rewrite using ONLY the numbered context, dropping or "
            "qualifying any unsupported claim, and keep [n] citations."
        )


class _Verdict(BaseModel):
    faithful: bool = Field(description="True if every claim is supported by the context.")
    unsupported: list[str] = Field(default_factory=list, description="Unsupported claims.")


def verify(answer: str, blocks: "list[ContextBlock]") -> FaithfulnessReport:
    """LLM entailment check that the answer's claims are grounded in the blocks."""
    from app.generation.llm_client import get_structured_llm
    from app.generation.prompts import format_context_blocks

    if not answer.strip() or not blocks:
        return FaithfulnessReport(faithful=True)
    try:
        model = get_structured_llm().with_structured_output(_Verdict)
        verdict: _Verdict = model.invoke(
            [
                (
                    "system",
                    "You are a strict fact-checker. Decide whether EVERY claim in the "
                    "answer is directly supported by the numbered context. List any "
                    "claim that is not supported. Ignore citation markers themselves.",
                ),
                (
                    "human",
                    f"Numbered context:\n{format_context_blocks(blocks)}\n\n"
                    f"Answer:\n{answer}",
                ),
            ]
        )
    except Exception:
        logger.warning("Faithfulness check failed; assuming faithful.", exc_info=True)
        return FaithfulnessReport(faithful=True)
    return FaithfulnessReport(faithful=verdict.faithful, unsupported=verdict.unsupported)
