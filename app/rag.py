from __future__ import annotations

import logging
from dataclasses import dataclass
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
from app.observability.metrics import collect_into, component_totals
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


def _empty(
    intent: str, answer: str, *, answer_format: str = "default", cached: bool = False
) -> dict[str, Any]:
    return {
        "answer": answer,
        "citations": [],
        "intent": intent,
        "answer_format": answer_format,
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
        with span("rag.faithfulness") as s:
            report = faithfulness.verify(answer, blocks)
            s.set("faithful", report.faithful)
        if not report.faithful:
            logger.info("Faithfulness check flagged claims; regenerating once.")
            retry = _generate(
                question, blocks,
                correction=report.correction_note(), answer_format=answer_format,
            )
            answer = faithfulness.validate_markers(retry, len(blocks))
    return answer


def _dual_search(
    search_query: str,
    *,
    tenant_id: str,
    user_groups: list[str],
    filters: list[Any] | None,
    query_vector: list[float] | None,
    settings: Any,
) -> list[Any]:
    """Two pulls sharing one query vector: website (source_type == website) and
    "not website". Preserves any non-source filters (language / date) on both.
    Their union guarantees the website's best chunks are fetched even though PDFs
    dominate the corpus (see docs/website-preference-retrieval.md)."""
    from qdrant_client.models import FieldCondition, MatchValue

    base = list(filters or [])
    website_cond = FieldCondition(key="source_type", match=MatchValue(value="website"))
    website = search(
        search_query,
        limit=settings.website_candidate_k,
        tenant_id=tenant_id,
        user_groups=user_groups,
        extra_filter=base + [website_cond],
        query_vector=query_vector,
    )
    others = search(
        search_query,
        limit=settings.retrieval_candidate_k,
        tenant_id=tenant_id,
        user_groups=user_groups,
        extra_filter=base or None,
        extra_must_not=[website_cond],
        query_vector=query_vector,
    )
    return website + others


def _supplement_attachments(
    blocks: list[ContextBlock],
    ranked: list[Any],
    *,
    search_query: str,
    query_vector: list[float],
    tenant_id: str,
    user_groups: list[str],
    n: int,
    segregate: bool,
) -> list[ContextBlock]:
    """Detailed answers: when admitted website blocks have attached PDFs that
    contributed nothing to the context, pull those attachments' chunks once and
    let rerank decide admission. Bounded to one extra Qdrant query; any failure
    keeps the original blocks."""
    from app.retrieval import catalog
    from app.retrieval.scoped_retrieval import search_within_documents

    try:
        website_ids = {
            b.payload.get("document_id")
            for b in blocks
            if b.payload.get("source_type") == "website" and b.payload.get("document_id")
        }
        if not website_ids:
            return blocks
        attachments = catalog.attachments_for(sorted(website_ids))
        if not attachments:
            return blocks
        # An attachment document's id is its file_uuid; it is "represented"
        # when any admitted block is that document or links to it.
        represented = {
            v
            for b in blocks
            for v in (b.payload.get("document_id"), b.payload.get("linked_pdf_id"))
            if v
        }
        file_uuids = list(dict.fromkeys(
            a["file_uuid"]
            for rows in attachments.values()
            for a in rows
            if a.get("file_uuid") and a["file_uuid"] not in represented
        ))
        if not file_uuids:
            return blocks
        extra = search_within_documents(
            query_vector, file_uuids, limit=10,
            tenant_id=tenant_id, user_groups=user_groups,
        )
        seen = {c.id for c in ranked}
        new = [c for c in extra if c.id not in seen]
        if not new:
            return blocks
        reranked = rerank(search_query, list(ranked) + new)
        return build_context(reranked, limit=n, segregate=segregate)
    except Exception:
        logger.warning("Attachment supplementation failed; keeping original blocks.",
                       exc_info=True)
        return blocks


def retrieve(
    search_query: str,
    *,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    filters: list[Any] | None = None,
    n: int | None = None,
    query_vector: list[float] | None = None,
    answer_format: str | None = None,
    source_type: str | None = None,
) -> list[ContextBlock]:
    settings = get_settings()
    n = n or settings.retrieval_top_k
    user_groups = user_groups or ["public"]

    # Prefer website content only when the feature is on, the user didn't pin a
    # source (explicit intent → honor their filter with a single pull, else the
    # PDF pull's "not website" would contradict a website filter), and the answer
    # isn't a table (tables live in PDFs — don't force a website lead).
    dual = bool(settings.prefer_website_enabled) and not source_type and answer_format != "table"

    if query_vector is None:
        from app.ingestion.embedder import embed_query_cached

        with span("rag.embed_query"):
            query_vector = embed_query_cached(search_query)

    with span("rag.search") as s:
        if dual:
            candidates = _dual_search(
                search_query, tenant_id=tenant_id, user_groups=user_groups,
                filters=filters, query_vector=query_vector, settings=settings,
            )
        else:
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
        table_boost = settings.rerank_table_boost if answer_format == "table" else 0.0
        ranked = rerank(search_query, candidates, table_boost=table_boost)
        s.set("survivors", len(ranked))
    if not ranked:
        return []
    with span("rag.context_build"):
        blocks = build_context(ranked, limit=n, segregate=dual)
    if answer_format == "detailed" and blocks:
        with span("rag.attachment_pull"):
            blocks = _supplement_attachments(
                blocks, ranked, search_query=search_query, query_vector=query_vector,
                tenant_id=tenant_id, user_groups=user_groups, n=n, segregate=dual,
            )
    return blocks


@dataclass
class _Generation:
    """What the answer step needs after the shared front-matter (query
    understanding, cache lookups, retrieval) has decided a fresh grounded answer
    must be generated. Carried out of `_prepare` so the buffered and streaming
    entrypoints share one pipeline and differ only in how they emit the answer."""

    pq: ProcessedQuery
    blocks: list[ContextBlock]
    query_vector: list[float]
    signature: str
    tenant_id: str
    user_groups: list[str]
    top_k: int


def _prepare(
    question: str,
    *,
    history: list[dict[str, str]] | None,
    tenant_id: str,
    user_groups: list[str] | None,
    top_k: int | None,
) -> tuple[dict[str, Any] | None, _Generation | None]:
    """Shared front-matter for both answer entrypoints.

    Returns ``(result, None)`` when a complete answer is already available (a
    response- or semantic-cache hit, chit-chat, a structured lookup, or a
    no-context refusal), or ``(None, generation)`` when a grounded answer still
    has to be generated.
    """
    from app.cache import redis_cache, semantic_cache
    from app.ingestion.embedder import embed_query_cached

    settings = get_settings()
    n = top_k or settings.retrieval_top_k
    user_groups = user_groups or ["public"]

    signature = redis_cache.response_signature(
        question, tenant_id=tenant_id, user_groups=user_groups, top_k=n
    )
    with span("rag.response_cache"):
        hit = redis_cache.get_response(signature)
    if hit is not None:
        return {**hit, "cached": True}, None

    with span("rag.query_understanding"):
        pq: ProcessedQuery = process(question, history)
    if pq.intent == "chitchat":
        return _empty("chitchat", _chitchat(question, history)), None

    if pq.intent == "structured":
        from app.retrieval.drupal_router import answer_structured, resolve_lookup_document

        chain_id = resolve_lookup_document(pq.analysis, question)
        if chain_id is not None:
            # Content question about one named title: answer from that
            # document's chunks (QA path below) instead of title+URL.
            from qdrant_client.models import FieldCondition, MatchValue

            pq.filters.append(
                FieldCondition(key="document_id", match=MatchValue(value=chain_id))
            )
        else:
            structured = answer_structured(question, history, analysis=pq.analysis)
            if structured is not None:
                structured.setdefault("answer_format", pq.answer_format)
                return structured, None

    if pq.intent == "scoped_summary":
        from app.retrieval.summarizer import summarize_scope

        with span("rag.scoped_summary"):
            summary = summarize_scope(
                pq.analysis, tenant_id=tenant_id, user_groups=user_groups
            )
        if summary is not None:
            summary.setdefault("answer_format", pq.answer_format)
            return summary, None
        # Empty/unresolvable scope: fall through to plain semantic QA.

    with span("rag.embed_query"):
        query_vector = embed_query_cached(pq.search_query)
    with span("rag.semantic_cache") as s:
        semantic = semantic_cache.lookup(
            query_vector, tenant_id=tenant_id, user_groups=user_groups,
            top_k=n, answer_format=pq.answer_format,
        )
        s.set("hit", semantic is not None)
    if semantic is not None:
        return {**semantic, "cached": True}, None

    blocks = retrieve(
        pq.search_query,
        tenant_id=tenant_id,
        user_groups=user_groups,
        filters=pq.filters,
        n=n,
        query_vector=query_vector,
        answer_format=pq.answer_format,
        source_type=pq.source_type,
    )
    if not blocks:
        return _empty(pq.intent, REFUSAL, answer_format=pq.answer_format), None

    return None, _Generation(
        pq=pq, blocks=blocks, query_vector=query_vector, signature=signature,
        tenant_id=tenant_id, user_groups=user_groups, top_k=n,
    )


def _assemble(answer: str, gen: _Generation) -> dict[str, Any]:
    return {
        "answer": answer,
        "citations": [c.model_dump() for c in build_citations(gen.blocks)],
        "intent": gen.pq.intent,
        "answer_format": gen.pq.answer_format,
        "used_chunks": len(gen.blocks),
        "conflict": any(b.conflict for b in gen.blocks),
        "cached": False,
    }


def _persist(gen: _Generation, result: dict[str, Any]) -> None:
    from app.cache import redis_cache, semantic_cache

    with span("rag.response_cache_store"):
        redis_cache.set_response(gen.signature, result)
    with span("rag.semantic_cache_store"):
        semantic_cache.store(
            gen.query_vector, result, tenant_id=gen.tenant_id,
            user_groups=gen.user_groups, top_k=gen.top_k,
            answer_format=gen.pq.answer_format,
        )


def _record(
    span_ctx: Any, result: dict[str, Any], stages: dict[str, float] | None = None
) -> None:
    record_query_metrics(
        latency_ms=span_ctx.elapsed_ms,
        intent=result.get("intent"),
        used_chunks=result.get("used_chunks", 0),
        has_citations=bool(result.get("citations")),
        answered=result.get("answer") != REFUSAL,
        conflict=result.get("conflict", False),
        cached=result.get("cached", False),
        components=component_totals(stages) if stages else None,
        stages={k: round(v, 1) for k, v in stages.items()} if stages else None,
    )


def _answer(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    result, gen = _prepare(
        question, history=history, tenant_id=tenant_id,
        user_groups=user_groups, top_k=top_k,
    )
    if result is not None:
        return result

    with span("rag.generate") as s:
        answer = _grounded_answer(
            gen.pq.search_query, gen.blocks, answer_format=gen.pq.answer_format
        )
        s.set("answer_chars", len(answer))
    result = _assemble(answer, gen)
    _persist(gen, result)
    return result


def answer_query(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    stages: dict[str, float] = {}
    with collect_into(stages), span("rag.answer_query") as s:
        result = _answer(
            question,
            history=history,
            tenant_id=tenant_id,
            user_groups=user_groups,
            top_k=top_k,
        )
        _record(s, result, stages)
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


def _stream_result(result: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Emit a ready-made result dict (cache hit, chit-chat, structured lookup, or
    refusal) as the standard token / sources / done SSE event sequence."""
    yield {"type": "token", "text": result.get("answer", "")}
    yield {
        "type": "sources",
        "citations": result.get("citations", []),
        "intent": result.get("intent", "qa"),
        "answer_format": result.get("answer_format", "default"),
        "used_chunks": result.get("used_chunks", 0),
        "conflict": result.get("conflict", False),
    }
    yield {"type": "done"}


def stream_answer(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    tenant_id: str = "default",
    user_groups: list[str] | None = None,
    top_k: int | None = None,
) -> Iterator[dict[str, Any]]:
    # Spans after the first yield only reach the global aggregates, not this
    # dict — the SSE driver resumes the generator in fresh contexts (see
    # metrics.collect_into) — so the logged breakdown covers the pre-token
    # stages, which is where retrieval time goes.
    stages: dict[str, float] = {}
    with collect_into(stages), span("rag.stream_answer") as s:
        result, gen = _prepare(
            question, history=history, tenant_id=tenant_id,
            user_groups=user_groups, top_k=top_k,
        )
        # Cache hit, chit-chat, structured lookup, or refusal — already complete.
        if result is not None:
            yield from _stream_result(result)
            _record(s, result, stages)
            return

        if get_settings().faithfulness_check:
            # Faithfulness needs the whole answer (and may regenerate once), which
            # is incompatible with live token streaming — so buffer, then emit.
            # The check is off by default, so the normal path streams token-by-token.
            answer = _grounded_answer(
                gen.pq.search_query, gen.blocks, answer_format=gen.pq.answer_format
            )
            yield {"type": "token", "text": answer}
        else:
            from app.generation import faithfulness

            parts: list[str] = []
            for token in _generate_stream(
                gen.pq.search_query, gen.blocks, answer_format=gen.pq.answer_format
            ):
                parts.append(token)
                yield {"type": "token", "text": token}
            answer = faithfulness.validate_markers("".join(parts), len(gen.blocks))

        result = _assemble(answer, gen)
        s.set("answer_chars", len(answer))
        yield {
            "type": "sources",
            "citations": result["citations"],
            "intent": result["intent"],
            "answer_format": result["answer_format"],
            "used_chunks": result["used_chunks"],
            "conflict": result["conflict"],
        }
        yield {"type": "done"}
        _persist(gen, result)
        _record(s, result, stages)


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
        filters=pq.filters, n=top_k, answer_format=pq.answer_format,
        source_type=pq.source_type,
    )
    return {
        "intent": pq.intent,
        "answer_format": pq.answer_format,
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
