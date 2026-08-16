# End-to-End Ingestion Pipeline Audit

**Date:** 2026-08-16
**Scope:** Source → Ingestion → Extraction → Chunking → Embedding → MySQL → Graph → Qdrant → Retrieval
**Method:** Live testing against the running production stores (MySQL `arc_db`, Qdrant `documents` @ 149,488 points, Neo4j), live Drupal source crawl, controlled failure injection, and full source review.

**VERDICT: FAIL — not production-ready.**

Three Critical defects cause silent, unrecoverable data loss. The corpus is currently
serving 85 documents that the catalog reports as successfully indexed but which have zero
retrievable content, and 99% of stored chunks were produced by a chunker that has since
been fixed four times over with no way to re-apply those fixes.

---

## 1. Actual End-to-End Architecture (as discovered)

The system is **two FastAPI applications** over **three stores**. There is no queue, no
message broker, no object storage, and no Celery — despite comments referencing a "celery
mode".

```
                  ┌──────────────────────── SOURCE ────────────────────────┐
                  │  Drupal JSON:API  https://teriin.org/jsonapi           │
                  │  node/{bundle} (18 bundles) + block_content/basic      │
                  │  + attached PDFs (file--file rels) + in-body PDF hrefs │
                  └───────────────────────────┬───────────────────────────┘
                                              │
   ENTRY POINTS                               ▼
   ├─ app/ingest_main.py (uvicorn :8001)  ── lifespan → scheduler._sweep_loop
   │    every worker_sweep_interval_seconds (3600), first run immediate
   ├─ POST /ingest/run      ── ad-hoc crawl        ⚠ NO AUTH
   ├─ POST /ingest/article  ── direct doc insert   ⚠ NO AUTH
   ├─ POST /reindex         ── DESTRUCTIVE         ⚠ NO AUTH
   └─ python -m app.ingestion.pipeline  (CLI)
                                              │
                                              ▼
   CHANGE DETECTION   app/ingestion/change_detection/drupal.py
     • prior state = state.load("article") + state.load("website")
     • high-water mark = MAX(changed_mark) per bundle, filter[changed] >= high
     • floored at earliest unresolved documents_retry row
     • blocks: full fetch (no incremental), <200 chars skipped as chrome
     • dead-link markers suppress known-404 attachments
     • optional delete reconciliation w/ completeness guard (10% / 2 docs)
                                              │
                                              ▼
   ORCHESTRATION      app/ingestion/pipeline.py :: _run / _handle
     • ONE run at a time (process-local threading.Lock)
     • ingest_workers=4 ThreadPoolExecutor; crawler stays single-threaded
     • per-doc: build → content_hash → enrich → chunk → embed → upsert
                → delete-old → persist → log
                                              │
        ┌─────────────────────┬───────────────┴────────┬──────────────────┐
        ▼                     ▼                        ▼                  ▼
   EXTRACTION            CHUNKING                 EMBEDDING          CATALOG
   drupal_extractor      chunking/               Azure OpenAI        MySQL arc_db
   attachment.py         segmenter→packer        text-embedding-     20 tables
   pdf_extractor         →classifier             3-large @ 3072      documents (11,368)
    ├ pymupdf_local      parent/child            batch 128           + 7 facet tables
    ├ camelot_tables     uuid5 chunk ids         reuse keyed on      + ingest_log (17,361)
    └ Azure DocIntel     breadcrumb embed        embed_hash+model    + retry/dead_link
   text_normalize        parents=zero vectors                        + enrichment/date
                                              │
                                              ▼
                                      QDRANT `documents`
                                      149,488 points (3072-d, Cosine)
                                      121,788 children + 27,700 parents
                                      10 payload indexes
                                              │
        ┌─────────────────────────────────────┴──────────────────────────┐
        ▼                                                                ▼
   RETRIEVAL (app/main.py :8000)                          NEO4J (OUT OF BAND)
   /chat /search — auth-gated                             ⚠ NOT written by ingestion
   hybrid_search (is_parent=False filter)                 only scripts/project_graph.py
   → reranker → context_builder → answerer                1,256 Docs / 2,710 Entities
   + semantic cache (Qdrant collection)                   / 1,653 Claims / 4,228 Aliases
```

### Undocumented / implicit stages found
- **Enrichment** (`enrich.py`) — an LLM abstract per content hash, cached in
  `documents_enrichment`; enabled in this deployment (`ENRICHMENT_ENABLED=true`).
- **Date resolution** (`date_resolution.py`) — evidence-based publication-date inference
  for PDFs; writes `documents_date_decision` (3,761 rows) as a review queue.
- **Attachment orphan collection** — a PDF is deleted when its *last* parent page drops it.
- **Dead-link markers** — 4xx attachments suppressed from future crawls.
- **Bundle-move protection** — a delete candidate found under a new bundle is spared.
- **Title-only refresh** — `refresh_document_title` rewrites payload titles without re-embedding.

---

## 2. Stage-by-Stage Test Results

| Stage | Result | Notes |
|---|---|---|
| Source reachability | **PASS** | JSON:API 200; 246 records from a full default crawl |
| Change detection (idempotency) | **PASS (now)** | 213 unchanged / 26 new / 7 changed; block re-crawl 123/123 unchanged |
| Extraction — text/metadata | **PASS** | content_hash reproduced exactly from live source |
| Extraction — attached PDF URLs | **FAIL** | F4, F5 — HTML entities and whitespace corrupt URLs |
| Extraction — empty body | **FAIL** | F1 — produces a "successful" wipe |
| Chunking — determinism | **PASS** | uuid5 over owned content; stable for identical input |
| Chunking — id stability across versions | **FAIL** | F3 — scheme changed; 0% overlap with stored ids |
| Embedding — dimensions/model | **PASS** | 3072-d verified on live points |
| Embedding — vector reuse | **FAIL** | F3 — 1,214 of 121,788 children carry `embed_model` |
| MySQL — referential integrity | **PASS** | 0 orphan rows across all 4 FK'd facet tables |
| MySQL — uniqueness | **PARTIAL** | F11 — 144 duplicate `documents_tag` rows |
| Qdrant — orphan vectors | **PASS** | 0 points without a MySQL row |
| Qdrant — version consistency | **PASS** | 0 doc_version mismatches; 0 docs with 2 live versions |
| Qdrant — parent/child integrity | **PASS** | 0 children pointing at a missing parent; 0 id/payload mismatches |
| Qdrant — coverage | **FAIL** | F1 — 85 catalogued documents have zero points |
| Graph — internal consistency | **PASS** | claims/entities/aliases all resolve; 0 stale nodes |
| Graph — pipeline integration | **FAIL** | F9 — not written by ingestion at all |
| Retrieval — self-retrieval | **PASS** | target document ranked #1 at 0.8386, correct `source_url` |
| Retrieval — parent leakage | **PASS** | zero-vectors score 0.0 and are filtered by `is_parent=False` |

---

## 3. Cross-System Reconciliation Results

Full scroll of all 149,488 Qdrant points against MySQL and Neo4j:

```
Qdrant points                       149,488   (121,788 children + 27,700 parents)
Qdrant distinct document_id          11,283
MySQL documents                      11,368
Neo4j Document nodes                  1,256

A. In MySQL, no vectors in Qdrant        85   ← F1  (all have indexed_at set)
B. In Qdrant, no MySQL row                0   ✓ delete path is clean
C. doc_version mismatch MySQL↔Qdrant      0   ✓
D. Documents with >1 live version         0   ✓
E. Children carrying embed_model      1,214 / 121,788  ← F3
F. Children with a dangling parent        0   ✓
G. payload.chunk_id != point id           0   ✓
H. Points missing published_at        1,522   ← F12
I. is_current=False                       0   ← F15 (vestigial)

MySQL entities 3,513 → Neo4j 2,710   (803 are claim_eligible=0, by design ✓)
MySQL claims   1,653 → Neo4j 1,653   ✓ exact
MySQL docs    11,368 → Neo4j 1,256   ← F9 (10,112 absent)
Neo4j Documents with no vectors          61   ← F1 overlap
```

**Reconciliation does not balance.** `Source ≠ MySQL ≠ Qdrant` at the document level.

---

## 4. Findings

### F1 — CRITICAL — An empty extraction deletes the document's vectors and reports success

| | |
|---|---|
| **Stage** | Orchestration / Vector store |
| **Location** | `app/ingestion/pipeline.py:336-339`, `app/core/clients/vector_store.py:108` |
| **Expected** | A document that extracts to nothing is treated as a failure; existing vectors are left intact. |
| **Actual** | Chunking returns `[]`; `index_chunks([])` returns 0 without touching Qdrant; `delete_document(doc_id, keep_ids=[])` is then called — and **`[]` is falsy**, so `must_not` becomes `None` and the filter deletes *every* point for that document. `_persist(..., indexed=True)` stamps `indexed_at`, and the run logs `status="indexed"`. |

**Root cause** — two independent defects compounding:
```python
# pipeline.py:337-339
chunks = index_chunks(new_chunks)                                    # 0, no-op
delete_document(record.document_id, keep_ids=[c.chunk_id for c in new_chunks])
_persist(record, doc, content_hash, version, indexed=True, ...)      # claims success

# vector_store.py:108
must_not=[HasIdCondition(has_id=list(keep_ids))] if keep_ids else None
#                                                    ^^^^^^^^ [] is falsy → spare nothing
```

**Evidence (live reproduction against a scratch Qdrant collection):**
```
PASS 1  chunks=1 indexed=1 points_in_qdrant=1
PASS 2  chunks=0 indexed=0 points_in_qdrant=0
        content_hash=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  vectors before empty re-ingest : 1
  vectors after  empty re-ingest : 0
  pipeline outcome it would log  : 'indexed' (chunks_indexed=0)
  VERDICT: DATA LOSS CONFIRMED
```

**Evidence (production):** 85 documents have `indexed_at` set and zero Qdrant points.
78 carry `content_hash = e3b0c442…b855`, which is SHA-256 of the empty string.
All 85 have `status='indexed'`, `chunks_indexed=0` in `ingest_log`.

The other 7 have real content and were lost to the pre-2026-08-11 heading-classification
bug (`8cf7f56 fix: emit heading-only sections instead of skipping them during packing`).
Example: `Corporate GHG acounting`, body `"DRL Corporate GHG accounting"` — chunks to 1
today, chunked to 0 on 2026-08-02. **It has never healed**, because its `content_hash` is
unchanged, so `content_changed()` returns False forever.

**Impact** — Silent corpus loss with a false success signal. Any Drupal editor who blanks a
body, any PDF whose text layer becomes unreadable, and any extractor regression removes
content from search while every dashboard reports a healthy ingest.

**Affected systems** — Qdrant (data loss), MySQL (false `indexed_at`), `ingest_log` (false status), retrieval (missing answers), Neo4j (61 documents reference content that cannot be retrieved).

**Reproduction**
1. Ingest a document with a real body.
2. Blank the body at source (or stub the extractor to return `""`).
3. Re-run ingestion for that document.
4. Observe zero points remain and the run logs `indexed`.

**Recommended fix**
1. Guard the swap — never delete when nothing replaced it:
   ```python
   if not new_chunks:
       logger.error("%s extracted to no chunks; keeping the previous version.",
                    record.document_id)
       _log(run_id, record, "error", doc=doc, error="extraction produced no chunks")
       return "error"          # lands in _UNRESOLVED_OUTCOMES → retry marker written
   ```
2. Make `delete_document` fail safe regardless of caller:
   ```python
   must_not=[HasIdCondition(has_id=list(keep_ids))] if keep_ids is not None else None
   ```
   and reject `keep_ids=[]` explicitly, since "spare nothing" is never what a swap wants.

**Validation after fix**
- Unit: empty-body document → outcome `error`, `delete_document` not called, retry row written.
- Unit: `delete_document(id, keep_ids=[])` raises rather than wiping.
- Integration: the reproduction above leaves `points_in_qdrant == 1`.
- Backfill: clear `content_hash` for the 85 affected ids and re-ingest.

---

### F2 — CRITICAL — `/reindex` permanently deletes 99.8% of documents instead of reindexing

| | |
|---|---|
| **Stage** | Control plane / Change detection |
| **Location** | `app/workers/tasks.py:25-32`, `app/api/ingest.py:79-92` |
| **Expected** | "Reindex" clears state so the next crawl rebuilds the document. |
| **Actual** | It deletes the vectors **and** the catalog row. The crawl window is `filter[changed] >= MAX(changed_mark)` per bundle, so a document whose `changed` predates its bundle's high-water mark is never fetched again. No retry marker is written, so no floor pulls the window back. |

```python
def reindex_document(document_id, source_type="website"):
    delete_document(document_id)          # all points gone
    removed = state.delete([document_id]) # catalog row gone → no changed_mark, no floor
    return {"document_id": ..., "manifest_rows_removed": removed}
```
The API returns `status="reset"`, implying recoverability.

**Evidence:**
```
Target document      : dc00358c-0510-475d-a00f-026f5fa3194d
  its changed_mark   : 1515666501  (2018-01-11)
  bundle high-water after its row is deleted: 1783506143 (2026-07-08)
  crawl filter is changed >= high-water
  -> would this doc be re-fetched after /reindex? False

COUNT of website docs that would be UNRECOVERABLE if /reindex were called on them:
   8176 of 8193
```
Corroborated by the live crawl: a full default sweep returns **246 records** against 11,368
catalogued documents — the other ~11,100 are outside the incremental window.

**Impact** — Irreversible loss of any document targeted by the operation most likely to be
used to *repair* a document. Combined with F7 (no auth) this is remotely triggerable.

**Recommended fix** — Do not delete the row. Reset the fingerprint and record a retry
marker so the floor pulls the crawl window back:
```python
def reindex_document(document_id, source_type="website"):
    prior = state.get(document_id)
    if prior is None:
        return {"document_id": document_id, "status": "unknown"}
    retries.record(document_id, source_type=prior.source_type, bundle=prior.bundle,
                   changed_mark=prior.changed_mark, outcome="reindex_requested")
    state.clear_content_hash(document_id)   # forces content_changed → True
    return {"document_id": document_id, "status": "queued"}
```
Delete the vectors only once the replacement has been indexed — which `_handle` already does.

**Validation** — Reindex a document whose `changed_mark` is the bundle minimum; assert the
next sweep re-fetches and re-indexes it.

---

### F3 — CRITICAL — No corpus re-index mechanism; every extraction/chunking/embedding fix is unreachable for existing data

| | |
|---|---|
| **Stage** | Systemic |
| **Expected** | A chunker or payload-schema change can be rolled out across the corpus. |
| **Actual** | Re-indexing is gated on `content_hash` (body text only) and on the incremental crawl window. Neither moves when *code* changes, so a document is pinned to whatever the chunker did the day it was first seen. |

**Evidence — the corpus was built 2026-08-02/03; correctness fixes landed after:**

| Commit | Date | Effect on stored data |
|---|---|---|
| `a25ea31` reject URLs and list markers as headings | 08-11 | never applied |
| `fad09b1` keep heading-classified lines as content | 08-11 | never applied |
| `b9335ec` require body content after a capitalisation-only heading | 08-11 | never applied |
| `8cf7f56` emit heading-only sections instead of skipping | 08-11 | never applied — **caused 7 of the 85 empty documents** |
| `b38220a` derive chunk ids from owned content | 08-12 | ids diverged corpus-wide |
| `d536b1d` key vector reuse on embedded text | 08-12 | reuse never fires |
| `98fb5f8` stop storing table markdown | 08-12 | 37,178 points still carry it |
| `a97a2ca` stop storing taxonomy term uuids | 08-12 | 123,339 still carry `term_ids` |
| `ba31605` stop storing tenant and acl | 08-12 | 147,996 still carry `acl`/`tenant_id` |

**Stale payload census (live Qdrant, 149,488 points):**
```
  acl             present: 147,996   (field removed from code)
  tenant_id       present: 147,996   (field removed from code)
  term_ids        present: 123,339   (field removed from code)
  theme_ids       present: 101,362   (field removed from code)
  table_markdown  present:  37,178   (field removed from code)
  embed_model     present:   1,214 / 121,788 children
  embed_hash      present:   1,214 / 121,788 children
```

**Chunk-id divergence, measured on a real document:**
```
CHUNK ID STABILITY  stored=1 recomputed=1 overlap=0
   !! stored-only=1 recomputed-only=1
```
Because `_reusable_vectors` looks up stored vectors **by chunk id**, and every id changed,
vector reuse can never hit. Every future re-index re-embeds the entire document at full
Azure cost — the optimisation is dead corpus-wide.

**Impact** — Correctness fixes do not reach production data; ~99% of the served corpus was
produced by a chunker with four known, fixed defects; embedding spend is permanently
inflated; payloads carry ~4 dead fields.

**Recommended fix**
1. Stamp a `pipeline_version` (chunker + payload schema) into the catalog row and the payload.
2. Extend the re-index test: `content_changed(...) or row.pipeline_version != CURRENT`.
3. Add `scripts/reindex_corpus.py --since-version` that walks the catalog (not the
   incremental crawl window) in batches, honouring `ingest_batch_size`/`pause`.
4. Run it once to normalise the corpus; verify `acl`/`term_ids`/`table_markdown` reach 0
   and `embed_model` reaches 121,788.

---

### F4 — HIGH — HTML entities are not decoded in in-body PDF URLs, guaranteeing 404

| | |
|---|---|
| **Stage** | Extraction |
| **Location** | `app/ingestion/extractors/drupal_extractor.py:75` (`_HREF_PDF_RE`), used at line 468 |
| **Expected** | `href="…/Receipts_&amp;_Payments.pdf"` yields `…/Receipts_&_Payments.pdf`. |
| **Actual** | The regex lifts the raw attribute value; `html.unescape` is never called anywhere in the module. The literal `&amp;` is kept, and the download 404s. |

**Evidence:**
```
as-extracted (&amp;) -> 404   decoded (&) -> 200  ctype=application/pdf
as-extracted (&amp;) -> 404   decoded (&) -> 200  ctype=application/pdf

_extract_inbody_pdfs extracted url =
  https://teriin.org/sites/default/files/files/Receipts_&amp;_Payments_22_23.pdf
expected =
  https://teriin.org/sites/default/files/files/Receipts_&_Payments_22_23.pdf
```
15 attachment link rows and 15 distinct skipped documents carry `&amp;`.

**Impact** — Every PDF whose filename contains `&` is permanently missing from the corpus
(FCRA receipts, TERI-CBS activity reports observed).

**Fix** — `raw = html.unescape(raw).strip()` before the `.pdf` test in `_extract_inbody_pdfs`.
**Validation** — Unit test on the entity fixture; re-crawl and assert the 15 ingest.

---

### F5 — HIGH — A whitespace-padded href produces a duplicate, permanently-404 document

| | |
|---|---|
| **Stage** | Extraction |
| **Location** | `app/ingestion/extractors/drupal_extractor.py:~471` |
| **Actual** | `raw.lower().startswith("http")` is False for `" https://…"`, so the absolute URL is treated as relative and concatenated onto the site base. `_BARE_PDF_RE` *also* matches the same link correctly, so **two** `DrupalFile`s are emitted with different synthetic uuids — one valid, one that always 404s. |

**Evidence:**
```
BUG 2 (whitespace in href):
   extracted url = 'https://www.ceew.in/sites/default/files/future.pdf'
   extracted url = 'https://teriin.org/ https://www.ceew.in/sites/default/files/future.pdf'
```
Live sample from `ingest_log`: `https://teriin.org/ https://www.ceew.in/sites/default/files/future.pdf` → 404.
57 attachment link rows contain a space.

**Impact** — Duplicate document identities, guaranteed-failing downloads, inflated skip counts.
**Fix** — `raw = html.unescape(raw).strip()` (same one-line fix as F4) and dedupe on the
normalised absolute URL before constructing the uuid.

---

### F6 — HIGH — 91 failed attachments are permanently stranded

| | |
|---|---|
| **Stage** | Retry / Change detection |
| **Expected** | A document that fails is retried. |
| **Actual** | 91 distinct attachments were skipped during the 2026-08-02→09 runs. The retry-marker feature (`a6fecda`) landed 2026-08-12, so nothing was recorded. They have **no catalog row**, so they contribute no `changed_mark`, and their parent nodes have since fallen below the bundle high-water mark. |

**Evidence:**
```
skipped docs: 91  with catalog row: 0  STRANDED: 91
error   docs: 16  with catalog row: 15  STRANDED: 1
documents_retry rows: ()          ← empty
documents_dead_link rows: 2       ← only the two 404s recorded post-08-12
live status of first 25 skipped URLs: {404: 23, ConnectTimeout: 2}
```
23 of 25 are 404s caused by F4/F5; the 2 timeouts (`cbs.teriin.org`) are a genuinely
unreachable host.

**Impact** — Permanent, invisible corpus gaps. Nothing surfaces them.
**Fix** — Backfill `documents_retry` from `ingest_log` where the latest status is
`error`/`skipped` and no catalog row exists; then let the existing floor logic recover them.
**Validation** — After backfill, assert `retries.floors()` pulls each affected bundle's
window back and the next sweep re-attempts all 91.

---

### F7 — HIGH — The ingestion control plane is completely unauthenticated

| | |
|---|---|
| **Stage** | API / Security |
| **Location** | `app/api/ingest.py` (no `Depends`), `app/app_factory.py:48-58` |
| **Actual** | `require_principal` is applied only in `app/api/chat.py:86` and `app/api/search.py:16`. Every ingestion route is open **even when `auth_enabled=True`**, including the destructive `/reindex` (see F2). CORS is `allow_origins=["*"]`. |

Exposed without credentials: `POST /ingest/run` (corpus-wide crawl — resource exhaustion),
`POST /ingest/article` (inject arbitrary content into the answer corpus — retrieval
poisoning), `POST /reindex` (irreversible deletion), `GET /ingest/log` (leaks internal ids,
titles, URLs, error strings).

**Fix** — Add `dependencies=[Depends(require_principal)]` to the ingest router, gate
mutating routes on an admin group, and bind the ingestion server to loopback / a private
network. Pin `CORS_ALLOW_ORIGINS`.

---

### F8 — HIGH — The scheduled sweep never reconciles deletes

`worker_sweep_reconcile` defaults to `False` and is not set in `.env`, so
`sweep()` calls `ingest_drupal(reconcile=False)`. Documents deleted or unpublished at source
are never removed. The reconciliation logic, its completeness guard, and the bundle-move
protection are all well-built and effectively **dead code in this deployment**.

**Evidence** — 0 `deleted` events in the entire 17,361-row `ingest_log`.
**Fix** — Enable `WORKER_SWEEP_RECONCILE=true` after one `--dry-run-reconcile` review.

---

### F9 — MEDIUM — The knowledge graph is not part of the pipeline

Nothing in `app/ingestion/`, `app/workers/`, or `app/api/ingest.py` writes Neo4j; only
`scripts/project_graph.py`, run by hand (last: `graph-project-v1:20260814T065651`).

```
DOCUMENTS mysql=11,368  neo4j=1,256   in_mysql_not_graph=10,112  stale_in_graph=0
CLAIMS    mysql= 1,653  neo4j=1,653   ✓ exact
ENTITIES  mysql= 3,513  neo4j=2,710   (803 claim_eligible=0, by design)
Neo4j Documents with no Qdrant vectors: 61
```
Drift is monotonic: new documents never appear, deleted ones would never leave.
Additionally **0 of 1,653 assertions carry a `chunk_id`** — all provenance is `cms_field`
and document-level. The `Chunk` label, its uniqueness constraint and the `chunk_document`
index exist but hold **0 nodes**; `claim_extraction_enabled=False` has never been on.

**Fix** — Either project incrementally at the end of each sweep, or schedule the projection
and add its freshness to `/metrics`. Document that chunk-level provenance is unimplemented.

---

### F10 — MEDIUM — No cross-store reconciliation, and readiness does not check MySQL

- No script compares MySQL ↔ Qdrant ↔ Neo4j. `scripts/verify_catalog_counts.py` validates
  catalog readers against independent SQL — MySQL-internal only.
- `/ready` (`app/api/health.py:85`) checks **only Qdrant**. MySQL — the system of record —
  is never probed, so the ingestion server reports ready while the catalog is unreachable.
- `/metrics` reports point counts and tuning values, not ingestion health. There is no
  counter for "documents that indexed 0 chunks", no error-rate alarm, no coverage check.
- `app/observability/metrics.py` is in-memory and per-process, reset on restart;
  `otel_enabled=False`, so nothing is exported.

This is why F1 sat undetected across 85 documents and why 12 consecutive runs on 2026-08-16
re-indexed the identical 108 documents (`documents_retry` empty, no warning emitted).

**Fix** — Ship the reconciliation used in this audit as `scripts/verify_corpus.py`, run it
after each sweep, fail the run on a non-zero A/B/C/D count, and add MySQL to `/ready`.

---

### F11 — MEDIUM — Duplicate tag rows from truncate-after-dedup

`app/catalog/state.py:57` de-duplicates on the **full** value and truncates afterwards:
```python
rows = [(document_id, v[:255]) for v in dict.fromkeys(x for x in values if x)]
```
Two tags sharing their first 255 characters become two identical rows. `documents_tag` has
no unique constraint (only `KEY idx_doc`, `KEY idx_val`), so nothing rejects them.
**Evidence:** 144 duplicate `(document_id, tag)` pairs. `documents_theme` is safe — it has
PK `(document_id, theme)`.
**Fix** — Truncate before de-duplicating, and add `UNIQUE(document_id, tag)`.

---

### F12 — MEDIUM — 1,522 points and 109 documents have no `published_at`

The `published_at` payload index covers 147,966 of 149,488 points. Recency tie-breaking
(`rerank_relevance_tolerance`) and every date range filter silently exclude the remainder —
they are not ranked down, they are invisible to date-filtered queries.
**Fix** — Backfill from `documents.published_at` / the Drupal `created` field; alert when a
document indexes without a date.

---

### F13 — LOW — Retry markers never record why a document failed

`app/ingestion/pipeline.py:368-374` calls `retries.record(...)` without `error=`, although
the parameter and the `error TEXT` column both exist. Every row's `error` is NULL, so the
retry queue cannot be triaged.
**Fix** — Thread the exception text through `_track_retry`.

---

### F14 — LOW — Configuration and deployment drift

- `NEO4J_PASSWORD` is **absent** from `.env`; the credential survives only inside a comment
  (`.env:55`). `get_settings().neo4j_password` is `""`, so the app cannot open the graph it
  is configured to use.
- `docker-compose.yml` deliberately pins `neo4j:2026.07.1-community` and explains why; the
  **running container is `neo4j:latest`**, started by hand. The pin is not in force.
- `knowledge_enabled=False` while `graph_routing_enabled=True` — the kill-switch reads as ON
  while the layer it gates is off.
- `.env:48` is `keyword_leg_enabled =true` (stray space); it happens to parse, but the file
  is inconsistent with every other key.
- `.env` is correctly gitignored and has never been committed. **No secret leak found.**

---

### F15 — LOW — `is_current` is vestigial

0 of 149,488 points have `is_current=False`, and nothing ever writes it False. The field is
indexed and filtered on, implying a soft-versioning scheme that does not exist. Either
implement it or drop it.

---

### F16 — LOW — `ensure_collection` creates only one of ten payload indexes

`app/core/clients/vector_store.py:31-48` ensures the collection and the `published_at`
datetime index. `_ensure_keyword_index` is **defined but never called**. The other nine
indexes exist only because `scripts/create_payload_indexes.py` and
`scripts/create_fulltext_index.py` were run by hand. A fresh deployment silently starts with
degraded filtering and no keyword leg. It also never validates that an **existing**
collection's dimension matches the configured embedding size.

---

## 5. Failure & Recovery Test Results

| Injected failure | Behaviour | Verdict |
|---|---|---|
| Extraction returns empty | Vectors deleted, logged `indexed` | **FAIL (F1)** |
| Attachment download 4xx | `None` → `skipped`, dead-link marker, suppressed next run | PASS |
| Attachment download timeout | `None` → `skipped`, no marker, retried while parent in window | PARTIAL (F6) |
| Drupal bundle fetch raises | Bundle skipped, run continues, other bundles unaffected | PASS |
| Per-document exception | Caught in `handle()`, logged `error`, retry marker written | PASS |
| Catalog write unreachable | Fails open with a warning across enrichment/retry/dead-link/date paths | PASS (by design) |
| Mid-index crash | New ids upserted first, delete last → old version stays searchable | PASS |
| Concurrent runs | `threading.Lock` → `IngestBusyError` → HTTP 409 | PASS (single process only) |
| Reconcile on a short enumeration | Refused by the 10% / 2-document completeness guard | PASS |
| Bundle move mistaken for deletion | Spared by `_safe_to_delete` re-read | PASS |
| `/reindex` on an old document | Permanent deletion | **FAIL (F2)** |

The index-then-delete swap ordering is genuinely well designed and holds under
interruption. The failure-handling weaknesses are all at the **boundaries** — empty results,
and operations that bypass the swap.

---

## 6. Performance, Concurrency & Scalability

- **Throughput** (measured from `ingest_log`): ~108 documents in ~3.5 min ≈ **31 docs/min**
  at `ingest_workers=4`.
- **Vector reuse is 100% dead** (F3) — every re-index re-embeds. This is the single largest
  avoidable cost.
- **`mysql_pool_size=5` vs `ingest_workers=4`** — within the documented rule (workers <
  pool), but leaves exactly one connection for the API. `/ingest/log` under a running sweep
  can wait up to `mysql_pool_timeout=30s`. No nested checkouts found, so no deadlock risk.
- **The `keep_ids` filter is unbounded** — a large PDF sends every chunk id in a
  `must_not: HasIdCondition`. Fine at observed sizes (max ~500), but it scales with document
  length and has no cap.
- **27,700 parent points (18.5%) carry 3072-d zero vectors** — ~340 MB of index storage for
  vectors that are never searched. A deliberate trade-off, but a named-vector or separate
  collection would reclaim it.
- **Full-corpus crawl is fast** (246 records in 20s) *because* it is incremental — which is
  also F2/F3's root enabler.
- No backpressure, rate-limit handling, or circuit breaker around Azure OpenAI; a 429 storm
  surfaces as per-document `error` outcomes.

---

## 7. Security & Data Integrity

| Area | Result |
|---|---|
| SQL injection | **PASS** — all f-string SQL interpolates only whitelisted table names via `safe_table()`; every value is parameterised. No injection surface found. |
| Secrets in VCS | **PASS** — `.env` gitignored, never committed. |
| Ingestion API auth | **FAIL** — F7, fully open including destructive routes. |
| CORS | **WEAK** — wildcard by default; credentials correctly off. |
| Ops endpoint exposure | PASS — `/metrics` 404s unless `ops_detail_enabled` or admin group. |
| Retrieval auth | PASS — `require_principal` on `/chat` and `/search`; JWT algorithm allow-list; `none` rejected. |
| Multi-tenancy | N/A — `tenant_id`/`acl` were deliberately removed; the corpus is public. 147,996 points still carry the dead fields (F3). |
| Unsafe file handling | PASS — PDFs are processed in memory, never written to disk; no path traversal surface. |
| SSRF | **WEAK** — `drupal_ingest_external_pdfs` is off by default, but `fetch_attachment` follows redirects with no host allow-list; an editor who can post a body link controls the fetch target. |
| PII | `documents_author` (4,370 rows) and `Person` nodes (200) hold named individuals from public CMS fields. No handling policy found. |

---

## 8. Missing Test Coverage

**The full suite passes — 2,075 passed, 1 skipped, in 24.9s — and catches none of F1–F16.**

The reason is structural: every pipeline test stubs the vector store with a lambda that
**discards the argument the bug lives in**:
```python
monkeypatch.setattr(pipeline, "delete_document", lambda doc_id, keep_ids=None: None)
```
This appears in `test_pipeline_catalog_wiring.py`, `test_pipeline_enrichment.py`,
`test_bundle_moves.py`, `test_unpublish_policy.py`, `test_attachment_orphans.py`. No test
ever asserts what `keep_ids=[]` does.

Missing scenarios, in priority order:

1. **Empty / whitespace-only document** → must not delete, must not report success. (F1)
2. **`delete_document(keep_ids=[])`** → must not wipe the document. (F1)
3. **`reindex_document` recoverability** → the document must come back on the next sweep. (F2)
4. **Pipeline-version migration** → a chunker change must mark documents for re-index. (F3)
5. **HTML-entity and whitespace hrefs** in `_extract_inbody_pdfs`. (F4, F5)
6. **Retry-marker lifecycle** for `skipped` attachments across runs. (F6)
7. **Auth required on every ingest route.** (F7)
8. **Cross-store reconciliation** as an assertion, not a script. (F10)
9. **Tag truncation collision** producing duplicate rows. (F11)
10. **Integration tests against real Qdrant + MySQL** — there are currently **none**; every
    test is a unit test over fakes. `app/local_tests/` exists but is not part of the suite.
11. Concurrency: two workers touching a shared attachment.
12. Azure 429 / timeout handling.
13. Large-document chunking (the `keep_ids` filter size ceiling).

---

## 9. Things Not In The Original Scope, Found Here

- **`/reindex` is a deletion primitive** (F2) — the highest-severity finding, and it sits
  outside the ingest path entirely.
- **The corpus is frozen against code fixes** (F3) — no migration mechanism exists at all.
- **Delete reconciliation is disabled in practice** (F8) — sophisticated, well-tested, never runs.
- **The knowledge graph is not part of the pipeline** (F9).
- **The ingestion API has no authentication** (F7).
- **Enrichment, date resolution, dead-link marking, orphan collection, and bundle-move
  protection** are all undocumented pipeline stages.
- **`ensure_collection` provisions 1 of 10 payload indexes** (F16) — a fresh deployment is
  silently degraded.
- **`is_current` is dead** (F15); `acl`/`tenant_id`/`term_ids`/`theme_ids`/`table_markdown`
  persist on ~99% of points after removal from code.
- **Enrichment orphans**: 80 `documents_enrichment` rows match no live `content_hash`.
- **91 attachment link rows** point at files with no document row.

---

## 10. Prioritised Remediation Plan

### P0 — before any further ingestion
1. **F1** — guard the empty-chunk swap; make `delete_document` reject `keep_ids=[]`. Add both tests.
2. **F2** — rewrite `reindex_document` to reset state + write a retry marker; never delete the row.
3. **F7** — put the ingest router behind `require_principal` + an admin group; bind to a private interface.

### P1 — this week
4. **F6** — backfill `documents_retry` from `ingest_log`; recover the 91 + 1 stranded documents.
5. **F4 / F5** — one-line `html.unescape(raw).strip()`; re-crawl the 15 + 57 affected links.
6. **F1 backfill** — clear `content_hash` on the 85 zero-vector documents and re-ingest.
7. **F10** — ship `scripts/verify_corpus.py`; run it after every sweep and fail on drift. Add MySQL to `/ready`.

### P2 — this month
8. **F3** — introduce `pipeline_version`; build `scripts/reindex_corpus.py`; normalise the corpus.
9. **F8** — enable `WORKER_SWEEP_RECONCILE` after a dry-run review.
10. **F12** — backfill `published_at`; alert on documents indexed without a date.
11. **F11** — truncate-then-dedupe; add `UNIQUE(document_id, tag)`.
12. **F16** — call `_ensure_keyword_index` from `ensure_collection`; validate collection dimension.

### P3 — planned work
13. **F9** — wire graph projection into the sweep, or schedule it and monitor freshness.
14. **F13**, **F14**, **F15** — error text on retry rows; fix `.env`/compose drift; resolve `is_current`.
15. Build the integration-test tier (items 10–13 in §8).

---

## 11. Production-Readiness Assessment

**What is genuinely strong.** The change-detection design is thoughtful and the reasoning is
documented to an unusually high standard. The index-then-delete swap is correct and survives
interruption. Delete reconciliation has a real completeness guard and bundle-move
protection. Referential integrity in MySQL is clean — 0 orphans across every FK'd table.
Version consistency between MySQL and Qdrant is perfect (0 mismatches, 0 double-versioned
documents). There are no orphaned vectors. Retrieval works: the traced document self-retrieved
at rank 1 with correct attribution. No SQL injection surface; no committed secrets.

**Why it is not production-ready.** The pipeline cannot currently guarantee that a document
which enters it stays correct and traceable:

- It **loses data silently while reporting success** (F1 — 85 documents today).
- Its **repair tool is a deletion tool** (F2 — 8,176 documents at risk).
- It has **no way to apply a bug fix to data already ingested** (F3 — ~99% of the corpus).
- **Nothing detects any of this** (F10) — the test suite is green, `/ready` is green,
  `/metrics` is green, and the catalog says every document is indexed.

The failure mode is consistent: the system is well-built for the paths it anticipates and
silent at the boundaries it does not.

---

## 12. Final Verdict

> **Can we confidently say the entire ingestion pipeline works correctly and reliably from
> source → extraction → chunking → embedding → MySQL → graph → Qdrant → retrieval, including
> edge cases, failures, retries, updates, deletes, duplicates, concurrency and recovery?**

**No.**

The happy path is sound and verifiably correct end-to-end. But three Critical defects break
the guarantee. Reconciliation does not balance — 85 documents are catalogued as indexed with
zero retrievable content, 10,112 are missing from the graph, and 99% of stored chunks were
produced by a chunker with four since-fixed correctness bugs that can never be re-applied.
The one operation an operator would reach for to fix a broken document destroys it instead,
and it is reachable without authentication.

**PASS is achievable.** The three P0 fixes are small and well-scoped — a guard clause, a
rewritten 6-line function, and a router dependency. The P1 backfills recover every document
identified here. What the system most lacks is not architecture but a **reconciliation
check that runs on every sweep and fails loudly** — the audit that found all of this took
one full-collection scroll and three SQL queries, and nothing in the codebase does it today.

---

### Appendix — Reproduction Artifacts

| Artifact | Purpose |
|---|---|
| `recon.py` | Full-corpus MySQL ↔ Qdrant ↔ Neo4j reconciliation (§3) |
| `test_empty_wipe.py` | Live F1 data-loss reproduction against a scratch collection |
| `trace_doc.py` | Single-document trace, source → retrieval (§ Stage results) |

All three ran against the live stack on 2026-08-16 and are reproducible as-is.
