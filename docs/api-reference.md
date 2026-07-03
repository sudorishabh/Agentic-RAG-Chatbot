# API Reference

All routes are registered in [app/main.py](../app/main.py). Schemas live in
[app/schemas/query.py](../app/schemas/query.py) and
[app/schemas/ingest.py](../app/schemas/ingest.py). Interactive docs are available at
`/docs` (Swagger) and `/redoc` when the server is running.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness — checks Qdrant (and Redis) |
| GET | `/metrics` | Effective config + store status snapshot |
| POST | `/chat` | Ask a question; **streams** the answer (SSE) |
| POST | `/chat/feedback` | Record thumbs up/down + clicked citations |
| POST | `/search` | Retrieval only — ranked context blocks, no generation |
| POST | `/ingest/pdf` | Upload and ingest a single PDF |
| POST | `/ingest/article` | Ingest an article inline, or crawl Drupal bundles |
| POST | `/reindex` | Reset a document for re-ingest, or run a full sweep |

---

## Ops

### `GET /health`
Always returns `{"status": "ok"}`. Use for liveness.

### `GET /ready`
Returns `200` with Qdrant + Redis status, or `503` if Qdrant is unreachable.

```json
{ "status": "ready",
  "qdrant": { "reachable": true, "collection": "documents", "collection_exists": true, "points": 12345 },
  "redis":  { "configured": true, "reachable": true } }
```

### `GET /metrics`
Effective configuration and store status — useful for confirming what a deployment is
actually running.

```json
{ "service": "agentic-rag",
  "qdrant": { "reachable": true, "collection": "documents", "collection_exists": true, "points": 12345 },
  "redis": { "configured": true, "reachable": true },
  "reranker_provider": "embedding",
  "retrieval": { "candidate_k": 40, "top_k": 6, "score_threshold": 0.0 },
  "caches": { "response": true, "embedding": true, "semantic": true } }
```

---

## Chat

### `POST /chat`
Streams the grounded answer as **Server-Sent Events** (`text/event-stream`).

Request body — `QueryRequest`:

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `question` | string | — | required, min length 1 |
| `history` | `ChatTurn[]` | `[]` | each `{ role: "user"\|"assistant", content }` |
| `tenant_id` | string | `"default"` | injected into the mandatory Qdrant filter |
| `user_groups` | string[] | `["public"]` | ACL — matched against each chunk's `acl` |
| `top_k` | int \| null | null | overrides `retrieval_top_k` |
| `stream` | bool | false | accepted for compatibility; `/chat` always streams |

Each SSE line is `data: <json>\n\n`. Event shapes:

```
data: {"type": "token", "text": "Customer records must be retained..."}
data: {"type": "token", "text": " for seven years [1]."}
data: {"type": "sources", "citations": [...], "intent": "qa", "used_chunks": 4, "conflict": false}
data: {"type": "done"}
```

- `token` — an incremental chunk of answer text (many of these).
- `sources` — emitted once after the answer: the structured `citations`, plus
  `intent`, `used_chunks`, and `conflict`.
- `done` — terminal event.

When nothing relevant is retrieved, a single `token` carries the exact refusal text
`"I don't have information on that in the available sources."`, followed by empty
`sources` and `done`.

### `POST /chat/feedback`
Records user feedback (logged, and pushed to a Redis list when available). Body —
`FeedbackRequest`:

| Field | Type | Notes |
| --- | --- | --- |
| `question` | string | the question that was answered |
| `rating` | `"up"` \| `"down"` | required |
| `answer` | string \| null | optional copy of the answer |
| `clicked_citations` | int[] | citation numbers the user opened |
| `comment` | string \| null | free text |

Response: `{ "status": "recorded" }`.

---

## Search

### `POST /search`
Same retrieval pipeline as `/chat` (query understanding → search → rerank → context
build) but **no generation**. Body — `SearchRequest` (same fields as `QueryRequest`
minus `stream`). Returns `SearchResponse`:

```json
{ "intent": "qa",
  "search_query": "data retention policy for disputes",
  "blocks": [
    { "n": 1, "score": 0.83, "conflict": false, "text": "...",
      "document_id": "...", "source_type": "pdf", "title": "Corporate Policy Guide 2024",
      "page_number": 42, "section_heading": "4.2 Data Retention Requirements" }
  ] }
```

---

## Ingest

### `POST /ingest/pdf`
`multipart/form-data` with a `file` field. Extracts, chunks, embeds, and indexes the
PDF immediately (inline — no change-detection bookkeeping). Returns `IngestResponse`:

```json
{ "filename": "policy.pdf", "document_id": "policy", "chunks_ingested": 37 }
```

Errors: `400` if the filename is missing or the file is empty.

### `POST /ingest/article`
Body — `ArticleIngestRequest`. Two modes:

- **Crawl mode** — provide `bundles: ["news", "report", ...]` to crawl those Drupal
  JSON:API bundles. Returns `{ "crawled": { "<bundle>": <count>, ... } }`.
- **Inline mode** — provide `title`/`body` (and optionally `url`, `uuid`, `bundle`)
  to ingest one article. Returns `{ "document_id": "...", "chunks_ingested": N }`.

Errors: `400` if neither `bundles` nor an article (`title`/`body`) is supplied.

### `POST /reindex`
Body — `ReindexRequest`. Two modes:

- **Sweep mode** — `sweep: true` runs a full incremental sweep (PDFs + Drupal) and
  returns `{ "status": "swept", "detail": { "pdfs": {...}, "drupal": {...} } }`.
- **Single document** — provide `document_id` (and optional `source_type`, default
  `"website"`) to delete it from Qdrant + the manifest so the next sweep re-ingests
  it. Returns `{ "status": "reset", "detail": {...} }`.

Errors: `400` if `document_id` is missing and `sweep` is not set.

> Ingest routes run the blocking work in a threadpool. When a Celery broker is
> configured these can be backed by workers; otherwise they execute inline. See
> [operations.md](operations.md#background-workers).
