# Configuration

All settings are defined in [app/config.py](../app/config.py) as a pydantic-settings
`Settings` model, accessed everywhere via `get_settings()` (memoized with `@lru_cache`).
Values are read from environment variables or a local `.env` file; env var names are the
upper-cased field names. Unknown env keys are ignored (`extra="ignore"`). See
[.env.example](../.env.example) for a starter template.

> Empty-string defaults generally mean "not configured." Azure credentials must be
> supplied for the service to function; most other settings have working defaults.

## Azure OpenAI — chat

| Setting | Default | Description |
| --- | --- | --- |
| `azure_openai_api_key` | `""` | API key for the chat deployment |
| `azure_openai_endpoint` | `""` | Resource endpoint URL |
| `azure_openai_api_version` | `2024-06-01` | API version |
| `azure_openai_model` | `""` | Chat deployment name |
| `llm_structured_temperature` | `None` | Temperature for structured/deterministic calls (query understanding, routing, rerank, faithfulness). **Leave unset** for reasoning models (gpt-5 / o-series) — they reject any non-default value, so `None` omits the parameter entirely. Set `0` for classic chat models. |

## Azure OpenAI — embeddings

| Setting | Default | Description |
| --- | --- | --- |
| `azure_openai_embedding_model` | `""` | Embedding deployment (e.g. `text-embedding-3-large`) |
| `azure_openai_embedding_key` | `""` | Embedding API key |
| `azure_openai_embedding_endpoint` | `""` | Embedding endpoint URL |
| `azure_openai_embedding_api_version` | `2024-06-01` | API version |
| `azure_openai_embedding_dimensions` | `1536` | Output vector size. `text-embedding-3-{small,large}` support Matryoshka truncation; `1536` halves storage/search cost vs 3-large's native 3072. Set blank/`None` for `ada-002`. Changing it requires recreating the Qdrant collection and re-indexing. |

## PDF extraction & OCR

See [ingestion.md](ingestion.md#extraction) for the extraction pipeline.

| Setting | Default | Description |
| --- | --- | --- |
| `extraction_mode` | `hybrid` | Routing: `hybrid` (per-page), `azure_only` (whole doc to Azure), `local_only` (PyMuPDF text only) |
| `azure_document_intelligence_endpoint` | `""` | Azure Document Intelligence endpoint (OCR for scanned/image pages) |
| `azure_document_intelligence_key` | `""` | Document Intelligence API key |
| `azure_document_intelligence_model` | `prebuilt-read` | DI model: `prebuilt-read` (OCR only, cheap, text only) or `prebuilt-layout` (~6x cost, also extracts tables/structure) |
| `camelot_flavor` | `lattice` | Camelot flavor for born-digital table pages; `lattice` retries empty pages with `stream` |
| `pdf_scanned_char_threshold` | `100` | Min extracted chars/page to treat a page as born-digital; below → routed to Azure OCR |

## Qdrant (vector store)

| Setting | Default | Description |
| --- | --- | --- |
| `qdrant_url` | `http://localhost:6333` | Qdrant endpoint |
| `qdrant_api_key` | `None` | API key (if secured) |
| `qdrant_collection` | `documents` | Collection name |

## Chunking

Chunking has **no environment settings**. Token budgets are preset-driven per
source type / bundle in
[app/ingestion/chunking/config.py](../app/ingestion/chunking/config.py) — see
[ingestion.md](ingestion.md#chunking--appingestionchunking).

## Retrieval & reranking

| Setting | Default | Description |
| --- | --- | --- |
| `retrieval_candidate_k` | `40` | Candidates pulled from Qdrant before reranking (also the "not website" pull size when the website preference is on) |
| `retrieval_top_k` | `6` | Context blocks kept after reranking |
| `hybrid_use_sparse` | `false` | Reserved for sparse/BM25 leg (dense-only today) |
| `reranker_provider` | `embedding` | `embedding` / `llm` / `cross_encoder` / `cohere` |
| `rerank_model` | `""` | Model id; defaults per provider when blank (`BAAI/bge-reranker-v2-m3` for cross-encoder, `rerank-3.5` for Cohere) |
| `rerank_score_threshold` | `0.0` | Drop candidates scoring below this after rerank (applied pre-segregation; keep at 0 unless tuned per source group) |
| `rerank_relevance_tolerance` | `0.03` | How close two relevance scores must be to count as "similarly relevant" — the width of a ranking band. Inside a band the newest document leads; across bands relevance always wins. Widen to let recency decide more often. Sized for the 0..1 scale of the `embedding`/`llm`/`cohere` providers; raise it for `cross_encoder` (unbounded logits). Replaces the old `rerank_recency_weight`/`rerank_authority_weight` blend (see [retrieval.md](retrieval.md#3-reranking--appretrievalrerankerpy)) |
| `rerank_table_boost` | `0.15` | Additive boost for table-bearing candidates when the user asked for a table-shaped answer (soft, not a filter) |
| `dedup_cosine_threshold` | `0.92` | Cosine threshold for query-time deduplication |
| `context_token_budget` | `9000` | Max tokens of retrieved context sent to the LLM. Blocks are parent chunks (~1800 tokens each), so this gates ~5 passages; sized so the website-preference split (2 website + ~3 PDF) fits. Lower toward 6000 for faster single-source answers |

### Website-content preference (dual retrieval)

See [website-preference-retrieval.md](website-preference-retrieval.md) for the design.

| Setting | Default | Description |
| --- | --- | --- |
| `prefer_website_enabled` | `false` | Master switch. When on (and no explicit `source_type`, non-table query), retrieval runs a website pull + a "not website" pull, merges them, and builds a website-first segregated context. Off = today's single-pull behavior. Launch off; flip on after eval tuning |
| `website_candidate_k` | `20` | Website-only candidates pulled alongside the (larger) not-website pull |
| `website_max_slots` | `2` | Max website blocks admitted (the concise lead); PDFs fill the remaining `retrieval_top_k` slots |
| `website_chunk_floor` | `0.30` | Raw-semantic relevance floor a website chunk must clear to take a website slot. Scale is reranker-provider-specific (dense cosine by default); **tune empirically** |

See [retrieval.md](retrieval.md) for how these combine.

## Generation

| Setting | Default | Description |
| --- | --- | --- |
| `faithfulness_check` | `false` | Run a post-generation entailment check; regenerate once if unfaithful |

## Authentication (public retrieval API)

When enabled, `/chat`, `/search` and `/source/{id}` require a **Bearer JWT**; the
caller's tenant and groups come from its verified claims — never from the request
body. Disabled (the default) means the anonymous principal: tenant `default`,
groups `["public"]`. See [api-reference.md](api-reference.md#authentication).

| Setting | Default | Description |
| --- | --- | --- |
| `auth_enabled` | `false` | Require a verified Bearer JWT on the public retrieval API |
| `jwt_secret` | `""` | Signature verification key: the shared secret (HS\*) or PEM public key (RS\*/ES\*) |
| `jwt_algorithms` | `HS256` | Comma-separated allow-list of accepted signing algorithms (`none` is always rejected) |
| `jwt_audience` | `""` | Audience to enforce when set (empty = not checked) |
| `jwt_issuer` | `""` | Issuer to enforce when set (empty = not checked) |
| `jwt_tenant_claim` | `tenant_id` | Claim carrying the caller's tenant |
| `jwt_groups_claim` | `groups` | Claim carrying the caller's authorization groups (list or comma-separated string) |

## API server

| Setting | Default | Description |
| --- | --- | --- |
| `cors_allow_origins` | `*` | Comma-separated origins allowed by CORS. The wildcard keeps the embeddable widget working from any host page (credentials stay off; a startup warning is logged) — pin the host site(s) in deployments serving non-public content. Grants are narrowed to `GET`/`POST` and the `Content-Type`/`Authorization` headers |
| `ops_detail_enabled` | `false` | Expose infrastructure detail (collection name, point counts, tuning values, error strings) on `/ready`, `/metrics` and `/metrics/timings`. Off: `/ready` is status-only and both metrics endpoints return 404 |
| `ops_admin_group` | `""` | JWT group whose members may read `/metrics` and `/metrics/timings` even when `ops_detail_enabled` is off (e.g. `admin`). Requires `auth_enabled`; non-members still get 404, never 401 — the endpoints stay invisible |
| `chat_stream_max_concurrency` | `64` | Max chat generations driven concurrently on the dedicated chat thread limiter; keeps long streams from starving the shared request threadpool |
| `source_base_url` | `""` | Absolute base URL of the retrieval API as reached from the browser; when set, citation links become `{base}/source/{id}#page=N`. Empty = relative `/source/...` paths |

## Caching

Redis holds the **response** and **embedding** caches only; the **semantic cache**
lives in its own Qdrant collection (nearest-neighbor lookup on the query embedding,
identity-scoped, TTL-pruned). Redis is optional — when `redis_url` is empty, the
Redis-backed caches are inert and the corpus version is `"0"`.

| Setting | Default | Description |
| --- | --- | --- |
| `redis_url` | `""` | Redis connection URL; enables the response/embedding caches when set |
| `response_cache_enabled` | `true` | Cache full responses (exact-signature hits) |
| `response_cache_ttl` | `86400` | Response cache TTL (seconds, 1 day) |
| `embedding_cache_enabled` | `true` | Cache query embeddings |
| `embedding_cache_ttl` | `604800` | Embedding cache TTL (seconds, 7 days) |
| `semantic_cache_enabled` | `true` | Reuse answers for near-identical prior queries (Qdrant-backed) |
| `semantic_cache_threshold` | `0.97` | Cosine similarity required for a semantic hit |
| `semantic_cache_collection` | `semantic_cache` | Dedicated Qdrant collection for semantic-cache entries |
| `semantic_cache_prune_every` | `200` | Opportunistic prune cadence: every N `store()` calls, expired entries are deleted (a prune also runs after each background sweep) |

See [operations.md](operations.md#caching).

## Background workers (Celery — optional)

| Setting | Default | Description |
| --- | --- | --- |
| `celery_broker_url` | `""` | Broker URL; when empty, tasks run inline |
| `celery_result_backend` | `""` | Result backend; falls back to `redis_url` |
| `worker_sweep_interval_seconds` | `3600` | Celery Beat sweep cadence (0 disables the schedule) |
| `worker_sweep_reconcile` | `false` | Reconcile Drupal deletes during scheduled sweeps |

## Observability

| Setting | Default | Description |
| --- | --- | --- |
| `metrics_log_enabled` | `true` | Log per-query RAG quality metrics |
| `otel_enabled` | `false` | Enable OpenTelemetry tracing |
| `otel_service_name` | `agentic-rag` | OTel service name |
| `otel_exporter_otlp_endpoint` | `""` | OTLP collector endpoint (adds a batch exporter) |
| `langfuse_enabled` | `false` | Enable Langfuse (reads `LANGFUSE_*` env vars) |

## MySQL (ingest-state manifest + structured path)

| Setting | Default | Description |
| --- | --- | --- |
| `mysql_host` | `localhost` | Host |
| `mysql_port` | `3306` | Port |
| `mysql_user` | `""` | User |
| `mysql_password` | `""` | Password |
| `mysql_database` | `""` | Database name |
| `mysql_connect_timeout` | `10` | Connect timeout (seconds) |
| `mysql_pool_size` | `5` | Connection pool size ([app/deps.py](../app/deps.py)) |
| `mysql_pool_timeout` | `30` | Max seconds to wait for a free pooled connection before raising `TimeoutError` (the pool fails fast instead of blocking forever) |
| `ingest_state_table` | `documents` | Manifest table name |

## Drupal (JSON:API source + structured queries)

| Setting | Default | Description |
| --- | --- | --- |
| `drupal_jsonapi_base` | `https://teriin.org/jsonapi` | JSON:API root |
| `drupal_request_timeout` | `60` | HTTP timeout (seconds) |
| `drupal_page_size` | `50` | JSON:API page size |
| `drupal_max_retries` | `3` | Retry attempts for 429/5xx |
| `drupal_reconcile_every` | `10` | Sweeps between full delete-reconciliation passes |
| `drupal_ingest_external_pdfs` | `false` | Also download/extract in-body PDF links on external (non-teriin.org) domains. Off keeps the corpus TERI-authored; the external URL still survives in the body text |
| `drupal_block_min_chars` | `200` | Custom blocks (`block_content`) with a stripped body shorter than this and no PDF are treated as boilerplate and skipped |

## PDF source discovery (sweeps)

| Setting | Default | Description |
| --- | --- | --- |
| `pdf_source_dirs` | `""` | Directories scanned for PDFs (path-list) |
| `pdf_source_path` | `""` | Single folder fallback when `pdf_source_dirs` is not set |
| `pdf_ignore_globs` | `""` | Glob patterns to exclude |

## Ingestion API & audit log

| Setting | Default | Description |
| --- | --- | --- |
| `max_upload_bytes` | `52428800` | Max size accepted by `/ingest/pdf` (50 MiB); larger uploads are rejected with `413` before the payload is fully buffered |
| `ingest_log_table` | `ingest_log` | Append-only audit table of ingestion events (one row per file/record per run) |
| `ingest_log_enabled` | `true` | Write ingestion events to the audit log |
| `ingest_log_unchanged` | `false` | Also log a row for every UNCHANGED doc. Off by default: on an incremental sweep almost every doc is unchanged, so per-doc rows are write amplification; the run tally already reports the count |
| `ingest_log_retention_days` | `90` | Days to keep audit rows; older rows are pruned after each background sweep (`0` = keep forever) |
