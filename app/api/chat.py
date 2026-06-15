"""Chat endpoints: streaming answer (SSE) + feedback capture.

``POST /chat`` streams the grounded answer token-by-token (§6.5) as Server-Sent
Events, then a final ``sources`` event carrying the citations built from payloads
(§8) and a ``done`` sentinel. ``POST /chat/feedback`` records the thumbs up/down +
clicked-citation signal that feeds evaluation (§10.4).
"""

from __future__ import annotations

import json
from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.observability.tracing import record_feedback
from app.rag import stream_answer
from app.schemas.query import FeedbackRequest, QueryRequest

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


@router.post("/chat/feedback")
def feedback(request: FeedbackRequest) -> dict[str, str]:
    record_feedback(request.model_dump())
    return {"status": "recorded"}
