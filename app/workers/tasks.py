from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


def ingest_drupal(bundles: list[str] | None = None, reconcile: bool = False) -> dict[str, int]:
    from app.ingestion.pipeline import ingest_drupal as run

    tally = run(bundles or None, reconcile_deletes=reconcile)
    return dict(tally)


def sweep() -> dict[str, dict[str, int]]:
    settings = get_settings()
    result = {"drupal": ingest_drupal(reconcile=settings.worker_sweep_reconcile)}
    logger.info("Sweep complete: %s", result)
    return result


def reindex_document(document_id: str, source_type: str = "website") -> dict[str, Any]:
    from app.catalog import state
    from app.core.clients import delete_document

    delete_document(document_id)
    removed = state.delete([document_id])
    logger.info("Reindex reset %s (%s); %d manifest rows removed", document_id, source_type, removed)
    return {"document_id": document_id, "manifest_rows_removed": removed}


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run an ingestion worker task inline.")
    parser.add_argument("task", choices=["sweep", "drupal"], help="Task to run.")
    parser.add_argument("--bundle", action="append", default=[], help="Limit Drupal to bundle(s).")
    parser.add_argument("--reconcile", action="store_true", help="Reconcile Drupal deletes.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if args.task == "drupal":
        print(ingest_drupal(args.bundle or None, reconcile=args.reconcile))
    else:
        print(sweep())
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
