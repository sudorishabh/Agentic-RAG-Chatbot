from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from app.retrieval.source_locator import resolve_source_file

router = APIRouter(tags=["source"])


@router.get("/source/{document_id}")
async def get_source(document_id: str) -> FileResponse:
    """Serve a document's source PDF inline so citation links open it in the
    browser's viewer (which honours the #page=N fragment)."""
    path = await run_in_threadpool(resolve_source_file, document_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Source file not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{path.name}"'},
    )
