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


def _mysql_status() -> dict:
    """Catalog reachability. One round trip, no table scan."""
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()
    return {"reachable": True, "database": get_settings().mysql_database}


# Stores this process cannot serve its purpose without. Qdrant is always one.
# MySQL is added by the ingestion server (app.ingest_main): it is the system of
# record there — the crawl cursor, the retry floor and every write live in it —
# so an ingestion server that cannot reach it is not ready by any definition.
#
# The retrieval server deliberately does not require it: dense retrieval answers
# from Qdrant alone, and taking the whole API out of a load balancer over a
# catalog blip would turn a degraded feature into an outage. It still reports
# MySQL's state in the detail body.
_REQUIRED_STORES: set[str] = set()


def require_for_readiness(*stores: str) -> None:
    """Declare which optional stores this process must be able to reach."""
    _REQUIRED_STORES.update(stores)


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


def _knowledge_status() -> dict:
    """Per-document knowledge-stage health: what ran, what is queued, what broke.

    Beside ``_neo4j_status`` rather than inside it, because the two answer
    different questions — that one is "is the graph reachable and how big is
    it", this one is "is the layer that fills it keeping up". Both report
    ``enabled: False`` and stop when ``knowledge_enabled`` is off, so a
    deployment that has not adopted the knowledge layer opens no connection to
    answer a probe.

    Only reachable from ``/metrics``, which is already hidden behind
    ``_ops_visible``: run counts, document ids and error strings are deployment
    detail and have no business on a public response.
    """
    from app.ingestion.knowledge_sync import status

    try:
        return status()
    except Exception as exc:  # pragma: no cover - the reporter is fail-open
        return {"enabled": True, "readable": False, "error": str(exc)}


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
    probes: dict[str, dict] = {}
    failed: dict[str, str] = {}

    for name, probe in (("qdrant", _qdrant_status), ("mysql", _mysql_status)):
        if name != "qdrant" and name not in _REQUIRED_STORES and not detail:
            # Not required here and nobody will read the body: don't pay for it.
            continue
        try:
            probes[name] = await run_in_threadpool(probe)
        except Exception as exc:
            probes[name] = {"reachable": False, "error": str(exc)}
            if name == "qdrant" or name in _REQUIRED_STORES:
                failed[name] = str(exc)

    if failed:
        content: dict = {"status": "not_ready"}
        if detail:
            content.update(probes)
        return JSONResponse(status_code=503, content=content)
    if not detail:
        return JSONResponse(content={"status": "ready"})
    probes["redis"] = await run_in_threadpool(_redis_status)
    probes["neo4j"] = await run_in_threadpool(_neo4j_status)
    return JSONResponse(content={"status": "ready", **probes})


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
    # The last reconciliation this process ran, never a fresh one: the checks
    # scroll the whole collection, which is not something a metrics scrape may
    # trigger. Absent until the first sweep has finished one.
    from app.ingestion.reconcile import last_report

    report = last_report()
    return {
        "service": settings.otel_service_name,
        "corpus_reconciliation": (
            {"ok": report.ok, "documents": report.documents, "points": report.points,
             "drift": {c.name: c.count for c in report.drift}}
            if report is not None else None
        ),
        "qdrant": qdrant,
        "redis": await run_in_threadpool(_redis_status),
        "neo4j": await run_in_threadpool(_neo4j_status),
        "knowledge": await run_in_threadpool(_knowledge_status),
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
