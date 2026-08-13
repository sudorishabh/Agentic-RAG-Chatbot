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
        extra_filter=base + [website_cond],
        query_vector=query_vector,
    )
    others = search(
        search_query,
        limit=settings.retrieval_candidate_k,
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
    query: str, *, limit: int
) -> list[Any]:
    """One paraphrase's dense pull (cached embed); [] on failure."""
    try:
        return search(
            query, limit=limit, query_vector=embed_query(query),
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
            reformulated, limit=limit, extra_filter=filters or None,
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
# handle worst — exact phrases, acronyms, alphanumeric codes, years, proper nouns.
_QUOTED = re.compile(r"\"([^\"]{2,})\"|'([^']{2,})'")
_CAP_BIGRAM = re.compile(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b")
# An acronym, optionally carrying the number that qualifies it: SDG 7, COP26.
# The number is part of the term because "SDG" alone matches every one of them.
_ACRONYM = re.compile(r"\b([A-Z]{2,}(?:[ -]?\d+)?)\b")
# A token mixing letters and digits — PM2.5, CO2, 1.5C. Dense embeddings blur
# these into their nearest word; they are exact by nature.
_ALNUM = re.compile(r"\b([A-Za-z]+\d+(?:\.\d+)?[A-Za-z]*)\b")
_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")

# Words that carry no retrieval signal. Small and deliberately conservative:
# this list only has to strip the scaffolding of a question, since the content
# fallback below is a last resort rather than the primary source of terms.
_STOPWORDS = frozenset(
    """
    a an and are as at be been by can could did do does for from had has have how
    in into is it its me my of on or say says should show that the their there
    these this those to us was were what when where which who whom whose why will
    with would you your about after before between during over under more most
    tell give find list
    """.split()
)
# Lowercase content words, used only when nothing more precise was found. Three
# characters is the floor rather than four: "air" and "gas" name whole domains
# in this corpus, and dropping them lost the point of the phrase.
_CONTENT = re.compile(r"\b([a-z][a-z-]{2,})\b")


def extract_key_terms(query: str) -> list[str] | None:
    """Deterministic salient terms for the keyword pull; None when the query has
    none at all.

    Ordered most to least precise. The lowercase content-word pass is a
    *fallback*, reached only when no quoted phrase, proper noun, acronym, code
    or year was found — because a query like "life cycle analysis of transport
    modes" names something exactly without capitalising any of it, and skipping
    the leg entirely there was the single biggest hole in the lexical path.
    Running it alongside the precise patterns instead would drown them in
    ordinary vocabulary.
    """
    terms: list[str] = [m.group(1) or m.group(2) for m in _QUOTED.finditer(query)]
    terms.extend(_CAP_BIGRAM.findall(query))
    terms.extend(_ALNUM.findall(query))
    terms.extend(_ACRONYM.findall(query))
    terms.extend(_YEAR.findall(query))
    if not terms:
        terms = [
            word for word in _CONTENT.findall(query.lower())
            if word not in _STOPWORDS
        ]
    unique: list[str] = []
    seen: set[str] = set()
    for term in terms:
        cleaned = term.strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            unique.append(cleaned)
    # Drop any term that is merely the opening of another one already kept. The
    # patterns overlap by design — "PM2.5" is also read as the acronym "PM2",
    # and "SDG 7" as the acronym "SDG" — and the shorter form is always the
    # less selective of the two.
    return [
        term
        for term in unique
        if not any(
            other != term and other.lower().startswith(term.lower())
            for other in unique
        )
    ] or None


def keyword_search(
    search_query: str,
    terms: list[str],
    *,
    filters: list[Any] | None,
    query_vector: list[float],
    limit: int,
) -> list[Any]:
    """One MatchText-filtered pull (dense ranking within keyword matches).

    The terms are OR-ed, one ``MatchText`` each. A single ``MatchText`` carrying
    several words is an AND across all of them, which made the leg brittle in
    exactly the case it exists for: "Emission Inventorisation for Faridabad
    Town" returned nothing, because no one chunk held all four words. OR-ing
    degrades toward the dense pull instead of collapsing to zero, and the
    ranking within the matched set is still dense similarity.

    Fails open to [] — notably while the chunk_text full-text index doesn't
    exist yet (scripts/create_fulltext_index.py).
    """
    if not terms:
        return []
    try:
        from qdrant_client.models import FieldCondition, Filter, MatchText

        cond = Filter(
            should=[
                FieldCondition(key="chunk_text", match=MatchText(text=term))
                for term in terms
            ]
        )
        return search(
            search_query, limit=limit,
            extra_filter=list(filters or []) + [cond], query_vector=query_vector,
        )
    except Exception:
        logger.debug("Keyword leg unavailable; dense-only.", exc_info=True)
        return []
