"""Keeping the knowledge graph in step with the corpus, without depending on it.

Nothing in ingestion wrote Neo4j. The projection existed only as
``scripts.project_graph``, run by hand — so the graph drifted from the moment
someone stopped running it, monotonically and invisibly.

Why this is a sweep-level step, not a per-document one
------------------------------------------------------
Projection is a whole-graph pass: it reads the staged entities and claims,
rewrites the current-state edges and removes the previous generation. Running it
per document would repeat that pass once per document, and a document is not
even the unit it operates on — claims are. It also has to be able to fail
without the document failing, which a synchronous step inside ``_handle`` cannot
offer. So it runs once, after the sweep, on the same thread the sweep finished
on.

Why it cannot break ingestion
-----------------------------
Neo4j is a derived store. Everything it holds is re-derivable from MySQL, which
is why ``scripts.project_graph --rebuild`` is always a valid repair — so an
unreachable graph is a degraded knowledge layer and nothing more. Every entry
point here returns rather than raises, and the sweep's result is computed and
logged before any of this runs. A graph outage costs a log line.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["project_after_sweep", "freshness", "is_stale"]


def _knowledge_layer_ready() -> bool:
    """Whether this deployment has a graph to keep fresh at all.

    ``knowledge_enabled`` off means nothing here opens a connection — the flag's
    documented contract is that ingestion and retrieval behave exactly as they
    do without the knowledge layer.
    """
    from app.config import get_settings

    return bool(get_settings().knowledge_enabled)


def freshness() -> dict[str, Any]:
    """How current the projection is. Reads the graph; never writes.

    Reports rather than raises in every direction: disabled, unreachable, never
    projected, and projected-at-a-known-time are four different answers and each
    one is useful.
    """
    if not _knowledge_layer_ready():
        return {"enabled": False}
    try:
        from app.core.clients import graph_available

        if not graph_available():
            return {"enabled": True, "reachable": False}
        from app.knowledge.graph.verify import projection_freshness

        state = projection_freshness()
    except Exception as exc:
        logger.debug("Could not read projection freshness.", exc_info=True)
        return {"enabled": True, "reachable": False, "error": str(exc)}
    return {"enabled": True, "reachable": True, **state.as_dict()}


def is_stale(report: dict[str, Any] | None = None) -> bool:
    """Whether the projection is older than the deployment tolerates.

    A graph that is disabled, unreachable or has never been projected is not
    "stale" — those are their own conditions, reported separately. Staleness is
    specifically "it was projected, and that was too long ago", which is the one
    that says the scheduled projection has stopped happening.
    """
    from app.config import get_settings

    state = report if report is not None else freshness()
    age = state.get("age_seconds")
    if age is None:
        return False
    return age > get_settings().graph_projection_max_age_seconds


def project_after_sweep() -> dict[str, Any] | None:
    """Refresh the projection at the end of a sweep. Never raises.

    Returns the projection report, or None when it did not run — disabled, not
    configured to run here, or the graph was unreachable. MySQL and Qdrant are
    already written and the sweep's outcome is already decided by the time this
    is called, so every one of those is a no-op rather than a failure.
    """
    from app.config import get_settings

    settings = get_settings()
    if not _knowledge_layer_ready() or not settings.graph_project_after_sweep:
        return None
    try:
        from app.core.clients import graph_available

        if not graph_available():
            logger.warning(
                "Neo4j is unreachable; the knowledge graph was not refreshed and "
                "is now behind the corpus. Ingestion is unaffected — the graph "
                "rebuilds from MySQL with scripts.project_graph."
            )
            return None

        from app.knowledge.graph.project import project
        from app.knowledge.graph.schema import ensure_graph_schema

        ensure_graph_schema()
        report = project().as_dict()
    except Exception:
        logger.exception(
            "Graph projection failed; the sweep and its documents are unaffected. "
            "The graph is a projection of MySQL and can be rebuilt at any time."
        )
        return None

    logger.info(
        "graph_projection version=%s nodes=%s relationships=%s",
        report.get("projection_version"), report.get("nodes"), report.get("relationships"),
    )
    return report
