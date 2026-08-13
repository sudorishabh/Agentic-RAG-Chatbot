"""The query→answer pipeline.

Shared front-matter (``_prepare``: query understanding, structured/summary
shortcuts, caches, retrieval) feeds both the streaming ``stream_answer`` entry
point and the retrieval-only ``search_blocks``. Answer generation is delegated to
:mod:`app.generation.answerer`; retrieval to :mod:`app.retrieval.retriever`.

Span labels stay ``rag.*`` — they are the stable metric-stage contract, not
import paths.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterator

from app.config import get_settings
from app.core.models.context import ContextBlock
from app.generation.answerer import chitchat, generate_answer, generate_stream
from app.generation.prompts import REFUSAL
from app.observability.metrics import collect_into, component_totals
from app.observability.tracing import record_query_metrics, span
from app.retrieval.citations import build_citations
from app.retrieval.query_processor import ProcessedQuery, process
from app.retrieval.retriever import retrieve

logger = logging.getLogger(__name__)


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


@dataclass
class _Generation:
    """What the answer step needs after the shared front-matter (query
    understanding, cache lookups, retrieval) has decided a fresh grounded answer
    must be generated. Carried out of `_prepare` so the buffered and streaming
    entrypoints share one pipeline and differ only in how they emit the answer."""

    pq: ProcessedQuery
    blocks: list[ContextBlock]
    query_vector: list[float]
    top_k: int
    # Deterministic catalog section prefixed onto a combined (database + content)
    # answer; "" for single-source answers.
    db_prefix: str = ""


# Content capabilities that pair with a database lookup into a combined answer.
_CONTENT_CAPS = frozenset({"qa", "comparison"})


def _capabilities(pq: ProcessedQuery) -> set[str]:
    """The detected multi-label intents (empty on the passthrough fallback)."""
    if pq.understanding is None:
        return set()
    return {p.label for p in pq.understanding.intents}


def _db_section(
    pq: ProcessedQuery, question: str, history: list[dict[str, str]] | None
) -> str:
    """Deterministic catalog answer to prefix onto a combined (database + content)
    response, reusing the already-extracted slots (no second LLM parse). '' when
    there is nothing to add. Owns its ``rag.db_section`` span so the timing is
    still recorded when this runs off the main thread (see ``_prepare``)."""
    with span("rag.db_section"):
        if pq.analysis is None or not pq.analysis.operation:
            return ""
        from app.retrieval.structured.answerer import answer_structured

        structured = answer_structured(question, history, analysis=pq.analysis)
        return structured["answer"] if structured else ""


def _catalog_listing(pq: ProcessedQuery, question: str) -> dict[str, Any] | None:
    """The catalog's take on a content question retrieval could not ground, or None
    to refuse as before.

    Framed with `NO_CONTENT_WITH_CATALOG` so a list of titles is never mistaken for
    the substance asked for. Fail-open by construction: this runs on a path that is
    already about to refuse, so a catalog error must degrade to that refusal rather
    than turn it into a 500."""
    from app.generation.prompts import NO_CONTENT_WITH_CATALOG
    from app.retrieval.structured.answerer import catalog_fallback

    with span("rag.catalog_fallback") as s:
        try:
            result = catalog_fallback(question, analysis=pq.analysis)
        except Exception:
            logger.warning("Catalog fallback failed; refusing instead.", exc_info=True)
            return None
        s.set("hit", result is not None)
    if result is None:
        return None
    # `intent` stays the question's own: a qa query answered from catalog rows is
    # still a qa query, and relabelling it would distort the intent metrics.
    return {
        **result,
        "answer": f"{NO_CONTENT_WITH_CATALOG}\n\n{result['answer']}",
        "intent": pq.intent,
        "answer_format": pq.answer_format,
    }


def _prepare(
    question: str,
    *,
    history: list[dict[str, str]] | None,
    top_k: int | None,
) -> tuple[dict[str, Any] | None, _Generation | None]:
    """Shared front-matter for both answer entrypoints.

    Returns ``(result, None)`` when a complete answer is already available (a
    response- or semantic-cache hit, chit-chat, a structured lookup, or a
    no-context refusal), or ``(None, generation)`` when a grounded answer still
    has to be generated.
    """
    from app.cache import semantic_cache
    from app.core.clients.embeddings import embed_query

    settings = get_settings()
    n = top_k or settings.retrieval_top_k

    with span("rag.query_understanding"):
        pq: ProcessedQuery = process(question, history)
    if pq.intent == "chitchat":
        return _empty("chitchat", chitchat(question, history)), None

    caps = _capabilities(pq)
    # A query that needs both catalog facts and document content: keep the
    # deterministic catalog answer and prefix it onto the grounded content answer.
    combined = "database" in caps and bool(caps & _CONTENT_CAPS)
    chained = False
    # Whether the catalog has already been asked about this query, so the
    # empty-retrieval fallback at the end doesn't re-run a query that just came
    # back with nothing. `combined` asks it via `_db_section` below.
    #
    # Deliberately not set for a scoped_summary that fell through: it returns None
    # both for a scope-less request and for one whose documents held no summarizable
    # text, and in the latter case a listing of those documents is exactly what is
    # worth showing. When the scope was genuinely empty the listing comes back empty
    # too, so the redundant case costs one query on a path that is already refusing.
    db_consulted = combined

    if pq.intent == "structured":
        from app.retrieval.structured.answerer import answer_structured
        from app.retrieval.structured.tools import resolve_lookup_chain

        chain_id = resolve_lookup_chain(pq.analysis, question)
        if chain_id is not None:
            # Content question about one named title: answer from that document's
            # chunks (QA path below) instead of title+URL.
            from qdrant_client.models import FieldCondition, MatchValue

            pq.filters.append(
                FieldCondition(key="document_id", match=MatchValue(value=chain_id))
            )
            chained = True
            # The chain came out of a catalog title lookup, so the catalog has
            # already placed this document; only its content is missing.
            db_consulted = True
        elif not combined:
            # Database-only: the deterministic catalog answer is complete.
            structured = answer_structured(question, history, analysis=pq.analysis)
            db_consulted = True
            if structured is not None:
                structured.setdefault("answer_format", pq.answer_format)
                return structured, None

    if pq.intent == "scoped_summary":
        from app.pipeline.summarize import summarize_scope

        with span("rag.scoped_summary"):
            summary = summarize_scope(pq.analysis)
        if summary is not None:
            summary.setdefault("answer_format", pq.answer_format)
            return summary, None
        # Empty/unresolvable scope: fall through to plain semantic QA.

    with span("rag.embed_query"):
        query_vector = embed_query(pq.search_query)
    with span("rag.semantic_cache") as s:
        semantic = semantic_cache.lookup(
            query_vector, top_k=n, answer_format=pq.answer_format,
            fingerprint=semantic_cache.facet_fingerprint(pq),
        )
        s.set("hit", semantic is not None)
    if semantic is not None:
        # A cached combined answer already carries its catalog section, so the
        # short-circuit here also skips rebuilding it.
        return {**semantic, "cached": True}, None

    def _run_retrieve() -> list[ContextBlock]:
        return retrieve(
            pq.search_query,
            filters=pq.filters,
            n=n,
            query_vector=query_vector,
            answer_format=pq.answer_format,
            source_type=pq.source_type,
            capabilities=caps,
        )

    # The deterministic catalog section (combined queries only) and content
    # retrieval are independent, so overlap them and pay the slower of the two
    # rather than their sum. copy_context() keeps the worker's span in this
    # request's stage breakdown; single-source queries skip the pool entirely.
    if combined and not chained:
        from concurrent.futures import ThreadPoolExecutor
        from contextvars import copy_context

        with ThreadPoolExecutor(max_workers=1) as pool:
            db_future = pool.submit(
                copy_context().run, _db_section, pq, question, history
            )
            blocks = _run_retrieve()
            db_prefix = db_future.result()
    else:
        db_prefix = ""
        blocks = _run_retrieve()

    if not blocks:
        # Combined query whose content retrieval came up empty: still return the
        # deterministic catalog answer rather than a blanket refusal.
        if db_prefix:
            return _empty(pq.intent, db_prefix, answer_format=pq.answer_format), None
        # Retrieval found nothing to ground an answer. Ask the catalog — which
        # indexes titles and facets rather than passages — but only when it hasn't
        # already answered nothing for this query.
        if not db_consulted:
            listing = _catalog_listing(pq, question)
            if listing is not None:
                return listing, None
        return _empty(pq.intent, REFUSAL, answer_format=pq.answer_format), None

    return None, _Generation(
        pq=pq, blocks=blocks, query_vector=query_vector,
        top_k=n, db_prefix=db_prefix,
    )


def _cited_blocks(body: str, blocks: list[ContextBlock]) -> list[ContextBlock]:
    """The blocks the answer actually cites.

    The sources footer lists what the answer used, not everything retrieval
    pulled: a block the answer left out — an off-topic PDF the model rightly
    dropped, say — must not resurface as a chip contradicting the answer above
    it. Falls back to every block when the answer cites nothing (or cites only
    blocks that are somehow absent), so provenance is never silently lost.
    """
    from app.generation.faithfulness import extract_markers

    cited = extract_markers(body)
    if not cited:
        return blocks
    return [b for b in blocks if b.n in cited] or blocks


def _assemble(answer: str, gen: _Generation) -> dict[str, Any]:
    from app.generation import faithfulness
    from app.generation.sections import strip_tags

    # The block wrappers are presentation, so every pass that reads the answer as
    # content works from the tag-free body.
    body = strip_tags(answer)
    # Deterministic numeric check (~0 ms): observe-only in v1 — flagged and
    # logged, never auto-corrected.
    mismatches = faithfulness.numeric_mismatches(body, gen.blocks)
    if mismatches:
        logger.info("Numeric claims not found in cited blocks: %s", mismatches)
    # The catalog section is deterministic (not from the blocks), so faithfulness
    # and numeric checks run on the grounded content only; compose for display.
    final = f"{gen.db_prefix}\n\n{answer}" if gen.db_prefix else answer
    return {
        "answer": final,
        "citations": [
            c.model_dump() for c in build_citations(_cited_blocks(body, gen.blocks))
        ],
        "intent": gen.pq.intent,
        "answer_format": gen.pq.answer_format,
        "used_chunks": len(gen.blocks),
        "conflict": any(b.conflict for b in gen.blocks),
        "numeric_mismatch": bool(mismatches),
        "cached": False,
    }


def _persist(gen: _Generation, result: dict[str, Any]) -> None:
    from app.cache import semantic_cache

    with span("rag.semantic_cache_store"):
        semantic_cache.store(
            gen.query_vector, result, top_k=gen.top_k,
            answer_format=gen.pq.answer_format,
            fingerprint=semantic_cache.facet_fingerprint(gen.pq),
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
        numeric_mismatch=result.get("numeric_mismatch") or None,  # logged only when set
        components=component_totals(stages) if stages else None,
        stages={k: round(v, 1) for k, v in stages.items()} if stages else None,
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
        "numeric_mismatch": result.get("numeric_mismatch", False),
    }
    yield {"type": "done"}


def stream_answer(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    top_k: int | None = None,
) -> Iterator[dict[str, Any]]:
    # Spans after the first yield only reach the global aggregates, not this
    # dict — the SSE driver resumes the generator in fresh contexts (see
    # metrics.collect_into) — so the logged breakdown covers the pre-token
    # stages, which is where retrieval time goes.
    stages: dict[str, float] = {}
    with collect_into(stages), span("rag.stream_answer") as s:
        result, gen = _prepare(question, history=history, top_k=top_k)
        # Cache hit, chit-chat, structured lookup, or refusal — already complete.
        if result is not None:
            yield from _stream_result(result)
            _record(s, result, stages)
            return

        from app.generation import faithfulness
        from app.generation.sections import strip_tags

        parts: list[str] = []
        # Combined answer: stream the deterministic catalog section first, then
        # the grounded content answer.
        if gen.db_prefix:
            yield {"type": "token", "text": gen.db_prefix + "\n\n"}
        for token in generate_stream(
            gen.pq.search_query, gen.blocks,
            history=history, answer_format=gen.pq.answer_format,
        ):
            parts.append(token)
            yield {"type": "token", "text": token}
        answer = faithfulness.validate_markers("".join(parts), len(gen.blocks))

        if get_settings().faithfulness_check:
            # Post-hoc verify: tokens streamed at full speed above; an
            # unfaithful answer gets one regeneration emitted as a correction
            # event, and the corrected version is what gets cached below.
            with span("rag.faithfulness") as fs:
                report = faithfulness.verify(strip_tags(answer), gen.blocks)
                fs.set("faithful", report.faithful)
            if not report.faithful:
                logger.info("Streamed answer flagged unfaithful; correcting once.")
                try:
                    retry = generate_answer(
                        gen.pq.search_query, gen.blocks,
                        history=history,
                        correction=report.correction_note(),
                        answer_format=gen.pq.answer_format,
                    )
                    corrected = faithfulness.validate_markers(retry, len(gen.blocks))
                except Exception:
                    logger.warning("Correction regeneration failed; keeping "
                                   "the streamed answer.", exc_info=True)
                    corrected = ""
                if corrected and corrected != answer:
                    answer = corrected
                    yield {
                        "type": "correction",
                        "text": f"{gen.db_prefix}\n\n{corrected}" if gen.db_prefix else corrected,
                        "reason": "faithfulness",
                    }

        result = _assemble(answer, gen)
        s.set("answer_chars", len(answer))
        yield {
            "type": "sources",
            "citations": result["citations"],
            "intent": result["intent"],
            "answer_format": result["answer_format"],
            "used_chunks": result["used_chunks"],
            "conflict": result["conflict"],
            "numeric_mismatch": result["numeric_mismatch"],
        }
        yield {"type": "done"}
        _persist(gen, result)
        _record(s, result, stages)


def search_blocks(
    question: str,
    *,
    history: list[dict[str, str]] | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    pq = process(question, history)
    blocks = retrieve(
        pq.search_query,
        filters=pq.filters, n=top_k, answer_format=pq.answer_format,
        source_type=pq.source_type, capabilities=_capabilities(pq),
    )
    return {
        "intent": pq.intent,
        "answer_format": pq.answer_format,
        "search_query": pq.search_query,
        "intents": [
            {"label": p.label, "confidence": p.confidence, "rationale": p.rationale}
            for p in (pq.understanding.intents if pq.understanding else [])
        ],
        "is_ambiguous": pq.is_ambiguous,
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
