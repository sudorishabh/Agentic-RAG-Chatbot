"""Recall-expansion retrieval strategies.

Each function is one optional pull layered on top of the base dense search, fused
back in by ``retriever.retrieve``. They call the shared LLM / embedding gateways
in :mod:`app.core.clients` directly — retrieval never depends on the generation
package for these.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.core.clients.embeddings import embed_query
from app.core.clients.llm import get_llm, get_structured_llm
from app.retrieval.fusion import rrf
from app.retrieval.hybrid_search import search
from app.retrieval.reranker import rerank

logger = logging.getLogger(__name__)


def dual_search(
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


_PARAPHRASE_SYSTEM = (
    "Rewrite the search query as alternative phrasings that could retrieve "
    "relevant passages a literal match might miss. Vary the wording and "
    "specificity; keep the meaning; do not add facts or constraints.\n"
    "Example: 'impact of biofuel adoption on rural incomes' -> "
    "['how biofuels affect farmer earnings in rural areas', "
    "'economic effects of biofuel programmes on village households']"
)


def paraphrases(search_query: str, n: int) -> list[str]:
    """LLM paraphrases of the query for the multi-query pull; [] on failure."""
    from pydantic import BaseModel

    class Paraphrases(BaseModel):
        queries: list[str] = []

    try:
        # Diversity is the point here, so temperature ~0.7 (not the pinned
        # parsing temperature).
        model = get_llm(temperature=0.7).with_structured_output(Paraphrases)
        result: Paraphrases = model.invoke(
            [
                ("system", _PARAPHRASE_SYSTEM),
                ("human", f"Give {n} paraphrases of: {search_query}"),
            ]
        )
        cleaned = [q.strip() for q in result.queries if q and q.strip()]
        return [q for q in cleaned if q.lower() != search_query.lower()][:n]
    except Exception:
        logger.warning("Paraphrase generation failed; base query only.", exc_info=True)
        return []


def paraphrase_search(
    query: str, *, tenant_id: str, user_groups: list[str], limit: int
) -> list[Any]:
    """One paraphrase's dense pull (cached embed); [] on failure."""
    try:
        return search(
            query, limit=limit, tenant_id=tenant_id, user_groups=user_groups,
            query_vector=embed_query(query),
        )
    except Exception:
        logger.warning("Paraphrase search failed for %r.", query, exc_info=True)
        return []


_CORRECTIVE_SYSTEM = (
    "The retrieved passages may not answer the question. Suggest ONE "
    "reformulated search query targeting the missing information: change the "
    "wording or angle toward what the passages lack; keep the original "
    "meaning; do not add facts.\n"
    "Example: question 'what did the report say about coastal erosion "
    "funding' with passages about erosion science but nothing on budgets -> "
    "'budget allocation for coastal erosion protection programmes'."
)


def corrective_query(search_query: str, ranked: list[Any]) -> str | None:
    """One structured reformulation aimed at what the weak results missed;
    None when it fails or merely echoes the original."""
    from pydantic import BaseModel

    class Reformulation(BaseModel):
        query: str = ""

    snippets = "\n".join(f"- {c.text[:200]}" for c in ranked[:3] if c.text)
    try:
        result: Reformulation = (
            get_structured_llm()
            .with_structured_output(Reformulation)
            .invoke(
                [
                    ("system", _CORRECTIVE_SYSTEM),
                    ("human", f"Question: {search_query}\n\n"
                              f"Best passages so far:\n{snippets or '(none)'}"),
                ]
            )
        )
    except Exception:
        logger.warning("Corrective reformulation failed.", exc_info=True)
        return None
    query = (result.query or "").strip()
    if not query or query.lower() == search_query.lower():
        return None
    return query


def corrective_requery(
    search_query: str,
    ranked: list[Any],
    *,
    tenant_id: str,
    user_groups: list[str],
    filters: list[Any] | None,
    limit: int,
    table_boost: float,
) -> list[Any]:
    """One-shot corrective retrieval: reformulate, search once, RRF-fuse with
    the current ranking, rerank once more. Strictly one iteration; any failure
    or empty gain keeps the original ranking."""
    try:
        reformulated = corrective_query(search_query, ranked)
        if not reformulated:
            return ranked

        extra = search(
            reformulated, limit=limit, tenant_id=tenant_id, user_groups=user_groups,
            extra_filter=filters or None,
            query_vector=embed_query(reformulated),
        )
        seen = {c.id for c in ranked}
        if not any(c.id not in seen for c in extra):
            return ranked
        return rerank(search_query, rrf([ranked, extra]), table_boost=table_boost)
    except Exception:
        logger.warning("Corrective requery failed; keeping original ranking.",
                       exc_info=True)
        return ranked


# Salient-term patterns for the keyword leg: the query features dense vectors
# handle worst — exact phrases, acronyms, years, proper nouns.
_QUOTED = re.compile(r"\"([^\"]{2,})\"|'([^']{2,})'")
_CAP_BIGRAM = re.compile(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b")
_ACRONYM = re.compile(r"\b[A-Z]{2,}\b")
_YEAR = re.compile(r"\b\d{4}\b")


def extract_key_terms(query: str) -> str | None:
    """Deterministic salient terms for a MatchText pull; None when the query
    has none (the keyword leg is skipped, not run over stopwords)."""
    terms: list[str] = [m.group(1) or m.group(2) for m in _QUOTED.finditer(query)]
    terms.extend(_CAP_BIGRAM.findall(query))
    terms.extend(_ACRONYM.findall(query))
    terms.extend(_YEAR.findall(query))
    unique: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if term.lower() not in seen:
            seen.add(term.lower())
            unique.append(term)
    return " ".join(unique) or None


def keyword_search(
    search_query: str,
    terms_text: str,
    *,
    tenant_id: str,
    user_groups: list[str],
    filters: list[Any] | None,
    query_vector: list[float],
    limit: int,
) -> list[Any]:
    """One MatchText-filtered pull (dense ranking within keyword matches).
    Fails open to [] — notably while the chunk_text full-text index doesn't
    exist yet (scripts/create_fulltext_index.py)."""
    try:
        from qdrant_client.models import FieldCondition, MatchText

        cond = FieldCondition(key="chunk_text", match=MatchText(text=terms_text))
        return search(
            search_query, limit=limit, tenant_id=tenant_id, user_groups=user_groups,
            extra_filter=list(filters or []) + [cond], query_vector=query_vector,
        )
    except Exception:
        logger.debug("Keyword leg unavailable; dense-only.", exc_info=True)
        return []
