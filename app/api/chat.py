from __future__ import annotations

import json
from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.rag import stream_answer
from app.schemas.query import QueryRequest

router = APIRouter(tags=["chat"])


def _sse(events: Iterator[dict]) -> Iterator[str]:
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"


@router.post("/chat")
def chat(request: QueryRequest) -> StreamingResponse:
    events = stream_answer(
        request.question,
        history=[turn.model_dump() for turn in request.history],
        tenant_id=request.tenant_id,
        user_groups=request.user_groups,
        top_k=request.top_k,
    )
    return StreamingResponse(
        _sse(events),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
