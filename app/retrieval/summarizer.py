"""Scoped summarization: map-reduce over a catalog-selected document set.

"Summarize the Climate theme / 2024 publications" cannot be served by
similarity search — the user defined a SET, not a topic. MySQL selects the
set (newest first, capped), Qdrant supplies each document's lead parent
chunk, and GPT-4o-mini summarizes hierarchically: per-document bullets in
parallel batches (map), then one aggregation call (reduce). Small scopes skip
the map stage entirely. Citations are document-level catalog rows. Any
failure returns None — the caller falls through to plain semantic RAG.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Sequence

from pydantic import BaseModel, Field

from app.ingestion import terms
from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES
from app.retrieval import catalog, scoped_retrieval
from app.retrieval.drupal_router import _normalize_bundle
from app.schemas.query import Citation

if TYPE_CHECKING:
    from app.retrieval.query_processor import QueryAnalysis

logger = logging.getLogger(__name__)

_SCOPE_DOC_CAP = 30      # v1 cap; plan §13.7 raises it with a two-level reduce
_DIRECT_DOC_LIMIT = 5    # <= this many docs: one grounded call, no map stage
_MAP_BATCH_TOKENS = 6000
_MAP_WORKERS = 4

_DIRECT_SYSTEM = (
    "You summarize a small collection of documents given as numbered context "
    "blocks. Use ONLY the blocks; cite the block number [n] after every claim "
    "it supports; do not add outside facts. Write one cohesive overview of "
    "the set — its main threads and notable specifics — not a per-document "
    "recap."
)

_MAP_SYSTEM = (
    "You summarize documents for a downstream aggregation step. For EACH "
    "input document, produce 2-3 short factual bullets strictly from its own "
    "text — no outside knowledge, no speculation, numbers copied exactly. "
    "Return one entry per document with its document_id copied verbatim.\n"
    "Example input:\n"
    "document_id: abc-1\ntitle: Rooftop solar in Delhi\ntext: The programme "
    "added 1.2 GW of rooftop capacity in 2023, led by commercial "
    "installations across three districts...\n"
    "Example output entry: document_id='abc-1', bullets=['Rooftop programme "
    "added 1.2 GW of capacity in 2023', 'Commercial installations led "
    "adoption across three districts']"
)

_REDUCE_SYSTEM = (
    "You write a thematic overview of a document collection. The input has "
    "one metadata line per document — '[n] title · date' — followed by that "
    "document's summary bullets. Using ONLY those bullets, write a cohesive "
    "summary of the collection's main threads, citing [n] after each claim "
    "it supports. Mention the period covered when the dates make it clear. "
    "Do not add facts."
)


@dataclass
class _Doc:
    document_id: str
    title: str
    url: str | None
    published: str  # ISO date (YYYY-MM-DD) or ""
    text: str


class DocSummary(BaseModel):
    document_id: str
    bullets: list[str] = Field(default_factory=list, description="2-3 short factual bullets.")


class BatchSummaries(BaseModel):
    summaries: list[DocSummary] = Field(default_factory=list)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _scope_filters(analysis: QueryAnalysis) -> dict[str, Any] | None:
    """Catalog kwargs for the analysis' scope; None when nothing scopes the
    set — a scope-less "summarize" belongs on the QA path. Unknown bundles are
    dropped rather than zeroing the set (a summary scope is soft, unlike the
    count guard); themes fall back to the category display name."""
    filters: dict[str, Any] = {}
    if analysis.theme:
        try:
            rows = terms.resolve_terms(analysis.theme)
        except Exception:
            logger.warning("Theme resolution failed; using category fallback.",
                           exc_info=True)
            rows = []
        if rows:
            filters["term_uuids"] = [r["term_uuid"] for r in rows]
        else:
            filters["category"] = analysis.theme
    bundle = _normalize_bundle(analysis.bundle)
    if bundle in DEFAULT_BUNDLES:
        filters["bundle"] = bundle
    if analysis.author:
        filters["author"] = analysis.author
    if analysis.title_contains:
        filters["title_contains"] = analysis.title_contains
    lo, hi = _parse_date(analysis.date_from), _parse_date(analysis.date_to)
    if lo is not None:
        filters["published_from"] = lo
    if hi is not None:
        filters["published_to"] = hi
    return filters or None


def _doc_from_payload(document_id: str, payload: dict[str, Any]) -> _Doc:
    return _Doc(
        document_id=document_id,
        title=str(payload.get("title") or document_id),
        url=payload.get("source_url"),
        published=str(payload.get("published_at") or "")[:10],
        text=str(payload.get("chunk_text") or ""),
    )


def _est_tokens(text: str) -> int:
    # Rough chars/4 is plenty for batch sizing; exactness doesn't matter here.
    return max(1, len(text) // 4)


def _batch_documents(
    docs: Sequence[_Doc], budget: int = _MAP_BATCH_TOKENS
) -> list[list[_Doc]]:
    """Greedy split into groups of ~budget estimated tokens, preserving order.
    An oversized single document still gets its own batch."""
    batches: list[list[_Doc]] = []
    current: list[_Doc] = []
    spent = 0
    for doc in docs:
        cost = _est_tokens(doc.text) + 50  # id/title framing overhead
        if current and spent + cost > budget:
            batches.append(current)
            current, spent = [], 0
        current.append(doc)
        spent += cost
    if current:
        batches.append(current)
    return batches


def _summarize_direct(question: str, docs: list[_Doc]) -> str:
    from app.generation.llm_client import get_llm
    from app.generation.prompts import format_context_blocks
    from app.retrieval.context_builder import ContextBlock

    blocks = [
        ContextBlock(
            n=i,
            text=doc.text,
            payload={"source_type": "website", "title": doc.title,
                     "published_at": doc.published},
        )
        for i, doc in enumerate(docs, start=1)
    ]
    response = get_llm().invoke(
        [
            ("system", _DIRECT_SYSTEM),
            ("human", f"Documents:\n{format_context_blocks(blocks)}\n\n"
                      f"Request: {question}"),
        ]
    )
    return getattr(response, "content", "") or ""


def _map_batch(batch: list[_Doc]) -> dict[str, list[str]]:
    from app.generation.llm_client import get_structured_llm

    parts = [
        f"document_id: {doc.document_id}\ntitle: {doc.title}\ntext: {doc.text}"
        for doc in batch
    ]
    model = get_structured_llm().with_structured_output(BatchSummaries)
    result: BatchSummaries = model.invoke(
        [("system", _MAP_SYSTEM), ("human", "\n\n---\n\n".join(parts))]
    )
    return {s.document_id: s.bullets for s in result.summaries if s.bullets}


def _summarize_map_reduce(question: str, docs: list[_Doc]) -> str:
    from app.generation.llm_client import get_llm

    batches = _batch_documents(docs)
    with ThreadPoolExecutor(max_workers=_MAP_WORKERS) as pool:
        mapped = list(pool.map(_map_batch, batches))
    bullets: dict[str, list[str]] = {}
    for part in mapped:
        bullets.update(part)

    lines: list[str] = []
    for i, doc in enumerate(docs, start=1):
        lines.append(f"[{i}] {doc.title}" + (f" · {doc.published}" if doc.published else ""))
        lines.extend(f"  - {b}" for b in bullets.get(doc.document_id, []))
    response = get_llm().invoke(
        [
            ("system", _REDUCE_SYSTEM),
            ("human", "Document summaries:\n" + "\n".join(lines)
                      + f"\n\nRequest: {question}"),
        ]
    )
    return getattr(response, "content", "") or ""


def summarize_scope(
    analysis: QueryAnalysis | None,
    *,
    tenant_id: str = "default",
    user_groups: Sequence[str] | None = None,
) -> dict[str, Any] | None:
    """Answer a scoped-summary query, or None to fall through to semantic RAG."""
    if analysis is None:
        return None
    try:
        filters = _scope_filters(analysis)
        if not filters:
            return None
        ids = catalog.document_ids_in_scope(limit=_SCOPE_DOC_CAP, **filters)
        if not ids:
            return None
        payloads = scoped_retrieval.lead_parents(
            ids, tenant_id=tenant_id, user_groups=user_groups
        )
        docs = [_doc_from_payload(i, payloads[i]) for i in ids if i in payloads]
        docs = [d for d in docs if d.text.strip()]
        if not docs:
            return None
        if len(docs) <= _DIRECT_DOC_LIMIT:
            answer = _summarize_direct(analysis.search_query, docs)
        else:
            answer = _summarize_map_reduce(analysis.search_query, docs)
        if not answer.strip():
            return None
    except Exception:
        logger.warning("Scoped summary failed; falling back to QA.", exc_info=True)
        return None

    citations = [
        Citation(n=i, type="website", title=d.title, url=d.url, document_id=d.document_id)
        for i, d in enumerate(docs, start=1)
    ]
    return {
        "answer": answer.strip(),
        "citations": [c.model_dump() for c in citations],
        "intent": "scoped_summary",
        "used_chunks": len(docs),
        "conflict": False,
        "cached": False,
    }
