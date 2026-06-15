"""RAG orchestrator — the top-level query pipeline (§6).

Ties the stages together end to end:

    query → retrieve (filtered dense search) → context selection (parent-expand,
    dedup, budget) → grounded generation with inline ``[n]`` markers →
    citations built from payloads.

This module owns the *flow*; the individual stages live in :mod:`app.retrieval`
and :mod:`app.generation` and are enhanced in place as they are built out (query
understanding, hybrid search, reranking, conflict surfacing, faithfulness,
caching, observability). The API layer calls :func:`answer_query`.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.generation.llm_client import get_llm
from app.generation.prompts import GROUNDED_SYSTEM_PROMPT, format_context_blocks
from app.retrieval.citations import build_citations
from app.retrieval.context_builder import ContextBlock, build_context
from app.retrieval.hybrid_search import search

logger = logging.getLogger(__name__)


def _generate(question: str, blocks: list[ContextBlock]) -> str:
    """Grounded generation: answer only from the numbered context, citing ``[n]``."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    if not blocks:
        return "I don't have information on that in the available sources."

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", GROUNDED_SYSTEM_PROMPT),
            ("human", "Numbered context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | get_llm() | StrOutputParser()
    return chain.invoke(
        {"context": format_context_blocks(blocks), "question": question}
    ).strip()


def answer_query(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    """Answer a question from the corpus and return a grounded, cited result.

    Returns a dict matching :class:`app.schemas.query.QueryResponse`.
    """
    settings = get_settings()
    n = top_k or settings.retrieval_top_k
    user_groups = user_groups or ["public"]

    candidates = search(
        question,
        limit=settings.retrieval_candidate_k,
        tenant_id=tenant_id,
        user_groups=user_groups,
    )
    blocks = build_context(candidates, limit=n)
    answer = _generate(question, blocks)
    citations = build_citations(blocks)

    return {
        "answer": answer,
        "citations": citations,
        "intent": "qa",
        "used_chunks": len(blocks),
        "conflict": any(b.conflict for b in blocks),
        "cached": False,
    }
