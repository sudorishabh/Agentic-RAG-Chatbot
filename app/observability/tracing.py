from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator

from app.config import get_settings
from app.observability import metrics as stage_metrics

logger = logging.getLogger("app.observability")

_otel_tracer: Any | None = None
_initialized = False


class Span:

    def __init__(self, name: str, attrs: dict[str, Any]):
        self.name = name
        self.attrs = attrs
        self.start = time.perf_counter()

    def set(self, key: str, value: Any) -> None:
        self.attrs[key] = value

    @property
    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self.start) * 1000.0


@contextmanager
def span(name: str, **attrs: Any) -> Iterator[Span]:
    s = Span(name, dict(attrs))
    otel_cm = None
    otel_span = None
    if _otel_tracer is not None:
        try:
            otel_cm = _otel_tracer.start_as_current_span(name)
            otel_span = otel_cm.__enter__()
        except Exception:  # pragma: no cover
            otel_cm = otel_span = None
    try:
        yield s
    finally:
        if otel_span is not None:
            try:
                for k, v in s.attrs.items():
                    otel_span.set_attribute(k, v)
                otel_cm.__exit__(None, None, None)
            except Exception:  # pragma: no cover
                pass
        stage_metrics.record_stage(s.name, s.elapsed_ms)
        logger.debug("span %s %.1fms %s", s.name, s.elapsed_ms, s.attrs or "")


def record_query_metrics(*, latency_ms: float | None = None, **metrics: Any) -> None:
    settings = get_settings()
    if latency_ms is not None:
        metrics["latency_ms"] = round(latency_ms, 1)
    metrics = {k: v for k, v in metrics.items() if v is not None}
    if settings.metrics_log_enabled:
        logger.info("rag_metrics %s", metrics)
    if _otel_tracer is not None:
        try:
            from opentelemetry import trace

            current = trace.get_current_span()
            for key, value in metrics.items():
                if isinstance(value, dict):  # stages breakdown; OTel wants scalars
                    value = str(value)
                current.set_attribute(f"rag.{key}", value)
        except Exception:  # pragma: no cover
            pass


def _init_otel(settings: Any) -> None:
    global _otel_tracer
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(
            resource=Resource.create({"service.name": settings.otel_service_name})
        )
        if settings.otel_exporter_otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
                )
            )
        trace.set_tracer_provider(provider)
        _otel_tracer = trace.get_tracer("app.rag")
        logger.info("OpenTelemetry tracing enabled (%s).", settings.otel_service_name)
    except Exception:  # pragma: no cover - SDK missing / bad config
        logger.warning("OpenTelemetry requested but unavailable; tracing off.", exc_info=True)


def init_observability(app: Any | None = None) -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True
    settings = get_settings()

    if settings.otel_enabled:
        _init_otel(settings)
        if app is not None and _otel_tracer is not None:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

                FastAPIInstrumentor.instrument_app(app)
            except Exception:  # pragma: no cover
                logger.warning("FastAPI OTel instrumentation unavailable.", exc_info=True)
