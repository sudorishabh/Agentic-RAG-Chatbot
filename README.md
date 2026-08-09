# Agentic RAG Chatbot

A FastAPI RAG service over a mixed corpus of **PDFs** and **website/Drupal articles**.
Hybrid retrieval on **Qdrant**, cross-encoder reranking, grounded generation with
**citations built from chunk payloads** (never hallucinated), intent routing to a
structured path answered from the local MySQL catalog, optional **Bearer-JWT auth**
on the public API, Redis response/embedding caches plus a Qdrant-backed semantic
cache, a background ingestion server, and observability. Models are served via
**Azure OpenAI**; orchestration uses LangChain.

The design rationale lives in [`docs/`](docs/) (chunking, canonical data model,
PDF extraction, and the end-to-end `gene` spec covering §5–§10).

## Architecture

```
app/
├── main.py                  Retrieval server: chat / search / health (read-only)
├── ingest_main.py           Ingestion server: ingest / reindex + background sweep
├── app_factory.py           Shared FastAPI setup (logging, CORS, observability)
├── config.py                Settings (environment / .env)
├── deps.py                  Shared clients: Qdrant, Redis, MySQL pool, embeddings, LLMs
├── rag.py                   Orchestration: retrieve → rerank → build context → generate (SSE)
├── api/
│   ├── auth.py              Bearer-JWT principal (tenant + groups) for the public API
│   ├── chat.py              POST /chat (SSE)
│   ├── search.py            POST /search   (retrieval only, no generation)
│   ├── ingest.py            POST /ingest/run, /ingest/article, /reindex; GET /ingest/log
│   └── health.py            GET /health, /ready, /metrics
├── schemas/                 Request/response models (query.py, ingest.py)
├── retrieval/
│   ├── query_processor.py   Query understanding: rewrite, intent routing, facet filters (§6.1)
│   ├── hybrid_search.py     Qdrant dense search (sparse-ready), RRF fusion (§5.5)
│   ├── reranker.py          Rerank: embedding / LLM / cross-encoder + recency·authority (§6.3, §9.4)
│   ├── context_builder.py   Parent-expand, cosine dedup, conflict flag, token budget (§6.4, §9)
│   ├── citations.py         Build numbered citations from chunk payloads (§8)
│   └── drupal_router.py     Structured lookup/list/count from the local catalog (§7)
├── generation/
│   ├── llm_client.py        Azure chat / structured LLM factories
│   ├── prompts.py           Strict grounding prompt + context formatting (§10.6)
│   └── faithfulness.py      Optional post-generation entailment check (§10.6)
├── ingestion/
│   ├── pipeline.py          Extract → canonical → chunk → embed → index
│   ├── upload.py            Inline PDF / article ingest entrypoints
│   ├── canonical.py         Canonical Document model (§1–2)
│   ├── chunker.py           Parent-child, structure-aware chunking (§3)
│   ├── embedder.py          Azure embeddings (+ embedding cache)
│   ├── indexer.py           Qdrant collection bootstrap + batched upsert
│   ├── change_detection.py  Incremental ingest (fingerprint / content hash / version)
│   ├── state.py             Ingest-state manifest (MySQL table)
│   └── extractors/          pdf_extractor.py (PyMuPDF/Camelot/Azure-OCR router), drupal_extractor.py
├── cache/                   redis_cache.py (response + embedding) · semantic_cache.py (Qdrant-backed) (§10.3)
├── workers/
│   ├── tasks.py             Celery ingestion workers, inline fallback when no broker (§10.4)
│   └── scheduler.py         Periodic background sweep loop (ingestion server)
├── observability/tracing.py Per-stage timing + RAG quality metrics + optional OTel/Langfuse (§10.4)
├── core/models.py           Shared domain models
└── local_tests/             Offline runners: canonical, chunking, PDF extraction
```

## Prerequisites

- Python 3.11+
- Docker (for Qdrant)
- **Azure OpenAI** — a chat deployment and an embedding deployment
- *Optional:* Azure Document Intelligence (OCR for scanned PDFs), MySQL/MariaDB
  (Drupal source + ingest-state manifest), Redis (caches), a Celery broker
  (background ingestion). All degrade gracefully when unconfigured.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on POSIX)
pip install -r requirements.txt
copy .env.example .env          # cp on POSIX
```

Fill in `.env` with your Azure OpenAI credentials and deployment names (see
**Configuration**). Then start Qdrant:

```bash
docker compose up -d
```

## Run

Two independent servers share the codebase and `.env`. Start Qdrant (above), then
run each in its own terminal:

```bash
# Retrieval server — query API (chat / search), read-only
uvicorn app.main:app --reload --port 8000

# Ingestion server — background change-detection sweep + ingest/reindex endpoints
uvicorn app.ingest_main:app --reload --port 8001
```

The ingestion server runs an incremental sweep (PDFs + Drupal → Qdrant) every
`WORKER_SWEEP_INTERVAL_SECONDS` (default 3600; set `0` to disable and ingest only
on demand). The first sweep runs at startup.

- Retrieval Swagger UI: http://127.0.0.1:8000/docs
- Ingestion Swagger UI: http://127.0.0.1:8001/docs
- Qdrant dashboard: http://localhost:6333/dashboard

## Endpoints

| Server | Method | Path | Purpose |
|---|---|---|---|
| Retrieval | `POST` | `/chat` | Ask a question. **Streams** the grounded answer as SSE: `token` events, then a `sources` event with citations, then `done` (or a terminal `error`). |
| Retrieval | `POST` | `/search` | Retrieval only — returns the ranked context blocks, no generation. |
| Ingestion | `POST` | `/ingest/run` | Incremental Drupal ingest (nodes, terms, blocks + their PDFs). |
| Ingestion | `POST` | `/ingest/article` | Index an inline article (`title`/`body`/`url`), or crawl live Drupal `bundles`. |
| Ingestion | `GET` | `/ingest/log` | Recent ingestion audit events. |
| Ingestion | `POST` | `/reindex` | Reset one `document_id` for re-ingest, or run a full incremental `sweep`. |
| Both | `GET` | `/health` | Liveness probe. |
| Both | `GET` | `/ready` | Readiness — 200/503 on Qdrant reachability (body detail only when `OPS_DETAIL_ENABLED`). |
| Both | `GET` | `/metrics` | Config + store snapshot; 404 unless `OPS_DETAIL_ENABLED`. |

When `AUTH_ENABLED` is set, the retrieval endpoints require an
`Authorization: Bearer <JWT>` header — see [docs/setup.md](docs/setup.md).

## Usage

Ingest an inline article:

```bash
curl -X POST http://127.0.0.1:8001/ingest/article \
  -H "Content-Type: application/json" \
  -d '{"title":"Solar Mini-Grid Pilot 2025","body":"The pilot connected 1,240 households...","url":"https://example.org/a"}'
```

Ask a question (SSE stream):

```bash
curl -N -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"How many households did the 2025 pilot connect?"}'
```

```
data: {"type": "token", "text": "The pilot connected 1,240 households [1]."}
data: {"type": "sources", "citations": [{"n":1,"type":"article","title":"Solar Mini-Grid Pilot 2025","url":"https://example.org/a"}], "intent": "qa", "used_chunks": 1}
data: {"type": "done"}
```

`/search` returns the same retrieval result without generation — handy for tuning K/N and inspecting scores.

## Configuration

Settings load from the environment / `.env` (see `app/config.py` for the full list
and defaults; `.env.example` for a starting template). The most relevant:

| Variable | Default | Description |
|---|---|---|
| `AZURE_OPENAI_MODEL` / `_API_KEY` / `_ENDPOINT` | — | Standard chat deployment (e.g. `gpt-5-mini`). |
| `AZURE_OPENAI_EMBEDDING_MODEL` / `_KEY` / `_ENDPOINT` | — | Embedding deployment (e.g. `text-embedding-3-large`). |
| `LLM_STRUCTURED_TEMPERATURE` | *(unset → omitted)* | Temperature for deterministic/structured calls (query understanding, routing, rerank, faithfulness). **Leave unset for reasoning models** (gpt-5 / o-series reject any value but the default); set `0` for classic chat models. |
| `AZURE_DOCUMENT_INTELLIGENCE_*` | — | Optional OCR/layout for scanned PDFs. |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL. |
| `QDRANT_COLLECTION` | `documents` | Collection name. |
| `REDIS_URL` | *(empty → disabled)* | Enables the response / embedding caches (the semantic cache lives in Qdrant). |
| `MYSQL_*` | `localhost:3306` | Ingest-state manifest / document catalog (also answers the structured-query path). |
| `AUTH_ENABLED` / `JWT_*` | `false` | Require a Bearer JWT on the public retrieval API. |
| `RETRIEVAL_CANDIDATE_K` | `40` | Wide candidate pool from hybrid search before reranking (K). |
| `RETRIEVAL_TOP_K` | `6` | Reranked context blocks handed to the LLM (N). |
| `RERANKER_PROVIDER` | `embedding` | `embedding` \| `llm` \| `cross_encoder` \| `cohere` \| `none`. |
| `RERANK_SCORE_THRESHOLD` | `0.0` | Drop weak blocks (hallucination guard); `0` disables. |
| `HYBRID_USE_SPARSE` | `false` | Collection is dense-only today; enable once sparse vectors are indexed. |
| `FAITHFULNESS_CHECK` | `false` | Optional post-generation entailment verification. |
| `CELERY_BROKER_URL` | *(empty → inline)* | Background ingestion; falls back to inline execution when unset. |

## Tests

```bash
python -m pytest -q        # unit suite (chunking, routing, filters, counting) — offline
```

Additional offline runners live under `app/local_tests/` (extraction coverage,
structured counting, thematic areas) — see
[docs/operations.md](docs/operations.md#offline-test-runners).
</content>
</invoke>
