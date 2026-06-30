from __future__ import annotations

import logging
from typing import Any, Iterator

from app.config import get_settings
from app.generation.llm_client import get_llm
from app.generation.prompts import (
    CHITCHAT_SYSTEM_PROMPT,
    GROUNDED_SYSTEM_PROMPT,
    format_context_blocks,
    format_directive,
)
from app.retrieval.citations import build_citations
from app.generation.prompts import REFUSAL
from app.observability.tracing import record_query_metrics, span
from app.retrieval.context_builder import ContextBlock, build_context
from app.retrieval.hybrid_search import search
from app.retrieval.query_processor import ProcessedQuery, process
from app.retrieval.reranker import rerank

logger = logging.getLogger(__name__)


def _chitchat(question: str, history: list[dict[str, str]] | None) -> str:
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


def _build_system(answer_format: str | None, correction: str | None) -> str:
    system = GROUNDED_SYSTEM_PROMPT
    directive = format_directive(answer_format)
    if directive:
        system += f"\n\n{directive}"
    if correction:
        system += f"\n\n{correction}"
    return system


def _generate(
    question: str,
    blocks: list[ContextBlock],
    *,
    correction: str | None = None,
    answer_format: str | None = None,
) -> str:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    if not blocks:
        return REFUSAL

    system = _build_system(answer_format, correction)
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


def _grounded_answer(
    question: str, blocks: list[ContextBlock], *, answer_format: str | None = None
) -> str:
    from app.generation import faithfulness

    answer = faithfulness.validate_markers(
        _generate(question, blocks, answer_format=answer_format), len(blocks)
    )
    if get_settings().faithfulness_check and blocks:
        report = faithfulness.verify(answer, blocks)
        if not report.faithful:
            logger.info("Faithfulness check flagged claims; regenerating once.")
            retry = _generate(
                question, blocks,
                correction=report.correction_note(), answer_format=answer_format,
            )
            answer = faithfulness.validate_markers(retry, len(blocks))
    return answer


def retrieve(
    search_query: str,
    *,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    filters: list[Any] | None = None,
    n: int | None = None,
    query_vector: list[float] | None = None,
) -> list[ContextBlock]:
    settings = get_settings()
    n = n or settings.retrieval_top_k
    user_groups = user_groups or ["public"]

    with span("rag.search") as s:
        candidates = search(
            search_query,
            limit=settings.retrieval_candidate_k,
            tenant_id=tenant_id,
            user_groups=user_groups,
            extra_filter=filters or None,
            query_vector=query_vector,
        )
        s.set("candidates", len(candidates))

    with span("rag.rerank") as s:
        ranked = rerank(search_query, candidates)
        s.set("survivors", len(ranked))
    if not ranked:
        return []
    return build_context(ranked, limit=n)


def _answer(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    from app.cache import redis_cache
    from app.ingestion.embedder import embed_query_cached

    settings = get_settings()
    n = top_k or settings.retrieval_top_k
    user_groups = user_groups or ["public"]

    signature = redis_cache.response_signature(
        question, tenant_id=tenant_id, user_groups=user_groups, top_k=n
    )
    hit = redis_cache.get_response(signature)
    if hit is not None:
        return {**hit, "cached": True}

    with span("rag.query_understanding"):
        pq: ProcessedQuery = process(question, history)
    if pq.intent == "chitchat":
        return _empty("chitchat", _chitchat(question, history))

    if pq.intent == "structured":
        from app.retrieval.drupal_router import answer_structured

        structured = answer_structured(question, history)
        if structured is not None:
            return structured

    query_vector = embed_query_cached(pq.search_query)
    semantic = redis_cache.semantic_lookup(query_vector)
    if semantic is not None:
        return {**semantic, "cached": True}

    blocks = retrieve(
        pq.search_query,
        tenant_id=tenant_id,
        user_groups=user_groups,
        filters=pq.filters,
        n=n,
        query_vector=query_vector,
    )
    if not blocks:
        return _empty(pq.intent, REFUSAL)

    with span("rag.generate") as s:
        answer = _grounded_answer(pq.search_query, blocks, answer_format=pq.answer_format)
        s.set("answer_chars", len(answer))
    citations = build_citations(blocks)

    result = {
        "answer": answer,
        "citations": [c.model_dump() for c in citations],
        "intent": pq.intent,
        "used_chunks": len(blocks),
        "conflict": any(b.conflict for b in blocks),
        "cached": False,
    }
    redis_cache.set_response(signature, result)
    redis_cache.semantic_store(query_vector, result)
    return result


def answer_query(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    with span("rag.answer_query") as s:
        result = _answer(
            question,
            history=history,
            tenant_id=tenant_id,
            user_groups=user_groups,
            top_k=top_k,
        )
        record_query_metrics(
            latency_ms=s.elapsed_ms,
            intent=result.get("intent"),
            used_chunks=result.get("used_chunks", 0),
            has_citations=bool(result.get("citations")),
            answered=result.get("answer") != REFUSAL,
            conflict=result.get("conflict", False),
            cached=result.get("cached", False),
        )
    return result


def _generate_stream(
    question: str, blocks: list[ContextBlock], *, answer_format: str | None = None
) -> Iterator[str]:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _build_system(answer_format, None)),
            ("human", "Numbered context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | get_llm(streaming=True) | StrOutputParser()
    yield from chain.stream(
        {"context": format_context_blocks(blocks), "question": question}
    )


def stream_answer(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    top_k: int | None = None,
) -> Iterator[dict[str, Any]]:
    from app.ingestion.embedder import embed_query_cached

    settings = get_settings()
    n = top_k or settings.retrieval_top_k
    user_groups = user_groups or ["public"]

    pq = process(question, history)
    if pq.intent == "chitchat":
        yield {"type": "token", "text": _chitchat(question, history)}
        yield {"type": "sources", "citations": [], "intent": "chitchat",
               "used_chunks": 0, "conflict": False}
        yield {"type": "done"}
        return

    if pq.intent == "structured":
        from app.retrieval.drupal_router import answer_structured

        structured = answer_structured(question, history)
        if structured is not None:
            yield {"type": "token", "text": structured["answer"]}
            yield {"type": "sources", **{k: structured[k] for k in
                   ("citations", "intent", "used_chunks", "conflict")}}
            yield {"type": "done"}
            return

    query_vector = embed_query_cached(pq.search_query)
    blocks = retrieve(
        pq.search_query, tenant_id=tenant_id, user_groups=user_groups,
        filters=pq.filters, n=n, query_vector=query_vector,
    )
    if not blocks:
        yield {"type": "token", "text": REFUSAL}
        yield {"type": "sources", "citations": [], "intent": pq.intent,
               "used_chunks": 0, "conflict": False}
        yield {"type": "done"}
        return

    for token in _generate_stream(pq.search_query, blocks, answer_format=pq.answer_format):
        yield {"type": "token", "text": token}
    yield {
        "type": "sources",
        "citations": [c.model_dump() for c in build_citations(blocks)],
        "intent": pq.intent,
        "used_chunks": len(blocks),
        "conflict": any(b.conflict for b in blocks),
    }
    yield {"type": "done"}


def search_blocks(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    pq = process(question, history)
    blocks = retrieve(
        pq.search_query, tenant_id=tenant_id, user_groups=user_groups,
        filters=pq.filters, n=top_k,
    )
    return {
        "intent": pq.intent,
        "search_query": pq.search_query,
        "blocks": [
            {
                "n": b.n,
                "score": round(b.score, 4),
                "conflict": b.conflict,
                "text": b.text,
                "document_id": b.payload.get("document_id"),
                "source_type": b.payload.get("source_type"),
                "title": b.payload.get("title"),
                "page_number": b.payload.get("page_number"),
                "section_heading": b.payload.get("section_heading"),
            }
            for b in blocks
        ],
    }
