"""Ingestion endpoints.

* ``POST /ingest/pdf``     — upload a PDF; extracted, chunked, and indexed via the
                            real pipeline (Docling + OCR + figure captioning).
* ``POST /ingest/article``— index an inline website article, or crawl live Drupal
                            bundles incrementally (``bundles``).
* ``POST /reindex``       — reset one document so the next sweep re-ingests it, or
                            trigger a full incremental sweep of both sources.

PDF/article ingest runs on a threadpool (it embeds); a full sweep is delegated to
the worker layer (which itself runs inline when no broker is configured).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.ingestion.upload import ingest_article, ingest_upload
from app.schemas.ingest import (
    ArticleIngestRequest,
    ArticleIngestResponse,
    IngestResponse,
    ReindexRequest,
    ReindexResponse,
)

router = APIRouter(tags=["ingest"])


@router.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    document_id, chunks = await run_in_threadpool(ingest_upload, file.filename, content)
    return IngestResponse(filename=file.filename, document_id=document_id, chunks_ingested=chunks)


@router.post("/ingest/article", response_model=ArticleIngestResponse)
async def ingest_article_route(request: ArticleIngestRequest) -> ArticleIngestResponse:
    if request.bundles:
        from app.workers.tasks import ingest_drupal

        crawled = await run_in_threadpool(ingest_drupal, request.bundles)
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


@router.post("/reindex", response_model=ReindexResponse)
async def reindex(request: ReindexRequest) -> ReindexResponse:
    if request.sweep:
        from app.workers.tasks import sweep

        detail = await run_in_threadpool(sweep)
        return ReindexResponse(status="swept", detail=detail)

    if not request.document_id:
        raise HTTPException(status_code=400, detail="document_id is required unless sweep=true")
    from app.workers.tasks import reindex_document

    detail = await run_in_threadpool(reindex_document, request.document_id, request.source_type)
    return ReindexResponse(status="reset", detail=detail)
