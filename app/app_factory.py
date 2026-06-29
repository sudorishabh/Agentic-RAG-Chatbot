from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.observability.tracing import init_observability


def _configure_app_logging() -> None:
    # Surface app.* INFO logs (e.g. ingestion progress) under uvicorn, which
    # otherwise only configures its own loggers.
    app_logger = logging.getLogger("app")
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        app_logger.addHandler(handler)
        app_logger.setLevel(logging.INFO)
        app_logger.propagate = False


def create_base_app(title: str, **kwargs: Any) -> FastAPI:
    """Build a FastAPI app with the shared logging, CORS and observability wiring.

    Used by both the retrieval server (app.main) and the ingestion server
    (app.ingest_main); pass ``lifespan=`` through kwargs for background tasks.
    """
    settings = get_settings()
    _configure_app_logging()

    app = FastAPI(title=title, version="0.1.0", **kwargs)

    origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_observability(app)
    return app
