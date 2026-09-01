# 11 — Observability and Logging

**Purpose.** Make one query's behaviour legible: what it was taken to mean, what
each retriever was asked, what it returned, how long each stage took, whether the
answer was faithful to what was retrieved, and — in aggregate — where a fleet of
queries spends its time and how often each fallback path fires.

**Components.** `app/observability/tracing.py`, `app/observability/metrics.py`,
`app/observability/retrieval_log/*`, `app/api/health.py`, `app/pipeline/query_pipeline.py`.

---

## Three layers of visibility

Ingestion has four layers (see
[docs/ingestion/11](../ingestion/11-observability-and-monitoring.md)); the read
path has three, because there is no run to tally — every request is its own unit
of work — and no cross-store reconciliation to run on a query (that stays a
write-path concern; see the ingestion doc for it).

| Layer | Question | Where |
| --- | --- | --- |
| **Logs** | What happened on this request? | stdout, the `rag_metrics` line |
| **Timing metrics & outcome counters** | Across many requests, where does the time go, and how often does a fallback fire? | spans → `GET /metrics/timings` |
| **The retrieval trace** | Exactly what happened on *this* query — every store call, every candidate, the context that reached the model? | `is_retrieval_log=true` → one JSON file per query |

The third layer is the one this codebase invested the most in, and it already has
its own document: **[`docs/retrieval-logging.md`](../retrieval-logging.md) is the
primary reference for it.** This document summarises what it captures and focuses
on how it wires into the read path's specific stages; read the other one for the
switch, the file layout, the detail levels and the report format.

---

## Logging

Standard `logging`, configured by whatever hosts the process (`uvicorn` here,
rather than the ingestion CLIs' own `basicConfig`).

### The line that matters most: `rag_metrics`

One line per completed query, from `tracing.record_query_metrics` at the end of
`app.pipeline.query_pipeline._record`:

```
INFO app.observability: rag_metrics {'latency_ms': 842.1, 'intent': 'qa',
     'used_chunks': 4, 'has_citations': True, 'answered': True,
     'conflict': False, 'cached': False,
     'components': {'llm': 511.2, 'qdrant': 203.4, 'embedding': 61.0, 'rerank': 12.1},
     'stages': {'rag.query_understanding': 180.2, 'rag.embed_query': 61.0,
                'rag.search': 140.3, 'rag.rerank': 12.1, 'rag.context_build': 8.9,
                'rag.generate': 439.6}}
```

`numeric_mismatch` is included **only when true** — `record_query_metrics` drops
`None` values before logging, so a clean line stays uncluttered and grepping for
`numeric_mismatch` finds only the queries that had one. `components` and `stages`
are the same per-request breakdown `GET /metrics/timings` reports globally,
attached here per query — see [Spans and timing metrics](#spans-and-timing-metrics)
below for how that breakdown survives the SSE stream's thread hops.

`metrics_log_enabled` (default `true`) gates the line; `record_query_metrics` also
sets each field as an OTel span attribute (`rag.<key>`) when tracing is on, so the
same numbers are queryable either way.

### Log levels, by intent

| Level | Used for |
| --- | --- |
| `DEBUG` | Every span's own timing line (`span %s %.1fms %s`), retrieval-log failures after the first one per process |
| `INFO` | `rag_metrics`, degraded-but-handled fallbacks (a leg returning nothing, a corrective requery firing, an unfaithful answer triggering one correction) |
| `WARNING` | The first time retrieval logging fails to write (further failures degrade to `DEBUG` — see [sink.py's `_warn`](#the-retrieval-trace-and-how-it-hooks-in)); a missing `ops_admin_group`-equivalent misconfiguration would be a config-time warning, not a per-query one |
| `ERROR` / `exception` | A retriever call that raised and was not handled by a fallback — these usually surface as `note_error` entries in the trace as well |

Nothing on the read path logs a per-document line the way ingestion does — a
query has no document-shaped unit — so `rag_metrics` and the retrieval trace
carry the whole record.

---

## Spans and timing metrics

`tracing.span(name, **attrs)` — the same primitive ingestion uses — wraps a piece
of work, records its elapsed time into the shared in-process registry
(`app/observability/metrics.py`), and forwards it to OTel when enabled.

### The read-path spans

Every span in `app/pipeline/query_pipeline.py` and `app/retrieval/retriever.py`,
in the order a `qa`-intent query actually hits them:

| Span | Wraps | Component |
| --- | --- | --- |
| `rag.query_understanding` | The understanding LLM call (`understanding/query_processor.py`) | `llm` |
| `rag.embed_query` | Embedding the search query (appears twice: once for the cache lookup, once inside `retriever.py` if the cache misses — see below) | `embedding` |
| `rag.semantic_cache` | The cache lookup itself | `qdrant` |
| `rag.search` | The whole candidate-fetch stage: base pull plus every recall leg | `qdrant` |
| `rag.multi_query` | Multi-query paraphrase fan-out, when `multi_query_enabled` | `other` |
| `rag.keyword_leg` | The full-text keyword leg, when `keyword_leg_enabled` | `other` |
| `rag.content_term_leg` | — | `other` |
| `rag.title_leg` | The title-anchored leg | `other` |
| `rag.search_relaxed` | A relaxed-filter fallback pass, when the first pull under-returns | `other` |
| `rag.rerank` | `search/reranker.py` | `rerank` |
| `rag.corrective` | The one-shot corrective requery, when `corrective_loop_enabled` and the top score is low | `other` |
| `rag.context_build` | `context/builder.py` | `other` |
| `rag.attachment_pull` | Fetching attachment-linked candidates for context expansion | `other` |
| `rag.graph_route` | Whether a query routes to `retrieval/graph/`, when `graph_retrieval_enabled` | `other` |
| `rag.graph_merge` | Merging graph results into the candidate set | `other` |
| `rag.temporal_gate` | Dropping candidates a temporal question excludes | `other` |
| `rag.db_section` | The structured (catalog-answer) path | `other` |
| `rag.catalog_fallback` | Structured answer falling through to ordinary retrieval | `other` |
| `rag.scoped_summary` | The "summarise everything about X" route (`pipeline/summarize.py`) | `other` |
| `rag.answer_plan` | Building the answer plan / directive | `other` |
| `rag.generate` | The generation LLM call | `llm` |
| `rag.faithfulness` | The post-generation entailment check, when `faithfulness_check` | `llm` |
| `rag.semantic_cache_store` | Writing a fresh answer into the cache | `qdrant` |
| `rag.stream_answer` | The whole request, as streamed by `/chat` | *(parent — excluded from component totals)* |

`app/observability/metrics.py`'s `_COMPONENTS` map is what assigns each stage to
`qdrant` / `llm` / `embedding` / `rerank` / `extraction` (ingestion-only) /
`other`; a span not in that map still counts under `other` rather than being
dropped, so `GET /metrics/timings` always accounts for 100% of measured time.
`rag.stream_answer` is the one parent span on the read path (`_PARENTS` in the
same module) — it wraps everything else, so it is excluded from component totals
to avoid double-counting, the same rule ingestion's `ingest.*` spans follow.

### Why `rag.embed_query` can appear twice

The cache lookup embeds the query first (`rag.embed_query` under `rag.semantic_cache`'s
parent stage); on a miss, `retriever.py` embeds it again for the actual search.
Both hit the same span name, so `GET /metrics/timings` reports one aggregate
`rag.embed_query` stage that blends cache-hit and cache-miss queries — the
per-request `rag_metrics` line's `stages` breakdown is the way to see a single
query's own count.

### Surviving the SSE stream

`stream_answer` advances the answer generator with one threadpool hop per
streamed token (`app.api.chat._sse`), and Python's `contextvars` do not carry
across that hop automatically. Two mechanisms compensate:

- `metrics.collect_into(stages)` shares a plain `dict` **by reference** into the
  per-request breakdown, rather than relying on the `ContextVar` context copy
  that a resumed generator loses. Every span still reports to the global
  registry regardless of thread, so `GET /metrics/timings`'s aggregates are
  unaffected either way — only the per-request `rag_metrics` breakdown depends
  on this.
- The retrieval trace's active-trace `ContextVar` has the same problem, so
  `_record` (in `query_pipeline.py`) is called with the trace object passed
  explicitly (`trace` positional argument to `retrieval_log.note_outcome`)
  rather than relying on `active()` to find it. Passing a `None` `log` — the bug
  this fixes — would silently write `"outcome": {}` for every streamed query,
  which is exactly what happened before the explicit-pass form existed. See the
  comment on `retrieval_log.note_outcome` for the history.

Both compensations exist for the same underlying reason and are worth knowing
together: **spans after the first yielded token still reach the global
registry, but per-request state built on `ContextVar`s needs to be threaded
through by hand.**

### Outcome counters

`metrics.record_event(family, outcome)` — the same primitive ingestion's
`embedding_http` counter uses — counts fallback-shaped outcomes that a stage
timing cannot express. The read path's only registered family today is
`graph_routing` (`app/retrieval/graph/policy.py`, `METRIC_FAMILY = "graph_routing"`):
every graph-routing attempt records an outcome, and a second event
(`graph_routing.class`) breaks it down by query class
(`f"{query_class}:{outcome}"`). `GET /metrics/timings`'s `events` object reports
both, with a `share_pct` per outcome — the fastest way to see, for example, what
fraction of graph-eligible queries actually got a graph answer versus fell back.

There is no dedicated counter for faithfulness-check outcomes
(`generation/faithfulness.py`) or for semantic-cache hit/miss — both are visible
per query (`rag_metrics`'s `cached` field; a `rag.faithfulness` span's `faithful`
attribute) but not aggregated into an `events` family. A fleet-wide cache hit
rate or faithfulness failure rate has to be computed from the `rag_metrics` log
stream or the retrieval-log summary (below), not read directly off `/metrics/timings`.

### `GET /metrics/timings`

Identical shape to the ingestion server's endpoint (same `snapshot()` function,
same process):

```json
{"since": "...", "window": 512,
 "components": [{"component": "llm", "total_ms": 950800.0, "calls": 1840, "share_pct": 54.2},
                {"component": "qdrant", "total_ms": 410200.0, "calls": 3680, "share_pct": 23.4}],
 "stages": [{"stage": "rag.generate", "component": "llm", "count": 1840,
             "total_ms": 807600.0, "avg_ms": 438.9, "p50_ms": 401.0,
             "p95_ms": 812.0, "max_ms": 3100.0}],
 "events": {"graph_routing": {"total": 220, "counts": {"routed": 140, "fallback": 80},
                              "share_pct": {"routed": 63.6, "fallback": 36.4}}}}
```

Percentiles cover the same rolling **512**-sample window; the registry is
**shared with ingestion** (same module, same process memory) only if the two
servers somehow ran in one process, which they never do — `main.py` and
`ingest_main.py` are separate processes, so each has its own registry, reset on
its own restart.

---

## The retrieval trace, and how it hooks in

**[`docs/retrieval-logging.md`](../retrieval-logging.md) is the reference —**
read it for the `is_retrieval_log` switch, every `RETRIEVAL_LOG_*` setting, the
`logs/<date>/<question> - <timestamp>/{trace.json,report.md}` layout, the two
detail levels (`compact` / `full`), and the `errors/` and `summary/` side
directories.

What that document does not need to say, because it is written to stand alone,
but is worth spelling out here for a reader of this observability set: **which
functions call it, and how it composes with spans and metrics.**

### Call sites, by package

| Function | Called from | What it records |
| --- | --- | --- |
| `retrieval_log.qdrant_call(...)` | `search/hybrid_search.py`, `search/scoped_retrieval.py`, `context/builder.py`, `graph/hydrate.py` (twice — the id→text hop) | One Qdrant round trip: the request shape, the returned points |
| `retrieval_log.graph_call(...)` | `graph/traverse.py` | One Cypher execution against Neo4j |
| `retrieval_log.record(...)` | `graph/policy.py` | A call the graph package already timed itself (avoids double-measuring) |
| `retrieval_log.note_query(...)` | `query_pipeline.py` | What understanding decided — intent, search query, filters, scope |
| `retrieval_log.note_outcome(...)` | `query_pipeline.py` (twice: the ready-made-result path, and `_record` for the generated-answer path) | How the query ended — cached, answered, citations, conflict, latency |
| `retrieval_log.note_context(...)` | `query_pipeline.py` (twice — same two paths) | The `ContextBlock`s that reached the model, and the rendered prompt string |
| `retrieval_log.note(...)` | `query_pipeline.py` | Anything else — `db_prefix_chars`, `plan_directive` |

Every one of these is free when `is_retrieval_log` is off: `retriever_call` reads
one `ContextVar`, finds it `None`, and returns a shared no-op object
(`_NullCall` / `NULL_CALL`) whose methods do nothing — no dict is built, no
`jsonable()` conversion runs. That is the property that lets call sites be
sprinkled through `search/`, `context/` and `graph/` without a cost/coverage
trade-off: coverage is free to maximise because the off switch is a single
boolean read, not a bypassed code path.

### How the mechanisms compose

For one traced query, all three layers describe the *same* underlying work from
three angles:

- **Spans** measure `rag.search` as one number: however many legs ran, however
  long the slowest one took, folded into one elapsed time.
- **The retrieval trace** breaks that same stage into one `RetrieverEvent` per
  Qdrant call inside it — the base pull, the multi-query fan-out, the keyword
  leg — each with its own latency, request shape and results.
- **`rag_metrics`** reports the span total again, alongside the query-level
  outcome, as the one-line summary that is cheap enough to always be on.

A query with `is_retrieval_log` off still gets the first and third; turning the
switch on adds the second, at the cost this document's sibling explains.

### Thread propagation

The read path fans out across threads more than ingestion does — parallel
search legs, the graph package's own executor — and `retrieval_log.bound(fn)`
is the mechanism that lets a worker thread contribute to the request's trace.
It reads the active `ContextVar` on the calling thread and closes over it,
returning `fn` unchanged when there is no active trace (so it costs nothing when
logging is off). Any new parallel fan-out point on the read path that should be
covered by the trace needs to route through `bound(...)`, the same way
`app/README.md`'s "where new code goes" table says a new retriever needs to wrap
its call in `retrieval_log.retriever_call(...)`.

---

## Health and readiness

Same four endpoints as the ingestion server (`app/api/health.py` is shared code,
mounted by both `app.main` and `app.ingest_main`), with different requirements:

| Endpoint | Auth | Answers |
| --- | --- | --- |
| `GET /health` | none | `{"status": "ok"}` — the process is up |
| `GET /ready` | none | 200/503. Body carries detail only when `ops_detail_enabled` |
| `GET /metrics` | ops-gated → else **404** | Store reachability, knowledge health, retrieval config |
| `GET /metrics/timings` | ops-gated → else **404** | Stage/component timings, event counters — see above |

### `/ready` on the read server

**Gated on Qdrant alone.** `_REQUIRED_STORES` starts empty in `app/api/health.py`
and only `app.ingest_main` calls `require_for_readiness("mysql")` at import
time — `app.main` never does. So on the retrieval server, an unreachable MySQL
degrades a feature (the structured/catalog answer route, author/theme
corroboration) rather than failing the readiness probe; only Qdrant, which dense
retrieval cannot function without, is hard-required. This is the deliberate
asymmetry documented in the code:

> "The retrieval server deliberately does not require it [MySQL]: dense
> retrieval answers from Qdrant alone, and taking the whole API out of a load
> balancer over a catalog blip would turn a degraded feature into an outage."

Contrast with the ingestion server, where MySQL is the system of record (the
crawl cursor, retry markers) and its own `/ready` is not meaningfully "ready"
without it — see
[docs/ingestion/11, `/ready` on the ingestion server](../ingestion/11-observability-and-monitoring.md#ready-on-the-ingestion-server).

With `ops_detail_enabled`, the body adds `redis` and `neo4j` probes, same
fail-soft shape as the ingestion server (Neo4j reachability is a value, not an
exception; `{"enabled": false}` without opening a connection when
`knowledge_enabled` is off).

### `/metrics` body on the read server

```json
{"service": "agentic-rag",
 "corpus_reconciliation": null,
 "qdrant": {"reachable": true, "collection": "documents", "collection_exists": true, "points": 391204},
 "redis": {"configured": true, "reachable": true},
 "neo4j": {"enabled": true, "reachable": true, "nodes": 8412, "relationships": 19022},
 "knowledge": {"enabled": true, "process_after_index": true, "runs": {...}, "pending": 3},
 "reranker_provider": "embedding",
 "retrieval": {"candidate_k": 40, "top_k": 6, "score_threshold": 0.0},
 "caches": {"semantic": true}}
```

`corpus_reconciliation` reads the **same** `app.ingestion.reconcile.last_report()`
the ingestion server's `/metrics` does — it is process-local state, so on the
retrieval server it is `null` unless that specific process has itself run a
sweep, which it never does. Read `corpus_reconciliation` from the ingestion
server, not this one.

`caches.semantic` is a config echo (`semantic_cache_enabled`), not a live hit
rate — see [10, Caching](10-caching.md#observability) for how to measure hit
rate.

---

## What to alert on

Ordered by how directly it means "someone must act". Cross-reference:
[docs/ingestion/11](../ingestion/11-observability-and-monitoring.md#what-to-alert-on)
covers the write-path side of the same corpus; a healthy read path still depends
on it.

### Page

| Signal | Why |
| --- | --- |
| `GET /ready` returns 503 for > 2 probe intervals | Qdrant is gone; no query can retrieve anything |
| `VectorDimensionMismatch` in logs | The collection's configured dimension does not match what queries embed against |
| `rag_metrics` line volume drops to zero | The server is up but no query is completing — check for an unhandled exception ahead of `_record` |

### Investigate today

| Signal | Why |
| --- | --- |
| `answered: False` share rising in `rag_metrics` | More questions are hitting the refusal path than usual — check `intent` alongside it |
| `graph_routing.fallback` share rising sharply | The graph is failing its budget or its templates are missing coverage — check `graph_routing_budget_seconds` and Neo4j reachability |
| `events.embedding_http.throttled` share rising (shared counter with ingestion) | Azure quota pressure is now affecting query latency, not just ingestion throughput |
| `p95_ms` for `rag.generate` climbing | LLM latency, not retrieval — check the deployment's own health before touching retrieval config |
| Retrieval-log write warnings (`Could not write a retrieval trace`) | Disk or permissions issue in `retrieval_log_dir`; the query itself is unaffected but the trace is being lost |

### Watch as a trend

| Signal | Why |
| --- | --- |
| `cached: True` share in `rag_metrics` | Falling semantic-cache hit rate means either more novel questions or a cache-invalidating ingestion pace outrunning `semantic_cache_ttl` — see [10](10-caching.md) |
| `used_chunks` distribution shrinking | Context builder admitting less than it used to — a token-budget or dedup change worth checking |
| `numeric_mismatch: True` occurrences | Recorded only when true; a rising count means generation is producing numbers not backed by context |
| `conflict: True` occurrences | Candidates from the corpus are increasingly disagreeing with each other on the same question |
| `rag.faithfulness`'s `faithful=False` rate (per-query only, not aggregated — grep logs or the retrieval-log summary) | Generation drifting from its grounding; not currently a counted metric, see above |

---

## Diagnostic recipes

**"Why did this specific answer look wrong?"**

Turn on `is_retrieval_log`, reproduce the question, and read `report.md` in its
trace folder — see [docs/retrieval-logging.md](../retrieval-logging.md) for the
folder-naming rules.

**"Where is query latency going, in aggregate?"**

```
GET /metrics/timings
```

`llm` dominant → generation or query-understanding latency, not retrieval.
`qdrant` dominant → search or the semantic cache; check candidate_k and how many
legs are firing. `rerank` non-trivial → check `reranker_provider` (a
`cross_encoder` provider costs materially more than `embedding`).

**"Is the graph pulling its weight?"**

```
GET /metrics/timings   →   events.graph_routing
```

A `fallback` share near 100% with `graph_retrieval_enabled=true` means routing
is attempting and losing, not that the flag is off — check
`graph_routing_budget_seconds` and Neo4j reachability before assuming the
predicate vocabulary is the problem.

**"Is the semantic cache actually being hit?"**

Grep `rag_metrics` for `'cached': True` share over a recent window, or use the
retrieval-log daily summary (`logs/summary/<date>.jsonl`) if logging is on —
see [10, Caching](10-caching.md#observability).

**"Did a streamed query's spans get lost?"**

They should not have — `metrics.collect_into` and the explicit-trace pass in
`_record` exist specifically to prevent this (see
[Surviving the SSE stream](#surviving-the-sse-stream)). If `rag_metrics.stages`
is empty for streamed queries but present for `/search`, that compensation has
regressed; check `app.api.chat._sse` still resumes the generator the same way.

---

Previous: [10 — Caching](10-caching.md) · Next: [12 — Operations and Troubleshooting](12-operations-and-troubleshooting.md)
