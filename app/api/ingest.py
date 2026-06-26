from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.config import get_settings
from app.ingestion.upload import ingest_article, ingest_upload
from app.schemas.ingest import (
    ArticleIngestRequest,
    ArticleIngestResponse,
    DirectIngestRequest,
    DirectIngestResponse,
    IngestResponse,
    PdfIngestRunResponse,
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


@router.post("/ingest/pdfs", response_model=PdfIngestRunResponse)
async def ingest_pdfs_route() -> PdfIngestRunResponse:
    settings = get_settings()
    source = settings.pdf_source_dirs or settings.pdf_source_path
    if not source:
        raise HTTPException(status_code=400, detail="PDF_SOURCE_PATH is not configured")
    from app.workers.tasks import ingest_pdfs

    tally = await run_in_threadpool(ingest_pdfs)
    return PdfIngestRunResponse(source=source, tally=tally)


@router.post("/ingest/run", response_model=DirectIngestResponse)
async def ingest_run_route(request: DirectIngestRequest | None = None) -> DirectIngestResponse:
    request = request or DirectIngestRequest()
    settings = get_settings()
    source = settings.pdf_source_dirs or settings.pdf_source_path
    from app.workers.tasks import ingest_drupal, ingest_pdfs

    pdfs = await run_in_threadpool(ingest_pdfs) if source else {}
    drupal = await run_in_threadpool(ingest_drupal, request.bundles, request.reconcile)
    return DirectIngestResponse(pdf_source=source or None, pdfs=pdfs, drupal=drupal)


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
