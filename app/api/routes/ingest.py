from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.schemas.ingest import IngestResponse
from app.services.ingestion import ingest_file

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    chunks = await run_in_threadpool(ingest_file, file.filename, content)
    return IngestResponse(filename=file.filename, chunks_ingested=chunks)
