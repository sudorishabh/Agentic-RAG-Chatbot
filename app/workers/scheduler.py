from __future__ import annotations

import asyncio
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


async def _sweep_loop(interval: float) -> None:
    """Run an incremental ingestion sweep, prune the semantic cache and the
    ingest log, then sleep, forever.

    The sweep and prunes are blocking (network / DB / Qdrant IO), so they run in
    a worker thread to keep the event loop responsive. Errors are logged and the
    loop continues on the next interval.
    """
    from app.cache import semantic_cache
    from app.ingestion import ingest_log
    from app.ingestion.pipeline import IngestBusyError
    from app.workers.tasks import sweep

    while True:
        try:
            result = await asyncio.to_thread(sweep)
            logger.info("Background sweep complete: %s", result)
        except asyncio.CancelledError:
            raise
        except IngestBusyError:
            logger.info("Skipping sweep; another ingestion run is in progress.")
        except Exception:
            logger.exception("Background sweep failed; retrying next interval.")
        if get_settings().semantic_cache_enabled:
            try:
                await asyncio.to_thread(semantic_cache.prune)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Semantic cache prune failed; continuing.")
        try:
            # No-op unless ingest_log_enabled and a retention window is set.
            await asyncio.to_thread(ingest_log.prune)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ingest log prune failed; continuing.")
        await asyncio.sleep(interval)


def start_sweep_scheduler() -> asyncio.Task | None:
    """Launch the periodic ingestion sweep as a background task.

    Returns the task handle, or None when disabled
    (``WORKER_SWEEP_INTERVAL_SECONDS`` <= 0). The first sweep runs immediately.
    """
    interval = get_settings().worker_sweep_interval_seconds
    if interval <= 0:
        logger.info("Background sweep disabled (worker_sweep_interval_seconds <= 0).")
        return None
    logger.info("Starting background sweep every %ss.", interval)
    return asyncio.create_task(_sweep_loop(float(interval)))


async def stop_sweep_scheduler(task: asyncio.Task | None) -> None:
    """Cancel the background sweep task and wait for it to unwind."""
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
