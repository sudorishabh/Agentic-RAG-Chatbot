"""End-to-end graph retrieval: question in, context blocks out.

    question -> route -> template -> Neo4j -> ids -> Qdrant -> rerank -> context

Two things this deliberately does **not** do:

* **It does not introduce a generation architecture.** The last two steps are
  the existing ``app.retrieval.reranker.rerank`` and
  ``app.retrieval.context_builder.build_context``; a graph answer becomes the
  same ``ContextBlock`` list every other answer is built from.
* **It does not touch the default retrieval path.** Nothing in
  ``app/retrieval/retriever.py`` or ``app/pipeline`` imports this module, and
  ``graph_retrieval_enabled`` is off. With the flag down this code is unreachable
  from a request.

Failure is a value at every step. No route, an unreachable graph, an empty
traversal or a failed hydration all return an empty list, and the caller falls
back to ordinary retrieval — the graph is an enrichment, and no question should
fail because it was unavailable.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GraphAnswer:
    """A graph-retrieved answer, with the trail that produced it."""

    blocks: list[Any] = field(default_factory=list)
    route: Any = None
    result: Any = None
    hydrated: int = 0
    elapsed_ms: float = 0.0
    stage_ms: dict[str, float] = field(default_factory=dict)
    reason: str = ""

    @property
    def answered(self) -> bool:
        return bool(self.blocks)

    @property
    def disputed(self) -> bool:
        """Whether any supporting claim is contradicted.

        A caller presenting this answer must say so. Current-state templates
        cannot produce it — a disputed claim gets no current edge — so it only
        arises for historical questions, where showing a labelled contradiction
        is better than hiding it.
        """
        return bool(self.result and self.result.has_disputed)

    def summary(self) -> dict[str, Any]:
        return {
            "answered": self.answered,
            "route": (
                {
                    "template_id": self.route.template_id,
                    "mode": self.route.mode,
                    "entity": self.route.entity_name,
                    "reason": self.route.reason,
                }
                if self.route
                else None
            ),
            "rows": len(self.result.rows) if self.result else 0,
            "hydrated_chunks": self.hydrated,
            "blocks": len(self.blocks),
            "disputed": self.disputed,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "stage_ms": {k: round(v, 1) for k, v in self.stage_ms.items()},
            "reason": self.reason,
        }


def answer(
    question: str,
    *,
    index: Any = None,
    limit: int | None = None,
    top_k: int | None = None,
    as_of: str | None = None,
    rerank_results: bool = True,
) -> GraphAnswer:
    """Answer one question from the graph, or return empty and explain why."""
    from app.config import get_settings
    from app.retrieval.graph import hydrate as hydration
    from app.retrieval.graph import router as routing
    from app.retrieval.graph import traverse

    started = time.perf_counter()
    out = GraphAnswer()
    stage: dict[str, float] = {}

    def _mark(name: str, since: float) -> float:
        now = time.perf_counter()
        stage[name] = (now - since) * 1000
        return now

    mark = started
    outcome = routing.route(question, index=index, as_of=as_of)
    mark = _mark("route", mark)
    if not outcome.routed:
        out.reason = outcome.reason
        out.stage_ms = stage
        out.elapsed_ms = (time.perf_counter() - started) * 1000
        return out
    out.route = outcome.route

    result = traverse.run_template(
        outcome.route.template_id, outcome.route.parameters, limit=limit
    )
    mark = _mark("neo4j", mark)
    out.result = result
    if result.error:
        out.reason = f"graph query failed: {result.error}"
        out.stage_ms = stage
        out.elapsed_ms = (time.perf_counter() - started) * 1000
        return out
    if result.empty:
        out.reason = "graph query returned no rows"
        out.stage_ms = stage
        out.elapsed_ms = (time.perf_counter() - started) * 1000
        return out

    candidates = hydration.hydrate(result)
    mark = _mark("qdrant", mark)
    out.hydrated = len(candidates)
    if not candidates:
        out.reason = "no source evidence could be hydrated"
        out.stage_ms = stage
        out.elapsed_ms = (time.perf_counter() - started) * 1000
        return out

    settings = get_settings()
    ranked = candidates
    if rerank_results:
        from app.retrieval.reranker import rerank

        # The existing reranker, unchanged. A graph answer is ranked the same way
        # every other answer is, so nothing new has to be tuned or trusted.
        ranked = rerank(question, candidates)
        mark = _mark("rerank", mark)

    from app.retrieval.context_builder import build_context

    out.blocks = build_context(
        ranked, limit=top_k or settings.retrieval_top_k, segregate=False
    )
    _mark("context", mark)
    out.stage_ms = stage
    out.elapsed_ms = (time.perf_counter() - started) * 1000
    out.reason = outcome.route.reason
    logger.info("Graph answer: %s", out.summary())
    return out
