# 02 — Triggers and the API Surface

**Purpose.** Decide who may ask a question, how the answer is transported back
(streamed or buffered), and what protects the server from an unbounded burst
of concurrent generations.

**Inputs.** An HTTP request to `POST /chat` or `POST /search`.

**Outputs.** A Server-Sent Events stream, or a single JSON response; log lines
and, optionally, a retrieval trace.

**Components.** `app/main.py`, `app/app_factory.py`, `app/api/chat.py`,
`app/api/search.py`, `app/api/auth.py`, `app/api/health.py`,
`app/schemas/query.py`, `app/config.py`.

---

## The retrieval server

The read path runs in its own FastAPI process, separate from ingestion:

```
uvicorn app.main:app --port 8000
```

`app/main.py` is three lines of composition: `create_base_app` (shared logging,
CORS and observability wiring, in `app/app_factory.py`) plus the health, chat
and search routers. It declares no readiness requirement of its own.

Contrast with the ingestion server (`app/ingest_main.py`), which calls
`require_for_readiness("mysql")` because MySQL is its system of record. The
retrieval server never calls that function: dense retrieval answers from
Qdrant alone, and taking the whole public API out of a load balancer over a
MySQL blip would turn a degraded feature (structured answers, citations that
enrich from the catalog) into an outage of everything, including plain
semantic QA. `/ready` here is gated on Qdrant only — see
[`docs/ingestion/11-observability-and-monitoring.md`](../ingestion/11-observability-and-monitoring.md#ready-on-the-ingestion-server)
for the ingestion server's contrasting `/ready` contract, and 11 in this set
for the full probe.

**CORS is wildcard-open by default** (`cors_allow_origins = "*"`), logged as a
warning on startup. That is deliberate for an embeddable chat widget that must
work from any host page, and is tolerable only because `allow_credentials` is
hard-coded `False` — with a wildcard origin, ambient cookies would turn every
page embedding the widget into a CSRF vector — and because identity here comes
from a non-ambient bearer token, not a cookie. A deployment serving anything
non-public should pin `CORS_ALLOW_ORIGINS` to its actual host(s).

---

## The two ways a request enters

### 1. `POST /chat` — streamed

Event contract (`app/api/chat.py`), each `data:` line one JSON object keyed by
`type`:

| Event | Meaning |
| --- | --- |
| `token` | One answer fragment. Concatenate in arrival order. |
| `correction` | A full replacement answer text — a faithfulness or date-claim check flagged the streamed draft. `reason` says which. Discard every prior token. |
| `sources` | Citations plus answer metadata (`intent`, `answer_format`, `used_chunks`, `conflict`, `numeric_mismatch`). Follows the final answer text. |
| `done` | Normal end of stream. |
| `error` | The stream failed mid-response. The answer already sent is incomplete. |

`chat()` depends on `require_principal` purely for its side effect — the
authentication gate — and discards the `Principal` it returns: identity no
longer scopes retrieval, so nothing downstream reads it.

The generator returned by `stream_answer` (`app/pipeline/query_pipeline.py`) is
synchronous and blocking — it waits on Qdrant, MySQL and, per token, the LLM.
Iterating it directly on the event loop would pin one of the shared
request-threadpool's ~40 threads for the whole generation; enough concurrent
chats would starve auth dependencies, health probes and every other sync
offload sharing that pool. So `_sse` drives it from a **dedicated capacity
limiter** (`chat_stream_max_concurrency`, default 64):

```python
limiter = _chat_limiter()
while True:
    event = await anyio.to_thread.run_sync(_next_event, events, limiter=limiter)
    if event is _END:
        break
    yield f"data: {json.dumps(event)}\n\n"
```

Extra chats queue on the chat limiter rather than contending with the shared
pool. `StopIteration` cannot cross the async boundary (PEP 479), so `_next_event`
converts it to a private `_END` sentinel rather than letting it propagate.

**Mid-stream failure.** By the time an exception surfaces, the 200 response
and its headers are already on the wire — there is no HTTP status left to
change. The only way to tell the client the answer was cut short is a terminal
SSE `error` event; the exception itself is logged, not rendered, so an
unhandled failure never leaks internals to the browser. A bare client
disconnect (no exception) instead renders as a complete answer from the
client's point of view — there is no signal for that case beyond the
connection closing.

**Cleanup runs either way.** The `finally` block closes the underlying sync
generator (via the same limiter) on both normal completion and client
disconnect, so the pipeline's own `finally`/context-manager blocks — closing
spans, flushing any cache write already in flight — still execute rather than
being abandoned mid-frame.

### 2. `POST /search` — buffered

```python
result = await run_in_threadpool(search_blocks, request.question, ...)
return SearchResponse(**result)
```

No SSE, no generation, no semantic-cache read or write. `search_blocks` runs
the same understanding step and the same `retriever.retrieve` call as `/chat`,
then returns the retrieved `ContextBlock`s directly — score, conflict flag,
text, and payload fields (`document_id`, `source_type`, `title`, `page_number`,
`section_heading`) — plus the detected intent and multi-label `intents`. It
exists for inspection, debugging and evaluation harnesses that want retrieval's
output without paying for generation.

Both endpoints require `require_principal` and neither uses the identity it
returns for anything but the auth gate itself.

---

## Authentication and authorization

The retrieval API's authentication is a **separate switch from ingestion's**,
and — unlike ingestion's — **off by default**:

| Setting | Default | Governs |
| --- | --- | --- |
| `auth_enabled` | `false` | `/chat`, `/search` |
| `ops_admin_group` | `""` | Who may see `/metrics`, `/metrics/timings` when `ops_detail_enabled` is off |

| Route | Authentication | Authorization |
| --- | --- | --- |
| `POST /chat` | required when `auth_enabled` | none — identity is not used to scope anything |
| `POST /search` | required when `auth_enabled` | none |
| `GET /health` | none | none |
| `GET /ready` | none | none (body detail gated by `ops_detail_enabled`) |
| `GET /metrics`, `/metrics/timings` | optional | visible if `ops_detail_enabled`, or if `auth_enabled` and the caller holds `ops_admin_group`; otherwise **404**, not 401 — the endpoint's existence is itself deployment detail |

### One token verifier, two switches

`_verified_principal` (`app/api/auth.py`) is the **only** implementation of
"who is this?", shared between the public retrieval API and the ingestion
control plane — two verifiers would be two chances to get token handling
wrong. It requires a Bearer JWT verified with `jwt_secret` and `jwt_algorithms`
(default `HS256`), `exp` always required, audience/issuer checked only when
configured. Groups come from the `jwt_groups_claim` claim (string or list) and
default to `("public",)` when absent or when auth is disabled — **never from
the request body**; `QueryRequest` and `SearchRequest` have no group field for
exactly that reason.

What differs between the two APIs is *whether* identity is required at all —
`auth_enabled` here, `ingest_auth_enabled` (default `true`) on the ingestion
side — reflecting that a public Q&A endpoint and a corpus-mutating control
plane have very different default risk. See
[`docs/ingestion/03-triggers-and-control-plane.md#authentication-and-authorization`](../ingestion/03-triggers-and-control-plane.md#authentication-and-authorization)
for the ingestion side of the same mechanism.

`optional_principal` backs the two `/metrics*` routes: a missing or invalid
token degrades to the anonymous principal instead of a 401, because a 401
would confirm the endpoint exists to a caller who was never going to be
let in — the routes already answer 404 to anyone `_ops_visible` rejects, and a
distinguishable auth failure would leak that distinction back.

### Failure modes

| Condition | Result |
| --- | --- |
| Missing bearer token, `auth_enabled=true` | 401 |
| Invalid or expired token | 401, logged at INFO |
| `jwt_secret` unset while auth is required | **500**, logged at ERROR — a misconfiguration, not a client error |
| Token valid but caller lacks `ops_admin_group` (metrics routes) | 404 |

---

## Backpressure and concurrency

The read path shares one external pressure point with ingestion and adds one
of its own.

| Pressure point | Defence |
| --- | --- |
| Concurrent chat generations | `chat_stream_max_concurrency` (default 64) on a dedicated `anyio.CapacityLimiter`; extra requests queue rather than exhausting the shared request threadpool. |
| Azure OpenAI embeddings | The same deployment-wide throttle gate ingestion uses (`app/core/clients/embeddings.py`) — every `embed_query` call on this path is subject to the identical 429 back-off and retry budget (`azure_openai_embedding_max_retries`, default 8). A throttled deployment slows both paths together, by design: it is one quota. |
| Request body size | Bounded input: `top_k` is clamped `1..50` by `QueryRequest`/`SearchRequest`, and `question` requires at least one character — an unbounded `top_k` would inflate retrieval and context-assembly work per request for no benefit. |

There is no per-caller rate limit and no request queue beyond the chat
limiter: a deployment expecting public traffic is expected to rate-limit at
the edge (reverse proxy, gateway), not in this process.

---

## Validation at this stage

| Check | On failure |
| --- | --- |
| Bearer token present and valid (`auth_enabled`) | 401 |
| `jwt_secret` configured when auth is required | 500 |
| `question` non-empty | 422 (Pydantic) |
| `top_k` within `1..50` | 422 (Pydantic) |
| Caller holds `ops_admin_group` for `/metrics*` when `ops_detail_enabled` is off | 404 |

## Failure scenarios

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| Missing/invalid bearer token | `require_principal` | 401 | Caller supplies a valid token |
| `jwt_secret` unset, auth required | `_verified_principal` | 500, ERROR logged | Configure `jwt_secret` |
| Generation raises mid-stream | `except Exception` in `_sse` | SSE `error` event; `logger.exception` | Client retries the question |
| Client disconnects mid-stream | `finally` closes the generator | Pipeline's own cleanup (spans, in-flight cache write) still runs; no client-visible signal | Nothing to recover — the client already left |
| Burst of concurrent chats | Chat capacity limiter saturated | Requests queue behind the limiter rather than the request threadpool | Raise `chat_stream_max_concurrency`, or add server capacity |
| Embedding deployment throttled | 429 hook in `core/clients/embeddings.py` | Every embedding call (chat and ingestion alike) pauses; retried within budget | Automatic; shared with ingestion — see [`docs/ingestion/03-triggers-and-control-plane.md#the-embedding-throttle-gate`](../ingestion/03-triggers-and-control-plane.md#the-embedding-throttle-gate) |
| CORS left wildcard in a non-public deployment | Startup WARNING log | None enforced — the log is the only signal | Set `CORS_ALLOW_ORIGINS` |

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `auth_enabled` | `false` | Authentication for `/chat`, `/search`. |
| `jwt_secret` | `""` | Shared secret (HS*) or PEM public key (RS*/ES*) for verifying tokens. |
| `jwt_algorithms` | `"HS256"` | Comma-separated allow-list; anything else, including unsigned `none`, is rejected. |
| `jwt_audience` / `jwt_issuer` | `""` / `""` | Enforced only when set. |
| `jwt_groups_claim` | `"groups"` | Claim carrying the caller's authorization groups. |
| `cors_allow_origins` | `"*"` | Comma-separated allow-list; `*` or empty logs a startup warning. |
| `chat_stream_max_concurrency` | `64` | Concurrent `/chat` generations before extra requests queue. |
| `ops_detail_enabled` | `false` | Whether `/ready` and `/metrics` bodies are visible without a group. |
| `ops_admin_group` | `""` | Group that may see `/metrics*` when `ops_detail_enabled` is off. Only honored when `auth_enabled`. |
| `retrieval_top_k` | `6` | Server default when a request omits `top_k`. |

## Hand-off

Both entry points converge on `process(question, history)` — how a question
becomes a `ProcessedQuery` is [03](03-query-understanding.md).

---

Previous: [01 — Read Path Overview](01-overview.md) · Next: [03 — Query Understanding](03-query-understanding.md)
