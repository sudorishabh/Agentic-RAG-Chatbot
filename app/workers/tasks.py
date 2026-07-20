from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


def _bump_cache_if_changed(tally: Counter) -> None:
    if tally.get("indexed") or tally.get("deleted"):
        from app.cache.redis_cache import bump_corpus_version

        bump_corpus_version()


def ingest_pdfs(dirs: list[str] | None = None) -> dict[str, int]:
    from pathlib import Path

    from app.ingestion.pipeline import ingest_pdfs as run

    roots = [Path(d) for d in dirs] if dirs else None
    tally = run(roots)
    _bump_cache_if_changed(tally)
    return dict(tally)


def ingest_drupal(bundles: list[str] | None = None, reconcile: bool = False) -> dict[str, int]:
    from app.ingestion.pipeline import ingest_drupal as run

    tally = run(bundles or None, reconcile_deletes=reconcile)
    _bump_cache_if_changed(tally)
    return dict(tally)


def sweep() -> dict[str, dict[str, int]]:
    settings = get_settings()
    pdfs = ingest_pdfs()
    drupal = ingest_drupal(reconcile=settings.worker_sweep_reconcile)
    result = {"pdfs": pdfs, "drupal": drupal}
    logger.info("Sweep complete: %s", result)
    return result


def reindex_document(document_id: str, source_type: str = "website") -> dict[str, Any]:
    from app.deps import delete_document
    from app.ingestion import state
    from app.cache.redis_cache import bump_corpus_version

    delete_document(document_id)
    removed = state.delete([document_id])
    bump_corpus_version()
    logger.info("Reindex reset %s (%s); %d manifest rows removed", document_id, source_type, removed)
    return {"document_id": document_id, "manifest_rows_removed": removed}


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
