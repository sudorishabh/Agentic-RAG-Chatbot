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
from app.generation.prompts import REFUSAL
from app.retrieval.context_builder import ContextBlock, build_context
from app.retrieval.hybrid_search import search
from app.retrieval.query_processor import ProcessedQuery, process
from app.retrieval.reranker import rerank

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


def _generate(question: str, blocks: list[ContextBlock], *, correction: str | None = None) -> str:
    """Grounded generation: answer only from the numbered context, citing ``[n]``.

    ``correction`` carries a faithfulness corrective note for a one-shot retry.
    """
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    if not blocks:
        return REFUSAL

    system = GROUNDED_SYSTEM_PROMPT + (f"\n\n{correction}" if correction else "")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Numbered context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | get_llm() | StrOutputParser()
    return chain.invoke(
        {"context": format_context_blocks(blocks), "question": question}
    ).strip()


def _grounded_answer(question: str, blocks: list[ContextBlock]) -> str:
    """Generate, scrub stray markers, and (optionally) verify + regenerate once."""
    from app.generation import faithfulness

    answer = faithfulness.validate_markers(_generate(question, blocks), len(blocks))
    if get_settings().faithfulness_check and blocks:
        report = faithfulness.verify(answer, blocks)
        if not report.faithful:
            logger.info("Faithfulness check flagged claims; regenerating once.")
            retry = _generate(question, blocks, correction=report.correction_note())
            answer = faithfulness.validate_markers(retry, len(blocks))
    return answer


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
    from app.cache import redis_cache
    from app.ingestion.embedder import embed_query_cached

    settings = get_settings()
    n = top_k or settings.retrieval_top_k
    user_groups = user_groups or ["public"]

    # Exact response cache: identical (query, scope) skips the whole pipeline (§10.3).
    signature = redis_cache.response_signature(
        question, tenant_id=tenant_id, user_groups=user_groups, top_k=n
    )
    hit = redis_cache.get_response(signature)
    if hit is not None:
        return {**hit, "cached": True}

    # Step 1 — query understanding: rewrite, intent routing, facet filters (§6.1).
    pq: ProcessedQuery = process(question, history)
    if pq.intent == "chitchat":
        return _empty("chitchat", _chitchat(question, history))

    # 'structured' intent → exact lookup / aggregate over the Drupal JSON:API (§7).
    # Falls through to semantic QA when the router can't answer it.
    if pq.intent == "structured":
        from app.retrieval.drupal_router import answer_structured

        structured = answer_structured(question, history)
        if structured is not None:
            return structured

    # Embed the (rewritten) query once — reused for retrieval and the semantic cache.
    query_vector = embed_query_cached(pq.search_query)
    semantic = redis_cache.semantic_lookup(query_vector)
    if semantic is not None:
        return {**semantic, "cached": True}

    candidates = search(
        pq.search_query,
        limit=settings.retrieval_candidate_k,
        tenant_id=tenant_id,
        user_groups=user_groups,
        extra_filter=pq.filters or None,
        query_vector=query_vector,
    )
    # Step 4 — rerank wide pool and apply the score-threshold refusal guard (§6.3).
    ranked = rerank(pq.search_query, candidates)
    if not ranked:
        return _empty(pq.intent, REFUSAL)

    blocks = build_context(ranked, limit=n)
    if not blocks:
        return _empty(pq.intent, REFUSAL)

    answer = _grounded_answer(pq.search_query, blocks)
    citations = build_citations(blocks)

    result = {
        "answer": answer,
        "citations": [c.model_dump() for c in citations],
        "intent": pq.intent,
        "used_chunks": len(blocks),
        "conflict": any(b.conflict for b in blocks),
        "cached": False,
    }
    # Cache the sourced answer for exact and near-duplicate future queries (§10.3).
    redis_cache.set_response(signature, result)
    redis_cache.semantic_store(query_vector, result)
    return result
