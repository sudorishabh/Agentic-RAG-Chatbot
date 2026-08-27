"""Cross-cutting instrumentation. Imported by every layer, imports none of them.

:mod:`.tracing` provides the ``span()`` context manager (and optional
OpenTelemetry export); :mod:`.metrics` is the in-process registry behind
``GET /metrics/timings``.
"""
