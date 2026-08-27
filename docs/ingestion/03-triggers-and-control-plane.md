# 03 — Triggers, Transport and the Control Plane

**Purpose.** Decide when ingestion runs, who may make it run, how much of the
machine and of the upstream quota it may use, and how a run is stopped cleanly.

**Inputs.** A timer, an HTTP request, or a CLI invocation.

**Outputs.** An outcome `Counter` (in-process, or as an HTTP response body), and
log lines.

**Components.** `app/ingest_main.py`, `app/workers/scheduler.py`,
`app/workers/tasks.py`, `app/api/ingest.py`, `app/api/auth.py`,
`app/api/health.py`, `app/ingestion/pipeline.py`.

---

## The ingestion server

Ingestion runs in its own FastAPI process, separate from the retrieval server:

```
uvicorn app.ingest_main:app --port 8001
```

`app/ingest_main.py` does three things: it starts the sweep scheduler for the
lifetime of the process (via `lifespan`), it mounts the health and ingest
routers, and it declares:

```python
require_for_readiness("mysql")
```

MySQL is the system of record for ingestion — the crawl cursor, the retry floor
and every write live in it — so an ingestion server that cannot reach it is not
ready by any definition, and `/ready` answers 503. The retrieval server
deliberately makes no such claim: dense retrieval answers from Qdrant alone, and
taking the whole API out of a load balancer over a catalog blip would turn a
degraded feature into an outage.

---

## The five ways a run starts

### 1. The scheduled sweep

`start_sweep_scheduler()` reads `worker_sweep_interval_seconds` (default 3600). If
it is `<= 0` the scheduler logs that it is disabled and returns `None`; otherwise
it creates an asyncio task running `_sweep_loop`. **The first sweep runs
immediately**, then every interval.

The loop body, in order:

```python
while True:
    try:    result = await asyncio.to_thread(sweep)
    except  CancelledError: raise
    except  IngestBusyError: log "Skipping sweep; another run is in progress."
    except  Exception:       log.exception("Background sweep failed; retrying next interval.")
    if semantic_cache_enabled: prune the semantic cache   (own try/except)
    prune the ingest log                                  (own try/except)
    await asyncio.sleep(interval)
```

Three details:

- The sweep is blocking (network, DB, Qdrant I/O), so it runs in a worker thread
  via `asyncio.to_thread` and the event loop stays responsive to health probes.
- `CancelledError` is always re-raised, in each of the three guarded blocks, so
  shutdown is not swallowed by a bare `except Exception`.
- Each prune is guarded **independently**, so a failing cache prune cannot stop
  log retention and neither can stop the next sweep.

`stop_sweep_scheduler(task)` cancels and awaits, so a `SIGTERM` unwinds the loop
rather than killing it mid-write. A sweep already in flight completes its current
document or dies with the process — see
[10, Process killed mid-run](10-failures-retries-and-recovery.md#the-process-dies-mid-run).

### 2. `POST /ingest/run`

```json
{ "bundles": ["news", "block_content:basic"], "reconcile": false }
```

Runs `ingest_drupal(bundles, reconcile)` in the threadpool. `bundles` is
normalised by a validator that drops blanks and treats an empty list as "use the
defaults". Returns `{"drupal": {<outcome>: <count>, ...}}`.

Admin-only. Maps `IngestBusyError` to **409 Conflict**.

### 3. `POST /reindex`

Two modes:

- `{"sweep": true}` → runs the full `sweep()`. Admin-only, 409 when busy.
- `{"document_id": "..."}` → **queues** one document to be rebuilt.

The single-document mode is worth reading carefully, because it used to be the
most destructive operation in the system. It now **deletes nothing**:

```python
retries.record(document_id, ..., outcome="reindex",
               error="reindex requested by an operator")
state.clear_change_markers(document_id)
```

That is two facts stated, and the ordinary pipeline acts on them: the retry marker
floors the crawl window at this document's position so the next sweep actually
reaches it, and the cleared `fingerprint`/`content_hash` make the crawl call it
`CHANGED` and the pipeline re-index it rather than refresh a fingerprint. The
vectors, the catalog row, the facets and the attachment links all stay exactly
where they are, and are replaced only by the ordinary swap once the new version
is indexed — so the document is searchable throughout, and a failed or
interrupted rebuild leaves the version it already had.

`changed_mark` is deliberately **not** cleared: it is the document's position in
the crawl, and the retry marker needs it to pull the window back far enough to
reach the document at all.

The response is `{"status": "queued", ...}` — which says the request was
*recorded*, not that the rebuild has happened. A document that is not catalogued
answers **404**, because there is nothing to queue and answering 200 would repeat
the false confidence the old `status="reset"` gave for a document it had just made
unrecoverable.

`source_type` in the request is accepted for the API's shape and logged; the
catalogued row is authoritative for what the document actually is.

### 4. `POST /ingest/article`

The out-of-band injection path (`app/ingestion/upload.py`). Two behaviours:

- If `bundles` is set, it is just a scoped crawl (same as `/ingest/run`).
- Otherwise `title`/`body` are required (400 if both are missing), and the
  document is built with `from_drupal_export`, chunked, embedded and indexed
  **immediately**.

It keeps **no change-detection state**: no `documents` row, no fingerprint, no
`changed_mark`. So the document is not tracked for later re-crawls, will never be
updated by a sweep, and will show up in reconciliation as
`points_without_catalog_row`. That is the honest consequence of injecting content
that has no source to be compared against. It does write to the ingest log
(`indexed` or `error`, with its own `run_id`), so the injection is auditable.

Use it for testing and for genuinely out-of-band content. It is not a bulk import
mechanism.

### 5. The CLIs

```bash
python -m app.ingestion.pipeline [--bundle B]... [--reconcile]
                                 [--include-unpublished] [--dry-run-reconcile]
python -m app.workers.tasks {sweep|drupal} [--bundle B]... [--reconcile]
python -m app.ingestion.reprocess ...        # via scripts/reprocess_corpus.py
```

Plus the diagnostic entry points: `python -m app.ingestion.extractors.drupal_extractor`
(inspect records), `... .pdf_extractor <path>` (extract one PDF),
`python -m app.ingestion.chunking <path>` (inspect chunking),
`python -m app.ingestion.field_audit` (which source fields are kept or dropped),
and `python -m tools.local_tests.run_ingestion_test` (a full pipeline run against
isolated `local_test_*` tables and a `local_test_documents` collection).

CLIs take the same in-process lock, so they cannot race a sweep **within the same
process** — but a CLI run in a *separate* process can race the server's sweep.
See the warning under [Mutual exclusion](#mutual-exclusion) below.

---

## What `sweep()` actually does

```python
def sweep():
    result = {"drupal": ingest_drupal(reconcile=settings.worker_sweep_reconcile)}
    knowledge  = knowledge_sync.catch_up()      # bounded, returns not raises
    projection = graph_sync.project_after_sweep()
    report     = reconcile.reconcile_after_sweep()
    return result  # + knowledge_catch_up, graph_projection, reconciliation
```

The ordering is deliberate. The ingestion result is computed and logged **first**,
so nothing after it can change the sweep's outcome. Knowledge catch-up runs
*before* projection so anything it stages is in this sweep's graph refresh rather
than the next one. Reconciliation runs last so it reports the stores as they stand
after everything else.

All three post-sweep stages **return rather than raise**, in every direction. A
Neo4j outage, an unreadable knowledge queue or a failed reconciliation costs a log
line. See [09](09-knowledge-layer-and-graph.md) and
[11](11-observability-and-monitoring.md).

---

## Authentication and authorization

The ingestion control plane is protected **independently of the retrieval API**,
and **by default**.

```python
router = APIRouter(tags=["ingest"],
                   dependencies=[Depends(require_ingest_principal)])
_ADMIN_ONLY = [Depends(require_ingest_admin)]
```

| Route | Authentication | Authorization |
| --- | --- | --- |
| `POST /ingest/run` | required | `ingest_admin_group` |
| `POST /ingest/article` | required | `ingest_admin_group` |
| `POST /reindex` | required | `ingest_admin_group` |
| `GET /ingest/log` | required | none |
| `GET /health` | none | none |
| `GET /ready` | none | none (body detail gated by `ops_detail_enabled`) |
| `GET /metrics`, `/metrics/timings` | optional | `ops_admin_group`, or `ops_detail_enabled`; otherwise **404** |

### Why authentication covers the read-only log too

`GET /ingest/log` returns internal document ids, titles, source URLs and error
strings. That is deployment detail and, in the error column, sometimes stack-ish
text. Authentication applies to the whole control plane; only *authorization* is
per route.

### `ingest_auth_enabled`

Default **`true`**, and deliberately a separate switch from `auth_enabled`. These
routes crawl the whole corpus, inject documents into the answer set, queue
rebuilds and read back internal ids — a different exposure from the public
retrieval API. A deployment that has not enabled retrieval auth is precisely the
one that would otherwise leave these open.

Turn it off only for an ingestion server on a private interface whose operators
accept that anyone who can reach it may drive it.

### Token verification

One implementation, `_verified_principal`, shared with the retrieval API — two
verifiers would be two chances to get token handling wrong. It requires a Bearer
JWT, verified with `jwt_secret` and `jwt_algorithms`, `exp` **required**, audience
and issuer checked when configured. Groups come from `jwt_groups_claim` (string
or list) and default to `("public",)`. Groups never come from the request body.

Failure modes: missing token → 401; invalid/expired → 401 (logged at INFO);
`jwt_secret` unset while auth is required → **500** and an ERROR log, because that
is a misconfiguration, not a client error.

### The admin group

`ingest_admin_group()` returns `ingest_admin_group or ops_admin_group`, so a
deployment that already names an operations group need not name a second one,
while one that wants ingestion held to a narrower group can say so.

If **neither** is set, the check cannot mean anything — there is nothing to
compare a claim against — so any authenticated caller may proceed and the gap is
logged at WARNING:

> No ingest_admin_group (or ops_admin_group) is configured, so any authenticated
> caller may start a crawl or queue a reindex.

That warning is worth alerting on in a production deployment.

### Credentials to *downstream* systems

The pipeline holds several secrets, all from environment/`.env` via
`app/config.py`: `azure_openai_embedding_key`, `azure_openai_api_key`,
`azure_document_intelligence_key`, `qdrant_api_key`, `mysql_password`,
`neo4j_password`, `jwt_secret`. It holds **no** credential for the source site —
the crawl is anonymous. See [09, Security notes](09-knowledge-layer-and-graph.md)
and [12](12-operations-and-troubleshooting.md#security-and-access-control) for the
full picture.

---

## Mutual exclusion

```python
_run_lock = threading.Lock()

@contextmanager
def _exclusive(what: str):
    if not _run_lock.acquire(blocking=False):
        raise IngestBusyError(f"Another ingestion run is in progress; {what} rejected.")
    ...
```

**Non-blocking**, so a second request is refused immediately rather than queued —
a queued crawl would run against a window that has already moved.

`_exclusive` guards `ingest_drupal` and `reconcile_dry_run`. Concurrent runs would
double-embed documents and race each other's delete/upsert and `documents` writes.

**The lock is process-local by design**, because the ingestion server is a single
private instance. Two consequences you must plan around:

- Running more than one ingestion server against the same MySQL and Qdrant is
  **not safe**. There is no distributed lock.
- A CLI invocation in a separate process can race a running server's sweep. Stop
  the sweep (set the interval to 0 and restart, or take the process down) before
  running a corpus-wide CLI operation.

`IngestBusyError` surfaces as HTTP 409 through `_run_exclusive`, and as an INFO
log line in the scheduler.

---

## The run loop

`_run(records, build_doc)` in `pipeline.py`. Setup, in order:

1. `state.ensure_table()` — the state DDL and its idempotent migrations. Not
   guarded: without the catalog there is no ingestion. This also warms the MySQL
   pool on the calling thread.
2. `ingest_log.ensure_table()` — guarded; a failure means events are skipped, not
   that the run stops.
3. `enrichment.ensure_table()` — only when `enrichment_enabled`; guarded.
4. `_pending_retries()` — read **once**, so a healthy sweep issues no delete per
   document. Guarded; falls back to an empty set.
5. `run_id = uuid4().hex` — stamped on every log row this run writes.

Then the loop, sequential or parallel.

### Accounting and the tally

```python
tally_lock = threading.Lock()
def note(outcome):  tally[f"enrich_{outcome}"] += 1   # called from worker threads
def flag(obs):      tally[obs] += 1                   # e.g. "undated"
def account(out):   tally[out] += 1; maybe throttle   # main loop only
```

`note` and `flag` run on worker threads while `account` is owned by the main loop,
so every write to the shared `Counter` takes the lock. The two touch disjoint
keys, so CPython would get away without it — but "disjoint" is an invariant no
caller is told about, and the lock is uncontended either way. The throttle sleep
happens *outside* the lock, so `note` never waits on a batch pause.

### The batch budget

```python
_WORKED_OUTCOMES = {"indexed", "deleted", "skipped", "error"}
```

Only real work counts against the budget. `unchanged` and `unchanged_content`
scans are free and must never exhaust it, or a caught-up capped run would stall
before reaching the documents that actually changed.

`budget_reached(record, pending)`:

- Returns `False` immediately when `ingest_max_docs_per_run` is 0 (unlimited).
- Returns `False` for **any `pdf_attachment`**, so a run can only stop at a
  document boundary. An attachment record follows its node immediately and must
  land in the same run, or the node's freshly written state row would hide it from
  the next crawl.
- Counts in-flight futures pessimistically (`worked + pending < max_docs`), so the
  cap can never overshoot.
- On tripping: logs `Batch budget of %d documents reached; stopping cleanly (the
  next run resumes from the high-water mark).` and sets `tally["budget_stop"] = 1`.

Throttling within a run: after every `ingest_batch_size` worked outcomes, sleep
`ingest_batch_pause_seconds`. Both default to 0 (no throttling).

### Sequential vs parallel

`ingest_workers == 1` is a plain `for record in records:` loop.

`ingest_workers > 1` keeps the **crawler single-threaded** — per-run dedup and
node-before-attachment ordering live there — and works the heavy per-document I/O
(download, extract, embed, index) in a `ThreadPoolExecutor`:

```python
ensure_collection()          # pre-create once so workers don't race the create
_prewarm_clients(settings)   # embeddings client, tiktoken BPE, LLM if enriching
with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ingest") as pool:
    for record in records:
        harvest completed futures -> account()
        if budget_reached(record, pending=len(in_flight)): break
        while len(in_flight) >= workers * 2:
            wait(FIRST_COMPLETED) -> account()
        in_flight.add(pool.submit(handle, record))
    wait(in_flight) -> account()
```

`_prewarm_clients` exists because `functools.lru_cache` does not hold its lock
across the wrapped call: two workers that miss at the same time both construct a
client and one is silently discarded with its connection pool unclosed. Warming on
the main thread makes every worker a cache hit. It is best-effort in every
direction — a client that cannot be built now is built by whichever worker needs
it first, which is the behaviour that predates the function. `get_mysql_pool` is
deliberately absent: `state.ensure_table()` already warmed it on this thread, and
it is the one whose double construction would actually cost something (two pools,
twice the connections). `tiktoken` is warmed because it downloads its BPE table on
a cold cache and four threads racing that is four downloads.

Documents are independent across MySQL (pooled connections, per-document
transactions) and Qdrant (per-document points), so this is safe — with two
constraints:

- **Keep `ingest_workers` below `mysql_pool_size`** (default 5). A worker holds a
  connection for the duration of a catalog write; exhausting the pool raises
  `TimeoutError` after `mysql_pool_timeout` seconds.
- **Camelot is serialised** by a module-level lock in `camelot_tables.py`. Its
  backend (pypdfium2) keeps open-document bookkeeping in unlocked module state;
  two threads inside `read_pdf` race it, producing "Some kids weakrefs have not
  been cleaned up", an `AssertionError` from the object finalizer, and — once the
  underlying PDFium objects are freed twice — an intermittent hard crash of the
  whole process with `STATUS_HEAP_CORRUPTION` (0xC0000374). Seen at 2 and 4
  workers, never at 1, frequency scaling with the worker count. Everything else
  in the per-document path stays concurrent, and Camelot holds the GIL throughout
  anyway, so almost no parallelism is given up.

---

## Backpressure and rate limiting

The pipeline pushes on four external systems, and each has its own defence.

| Downstream | Pressure | Defence |
| --- | --- | --- |
| Drupal JSON:API | one request per page, plus one per PDF | `urllib3` `Retry` on 429/5xx with `backoff_factor=1.0` and `respect_retry_after_header`; single shared session; `drupal_page_size` bounds response size |
| Azure Document Intelligence | one call per document (or per scanned page range) | The SDK's own polling; failures return `{}` and the pages degrade to local text |
| Azure OpenAI embeddings | one call per 128 chunks | A **deployment-wide throttle gate** (below) plus `azure_openai_embedding_max_retries` (default 8) |
| MySQL | one transaction per document | A bounded LIFO pool (`mysql_pool_size`) with `mysql_pool_timeout` fail-fast |
| Qdrant | one retrieve + N upserts + one delete per document | Batches of 128 points |

### The embedding throttle gate

`app/core/clients/embeddings.py` installs httpx event hooks on the SDK's client:

- **Response hook.** Every embedding response is counted as `ok` / `throttled` /
  `error` in the `embedding_http` event family, visible in
  `GET /metrics/timings`. On a 429 it reads `retry-after` (numeric seconds *or*
  an HTTP-date, both legal), clamps it to
  `azure_openai_embedding_max_throttle_seconds` (default 60), and records a hold.
- **Request hook.** Every outgoing embedding request blocks until the hold
  expires.

The gate exists because retries alone do not stop `ingest_workers > 1` from
re-colliding: each worker backs off privately, so while one waits the others keep
spending the very quota it is waiting for and the deployment stays saturated.
Quota is a property of the Azure deployment, so the backoff has to be too. The
hold is stored as a **deadline, not a countdown**, so concurrent 429s collapse
into a single wait instead of stacking into a multiple of it.

An absent or unparseable `retry-after` falls back to the ceiling: pausing too long
is recoverable, pausing too little is what got us throttled.

`max_retries` defaults to **8**, not the SDK's 2, because Azure asks for
"retry after 3 seconds" under sustained load and 2 attempts is short of riding out
a throttling window — losing the document to `documents_retry` instead.

---

## Validation at this stage

| Check | On failure |
| --- | --- |
| Run lock acquired | `IngestBusyError` → 409, or a logged sweep skip |
| Bearer token present and valid | 401 |
| `jwt_secret` configured when auth required | 500 |
| Caller holds the admin group | 403 |
| `document_id` present unless `sweep=true` | 400 |
| Document is catalogued (for `/reindex`) | 404 |
| `title` or `body` present (for `/ingest/article` without bundles) | 400 |
| `bundles` entries non-blank | silently normalised; empty list means "defaults" |
| Table names are alphanumeric-plus-underscore | `safe_table()` falls back to the default name, so a bad `ingest_state_table` cannot become an injection vector |

## Failure scenarios

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| Sweep raises | `except Exception` in `_sweep_loop` | `logger.exception`, loop continues | Next interval |
| Sweep overruns the interval | The next tick finds the lock held | `IngestBusyError` → INFO skip | Nothing to do; consider a longer interval or a batch cap |
| MySQL down at startup | `/ready` probe | 503, taken out of the load balancer | Restore MySQL |
| MySQL down mid-run | Raised from the first catalog call | `state.ensure_table()` is unguarded, so the run raises and the scheduler logs it | Next interval |
| MySQL pool exhausted | `TimeoutError` after `mysql_pool_timeout` | Document fails → `error` outcome + retry marker | Lower `ingest_workers` below `mysql_pool_size` |
| Embedding deployment throttled | 429 hook | All embedding pauses; SDK retries within budget; WARNING logged | Automatic; if retries are exhausted the document errors and retries next sweep |
| Embedding quota exhausted for the whole window | Repeated `error` outcomes | Documents land in `documents_retry` and are retried next sweep | Raise quota, or cap the run with `ingest_max_docs_per_run` |
| Process killed mid-document | Nothing in-process | Points may exist without a committed row; the swap ordering means the previous version is intact | Next sweep re-processes; reconciliation reports `points_without_catalog_row` |
| Camelot crashes the process | Hard exit | — | Set `ingest_workers=1`; the module lock already prevents the known race |
| Unbounded log growth | `documents`/`ingest_log` size | `ingest_log_retention_days` (default 90) prunes in 10,000-row batches after each sweep | Set a retention window; `0` disables pruning |

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `worker_sweep_interval_seconds` | `3600` | Sweep cadence. `<= 0` disables the scheduler entirely. |
| `worker_sweep_reconcile` | `false` | Whether the scheduled sweep reconciles deletes. |
| `ingest_max_docs_per_run` | `0` | Cap on *worked* documents per run. 0 = unlimited. |
| `ingest_batch_size` | `0` | Throttle every N worked documents. |
| `ingest_batch_pause_seconds` | `0.0` | How long to pause. |
| `ingest_workers` | `1` | Concurrent per-document workers. Keep below `mysql_pool_size`. |
| `mysql_pool_size` | `5` | Pooled connections. |
| `mysql_pool_timeout` | `30` | Fail-fast wait for a free connection. |
| `ingest_auth_enabled` | `true` | Auth for the whole control plane. |
| `ingest_admin_group` | `""` | Group for mutating routes; falls back to `ops_admin_group`. |
| `ingest_log_enabled` | `true` | Whether events are recorded at all. |
| `ingest_log_unchanged` | `false` | Whether `UNCHANGED` documents get a row. Off because on an incremental sweep almost every document is unchanged, so logging each is one INSERT+commit per document and the main driver of log growth. |
| `ingest_log_retention_days` | `90` | Prune window. `0` disables pruning. |
| `verify_corpus_after_sweep` | `true` | Whether reconciliation runs. |

## Hand-off

The run loop hands each `ChangeRecord` to `_handle`. What `_handle` does with it
depends entirely on the record's status, which is [04](04-change-detection-and-versioning.md).

---

Previous: [02 — Sources and Data Acquisition](02-sources-and-acquisition.md) · Next: [04 — Change Detection and Versioning](04-change-detection-and-versioning.md)
