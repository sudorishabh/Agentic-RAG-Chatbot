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


def citation_coverage(answer: str) -> float:
    """Deterministic: fraction of sentences (simple split; bullet/table lines
    count as sentences) carrying at least one [n] marker."""
    sentences = [
        s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", answer) if s.strip()
    ]
    if not sentences:
        return 0.0
    return sum(1 for s in sentences if _MARKER.search(s)) / len(sentences)


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


class _Claim(BaseModel):
    text: str
    citations: list[int] = Field(default_factory=list)


class _ClaimList(BaseModel):
    claims: list[_Claim] = Field(default_factory=list)


class _Support(BaseModel):
    supported: bool


_EXTRACT_SYSTEM = (
    "Split the answer into atomic factual claims for verification. One claim "
    "= one checkable statement, wording copied faithfully; keep the [n] "
    "markers cited for each claim as its citations. Skip greetings, hedges, "
    "and meta statements about the answer itself.\n"
    "Example answer: 'The programme added 1.2 GW in 2023 [1]. Adoption was "
    "led by commercial installations [1][3].'\n"
    "Example claims: text='The programme added 1.2 GW in 2023', citations=[1]; "
    "text='Adoption was led by commercial installations', citations=[1, 3]."
)

_SUPPORT_SYSTEM = (
    "Decide whether the passage supports the claim. supported=true ONLY when "
    "the passage states the claim or directly entails it — numbers, dates and "
    "names must match exactly. supported=false when the claim is absent, "
    "contradicted, or only loosely related.\n"
    "Example (true): claim 'Capacity grew 40% in 2023' vs passage "
    "'...capacity rose by 40% during 2023...'.\n"
    "Example (false): claim 'The plant opened in 2019' vs passage 'The plant "
    "was announced in 2019' — announced is not opened."
)


def _extract_claims(answer: str) -> list[_Claim]:
    from app.generation.llm_client import get_structured_llm

    result: _ClaimList = get_structured_llm().with_structured_output(_ClaimList).invoke(
        [("system", _EXTRACT_SYSTEM), ("human", f"Answer:\n{answer}")]
    )
    return [c for c in result.claims if c.text.strip()]


def _claim_supported(claim: str, evidence: str) -> bool | None:
    """One binary verdict; None on error (the claim is skipped, not flagged)."""
    from app.generation.llm_client import get_structured_llm

    try:
        verdict: _Support = get_structured_llm().with_structured_output(_Support).invoke(
            [("system", _SUPPORT_SYSTEM), ("human", f"Claim: {claim}\n\nPassage:\n{evidence}")]
        )
        return bool(verdict.supported)
    except Exception:
        logger.warning("Claim support check failed; skipping claim.", exc_info=True)
        return None


def verify(answer: str, blocks: "list[ContextBlock]") -> FaithfulnessReport:
    """Claim-level faithfulness: extract atomic claims, then one binary
    supported/unsupported verdict per claim (in parallel) against its cited
    blocks — mini is unreliable as a holistic grader but strong at scoped
    binary verdicts. Fails open to faithful at every stage."""
    from concurrent.futures import ThreadPoolExecutor

    if not answer.strip() or not blocks:
        return FaithfulnessReport(faithful=True)
    try:
        claims = _extract_claims(answer)
    except Exception:
        logger.warning("Claim extraction failed; assuming faithful.", exc_info=True)
        return FaithfulnessReport(faithful=True)
    if not claims:
        return FaithfulnessReport(faithful=True)

    by_n = {b.n: b.text for b in blocks}
    everything = "\n\n".join(b.text for b in blocks)

    def evidence(claim: _Claim) -> str:
        cited = [by_n[n] for n in claim.citations if n in by_n]
        return "\n\n".join(cited) if cited else everything

    with ThreadPoolExecutor(max_workers=4) as pool:
        verdicts = list(
            pool.map(lambda c: _claim_supported(c.text, evidence(c)), claims)
        )
    unsupported = [c.text for c, v in zip(claims, verdicts) if v is False]
    return FaithfulnessReport(faithful=not unsupported, unsupported=unsupported)


# Numbers/percents in answers, thousands separators tolerated ("1,234").
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set[str]:
    return {m.replace(",", "") for m in _NUMBER.findall(text)}


def numeric_mismatches(answer: str, blocks: "list[ContextBlock]") -> list[str]:
    """Numbers in the answer that appear in no cited block (all blocks when
    nothing is cited). Deterministic, no LLM — an observability signal, not a
    blocker; percent signs and thousands separators are normalized away to
    keep false flags low."""
    if not blocks:
        return []
    stripped = _MARKER.sub(" ", answer)  # citation markers are not claims
    claimed = _numbers(stripped)
    if not claimed:
        return []
    cited = extract_markers(answer)
    texts = [b.text for b in blocks if not cited or b.n in cited]
    available: set[str] = set()
    for text in texts:
        available |= _numbers(text)
    return sorted(n for n in claimed if n not in available)
