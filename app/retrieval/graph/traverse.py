"""Execute a registry template against Neo4j and return structured results.

The only module that talks to the graph on the read path, and it accepts a
``template_id`` plus parameters — never a query. Sessions are opened read-only
(``read_session``), so this path structurally cannot write, which matters
because Neo4j Community has no role-based access control to enforce it for us.

Failure is a value, not an exception: an unreachable graph returns an empty
result and the caller falls back to ordinary retrieval. The graph is an
enrichment, and no question should fail because it was unavailable.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.retrieval.graph import templates as reg

logger = logging.getLogger(__name__)

# A query that has not answered in this long is not going to help a chat turn.
QUERY_TIMEOUT_SECONDS = 5.0


@dataclass
class GraphResult:
    """What a graph query found: identifiers and structure, never text."""

    template_id: str
    mode: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    entity_ids: list[str] = field(default_factory=list)
    claim_ids: list[str] = field(default_factory=list)
    chunk_ids: list[str] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    truncated: bool = False
    error: str | None = None

    @property
    def empty(self) -> bool:
        return not self.rows

    @property
    def has_disputed(self) -> bool:
        """Whether any row rests on a contradicted claim.

        Current-state templates can never return one — a disputed claim gets no
        current edge — so this only fires on historical queries, where the row
        must be presented as disputed rather than as fact.
        """
        return any(row.get("status") == "disputed" for row in self.rows)

    def summary(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id, "mode": self.mode,
            "rows": len(self.rows), "claims": len(self.claim_ids),
            "chunks": len(self.chunk_ids), "documents": len(self.document_ids),
            "elapsed_ms": round(self.elapsed_ms, 1),
            "truncated": self.truncated, "disputed": self.has_disputed,
            "error": self.error,
        }


_ID_FIELDS = (
    ("entity_ids", ("subject_id", "object_id", "project_id", "person_id",
                    "funder_id", "organization_id",
                    # The predicate-parameterized templates name their ends by
                    # position rather than by type, since one query serves every
                    # approved predicate.
                    "anchor_id", "mid_id", "far_id")),
    ("claim_ids", ("claim_id", "funding_claim_id", "via_claim_id")),
    ("chunk_ids", ("chunk_id",)),
    ("document_ids", ("document_id",)),
)


def _collect(result: GraphResult) -> None:
    """Gather the identifiers a hydration step will need, deduplicated and
    order-stable so a repeated query hydrates the same way."""
    buckets: dict[str, list[str]] = {name: [] for name, _ in _ID_FIELDS}
    seen: dict[str, set[str]] = {name: set() for name, _ in _ID_FIELDS}
    for row in result.rows:
        for name, keys in _ID_FIELDS:
            for key in keys:
                value = row.get(key)
                if isinstance(value, str) and value and value not in seen[name]:
                    seen[name].add(value)
                    buckets[name].append(value)
    result.entity_ids = buckets["entity_ids"]
    result.claim_ids = buckets["claim_ids"]
    result.chunk_ids = buckets["chunk_ids"]
    result.document_ids = buckets["document_ids"]


def run_template(
    template_id: str,
    params: dict[str, Any],
    *,
    limit: int | None = None,
    session: Any = None,
    mode: str | None = None,
) -> GraphResult:
    """Run one registry template. Never raises; never accepts Cypher.

    ``mode`` overrides the template's own. The predicate-parameterized templates
    read Claim nodes whichever period they are asked about, so their declared
    mode describes the storage rather than the question: the *same* template
    answers "who leads this now" and "who led it in 2015", differing only in the
    window bound into it. The caller — which knows which question was asked —
    states the mode so that everything downstream that presents a result
    (row budget, the "including past relationships" heading, the current/
    historical distinction in the answer) is driven by the question rather than
    by an implementation detail. An override is still checked against the
    closed set of modes.
    """
    try:
        template = reg.get(template_id)
    except reg.UnknownTemplate as exc:
        logger.warning("Rejected unknown template: %s", exc)
        return GraphResult(template_id, "unknown", error=str(exc))

    effective_mode = template.mode
    if mode is not None:
        if mode not in reg.MODES:
            logger.warning("Rejected unknown result mode: %r", mode)
            return GraphResult(
                template.template_id, template.mode,
                error=f"unknown mode: {mode!r}",
            )
        effective_mode = mode

    result = GraphResult(template.template_id, effective_mode)
    try:
        checked = reg.validate_parameters(template, params, limit=limit)
    except reg.InvalidParameter as exc:
        logger.warning("Rejected parameters for %s: %s", template_id, exc)
        result.error = str(exc)
        return result

    started = time.perf_counter()
    try:
        if session is not None:
            records = session.run(template.cypher, **checked)
            result.rows = [dict(r) for r in records]
        else:
            from app.core.clients.graph import read_session

            with read_session() as opened:
                records = opened.run(template.cypher, **checked)
                result.rows = [dict(r) for r in records]
    except Exception as exc:
        # The graph is an enrichment. An outage costs the graph leg, never the
        # answer, so this degrades to an empty result and the caller falls back.
        logger.warning("Graph query %s failed.", template_id, exc_info=True)
        result.error = f"{type(exc).__name__}: {exc}"
        result.elapsed_ms = (time.perf_counter() - started) * 1000
        return result

    result.elapsed_ms = (time.perf_counter() - started) * 1000
    result.truncated = len(result.rows) >= checked["limit"]
    _collect(result)
    return result
