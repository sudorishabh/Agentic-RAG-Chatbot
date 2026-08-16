from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.ingestion.pipeline import IngestBusyError
from app.ingestion.upload import ingest_article
from app.schemas.ingest import (
    ArticleIngestRequest,
    ArticleIngestResponse,
    DirectIngestRequest,
    DirectIngestResponse,
    IngestLogResponse,
    ReindexRequest,
    ReindexResponse,
)

router = APIRouter(tags=["ingest"])


async def _run_exclusive(fn, *args):
    """Run a corpus-wide ingestion task in the threadpool, mapping the
    one-run-at-a-time rejection (IngestBusyError) to HTTP 409."""
    try:
        return await run_in_threadpool(fn, *args)
    except IngestBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/ingest/run", response_model=DirectIngestResponse)
async def ingest_run_route(request: DirectIngestRequest | None = None) -> DirectIngestResponse:
    request = request or DirectIngestRequest()
    from app.workers.tasks import ingest_drupal

    drupal = await _run_exclusive(ingest_drupal, request.bundles, request.reconcile)
    return DirectIngestResponse(drupal=drupal)


@router.post("/ingest/article", response_model=ArticleIngestResponse)
async def ingest_article_route(request: ArticleIngestRequest) -> ArticleIngestResponse:
    if request.bundles:
        from app.workers.tasks import ingest_drupal

        crawled = await _run_exclusive(ingest_drupal, request.bundles)
        return ArticleIngestResponse(crawled=crawled)

    if not (request.body or request.title):
        raise HTTPException(status_code=400, detail="Provide an article (title/body) or bundles to crawl")
    document_id, chunks = await run_in_threadpool(
        ingest_article,
        title=request.title,
        body=request.body,
        url=request.url,
        uuid=request.uuid,
        bundle=request.bundle,
    )
    return ArticleIngestResponse(document_id=document_id, chunks_ingested=chunks)


@router.get("/ingest/log", response_model=IngestLogResponse)
async def ingest_log_route(
    limit: int = 100,
    source_type: str | None = None,
    document_id: str | None = None,
    status: str | None = None,
) -> IngestLogResponse:
    from app.catalog import log as ingest_log

    rows = await run_in_threadpool(
        ingest_log.recent,
        limit=limit,
        source_type=source_type,
        document_id=document_id,
        status=status,
    )
    return IngestLogResponse(count=len(rows), entries=rows)


@router.post("/reindex", response_model=ReindexResponse)
async def reindex(request: ReindexRequest) -> ReindexResponse:
    """Queue a document to be rebuilt, or run a full sweep.

    Deletes nothing. A document reindex records a retry marker and clears the
    document's change markers, so the next crawl reaches it and rebuilds it; its
    catalog row and its existing vectors stay in place and are replaced only once
    the new version has been indexed. ``status="queued"`` says the request was
    recorded, not that the rebuild has happened — the next sweep does that.

    404 when the document is not catalogued: there is nothing to queue, and
    answering 200 would repeat the false-confidence the old ``status="reset"``
    gave for a document it had just made unrecoverable.
    """
    if request.sweep:
        from app.workers.tasks import sweep

        detail = await _run_exclusive(sweep)
        return ReindexResponse(status="swept", detail=detail)

    if not request.document_id:
        raise HTTPException(status_code=400, detail="document_id is required unless sweep=true")
    from app.workers.tasks import reindex_document

    detail = await run_in_threadpool(reindex_document, request.document_id, request.source_type)
    if detail.get("status") == "unknown":
        raise HTTPException(
            status_code=404,
            detail=f"{request.document_id} is not catalogued; nothing to reindex.",
        )
    return ReindexResponse(status=detail.get("status", "queued"), detail=detail)
