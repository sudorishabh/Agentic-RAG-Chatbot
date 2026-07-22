from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from app.api.auth import Principal, require_principal
from app.pipeline.query_pipeline import search_blocks
from app.schemas.query import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest, principal: Principal = Depends(require_principal)
) -> SearchResponse:
    result = await run_in_threadpool(
        search_blocks,
        request.question,
        history=[turn.model_dump() for turn in request.history],
        tenant_id=principal.tenant_id,
        user_groups=principal.groups,
        top_k=request.top_k,
    )
    return SearchResponse(**result)
