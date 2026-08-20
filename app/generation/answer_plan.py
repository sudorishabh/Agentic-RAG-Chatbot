"""Evidence-coverage plan: what the question asks for, and what the retrieved
context can actually support.

The problem this exists to solve
---------------------------------
Retrieval can succeed and generation can still under-deliver: Q001 retrieved
the Mission and Goals page — the correct, authoritative source — and the
answer stated the mission but omitted the twelve stated goals and all six
values, both present on the same page. The evidence was there; the prompt's
generic "answer factually, in as much depth as the context genuinely
supports" gave the model no reason to notice it had left two of three asked-for
things on the table.

"Be more complete" is not a fix for that, because it doesn't tell the model
what it was asked for. The fix computed here is narrower and evidence-grounded:
work out the distinct, separately-answerable things the question names, check
each one against the actual retrieved text (no LLM judgement, no invention),
and hand generation an explicit, per-item directive — answer this, this is
supported; say plainly that the corpus does not specify that, don't invent it.

Deliberately small
-------------------
* One structured LLM call to decompose the question — the same shape and cost
  as the query-understanding call already made every request, and run in
  parallel with retrieval so it adds no serial latency (see
  ``app.pipeline.query_pipeline``).
* Coverage is checked by lexical matching against the retrieved text, not by a
  second model call: cheap, deterministic, and it can only ever narrow what
  the model is told is supported — it cannot fabricate a match that is not
  actually in the text.
* The directive is emitted only when it would change anything: a single-item,
  fully-supported plan (the overwhelming majority of questions) produces no
  text at all, so this cannot regress a question the base prompt already
  handles.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Sequence

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class _Requirements(BaseModel):
    requirements: list[str] = Field(default_factory=list)


_REQUIREMENTS_SYSTEM = (
    "List the distinct, separately-answerable things this question asks for, "
    "as short noun phrases (2-4 words each), in the order asked.\n"
    "Return exactly ONE item for a question with a single subject, however long "
    "or detailed the wording — do not invent sub-parts a plain reading does not "
    "ask for.\n"
    "Return more than one item ONLY when the question explicitly names several "
    "distinct things via 'and', a list, or multiple question words — e.g. "
    "'mission and vision' -> ['mission', 'vision']; 'what services and "
    "certifications does X offer' -> ['services', 'certifications'].\n"
    "Never add a requirement the wording does not name (no 'history' unless "
    "asked, no 'values' unless asked). Copy the requesting words rather than "
    "paraphrasing broadly, so 'primary mission and vision' yields "
    "['mission', 'vision'], not ['overview']."
)


def extract_requirements(question: str) -> list[str]:
    """The distinct things the question asks for, or ``[]`` on any failure.

    Fails open to an empty list, which is a no-op everywhere downstream: no
    requirements means no directive is built and generation behaves exactly as
    it did before this module existed.
    """
    if not (question or "").strip():
        return []
    try:
        from app.core.clients.llm import get_structured_llm

        result: _Requirements = (
            get_structured_llm().with_structured_output(_Requirements)
            .invoke([("system", _REQUIREMENTS_SYSTEM), ("human", question)])
        )
        return [r.strip() for r in result.requirements if r and r.strip()][:6]
    except Exception:
        logger.warning("Requirement extraction failed; skipping the answer plan.",
                       exc_info=True)
        return []


_WORD = re.compile(r"[a-z][a-z'-]{2,}")
_STOPWORDS = frozenset(
    """
    the a an of to in on for and or with by from as at is are was were be been
    being this that these those it its their our we us you your they them what
    which who whom whose when where why how does do did can could will would
    should has have had primary main key does not
    """.split()
)


def _terms(requirement: str) -> list[str]:
    """The requirement's own content words — what to look for in the evidence."""
    return [
        w for w in _WORD.findall(requirement.lower())
        if w not in _STOPWORDS and len(w) >= 3
    ]


@dataclass
class AnswerPlan:
    """What the question asked for, and what the retrieved text can support.

    ``evidence_blocks`` is kept only for callers that want to inspect or log
    the plan; the directive text is derived from ``supported``/``unsupported``
    alone and never repeats block content, so nothing here can introduce a
    fact generation did not already have in the numbered context.
    """

    requirements: list[str] = field(default_factory=list)
    supported: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    evidence_blocks: list[int] = field(default_factory=list)


def build_plan(requirements: Sequence[str], blocks: Sequence) -> AnswerPlan:
    """Check each requirement against the retrieved text.

    A requirement counts as supported when any one of its content words
    appears in the concatenated block text — deliberately permissive, so the
    failure mode of a bad match is "the directive says nothing" (silence,
    identical to today) rather than "the directive wrongly tells the model to
    disclaim something the text actually covers". Precision is generation's
    job; this step only decides whether to raise the question at all.
    """
    requirements = [r for r in requirements if r and r.strip()]
    if len(requirements) < 2:
        # A single requirement is the ordinary case the base prompt already
        # handles — "answer factually, in as much depth as the context
        # genuinely supports" is sufficient when there is only one thing to
        # cover, and emitting a directive here would be pure noise on the vast
        # majority of questions.
        return AnswerPlan(requirements=list(requirements),
                          supported=list(requirements))
    text = " ".join(getattr(b, "text", "") or "" for b in blocks).lower()
    supported, unsupported = [], []
    for requirement in requirements:
        terms = _terms(requirement)
        hit = any(t in text for t in terms) if terms else False
        (supported if hit else unsupported).append(requirement)
    return AnswerPlan(
        requirements=list(requirements), supported=supported,
        unsupported=unsupported,
        evidence_blocks=[getattr(b, "n", 0) for b in blocks],
    )


def plan_directive(plan: AnswerPlan) -> str:
    """The prompt addition for this plan, or ``""`` when nothing needs saying.

    Silent whenever there is one requirement or every requirement is
    supported — the ordinary case — so this can only add instruction, never
    remove the model's freedom to write a normal answer. It only speaks up for
    the two situations the base prompt handles poorly: a genuinely multi-part
    question (push for covering all the supported parts, not just the first),
    and a part the evidence does not cover (say so, don't invent it).
    """
    if len(plan.requirements) < 2:
        return ""
    lines = [
        "\n\n## This question has more than one part",
        f"It asks about: {', '.join(plan.requirements)}.",
    ]
    if plan.supported:
        lines.append(
            f"The retrieved context has material on: {', '.join(plan.supported)}. "
            "Cover every one of these with the specific facts, terms or figures "
            "the context states — do not answer only the first and summarize "
            "the rest away."
        )
    if plan.unsupported:
        lines.append(
            f"The retrieved context does NOT clearly cover: "
            f"{', '.join(plan.unsupported)}. Say plainly that the retrieved "
            "material does not specify this part, in one short clause — never "
            "invent it, and never substitute a generic description in its place."
        )
    if plan.supported:
        lines.append(
            "At least one part of this question is answered below — do not "
            "refuse the whole question because one part is unsupported."
        )
    return "\n".join(lines)
