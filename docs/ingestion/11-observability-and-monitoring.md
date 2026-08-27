# 11 — Observability, Monitoring and Alerting

**Purpose.** Make the pipeline's behaviour legible: what it did, how long it took,
what it could not do, and whether the stores still agree with each other.

**Components.** `app/observability/tracing.py`, `app/observability/metrics.py`,
`app/api/health.py`, `app/ingestion/reconcile.py`, `app/catalog/log.py`.

---

## Four layers of visibility

| Layer | Question | Where |
| --- | --- | --- |
| **Logs** | What happened to this document? | stdout, and `ingest_log` |
| **Run tallies** | What did this run do, in aggregate? | the returned `Counter`, and the `ingest_throughput` line |
| **Timing metrics** | Where does the time go? | spans → `GET /metrics/timings` |
| **Reconciliation** | Do the stores still agree? | per sweep → logs and `GET /metrics` |

Each catches a different class of problem, and the fourth catches the class the
others structurally cannot.

---

## Logging

Standard `logging`, configured by whatever hosts the process. The CLIs set
`level=INFO, format="%(levelname)s %(name)s: %(message)s"`.

### The lines that matter most

Per run:

```
INFO app.ingestion.pipeline: Drupal ingestion started (bundles=default, reconcile=False)
INFO app.ingestion.pipeline: ingest_throughput workers=4 elapsed_seconds=612.3
     documents_processed=180 documents_per_minute=17.6 errors=2
     enrichment_failures=0 indexed_without_date=3
INFO app.ingestion.pipeline: Drupal ingestion finished: {'unchanged': 5821, 'indexed': 178, 'error': 2}
INFO app.workers.tasks: Sweep complete: {...}
```

Per document:

```
INFO  Ingesting website <uuid> (https://teriin.org/…)
INFO  Extracted report.pdf: 42 page(s), 6 table(s); OCR on page(s) [1, 2]
INFO  Indexed 47 points (39 children: 12 embedded, 27 reused; 8 parents) into 'documents'
INFO  changed <uuid> -> v3
INFO  Unchanged content for <uuid>; fingerprint refreshed.
INFO  Deleted <uuid> (https://…)
INFO  Deleted 2 attachment(s) orphaned by <uuid>; 3 still linked elsewhere.
WARN  Indexing <uuid> (website/news) with no publication date; it will be excluded
      from date-filtered results.
ERROR <uuid> (…) extracted to nothing; keeping the previous version rather than
      replacing it with an empty one.
```

### `ingest_throughput`, and why it is throughput not latency

```python
per_minute = worked / elapsed * 60
```

Deliberately **not** per-document latency: the `ingest.*` spans measure that already,
and it gets *worse* under concurrency even as the run gets faster — workers contend,
so each document takes longer while more of them finish per minute. Throughput is
the number that moves in the direction `ingest_workers` is meant to move it.

`documents_processed` is the **budget's** notion of work (`_WORKED_OUTCOMES`), so
unchanged scans — which cost nothing and would otherwise inflate the rate — are
excluded, and two runs over different-sized changed sets stay comparable.

The line also carries `errors`, `enrichment_failures` (`enrich_failed + enrich_error`)
and `indexed_without_date`. Those three are the run-level health signals.

### Log levels, by intent

| Level | Used for |
| --- | --- |
| `DEBUG` | Span timings, "could not read stored vectors; embedding every chunk", classifier hiccups on one page |
| `INFO` | Every normal outcome, every deliberate skip, every date-gate downgrade, the throttle gate holding a request |
| `WARNING` | Something degraded but handled: a bundle skipped, an attachment dead, a table unreachable, a fail-open catalog write, **a refused delete reconciliation**, an undated document, drift found |
| `ERROR`/`exception` | A document lost this run, or a component that was expected to work did not |

The convention worth relying on: **a WARNING means "the pipeline handled this, and a
human should know"**. Nothing routine logs at WARNING, which is what makes WARNING
worth alerting on.

---

## The ingest log as a queryable audit trail

`ingest_log` — one row per document per run, append-only, retention-pruned. See
[08](08-persistence-and-catalog.md#ingest_log) for the schema.

`GET /ingest/log?limit=100&status=error&source_type=pdf_attachment&document_id=...`
returns the most recent rows first by insertion order, capped at 1000, with
`event_time` rendered as ISO. Authenticated (no group required).

```sql
-- One run, end to end
SELECT status, COUNT(*) FROM ingest_log WHERE run_id = '<hex>' GROUP BY 1;

-- What happened to one document over time
SELECT event_time, run_id, status, doc_version, chunks_indexed, LEFT(error_message,160)
FROM ingest_log WHERE document_id = '...' ORDER BY id DESC;

-- Error trend by day
SELECT DATE(event_time) d, status, COUNT(*) FROM ingest_log
WHERE status IN ('error','skipped') GROUP BY 1,2 ORDER BY 1 DESC;

-- Which errors, grouped by message shape
SELECT LEFT(error_message, 80) cause, COUNT(*) n FROM ingest_log
WHERE status IN ('error','skipped') AND event_time > NOW() - INTERVAL 7 DAY
GROUP BY 1 ORDER BY n DESC;

-- Indexing volume per sweep
SELECT run_id, MIN(event_time) started, COUNT(*) events,
       SUM(status='indexed') indexed, SUM(chunks_indexed) points
FROM ingest_log GROUP BY run_id ORDER BY started DESC LIMIT 20;
```

`ingest_log_unchanged` is **off** by default, so an incremental sweep writes rows only
for documents something happened to. Turning it on writes one INSERT+commit per
document and is the main driver of the log's growth — useful for a short
investigation, not as a standing setting.

**Retention is also recovery evidence.** `ingest_log_retention_days` (default 90) is
how far back `scripts.recover_stranded` can see; lowering it discards the only trace
of documents that failed before they were ever catalogued.

`prune()` deletes in 10,000-row batches so a large backlog never holds one long
row-lock transaction, and never raises — retention is housekeeping and must not break
the sweep loop.

---

## Spans and timing metrics

`tracing.span(name, **attrs)` is a context manager that records elapsed time into the
in-process registry and, when OpenTelemetry is enabled, into a real OTel span.

### The ingestion spans

| Span | Wraps | Attributes | Component |
| --- | --- | --- | --- |
| `ingest.extract` | the whole document build (download + extract + date) | `source_type` | `extraction` |
| `ingest.chunk` | `chunk_canonical` | — | `other` |
| `ingest.embed` | the embedding calls | `chunks`, `reused` | `embedding` |
| `ingest.upsert` | the batched upserts | `points` | `qdrant` |

`GET /metrics/timings` returns per-stage `count / total_ms / avg / p50 / p95 / max`
plus per-component totals and shares:

```json
{"since": "...", "window": 512,
 "components": [{"component": "extraction", "total_ms": 412000.0, "calls": 180, "share_pct": 61.2},
                {"component": "embedding",  "total_ms": 141000.0, "calls": 180, "share_pct": 21.0}],
 "stages": [{"stage": "ingest.extract", "component": "extraction", "count": 180,
             "total_ms": 412000.0, "avg_ms": 2288.9, "p50_ms": 1420.0,
             "p95_ms": 9100.0, "max_ms": 41000.0}],
 "events": {"embedding_http": {"total": 1204,
                               "counts": {"ok": 1198, "throttled": 6},
                               "share_pct": {"ok": 99.5, "throttled": 0.5}}}}
```

Percentiles cover a rolling window of the last **512** samples per stage. The registry
is **per process** and resets on restart, so treat it as a live view rather than a
time series — export to OTel if you need history.

### Outcome counters

`metrics.record_event(family, outcome)` counts things that stage timings cannot
express: **a route that silently fell back looks identical to one that was never
attempted unless the two are counted apart.** The family ingestion uses is
`embedding_http` (`ok` / `throttled` / `error`), and it is the earliest visible sign
of quota pressure — the SDK swallows a retried 429, so the call succeeds and nothing
upstream learns the deployment is at its quota until the retry budget runs out and a
document lands in `documents_retry` instead.

### OpenTelemetry

`otel_enabled` (default false) installs an SDK tracer with
`service.name = otel_service_name`, and an OTLP/HTTP exporter when
`otel_exporter_otlp_endpoint` is set. A missing SDK or bad config logs a warning and
leaves tracing off — it never fails the process. Span attributes are set on the OTel
span at exit.

---

## Health and readiness

| Endpoint | Auth | Answers |
| --- | --- | --- |
| `GET /health` | none | `{"status": "ok"}` — the process is up |
| `GET /ready` | none | 200/503. **The status code is the contract**; the body carries infrastructure detail only when `ops_detail_enabled`, because error strings and point counts fingerprint the deployment |
| `GET /metrics` | ops-gated → else **404** | Reconciliation summary, store reachability, knowledge health, retrieval config |
| `GET /metrics/timings` | ops-gated → else **404** | Stage and component timings, event counters |

`/metrics` answers **404, not 403**, to callers who may not see it: its whole body is
deployment detail, so the endpoint is hidden entirely rather than advertised.

### `/ready` on the ingestion server

`_REQUIRED_STORES` is `{"qdrant"}` by default; `app/ingest_main.py` adds `"mysql"`.
So the ingestion server is not ready without either. Probes it does not need and
nobody will read are skipped rather than paid for.

With `ops_detail_enabled`, the body adds `redis` and `neo4j` probes. Neo4j reports
reachability as a **value rather than an exception**, and returns
`{"enabled": false}` without opening a connection when `knowledge_enabled` is off.

### `/metrics` body

```json
{"service": "agentic-rag",
 "corpus_reconciliation": {"ok": false, "documents": 12043, "points": 391204,
                           "drift": {"documents_without_date": 37}},
 "qdrant": {"reachable": true, "collection": "documents",
            "collection_exists": true, "points": 391204},
 "redis": {"configured": true, "reachable": true},
 "neo4j": {"enabled": true, "reachable": true, "nodes": 8412, "relationships": 19022},
 "knowledge": {"enabled": true, "process_after_index": true, "knowledge_version": "...",
               "runs": {...}, "pending": 3, "latest": [...], "recent_errors": [...]},
 "reranker_provider": "...", "retrieval": {...}, "caches": {"semantic": true}}
```

`corpus_reconciliation` is **the last reconciliation this process ran, never a fresh
one**: the checks scroll the whole collection, which is not something a metrics
scrape may trigger. It is `null` until the first sweep has finished one.

---

## Cross-store reconciliation

`app/ingestion/reconcile.py`, run after every sweep when
`verify_corpus_after_sweep` is on (default).

### Why it exists

Nothing compared the stores. The test suite was green, `/ready` was green, `/metrics`
was green, and **the catalog said every document was indexed while 85 of them had no
retrievable content at all.** The defect that produced them was found by one full
scroll and three SQL queries — which is exactly what this does, on every sweep,
loudly.

### Shape

One scroll of the collection builds a per-document picture (points, versions,
parents, payload stamps), one query builds the catalog's, and each invariant is a
`Check` over the pair. A check reports a count, up to five example ids, and **what to
do about it** — a number with no next step is how drift gets watched rather than
fixed.

The scroll requests only seven payload fields
(`document_id, doc_version, is_parent, chunk_id, parent_chunk_id, published_at,
pipeline_version`) — `chunk_text` alone would be a hundred times the bytes.

### Failure semantics

**This reads. It never deletes, re-indexes or repairs anything.** A reconciliation
that acted on what it found would be a second, unsupervised ingestion path, and the
failure mode of a wrong reading would be data loss rather than a wrong number.

Optional stores are treated as optional: an unreachable Neo4j is **skipped**, never a
violation — a graph outage must not make a healthy corpus look broken. Qdrant and
MySQL are the system of record and its index; if either cannot be read the report
says so and fails, because at that point nothing can be verified.

A **skipped check is not a passing check** and is never reported as one.

### The checks

| Check | Non-zero means | What to do |
| --- | --- | --- |
| `indexed_without_points` | The catalog reports the document indexed and it has no points at all. **The signature of the defect this module was written for.** | Clear its content hash (`state.clear_change_markers`) and let the next sweep rebuild it |
| `points_without_catalog_row` | Points for a document the catalog has never heard of — the delete path leaving vectors behind, an ingest that wrote points and lost its row, or a `/ingest/article` injection | Retrievable and uncatalogued; `delete_document(id)` removes them |
| `duplicate_live_versions` | A document's points carry more than one `doc_version` — an interrupted swap | Re-index to collapse it |
| `version_mismatch` | Points disagree with the catalog's `doc_version` — the swap completed and the row did not follow | Re-index; the catalog is authoritative |
| `chunk_id_mismatch` | A point's payload `chunk_id` is not its own id. **Citations resolve by payload, so these cite the wrong chunk** | Re-index |
| `children_without_parent` | A child names a parent that does not exist | Context expansion falls back to the child alone; re-index |
| `catalog_pipeline_drift` | Documents not built by the current pipeline | `scripts.reprocess_corpus` |
| `point_pipeline_drift` | Points written by a different pipeline — **a document can be stamped current while old points survive beside the new ones**, so both sides are checked | Re-indexing replaces them |
| `documents_without_date` | Documents with no publication date. Not an error — some sources state none — but they are **invisible** to date filters and recency ranking rather than merely ranked low | Check the source exposes a date field |
| `date_provenance_unrecorded` | `published_at` with no recorded origin. Every write path sets it, so these came from one that does not — or predate the backfill | `scripts.backfill_date_provenance` |
| `stated_date_not_applied` | The source states a publication date that `published_at` does not match | Re-run `scripts.backfill_source_dates`. Note `app.ingestion.backfill` lifts dates out of chunk payloads and can overwrite a resolved value |
| `undeclared_source_date_field` | A source field that looks like a date and holds a parseable one, which nothing has classified. It is being **ignored** — the safe direction — but if it is a publication date those documents are mis-dated | Classify it in `source_dates.FIELD_KINDS` |
| `year_precision_not_january` | A year-precision date whose value is not 1 January. The day is a marker for the year, so anything else means the value and its precision disagree about what is known | Investigate |
| `graph_projection` | MySQL-vs-graph disagreement, **or** the projection has stopped running / has no stamp | `scripts.project_graph`; check `graph_project_after_sweep` |

### The bar for living here

Every one of these checks was **zero when it was written**, and each has a specific
cause when it stops being zero. That is the bar: a check that is non-zero in a healthy
corpus would make every sweep warn, and **a warning that is always on is not a
warning.**

`scripts.audit_dates` keeps the deeper measurements that are legitimately non-zero —
30 documents dated before the period their own name states, 2,796 dated by an import
batch with nothing better available.

The date checks are additionally each independently fail-soft: an unreadable catalogue
reports a **skipped** check rather than failing a sweep that otherwise worked.

`stated_date_not_applied` deliberately calls `resolve_published_at` — the same single
decision ingestion and the backfill make — rather than `publication_date` directly.
Asking `publication_date` would be a third copy of the rule, and it would miscount the
228 documents whose stated *year* the stored date already falls in, which the design
deliberately leaves alone.

### Output

```
INFO  corpus_reconcile ok=true documents=12043 points=391204
      indexed_without_points=0 points_without_catalog_row=0 ...

WARN  corpus_reconcile ok=false documents=12043 points=391204 ...
WARN  corpus_drift documents_without_date=37 samples=a1b2,c3d4,… — Documents with
      no publication date. They are invisible to date filters and to recency
      ranking; check the source exposes a date field.
```

Drift is logged at WARNING with the offending counts — the whole point is that it
stops being silent — but it **does not fail the sweep**: the documents that ingested
successfully did so, and refusing to admit that would help nobody.

The report is kept in `_last` for `/metrics` to show.

### On demand

```bash
python -m scripts.verify_corpus            # human-readable
python -m scripts.verify_corpus --json     # machine-readable
```

Exit codes: **0** clean, **1** drift found, **2** the stores could not be read. That
makes it usable as a deployment gate.

Run it after a rebuild, after a sweep, or whenever an answer looks wrong.

### Cost

One full scroll of the collection per sweep, plus a handful of queries — including one
that reads every `raw_meta` blob for the date checks. On a corpus of ~390k points that
is seconds to a couple of minutes. It is the price of not discovering silent drift
months later. If it becomes too expensive, turn it off deliberately
(`verify_corpus_after_sweep=false`) and schedule `scripts.verify_corpus` instead —
do not leave it half-on.

---

## What to alert on

Ordered by how directly it means "someone must act".

### Page

| Signal | Why |
| --- | --- |
| `GET /ready` returns 503 for > 2 probe intervals | MySQL or Qdrant is gone; ingestion is stopped |
| `VectorDimensionMismatch` in logs | Writes are being rejected; a configuration mistake |
| No `Drupal ingestion finished` line for > 3 × `worker_sweep_interval_seconds` | The scheduler has stopped, or a sweep is wedged |

### Investigate today

| Signal | Why |
| --- | --- |
| `Refusing to reconcile deletes for …` | Either the source is broken or a real mass removal is being held back. Both need a human |
| `corpus_reconcile ok=false` with `indexed_without_points > 0` | Documents claim to be indexed and answer nothing |
| `corpus_reconcile ok=false` with `chunk_id_mismatch > 0` | Citations point at the wrong text |
| `documents_retry` count rising sweep over sweep | Failures are accumulating, and each holds its bundle's window open |
| `error` count in the run tally rising | Same, at the run level |
| `embedding_http.throttled` share > a few percent | Quota pressure; documents will start erroring |
| `budget_stop = 1` on consecutive runs | The pipeline is not keeping up with the change rate |
| No `ingest_admin_group` configured (WARNING at startup of every admin call) | The control plane is effectively open to any authenticated caller |

### Watch as a trend

| Signal | Why |
| --- | --- |
| `documents_per_minute` dropping | Source slower, more OCR, more contention |
| `indexed_without_date` non-zero and growing | A source field changed, or a new bundle has no date field |
| `enrich_failed + enrich_error` non-zero | The abstract cache is silently re-paying per document |
| `documents_date_decision` where `action='needs_manual_review'` growing | A review queue nobody is working |
| `documents_dead_link` growing | Link rot at the source |
| `catalog_pipeline_drift` non-zero after a version bump | A reprocess is owed |
| `documents_knowledge_run` `pending` depth growing | The knowledge backlog is draining slower than it accumulates |
| `ingest_log` table size | Retention is off or too long |

---

## Diagnostic recipes

**"Which documents did this sweep touch, and what happened?"**

```sql
SELECT status, COUNT(*) FROM ingest_log
WHERE run_id = (SELECT run_id FROM ingest_log ORDER BY id DESC LIMIT 1)
GROUP BY 1;
```

**"Is the corpus complete?"**

```bash
python -m scripts.verify_corpus
```

**"Why is document X not in answers?"**

```sql
SELECT document_id, source_type, bundle, doc_version, pipeline_version,
       fingerprint, content_hash, published_at, published_at_source, indexed_at
FROM documents WHERE document_id = '...';

SELECT * FROM documents_retry     WHERE document_id = '...';
SELECT * FROM documents_dead_link WHERE document_id = '...';

SELECT event_time, status, doc_version, chunks_indexed, LEFT(error_message,200)
FROM ingest_log WHERE document_id = '...' ORDER BY id DESC LIMIT 10;
```

Then check the points exist (`document_id` is an indexed payload field) and that
`published_at` is set — an undated document is invisible to every date filter.

**"Where is the time going?"**

```
GET /metrics/timings
```

`extraction` dominant → PDFs and OCR. `embedding` dominant → little vector reuse
(expected right after a version bump or a mass retitle). `qdrant` dominant → check
batch sizes and the store's health. `other` dominant → chunking, which usually means
very large documents.

**"Is anything being throttled?"**

`GET /metrics/timings` → `events.embedding_http`.

**"Did the last code change reach the corpus?"**

```bash
python -m scripts.reprocess_corpus --dry-run
```

Zero stale documents means yes.

---

## The local test harness

```bash
python -m tools.local_tests.run_ingestion_test --bundle article --max-docs 3
python -m tools.local_tests.run_ingestion_test --cleanup
```

Runs **only** the ingestion pipeline and reports every stage per document: change
detection, extraction, canonical mapping, chunking, indexing, and exactly what landed
in MySQL. It crawls live Drupal nodes of one bundle plus the PDFs attached to or
linked from them.

**Isolated by default**: all writes go to `local_test_*` MySQL tables and a
`local_test_documents` Qdrant collection, never the real catalog. Documents are
processed through the pipeline's own per-document handler, so it exercises the real
code path.

Run it twice to see change detection in action: the second run reports the same
documents as `UNCHANGED` straight from the MySQL state table.

This is the fastest way to validate a pipeline change against real data without
touching production state.

---

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `verify_corpus_after_sweep` | `true` | Whether reconciliation runs per sweep. |
| `metrics_log_enabled` | — | Whether `rag_metrics` lines are emitted (retrieval-side). |
| `otel_enabled` | `false` | OpenTelemetry tracing. |
| `otel_service_name` | `agentic-rag` | `service.name`. |
| `otel_exporter_otlp_endpoint` | `""` | OTLP/HTTP endpoint. Unset means spans are recorded in-process only. |
| `ops_detail_enabled` | — | Whether `/ready` and `/metrics` bodies are visible without a group. |
| `ops_admin_group` | `""` | Group that may see `/metrics`. |
| `ingest_log_enabled` | `true` | The audit trail. |
| `ingest_log_unchanged` | `false` | Rows for unchanged documents. |
| `ingest_log_retention_days` | `90` | Prune window, and how far back recovery can see. |

---

Previous: [10 — Failures, Retries and Recovery](10-failures-retries-and-recovery.md) · Next: [12 — Operations, Configuration and Troubleshooting](12-operations-and-troubleshooting.md)
