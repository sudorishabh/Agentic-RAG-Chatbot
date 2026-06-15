"""Background ingestion workers (§10.4).

The query path stays fast; the *expensive* work (extraction, embedding,
re-indexing) runs out-of-band here. Each task is a thin wrapper over the existing
ingest pipeline so the worker owns scheduling/retries, not business logic:

* :func:`sweep`          — the periodic job: incremental scan of both sources
                           (local PDFs + Drupal JSON:API), the change-detected
                           backbone of the manifest.
* :func:`ingest_pdfs` / :func:`ingest_drupal` — explicit per-source triggers.
* :func:`ingest_upload` — embed one uploaded file off the request thread.
* :func:`reindex_document` — purge a document's points + manifest row so the next
                           sweep re-ingests it fresh.

**Celery is optional.** With it installed, these are real tasks (``.delay()`` /
beat schedule from settings); without it, the very same names are plain callables
that run synchronously — so imports never fail and a single-process deployment
still works. Run ``python -m app.workers.tasks sweep`` to fire the sweep without a
broker.
"""

from __future__ import annotations

import base64
import logging
from collections import Counter
from typing import Any, Callable

from app.config import get_settings

logger = logging.getLogger(__name__)

try:  # Celery is an optional dependency (see requirements.txt).
    from celery import Celery

    _HAS_CELERY = True
except Exception:  # pragma: no cover - celery not installed
    Celery = None  # type: ignore[assignment]
    _HAS_CELERY = False


def _build_celery() -> Any | None:
    if not _HAS_CELERY:
        return None
    settings = get_settings()
    broker = settings.celery_broker_url or settings.redis_url
    if not broker:
        logger.warning("No celery broker / redis_url configured; tasks run inline.")
        return None
    backend = settings.celery_result_backend or settings.redis_url or None
    app = Celery("agentic_rag", broker=broker, backend=backend)
    app.conf.task_default_queue = "ingest"
    app.conf.task_track_started = True
    if settings.worker_sweep_interval_seconds > 0:
        app.conf.beat_schedule = {
            "incremental-sweep": {
                "task": "app.workers.tasks.sweep",
                "schedule": float(settings.worker_sweep_interval_seconds),
            }
        }
    return app


celery_app = _build_celery()


def _task(name: str) -> Callable[[Callable], Callable]:
    """Register a Celery task when a broker is available, else leave the plain
    callable untouched so it can be invoked synchronously."""

    def decorator(fn: Callable) -> Callable:
        if celery_app is not None:
            return celery_app.task(name=name)(fn)
        return fn

    return decorator


def _bump_cache_if_changed(tally: Counter) -> None:
    """Invalidate cached answers when a run actually wrote to the index (§10.3)."""
    if tally.get("indexed") or tally.get("deleted"):
        from app.cache.redis_cache import bump_corpus_version

        bump_corpus_version()


# --------------------------------------------------------------------------- #
# Tasks
# --------------------------------------------------------------------------- #
@_task("app.workers.tasks.ingest_pdfs")
def ingest_pdfs(dirs: list[str] | None = None) -> dict[str, int]:
    """Incrementally ingest changed PDFs from the configured (or given) dirs."""
    from pathlib import Path

    from app.ingestion.pipeline import ingest_pdfs as run

    roots = [Path(d) for d in dirs] if dirs else None
    tally = run(roots)
    _bump_cache_if_changed(tally)
    return dict(tally)


@_task("app.workers.tasks.ingest_drupal")
def ingest_drupal(bundles: list[str] | None = None, reconcile: bool = False) -> dict[str, int]:
    """Incrementally ingest changed Drupal nodes (optionally reconciling deletes)."""
    from app.ingestion.pipeline import ingest_drupal as run

    tally = run(bundles or None, reconcile_deletes=reconcile)
    _bump_cache_if_changed(tally)
    return dict(tally)


@_task("app.workers.tasks.sweep")
def sweep() -> dict[str, dict[str, int]]:
    """The periodic job: incremental ingest of both sources in one pass."""
    settings = get_settings()
    pdfs = ingest_pdfs()
    drupal = ingest_drupal(reconcile=settings.worker_sweep_reconcile)
    result = {"pdfs": pdfs, "drupal": drupal}
    logger.info("Sweep complete: %s", result)
    return result


@_task("app.workers.tasks.ingest_upload")
def ingest_upload(filename: str, content_b64: str) -> dict[str, Any]:
    """Embed one uploaded file (content base64-encoded for broker serialization)."""
    from app.ingestion.upload import ingest_upload as run

    document_id, points = run(filename, base64.b64decode(content_b64))
    return {"document_id": document_id, "points": points}


@_task("app.workers.tasks.reindex_document")
def reindex_document(document_id: str, source_type: str = "article") -> dict[str, Any]:
    """Forget a document (purge points + manifest) so the next sweep re-ingests it."""
    from app.deps import delete_document
    from app.ingestion import state
    from app.cache.redis_cache import bump_corpus_version

    delete_document(document_id)
    removed = state.delete([document_id])
    bump_corpus_version()
    logger.info("Reindex reset %s (%s); %d manifest rows removed", document_id, source_type, removed)
    return {"document_id": document_id, "manifest_rows_removed": removed}


# --------------------------------------------------------------------------- #
# CLI — run a task synchronously without a broker:
#   python -m app.workers.tasks sweep
#   python -m app.workers.tasks pdfs
#   python -m app.workers.tasks drupal --reconcile
# --------------------------------------------------------------------------- #
def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run an ingestion worker task inline.")
    parser.add_argument("task", choices=["sweep", "pdfs", "drupal"], help="Task to run.")
    parser.add_argument("--bundle", action="append", default=[], help="Limit Drupal to bundle(s).")
    parser.add_argument("--reconcile", action="store_true", help="Reconcile Drupal deletes.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    fn = {"sweep": sweep, "pdfs": ingest_pdfs, "drupal": ingest_drupal}[args.task]
    if args.task == "drupal":
        print(ingest_drupal(args.bundle or None, reconcile=args.reconcile))
    else:
        print(fn())
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
