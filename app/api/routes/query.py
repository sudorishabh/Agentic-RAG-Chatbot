from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.rag import answer_query
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    result = await run_in_threadpool(
        answer_query,
        request.question,
        history=[turn.model_dump() for turn in request.history],
        tenant_id=request.tenant_id,
        user_groups=request.user_groups,
        top_k=request.top_k,
    )
    return QueryResponse(**result)
