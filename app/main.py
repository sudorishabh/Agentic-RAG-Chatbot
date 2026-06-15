from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.search import router as search_router
from app.config import get_settings
from app.observability.tracing import init_observability

settings = get_settings()

app = FastAPI(title="Agentic RAG Chatbot", version="0.1.0")

# Optional tracing + RAG-quality metrics (no-op unless configured, §10.4).
init_observability(app)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(ingest_router)
