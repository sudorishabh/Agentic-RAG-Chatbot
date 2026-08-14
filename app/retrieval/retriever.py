"""Retrieval orchestration.

Turns a processed search query into the final ordered ``ContextBlock`` list:
picks the base pull (plain or website-biased dual), fans out the optional
recall-expansion legs (multi-query, keyword) and fuses them, reranks, runs the
optional corrective loop, builds context, and supplements attachments for
detailed answers. Lifted out of the old ``app.rag`` god module.

Span labels stay ``rag.*`` — they are the stable metric-stage contract consumed
by observability/metrics (see docs/operations.md), not import paths.
"""
from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.core.clients.embeddings import embed_query
from app.core.models.context import ContextBlock
from app.observability.tracing import span
from app.retrieval.context_builder import build_context
from app.retrieval.fusion import rrf
from app.retrieval.hybrid_search import search
from app.retrieval.reranker import rerank
from app.retrieval.search.strategies import (
    corrective_requery,
    dual_search,
    extract_key_terms,
    keyword_search,
    paraphrase_search,
    paraphrases,
)
from app.retrieval.understanding.filters import date_conditions

logger = logging.getLogger(__name__)

# `retrieve` is the retrieval engine's sole public entry point; the stages it
# composes here (and in app.retrieval.search.strategies) are internal and free
# to change. The rest of the app depends only on this name.
__all__ = ["retrieve"]

# Content capabilities (from query understanding) whose open-ended search
# benefits from multi-query recall expansion; a pure `database` lookup does not.
_MULTI_QUERY_INTENTS = frozenset({"qa", "comparison"})


def _supplement_attachments(
    blocks: list[ContextBlock],
    ranked: list[Any],
    *,
    search_query: str,
    query_vector: list[float],
    n: int,
    segregate: bool,
) -> list[ContextBlock]:
    """Detailed answers: when admitted website blocks have attached PDFs that
    contributed nothing to the context, pull those attachments' chunks once and
    let rerank decide admission. Bounded to one extra Qdrant query; any failure
    keeps the original blocks."""
    from app.catalog import queries as catalog
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
        extra = search_within_documents(query_vector, file_uuids, limit=10)
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


def _observe_in_shadow(search_query: str, blocks: list[ContextBlock]) -> None:
    """Hand the question to graph shadow mode, if it is enabled.

    Deliberately the only contact production retrieval has with the graph, and
    it is one-way: the call returns nothing, runs its work on a background
    thread, and swallows every error, so neither the blocks above nor the
    latency of this request can be affected by it.

    The import is local so that with the flag off — the default — the graph
    package is never even loaded.
    """
    from app.config import get_settings

    if not getattr(get_settings(), "graph_shadow_enabled", False):
        return
    try:
        from app.retrieval.graph import shadow

        shadow.observe(search_query, blocks)
    except Exception:  # pragma: no cover - defence in depth
        logger.warning("Graph shadow hook failed.", exc_info=True)


def retrieve(
    search_query: str,
    *,
    filters: list[Any] | None = None,
    n: int | None = None,
    query_vector: list[float] | None = None,
    answer_format: str | None = None,
    source_type: str | None = None,
    capabilities: set[str] | None = None,
) -> list[ContextBlock]:
    settings = get_settings()
    n = n or settings.retrieval_top_k

    # Prefer website content only when the feature is on, the user didn't pin a
    # source (explicit intent → honor their filter with a single pull, else the
    # PDF pull's "not website" would contradict a website filter), and the answer
    # isn't a table (tables live in PDFs — don't force a website lead).
    dual = bool(settings.prefer_website_enabled) and not source_type and answer_format != "table"
    # Multi-query only where recall expansion helps: an open-ended content
    # search (not a pure structured lookup), no explicit scope already narrowing
    # the pull, and enough words that paraphrases can actually diverge (short
    # factoids are already unambiguous). The capabilities come from query
    # understanding; an empty set (the degraded passthrough) is treated as QA.
    content_search = not capabilities or bool(capabilities & _MULTI_QUERY_INTENTS)
    multi = (
        bool(settings.multi_query_enabled)
        and content_search
        and not source_type
        and not filters
        and len(search_query.split()) >= 5
    )

    if query_vector is None:
        with span("rag.embed_query"):
            query_vector = embed_query(search_query)

    def _base_search(active_filters: list[Any] | None, *, use_dual: bool) -> list[Any]:
        if use_dual:
            return dual_search(
                search_query, filters=active_filters,
                query_vector=query_vector, settings=settings,
            )
        return search(
            search_query,
            limit=settings.retrieval_candidate_k,
            extra_filter=active_filters or None,
            query_vector=query_vector,
        )

    keyword_terms = (
        extract_key_terms(search_query) if settings.keyword_leg_enabled else None
    )

    with span("rag.search") as s:
        if multi or keyword_terms:
            from concurrent.futures import ThreadPoolExecutor

            rankings: list[list[Any]] = []
            # Paraphrase generation and the keyword pull overlap the base
            # pull, so the added wall-clock is only the paraphrase searches
            # that follow the generation step.
            with ThreadPoolExecutor(max_workers=4) as pool:
                base_future = pool.submit(_base_search, filters, use_dual=dual)
                keyword_future = (
                    pool.submit(
                        keyword_search, search_query, keyword_terms,
                        filters=filters, query_vector=query_vector,
                        limit=settings.retrieval_candidate_k,
                    )
                    if keyword_terms
                    else None
                )
                if multi:
                    with span("rag.multi_query") as mq:
                        queries = pool.submit(
                            paraphrases, search_query, settings.multi_query_paraphrases
                        ).result()
                        rankings.extend(
                            r
                            for r in pool.map(
                                lambda q: paraphrase_search(
                                    q, limit=settings.retrieval_candidate_k,
                                ),
                                queries,
                            )
                            if r
                        )
                        mq.set("paraphrases", len(queries))
                if keyword_future is not None:
                    with span("rag.keyword_leg") as kw:
                        keyword_hits = keyword_future.result()
                        kw.set("hits", len(keyword_hits))
                    if keyword_hits:
                        rankings.append(keyword_hits)
                base = base_future.result()
            candidates = rrf([base] + rankings) if rankings else base
        else:
            candidates = _base_search(filters, use_dual=dual)
        s.set("candidates", len(candidates))

    # Facet filters (theme / author / source_type) are LLM-extracted and applied
    # as hard AND conditions. When they lift terms straight out of the question —
    # a title query parsed into theme="SDG 7", author="TERI" — those literals
    # rarely equal the stored metadata, and their intersection can be empty even
    # when the corpus plainly answers the question. A total miss under facets is
    # never better than the plain semantic pull, so retry once without them
    # rather than refusing. Precision-preserving: only fires on zero, so a
    # non-empty facet-scoped result is left exactly as-is.
    #
    # A date scope survives the retry (see `date_conditions`): the facets are
    # guesses at the corpus's labelling, but the period is the user's own
    # constraint, and answering "reports from 2023" out of 2019 is worse than
    # answering nothing — the more so because the widening is invisible, recorded
    # on the span below and never in the answer. When the window genuinely holds
    # no chunks, empty is honest and the pipeline's refusal path is correct —
    # which is also why an all-dates filter set skips the retry outright: it would
    # re-run the pull that just came back empty.
    kept = date_conditions(filters)
    if not candidates and filters and len(kept) < len(filters):
        with span("rag.search_relaxed") as s:
            relaxed_dual = bool(settings.prefer_website_enabled) and answer_format != "table"
            candidates = _base_search(kept or None, use_dual=relaxed_dual)
            s.set("candidates", len(candidates))
            s.set("relaxed", True)
            s.set("kept_date_scope", bool(kept))
        logger.info(
            "Facet filters matched no chunks; retried without facets%s (%d candidates).",
            " but within the date scope" if kept else "", len(candidates),
        )

    with span("rag.rerank") as s:
        table_boost = settings.rerank_table_boost if answer_format == "table" else 0.0
        ranked = rerank(search_query, candidates, table_boost=table_boost)
        s.set("survivors", len(ranked))
    if (
        bool(settings.corrective_loop_enabled)
        and ranked
        and ranked[0].semantic_score < settings.corrective_min_score
    ):
        with span("rag.corrective") as s:
            score_before = ranked[0].semantic_score
            ranked = corrective_requery(
                search_query, ranked,
                filters=filters, limit=settings.retrieval_candidate_k,
                table_boost=table_boost,
            )
            score_after = ranked[0].semantic_score if ranked else 0.0
            # Did the retry actually lift the top result? Recorded so we can
            # later judge whether the corrective loop earns its extra LLM +
            # search cost before tuning or removing it.
            s.set("survivors", len(ranked))
            s.set("score_before", round(score_before, 4))
            s.set("score_after", round(score_after, 4))
            s.set("improved", score_after > score_before)
            logger.info(
                "corrective loop: top score %.4f -> %.4f (%s)",
                score_before, score_after,
                "improved" if score_after > score_before else "no gain",
            )
    if not ranked:
        _observe_in_shadow(search_query, [])
        return []
    with span("rag.context_build"):
        blocks = build_context(ranked, limit=n, segregate=dual)
    if answer_format == "detailed" and blocks:
        with span("rag.attachment_pull"):
            blocks = _supplement_attachments(
                blocks, ranked, search_query=search_query, query_vector=query_vector,
                n=n, segregate=dual,
            )
    _observe_in_shadow(search_query, blocks)
    return blocks
