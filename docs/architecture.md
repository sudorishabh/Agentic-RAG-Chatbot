# Architecture

How the implemented system is wired, and how a request travels through it.

## Module map

The dependency direction is: `retrieval` never imports `generation`; `generation`
never imports retrieval internals (only the shared `core.models.ContextBlock`
contract); `pipeline` is the only layer that combines both. Ingestion writes the
document catalog, retrieval reads it — both through `app/catalog/`.

```
app/
├── main.py                  Retrieval server: health + chat + search + source routers
├── ingest_main.py           Ingestion server: health + ingest routers + sweep scheduler
├── app_factory.py           Shared FastAPI wiring: logging, CORS, observability
├── config.py                Settings (pydantic-settings, loaded from env / .env)
├── api/
│   ├── auth.py              Bearer-JWT principal (tenant + groups) for the public API
│   ├── chat.py              POST /chat (SSE stream on a dedicated thread limiter)
│   ├── search.py            POST /search   (retrieval only, no generation)
│   ├── source.py            GET /source/{id} (cited PDFs, tenant/ACL-scoped)
│   ├── ingest.py            POST /ingest/pdf(s), /ingest/run, /ingest/article, /reindex; GET /ingest/log
│   └── health.py            GET /health, /ready, /metrics
├── schemas/                 Pydantic request/response models (query.py, ingest.py)
├── core/
│   ├── clients/             Shared infra gateways: vector_store.py (Qdrant), database.py
│   │                        (MySQL pool), cache.py (Redis), embeddings.py, llm.py
│   └── models/              CanonicalDocument/CanonicalSection (document.py) and the
│                            retrieval→generation ContextBlock contract (context.py)
├── pipeline/                Orchestration: the only layer depending on both
│   │                        retrieval and generation
│   ├── query_pipeline.py    query → cache → retrieve → generate → assemble → persist
│   └── summarize.py         Scoped-summary use case (catalog scope + map-reduce LLM synthesis)
├── retrieval/               READ PATH — no LLM answer synthesis
│   ├── query_processor.py   Intent + rewrite + facet filters (control flow)    → ProcessedQuery
│   ├── understanding/       prompts.py (the classification prompt), filters.py (Qdrant facet filters)
│   ├── retriever.py         retrieve(): base/dual search → fuse → rerank → context → supplement
│   ├── search/strategies.py Dual (website-biased) pull, keyword leg, multi-query, corrective requery
│   ├── hybrid_search.py     Qdrant search with tenant/ACL/facet filters → Candidate[]
│   ├── fusion.py            Reciprocal-rank fusion
│   ├── reranker.py          Rerank (embedding/llm/cross_encoder/cohere) + recency·authority
│   ├── context_builder.py   Parent-expand, cosine dedup, conflict flag, token budget, website-first segregation → ContextBlock[]
│   ├── citations.py         Build numbered citations from chunk payloads
│   ├── source_locator.py    document_id → on-disk PDF (roots + tenant/ACL guarded)
│   ├── scoped_retrieval.py  Id-scoped Qdrant reads for scoped summarization
│   └── structured/          Catalog (database-intent) capability: entities.py, filters.py,
│                            planner.py, tools.py, types.py, answerer.py (the query-pipeline adapter)
├── generation/               ANSWER SYNTHESIS — no retrieval dependency
│   ├── answerer.py           Grounded generate/stream + chitchat
│   ├── prompts.py            Grounding + chitchat prompts, context formatting
│   └── faithfulness.py       Citation-marker validation + optional entailment check
├── catalog/                  The document catalog (MySQL): ingestion writes, retrieval reads
│   ├── schema.py             All table DDL + migrations
│   ├── models.py             StateRecord / TermLink / AttachmentLink / LogEntry
│   ├── db.py                 Shared DAO helpers (timestamps, table-name guards)
│   ├── state.py              Ingest-state write model + point reads
│   ├── queries.py            Retrieval-facing analytical reads (count/list/distribution,
│   │                         id-scoped reads for scoped summarization/attachment supplementation)
│   ├── terms.py               Taxonomy-term catalog + aliases
│   ├── log.py                 Append-only ingest audit log (retention-pruned)
│   └── payload_refresh.py     Rename-driven display refresh (MySQL facet + Qdrant payload)
├── ingestion/                 WRITE PATH
│   ├── pipeline.py            Incremental ingest orchestration (PDF + Drupal), one run at a time
│   ├── upload.py               Inline one-off PDF / article ingest
│   ├── canonical.py            Build CanonicalDocument from extractor output
│   ├── textutil.py              Shared text helpers (slugify)
│   ├── chunking/                Structure-aware parent/child chunking: config.py (presets),
│   │                            models.py (Chunk/DocumentMeta), payload.py (Qdrant serialization),
│   │                            segmenter.py (markdown/heading parsing), packer.py (token windowing/
│   │                            overlap), classifier.py (toc/references/glossary)
│   ├── indexer.py                Chunk → embed children → upsert to Qdrant
│   ├── change_detection/          base.py (ChangeRecord/ChangeStatus), files.py (PDF scan),
│   │                              drupal.py (JSON:API crawl + delete reconciliation)
│   ├── backfill.py                One-time catalog title/url backfill from Qdrant payloads
│   └── extractors/                pdf_extractor.py (PyMuPDF text / Camelot tables / Azure-OCR),
│                                  drupal_extractor.py (JSON:API: nodes + taxonomy + blocks),
│                                  attachment.py (attached-PDF download + build)
├── cache/semantic_cache.py    Qdrant-backed semantic cache (lookup / store / prune)
├── workers/
│   ├── tasks.py               Celery ingestion tasks with inline fallback + CLI
│   └── scheduler.py           In-process periodic sweep + cache/log pruning (ingestion server)
├── observability/tracing.py   Per-stage spans, RAG metrics, optional OTel/Langfuse
└── local_tests/                Offline runners (counting, Drupal extraction, PDF extraction, thematic areas)
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
  ([app/catalog/state.py](../app/catalog/state.py), read via
  [app/catalog/queries.py](../app/catalog/queries.py)) — which also answers the
  structured count/list/lookup path — plus the taxonomy-term catalog
  ([app/catalog/terms.py](../app/catalog/terms.py)) and the ingestion audit log
  ([app/catalog/log.py](../app/catalog/log.py)). Accessed through a small
  connection pool in [app/core/clients/database.py](../app/core/clients/database.py)
  that reserves a slot before connecting and fails fast after `mysql_pool_timeout`.
- **Azure OpenAI** — chat + embeddings.
- **Redis** *(optional)* — the semantic-cache prune scheduling and the
  corpus-version counter. Everything degrades gracefully to "no cache" when
  `redis_url` is unset.

Clients are created lazily and memoized with `@lru_cache` in
[app/core/clients/](../app/core/clients/) (`vector_store.py`, `database.py`, `cache.py`,
`embeddings.py`, `llm.py`) — the one place every feature package depends on for
infrastructure access.

## Query lifecycle

The HTTP entry point for asking a question is **`POST /chat`**, which streams via
`stream_answer()`; a retrieval-only `search_blocks()` backs `POST /search`. Both
live in [app/pipeline/query_pipeline.py](../app/pipeline/query_pipeline.py) — the
orchestration layer that is the only place depending on both `retrieval` and
`generation`.

```
question
  │
  ▼
process()  ── query_processor: LLM classifies intent + rewrites + extracts facet filters
  │            → ProcessedQuery{ search_query, intent, filters }
  │
  ├─ intent == "chitchat"   → answer directly with CHITCHAT prompt, no retrieval
  │
  ├─ intent == "structured" → structured/answerer.answer_structured() — answered from
  │                            the LOCAL catalog (MySQL documents: count / list / lookup);
  │                            no live website calls at query time
  │                            (falls through to RAG if it can't handle the query)
  │
  └─ intent == "qa" (default)
        │
        ▼
   semantic_cache.lookup()       Qdrant-backed semantic cache, keyed by embedding + facets
        │
        ▼
   retriever.retrieve():
     search()        hybrid_search: Qdrant search, candidate_k≈40, with
        │            mandatory filters is_parent=false / is_current=true / tenant_id
        │            + ACL MatchAny(user_groups) + query-derived facets.
        │            (When prefer_website_enabled and no explicit source_type / non-table:
        │             TWO pulls — website + "not website" — merged; see retrieval.md §6)
        ▼
     rerank()        reranker: semantic score (provider) → relevance bands, newest
        │            first inside a band, threshold-filtered, truncated to top_k
        │            (raw score kept)
        ▼
     build_context() context_builder: parent-expand → cosine dedup → conflict flag →
        │            (attention reorder, OR website-first segregation when preferring
        │             website) → token budget → ContextBlock[]
        ▼
   answerer.generate(_stream)()   grounded LLM call over numbered context blocks
        │                          (optional faithfulness check + one regeneration)
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
- **Retrieval never imports generation.** The recall-expansion strategies (dual
  pull, multi-query, corrective requery) call the shared LLM/embedding gateways in
  `core.clients` directly; the only place retrieval and generation meet is
  `pipeline/query_pipeline.py`.

## Streaming vs. non-streaming

Both answer entrypoints share one pipeline in
[app/pipeline/query_pipeline.py](../app/pipeline/query_pipeline.py)
(`_prepare` → generate → `_assemble` → `_persist` → `_record`); they differ only
in how the answer is emitted.

| Path | Function | Caches used | Notes |
| --- | --- | --- | --- |
| `POST /chat` | `stream_answer()` | semantic | SSE: `token` → `sources` → `done` (terminal `error` on mid-stream failure). Streams token-by-token; buffers-then-emits when `faithfulness_check` is on |
| `POST /search` | `search_blocks()` | none | Returns ranked blocks, no generation |

The semantic-cache lookup happens in `_prepare`, after query understanding, so
`/chat` serves a cache hit as a single `token` event. See
[operations.md](operations.md#caching) for cache details.

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
