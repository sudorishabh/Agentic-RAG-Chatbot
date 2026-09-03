# 10 — Failures, Retries and Recovery

**Purpose.** One place that says, for every way this pipeline can go wrong: how it is
detected, what the system does, whether data is retried or discarded, how recovery
works, and what an operator should do.

**Components.** `app/ingestion/pipeline.py` (outcomes and retry bookkeeping),
`app/catalog/retries.py`, `app/catalog/dead_links.py`,
`app/ingestion/recovery.py`, `app/ingestion/reprocess.py`,
`app/ingestion/reconcile.py`, `app/workers/tasks.py`.

---

## The two failure philosophies

Every decision in this pipeline picks one of these, and which one it picks is never
arbitrary.

**Fail open — for external dependencies.** A failure costs a log line and, at worst,
one document's freshness. It never costs the run. This applies to: every catalog
write on the ingest path, dead-link marking, retry marking, enrichment, date-decision
recording, the knowledge layer, graph projection, reconciliation, orphan collection,
and log writes.

**Fail closed — for anything that would change or remove content.** Weak or missing
evidence leaves the existing state untouched. This applies to: empty extractions,
delete reconciliation, date overrides, `delete_document(keep_ids=[])`, bundle-move
confirmation, and the vector-reuse key.

If you are adding code here, decide which one you are in before you write the
`except`.

---

## The outcome vocabulary

`ingest_drupal` returns a `Counter`. Every document that reaches processing ends in
exactly one outcome.

| Outcome | Meaning | Retry marker | Counts against budget |
| --- | --- | --- | --- |
| `indexed` | Chunked, embedded, upserted, swapped, persisted, logged | **cleared** (if pending) | yes |
| `unchanged` | Fingerprint matched and the pipeline version is current; never built | — | no |
| `unchanged_content` | Fingerprint moved, content hash and version did not; row and payload title refreshed, nothing re-embedded | **cleared** (if pending) | no |
| `deleted` | Points and row removed; orphaned attachments collected | **cleared** (if pending) | yes |
| `skipped` | The document could not be built — download or extraction returned nothing | **written** | yes |
| `error` | The document raised, or extracted to nothing | **written** | yes |

Plus two run-level counters that are not outcomes:

| Key | Meaning |
| --- | --- |
| `undated` | Documents indexed with no effective date. Reported as `indexed_without_date`. |
| `budget_stop` | Set to 1 when the run stopped on its document cap. |

And the enrichment tally: `enrich_hit`, `enrich_stored`, `enrich_skipped`,
`enrich_failed`, `enrich_exhausted`, `enrich_error`, `enrich_aborted`.

### The outcome sets, and the one that is in neither

```python
_UNRESOLVED_OUTCOMES = {"error", "skipped"}
_RESOLVED_OUTCOMES   = {"indexed", "unchanged_content", "deleted"}
_WORKED_OUTCOMES     = {"indexed", "deleted", "skipped", "error"}
```

A document that reached processing **must** end in one of the first two sets, or the
crawl cursor loses track of it. `unchanged` is in neither: it never reached a build,
and a document that is unchanged already has the catalog row that positions the
cursor.

---

## The complete failure catalogue

### Source and network

| Scenario | Detection | Response | Data fate | Operator action |
| --- | --- | --- | --- | --- |
| Source host down | `RequestException` in `iter_bundle_records` | `logger.exception`, that bundle skipped, run continues | Nothing lost; the high-water mark did not move | None; check the site if it persists |
| One bundle 400s | Same | Same, per bundle | Nothing lost | Check the bundle name / sort field |
| Mid-pagination failure | Same | Bundle abandoned mid-walk | Records already yielded were processed; the rest wait | None |
| Source slow / timeout | `drupal_request_timeout` | Per-request; retried by `urllib3` for 429/5xx | — | Raise the timeout, or lower `drupal_page_size` |
| Source rate-limits (429) | `status_forcelist` | Retried with `backoff_factor=1.0`, honouring `Retry-After` | — | Lower `drupal_page_size`, add `ingest_batch_pause_seconds` |
| Relationship sample fails | `except` in `_discover_relationship_fields` | Warning; crawl continues without `include` | Labels missing this run | None; returns next run |
| PDF download times out | `RequestException` (not 4xx) | Full traceback, `skipped` | **Retried** next sweep | None |
| PDF 404/403 | `dead_link_status` is a 4xx | One warning, **dead-link marker**, `skipped` | Suppressed until the fingerprint changes | Re-upload and save the node, or clear the marker |
| PDF body empty | `not content` | Warning, `skipped` | Retried next sweep | Check the file at source |
| Plain-http PDF host gone | Connect hang | HTTPS variant tried **first** | — | None |

### Extraction

| Scenario | Detection | Response | Data fate | Operator action |
| --- | --- | --- | --- | --- |
| PDF corrupt / not a PDF | PyMuPDF raises in `classify_document` | Whole document biased to Azure; if that also fails, empty extraction → `error` | **Previous version kept** | Fix or remove the source file |
| Pure scan, Azure unconfigured | `_di_client()` is `None` | Warning; pages degrade to local text (empty) → `error` | Previous version kept | Configure Azure DI |
| Azure DI fails | `except` in `_ocr_pdf` | `logger.exception`, `{}`; those pages get local text | Document indexed with degraded pages | Check the DI endpoint/quota |
| Camelot missing / Ghostscript missing | Import error / raise | `{}`; page keeps its prose | Tables degrade to plain text | Install Camelot / Ghostscript |
| PDF forbids extraction | `PDFTextExtractionNotAllowed` | Warning; local text | Tables lost | None |
| Camelot leaks temp files (Windows) | Temp dir growth | `gc.collect()` + retry delete | — | Watch the temp dir |
| Camelot races under workers | Process crash `0xC0000374` | Prevented by `_camelot_lock` | — | `ingest_workers=1` if it recurs |
| **Extraction produces nothing** | `_extraction_is_empty` | `error`, **nothing below runs** | **Previous version fully intact** — vectors, row, `indexed_at` | Investigate; retry marker brings it back |
| PUA / `(cid:N)` text layer | **Not detected** | Indexed as garbage | Garbage indexed | Re-source the PDF; a manual `azure_only` run may help |
| Running-header stripper removes real content | Manual reading | Parity rule + key-length window limit it | Content lost from the chunk | Lower or zero `pdf_running_header_min_fraction` |
| Number-soup stripper removes a real table | Manual reading | Table lines excluded from the heuristics | Content lost | `pdf_drop_number_soup=false` |

### Dates

| Scenario | Detection | Response | Operator action |
| --- | --- | --- | --- |
| Source has no date at all | `not doc.effective_start_date` | `undated` flag, WARNING, **still indexed** | Check the source exposes a date field; the document is invisible to date filters |
| New undeclared date-like field | `date_checks.undeclared_source_date_field` | Ignored (safe), reported per sweep | Classify it in `FIELD_KINDS` |
| Stated date not applied | `date_checks.stated_date_not_applied` | Reported | `scripts.backfill_bundle_dates` |
| Attachment date differs from its page's | `date_checks.attachment_date_adrift` | Reported | `scripts.backfill_bundle_dates` |
| Bundle has no declared date field | `date_checks.unmapped_bundle_dates` | `created` kept, reported | Declare it in `BUNDLE_DATE_FIELDS` |
| Provenance unrecorded | `date_checks.date_provenance_unrecorded` | Reported | `scripts.backfill_date_provenance` |
| Year precision, non-January value | `date_checks.year_precision_not_january` | Reported | Investigate — value and precision disagree |
| Implausible CMS value | `is_plausible` | Discarded, INFO log | Fix the CMS data |
| LLM unavailable | `interpret` returns `None` | `keep_page_date`, `rule="llm_unavailable"` | None; next re-index re-attempts |
| LLM proposes an ungrounded date | Ten gates in `safe_action` | Downgraded to `review` | Read `documents_date_decision` |
| Date-decision table unreachable | `except` in both recorders | One warning | None |

### Indexing and storage

| Scenario | Detection | Response | Data fate | Operator action |
| --- | --- | --- | --- | --- |
| Qdrant unreachable | Raise from `ensure_collection` / `upsert` | `error`, retry marker | Previous version intact | Restore Qdrant |
| Qdrant unreachable mid-upsert | Partial batches | The scoped delete never runs | Both versions present, both `is_current` | Next sweep collapses it; `duplicate_live_versions` reports it |
| Collection dimension mismatch | `_validate_dimension` | `VectorDimensionMismatch` raised — loud | Nothing written | Repoint `azure_openai_embedding_dimensions`, or use a new collection |
| Deployment repointed **in place** | **Not detectable** | Silent mix of two vector spaces | Corpus half-broken | Clear the collection and re-ingest |
| Embedding throttled (429) | Response hook | **Deployment-wide pause** + up to 8 SDK retries | — | Automatic; watch `embedding_http.throttled` |
| Embedding quota exhausted | Repeated `error` | Documents land in `documents_retry` | Retried next sweep | Raise quota, or cap the run |
| `chunk_text` index missing | **Nothing at ingest time** | The keyword retrieval leg silently does nothing | Retrieval degraded | `scripts.create_fulltext_index` |
| `keep_ids=[]` passed to delete | `ValueError` in `delete_document` | Raised at the boundary | Nothing deleted | Fix the caller |
| MySQL unreachable at run start | `state.ensure_table()` raises | Run fails | Nothing written | Restore MySQL |
| MySQL unreachable mid-run | Raise inside `_handle` | `error`, retry marker (also fails open) | Previous version intact | Next sweep |
| MySQL pool exhausted | `TimeoutError` after `mysql_pool_timeout` | Per-document `error` | — | Lower `ingest_workers` below `mysql_pool_size` |
| Duplicate facet under collation | Error 1062, **absorbed** by `_KEEP_FIRST` | Row skipped | Would otherwise have failed the whole document's transaction | None |
| Log write fails | `except` in `log.record` | `logger.exception` | The event is lost; `documents` is still correct | None |
| Orphan check fails | `except` | Warning; attachments left in place | Stale attachment survives | Next sweep, or a manual delete |

### Deletes

| Scenario | Detection | Response | Operator action |
| --- | --- | --- | --- |
| Live enumeration truncated | `_deletions_are_plausible` | **Bundle's deletes refused**, WARNING with counts and the setting to change | Investigate the source. Raise the ratio **only** if the drop is real |
| Live enumeration empty | Same rule | Never believed | Investigate |
| Enumeration request fails | `except` | Bundle's deletes skipped | None |
| Document moved bundle | `_safe_to_delete` | Spared, INFO log | None |
| Catalog read fails during the move check | `except` | **Spared** | None; costs one more sweep |
| Document unpublished at source | Absent from the live set | **Treated as deleted** | Republish; it returns as `NEW` on the very next run |
| A page drops a PDF | `_persist` link diff | Orphan collected if it was the last claim | None |

### Process and concurrency

| Scenario | Detection | Response | Data fate | Operator action |
| --- | --- | --- | --- | --- |
| Second run requested while one is active | Non-blocking lock | `IngestBusyError` → 409, or a logged sweep skip | — | None |
| Two ingestion **processes** | **Not detected** — the lock is process-local | Double embedding, raced writes | Corruption possible | Never run two; stop the sweep before a CLI corpus operation |
| Sweep overruns its interval | Next tick finds the lock held | Skipped | — | Longer interval, or cap the run |
| Process killed mid-run | — | See below | | |
| Ctrl-C during enrichment | `is_shutdown_error` | `aborted`, **no attempt consumed** | — | None |

#### The process dies mid-run

Nothing is lost, because of the swap ordering and because every write is idempotent:

- **Before the upsert** — nothing changed. Next sweep re-processes the document.
- **Between upsert and delete** — the collection holds both versions, both marked
  `is_current`. Search may return either; both are real content from the same
  document. Reconciliation reports `duplicate_live_versions`, and the next re-index
  collapses it.
- **Between delete and the catalog write** — the new points exist without a
  committed row. Reconciliation reports `points_without_catalog_row`. The next
  sweep sees no row (or a stale one), rebuilds, and the swap overwrites the same
  content-derived ids.
- **After the catalog write, before the log write** — the document is correct; only
  the audit line is missing.

The one thing to know: `doc_version` may skip a number, and the crawl's high-water
mark for that bundle may be slightly behind. Both are harmless.

---

## Retry markers, in operation

Full mechanics are in
[04, Retry markers](04-change-detection-and-versioning.md#retry-markers). The
operational summary:

- Written on `error` / `skipped`, with **why** in the `error` column.
- Cleared on `indexed` / `unchanged_content` / `deleted`, but only if the id was
  already pending — so a healthy sweep issues no `DELETE` per document.
- `floors()` gives the crawl the earliest unresolved position per bundle, widening
  the window until the failure is inside it.
- **No attempt cap.** A document that fails forever holds its bundle's floor down
  forever. The cost is a larger scan per run, not lost work.

### Triage

```sql
-- Group by cause, not by document — this is the query that turns a list of ids
-- into a diagnosis.
SELECT outcome, bundle, COUNT(*) n, MIN(first_seen) oldest, MAX(attempts) tries,
       LEFT(MIN(error), 160) example
FROM documents_retry
GROUP BY outcome, bundle
ORDER BY n DESC;

-- Documents stuck longest
SELECT document_id, bundle, outcome, attempts, first_seen, LEFT(error, 200)
FROM documents_retry ORDER BY first_seen ASC LIMIT 30;

-- How much of each bundle the widened window now covers
SELECT r.bundle,
       FROM_UNIXTIME(MIN(r.changed_mark))  AS window_reaches_back_to,
       FROM_UNIXTIME(MAX(d.changed_mark))  AS high_water_mark
FROM documents_retry r JOIN documents d ON d.bundle = r.bundle
WHERE r.changed_mark IS NOT NULL GROUP BY r.bundle;
```

If a document is genuinely unfixable — a source file that no longer exists and never
will — delete its retry row deliberately so it stops holding the floor down:

```sql
DELETE FROM documents_retry WHERE document_id = '...';
```

Do that knowingly. Deleting a row for a document that *could* be fixed makes it
unreachable again until its source is edited.

---

## Dead attachment links

`documents_dead_link` — attachments the site no longer serves.

The problem: old node body HTML links tender notices, RFQs and similar PDFs that were
taken down once they closed. The link stays in the text forever, so every sweep
harvests it, downloads it, and gets the same 404 — work that can never succeed and
that nothing in the catalog records, since a failed download produces no document row
and therefore no fingerprint to compare against next time.

**Recorded only for a client error**, where the server positively answered that the
file is not there. A timeout or a 5xx stays retryable, because those clear on their
own.

**Qualified by fingerprint, not permanent.** A marker suppresses the download only
while the attachment's fingerprint still matches the one that failed, so the retry
comes back exactly when something could have changed:

| Origin | Fingerprint | What revives it |
| --- | --- | --- |
| `attachment` | the node's `changed` | Re-upload the file and **save the node** |
| `inbody` | the URL-derived uuid | **Edit the link** — the corrected URL yields a *different* uuid, which is a row that was never marked dead |

A link nobody touches is never downloaded again.

`record()` counts another attempt when the same fingerprint fails again (the sweep
reached it before the marker existed, or the crawl chose to retry) and **restarts**
the count on a different fingerprint, since that describes a different state of the
source. The `ON DUPLICATE KEY` assignment order is load-bearing: `attempts` and
`first_seen` compare against the *stored* fingerprint, so both must be evaluated
before `fingerprint` is overwritten — MySQL applies these assignments left to right.

Loading the skip list fails open to an empty dict: without it the crawl re-downloads
a handful of dead URLs, which is exactly what it did before markers existed and no
reason to abandon a sweep over.

```sql
-- What is being suppressed
SELECT status, COUNT(*) FROM documents_dead_link GROUP BY 1;
SELECT document_id, status, attempts, first_seen, url
FROM documents_dead_link ORDER BY attempts DESC LIMIT 30;

-- Force a retry
DELETE FROM documents_dead_link WHERE document_id IN (...);
```

---

## Recovery: documents that failed before markers existed

`app/ingestion/recovery.py`, driven by `python -m scripts.recover_stranded`.

The retry marker landed **after** the corpus was built. Documents that errored or
were skipped before it existed left no trace at all: no catalog row (so they
contribute no `changed_mark`, and the incremental cursor sits above them), and no
retry row (so no floor pulls the window back). **The only evidence they ever existed
is the append-only `ingest_log`**, which nothing reads.

This module reads it, and reuses the existing floor machinery. It is **not a queue**:
it writes ordinary retry markers and the next ordinary sweep does the work.

### Finding them

```sql
-- The LAST thing the log said about each document
SELECT l.* FROM ingest_log l
JOIN (SELECT document_id, MAX(id) id FROM ingest_log GROUP BY document_id) last
  ON last.id = l.id
WHERE l.status IN ('skipped','error')
  AND no row in documents
  AND no row in documents_retry
```

An append-only log holds every attempt, and only the **final** one says whether the
document is still out. A document with a catalog row is not stranded whatever the log
says — it was indexed later, or is being retried already. A document with a retry
marker is likewise left alone; re-marking it would only reset its attempt count.

### Why the *parent* is marked, not the attachment

The obvious repair — a retry marker per stranded attachment id — is **wrong** for
in-body PDFs, which are 77 of the 91 stranded documents here. Their id is a hash of
the URL, and most were stranded precisely *because* that URL was malformed (an
undecoded `&amp;`, a whitespace-padded `href`). Once the extractor resolves those
correctly, the same link yields a **different id**, so a marker on the old id can
never resolve: it is never seen again, and its floor holds that bundle's window open
forever, scanning the whole bundle every sweep.

Marking the parent node has none of that. The parent's id is stable, the crawl
re-yields whatever attachments it currently links to — corrected URLs included — and
the marker clears the moment the parent re-ingests, **in the same run**. One marker
also covers every stranded attachment on that page: 91 attachments here resolve to
47 parents.

Where an attachment hangs off several pages, the **earliest** parent is chosen: its
position is furthest back, so the widened window covers the others too and one crawl
reaches every page that links the file.

### The report

```json
{"dry_run": true, "stranded": 91, "markers": 47, "recovering": 91,
 "unrecoverable": [{"document_id": "...", "reason": "no linking page and no bundle to crawl from", "url": "..."}],
 "unfloorable": ["..."]}
```

- **`unrecoverable`** — no linking page and no bundle to crawl from. Nothing can be
  done automatically.
- **`unfloorable`** — recorded anyway, because it makes the document visible for
  triage and it resolves if its source is crawled in full. It just cannot pull a
  window back, **and saying so is better than implying it will return.**

Idempotent in the way that matters: a document that already has a marker is not in
`stranded()`, so re-running neither duplicates markers nor resets an attempt count.
Nothing is deleted and no document id is invented — every marker names a document
the catalog already holds.

```bash
python -m scripts.recover_stranded --dry-run
python -m scripts.recover_stranded
```

---

## Recovery: rebuilding after a code change

`app/ingestion/reprocess.py`, driven by `python -m scripts.reprocess_corpus`.

The incremental crawl cannot do this on its own: a code change moves nothing in
Drupal, so a document last edited in 2018 stays outside every window forever, however
many chunker fixes land.

So the **selection comes from the catalog**: which documents are not on
`PIPELINE_VERSION`, and how far back the crawl would have to reach to include them.
That per-bundle floor is handed to the ordinary crawl as `extra_floors`, which
reaches them, and the ordinary pipeline rebuilds them — **no second ingestion path,
no re-implemented extraction, and every guard on the normal path still in force.**

### The census

```sql
SELECT bundle, COUNT(*) documents, MIN(changed_mark) floor,
       SUM(changed_mark IS NULL) without_position
FROM documents
WHERE pipeline_version IS NULL OR pipeline_version <> 'c1.i1.p1.e1'
GROUP BY bundle ORDER BY documents DESC
```

One grouped read rather than a scan: the question is per bundle, because the crawl
window is. A NULL version counts as stale — every row written before versions were
stamped has one, and those are precisely the documents this exists for.

`without_position` documents carry no `changed_mark` and cannot widen a window; they
are reached only if their bundle is crawled in full. The CLI reports the count so it
is not a surprise.

### Three properties that matter for a corpus-sized run

- **Resumable.** Progress lives in the catalog: a rebuilt document is stamped with
  the current version and leaves the stale set. **Interrupt at any point and re-run**
  — it recomputes what is left and carries on. Nothing is written to track a run.
- **Bounded.** `--limit` caps the documents processed, `--batch-size` / `--pause`
  throttle within a pass, and the existing budget only counts real work — the
  documents re-fetched inside the widened window that turn out to be current cost a
  fingerprint comparison and nothing else.
- **Non-destructive.** `reconcile_deletes` is **never** passed, so no crawl driven by
  this module can delete a document. Replacement is the ordinary swap.

### The pass loop

Each pass recomputes the census, widens the window to the oldest stale document per
bundle, and runs one ordinary ingestion. Passes repeat until nothing is stale, the
limit is spent, `max_passes` (50) is reached, or **a pass makes no progress**. That
last guard matters: a document that fails to rebuild stays stale, and without it the
loop would run forever re-attempting it. It logs:

> A pass rebuilt nothing while N document(s) remain stale. They are failing to
> rebuild rather than waiting their turn — check ingest_log and documents_retry for
> the reason.

`_limits` is a context manager that applies this invocation's batch controls to the
settings object and **puts them back** afterwards, so a long-lived process (or a
test) is not left with the deployment's configuration edited behind it.

```bash
python -m scripts.reprocess_corpus --dry-run        # census + window only
python -m scripts.reprocess_corpus --limit 200      # a cautious first pass
python -m scripts.reprocess_corpus --bundle news    # one bundle
python -m scripts.reprocess_corpus                  # everything, in passes
```

`--dry-run` prints the census and the window it would ask for and returns before any
ingestion. It does call `state.ensure_table()` — the question cannot be asked before
the column exists — which adds a nullable column and an index and changes no row, so
a dry run is still a dry run.

---

## Recovery: single documents

```bash
curl -X POST /reindex -d '{"document_id": "..."}'          # queue one document
```

Writes a retry marker with `outcome="reindex"` and clears the change markers.
**Deletes nothing.** See
[03, POST /reindex](03-triggers-and-control-plane.md#3-post-reindex) for why this
replaced an operation that used to delete the catalog row and make the document
permanently unreachable.

Equivalent by hand, when you have SQL access and no HTTP:

```sql
UPDATE documents SET fingerprint = '', content_hash = '', updated_at = NOW()
WHERE document_id = '...';                       -- clear_change_markers
INSERT INTO documents_retry (document_id, source_type, bundle, changed_mark,
                             outcome, attempts, error, first_seen, updated_at)
SELECT document_id, source_type, bundle, changed_mark, 'reindex', 1,
       'manual', NOW(), NOW() FROM documents WHERE document_id = '...'
ON DUPLICATE KEY UPDATE attempts = attempts + 1, updated_at = NOW();
```

Note `changed_mark` is **not** cleared: it is the document's position in the crawl,
and the retry marker needs it to pull the window back far enough to reach the
document at all.

---

## Recovery: backfilling the catalog from the vector store

`python -m app.ingestion.backfill` reconstructs document-level facets —
`effective_start_date`, `authors`, `categories`, `title`, `source_url` — by scrolling the
collection and aggregating chunk payloads per `document_id` (first-seen date, unioned
author/category values).

This is a repair for a catalog that lost rows or columns while the collection is
intact. **Use it deliberately**: it lifts `effective_start_date` out of chunk payloads, which
can overwrite a value the date resolver decided. Reconciliation's
`stated_date_not_applied` check names this module explicitly as a cause, and the fix
is to re-run `scripts.backfill_bundle_dates` afterwards.

---

## Replay and reprocessing: which tool for which problem

| Problem | Tool | Deletes anything? |
| --- | --- | --- |
| One document is wrong or stale | `POST /reindex {"document_id": ...}` | No |
| A code change needs to reach the corpus | `scripts.reprocess_corpus` | No |
| Documents failed before retry markers existed | `scripts.recover_stranded` | No |
| A dead PDF came back | `DELETE FROM documents_dead_link WHERE ...` | No |
| Catalog rows lost, collection intact | `app.ingestion.backfill` | No |
| Abstracts missing on documents that never change | `app.ingestion.enrich_backfill` | No |
| Dates need re-deriving after a mapping change | `scripts.backfill_bundle_dates`, `scripts.backfill_date_provenance` | No |
| Knowledge stage did not land | catch-up sweep, `scripts.knowledge_document`, `scripts.build_knowledge` | No |
| Graph is behind | `scripts.project_graph [--rebuild]` | Graph only, which is derived |
| Legacy table names | `scripts.rename_catalog_tables` | No (renames) |
| `source_type` still `article` | `scripts.migrate_source_type_website` | No |
| Embedding model genuinely changed in place | **Clear the collection and re-ingest** | Yes — the only such operation |

**Nothing in this list except the last deletes content.** That is deliberate: every
repair is expressed as "state a fact and let the ordinary pipeline act on it".

---

## Detection: what notices a problem, and when

| Detector | Cadence | Catches |
| --- | --- | --- |
| Run tally (`error`, `skipped`, `undated`, `budget_stop`) | per run | Immediate failures |
| `ingest_throughput` log line | per run | Throughput collapse, error rate, enrichment failures, undated count |
| `documents_retry` depth and age | continuous | Documents that keep failing |
| `documents_dead_link` | continuous | Permanently gone attachments |
| `documents_date_decision` where `action='needs_manual_review'` | continuous | Dates a person must settle |
| `documents_knowledge_run` where `status IN ('failed','partial')` | continuous | Knowledge-stage failures |
| **Cross-store reconciliation** | per sweep | Silent drift — the class of problem nothing else sees |
| `GET /ready` | probe cadence | MySQL / Qdrant unreachable |
| `GET /metrics` | scrape cadence | Last reconciliation, store reachability, knowledge health |
| `GET /metrics/timings` | scrape cadence | Stage latency, throttle counts |

Reconciliation exists because the test suite was green, `/ready` was green,
`/metrics` was green, and the catalog said every document was indexed **while 85 of
them had no retrievable content at all**. See
[11](11-observability-and-monitoring.md#cross-store-reconciliation).

---

## Configuration

| Setting | Default | Effect on failure behaviour |
| --- | --- | --- |
| `drupal_max_retries` | `3` | Transport retries for 429/5xx. |
| `drupal_request_timeout` | `60` | When a slow source becomes a skip. |
| `azure_openai_embedding_max_retries` | `8` | How long a throttled document holds on before erroring. |
| `azure_openai_embedding_max_throttle_seconds` | `60.0` | Ceiling on one throttle pause. |
| `enrichment_max_attempts` | `3` | Failures before a document is left un-enriched. |
| `knowledge_stage_max_attempts` | `3` | Retries before catch-up leaves a document alone. |
| `ingest_reconcile_max_missing_ratio` | `0.10` | How much of a bundle one run may delete. |
| `ingest_reconcile_min_deletions` | `2` | Absolute allowance below that ratio. |
| `ingest_max_docs_per_run` | `0` | Bounds the damage of a bad run; makes recovery incremental. |
| `verify_corpus_after_sweep` | `true` | Whether drift is detected at all. |
| `ingest_log_retention_days` | `90` | How far back `recover_stranded` can see. **Lowering this discards recovery evidence.** |

---

Previous: [09 — The Knowledge Layer and Graph](09-knowledge-layer-and-graph.md) · Next: [11 — Observability, Monitoring and Alerting](11-observability-and-monitoring.md)
