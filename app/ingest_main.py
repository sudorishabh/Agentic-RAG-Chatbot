from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.app_factory import create_base_app
from app.workers.scheduler import start_sweep_scheduler, stop_sweep_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run the periodic ingestion sweep for the lifetime of the server."""
    task = start_sweep_scheduler()
    try:
        yield
    finally:
        await stop_sweep_scheduler(task)


# Ingestion server: background change-detection sweep + ingest/reindex control
# endpoints. Run separately from the retrieval server, e.g.:
#   uvicorn app.ingest_main:app --port 8001
app = create_base_app("Agentic RAG Ingestion", lifespan=lifespan)

app.include_router(health_router)
app.include_router(ingest_router)
