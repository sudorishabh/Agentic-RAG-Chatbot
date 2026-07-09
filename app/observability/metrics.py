"""In-process stage timing metrics: which pipeline stage takes how much time.

Every ``tracing.span()`` reports its elapsed time here, keyed by span name
("rag.search", "ingest.embed", ...). ``snapshot()`` returns per-stage
aggregates (count / total / avg / p50 / p95 / max) served by
``GET /metrics/timings``, and ``collect_into()`` gathers a per-request
breakdown that ends up on the ``rag_metrics`` log line.

The registry is per-process — each uvicorn worker keeps its own numbers and
they reset on restart. Parent spans (e.g. "rag.answer_query") include the
time of the child stages they wrap, so stage totals overlap by design.
"""

from __future__ import annotations

import threading
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Iterator

_WINDOW = 512  # recent samples kept per stage; percentiles cover this window


class _StageStats:
    __slots__ = ("count", "total_ms", "max_ms", "samples")

    def __init__(self) -> None:
        self.count = 0
        self.total_ms = 0.0
        self.max_ms = 0.0
        self.samples: deque[float] = deque(maxlen=_WINDOW)

    def add(self, elapsed_ms: float) -> None:
        self.count += 1
        self.total_ms += elapsed_ms
        if elapsed_ms > self.max_ms:
            self.max_ms = elapsed_ms
        self.samples.append(elapsed_ms)


_lock = threading.Lock()
_stages: dict[str, _StageStats] = {}
_since = datetime.now(timezone.utc)

_breakdown: ContextVar[dict[str, float] | None] = ContextVar(
    "stage_breakdown", default=None
)


def record_stage(name: str, elapsed_ms: float) -> None:
    with _lock:
        stats = _stages.get(name)
        if stats is None:
            stats = _stages[name] = _StageStats()
        stats.add(elapsed_ms)
    per_request = _breakdown.get()
    if per_request is not None:
        per_request[name] = per_request.get(name, 0.0) + elapsed_ms


@contextmanager
def collect_into(breakdown: dict[str, float]) -> Iterator[None]:
    """Additionally route this context's span timings into ``breakdown``.

    The caller owns the dict, so the collected numbers survive even when the
    context doesn't: the chat SSE stream advances the RAG generator with one
    threadpool hop per event (see app.api.chat._sse), so spans after the first
    yield run in fresh context copies. Those still hit the global registry —
    only the per-request dict misses them — and the reset below may then see
    a token from another context, which is harmless because that context copy
    is discarded anyway.
    """
    token = _breakdown.set(breakdown)
    try:
        yield
    finally:
        try:
            _breakdown.reset(token)
        except ValueError:  # generator resumed in a different context
            pass


def _percentile(ordered: list[float], q: float) -> float:
    return ordered[max(0, min(len(ordered) - 1, round(q * (len(ordered) - 1))))]


def snapshot() -> dict[str, Any]:
    with _lock:
        copied = {
            name: (s.count, s.total_ms, s.max_ms, list(s.samples))
            for name, s in _stages.items()
        }
    stages = []
    for name, (count, total, max_ms, samples) in sorted(
        copied.items(), key=lambda item: item[1][1], reverse=True
    ):
        ordered = sorted(samples)
        stages.append(
            {
                "stage": name,
                "count": count,
                "total_ms": round(total, 1),
                "avg_ms": round(total / count, 1),
                "p50_ms": round(_percentile(ordered, 0.50), 1),
                "p95_ms": round(_percentile(ordered, 0.95), 1),
                "max_ms": round(max_ms, 1),
            }
        )
    return {"since": _since.isoformat(), "window": _WINDOW, "stages": stages}


def reset() -> None:
    global _since
    with _lock:
        _stages.clear()
        _since = datetime.now(timezone.utc)
