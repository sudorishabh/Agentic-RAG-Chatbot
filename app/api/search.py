from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from app.api.auth import Principal, require_principal
from app.pipeline.query_pipeline import search_blocks
from app.schemas.query import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    # The authentication gate; see the note in app/api/chat.py. Its identity is
    # not used for scoping — retrieval covers the whole public corpus.
    _principal: Principal = Depends(require_principal),
) -> SearchResponse:
    result = await run_in_threadpool(
        search_blocks,
        request.question,
        history=[turn.model_dump() for turn in request.history],
        top_k=request.top_k,
    )
    return SearchResponse(**result)
