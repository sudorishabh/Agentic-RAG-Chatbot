from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.config import get_settings
from app.ingestion.pipeline import IngestBusyError
from app.ingestion.upload import ingest_article, ingest_upload
from app.schemas.ingest import (
    ArticleIngestRequest,
    ArticleIngestResponse,
    DirectIngestRequest,
    DirectIngestResponse,
    IngestLogResponse,
    IngestResponse,
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


async def _read_capped(file: UploadFile, limit: int) -> bytes:
    """Read an upload in bounded chunks, rejecting anything over ``limit`` bytes
    before the whole payload is buffered — an unbounded read is a memory-DoS."""
    buf = bytearray()
    while True:
        chunk = await file.read(1 << 20)  # 1 MiB
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > limit:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the maximum upload size of {limit} bytes",
            )
    return bytes(buf)


@router.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted")
    content = await _read_capped(file, get_settings().max_upload_bytes)
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="File is not a valid PDF")
    document_id, chunks = await run_in_threadpool(ingest_upload, file.filename, content)
    return IngestResponse(filename=file.filename, document_id=document_id, chunks_ingested=chunks)


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
    if request.sweep:
        from app.workers.tasks import sweep

        detail = await _run_exclusive(sweep)
        return ReindexResponse(status="swept", detail=detail)

    if not request.document_id:
        raise HTTPException(status_code=400, detail="document_id is required unless sweep=true")
    from app.workers.tasks import reindex_document

    detail = await run_in_threadpool(reindex_document, request.document_id, request.source_type)
    return ReindexResponse(status="reset", detail=detail)
