from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.api.auth import Principal, optional_principal
from app.config import get_settings

router = APIRouter(tags=["ops"])


def _ops_visible(principal: Principal) -> bool:
    """Metrics visibility: the ops_detail_enabled deployments (private/dev)
    see everything; otherwise only members of ops_admin_group do, and only
    when auth is on — unverified callers are all anonymous."""
    settings = get_settings()
    if settings.ops_detail_enabled:
        return True
    group = settings.ops_admin_group
    return bool(group) and settings.auth_enabled and group in principal.user_groups


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

def _qdrant_status() -> dict:
    from app.core.clients import get_qdrant_client

    settings = get_settings()
    client = get_qdrant_client()
    exists = client.collection_exists(settings.qdrant_collection)
    points = None
    if exists:
        points = client.count(settings.qdrant_collection, exact=False).count
    return {"reachable": True, "collection": settings.qdrant_collection,
            "collection_exists": exists, "points": points}


def _neo4j_status() -> dict:
    """Knowledge-graph reachability, plus how much is in it.

    Reports ``enabled: False`` and stops when ``knowledge_enabled`` is off — the
    default — so a deployment that has not adopted the knowledge layer never
    opens a Neo4j connection just to answer a probe. Reachability is a value
    rather than an exception because the graph is a rebuildable projection: it
    being down is a degraded knowledge layer, never an unready service.
    """
    settings = get_settings()
    if not settings.knowledge_enabled:
        return {"enabled": False}
    from app.core.clients import graph_available, read_session

    if not graph_available():
        return {"enabled": True, "reachable": False}
    try:
        with read_session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS n").single()["n"]
            rels = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS n"
            ).single()["n"]
        return {
            "enabled": True, "reachable": True,
            "database": settings.neo4j_database, "nodes": nodes,
            "relationships": rels,
        }
    except Exception:
        return {"enabled": True, "reachable": False}


def _redis_status() -> dict:
    from app.core.clients import get_redis

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
    neo4j = await run_in_threadpool(_neo4j_status)
    return JSONResponse(
        content={"status": "ready", "qdrant": qdrant, "redis": redis, "neo4j": neo4j}
    )


@router.get("/metrics/timings")
async def metrics_timings(
    principal: Principal = Depends(optional_principal),
) -> dict:
    """Per-stage / per-component timing aggregates: where the time goes.

    Fed by the tracing spans (rag.* on the retrieval server, ingest.* on the
    ingestion server). Per-process, in-memory, reset on restart; parent spans
    include their children's time. Same visibility gate as /metrics."""
    if not _ops_visible(principal):
        raise HTTPException(status_code=404, detail="Not Found")
    from app.observability.metrics import snapshot

    return snapshot()


@router.get("/metrics")
async def metrics(principal: Principal = Depends(optional_principal)) -> dict:
    settings = get_settings()
    if not _ops_visible(principal):
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
        "neo4j": await run_in_threadpool(_neo4j_status),
        "reranker_provider": settings.reranker_provider,
        "retrieval": {
            "candidate_k": settings.retrieval_candidate_k,
            "top_k": settings.retrieval_top_k,
            "score_threshold": settings.rerank_score_threshold,
        },
        "caches": {
            "semantic": settings.semantic_cache_enabled,
        },
    }
