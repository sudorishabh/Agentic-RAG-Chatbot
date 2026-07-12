"""Decomposed GPT-4o-mini judges for eval runs.

Mini is unreliable as a holistic grader but strong at micro-verdicts, so
judging is decomposed: claim extraction (one structured call), then one
binary supported/unsupported call per claim (bounded thread pool), plus a
separately-anchored 1-5 relevance rubric. `citation_coverage` is fully
deterministic. Every judge fails open (None) — a judging error must never
fail an eval run or, later, a production request.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Sequence

from pydantic import BaseModel, Field

# Canonical home is production code (the quality monitor uses it too);
# re-exported here so eval callers keep one import site for all judges.
from app.generation.faithfulness import citation_coverage  # noqa: F401

logger = logging.getLogger(__name__)

_CHECK_WORKERS = 4


class Claim(BaseModel):
    text: str
    citations: list[int] = Field(default_factory=list)


class ClaimList(BaseModel):
    claims: list[Claim] = Field(default_factory=list)


class SupportVerdict(BaseModel):
    supported: bool


class RelevanceScore(BaseModel):
    score: int = Field(description="1-5 per the rubric.")


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

_RELEVANCE_SYSTEM = (
    "Rate how well the answer addresses the question, 1-5: 5 = fully answers "
    "with specifics; 4 = answers with minor gaps; 3 = partially answers; 2 = "
    "on-topic but mostly misses the point; 1 = irrelevant or empty.\n"
    "Example (2): Q 'What did the 2024 budget allocate to solar?' A 'Solar "
    "energy is important for India.' — on-topic, answers nothing.\n"
    "Example (5): Q 'What did the 2024 budget allocate to solar?' A 'Rs 10,000 "
    "crore for grid-scale solar plus rooftop subsidies [1], a 12% increase "
    "over 2023 [2].' — specific, complete, cited."
)


def _structured(schema: type[BaseModel]) -> Any:
    from app.generation.llm_client import get_structured_llm

    return get_structured_llm().with_structured_output(schema)


def extract_claims(answer: str) -> list[Claim]:
    """Atomic claims with their [n] citations. Raises on LLM failure —
    judge_faithfulness turns that into a None report."""
    result: ClaimList = _structured(ClaimList).invoke(
        [("system", _EXTRACT_SYSTEM), ("human", f"Answer:\n{answer}")]
    )
    return [c for c in result.claims if c.text.strip()]


def claim_supported(claim: str, block_text: str) -> bool | None:
    """One binary verdict; None on error (dropped from the rate, not counted
    against the answer)."""
    try:
        verdict: SupportVerdict = _structured(SupportVerdict).invoke(
            [
                ("system", _SUPPORT_SYSTEM),
                ("human", f"Claim: {claim}\n\nPassage:\n{block_text}"),
            ]
        )
        return bool(verdict.supported)
    except Exception:
        logger.warning("Claim support check failed.", exc_info=True)
        return None


def _text_for_claim(claim: Claim, block_texts: Sequence[str]) -> str:
    """The evidence a claim is checked against: its cited blocks (1-indexed);
    uncited or out-of-range claims are checked against the whole context."""
    cited = [block_texts[n - 1] for n in claim.citations if 1 <= n <= len(block_texts)]
    return "\n\n".join(cited or block_texts)


def judge_faithfulness(
    answer: str, block_texts: Sequence[str]
) -> dict[str, Any] | None:
    """Claim-level faithfulness report, or None when judging itself failed.

    Report: {claims: [{text, citations, supported}], total, supported, rate,
    faithful} — `faithful` means every checkable claim was supported.
    """
    if not block_texts:
        return None
    try:
        claims = extract_claims(answer)
    except Exception:
        logger.warning("Claim extraction failed.", exc_info=True)
        return None
    if not claims:
        return {"claims": [], "total": 0, "supported": 0, "rate": 1.0, "faithful": True}

    with ThreadPoolExecutor(max_workers=_CHECK_WORKERS) as pool:
        verdicts = list(
            pool.map(lambda c: claim_supported(c.text, _text_for_claim(c, block_texts)), claims)
        )
    checked = [(c, v) for c, v in zip(claims, verdicts) if v is not None]
    if not checked:
        return None
    supported = sum(1 for _, v in checked if v)
    return {
        "claims": [
            {"text": c.text, "citations": c.citations, "supported": v}
            for c, v in checked
        ],
        "total": len(checked),
        "supported": supported,
        "rate": round(supported / len(checked), 3),
        "faithful": supported == len(checked),
    }


def judge_relevance(question: str, answer: str) -> int | None:
    """1-5 rubric score, clamped; None on error."""
    try:
        result: RelevanceScore = _structured(RelevanceScore).invoke(
            [
                ("system", _RELEVANCE_SYSTEM),
                ("human", f"Question: {question}\n\nAnswer:\n{answer}"),
            ]
        )
        return max(1, min(5, int(result.score)))
    except Exception:
        logger.warning("Relevance judge failed.", exc_info=True)
        return None


