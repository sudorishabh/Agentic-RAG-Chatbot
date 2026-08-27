"""Per-query retrieval traces: what each retriever was asked, and what it returned.

Turned on with one environment key::

    is_retrieval_log=true

and then every query writes one JSON file under ``logs/<date>/`` holding the
whole retrieval pipeline: the Qdrant pulls (collection, filters, limit, hit ids,
scores, payload metadata, text, latency), the graph's route and Cypher template
with its rows and identifiers, every MySQL statement with its parameters, tables
and rows, and the context that finally reached the LLM — plus per-retriever
totals, per-stage timings and anything that failed. With the flag off, each
instrumentation point is a boolean read and nothing is built, serialized or
written.

Why it lives here
-----------------
``app/observability`` is layer 1: it may be imported by every layer and imports
none of them (``tests/test_architecture.py`` asserts this). A trace has to be
written from the client gateways, from retrieval, from the catalog and from the
pipeline, so it can only live at the bottom. The consequence is that this
package never imports a ``Candidate``, a ``ContextBlock`` or a Qdrant model —
:mod:`.views` reads them by duck-typing instead.

The modules
-----------
:mod:`.recorder`  the API the application calls: :func:`query_log` per request,
                  :func:`qdrant_call` / :func:`graph_call` / :func:`mysql_call`
                  per retriever call, :func:`bound` to carry a trace onto a
                  worker thread, and the ``note_*`` functions for the
                  query-level record.
:mod:`.models`    the trace's shape — one ``QueryLog``, many ``RetrieverEvent``.
:mod:`.views`     how each store's results are rendered, bounded, into a trace.
:mod:`.safe`      JSON conversion, secret redaction, and the size caps.
:mod:`.sql`       the connection proxy that traces MySQL without editing every
                  query.
:mod:`.sink`      where a finished trace goes on disk, and the guarantee that a
                  logging failure costs only the trace.

Adding a retriever is one call — ``retriever_call("elasticsearch", "search",
...)`` — and nothing in this package has to change.
"""
from __future__ import annotations

from app.observability.retrieval_log.models import (
    GRAPH,
    MYSQL,
    QDRANT,
    SCHEMA_VERSION,
    QueryLog,
    RetrieverEvent,
)
from app.observability.retrieval_log.recorder import (
    active,
    bound,
    enabled,
    finish,
    graph_call,
    mysql_call,
    note,
    note_context,
    note_error,
    note_outcome,
    note_query,
    qdrant_call,
    query_log,
    record,
    retriever_call,
    start,
)
from app.observability.retrieval_log.sink import log_root

__all__ = [
    "GRAPH",
    "MYSQL",
    "QDRANT",
    "SCHEMA_VERSION",
    "QueryLog",
    "RetrieverEvent",
    "active",
    "bound",
    "enabled",
    "finish",
    "graph_call",
    "log_root",
    "mysql_call",
    "note",
    "note_context",
    "note_error",
    "note_outcome",
    "note_query",
    "qdrant_call",
    "query_log",
    "record",
    "retriever_call",
    "start",
]
