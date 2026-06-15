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
from app.generation.prompts import (
    CHITCHAT_SYSTEM_PROMPT,
    GROUNDED_SYSTEM_PROMPT,
    format_context_blocks,
)
from app.retrieval.citations import build_citations
from app.retrieval.context_builder import ContextBlock, build_context
from app.retrieval.hybrid_search import search
from app.retrieval.query_processor import ProcessedQuery, process

logger = logging.getLogger(__name__)


def _chitchat(question: str, history: list[dict[str, str]] | None) -> str:
    """Answer a greeting / meta turn directly, without retrieval, keeping the bot
    scoped to the corpus (§10.6.6)."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [("system", CHITCHAT_SYSTEM_PROMPT), ("human", "{question}")]
    )
    chain = prompt | get_llm() | StrOutputParser()
    return chain.invoke({"question": question}).strip()


def _empty(intent: str, answer: str, *, cached: bool = False) -> dict[str, Any]:
    return {
        "answer": answer,
        "citations": [],
        "intent": intent,
        "used_chunks": 0,
        "conflict": False,
        "cached": cached,
    }


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

    # Step 1 — query understanding: rewrite, intent routing, facet filters (§6.1).
    pq: ProcessedQuery = process(question, history)
    if pq.intent == "chitchat":
        return _empty("chitchat", _chitchat(question, history))

    # 'structured' intent routes to the Drupal JSON:API router (§7); until that is
    # wired it falls through to semantic QA so the question is still answered.

    candidates = search(
        pq.search_query,
        limit=settings.retrieval_candidate_k,
        tenant_id=tenant_id,
        user_groups=user_groups,
        extra_filter=pq.filters or None,
    )
    blocks = build_context(candidates, limit=n)
    if not blocks:
        return _empty(pq.intent, _generate(pq.search_query, blocks))

    answer = _generate(pq.search_query, blocks)
    citations = build_citations(blocks)

    return {
        "answer": answer,
        "citations": citations,
        "intent": pq.intent,
        "used_chunks": len(blocks),
        "conflict": any(b.conflict for b in blocks),
        "cached": False,
    }
