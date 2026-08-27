"""The shape of a retrieval trace: one :class:`QueryLog`, many :class:`RetrieverEvent`.

One file per query, one event per call a retriever made. The event is
deliberately generic — ``retriever``, ``operation``, ``request``, ``results`` —
so a fourth store can be traced by calling
:func:`app.observability.retrieval_log.retriever_call` with a new name, and
nothing here has to change.

A ``QueryLog`` is shared across every thread one query fans out onto (the
parallel search legs, the graph's own executor), so appends are serialized by a
lock. Reads happen after the query has finished.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1

#: The three stores traced today. Not a closed set — these name what the
#: summary rolls up by, and an unknown name simply appears alongside them.
QDRANT = "qdrant"
GRAPH = "graph"
MYSQL = "mysql"


def iso(moment: datetime | None = None) -> str:
    """ISO 8601, UTC, milliseconds — the one timestamp format in a trace."""
    return (moment or datetime.now(timezone.utc)).isoformat(timespec="milliseconds")


@dataclass
class RetrieverEvent:
    """One call to one retriever: what it was asked, what came back, how long."""

    retriever: str
    operation: str
    #: Where in the pipeline the call was issued ("dense_pull", "graph_hydrate",
    #: "catalog_query"). Two calls to the same store in one query are told apart
    #: by this, not by their position in the list.
    stage: str = ""
    #: What the store was asked for: collection, filters, limit, SQL, template
    #: id and parameters. Redacted and bounded on the way in.
    request: dict[str, Any] = field(default_factory=dict)
    #: What came back, capped by ``retrieval_log_max_results``. ``result_count``
    #: is the true total either way, so a capped sample never misreports recall.
    results: list[Any] = field(default_factory=list)
    result_count: int = 0
    results_truncated: bool = False
    #: Anything measured about the call that is not a result: score ranges, row
    #: budgets, hydration counts.
    metrics: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    started_at: str = field(default_factory=iso)
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "retriever": self.retriever,
            "operation": self.operation,
            "stage": self.stage,
            "started_at": self.started_at,
            "latency_ms": round(self.latency_ms, 2),
            "request": self.request,
            "result_count": self.result_count,
        }
        # Derived as well as recorded: a caller that keeps counting after the
        # sample filled up (a large result set read one row at a time) moves
        # ``result_count`` without touching the flag, and a trace must never
        # claim it holds every result when it does not.
        if self.results_truncated or len(self.results) < self.result_count:
            out["results_truncated"] = True
        if self.results:
            out["results"] = self.results
        if self.metrics:
            out["metrics"] = self.metrics
        if self.error is not None:
            out["error"] = self.error
        return out


@dataclass
class QueryLog:
    """Everything one user query did, across every retriever it touched."""

    request_id: str
    question: str
    entrypoint: str
    started_at: str
    #: Monotonic origin for the total latency; the wall-clock stamp above is for
    #: reading, this is for measuring.
    started_perf: float
    top_k: int | None = None
    history_turns: int = 0
    #: What query understanding decided (intent, rewritten search query,
    #: filters, capabilities). Filled once, by the pipeline.
    query: dict[str, Any] = field(default_factory=dict)
    events: list[RetrieverEvent] = field(default_factory=list)
    #: The context that actually reached the LLM.
    context: dict[str, Any] = field(default_factory=dict)
    #: How the query ended: intent, cache status, citations, refusal.
    outcome: dict[str, Any] = field(default_factory=dict)
    #: Failures that were not one retriever's own — a pipeline exception, a
    #: fallback that fired. A retriever's own failure lives on its event.
    errors: list[dict[str, Any]] = field(default_factory=list)
    #: Per-stage span timings, shared by reference with the pipeline's own
    #: breakdown, so a trace reports the same numbers the metrics line does.
    stages: dict[str, float] | None = None
    notes: dict[str, Any] = field(default_factory=dict)
    finished_at: str = ""
    total_latency_ms: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    #: The ``ContextVar`` token that made this the active trace, kept here so
    #: whichever thread finishes the query can restore what was active before.
    reset_token: Any = field(default=None, repr=False)

    @classmethod
    def start(
        cls,
        question: str,
        *,
        entrypoint: str,
        top_k: int | None = None,
        history_turns: int = 0,
        stages: dict[str, float] | None = None,
    ) -> "QueryLog":
        return cls(
            request_id=uuid.uuid4().hex,
            question=question,
            entrypoint=entrypoint,
            started_at=iso(),
            started_perf=time.perf_counter(),
            top_k=top_k,
            history_turns=history_turns,
            stages=stages,
        )

    @property
    def day(self) -> str:
        """The UTC date the query started — the directory its file goes in."""
        return self.started_at[:10]

    def add(self, event: RetrieverEvent) -> None:
        with self.lock:
            self.events.append(event)

    def add_error(self, where: str, exc: BaseException | str) -> None:
        entry = {
            "where": where,
            "at": iso(),
            "type": type(exc).__name__ if isinstance(exc, BaseException) else "message",
            "message": str(exc),
        }
        with self.lock:
            self.errors.append(entry)

    def finish(self) -> None:
        if self.finished_at:
            return
        self.total_latency_ms = (time.perf_counter() - self.started_perf) * 1000.0
        self.finished_at = iso()

    # -- read-out ----------------------------------------------------------
    def per_retriever(self) -> dict[str, dict[str, Any]]:
        """Calls, results, latency and failures rolled up per store.

        The question an analyst asks first — what did each retriever cost, and
        what did it return — answered without walking the event list.
        """
        rolled: dict[str, dict[str, Any]] = {}
        for event in self.events:
            bucket = rolled.setdefault(
                event.retriever,
                {"calls": 0, "results": 0, "latency_ms": 0.0, "errors": 0,
                 "stages": []},
            )
            bucket["calls"] += 1
            bucket["results"] += event.result_count
            bucket["latency_ms"] += event.latency_ms
            if event.error is not None:
                bucket["errors"] += 1
            if event.stage and event.stage not in bucket["stages"]:
                bucket["stages"].append(event.stage)
        for bucket in rolled.values():
            bucket["latency_ms"] = round(bucket["latency_ms"], 2)
        return rolled

    def to_dict(self) -> dict[str, Any]:
        rolled = self.per_retriever()
        out: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "timestamp": self.started_at,
            "entrypoint": self.entrypoint,
            "question": self.question,
            "top_k": self.top_k,
            "history_turns": self.history_turns,
            "query": self.query,
            "retrievers": {"invoked": sorted(rolled), "totals": rolled},
            "timings": {
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "total_latency_ms": round(self.total_latency_ms, 2),
                "retrieval_latency_ms": round(
                    sum(e.latency_ms for e in self.events), 2
                ),
                "stages_ms": (
                    {k: round(v, 1) for k, v in sorted(self.stages.items())}
                    if self.stages
                    else {}
                ),
            },
            "events": [e.to_dict() for e in self.events],
            "context": self.context,
            "outcome": self.outcome,
            "errors": list(self.errors),
        }
        if self.notes:
            out["notes"] = self.notes
        return out

    def summary(self) -> dict[str, Any]:
        """One flat row per query for the JSONL digest (pandas-friendly)."""
        rolled = self.per_retriever()
        row: dict[str, Any] = {
            "request_id": self.request_id,
            "timestamp": self.started_at,
            "entrypoint": self.entrypoint,
            "question": self.question,
            "intent": self.query.get("intent"),
            "retrievers": sorted(rolled),
            "total_latency_ms": round(self.total_latency_ms, 2),
            "context_blocks": self.context.get("block_count", 0),
            "cached": self.outcome.get("cached"),
            "answered": self.outcome.get("answered"),
            "errors": len(self.errors) + sum(b["errors"] for b in rolled.values()),
        }
        for name, bucket in rolled.items():
            row[f"{name}_calls"] = bucket["calls"]
            row[f"{name}_results"] = bucket["results"]
            row[f"{name}_latency_ms"] = bucket["latency_ms"]
        return row

    @property
    def failed(self) -> bool:
        """Whether anything in this query went wrong. The ``errors/`` copy
        exists so those traces can be found without reading every file."""
        return bool(self.errors) or any(e.error is not None for e in self.events)
