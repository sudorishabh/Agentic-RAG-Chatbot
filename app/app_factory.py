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
    if not origins or "*" in origins:
        # Wildcard keeps the embeddable widget working from any host page, and
        # is tolerable only because credentials stay off and auth uses a
        # non-ambient bearer token — but deployments serving non-public content
        # should pin the host origins.
        logging.getLogger(__name__).warning(
            "CORS allows all origins; set CORS_ALLOW_ORIGINS to pin the host "
            "site(s) in production."
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        # Never enable credentials here: with a wildcard-capable origin config,
        # ambient cookies would make every embedding page a CSRF vector.
        allow_credentials=False,
        # The whole API is GET/POST; the clients send JSON plus, when auth is
        # enabled, a bearer token. Grant exactly that instead of "*".
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    init_observability(app)
    return app
