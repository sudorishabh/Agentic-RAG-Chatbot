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

## Azure OpenAI — reasoning (optional, separate deployment)

| Setting | Default | Description |
| --- | --- | --- |
| `azure_openai_reasoning_api_key` | `""` | Key for the reasoning deployment |
| `azure_openai_reasoning_endpoint` | `""` | Reasoning endpoint URL |
| `azure_openai_reasoning_api_version` | `2024-06-01` | API version |
| `azure_openai_reasoning_model` | `""` | Reasoning deployment name |
| `llm_structured_temperature` | `None` | Temperature for structured/deterministic calls (query understanding, routing, rerank, faithfulness). **Leave unset** for reasoning models (gpt-5 / o-series) — they reject any non-default value, so `None` omits the parameter entirely. Set `0` for classic chat models. |

## Azure OpenAI — embeddings

| Setting | Default | Description |
| --- | --- | --- |
| `azure_openai_embedding_model` | `""` | Embedding deployment (e.g. `text-embedding-3-large`) |
| `azure_openai_embedding_key` | `""` | Embedding API key |
| `azure_openai_embedding_endpoint` | `""` | Embedding endpoint URL |
| `azure_openai_embedding_api_version` | `2024-06-01` | API version |

## PDF extraction & OCR

See [ingestion.md](ingestion.md#extraction) for the extraction pipeline.

| Setting | Default | Description |
| --- | --- | --- |
| `azure_document_intelligence_endpoint` | `""` | Azure Document Intelligence endpoint (OCR for scanned PDFs) |
| `azure_document_intelligence_key` | `""` | Document Intelligence API key |
| `azure_document_intelligence_model` | `prebuilt-layout` | DI model |
| `pdf_scanned_char_threshold` | `100` | Min extracted chars/page to treat a page as digital; below → OCR |

## Qdrant (vector store)

| Setting | Default | Description |
| --- | --- | --- |
| `qdrant_url` | `http://localhost:6333` | Qdrant endpoint |
| `qdrant_api_key` | `None` | API key (if secured) |
| `qdrant_collection` | `documents` | Collection name |

## Chunking

| Setting | Default | Description |
| --- | --- | --- |
| `chunk_size` | `1000` | Legacy/base chunk size (the chunker uses token-based presets — see [ingestion.md](ingestion.md#chunking--appingestionchunkerpy)) |
| `chunk_overlap` | `200` | Legacy/base overlap |

## Retrieval & reranking

| Setting | Default | Description |
| --- | --- | --- |
| `retrieval_candidate_k` | `40` | Candidates pulled from Qdrant before reranking |
| `retrieval_top_k` | `6` | Context blocks kept after reranking |
| `hybrid_use_sparse` | `false` | Reserved for sparse/BM25 leg (dense-only today) |
| `reranker_provider` | `embedding` | `embedding` / `llm` / `cross_encoder` / `cohere` |
| `rerank_model` | `""` | Model id; defaults per provider when blank (`BAAI/bge-reranker-v2-m3` for cross-encoder, `rerank-3.5` for Cohere) |
| `rerank_score_threshold` | `0.0` | Drop candidates scoring below this after rerank |
| `rerank_recency_weight` | `0.05` | Weight of recency in the blended score |
| `rerank_authority_weight` | `0.05` | Weight of source authority in the blended score |
| `dedup_cosine_threshold` | `0.92` | Cosine threshold for query-time deduplication |
| `context_token_budget` | `8000` | Max tokens of retrieved context sent to the LLM |

See [retrieval.md](retrieval.md) for how these combine.

## Generation

| Setting | Default | Description |
| --- | --- | --- |
| `faithfulness_check` | `false` | Run a post-generation entailment check; regenerate once if unfaithful |

## Caching (Redis)

Redis is optional — when `redis_url` is empty, all caches are inert and the corpus
version is `"0"`.

| Setting | Default | Description |
| --- | --- | --- |
| `redis_url` | `""` | Redis connection URL; enables caches when set |
| `response_cache_enabled` | `true` | Cache full responses (non-streaming path) |
| `response_cache_ttl` | `86400` | Response cache TTL (seconds, 1 day) |
| `embedding_cache_enabled` | `true` | Cache query embeddings |
| `embedding_cache_ttl` | `604800` | Embedding cache TTL (seconds, 7 days) |
| `semantic_cache_enabled` | `true` | Reuse near-identical prior queries |
| `semantic_cache_threshold` | `0.97` | Cosine similarity required for a semantic hit |
| `semantic_cache_max` | `200` | Max entries in the semantic cache list |

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
| `ingest_state_table` | `ingest_state` | Manifest table name |

## Drupal (JSON:API source + structured queries)

| Setting | Default | Description |
| --- | --- | --- |
| `drupal_jsonapi_base` | `https://teriin.org/jsonapi` | JSON:API root |
| `drupal_request_timeout` | `60` | HTTP timeout (seconds) |
| `drupal_page_size` | `50` | JSON:API page size |
| `drupal_max_retries` | `3` | Retry attempts for 429/5xx |
| `drupal_reconcile_every` | `10` | Sweeps between full delete-reconciliation passes |

## PDF source discovery (sweeps)

| Setting | Default | Description |
| --- | --- | --- |
| `pdf_source_dirs` | `""` | Directories scanned for PDFs (path-list) |
| `pdf_ignore_globs` | `""` | Glob patterns to exclude |
