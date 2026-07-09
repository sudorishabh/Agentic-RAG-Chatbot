# Operations

Caching, background ingestion, observability, and runtime probes.

## Caching

The **response** and **embedding** caches live in Redis
([app/cache/redis_cache.py](../app/cache/redis_cache.py)) and degrade silently to
no-op when `redis_url` is unset. The **semantic cache** lives in a dedicated
Qdrant collection ([app/cache/semantic_cache.py](../app/cache/semantic_cache.py)).
Invalidation hangs off a **corpus version** counter that bumps on every ingest
that changes the index.

| Cache | Store | Gate | TTL | Key / scope | Functions |
| --- | --- | --- | --- | --- | --- |
| Response | Redis | `response_cache_enabled` | `response_cache_ttl` (1 day) | sha256(corpus_version + normalized question + `tenant\|groups\|top_k`) | `response_signature`, `get_response`, `set_response` |
| Embedding | Redis | `embedding_cache_enabled` | `embedding_cache_ttl` (7 days) | sha256(model + text) | `get_embedding`, `set_embedding` (used by `embed_query_cached`) |
| Semantic | Qdrant (`semantic_cache_collection`) | `semantic_cache_enabled` | `response_cache_ttl` via `expires_at` | nearest-neighbor on the query embedding, filtered to the caller's identity partition (corpus_version + tenant + groups + top_k + answer_format) | `lookup`, `store`, `prune` |
| Corpus version | Redis | always | — | `rag:corpus_version` | `corpus_version`, `bump_corpus_version` |

- **Response cache** keys include the corpus version, so a bump invalidates every
  cached answer at once. Read/written by **both** answer paths (`/chat` and
  `answer_query()` share one pipeline).
- **Semantic cache** returns a prior answer when the incoming query embedding's
  cosine similarity ≥ `semantic_cache_threshold` (0.97) within the caller's
  partition. Expired entries are filtered at lookup and deleted by `prune()` —
  which runs after each background sweep and opportunistically every
  `semantic_cache_prune_every` stores.
- **Embedding cache** is keyed by model + text and intentionally **persists across
  ingests** (an embedding for the same text doesn't change).

The corpus version is bumped by ingest workers when a tally reports indexed/deleted
documents, and by inline uploads ([app/ingestion/upload.py](../app/ingestion/upload.py)).

## Background workers

[app/workers/tasks.py](../app/workers/tasks.py). Wraps the ingestion pipeline as Celery
tasks, but **runs inline when no broker is configured** (`celery_broker_url` empty), so
the system works with or without Celery.

Tasks:

| Task | Signature | Does |
| --- | --- | --- |
| `ingest_pdfs` | `(dirs=None) -> dict` | incremental PDF ingest; bumps corpus version on change |
| `ingest_drupal` | `(bundles=None, reconcile=False) -> dict` | incremental Drupal ingest |
| `sweep` | `() -> dict` | runs both (`drupal` with `reconcile=worker_sweep_reconcile`) |
| `ingest_upload` | `(filename, content_b64) -> dict` | decode + inline upload ingest |
| `reindex_document` | `(document_id, source_type="website") -> dict` | delete from Qdrant + manifest, bump version |

**Inline CLI** (no broker needed):

```bash
python -m app.workers.tasks sweep                 # PDFs + Drupal, once
python -m app.workers.tasks pdfs
python -m app.workers.tasks drupal --bundle news --bundle report --reconcile
```

**With Celery** (`celery_broker_url` / `celery_result_backend` set — falls back to
`redis_url`):

```bash
celery -A app.workers.tasks worker --loglevel=info
celery -A app.workers.tasks beat   --loglevel=info   # if worker_sweep_interval_seconds > 0
```

The default task queue is `ingest`. When `worker_sweep_interval_seconds > 0`, a Beat
schedule runs `sweep` on that cadence.

**In-process scheduler** ([app/workers/scheduler.py](../app/workers/scheduler.py)):
the ingestion server also runs the sweep loop itself (no Celery required) for the
lifetime of the process. After each sweep it prunes expired **semantic-cache**
entries and **ingest-log** rows older than `ingest_log_retention_days`.

**One run at a time:** corpus-wide ingestion runs (sweep / PDF scan / Drupal
crawl) are mutually exclusive within the process. A manual API trigger during a
run gets `409 Conflict`; the scheduled sweep just logs a skip and retries next
interval.

## Observability

[app/observability/tracing.py](../app/observability/tracing.py). Initialized at startup
by `init_observability(app)` ([app/main.py](../app/main.py)).

- `span(name, **attrs)` — context manager timing a stage; logs elapsed ms and
  attributes, and creates an OpenTelemetry span when OTel is enabled. The query
  pipeline is covered end to end (`rag.response_cache`, `rag.query_understanding`,
  `rag.embed_query`, `rag.semantic_cache`, `rag.search`, `rag.rerank`,
  `rag.context_build`, `rag.generate`, `rag.faithfulness`, `rag.cache_store`) in
  [app/rag.py](../app/rag.py), and ingestion (`ingest.extract`, `ingest.chunk`,
  `ingest.embed`, `ingest.upsert`) in the pipeline and indexer.
- **Stage timing metrics** ([app/observability/metrics.py](../app/observability/metrics.py)) —
  every span also feeds an in-process registry of per-stage timings. `GET
  /metrics/timings` (gated by `ops_detail_enabled`, mounted on both servers)
  returns count / total / avg / p50 / p95 / max per stage, sorted by total time —
  the "which stage is the time going to" view. Per-process and reset on restart;
  parent spans include their children's time.
- `record_query_metrics(*, latency_ms=None, **metrics)` — per-query RAG quality metrics
  (`intent`, `used_chunks`, `has_citations`, `answered`, `conflict`, `cached`). Logged
  as `rag_metrics` when `metrics_log_enabled`, and attached to the current OTel span.
  Recorded on both the streaming and buffered answer paths, cache hits included.
  The log line now also carries a per-request `stages` breakdown (ms per stage);
  on the streaming path it covers the stages up to the first token.

Optional integrations (off by default):

- **OpenTelemetry** — `otel_enabled=true` builds a `TracerProvider`
  (`otel_service_name`), instruments FastAPI, and — if `otel_exporter_otlp_endpoint` is
  set — exports via a batch OTLP span processor.
- **Langfuse** — `langfuse_enabled=true` initializes a client from `LANGFUSE_*` env
  vars (`get_langfuse()` returns it or `None`).

Both fail gracefully if the SDK isn't installed.

## Runtime probes

| Endpoint | Use |
| --- | --- |
| `GET /health` | liveness — always `200` |
| `GET /ready` | readiness — `200`/`503` on Qdrant reachability; body detail only when `ops_detail_enabled` |
| `GET /metrics` | effective config + store snapshot; returns `404` unless `ops_detail_enabled` |
| `GET /metrics/timings` | per-stage timing aggregates (which stage takes how much time); returns `404` unless `ops_detail_enabled` |

Probes consume the status code; the detailed bodies fingerprint the deployment,
so they are off by default on the public API. See
[api-reference.md](api-reference.md#ops) for response shapes.

## Maintenance notes

- **One-time catalog backfill.** Documents ingested before the catalog gained
  `title`/`url` need a single backfill from the Qdrant payloads (new ingests
  populate them automatically):

  ```bash
  python -m app.ingestion.backfill
  ```

- **MySQL pool fails fast.** A request waits at most `mysql_pool_timeout` (30 s)
  for a free pooled connection, then raises `TimeoutError` — the pool no longer
  blocks forever, and a failed connect releases its reserved slot.
- **Ingest audit log is bounded.** Rows older than `ingest_log_retention_days`
  (90) are pruned after each sweep; per-doc `unchanged` rows are not written
  unless `ingest_log_unchanged` is set.
- **Uploads are capped.** `/ingest/pdf` rejects files over `max_upload_bytes`
  (413) and non-PDF content (415) before buffering the payload.

## Offline test runners

[app/local_tests/](../app/local_tests/) — offline checks with reports written
next to each runner:

```bash
python -m app.local_tests.counting_test.run            # structured count/list path
python -m app.local_tests.drupal_extraction_test.run   # JSON:API extraction coverage
python -m app.local_tests.pdf_extraction_test.run      # extraction + OCR routing
python -m app.local_tests.thematic_areas_test.run      # taxonomy / thematic areas
```
