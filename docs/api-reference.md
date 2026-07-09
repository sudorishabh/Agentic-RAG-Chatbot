# API Reference

The service runs as **two servers**:

- **Retrieval server** ([app/main.py](../app/main.py)) — public-facing:
  `/chat`, `/search`, `/source/{id}`, plus health probes.
- **Ingestion server** ([app/ingest_main.py](../app/ingest_main.py)) — private
  (network-isolated, no in-app auth): `/ingest/*`, `/reindex`, plus health probes
  and the background sweep scheduler.

Schemas live in [app/schemas/query.py](../app/schemas/query.py) and
[app/schemas/ingest.py](../app/schemas/ingest.py). Interactive docs are available at
`/docs` (Swagger) and `/redoc` on each server.

| Server | Method | Path | Purpose |
| --- | --- | --- | --- |
| retrieval | GET | `/health` | Liveness probe |
| retrieval | GET | `/ready` | Readiness — 200/503 based on Qdrant reachability |
| retrieval | GET | `/metrics` | Config + store snapshot (only when `ops_detail_enabled`) |
| retrieval | GET | `/metrics/timings` | Per-stage timing aggregates (only when `ops_detail_enabled`) |
| retrieval | POST | `/chat` | Ask a question; **streams** the answer (SSE) |
| retrieval | POST | `/search` | Retrieval only — ranked context blocks, no generation |
| retrieval | GET | `/source/{document_id}` | Serve a cited document's source PDF inline |
| ingestion | POST | `/ingest/pdf` | Upload and ingest a single PDF |
| ingestion | POST | `/ingest/pdfs` | Scan + ingest the configured PDF source dirs |
| ingestion | POST | `/ingest/run` | Incremental ingest: PDFs + Drupal |
| ingestion | POST | `/ingest/article` | Ingest an article inline, or crawl Drupal bundles |
| ingestion | GET | `/ingest/log` | Recent ingestion audit events |
| ingestion | POST | `/reindex` | Reset a document for re-ingest, or run a full sweep |

---

## Authentication

When `auth_enabled` is on, the public endpoints (`/chat`, `/search`,
`/source/{id}`) require an `Authorization: Bearer <JWT>` header. The backend
verifies the signature (`jwt_secret` / `jwt_algorithms`, plus audience/issuer when
configured) and derives the caller's **tenant** and **groups** from the token's
claims (`jwt_tenant_claim` / `jwt_groups_claim`). A missing or invalid token is a
`401`.

When auth is disabled (default), requests run as the anonymous principal —
tenant `default`, groups `["public"]`.

Either way, **identity never comes from the request body**: `tenant_id` and
`user_groups` are not accepted as request fields.

---

## Ops

The health router is mounted on both servers.

### `GET /health`
Always returns `{"status": "ok"}`. Use for liveness.

### `GET /ready`
Returns `200 {"status": "ready"}` or `503 {"status": "not_ready"}` — the status
code is the contract for orchestrator probes. Infrastructure detail (collection
name, point counts, error strings) is included in the body **only when
`ops_detail_enabled`** — it fingerprints the deployment on a public API:

```json
{ "status": "ready",
  "qdrant": { "reachable": true, "collection": "documents", "collection_exists": true, "points": 12345 },
  "redis":  { "configured": true, "reachable": true } }
```

### `GET /metrics`
Effective configuration and store status. Returns `404` unless
`ops_detail_enabled` is set (its whole body is deployment detail).

```json
{ "service": "agentic-rag",
  "qdrant": { "reachable": true, "collection": "documents", "collection_exists": true, "points": 12345 },
  "redis": { "configured": true, "reachable": true },
  "reranker_provider": "embedding",
  "retrieval": { "candidate_k": 40, "top_k": 6, "score_threshold": 0.0 },
  "caches": { "response": true, "embedding": true, "semantic": true } }
```

### `GET /metrics/timings`
Per-stage timing aggregates — which pipeline stage takes how much time. Fed by
the tracing spans (`rag.*` on the retrieval server, `ingest.*` on the ingestion
server, which also mounts this router). Sorted by total time, percentiles over
the last 512 samples per stage; in-memory per process, reset on restart. Parent
spans (`rag.answer_query`, `rag.stream_answer`) include their children's time.
Returns `404` unless `ops_detail_enabled`.

```json
{ "since": "2026-07-09T10:00:00+00:00",
  "window": 512,
  "stages": [
    { "stage": "rag.stream_answer", "count": 42, "total_ms": 98213.5, "avg_ms": 2338.4,
      "p50_ms": 2100.9, "p95_ms": 4880.2, "max_ms": 7012.0 },
    { "stage": "rag.generate", "count": 40, "total_ms": 71400.1, "avg_ms": 1785.0,
      "p50_ms": 1650.2, "p95_ms": 3900.8, "max_ms": 5100.3 },
    { "stage": "rag.search", "count": 40, "total_ms": 9120.7, "avg_ms": 228.0,
      "p50_ms": 210.4, "p95_ms": 390.1, "max_ms": 610.9 } ] }
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
| `top_k` | int \| null | null | overrides `retrieval_top_k`; bounded 1–50 (`422` outside) |
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
- `done` — terminal event. Every complete answer ends with it; a stream that
  stops without `done` was truncated.
- `error` — terminal event emitted when generation fails **mid-stream** (the 200
  and headers are already sent, so an HTTP error is no longer possible). The
  event is deliberately generic; details stay in the server log.

When nothing relevant is retrieved, a single `token` carries the exact refusal text
`"I don't have information on that in the available sources."`, followed by empty
`sources` and `done`.

---

## Search

### `POST /search`
Same retrieval pipeline as `/chat` (query understanding → search → rerank → context
build) but **no generation**. Body — `SearchRequest` (`question`, `history`,
`top_k`; same bounds as `/chat`). Returns `SearchResponse`:

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

## Source files

### `GET /source/{document_id}`
Serves the document's source PDF inline (`application/pdf`) so citation links open
in the browser's viewer (which honours the `#page=N` fragment). The id may be a
`document_id` or `pdf_id`.

Scoped to the caller's tenant/ACL — the same visibility rule as search, checked
against the point payload. A document outside the caller's scope, an unknown id, a
missing file, or a stored path outside the configured source roots all return the
same `404` (no existence disclosure).

---

## Ingest (private server)

### `POST /ingest/pdf`
`multipart/form-data` with a `file` field. Validates before buffering the payload:

- `400` — missing filename, non-`.pdf` suffix, or empty file
- `413` — larger than `max_upload_bytes` (default 50 MiB)
- `415` — content does not start with the `%PDF-` magic bytes

Extracts, chunks, embeds, and indexes the PDF immediately (inline — no
change-detection bookkeeping). Returns `IngestResponse`:

```json
{ "filename": "policy.pdf", "document_id": "policy", "chunks_ingested": 37 }
```

### `POST /ingest/pdfs`
Runs the incremental PDF scan over the configured source dirs
(`pdf_source_dirs` / `pdf_source_path`; `400` when neither is set). Returns the
per-status tally.

### `POST /ingest/run`
Body — `DirectIngestRequest` (`bundles`, `reconcile`, both optional). Runs the PDF
scan (when a source is configured) then the Drupal crawl. Returns both tallies.

### `POST /ingest/article`
Body — `ArticleIngestRequest`. Two modes:

- **Crawl mode** — provide `bundles: ["news", "report", ...]` to crawl those Drupal
  JSON:API bundles. Returns `{ "crawled": { "<status>": <count>, ... } }`.
- **Inline mode** — provide `title`/`body` (and optionally `url`, `uuid`, `bundle`)
  to ingest one article. Returns `{ "document_id": "...", "chunks_ingested": N }`.

Errors: `400` if neither `bundles` nor an article (`title`/`body`) is supplied.

### `GET /ingest/log`
Query params: `limit` (default 100, max 1000), `source_type`, `document_id`,
`status`. Returns the most recent audit events, newest first.

### `POST /reindex`
Body — `ReindexRequest`. Two modes:

- **Sweep mode** — `sweep: true` runs a full incremental sweep (PDFs + Drupal) and
  returns `{ "status": "swept", "detail": { "pdfs": {...}, "drupal": {...} } }`.
- **Single document** — provide `document_id` (and optional `source_type`, default
  `"website"`) to delete it from Qdrant + the manifest so the next sweep re-ingests
  it. Returns `{ "status": "reset", "detail": {...} }`.

Errors: `400` if `document_id` is missing and `sweep` is not set.

> **One run at a time.** Corpus-wide runs (`/ingest/pdfs`, `/ingest/run`, crawl
> mode, sweep mode) are mutually exclusive with each other and with the background
> sweep — a second concurrent trigger returns `409 Conflict`. Ingest routes run the
> blocking work in a threadpool; when a Celery broker is configured they can be
> backed by workers instead. See [operations.md](operations.md#background-workers).
