# Architecture

How the implemented system is wired, and how a request travels through it.

## Module map

```
app/
├── main.py                  Retrieval server: health + chat + search + source routers
├── ingest_main.py           Ingestion server: health + ingest routers + sweep scheduler
├── app_factory.py           Shared FastAPI wiring: logging, CORS, observability
├── config.py                Settings (pydantic-settings, loaded from env / .env)
├── deps.py                  Shared clients: Qdrant, MySQL pool, Redis, embeddings, LLMs
├── rag.py                   Orchestration: query → retrieve → rerank → context → generate
├── api/
│   ├── auth.py              Bearer-JWT principal (tenant + groups) for the public API
│   ├── chat.py              POST /chat (SSE stream on a dedicated thread limiter)
│   ├── search.py            POST /search   (retrieval only, no generation)
│   ├── source.py            GET /source/{id} (cited PDFs, tenant/ACL-scoped)
│   ├── ingest.py            POST /ingest/pdf(s), /ingest/run, /ingest/article, /reindex; GET /ingest/log
│   └── health.py            GET /health, /ready, /metrics
├── schemas/                 Pydantic request/response models (query.py, ingest.py)
├── retrieval/
│   ├── query_processor.py   Intent + rewrite + facet filters       → ProcessedQuery
│   ├── hybrid_search.py     Qdrant search with tenant/ACL/facet filters → Candidate[]
│   ├── reranker.py          Rerank (embedding/llm/cross_encoder/cohere) + recency·authority
│   ├── context_builder.py   Parent-expand, cosine dedup, conflict flag, token budget, website-first segregation → ContextBlock[]
│   ├── citations.py         Build numbered citations from chunk payloads
│   ├── source_locator.py    document_id → on-disk PDF (roots + tenant/ACL guarded)
│   └── drupal_router.py     Structured path for lookup/list/count — answers from the local catalog (MySQL ingest_state)
├── generation/
│   ├── llm_client.py        Azure chat / structured LLM factories
│   ├── prompts.py           Grounding + chitchat prompts, context formatting
│   └── faithfulness.py      Citation-marker validation + optional entailment check
├── ingestion/
│   ├── pipeline.py          Incremental ingest orchestration (PDF + Drupal), one run at a time
│   ├── upload.py            Inline one-off PDF / article ingest
│   ├── canonical.py         Build CanonicalDocument from extractor output
│   ├── chunker.py           Structure-aware parent/child chunking
│   ├── embedder.py          Azure embeddings + embedding cache
│   ├── indexer.py           Chunk → embed children → upsert to Qdrant
│   ├── change_detection.py  Fingerprint / content-hash incremental detection (stat pre-filter for PDFs)
│   ├── state.py             Ingest-state manifest + document catalog (MySQL table)
│   ├── ingest_log.py        Append-only audit log (retention-pruned)
│   ├── backfill.py          One-time catalog title/url backfill from Qdrant payloads
│   └── extractors/          pdf_extractor.py (PyMuPDF text / Camelot tables / Azure-OCR), drupal_extractor.py (JSON:API: nodes + taxonomy + blocks, attached & in-body PDFs)
├── cache/
│   ├── redis_cache.py       Response + embedding caches, corpus version, identity partition
│   └── semantic_cache.py    Qdrant-backed semantic cache (lookup / store / prune)
├── workers/
│   ├── tasks.py             Celery ingestion tasks with inline fallback + CLI
│   └── scheduler.py         In-process periodic sweep + cache/log pruning (ingestion server)
├── observability/tracing.py Per-stage spans, RAG metrics, optional OTel/Langfuse
├── core/models.py           CanonicalDocument / CanonicalSection domain models
└── local_tests/             Offline runners (counting, Drupal extraction, PDF extraction, thematic areas)
```

The service runs as **two servers** built by the shared
[app/app_factory.py](../app/app_factory.py):

- [app/main.py](../app/main.py) — the **public retrieval server** (chat, search,
  source files, probes). When `auth_enabled` is set, requests must carry a Bearer
  JWT ([app/api/auth.py](../app/api/auth.py)); identity never comes from the body.
- [app/ingest_main.py](../app/ingest_main.py) — the **private ingestion server**
  (ingest/reindex endpoints + the background sweep scheduler). It is protected by
  network isolation, not in-app auth, and must never be exposed publicly.

## Two data stores + two model services

- **Qdrant** — semantic retrieval over chunked unstructured text. The main
  collection (`qdrant_collection`, default `documents`) holds child chunks with
  dense embeddings and parent chunks as zero-vectors fetched by id during
  parent-expand. A second, dedicated collection (`semantic_cache_collection`)
  backs the **semantic answer cache**
  ([app/cache/semantic_cache.py](../app/cache/semantic_cache.py)).
- **MySQL** — durable ingest-state manifest / document catalog
  ([app/ingestion/state.py](../app/ingestion/state.py)) — which also answers the
  structured count/list/lookup path — plus the ingestion audit log. Accessed
  through a small connection pool in [app/deps.py](../app/deps.py) that reserves
  a slot before connecting and fails fast after `mysql_pool_timeout`.
- **Azure OpenAI** — chat + embeddings.
- **Redis** *(optional)* — the response and embedding caches and the
  corpus-version counter. Everything degrades gracefully to "no cache" when
  `redis_url` is unset.

Clients are created lazily and memoized with `@lru_cache` in
[app/deps.py](../app/deps.py) and [app/generation/llm_client.py](../app/generation/llm_client.py).

## Query lifecycle

The HTTP entry point for asking a question is **`POST /chat`**, which streams via
`stream_answer()`. There is also a cache-aware non-streaming function
`answer_query()` (programmatic) and a retrieval-only `search_blocks()` behind
`POST /search`. All live in [app/rag.py](../app/rag.py).

```
question
  │
  ▼
process()  ── query_processor: LLM classifies intent + rewrites + extracts facet filters
  │            → ProcessedQuery{ search_query, intent, filters }
  │
  ├─ intent == "chitchat"   → answer directly with CHITCHAT prompt, no retrieval
  │
  ├─ intent == "structured" → drupal_router.answer_structured() — answered from the
  │                            LOCAL catalog (MySQL ingest_state: count / list / lookup);
  │                            no live website calls at query time
  │                            (falls through to RAG if it can't handle the query)
  │
  └─ intent == "qa" (default)
        │
        ▼
   embed_query_cached()          embedding cache (Redis) keyed by model+text
        │
        ▼
   retrieve():
     search()        hybrid_search: Qdrant search, candidate_k≈40, with
        │            mandatory filters is_parent=false / is_current=true / tenant_id
        │            + ACL MatchAny(user_groups) + query-derived facets.
        │            (When prefer_website_enabled and no explicit source_type / non-table:
        │             TWO pulls — website + "not website" — merged; see retrieval.md §6)
        ▼
     rerank()        reranker: semantic score (provider) blended with recency,
        │            threshold-filtered, sorted, truncated to top_k (raw score kept)
        ▼
     build_context() context_builder: parent-expand → cosine dedup → conflict flag →
        │            (attention reorder, OR website-first segregation when preferring
        │             website) → token budget → ContextBlock[]
        ▼
   _generate(_stream)()   grounded LLM call over numbered context blocks
        │                 (optional faithfulness check + one regeneration)
        ▼
   build_citations()      structured citations assembled from payloads (never the LLM)
        │
        ▼
   answer + citations + intent + used_chunks + conflict
```

Key invariants:

- **Identity comes from the verified principal, never the body.** With
  `auth_enabled`, tenant/groups are claims of a backend-verified Bearer JWT;
  otherwise the anonymous principal (`default` / `["public"]`). The same identity
  scopes `/chat`, `/search`, and `/source/{id}`.
- **Citations come from payloads, not the model.** The LLM only emits `[n]` markers;
  [app/retrieval/citations.py](../app/retrieval/citations.py) maps each marker to real
  metadata, and [app/generation/faithfulness.py](../app/generation/faithfulness.py)
  strips any marker outside `1..len(blocks)`.
- **Refuse rather than guess.** If retrieval yields no blocks, the answer is the exact
  `REFUSAL` string from [app/generation/prompts.py](../app/generation/prompts.py).
- **Tenant/ACL filters are mandatory** on every Qdrant query (built in
  `hybrid_search.build_filter`; mirrored by the source-file lookup).

## Streaming vs. non-streaming

Both answer entrypoints share one pipeline in [app/rag.py](../app/rag.py)
(`_prepare` → generate → `_assemble` → `_persist` → `_record`); they differ only
in how the answer is emitted.

| Path | Function | Caches used | Notes |
| --- | --- | --- | --- |
| `POST /chat` | `stream_answer()` | embedding + response + semantic | SSE: `token` → `sources` → `done` (terminal `error` on mid-stream failure). Streams token-by-token; buffers-then-emits when `faithfulness_check` is on |
| programmatic | `answer_query()` | embedding + response + semantic | Buffered; same pipeline |
| `POST /search` | `search_blocks()` | embedding cache only | Returns ranked blocks, no generation |

Cache lookups happen in `_prepare` (response cache first, then — after query
understanding — the semantic cache), so `/chat` serves cache hits as a single
`token` event. See [operations.md](operations.md#caching) for cache details.

## Ingestion lifecycle (summary)

```
source (PDF on disk | Drupal JSON:API | HTTP upload)
   │
   ▼
extract  →  canonical  →  chunk (parent/child)  →  embed children  →  upsert Qdrant
   │                                                                        │
   └────────────────────── change detection + ingest-state manifest (MySQL) ┘
```

Incremental ingest skips unchanged documents via a fingerprint (PDFs are
pre-filtered on size+mtime before hashing), and skips re-indexing when only the
fingerprint (not the content hash) changed. Reindexing upserts the new version's
points **before** deleting the old ones, so a document never disappears from
search mid-swap. Corpus-wide runs are mutually exclusive (a concurrent trigger is
rejected). Full detail in [ingestion.md](ingestion.md).
