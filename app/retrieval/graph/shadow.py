"""Run graph retrieval beside production retrieval, and only watch.

Shadow mode exists to collect evidence on live traffic before anything is
routed to the graph. Production retrieval stays authoritative; the graph runs on
the same question and the comparison is written to a log. **The user's answer is
byte-for-byte what it would have been with this module absent.**

That is enforced structurally, not by discipline:

* ``observe`` returns ``None``. There is no value for a caller to use, so no
  caller can accidentally let a shadow result reach an answer.
* It runs on a **background thread**, so graph latency is never added to the
  request. A slow or hanging graph delays nothing.
* Every exception is swallowed and logged. An unreachable Neo4j cannot fail a
  request that had already succeeded without it.
* Work is **dropped** rather than queued when observations are already in
  flight, so a traffic spike cannot grow an unbounded backlog.

The graph package is imported *inside* the worker, so with the flag off this
module costs one boolean check and loads nothing.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)

# Concurrent observations. Small on purpose: shadow work is diagnostic and must
# never compete with request handling for the interpreter.
MAX_WORKERS = 2

# Observations allowed in flight before new ones are dropped. Dropping is the
# correct response to saturation here — a missing sample costs a row in a
# report, a backlog costs the process.
MAX_IN_FLIGHT = 8

_executor: ThreadPoolExecutor | None = None
_lock = threading.Lock()
_in_flight = 0
_dropped = 0


def _executor_for_shadow() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=MAX_WORKERS, thread_name_prefix="graph-shadow"
        )
    return _executor


def _document_ids(blocks: Any) -> list[str]:
    out: list[str] = []
    for block in blocks or []:
        payload = getattr(block, "payload", None) or {}
        document_id = payload.get("document_id")
        if document_id and document_id not in out:
            out.append(document_id)
    return out


def _record(question: str, answer: Any, production_documents: list[str],
            elapsed_ms: float) -> dict[str, Any]:
    """The comparison, flattened for a log line or a JSONL row."""
    route = answer.route
    result = answer.result
    graph_documents = list(result.document_ids) if result else []
    overlap = len(set(graph_documents) & set(production_documents))
    return {
        "question": question[:300],
        "routed": route is not None,
        "template_id": route.template_id if route else None,
        "mode": route.mode if route else None,
        "entity": route.entity_name if route else None,
        "reason": answer.reason,
        "rows": len(result.rows) if result else 0,
        "graph_error": result.error if result else None,
        "hydrated": answer.hydrated,
        "facts_block": answer.facts,
        "blocks": len(answer.blocks),
        "disputed": answer.disputed,
        "graph_documents": len(graph_documents),
        "production_documents": len(production_documents),
        "document_overlap": overlap,
        # Whether the graph found evidence production missed. The reason to run
        # a shadow at all: agreement is reassuring, disagreement is the signal.
        "novel_documents": len(set(graph_documents) - set(production_documents)),
        "graph_ms": round(elapsed_ms, 1),
        "stage_ms": {k: round(v, 1) for k, v in (answer.stage_ms or {}).items()},
    }


def _write(record: dict[str, Any]) -> None:
    from app.config import get_settings

    settings = get_settings()
    logger.info("graph shadow: %s", json.dumps(record, default=str))

    path = getattr(settings, "graph_shadow_log_path", None)
    if not path:
        return
    try:
        from pathlib import Path

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")
    except Exception:
        logger.warning("Could not append to the graph shadow log.", exc_info=True)


def _run(question: str, production_documents: list[str]) -> None:
    global _in_flight
    try:
        from app.retrieval.graph import pipeline, policy

        started = time.perf_counter()
        # The cached index, for the same reason routing uses it: rebuilding it
        # per observation would make the shadow cost more than the thing it
        # observes.
        answer = pipeline.answer(question, index=policy.entity_index())
        elapsed = (time.perf_counter() - started) * 1000
        _write(_record(question, answer, production_documents, elapsed))
    except Exception:
        # A shadow failure is a diagnostic gap, never a user-visible one.
        logger.warning("Graph shadow observation failed.", exc_info=True)
    finally:
        with _lock:
            _in_flight -= 1


def observe(question: str, production_blocks: Any = None) -> None:
    """Compare the graph against production for this question, in the background.

    Returns ``None`` always, and never raises. Safe to call unconditionally —
    the flag is checked here rather than at the call site.
    """
    global _in_flight, _dropped
    try:
        from app.config import get_settings

        if not getattr(get_settings(), "graph_shadow_enabled", False):
            return
        if not question or not question.strip():
            return

        with _lock:
            if _in_flight >= MAX_IN_FLIGHT:
                _dropped += 1
                if _dropped % 50 == 1:
                    logger.info(
                        "Graph shadow saturated; dropped %d observation(s).",
                        _dropped,
                    )
                return
            _in_flight += 1

        documents = _document_ids(production_blocks)
        _executor_for_shadow().submit(_run, question, documents)
    except Exception:
        # Including a failure to submit. Nothing here may propagate.
        logger.warning("Could not start a graph shadow observation.", exc_info=True)
        with _lock:
            _in_flight = max(0, _in_flight - 1)


def stats() -> dict[str, int]:
    """In-flight and dropped counts, for tests and diagnostics."""
    with _lock:
        return {"in_flight": _in_flight, "dropped": _dropped}


def reset() -> None:
    """Drop the executor. For tests; not part of the request path."""
    global _executor, _in_flight, _dropped
    with _lock:
        executor, _executor = _executor, None
        _in_flight = 0
        _dropped = 0
    if executor is not None:
        executor.shutdown(wait=False)
