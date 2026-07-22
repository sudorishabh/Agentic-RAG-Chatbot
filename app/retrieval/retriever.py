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

logger = logging.getLogger(__name__)


def supplement_attachments(
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
    intent: str = "qa",
) -> list[ContextBlock]:
    settings = get_settings()
    n = n or settings.retrieval_top_k
    user_groups = user_groups or ["public"]

    # Prefer website content only when the feature is on, the user didn't pin a
    # source (explicit intent → honor their filter with a single pull, else the
    # PDF pull's "not website" would contradict a website filter), and the answer
    # isn't a table (tables live in PDFs — don't force a website lead).
    dual = bool(settings.prefer_website_enabled) and not source_type and answer_format != "table"
    # Multi-query only where recall expansion helps: plain qa, no explicit
    # scope already narrowing the pull, and enough words that paraphrases can
    # actually diverge (short factoids are already unambiguous).
    multi = (
        bool(settings.multi_query_enabled)
        and intent == "qa"
        and not source_type
        and not filters
        and len(search_query.split()) >= 5
    )

    if query_vector is None:
        with span("rag.embed_query"):
            query_vector = embed_query(search_query)

    def _base_search() -> list[Any]:
        if dual:
            return dual_search(
                search_query, tenant_id=tenant_id, user_groups=user_groups,
                filters=filters, query_vector=query_vector, settings=settings,
            )
        return search(
            search_query,
            limit=settings.retrieval_candidate_k,
            tenant_id=tenant_id,
            user_groups=user_groups,
            extra_filter=filters or None,
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
                base_future = pool.submit(_base_search)
                keyword_future = (
                    pool.submit(
                        keyword_search, search_query, keyword_terms,
                        tenant_id=tenant_id, user_groups=user_groups,
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
                                    q, tenant_id=tenant_id, user_groups=user_groups,
                                    limit=settings.retrieval_candidate_k,
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
            candidates = _base_search()
        s.set("candidates", len(candidates))

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
            ranked = corrective_requery(
                search_query, ranked, tenant_id=tenant_id, user_groups=user_groups,
                filters=filters, limit=settings.retrieval_candidate_k,
                table_boost=table_boost,
            )
            s.set("survivors", len(ranked))
    if not ranked:
        return []
    with span("rag.context_build"):
        blocks = build_context(ranked, limit=n, segregate=dual)
    if answer_format == "detailed" and blocks:
        with span("rag.attachment_pull"):
            blocks = supplement_attachments(
                blocks, ranked, search_query=search_query, query_vector=query_vector,
                tenant_id=tenant_id, user_groups=user_groups, n=n, segregate=dual,
            )
    return blocks
