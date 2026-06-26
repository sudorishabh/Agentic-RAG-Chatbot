import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.search import router as search_router
from app.config import get_settings
from app.observability.tracing import init_observability

settings = get_settings()

# Surface app.* INFO logs (e.g. ingestion progress) under uvicorn, which
# otherwise only configures its own loggers.
_app_logger = logging.getLogger("app")
if not _app_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    _app_logger.addHandler(_handler)
    _app_logger.setLevel(logging.INFO)
    _app_logger.propagate = False

app = FastAPI(title="Agentic RAG Chatbot", version="0.1.0")

_cors_origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_observability(app)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(ingest_router)
