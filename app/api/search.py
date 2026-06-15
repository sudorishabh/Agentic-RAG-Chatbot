"""Raw retrieval endpoint — ``POST /search`` (debugging / evaluation, §10.5).

Runs query understanding + hybrid search + rerank + context selection and returns
the selected blocks **without** generation, so you can inspect what the LLM would
have seen and measure retrieval quality (Recall@K / nDCG) against a golden set.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.rag import search_blocks
from app.schemas.query import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    result = await run_in_threadpool(
        search_blocks,
        request.question,
        history=[turn.model_dump() for turn in request.history],
        tenant_id=request.tenant_id,
        user_groups=request.user_groups,
        top_k=request.top_k,
    )
    return SearchResponse(**result)
