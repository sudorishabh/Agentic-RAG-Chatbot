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
