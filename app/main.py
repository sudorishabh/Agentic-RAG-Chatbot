from fastapi import FastAPI

from app.api.routes.ingest import router as ingest_router
from app.api.routes.query import router as query_router
from app.config import get_settings
from app.observability.tracing import init_observability

settings = get_settings()

app = FastAPI(title="Agentic RAG Chatbot", version="0.1.0")

# Optional tracing + RAG-quality metrics (no-op unless configured, §10.4).
init_observability(app)

app.include_router(ingest_router)
app.include_router(query_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
