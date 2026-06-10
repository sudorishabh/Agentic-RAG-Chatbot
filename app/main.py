from fastapi import FastAPI

from app.api.routes.ingest import router as ingest_router
from app.api.routes.query import router as query_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Agentic RAG Chatbot", version="0.1.0")

app.include_router(ingest_router)
app.include_router(query_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
