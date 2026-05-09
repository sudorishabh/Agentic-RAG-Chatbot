from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag import answer_query

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    result = await run_in_threadpool(answer_query, request.question)
    return QueryResponse(**result)
