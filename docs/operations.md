# Operations

Caching, background ingestion, observability, and runtime probes.

## Caching

[app/cache/redis_cache.py](../app/cache/redis_cache.py). All caches require `redis_url`
and degrade silently to no-op when Redis is absent. Cache invalidation hangs off a
**corpus version** counter that bumps on every ingest that changes the index.

| Cache | Gate | TTL / size | Key | Functions |
| --- | --- | --- | --- | --- |
| Response | `response_cache_enabled` | `response_cache_ttl` (1 day) | sha256(corpus_version + normalized question + `tenant\|groups\|top_k`) | `response_signature`, `get_response`, `set_response` |
| Embedding | `embedding_cache_enabled` | `embedding_cache_ttl` (7 days) | sha256(model + text) | `get_embedding`, `set_embedding` (used by `embed_query_cached`) |
| Semantic | `semantic_cache_enabled` | list capped at `semantic_cache_max` (200) | list keyed by corpus_version | `semantic_lookup`, `semantic_store` |
| Corpus version | always | — | `rag:corpus_version` | `corpus_version`, `bump_corpus_version` |

- **Response cache** keys include the corpus version, so a bump invalidates every
  cached answer at once. Read/written on the non-streaming `answer_query()` path.
- **Semantic cache** compares the incoming query embedding to stored ones and returns a
  prior answer when cosine ≥ `semantic_cache_threshold` (0.97). Its list key also
  includes the corpus version, so it invalidates on bump too.
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

## Observability

[app/observability/tracing.py](../app/observability/tracing.py). Initialized at startup
by `init_observability(app)` ([app/main.py](../app/main.py)).

- `span(name, **attrs)` — context manager timing a stage; logs elapsed ms and
  attributes, and creates an OpenTelemetry span when OTel is enabled. Used around
  `rag.search`, `rag.rerank`, `rag.generate`, `rag.answer_query` in
  [app/rag.py](../app/rag.py).
- `record_query_metrics(*, latency_ms=None, **metrics)` — per-query RAG quality metrics
  (`intent`, `used_chunks`, `has_citations`, `answered`, `conflict`, `cached`). Logged
  as `rag_metrics` when `metrics_log_enabled`, and attached to the current OTel span.
- `record_feedback(feedback)` — logs `rag_feedback` and pushes to a capped Redis list
  (`rag:feedback`) when available; called by `POST /chat/feedback`.

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
| `GET /ready` | readiness — `200` with Qdrant/Redis status, `503` if Qdrant is down |
| `GET /metrics` | effective config + store snapshot (point count, reranker, K values, cache flags) |

See [api-reference.md](api-reference.md#ops) for response shapes.

## Offline test runners

[app/local_tests/](../app/local_tests/) — no external services required:

```bash
python -m app.local_tests.run_all [path/to/file.pdf]   # all three
python -m app.local_tests.test_canonical               # Drupal export → canonical
python -m app.local_tests.test_chunking                # parent/child chunking
python -m app.local_tests.test_pdf_extraction [pdf]    # extraction + OCR routing
```

Reports are written under `app/local_tests/outputs/`.
