from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.config import get_settings

router = APIRouter(tags=["ops"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

def _qdrant_status() -> dict:
    from app.deps import get_qdrant_client

    settings = get_settings()
    client = get_qdrant_client()
    exists = client.collection_exists(settings.qdrant_collection)
    points = None
    if exists:
        points = client.count(settings.qdrant_collection, exact=False).count
    return {"reachable": True, "collection": settings.qdrant_collection,
            "collection_exists": exists, "points": points}


def _redis_status() -> dict:
    from app.deps import get_redis

    client = get_redis()
    if client is None:
        return {"configured": False}
    try:
        client.ping()
        return {"configured": True, "reachable": True}
    except Exception:
        return {"configured": True, "reachable": False}


@router.get("/ready")
async def ready() -> JSONResponse:
    """Readiness probe. The 200/503 status code is the contract; the body
    carries infrastructure detail only when ``ops_detail_enabled`` — error
    strings and point counts fingerprint the deployment on the public API."""
    detail = get_settings().ops_detail_enabled
    try:
        qdrant = await run_in_threadpool(_qdrant_status)
    except Exception as exc:
        content: dict = {"status": "not_ready"}
        if detail:
            content["qdrant"] = {"reachable": False, "error": str(exc)}
        return JSONResponse(status_code=503, content=content)
    if not detail:
        return JSONResponse(content={"status": "ready"})
    redis = await run_in_threadpool(_redis_status)
    return JSONResponse(content={"status": "ready", "qdrant": qdrant, "redis": redis})


@router.get("/metrics")
async def metrics() -> dict:
    settings = get_settings()
    if not settings.ops_detail_enabled:
        # Hide the endpoint entirely: its whole body is deployment detail.
        raise HTTPException(status_code=404, detail="Not Found")
    try:
        qdrant = await run_in_threadpool(_qdrant_status)
    except Exception as exc:
        qdrant = {"reachable": False, "error": str(exc)}
    return {
        "service": settings.otel_service_name,
        "qdrant": qdrant,
        "redis": await run_in_threadpool(_redis_status),
        "reranker_provider": settings.reranker_provider,
        "retrieval": {
            "candidate_k": settings.retrieval_candidate_k,
            "top_k": settings.retrieval_top_k,
            "score_threshold": settings.rerank_score_threshold,
        },
        "caches": {
            "response": settings.response_cache_enabled,
            "embedding": settings.embedding_cache_enabled,
            "semantic": settings.semantic_cache_enabled,
        },
    }
