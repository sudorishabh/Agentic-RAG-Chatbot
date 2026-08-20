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
    # Both of these run after the ingestion, not inside it, and neither can fail
    # it: the documents are already written and the result above is already
    # decided. Projection first, so reconciliation reports the graph as it stands
    # after this sweep rather than as it stood before.
    from app.ingestion.graph_sync import project_after_sweep
    from app.ingestion.knowledge_sync import catch_up
    from app.ingestion.reconcile import reconcile_after_sweep

    # Documents whose per-document knowledge stage did not land — it failed, it
    # was cut short by its budget, or it never ran. Bounded, and before the
    # projection so anything it stages is in this sweep's graph refresh rather
    # than the next one. Returns rather than raises, like everything else here.
    knowledge = catch_up()
    if knowledge is not None and knowledge.get("examined"):
        result["knowledge_catch_up"] = knowledge

    projection = project_after_sweep()
    if projection is not None:
        result["graph_projection"] = {
            "version": projection.get("projection_version"),
            **projection.get("nodes", {}),
        }

    report = reconcile_after_sweep()
    if report is not None:
        result["reconciliation"] = {
            check.name: check.count for check in report.checks if not check.skipped
        }
    return result


# What a reindex request is called in `documents_retry.outcome`. Its own value
# rather than "error": the document did not fail, an operator asked for it back,
# and a retry queue that cannot tell those apart cannot be triaged.
REINDEX_OUTCOME = "reindex"


def reindex_document(document_id: str, source_type: str = "website") -> dict[str, Any]:
    """Queue a document to be rebuilt on the next crawl. Deletes nothing.

    This used to delete the document's vectors *and* its catalog row. The row is
    what positions the incremental crawl — the window is
    ``changed >= MAX(changed_mark)`` per bundle — so removing it put every
    document whose ``changed`` predated its bundle's high-water mark permanently
    out of reach: the repair tool was the most destructive operation in the
    system, and it reported ``status="reset"`` as though it were recoverable.

    What it does instead is state two facts and let the ordinary pipeline act on
    them:

    * a retry marker, which floors the crawl window at this document's position
      so the next sweep actually reaches it;
    * cleared change markers, so the crawl calls it CHANGED and the pipeline
      re-indexes it rather than refreshing a fingerprint.

    The vectors stay exactly where they are. They are replaced by the swap in
    ``_handle`` — new points upserted first, everything else for the document
    deleted after — so the document is searchable throughout, and a failed or
    interrupted rebuild leaves the version it already had.

    ``source_type`` is accepted for the API's shape and logged; the catalogued
    row is authoritative for what the document actually is.
    """
    from app.catalog import retries, state

    prior = state.get(document_id)
    if prior is None:
        logger.warning(
            "Reindex requested for %s, which is not catalogued; nothing to queue.",
            document_id,
        )
        return {"document_id": document_id, "status": "unknown"}

    retries.ensure_table()
    retries.record(
        document_id,
        source_type=prior.source_type,
        bundle=prior.bundle,
        changed_mark=prior.changed_mark,
        outcome=REINDEX_OUTCOME,
        error="reindex requested by an operator",
    )
    state.clear_change_markers(document_id)
    logger.info(
        "Reindex queued for %s (%s/%s, changed_mark=%s); nothing was deleted.",
        document_id, prior.source_type, prior.bundle, prior.changed_mark,
    )
    return {
        "document_id": document_id,
        "status": "queued",
        "source_type": prior.source_type,
        "bundle": prior.bundle,
        "changed_mark": prior.changed_mark,
        "doc_version": prior.doc_version,
    }


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
