# Architecture

How the implemented system is wired, and how a request travels through it.

## Module map

```
app/
├── main.py                  FastAPI app + observability init + router wiring
├── config.py                Settings (pydantic-settings, loaded from env / .env)
├── deps.py                  Shared clients: Qdrant, MySQL pool, Redis, embeddings, LLMs
├── rag.py                   Orchestration: query → retrieve → rerank → context → generate
├── api/
│   ├── chat.py              POST /chat (SSE stream), POST /chat/feedback
│   ├── search.py            POST /search   (retrieval only, no generation)
│   ├── ingest.py            POST /ingest/pdf, /ingest/article, /reindex
│   └── health.py            GET /health, /ready, /metrics
├── schemas/                 Pydantic request/response models (query.py, ingest.py)
├── retrieval/
│   ├── query_processor.py   Intent + rewrite + facet filters       → ProcessedQuery
│   ├── hybrid_search.py     Qdrant search with tenant/ACL/facet filters → Candidate[]
│   ├── reranker.py          Rerank (embedding/llm/cross_encoder/cohere) + recency·authority
│   ├── context_builder.py   Parent-expand, cosine dedup, conflict flag, token budget, website-first segregation → ContextBlock[]
│   ├── citations.py         Build numbered citations from chunk payloads
│   └── drupal_router.py     Structured MySQL/JSON:API path for lookup/list/count queries
├── generation/
│   ├── llm_client.py        Azure chat / structured LLM factories
│   ├── prompts.py           Grounding + chitchat prompts, context formatting
│   └── faithfulness.py      Citation-marker validation + optional entailment check
├── ingestion/
│   ├── pipeline.py          Incremental ingest orchestration (PDF + Drupal)
│   ├── upload.py            Inline one-off PDF / article ingest
│   ├── canonical.py         Build CanonicalDocument from extractor output
│   ├── chunker.py           Structure-aware parent/child chunking
│   ├── embedder.py          Azure embeddings + embedding cache
│   ├── indexer.py           Chunk → embed children → upsert to Qdrant
│   ├── change_detection.py  Fingerprint / content-hash incremental detection
│   ├── state.py             Ingest-state manifest (MySQL table)
│   └── extractors/          pdf_extractor.py (PyMuPDF text / Camelot tables / Azure-OCR), drupal_extractor.py (JSON:API: nodes + taxonomy + blocks, attached & in-body PDFs)
├── cache/redis_cache.py     Response / embedding / semantic caches + corpus version
├── workers/tasks.py         Celery ingestion tasks with inline fallback + CLI
├── observability/tracing.py Per-stage spans, RAG metrics, optional OTel/Langfuse
├── core/models.py           CanonicalDocument / CanonicalSection domain models
└── local_tests/             Offline runners (canonical, chunking, PDF extraction)
```

Application startup is [app/main.py](../app/main.py): it constructs the `FastAPI`
app, calls `init_observability(app)`, and includes the health, chat, search, and
ingest routers.

## Two data stores + two model services

- **Qdrant** — semantic retrieval over chunked unstructured text. One collection
  (`qdrant_collection`, default `documents`). Child chunks carry dense embeddings;
  parent chunks are stored as zero-vectors and fetched by id during parent-expand.
- **MySQL** — durable ingest-state manifest ([app/ingestion/state.py](../app/ingestion/state.py))
  and the structured-query path. Accessed through a small connection pool in
  [app/deps.py](../app/deps.py).
- **Azure OpenAI** — chat + embeddings.
- **Redis** *(optional)* — caches and the corpus-version counter. Everything degrades
  gracefully to "no cache" when `redis_url` is unset.

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
  ├─ intent == "structured" → drupal_router.answer_structured() (MySQL/JSON:API)
  │                            count / list / lookup; returns answer + citations
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

- **Citations come from payloads, not the model.** The LLM only emits `[n]` markers;
  [app/retrieval/citations.py](../app/retrieval/citations.py) maps each marker to real
  metadata, and [app/generation/faithfulness.py](../app/generation/faithfulness.py)
  strips any marker outside `1..len(blocks)`.
- **Refuse rather than guess.** If retrieval yields no blocks, the answer is the exact
  `REFUSAL` string from [app/generation/prompts.py](../app/generation/prompts.py).
- **Tenant/ACL filters are mandatory** on every Qdrant query (built in
  `hybrid_search.build_filter`).

## Streaming vs. non-streaming

| Path | Function | Caches used | Notes |
| --- | --- | --- | --- |
| `POST /chat` | `stream_answer()` | embedding cache only | Server-Sent Events: `token` → `sources` → `done` |
| programmatic | `answer_query()` | embedding + response + semantic | Cache-aware; wraps `_answer()` and records metrics |
| `POST /search` | `search_blocks()` | embedding cache only | Returns ranked blocks, no generation |

The response and semantic caches are populated/read on the `answer_query()` path; the
SSE `/chat` path intentionally streams fresh each time (it still benefits from the
embedding cache). See [operations.md](operations.md#caching) for cache details.

## Ingestion lifecycle (summary)

```
source (PDF on disk | Drupal JSON:API | HTTP upload)
   │
   ▼
extract  →  canonical  →  chunk (parent/child)  →  embed children  →  upsert Qdrant
   │                                                                        │
   └────────────────────── change detection + ingest-state manifest (MySQL) ┘
```

Incremental ingest skips unchanged documents via a fingerprint, and skips re-indexing
when only the fingerprint (not the content hash) changed. Full detail in
[ingestion.md](ingestion.md).
