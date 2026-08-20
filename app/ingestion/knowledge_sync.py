"""Building the knowledge layer as documents are ingested, without risking them.

The sibling of :mod:`app.ingestion.graph_sync`, and deliberately the same shape.
That module refreshes the whole-graph projection once per sweep; this one runs
the knowledge layer for one document that has just been indexed, so a new
document contributes knowledge without waiting for the next corpus pass.

Where this is called, and why exactly there
-------------------------------------------
``app.ingestion.pipeline._handle``, immediately before it returns ``"indexed"``.
By that point five things have already happened and none of them can be undone
by anything here:

1. the chunks were built,
2. Qdrant holds the new version's points,
3. the previous version's points have been swapped out,
4. the catalog row and its facet rows are committed,
5. the ingest log records the document as indexed.

So the document's fate is settled before this module is entered. It is called
for ``indexed`` and nothing else — not ``deleted``, ``unchanged``,
``unchanged_content``, ``skipped`` or ``error`` — because those are either not a
successful index or, for ``unchanged_content``, a document whose chunks did not
change and whose knowledge is therefore already whatever the last run made it.

Why it cannot break ingestion
-----------------------------
Structurally, not by care:

* every entry point returns rather than raises, and the outermost body is a
  bare ``except Exception``;
* ``_handle`` ignores the return value, so there is no path by which a report
  becomes an outcome;
* ``"indexed"`` is in ``_RESOLVED_OUTCOMES``, so no retry marker is written
  whatever happens here;
* nothing in this module or in :mod:`app.knowledge.document_pipeline` imports
  ``index_chunks`` or ``delete_document``. A knowledge failure cannot remove a
  vector, because the code to remove one is not reachable from it.

A knowledge failure therefore costs a log line and a row in
``documents_knowledge_run`` saying so. The catch-up sweep and
``scripts.knowledge_document`` pick it up later; ``scripts.build_knowledge``
repairs anything they miss.

Ships inert
-----------
Double-gated on ``knowledge_enabled`` (this deployment has a knowledge layer at
all) and ``knowledge_process_after_index`` (build it on the ingest path). Both
must be true; the second defaults false. With either off, nothing here imports
``app.knowledge``, opens a connection, or costs a document anything measurable.
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

__all__ = ["process_after_index", "enabled", "catch_up", "status"]


def enabled() -> bool:
    """Whether the per-document knowledge stage runs on this deployment.

    Both flags, and in this order: ``knowledge_enabled`` is the master switch
    whose documented contract is that ingestion behaves exactly as it does
    without the knowledge layer, and ``knowledge_process_after_index`` is the
    separate decision to build that layer incrementally rather than only in
    ``scripts.build_knowledge``.

    Never raises. It is called from the ingest path *before* the arguments to
    :func:`process_after_index` are assembled, so it is the outermost guard and
    has to hold even if configuration cannot be read at all — in which case the
    honest answer is "not enabled".
    """
    try:
        from app.config import get_settings

        settings = get_settings()
        return bool(
            settings.knowledge_enabled and settings.knowledge_process_after_index
        )
    except Exception:  # pragma: no cover - configuration is not this module's job
        logger.debug("Could not read knowledge settings; treating as off.",
                     exc_info=True)
        return False


def process_after_index(
    *,
    document_id: str,
    doc_version: int,
    chunks: Sequence[Any],
    source_type: str = "",
    bundle: str | None = None,
    content_hash: str = "",
    raw_meta: dict[str, Any] | None = None,
    authors: Sequence[str] = (),
    run_id: str | None = None,
) -> dict[str, Any] | None:
    """Run the knowledge stage for a document that was just indexed.

    **Never raises.** Returns the run's report, or None when the stage did not
    run — disabled, or nothing to work on. The caller is expected to ignore both.

    ``chunks`` are ingestion's own :class:`app.ingestion.chunking.Chunk` objects,
    already in memory. Passing them rather than re-reading Qdrant is not only
    cheaper: it guarantees the knowledge layer reads exactly the text that was
    just indexed, with no window in which a concurrent write could change the
    answer underneath it.
    """
    if not enabled():
        return None
    if not document_id or not chunks:
        return None

    try:
        from app.knowledge.document_pipeline import (
            DocumentInput, StageOptions, process_document,
        )

        doc = DocumentInput.from_chunks(
            document_id=document_id, doc_version=doc_version, chunks=chunks,
            source_type=source_type, bundle=bundle, content_hash=content_hash,
            raw_meta=raw_meta, authors=authors, run_id=run_id,
        )
        if not doc.chunks:
            # Every chunk was a parent. Nothing to extract from, and not a
            # failure — the document is indexed and its children carry the text.
            return None
        report = process_document(doc, StageOptions.from_settings())
    except Exception:
        # The document is already indexed, its catalog row is written and its
        # log entry says so. Whatever went wrong here, none of that changes.
        logger.exception(
            "The knowledge stage failed for %s; the document is indexed and "
            "unaffected. It is re-runnable with "
            "`python -m scripts.knowledge_document %s`.",
            document_id, document_id,
        )
        return None

    return report.as_dict()


def catch_up(limit: int | None = None) -> dict[str, Any] | None:
    """Re-run the knowledge stage for documents whose last attempt did not land.

    The bounded sweep-level companion to the per-document hook, called after a
    sweep alongside ``graph_sync.project_after_sweep``. Two populations, both
    from ``knowledge_runs.pending``: runs that ended ``partial`` or ``failed``
    and are under the attempt ceiling, and indexed documents with no run row at
    all — a stage that never ran, or crashed before it could report.

    Bounded on purpose. A backlog is drained across sweeps rather than in one
    unbounded pass that would make an ingestion run's duration depend on how
    long the knowledge layer had been broken.

    Never raises, for the same reason as everything else here.
    """
    if not enabled():
        return None
    try:
        return _catch_up(limit)
    except Exception:
        # `sweep()` calls this bare, the way it calls project_after_sweep, and
        # relies on the same contract. The contract has to hold for *everything*
        # inside — a failed import, an unreadable setting — not only for the
        # store calls that have their own handlers.
        logger.exception(
            "The knowledge catch-up failed; the sweep and its documents are "
            "unaffected and the queued documents stay queued."
        )
        return None


def _catch_up(limit: int | None) -> dict[str, Any] | None:
    from app.config import get_settings
    from app.catalog import knowledge_runs
    from app.knowledge.document_loader import load_document
    from app.knowledge.document_pipeline import StageOptions, process_document

    settings = get_settings()
    budget = limit if limit is not None else _DEFAULT_CATCH_UP
    try:
        due = knowledge_runs.pending(
            max_attempts=settings.knowledge_stage_max_attempts, limit=budget
        )
    except Exception:
        logger.warning(
            "Could not read the knowledge retry queue; skipping catch-up.",
            exc_info=True,
        )
        return None
    if not due:
        return {"examined": 0, "ok": 0, "failed": 0}

    options = StageOptions.from_settings()
    tally = {"examined": 0, "ok": 0, "failed": 0}
    for row in due:
        tally["examined"] += 1
        try:
            doc = load_document(row["document_id"])
            if doc is None:
                tally["failed"] += 1
                continue
            report = process_document(doc, options)
            tally["ok" if report.status == "ok" else "failed"] += 1
        except Exception:
            tally["failed"] += 1
            logger.warning(
                "Knowledge catch-up failed for %s; it stays queued.",
                row.get("document_id"), exc_info=True,
            )
    logger.info("knowledge_catch_up %s", tally)
    return tally


# How many documents one sweep's catch-up may process. Small: the point is that
# a backlog drains steadily, not that any single sweep clears it.
_DEFAULT_CATCH_UP = 25


def status() -> dict[str, Any]:
    """Operator view of the per-document knowledge layer. Reads; never writes.

    Reports rather than raises in every direction, like
    ``graph_sync.freshness``: disabled, unreadable, and healthy are three
    different answers and each one is useful.
    """
    from app.config import get_settings

    settings = get_settings()
    if not settings.knowledge_enabled:
        return {"enabled": False}
    state: dict[str, Any] = {
        "enabled": True,
        "process_after_index": bool(settings.knowledge_process_after_index),
        "project_per_document": bool(settings.knowledge_project_per_document),
        "max_attempts": settings.knowledge_stage_max_attempts,
    }
    try:
        from app.catalog import knowledge_runs
        from app.knowledge.version import knowledge_version

        state["knowledge_version"] = knowledge_version()
        state["runs"] = knowledge_runs.status_counts()
        state["pending"] = len(
            knowledge_runs.pending(
                max_attempts=settings.knowledge_stage_max_attempts, limit=500
            )
        )
        state["latest"] = [
            {
                "document_id": row["document_id"],
                "doc_version": row["doc_version"],
                "status": row["status"],
                "attempts": row["attempts"],
                "claims_staged": row["claims_staged"],
                "pending_predicates": row["pending_predicates"],
                "projection_status": row["projection_status"],
                "projection_version": row["projection_version"],
                "knowledge_version": row["knowledge_version"],
            }
            for row in knowledge_runs.latest(5)
        ]
        state["recent_errors"] = [
            {
                "document_id": row["document_id"],
                "doc_version": row["doc_version"],
                "attempts": row["attempts"],
                "error": row["last_error"],
            }
            for row in knowledge_runs.recent_errors(5)
        ]
    except Exception as exc:
        logger.debug("Could not read knowledge run state.", exc_info=True)
        state["readable"] = False
        state["error"] = str(exc)
    return state
