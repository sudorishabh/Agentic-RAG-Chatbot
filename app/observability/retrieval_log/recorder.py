"""The API the retrieval path calls, and the switch that makes it free.

One flag decides everything: ``is_retrieval_log``. With it off, every function
here costs a boolean read and a ``ContextVar.get`` — no trace object, no
serialization, no directory, no write. That is the whole reason the *shape* of
this API is what it is: call sites pass a callable (or nothing) rather than a
built dictionary, so the cost of describing a request is paid only when someone
asked for the description.

    with retrieval_log.qdrant_call("vector_search", stage="dense_pull",
                                  request=lambda: {"limit": limit}) as call:
        response = client.query_points(...)
        call.qdrant_results(response.points)

Two properties every call site depends on:

* **Nothing here raises.** A trace is worth less than an answer, so a failure to
  record is swallowed and logged. The one exception that *is* propagated is the
  application's own — the ``with`` block records it and re-raises, so a
  retriever's failure is captured without being hidden from the caller.
* **Threads are handled explicitly.** A query fans out onto worker threads (the
  parallel search legs, the graph's executor) and a ``ContextVar`` set on the
  request thread is *not* visible there. :func:`bound` carries the active trace
  across that boundary; it returns the function unchanged when logging is off,
  so a disabled build pays nothing for the plumbing.
"""
from __future__ import annotations

import functools
import logging
import time
from contextvars import ContextVar
from typing import Any, Callable, Iterable, Sequence

from app.config import get_settings
from app.observability.retrieval_log import views
from app.observability.retrieval_log.models import (
    GRAPH,
    MYSQL,
    QDRANT,
    QueryLog,
    RetrieverEvent,
)
from app.observability.retrieval_log.safe import jsonable

logger = logging.getLogger(__name__)

_current: ContextVar[QueryLog | None] = ContextVar("retrieval_log", default=None)


def enabled() -> bool:
    """Whether ``is_retrieval_log`` is set. Read from configuration every time —
    never captured at import — so a test or a reload can flip it."""
    try:
        return bool(get_settings().is_retrieval_log)
    except Exception:  # pragma: no cover - unreadable settings must not break a query
        return False


def active() -> QueryLog | None:
    """The trace this thread is contributing to, or None."""
    return _current.get()


class _Limits:
    """The bounds and the rendering one event is recorded under, read per call."""

    __slots__ = ("max_results", "text_limit", "include_text", "compact")

    def __init__(self) -> None:
        settings = get_settings()
        self.max_results = max(0, int(settings.retrieval_log_max_results))
        self.text_limit = max(0, int(settings.retrieval_log_max_text_chars))
        self.include_text = bool(settings.retrieval_log_include_text)
        # "compact" (the default) renders one line per retrieved item; "full"
        # renders the structured object. See `views` for why the default is the
        # readable one.
        self.compact = (
            str(getattr(settings, "retrieval_log_detail", "compact") or "compact")
            .strip().lower() != "full"
        )


class Call:
    """One in-flight retriever call, and the handle used to describe it.

    A context manager rather than a pair of functions so the latency covers
    exactly the call, and so an exception cannot leave the event unrecorded.
    """

    __slots__ = ("_log", "_event", "_limits", "_started")

    def __init__(
        self,
        log: QueryLog,
        retriever: str,
        operation: str,
        *,
        stage: str,
        request: dict[str, Any] | Callable[[], dict[str, Any]] | None,
    ) -> None:
        self._log = log
        self._limits = _Limits()
        self._event = RetrieverEvent(
            retriever=retriever, operation=operation, stage=stage
        )
        self.describe(request)
        self._started = time.perf_counter()

    # -- describing the request -------------------------------------------
    def describe(
        self, request: dict[str, Any] | Callable[[], dict[str, Any]] | None, **extra: Any
    ) -> None:
        """Merge fields into the request record. Accepts a callable so the caller
        can build the description lazily; a failure to build it is not a failure
        of the query, so it is recorded as a note and the call continues."""
        fields: dict[str, Any] = {}
        try:
            if callable(request):
                request = request()
            if request:
                fields.update(request)
            if extra:
                fields.update(extra)
            # The whole mapping goes through `jsonable`, not each value, so a
            # top-level field named like a secret is redacted by the same rule
            # as a nested one.
            converted = jsonable(fields, limit=self._limits.text_limit)
            if isinstance(converted, dict):
                if self._limits.compact:
                    converted = views.compact_request(converted)
                self._event.request.update(converted)
        except Exception:
            self._event.request.setdefault("_describe_failed", True)
            logger.debug("Could not describe a retrieval request.", exc_info=True)

    def note(self, **metrics: Any) -> None:
        """Record something measured about the call that is not a result."""
        try:
            converted = jsonable(metrics, limit=self._limits.text_limit)
            if isinstance(converted, dict):
                self._event.metrics.update(converted)
        except Exception:  # pragma: no cover - defence in depth
            logger.debug("Could not record retrieval metrics.", exc_info=True)

    # -- recording results ------------------------------------------------
    def _results(self, rendered: list[Any], total: int) -> None:
        self._event.results = rendered
        self._event.result_count = total
        self._event.results_truncated = len(rendered) < total

    def qdrant_results(self, points: Sequence[Any]) -> None:
        """Points straight off a Qdrant response."""
        try:
            points = list(points or [])
            rendered = (
                views.qdrant_points_compact(
                    points,
                    limit=self._limits.max_results,
                    include_text=self._limits.include_text,
                )
                if self._limits.compact
                else views.qdrant_points(
                    points,
                    limit=self._limits.max_results,
                    include_text=self._limits.include_text,
                    text_limit=self._limits.text_limit,
                )
            )
            self._results(rendered, len(points))
        except Exception:  # pragma: no cover - defence in depth
            self._degrade()

    def candidate_results(self, items: Sequence[Any]) -> None:
        """Search candidates, with all three of their scores."""
        try:
            items = list(items or [])
            rendered = (
                views.candidates_compact(
                    items,
                    limit=self._limits.max_results,
                    include_text=self._limits.include_text,
                )
                if self._limits.compact
                else views.candidates(
                    items,
                    limit=self._limits.max_results,
                    include_text=self._limits.include_text,
                    text_limit=self._limits.text_limit,
                )
            )
            self._results(rendered, len(items))
        except Exception:  # pragma: no cover - defence in depth
            self._degrade()

    def row_results(self, rows: Iterable[Any], *, total: int | None = None) -> None:
        """Graph rows or SQL rows."""
        try:
            listed = list(rows or [])
            count = len(listed) if total is None else total
            if self._limits.compact and count > views.BULK_ROWS:
                # A whole vocabulary, not an answer. See `views.BULK_ROWS`.
                self._event.results = []
                self._event.result_count = count
                self._event.metrics["rows_sampled"] = False
                return
            rendered = (
                views.rows_compact(listed, limit=self._limits.max_results)
                if self._limits.compact
                else views.rows(
                    listed, limit=self._limits.max_results,
                    text_limit=self._limits.text_limit,
                )
            )
            self._results(rendered, count)
        except Exception:  # pragma: no cover - defence in depth
            self._degrade()

    def count_only(self, total: int) -> None:
        """A call whose results are counted but not kept."""
        self._event.result_count = int(total or 0)

    @property
    def max_results(self) -> int:
        """How many results this event will keep in full — so a caller reading
        rows one at a time can stop re-rendering a sample that cannot change."""
        return self._limits.max_results

    def _degrade(self) -> None:
        self._event.metrics["_results_unrecorded"] = True
        logger.debug("Could not record retrieval results.", exc_info=True)

    # -- failures ----------------------------------------------------------
    def fail(self, exc: BaseException | str, *, where: str = "") -> None:
        """Record a failure the caller is handling itself.

        Several retrievers catch their own exception and degrade — a hydration
        batch that could not be fetched, a scroll that failed. Those never reach
        ``__exit__``, and a trace that showed them as empty-but-fine would hide
        exactly the thing it exists to reveal.
        """
        self._event.error = {
            "type": type(exc).__name__ if isinstance(exc, BaseException) else "message",
            "message": str(exc)[:2000],
            "where": where or self._event.stage,
        }

    # -- committing --------------------------------------------------------
    def commit(self, *, latency_ms: float | None = None) -> None:
        """Attach the event to the trace, with a latency someone else timed."""
        try:
            self._event.latency_ms = (
                (time.perf_counter() - self._started) * 1000.0
                if latency_ms is None
                else float(latency_ms)
            )
            self._log.add(self._event)
        except Exception:  # pragma: no cover - logging must not add a failure
            logger.debug("Could not record a retrieval event.", exc_info=True)

    # -- context-manager protocol ------------------------------------------
    def __enter__(self) -> "Call":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if exc is not None and self._event.error is None:
            self.fail(exc)
        self.commit()
        return False  # never swallow the application's exception


class _NullCall:
    """What every instrumentation point gets when logging is off: a shared
    object whose methods do nothing. No allocation, no serialization, no work."""

    __slots__ = ()

    def describe(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    note = describe
    qdrant_results = describe
    candidate_results = describe
    row_results = describe
    count_only = describe
    fail = describe

    def __enter__(self) -> "_NullCall":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False


NULL_CALL = _NullCall()


def retriever_call(
    retriever: str,
    operation: str,
    *,
    stage: str = "",
    request: dict[str, Any] | Callable[[], dict[str, Any]] | None = None,
) -> Any:
    """Trace one call to one retriever. Use as a context manager.

    ``retriever`` is a free-form name — "qdrant", "graph", "mysql" today; a new
    store needs no change here or anywhere else in this package.
    """
    log = _current.get()
    if log is None:
        return NULL_CALL
    try:
        return Call(log, retriever, operation, stage=stage, request=request)
    except Exception:  # pragma: no cover - defence in depth
        logger.debug("Could not open a retrieval trace event.", exc_info=True)
        return NULL_CALL


def qdrant_call(operation: str, **kwargs: Any) -> Any:
    return retriever_call(QDRANT, operation, **kwargs)


def graph_call(operation: str, **kwargs: Any) -> Any:
    return retriever_call(GRAPH, operation, **kwargs)


def mysql_call(operation: str, **kwargs: Any) -> Any:
    return retriever_call(MYSQL, operation, **kwargs)


def record(
    retriever: str,
    operation: str,
    *,
    stage: str = "",
    request: dict[str, Any] | Callable[[], dict[str, Any]] | None = None,
    latency_ms: float = 0.0,
    result_count: int = 0,
    rows: Iterable[Any] | None = None,
    metrics: dict[str, Any] | None = None,
    error: BaseException | str | None = None,
) -> None:
    """Record a call that has already happened, with a latency someone else timed.

    For the retrievers that measure themselves — the graph reports its own
    per-stage timings — where wrapping the call in :func:`retriever_call` would
    only measure it twice.
    """
    log = _current.get()
    if log is None:
        return
    try:
        call = Call(log, retriever, operation, stage=stage, request=request)
        if rows is not None:
            call.row_results(rows, total=result_count or None)
        else:
            call.count_only(result_count)
        if metrics:
            call.note(**metrics)
        if error is not None:
            call.fail(error)
        call.commit(latency_ms=latency_ms or 0.0)
    except Exception:  # pragma: no cover - defence in depth
        logger.debug("Could not record a retrieval event.", exc_info=True)


# -- query-level notes -----------------------------------------------------
#
# Each takes the trace as an optional positional argument. The default — this
# thread's active trace — is what every call site inside retrieval wants. The
# explicit form exists for the one place that cannot use it: the SSE driver
# advances the answer generator with a threadpool hop per event (see
# `app.observability.metrics.collect_into`), so everything the pipeline records
# *after* the first token runs in a fresh context where the ContextVar is unset.
# Recording the outcome there silently did nothing — every streamed query wrote
# `"outcome": {}` — and passing the object closes that hole for good.
#
# Positional-only, so a field named "log" cannot collide with it.
def note_query(log: QueryLog | None = None, /, **fields: Any) -> None:
    """What query understanding decided: intent, search query, filters, scope."""
    target = log or _current.get()
    if target is None:
        return
    _merge(target.query, fields)


def note_outcome(log: QueryLog | None = None, /, **fields: Any) -> None:
    """How the query ended: cached, answered, citations, refusal."""
    target = log or _current.get()
    if target is None:
        return
    _merge(target.outcome, fields)


def note(log: QueryLog | None = None, /, **fields: Any) -> None:
    """Anything else worth keeping that is not a retriever call."""
    target = log or _current.get()
    if target is None:
        return
    _merge(target.notes, fields)


def note_context(
    blocks: Sequence[Any], *, rendered: Callable[[], str] | str | None = None
) -> None:
    """The context that reached the LLM — the last thing a trace records, and the
    one that makes the rest of it answerable ("was the right passage retrieved,
    and did it survive to the prompt?").

    ``rendered`` is the assembled context string, or a callable producing it.
    Pass it wherever the answer is generated from these blocks, so the trace
    holds what the model was actually sent rather than a reconstruction of it —
    a callable, because rendering it costs a string join that a disabled trace
    must not pay for.
    """
    log = _current.get()
    if log is None:
        return
    try:
        limits = _Limits()
        try:
            text = rendered() if callable(rendered) else rendered
        except Exception:
            # A formatter failure costs the rendered string, not the blocks.
            logger.debug("Could not render the context for the trace.", exc_info=True)
            text = None
        log.context = views.context_blocks(
            blocks,
            limit=limits.max_results,
            include_text=limits.include_text,
            text_limit=limits.text_limit,
            compact=limits.compact,
            rendered=text,
        )
    except Exception:  # pragma: no cover - defence in depth
        logger.debug("Could not record the retrieval context.", exc_info=True)


def note_error(where: str, exc: BaseException | str) -> None:
    """A failure that belongs to the query rather than to one retriever."""
    log = _current.get()
    if log is None:
        return
    try:
        log.add_error(where, exc)
    except Exception:  # pragma: no cover - defence in depth
        logger.debug("Could not record a retrieval error.", exc_info=True)


def _merge(target: dict[str, Any], fields: dict[str, Any]) -> None:
    try:
        limit = get_settings().retrieval_log_max_text_chars
        converted = jsonable(
            {k: v for k, v in fields.items() if v is not None}, limit=limit
        )
        if isinstance(converted, dict):
            if _Limits().compact:
                converted = views.compact_request(converted)
            target.update(converted)
    except Exception:  # pragma: no cover - defence in depth
        logger.debug("Could not record a retrieval note.", exc_info=True)


# -- lifecycle -------------------------------------------------------------
def start(
    question: str,
    *,
    entrypoint: str,
    top_k: int | None = None,
    history: Sequence[Any] | None = None,
    stages: dict[str, float] | None = None,
) -> QueryLog | None:
    """Begin a trace and make it this thread's active one, or return None.

    Callers normally want :func:`query_log`, which also finishes and writes it.
    """
    if not enabled():
        return None
    try:
        log = QueryLog.start(
            question,
            entrypoint=entrypoint,
            top_k=top_k,
            history_turns=len(history or []),
            stages=stages,
        )
    except Exception:  # pragma: no cover - defence in depth
        logger.debug("Could not start a retrieval trace.", exc_info=True)
        return None
    log.reset_token = _current.set(log)
    return log


def finish(log: QueryLog | None) -> None:
    """Close a trace, restore the previous one, and write the file."""
    if log is None:
        return
    token, log.reset_token = log.reset_token, None
    if token is not None:
        try:
            _current.reset(token)
        except ValueError:
            # The generator was resumed in a different context than the one that
            # set the token — the SSE driver does exactly that, one threadpool
            # hop per event (see app.observability.metrics.collect_into). The
            # context copy is discarded anyway, so there is nothing to restore.
            pass
    try:
        log.finish()
    except Exception:  # pragma: no cover - defence in depth
        logger.debug("Could not close a retrieval trace.", exc_info=True)
        return
    from app.observability.retrieval_log import sink

    sink.write(log)


class query_log:
    """Trace one user query, from the first retriever call to the answer.

    A class rather than ``@contextmanager`` so that the disabled path allocates
    one empty object and does nothing else, and so a generator resumed on
    another thread (the SSE stream) still finishes exactly once.
    """

    __slots__ = ("log",)

    def __init__(
        self,
        question: str,
        *,
        entrypoint: str,
        top_k: int | None = None,
        history: Sequence[Any] | None = None,
        stages: dict[str, float] | None = None,
    ) -> None:
        self.log = start(
            question,
            entrypoint=entrypoint,
            top_k=top_k,
            history=history,
            stages=stages,
        )

    def __enter__(self) -> QueryLog | None:
        return self.log

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if self.log is not None and exc is not None:
            note_error("pipeline", exc)
        finish(self.log)
        self.log = None
        return False  # the query's own failure is the caller's to handle


def bound(fn: Callable[..., Any]) -> Callable[..., Any]:
    """``fn``, wrapped so it contributes to *this* thread's trace when it runs on
    another one.

    Worker threads start with an empty context, so retrieval's parallel legs and
    the graph's executor would otherwise record nothing. Returns ``fn`` itself
    when there is no active trace, which is what makes this free when logging is
    off — and safe to leave at every fan-out point.
    """
    log = _current.get()
    if log is None:
        return fn

    @functools.wraps(fn)
    def runner(*args: Any, **kwargs: Any) -> Any:
        token = _current.set(log)
        try:
            return fn(*args, **kwargs)
        finally:
            _current.reset(token)

    return runner
