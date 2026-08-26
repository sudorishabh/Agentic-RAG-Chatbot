# Agentic RAG Chatbot — Whole Codebase Guide

A plain-language map of the **entire codebase** and the **logic of every step**,
written to be read top-to-bottom. Verified line-by-line against the code at
commit `b9c8f38` (August 2026) — multi-label intents, database planner + tools,
name-keyed catalog, banded reranking, two-block answers, ingest-time enrichment.

> Companion deep-dives in the repo: `architecture.md` (module map),
> `retrieval-and-generation-flow.md` (query flow), `intent-classification-design.md`
> (intents), `database-planner-architecture.md` + `database-tool-registry.md`
> (catalog tools), `database-retrieval-redesign.md` (entity resolution),
> `retire-term-tables-plan.md` (name-keyed catalog), `ingestion.md`,
> `retrieval.md`, `generation.md`, `website-preference-retrieval.md`.
> `INTERVIEW_ARCHITECTURE_GUIDE.md` (system narrative) and
> `INTERVIEW_QUERY_PIPELINE_DEEPDIVE.md` (query-path depth + question bank) are
> the interview-facing cuts of this same material.

---

## 1. What this system is (in one breath)

A production **Retrieval-Augmented Generation** chatbot over TERI's knowledge base:
~11k **PDFs** plus the **teriin.org Drupal website**. It has two halves:

- an **ingestion pipeline** that turns every PDF and web page into chunked, embedded
  records in **Qdrant**, with a **MySQL catalog** of metadata alongside;
- an **agentic query pipeline** that classifies each question (multi-label), routes
  it to the right strategy (semantic search / catalog lookup / scoped summary / a
  combination of them), retrieves with several fused strategies, and generates a
  **grounded, cited** answer that refuses rather than hallucinate.

Multi-tenant, ACL-scoped, streams answers over SSE. A dependency-free embeddable
widget (`ui/script.js`) is the reference client.

---

## 2. The big picture

```
                    CLIENTS  (Bearer-JWT → tenant + groups)
                              │ HTTPS
      ┌───────────────────────┼─────────────────────────────────────┐
      ▼                                                              ▼
 PUBLIC RETRIEVAL SERVER  (app/main.py)        PRIVATE INGESTION SERVER (app/ingest_main.py)
   POST /chat   (SSE stream)                      POST /ingest/pdf|pdfs|run|article
   POST /search (retrieval only)                  POST /reindex,  GET /ingest/log
   GET  /source/{id}                              + background sweep scheduler
   GET  /health /ready /metrics /metrics/timings  (network-isolated, NEVER public)
      │                                                              │
   ┌──┴──────────┬─────────────┐                          ┌──────────┴────────┐
   ▼             ▼             ▼                          ▼                   ▼
 Qdrant     Azure OpenAI    MySQL                      MySQL           Drupal JSON:API
 vectors    chat + embed    catalog                   catalog         + PDF files
```

**Two servers, one shared factory** (`app_factory.create_base_app`): app logging,
CORS (credentials always off, methods `GET`/`POST`, headers `Content-Type` +
`Authorization`; a wildcard origin logs a warning), and observability init. The
public server answers questions; identity comes from a **verified Bearer JWT**,
never the request body. The ingestion server is protected by network isolation and
never exposed.

**Two data stores + one model service:** Qdrant (semantic vectors + the semantic
answer cache), MySQL (durable catalog + audit log + enrichment cache), Azure
OpenAI (chat + `text-embedding-3-large`, 3072-dim by default).

### The layering rule

The codebase is packaged with a **strict dependency direction**:

```
        pipeline/          ← the ONLY layer that touches both sides
        ┌────┴─────┐
   retrieval/   generation/     retrieval NEVER imports generation;
   (READ path)  (WRITE answer)  generation NEVER imports retrieval internals
        │            │          (they meet only via core/models.ContextBlock)
        └─────┬──────┘
          core/clients/         shared infra gateways (Qdrant, MySQL, Redis,
          core/models/          embeddings, LLM) + shared domain models
              │
        catalog/  ← ingestion WRITES it, retrieval READS it (the one shared store layer)
              │
        ingestion/ (WRITE path)
```

Everything reaches infrastructure through `core/clients/` (`@lru_cache`-memoized
lazy singletons) — the single place any package depends on for a Qdrant / MySQL /
Redis / embedding / LLM handle.

Two deliberate placement decisions worth knowing:

- `app/retrieval/catalog_prompt.py` holds the prompt text describing the catalog
  to three different LLM calls (intent classifier, slot-extraction fallback, v2
  planner). It sits *outside* `retrieval/structured/` on purpose: importing any
  submodule of that package runs its `__init__`, which pulls in the tools, planner
  and their MySQL/Qdrant/LLM clients — too much to pay just for prompt strings, and
  it would create an import cycle. (`app/retrieval/` has no `__init__.py`.)
- `app/pipeline/summarize.py` (scoped summarization) lives in the orchestration
  layer because it combines retrieval (catalog scope + lead-chunk fetch) with
  generation (the summary calls), so it belongs to neither feature package.

---

## 3. The package map (layer by layer)

| Package | Role | Key modules |
|---|---|---|
| `app/main.py`, `ingest_main.py`, `app_factory.py` | the two servers + shared FastAPI wiring | — |
| `app/api/` | HTTP endpoints | `chat.py` (/chat SSE + chat-only capacity limiter), `search.py`, `source.py` (cited PDFs), `ingest.py`, `health.py` (health/ready/metrics), `auth.py` (JWT principal) |
| `app/core/clients/` | **infra gateways** (lazy singletons) | `vector_store.py` (Qdrant + collection/index bootstrap), `database.py` (MySQL pool), `cache.py` (Redis, optional), `embeddings.py`, `llm.py` |
| `app/core/models/` | **shared domain contracts** | `document.py` (CanonicalDocument/Section, EntityRef, FileLink), `context.py` (the retrieval→generation `ContextBlock`) |
| `app/core/dates.py` | tolerant ISO-date handling for LLM-supplied bounds | `IsoDate`, `parse_iso_date`, `exclusive_end`/`inclusive_end`, `current_date_directive` |
| `app/pipeline/` | **orchestration** (only layer over retrieval + generation) | `query_pipeline.py` (the `/chat` + `/search` spine), `summarize.py` (scoped-summary use case) |
| `app/retrieval/` | **READ path** — no answer synthesis | `query_processor.py` (understanding), `understanding/` (prompt + facet filters), `retriever.py` (the `retrieve()` engine), `search/strategies.py` (dual/keyword/multi/corrective), `hybrid_search.py` (the search primitive + mandatory filter), `fusion.py` (RRF), `reranker.py` (banded ranking), `volatility.py`, `context_builder.py`, `citations.py`, `scoped_retrieval.py`, `source_locator.py`, `catalog_prompt.py`, `structured/` |
| `app/retrieval/structured/` | **catalog "database" capability** | `planner.py` (v1 deterministic + v2 LLM plan → parallel execute), `tools.py` (count/list/lookup/aggregate/list_themes/resolve_entity + guards + rendering), `entities.py` (Entity Registry), `filters.py` (Scope Resolver), `resolve.py` (fuzzy name matching), `answerer.py` (adapter + catalog fallback), `types.py` (RecordFilters/ToolCall/ToolResult/DatabasePlan) |
| `app/generation/` | **ANSWER synthesis** — no retrieval dependency | `answerer.py` (grounded generate/stream + chitchat), `prompts.py` (two grounding contracts + format directives + context formatting), `sections.py` (the two-block answer structure), `faithfulness.py` (marker validation, claim check, numeric check) |
| `app/catalog/` | **the MySQL document catalog** (ingestion writes, retrieval reads) | `schema.py` (DDL + idempotent migrations), `models.py`, `db.py` (timestamp + table-name guard), `state.py` (write model), `queries.py` (analytical + id-scope reads), `theme_taxonomy.py` (primary/sub theme map over `app/data.json`), `enrichment.py` (abstract cache), `log.py` (audit log) |
| `app/ingestion/` | **WRITE path** | `pipeline.py` (run orchestration, batching, parallelism), `change_detection/` (base/files/drupal), `extractors/` (pdf, pymupdf_local, camelot_tables, text_normalize, drupal, attachment), `canonical.py`, `chunking/` (segmenter/packer/classifier/payload/config), `indexer.py`, `enrich.py` + `enrich_backfill.py`, `upload.py`, `backfill.py`, `field_audit.py`, `textutil.py` |
| `app/cache/` | Qdrant-backed semantic answer cache | `semantic_cache.py`, `cache_keys.py` (partition = preference fingerprint + identity + format) |
| `app/observability/` | spans + stage timings + query metrics | `tracing.py`, `metrics.py` |
| `app/workers/` | sweep tasks + in-process scheduler | `tasks.py`, `scheduler.py` |
| `app/local_tests/` | standalone end-to-end ingestion harness (isolated `local_test_*` tables/collection) | `run_ingestion_test.py`, `serialize.py`, `dump.py`, `db_checks.py`, `reporting.py` |
| `app/config.py` | all settings (pydantic-settings from env/`.env`) | — |
| `scripts/` | one-shot migrations + index creation | `create_payload_indexes.py`, `create_fulltext_index.py`, `rename_catalog_tables.py`, `drop_term_tables.py`, `reclassify_theme_rows.py`, `backfill_tag_facet.py`, `rename_theme.py`, `migrate_source_type_website.py` |
| `ui/` | dependency-free embeddable widget (Shadow DOM), mirrors the two-block answer parsing | `script.js`, `index.html` |

---

## 4. The data model — the foundation

### 4.1 One canonical shape (`core/models/document.py`)

Every PDF or web page becomes a `CanonicalDocument` before chunking, so one
pipeline serves both. Fields: `document_id`, `source_type` ∈ {`pdf`, `website`,
`pdf_attachment`}, `sections[]`, facets (`authors`, `tags`, `categories` = themes),
scope (`tenant_id`, `acl`, `language`), `published_at`, `doc_version`,
`is_current`, `content_hash`, **cross-links** (`linked_pdf_id` /
`linked_article_uuid`) that mark "this web page and that PDF are the same content
in two formats", plus catalog-only extras (`entity_refs`, `file_links`,
`raw_meta`).

**`compute_content_hash()` covers body text ONLY** — no title, no metadata. That
is deliberate: the hash has to be reproducible from the source bytes, or a title
read off a PDF cover page would make it unstable and re-version + re-embed the
whole corpus on every sweep. Metadata still reaches storage; it just does not gate
re-indexing (a drifted title is carried by `refresh_document_title`, which rewrites
one payload field with no re-embed).

### 4.2 Why two stores

- **Qdrant** answers *"what does the content say?"* by semantic similarity.
- **MySQL** answers *"how many / which / when / by whom?"* relationally — exact
  counts and lists a vector search can't do reliably. Count and list read the
  **same** catalog rows, so they can never disagree.

### 4.3 Parent/child chunking (the key retrieval trick)

```
 PARENT chunk (~1800-2600 tok) ── stored as a ZERO vector (payload carrier, fetched by id)
   ├─ child (~400-480 tok) ── embedded ◄── search matches THIS (precise)
   ├─ child (~400-480 tok) ── embedded ◄──
   └─ child (~400-480 tok) ── embedded ◄──
```

Search hits small children (precise), then at answer time each winning child is
**replaced by its parent** ("parent-expand") for fuller context. Only children are
embedded (cheaper); parents are fetched by id. Two refinements:

- **A single-child section emits no parent** — it would be a near-duplicate of its
  own child; context falls back to child text when `parent_chunk_id` is absent.
- **Only the child's `embed_text` carries a breadcrumb** (`title › heading`, capped
  at 32 tokens). Headings are lifted out of the block stream into `Section.heading`
  and only rejoined onto *parent* text — and parents are never embedded — so
  without the breadcrumb a heading would reach no vector at all. `text` (what
  citations quote and `content_hash` covers) stays clean.

### 4.4 MySQL catalog tables (`catalog/schema.py`)

Table names were simplified from the legacy `ingest_state*` forms; the document
table name still follows the `ingest_state_table` setting (default `documents`).
`catalog/db.py::safe_table` whitelists the identifier so a bad setting can't become
a SQL-injection vector.

| Table | Grain | Notable columns |
|---|---|---|
| `documents` | one row per document | `document_id` (PK), `source_type`, `source_key`, `bundle`, `entity_type`, `fingerprint`, `content_hash`, `doc_version`, `changed_mark`, `size`/`mtime_ns`, `published_at`, `title`, `url`, `raw_meta` (JSON), `indexed_at` |
| `documents_author` | doc × author | `author` (matched with `LIKE`) |
| `documents_tag` | doc × tag | `tag` (matched **exactly**, case-insensitive fallback) |
| `documents_theme` | doc × theme | `theme`, `theme_type` (`primary`/`sub`), `parent`, `theme_group` (`main`/`other`), PK `(document_id, theme)` |
| `documents_attachment` | doc × attached PDF | `file_uuid`, `document_id`, `origin` (`attachment`/`inbody`), `url`, `filename` |
| `documents_enrichment` | content hash | `content_hash` (PK), `version`, `abstract`, `attempts`, `last_error` — **no FK, keyed by content not document** (see §5.6) |
| `ingest_log` | one row per document per run | `run_id`, `status`, `doc_version`, `chunks_indexed`, `error_message`, `event_time` |

**The taxonomy-term tables are retired.** `terms`, `term_aliases` and
`documents_term` are gone: the catalog is keyed by **name** (themes in
`documents_theme`, tags in `documents_tag`) and taxonomy UUIDs live only in Qdrant
payloads. `scripts/drop_term_tables.py` removes the leftovers; see
`retire-term-tables-plan.md`.

Migrations are idempotent and run on `ensure_state_table()`:
`migrate_renamed_facets` (carries `documents_category` → `documents_theme`
*including the value column*), then `migrate_theme_hierarchy` (adds
`theme_type`/`parent`/`theme_group`, then the PK — whose failure on legacy
duplicates is logged, not fatal).

### 4.5 Qdrant payload (per chunk)

`chunk_id`, `document_id`, `is_parent`, `source_type`, `title`,
`section_heading`, `section_type` (`toc`/`references`/`glossary` are excluded from
search), `chunk_text`, `content_hash`, `token_count`, `has_table`,
`table_markdown`, `doc_version`, `is_current`, `tenant_id`, `acl`, `tags`,
`categories`, `authors`, `term_ids`, `theme_ids`, `language`, `source_url`,
`file_url`, `published_at`, `pdf_id`, `pdf_path`, `article_uuid`, `linked_pdf_id`,
`linked_article_uuid`; children additionally carry `parent_chunk_id`,
`chunk_index`, `page_number`; plus `page_range` and the document's `extra`
(e.g. `bundle`, `nid`, `changed`). Empty values are dropped, so payloads stay lean.

Indexes created at ingest (`core/clients/vector_store.ensure_collection`):
`published_at` (datetime), `term_ids`, `theme_ids` (keyword). The rest of the
query-path filters and the full-text index are created by the two scripts in §7.5.

---

## 5. Ingestion — the logic, step by step

```
 SOURCE            EXTRACT           CANONICAL         CHUNK          EMBED+INDEX
 PDF on disk  ─┐
 Drupal API   ─┼─► per-source  ──► CanonicalDocument ─► parent/child ─► embed children,
 HTTP upload  ─┘   extractor        (one shape)         chunks          upsert Qdrant
                      ▲                                                     │
                      └──── change detection + catalog (MySQL) + audit log ──┘
```

### 5.1 Change detection first (`ingestion/change_detection/`)

Both sources yield the same `ChangeRecord` (`status`, ids, `fingerprint`,
`prior` state row, `payload`), and share one decision (`compute_status`): unseen →
`NEW`, changed fingerprint → `CHANGED`, else `UNCHANGED`; a vanished document →
`DELETED`.

- **Files** (`files.py`): walk the configured roots (ignore globs honoured for
  files *and* directories), **pre-filter on size + mtime** so an untouched file is
  never read or hashed, else fingerprint = SHA-256 of the bytes. Duplicate
  document ids (same slug from two paths) are warned and skipped.
- **Drupal** (`drupal.py`): a "source" is `(entity_type, bundle, incremental)`.
  Node bundles crawl incrementally against a `MAX(changed_mark)` **high-water
  mark** with `>=` (so a same-second edit isn't skipped); taxonomy vocabularies and
  custom blocks are small, so they are fetched in full and change-detected purely
  on fingerprint. **The crawl is always oldest-first**, which makes the high-water
  mark a *resume cursor*: a capped or interrupted run continues where it stopped
  instead of stranding older documents behind the filter. Boilerplate custom blocks
  (below `drupal_block_min_chars` and carrying no PDF) are skipped.
  Each attached or in-body PDF is yielded as its own `pdf_attachment` record right
  after its node; in-body PDFs are fingerprinted on their URL-derived uuid so the
  same PDF linked from many nodes ingests exactly once (and the fingerprint fits
  the `VARCHAR(128)` column). Delete reconciliation is opt-in: incremental sources
  enumerate live UUIDs separately, full-fetch sources use what the run just yielded.

### 5.2 Extract

- **PDFs** (`extractors/pdf_extractor.py`): `EXTRACTION_MODE` ∈ {`hybrid`
  (default), `azure_only`, `local_only`}. Hybrid **classifies every page** with
  PyMuPDF (`pymupdf_local.classify_document` → `PageSignal.route`) and routes:
  scanned/image → **Azure Document Intelligence OCR** (`prebuilt-read` by default;
  `prebuilt-layout` costs ~6× more but reconstructs tables), born-digital **table**
  → **Camelot** (lattice, falling back to stream per page) merged with the page's
  PyMuPDF prose, everything else → **PyMuPDF text**. Text captured during
  classification is reused, so local/table pages never re-parse the PDF. Every
  failure degrades: Azure unavailable → those pages fall back to local text;
  Camelot missing/empty → the page keeps its prose; classification itself failing →
  the whole document goes to Azure (then local).
  Then `_normalize_result` cleans each page (`text_normalize`): HTML layout
  comments, `<figure>` wrappers, page-number bars, degenerate "infographic" tables,
  chart number-soup regions, ligature repair (`ﬁ`, and `speci c` → `specific`),
  formula subscripts (`CO,` → `CO2`), and **running headers/footers** detected as
  short lines repeated across ≥50% of pages (joined-window matching, so a footer
  fragmented differently per page still matches).
- **Drupal** (`extractors/drupal_extractor.py`): JSON:API crawl with per-bundle
  `field_*` relationship discovery (plus `parent` for taxonomy terms), retrying
  session, cursor pagination. Attributes are partitioned into **body** (formatted
  text fields and long strings > 255 chars) vs **metadata** (short scalars/lists);
  relationships resolve to labels **and** `EntityRef`s carrying the target UUID and
  JSON:API type (so a later rename can't break joins). HTML → text preserves link
  URLs, image alts, iframe srcs and table cell boundaries. PDFs are collected from
  every `file--file` reference *and* harvested from rich-text hrefs/bare URLs
  (internal always; external only when `drupal_ingest_external_pdfs`); skipped
  non-PDF document attachments (`.docx`, `.xlsx`, …) are logged so a real gap is
  visible.
- **Attachments** (`extractors/attachment.py`): download (trying `https://` first,
  because teriin.org no longer answers on port 80), extract, and build a
  `pdf_attachment` document that **inherits its node's entity refs and facets**, so
  theme-scoped retrieval and per-theme counts reach the attached content too.

### 5.3 Canonicalize (`ingestion/canonical.py`)

Map extractor output to a `CanonicalDocument`. Facet routing is explicit and
shared by nodes and their attachments (`drupal_facets`): themes come from
`theme`-named fields **plus any reference into a theme vocabulary** (vocabulary
routing beats field-name guessing); tags from `tag`/`keyword` fields; authors from
`author` fields. `field_audit.py` reports against these same constants, so the
audit can't drift from the rules.

### 5.4 Chunk (`ingestion/chunking/`)

`segmenter.py` parses markdown-ish structure into typed blocks (text / code /
table / heading) — heading detection rejects extraction artefacts (ToC dot
leaders, HTML-comment fragments, pipe/formula rows, OCR symbol soup, measurement
fragments) — and assembles sections a heading owns, merging undersized ones.
`packer.py` (tiktoken with a chars/4 fallback) packs parents, then children within
each parent, coalesces undersized windows, and applies **sentence-aware overlap
carry** so a child starts on a whole sentence. `classifier.py` flags
toc/references/glossary by line *shape* (extraction garbles their headings).
`payload.py` serializes the Qdrant payload. Chunk ids are `uuid5(document_id | vN |
suffix)` — deterministic and **version-scoped**, which is what makes §5.7 safe.
`config.py` holds per-bundle presets (article ~380/1600, pdf ~450/2000,
research_papers ~480, `small_pdf` = one giant parent for ≤10-page documents).

### 5.5 Embed + index (`ingestion/indexer.py`)

Embed the child chunks in batches of 128 (`embed_text`, i.e. breadcrumb + text),
upsert children with vectors and parents as zero-vectors, stamping
`created_at`/`updated_at`.

### 5.6 Enrichment — the ingest-time abstract (`ingestion/enrich.py`)

Optional (`enrichment_enabled`, **off by default** — the first pass over an
existing corpus costs real money, so it should be a deliberate act). For each
document: adaptive sizing — ≤12k tokens is one call, longer documents get
notes-per-window (6k windows, 4 workers) then one reduce. Bodies under 600 chars
are skipped (they are their own best summary).

Cached in `documents_enrichment` **by `content_hash`, not `document_id`**, so the
cache survives a state-table reset (the usual way to force a reindex), and two
documents with identical bodies enrich once. Invalidated by **version, not TTL**:
`abstract_version()` hashes the prompts + model, so editing a prompt
transparently re-enriches. Failures are *recorded* (`attempts`) so a hopeless
document stops being retried after `enrichment_max_attempts`; a version change
resets the budget. `enrich_backfill.py` is the deliberate, `--limit`-bounded CLI
pass over documents the sweep never re-crawls (it rebuilds text from indexed
chunks rather than re-downloading anything).

Why it matters at query time: a scoped summary would otherwise represent each
document by its *lead parent chunk*, which for a long report is the cover page or
table of contents (see §6.5).

### 5.7 Persist + audit (`catalog/state.py`, `catalog/log.py`)

Write the `documents` row and replace its author / tag / theme / attachment rows in
one transaction. Theme rows are classified by `theme_taxonomy.classify` against
`app/data.json`: a bucket's children are **primary tags** (`parent` NULL),
anything below one is a **sub-theme** pointing at that tag, the bucket name itself
is never a theme, and each row records the `main`/`other` bucket it traces back to.
Stringified junk (`"False"`, `"True"`, `"none"`…) is dropped — the catalog once
held 404 rows whose theme was the literal string `"False"`. An unknown theme is
kept as an unparented sub-theme rather than dropped.

Every document/run outcome is appended to `ingest_log` (`indexed`,
`unchanged_content`, `deleted`, `skipped`, `error`; `unchanged` only when
`ingest_log_unchanged`), pruned by `ingest_log_retention_days` in batches.

### 5.8 The run loop (`ingestion/pipeline.py`)

Per document (`_handle`):

```
 DELETED           → delete Qdrant points + catalog row
 UNCHANGED         → refresh the size/mtime stat if it drifted, done (free)
 NEW / CHANGED     → build doc → content_hash → enrich (cache-first)
                      ├─ content hash unchanged → persist state (indexed=False),
                      │    refresh the payload title if it drifted, DON'T re-index
                      └─ changed → next_version → chunk → INDEX NEW POINTS
                           → delete_document(keep_ids=new) → persist → log
```

**Zero-downtime reindex:** index the new version's points **first**, then delete
everything else for that document. Chunk ids are version-scoped, so the old version
stays searchable until the swap and a mid-index crash leaves it fully intact.

Run-level controls: **one corpus-wide run at a time** (`_exclusive` → a rejected
trigger becomes HTTP 409); `ingest_max_docs_per_run` stops cleanly at a *document*
boundary (never between a node and its attachments) and counts in-flight work
pessimistically so the cap can't overshoot; unchanged scans are free and never
consume the budget; `ingest_batch_size`/`_pause_seconds` throttle within a run;
`ingest_workers > 1` runs a single-threaded crawler feeding a bounded pool of
per-document workers (keep it below `mysql_pool_size`).

`workers/scheduler.py` runs the sweep on the ingestion server's lifespan:
sweep → prune the semantic cache → prune the ingest log → sleep
`worker_sweep_interval_seconds` (3600), each step logged-and-continued on error.

---

## 6. Query — the logic, step by step

The spine is `app/pipeline/query_pipeline.py` (`stream_answer` for `/chat`,
`search_blocks` for `/search`), and its shared front-matter is `_prepare`:
**understand → route → (embed + cache) → retrieve → generate → verify / assemble /
persist / record.**

`/chat` runs the blocking pipeline from the event loop one event at a time through
`anyio.to_thread` with a **chat-only capacity limiter**
(`chat_stream_max_concurrency=64`): each active stream would otherwise pin one of
the ~40 shared request-threadpool threads for a whole generation and starve auth
dependencies and probes. The generator is closed in a `finally`, so a client
disconnect still runs the pipeline's cleanup (spans, cache writes).

### STEP A — Understand (multi-label) · `retrieval/query_processor.py`

One structured LLM call turns the turn (+ up to 12 turns of history) into a
**`QueryUnderstanding`**:

- `intents[]` — a **set** of `{label, confidence, rationale}` (multi-label)
- `query_rewrite` — standalone, pronoun-resolved query
- `output_format` — prose / list / table / csv / json / markdown / diagram / timeline
- `scope` — `source_type`, `target`, `theme`, `author`, `tags`, `date_from`,
  `date_to_inclusive`, `language`
- database slots — `operation`, `group_by`, `bundle`, `title_contains`,
  `theme_children`, `limit`

**The intent taxonomy (nine labels, three axes):**

| Kind | Labels | Behavior |
|---|---|---|
| **Content** (combine freely) | `qa`, `database`, `summarization`, `comparison` | multi-label |
| **Format modifier** | `structured_output` | sets `output_format`, never appears alone |
| **Terminal** (exclusive, highest wins) | `safety_policy` > `out_of_scope` > `clarification_needed` > `chitchat` | short-circuit before retrieval |

**Rule of thumb:** data *inside* a document → `qa`; facts *about the catalog* (how
many reports) → `database`; summarizing a **set** → `summarization`; a single named
document → `qa` + summary format.

**Three prompt blocks are appended per request**, in this order (static prefix
first so the long stable part stays prompt-cacheable):

1. `catalog_inventory_directive()` — names the bundles this deployment *actually
   holds* and which configured ones have no rows, so the model can't confidently
   set a content type that will answer a flat zero;
2. `catalog_coverage_directive()` — names the real `published_range`, so "this
   year" against a corpus that stops in 2024 scopes to what exists, and settles
   that **"the latest" means no date bound at all** (ranking already prefers the
   newest of comparable documents; a guessed bound would *exclude* the answer);
3. `current_date_directive()` — anchors relative dates to today (UTC), because a
   model left alone resolves "last six months" against its training data and the
   failure is invisible: the dates come back well-formed, just wrong.

**Dates are asked for inclusively and converted in code.** The LLM fills
`date_to_inclusive` (the last day to include) and `QueryScope.date_to` derives the
half-open bound via `exclusive_end` — a model reliably copies a date the user typed
and unreliably increments one, and when it forgets, a single-day query loses every
row. `core/dates.IsoDate` also sanitizes trailing JSON punctuation
(`"2022-01-01},"`) at the model boundary, because a dropped bound silently *widens*
the query.

**Confidence (hybrid):** with `analysis_votes=1` (default) it's the model's
self-reported score; with `>1` it fires N samples in parallel at temperature 0.7
and confidence = the agreement share. `_resolve_intents` then applies the
threshold (`intent_confidence_threshold=0.5`), terminal exclusivity + priority, the
"`structured_output` never alone" rule, and a guaranteed content fallback.
`_merge_understanding` majority-votes the scalar attributes field by field (a slot
added to the schema must be voted here too, or it silently resets to its default).

**Back-compat:** the rich set is collapsed onto a single legacy route
(`pq.intent`) plus a `QueryAnalysis` of flat slots, while the full multi-label
result stays on `pq.understanding` (exposed on `/search`, logged, and read as
"capabilities" by the router). **Fails open** to plain `qa` on any error.

One deliberate mapping: **`out_of_scope` routes to `qa`, not chitchat.** The
classifier is one stochastic sample and frequently mislabels an in-corpus question
(a pasted title, a domain topic) as out-of-scope; blind deflection then hides
content the store actually holds. Routing it through retrieval lets the corpus be
the arbiter — a genuinely off-topic query retrieves nothing usable and the
grounding prompt returns the standard refusal.

**Facet scope → Qdrant conditions** (`understanding/filters.py`): theme →
`categories MatchAny(name variants)` (name-only now that the term tables are
retired), `tags MatchAny`, `source_type=pdf` → `{pdf, pdf_attachment}`,
`website` → `{website, article}` (pre-rename points), `language MatchValue`,
dates → `published_at DatetimeRange(gte, lt)` in UTC.

**`author` is deliberately NOT applied as a qa-path filter.** The stored `authors`
field is an exact-match keyword index populated on only ~20% of chunks with full
display names ("Ms Meena Sehgal", "TERI Web Desk"), while the classifier extracts a
loose form ("TERI", "Sharma"). As a hard `AND` it excluded the 80% of the corpus
with no author at all and then missed the rest — turning strong matches into false
refusals. Author scoping stays on the catalog path, which `LIKE`-matches its facet
table.

### STEP B — Route · `pipeline/query_pipeline.py`

```
pq.intent (+ capabilities from pq.understanding)
   ├─ chitchat                 → plain LLM reply, no retrieval                 → done
   ├─ structured, title lookup that is really a content question
   │                           → add a document_id filter and fall into QA on that doc
   ├─ structured (database only)→ Database Planner → catalog tools              → done
   ├─ scoped_summary           → summarizer (empty/unsummarizable scope → qa)   → done
   ├─ database + qa/comparison → catalog section (deterministic) ▸ prefix ▸ QA answer
   └─ qa (default + fallbacks) → STEP C onward (full RAG)
```

The **combined answer** is the interesting one: when a query carries both
`database` and a content intent, the deterministic catalog answer and content
retrieval are **independent**, so they run concurrently (a one-worker pool with
`copy_context()` so the worker's span still lands in this request's stage
breakdown) and the request pays the slower of the two rather than their sum. The
catalog text is prefixed onto the grounded answer; faithfulness and the numeric
check run on the grounded part only, so the exact count is never "corrected".

Two empty-retrieval fallbacks, in order:

1. a combined query whose content retrieval came up empty still returns its
   deterministic catalog answer alone;
2. otherwise, if the catalog hasn't already been asked about this query,
   `catalog_fallback` offers what the catalog *lists* for the question's scope —
   framed by `NO_CONTENT_WITH_CATALOG` ("I don't have content that answers that.
   The closest I can offer is what the catalogue lists for it.") so a list of
   titles is never mistaken for the substance asked for. It requires a **subject**
   facet (theme / tags / author / title_contains) — "the 10 most recent reports"
   answers no question — forces `operation=list`, never spends an LLM parse, and
   fails open to the plain refusal.

### The Database capability (STEP B's `database` branch) · `retrieval/structured/`

A **planner + tools** system. *Operations are tools; the entity (bundle) is a
parameter*, so registering a content type is a data change, not new code.

```
 database intent ─► planner.plan(slots)            (v1: deterministic operation→tool)
                    planner.plan_multi(question)   (v2: LLM, ≤4 calls, opt-in)
                          ▼
                    DatabasePlan = [ToolCall, …] ─► execute() (parallel, fail-open)
                          ▼
                    ToolResult{ ok, data, citations, rendered, error_kind }
                          ▼
                    _compose(): stack rendered sections, renumber citations
```

| Tool | Answers | Backing |
|---|---|---|
| `count_records` | "how many research papers in 2024" | `queries.count_documents` |
| `list_records` | "list 2023 news" (recent-first, cited; bullets / table / timeline) | `queries.list_documents` |
| `lookup_record` | "the article titled X" — returns a `chain_document_id` when it uniquely identifies a document for a content question | `queries.list_documents` |
| `aggregate_records` | "articles per theme / year / author / content type" | `queries.distribution` |
| `list_themes` | "what themes do you cover?" — top-level themes split **Main / Other**, optionally with sub-themes nested, or one parent's children | `queries.theme_vocabulary` |
| `resolve_entity` | fuzzy free-text name → canonical author / bundle / theme | `structured/resolve.py` |

**Two shared pieces.** The **Entity Registry** (`entities.py`) binds a bundle to
its query shape and owns synonyms, display labels, the words that name *several*
bundles, and `is_available()` (a bundle can be configured yet have no rows).
The **Scope Resolver** (`filters.py`) is the one place free-text names are
canonicalized and dates parsed. Canonicalization happens *there* rather than as a
planner step because a plan's calls execute in parallel with no data flow between
them — a `resolve_entity` call could never hand its result to a sibling
`count_records`. `tools.resolve_entity` remains for the one thing that path can't
do: asking the user which of several close matches they meant.

**Fuzzy matching** (`resolve.py`) is plain normalization + `difflib` over each
type's small candidate set (16 bundles, ~200 themes, low hundreds of authors —
no new infrastructure). `score()` is the max of a whole-string ratio, a
word-order-insensitive token-set ratio, a single-token prefix/abbreviation score
(discounted by how much of the candidate that token covers) and a length-aware
substring boost. `classify_band()` then says **ACCEPT** (≥0.90, or ≥0.60 with a
≥0.30 lead over the runner-up), **AMBIGUOUS** (≥0.60), or **MISS**. Tags are
matched *exactly* instead: they are a long-tail freeform vocabulary (~237 terms
over ~224 documents) where similarity ranking would flag an ambiguity on almost
every query.

**The guard ladder is where most of the correctness lives.** Every guard exists
because some phrasing produced a confidently wrong number:

| Situation | Behaviour | Why |
|---|---|---|
| Unrecognized bundle | `ok=False` → fall through to semantic search | never a misleading zero |
| A word naming several bundles ("projects") | **terminal** clarification (`ambiguous_entity`) | picking one reports its total as if it were all; omitting it counts articles as projects |
| Author/theme/tag matched nothing | filter still runs; only an **empty** result becomes "No author matching 'X' found" | being unsure is not proof of absence — the query may find rows anyway |
| Name matched several candidates closely | ask which was meant, never silently pick | §4 of the redesign: ask on ambiguity |
| Bundle registered but absent from *this* catalog | fall through | "0 reports" would be a fact about the vocabulary, not the corpus |
| Zero under a **guessed** title substring | fall through to semantic search | `title LIKE '%…%'` searches one column; the subject lives in the body. Unless the question is about titles ("titled X", a quoted phrase), that zero would claim the corpus is silent on a topic when only its titles are |
| Generic collective word ("publications", "works") | clear an inferred bundle so the count spans everything | 10 papers reported instead of 21 papers + articles |

`error_kind` decides terminal vs fall-through: `unresolved` / `ambiguous` are
terminal only while `entity_resolution_enabled` is on (they come from fuzzy
matching, which wants an eval first); `ambiguous_entity` is terminal
unconditionally (a curated list, nothing fuzzy about it). Everything else keeps the
fall-through to semantic search.

Answers state their own interpretation: `_scope_phrase` names every active filter
("There are 12 research papers by Dr Suneel Pandey on 'Waste' in 2024…") using the
**canonical** names resolution matched, and `_period_label` names the last day
actually covered rather than echoing the exclusive bound. `_applied_filters` is the
same set structurally, so a caller can check the interpretation programmatically.

### STEP C — Embed + cache (qa path)

Embed the `search_query` once (reused by every retrieval leg), then look up the
**semantic answer cache** (`cache/semantic_cache.py`): a dedicated Qdrant
collection, nearest neighbour on the query vector, gated at cosine
`semantic_cache_threshold=0.995` (near-verbatim rephrasings only — at the old 0.97
a different year or theme could return the wrong cached answer). The scope
partition (`cache_keys.semantic_partition`) is a hash of the **retrieval-preference
fingerprint** + caller identity (tenant | groups | top_k) + `answer_format`, so
retuning the preference knobs or crossing an ACL boundary self-invalidates. On top
of that, the stored **facet fingerprint** must match exactly (theme, author, dates,
tags, source_type, language) — legacy entries without one count as mismatches.
Qdrant has no TTL, so each point carries `expires_at`, filtered at lookup and
deleted by `prune` (opportunistically every 200 stores, and on every sweep).

### STEP D — Retrieve · `retrieval/retriever.py` (the heart of RAG)

```
 search_query, filters, format, capabilities
   ▼  decide legs:
     dual  = prefer_website_enabled(ON) AND no source_type AND format ≠ table
     multi = multi_query_enabled AND content intent AND no source_type
             AND no filters AND ≥5 words
     keyword_terms = salient terms  (only if keyword_leg_enabled)
   ▼  CANDIDATE GENERATION (one shared ThreadPoolExecutor, max_workers=4):
     (a) BASE  dense k=40   (or DUAL: website@20 + not-website@40, same vector)
     (b) KEYWORD  MatchText(chunk_text = quoted/proper-noun/acronym/year terms)
     (c) MULTI   LLM writes 2 paraphrases (temp 0.7) → dense search each
   ▼  RRF FUSION  score = Σ 1/(60+rank)   (rank-based → fuses incomparable scales)
   ▼  FACET RELAXATION (only on a total miss under LLM-guessed facets; keeps the date scope)
   ▼  RERANK  banded: relevance ▸ completeness ▸ recency ▸ authority
   ▼  CORRECTIVE (if enabled AND top raw semantic < 0.2): reformulate → 1 pull → RRF → rerank
   ▼  BUILD CONTEXT: parent-expand → dedup(0.92) → budget(9000) → attention-order OR website-first
   ▼  ATTACHMENT SUPPLEMENT (answer_format=detailed only)
   ▼  ContextBlock[]
```

**Mandatory security filter on every search** (`hybrid_search.build_filter`):
`is_parent=false`, `is_current=true`, `tenant_id`, `acl MatchAny(groups)`, and
`must_not section_type ∈ {toc, references, glossary}`. The collection's existence
is verified once per process, so steady state is a single `query_points` per pull.

**The dual pull** (`prefer_website_enabled`, **on**) issues two searches sharing one
query vector — `source_type == website` at k=20 and a "not website" pull at k=40,
both keeping any non-source filters. Their union guarantees the small website's best
chunks are fetched even though ~11k PDFs dominate the corpus.

**Facet relaxation** — when a facet-scoped pull returns *nothing*, retry once
without the facets. The distinction is **who chose the constraint**: theme, author
and source_type are the LLM's guesses at how the corpus happens to be labelled, so
discarding them recovers from a bad guess; a **date range is what the user actually
asked for**, so it survives the retry (`date_conditions`) — answering "reports from
2023" out of 2019 is worse than answering nothing, the more so because the widening
is invisible (recorded on the span and the log, never in the answer). A date-only
filter set skips the retry entirely, since it would re-run the pull that just came
back empty.

**Reranking is banded, not blended** (`reranker.py`). The old weighted blend got
the important case backwards: min-max normalizing the semantic scores separates
candidates most aggressively exactly when they are closest together, while a
recency weight small enough not to overrule a better passage is also too small to
break the ties it exists for. So candidates are **banded** and ranked on the bands
in priority order:

1. **relevance** — scores within `rerank_relevance_tolerance` (0.03) of the band
   *leader* are "similarly relevant"; a candidate a band lower never climbs past
   one above it. The band widens ×`rerank_volatile_tolerance_multiplier` (2.0) when
   `volatility.is_volatile(query)` matches a lexicon of things that go stale
   (pricing, APIs, regulations, announcements) or asks for the current state
   ("latest", "as of"). Widening only changes how often the lower keys are
   reachable — nothing ever crosses a band.
2. **completeness** — within a relevance band, a passage holding
   `rerank_substance_ratio` (1.5×) the text of another says substantially more and
   leads it. Length is a log-scaled proxy: accuracy isn't measurable at ranking
   time, but a chunk cut short does carry less of an answer. Bands are cut *within*
   each relevance band, so a long passage from a less relevant document can't place
   the boundary that splits two similarly relevant ones.
3. **recency** — comparable passages settle on `published_at`, newest first
   (undated sits mid-set at 0.5, so an unknown neither leads nor trails).
4. **authority** — a `source_authority` payload override. Nothing writes it today,
   so it is a constant that cannot reorder anything; it stays as the lowest key so a
   corpus that starts stamping authority gets the behaviour for free.

So two editions of the same annual report land in one band and, unless one is a
fragment, the newer leads — while an older passage that actually answers the
question still outranks a newer one that merely mentions it. Providers:
`embedding` (reuse the dense score, default), `llm` (≤40 candidates),
`cross_encoder` (`BAAI/bge-reranker-v2-m3`, cached), `cohere` (`rerank-3.5`,
cached client) — every non-default provider falls back to the dense score on error.
`rerank_table_boost` (0.15) lifts *relevance* for a table-bearing chunk when the
answer wants a table (so it can climb a band), and is inert when smaller than the
tolerance. Returned candidates carry the band basis in `score` and the raw provider
score in `semantic_score`; **`score` is not monotone with the returned order**,
because inside a band recency decides.

**Context building** (`context_builder.py`): parent-expand each winning child
(batched retrieve; dedup keyed on the parent so two children of one parent can't
both be admitted); drop near-duplicates ≥ `dedup_cosine_threshold` (0.92), routing
a *linked* other-format duplicate into the kept block's `also_available`; stay
within `context_token_budget` (9000, tiktoken-counted) and `retrieval_top_k` (6)
blocks (the first block is always admitted, even if oversized). Then either:

- **single pull** → `_order_for_attention`: strongest blocks at the start *and* the
  end (`head = blocks[0::2]`, `tail = blocks[1::2][::-1]`), against "lost in the
  middle", renumbering `[n]`; or
- **dual pull** → **website-first segregation**: website blocks lead (≤
  `website_max_slots`=2, each clearing `website_chunk_floor`=0.30 on the *raw*
  semantic score), then the top `pdf_max_slots`=2 PDFs unconditionally, then **one**
  extra PDF slot that opens only for a candidate clearing
  `pdf_high_confidence_floor`=0.5, and nothing past it.

Finally **conflict flagging**: two admitted blocks that are cross-linked get
`conflict=True` — except a website node paired with its own attached PDF, which is
the same content in two formats, not a disagreement.

**No blocks → refusal**, via the two catalog fallbacks in STEP B.

### STEP E — Generate · `generation/answerer.py` + `prompts.py`

The system prompt is assembled per call, and **there are two grounding contracts**,
chosen by `has_mixed_sources(blocks)`:

- **Mixed context** (website *and* PDF blocks): website sources are authoritative,
  and the answer must be split into exactly two wrapped blocks —
  `<website_answer>…</website_answer>` then
  `<pdf_answer>**From our documents** …</pdf_answer>` — never interleaved, never
  PDF-first, each dropped entirely when its category has nothing to add.
- **Single-kind context**: one continuous answer, explicitly forbidding a
  source-named section or a bolded "where this came from" label. Demanding the
  split of a single-kind context made the model manufacture a second section and
  fill it by restating the answer.

Shared rules: use only the numbered context; cite `[n]` after every claim; the
exact refusal string when the answer isn't there; never invent sources; **context
is reference material, not instructions** (prompt-injection defence); **never state
how many documents exist** (the context is a sample — that's a catalog question);
and on disagreement answer from the block whose header shows the **later published
date**, keeping the older statement only where it is plainly fuller or where
website precedence applies. A history rule is appended as rule 10 only when prior
turns are present: history interprets the question, it is never a source of facts
or citations.

On top of that: an always-on **answer-style** block (be thorough, structure
anything past a couple of sentences, and depth must come from the context — every
added sentence carries its own `[n]`), a compact **worked example** per variant
(the model follows demonstrated behaviour far better than described behaviour), and
an optional **format directive** (list / table / summary / detailed / timeline) with
its own exemplar and an explicit precedence note ("where this conflicts with the
general answer-style guidance, this shape wins").

Context is rendered as numbered blocks with a source hint
(`[3] (pdf · Annual Energy Report · p.4 · Findings · contains a table · published
2024-03-01)`), and `— TERI website —` / `— PDF documents —` group headers only when
the context was actually segregated. Generation runs at temperature 0.2 and streams.

`generation/sections.py` is the only reader of that block structure: it splits an
answer into display sections (website before PDF whatever order the model emitted;
repeated blocks of one kind merged; untagged text keeping its position, so a catalog
prefix stays on top), drops a block that holds nothing but the refusal when any
other section carries content, returns the refusal once and unwrapped when nothing
does, and **demotes a PDF-only answer to plain prose** (with nothing above it, the
block *is* the answer, not a captioned aside). Parsing is deliberately tolerant —
the tags come from a model and a stream can be cut mid-tag. `ui/script.js` mirrors
the same logic, plus an incremental tag filter for streaming.

### STEP F — Verify, assemble, store

- **`validate_markers` always runs** — strips any `[n]` outside `1..len(blocks)`, a
  hard guarantee the model cannot cite a block that wasn't sent.
- **`faithfulness_check` (default off):** extract atomic claims → one
  supported/not verdict per claim in parallel against its *cited* blocks (a small
  model is unreliable as a holistic grader but strong at scoped binary verdicts) →
  if any claim is unsupported, regenerate **once** with a correction note, emitted
  as a `correction` SSE event (the corrected text is what gets cached). Fails open
  to "faithful" at every stage. The correction note points back at the structure the
  prompt already specifies, so a single-source answer isn't told to preserve blocks
  it never had.
- **`numeric_mismatches`** (observe-only): flags numbers in the answer that appear
  in no cited block; logged and reported on the response, never auto-corrected.
- **Citations are built from payloads, never the model** (`citations.py`): a website
  block links to its own page (never to its attachment, which is its own citation),
  a PDF to its `file_url#page=N` or the local `/source/{id}#page=N` fallback.
- **The sources footer lists only what the answer cited** (`_cited_blocks`): a block
  the model rightly dropped must not resurface as a chip contradicting the answer
  above it — falling back to every block if the answer cites nothing.
- `_persist` stores the result in the semantic cache; `_record` emits the
  `rag_metrics` log line with the per-stage and per-component breakdown.
- **SSE sequence:** `token`* → (`correction`?) → `sources` → `done`, with a terminal
  `error` event if the stream fails mid-response (the 200 is already on the wire, so
  a bare disconnect would render as a complete answer). Ready-made results
  (chitchat, catalog answer, scoped summary, cache hit, refusal) use the same shape
  via one `token` event.

### 6.5 The scoped-summary path · `pipeline/summarize.py`

"Summarize the Climate theme / 2024 publications" can't be served by similarity
search — the user defined a **set**, not a topic (searching the phrase retrieves
chunks similar to *"summarize theme X"*).

```
 analysis.scope ──► _scope_filters (theme canonicalized, bundle validated, author,
        │            title, dates)   → None if nothing scopes the set → fall to QA
        ▼
 catalog.document_ids_in_scope(limit=30)            # newest-first, capped
        ▼
 _collect_docs: ingest-time ABSTRACT per document (catalog.abstracts_for),
        │        falling back to a lead parent chunk only for un-enriched docs
        ▼
 total ≤ 12k est. tokens?  ── yes ─► ONE grounded call over all documents
        └─ no ─► MAP (batches ~6k tokens, 4 workers, structured bullets per doc)
                  ▸ REDUCE (one cohesive thematic overview citing [n])
        ▼
 document-level citations ;  any failure → None → plain QA
```

The abstract preference matters: an abstract is built from the whole document,
whereas the lead parent chunk is only its *first section* — for a long report, the
cover page or table of contents. Once abstracts exist, most scopes skip the map
stage entirely. `scoped_retrieval.lead_parents` is the fallback, and it escalates:
children carry `chunk_index` and parents don't, so it takes each document's
earliest *usable* child (the mandatory filter excludes toc/references/glossary, so
a report whose first chunk is its ToC used to vanish from the scope silently), looks
past the front matter, and as a last resort takes the opening chunk anyway.

---

## 7. Cross-cutting concerns

### 7.1 Security / multi-tenancy

- Identity = **verified Bearer JWT** claims (tenant + groups) — never the request
  body, which is why `QueryRequest` has no tenant field at all. Anonymous (auth
  off) = tenant `default`, groups `["public"]`. Algorithms are an allow-list,
  `exp` is required, audience/issuer enforced when configured.
- Mandatory `tenant_id` + `acl MatchAny(groups)` on **every** Qdrant query, and the
  same conditions on `/source/{id}` — a document outside your search visibility is
  a 404, not a download. Source files are additionally confined to the configured
  PDF roots (path-traversal guard), and `top_k` is bounded (1..50) on public input.
- CORS never enables credentials (a wildcard-capable origin plus ambient cookies
  would make every embedding page a CSRF vector); auth uses a non-ambient bearer.
- `/metrics` and `/metrics/timings` answer **404** unless `ops_detail_enabled` or
  the caller is in `ops_admin_group` (only meaningful with auth on) — their bodies
  fingerprint the deployment. `/ready`'s contract is the status code; detail is
  gated the same way.

### 7.2 Caching

The semantic answer cache (Qdrant collection) is the one answer cache; the older
Redis exact-match and embedding caches were removed. Redis remains an optional
client (`redis_url`) and is reported by `/ready`. Two more caches worth naming: the
**enrichment cache** (content-hash keyed, version-invalidated) and short in-process
TTL caches for `available_bundles()` / `published_range()` (600 s) plus an
`lru_cache` of distinct authors (with `reload_authors()` to drop it).

### 7.3 Fail-open, everywhere

Bad understanding → passthrough `qa`; catalog can't answer → fall through to `qa`;
empty scope → `qa`; name resolution fails → filter on the name as typed; a
retrieval leg fails → `[]`; the keyword index doesn't exist → dense-only; rerank
provider down → dense score; parent fetch fails → child text; faithfulness error →
assume faithful; MySQL blip in the prompt directives → omit the block rather than
claim the catalog is empty; enrichment unavailable → index without an abstract.
The consistent exception is the guard ladder in §6's database branch, where being
*explicit* about a miss beats guessing.

### 7.4 Observability

`tracing.span(name)` times a stage, feeds `observability/metrics` (per-stage
count / total / avg / p50 / p95 / max over a 512-sample window, plus per-component
totals: qdrant / llm / embedding / rerank / extraction / other) and optionally
mirrors to OpenTelemetry. `collect_into` gathers a per-request breakdown onto the
`rag_metrics` line. Stage names are the stable contract: `rag.query_understanding`,
`rag.embed_query`, `rag.semantic_cache`, `rag.db_section`, `rag.scoped_summary`,
`rag.search`, `rag.multi_query`, `rag.keyword_leg`, `rag.search_relaxed`,
`rag.rerank`, `rag.corrective`, `rag.context_build`, `rag.attachment_pull`,
`rag.faithfulness`, `rag.catalog_fallback`, `rag.semantic_cache_store`,
`rag.stream_answer` (the parent, excluded from component totals), and
`ingest.extract` / `ingest.chunk` / `ingest.embed` / `ingest.upsert`.

Note: on the streaming path only the **pre-token** stages reach the per-request
dict, because the SSE driver resumes the generator in fresh contexts; later spans
still reach the global aggregates. Retrieval time — the part worth watching — is
all pre-token.

### 7.5 Operational prerequisites

- `scripts/create_payload_indexes.py` — indexes the fields every query filters on
  beyond the three created at ingest.
- `scripts/create_fulltext_index.py` — the `chunk_text` full-text index the keyword
  leg needs (until it exists, that leg fails open to dense-only).
- Both are idempotent, run server-side over existing points (no re-embedding), and
  must not run during an ingestion run.
- Migrations for an existing deployment: `rename_catalog_tables.py`,
  `drop_term_tables.py`, `reclassify_theme_rows.py`, `backfill_tag_facet.py`,
  `migrate_source_type_website.py`; `rename_theme.py` for a CMS theme rename (which
  incremental ingestion cannot notice, because renaming a taxonomy term doesn't bump
  the referencing nodes' `changed` marks — and step 2 is editing `app/data.json`).

---

## 8. Current feature-flag defaults (know these)

| Setting | Default | Notes |
|---|---|---|
| `prefer_website_enabled` | **True** | dual website-first pull is **ON** |
| `website_candidate_k` / `website_max_slots` / `website_chunk_floor` | 20 / 2 / 0.30 | website lead |
| `pdf_max_slots` / `pdf_high_confidence_floor` | 2 / 0.5 | PDF depth + the gated 3rd slot |
| `retrieval_candidate_k` / `retrieval_top_k` | 40 / 6 | candidates per pull / blocks kept |
| `context_token_budget` / `dedup_cosine_threshold` | 9000 / 0.92 | context building |
| `reranker_provider` | `embedding` | reuse the dense score |
| `rerank_relevance_tolerance` | 0.03 | relevance band width |
| `rerank_volatile_tolerance_multiplier` | 2.0 | band widening on stale-prone topics |
| `rerank_substance_ratio` | 1.5 | completeness tier ratio |
| `rerank_table_boost` / `rerank_score_threshold` | 0.15 / 0.0 | table nudge / raw-score floor (off) |
| `analysis_votes` / `intent_confidence_threshold` | 1 / 0.5 | self-consistency off; per-label gate |
| `multi_query_enabled` / `multi_query_paraphrases` | False / 2 | paraphrase expansion (opt-in) |
| `keyword_leg_enabled` | False | full-text leg (opt-in; needs the index) |
| `corrective_loop_enabled` / `corrective_min_score` | False / 0.2 | CRAG requery (opt-in) |
| `database_multi_call_enabled` | False | LLM planner v2 (v1 deterministic default) |
| `entity_resolution_enabled` | False | terminal unresolved/ambiguous answers (matching itself always runs) |
| `faithfulness_check` | False | claim verify + one regen (markers always validated) |
| `semantic_cache_enabled` / `_threshold` / `_ttl` | True / 0.995 / 86400 | the surviving answer cache |
| `enrichment_enabled` / `enrichment_max_attempts` | False / 3 | ingest-time abstracts (opt-in; spend control) |
| `auth_enabled` | False | turn on for any non-public corpus |
| `ops_detail_enabled` / `ops_admin_group` | False / "" | metrics visibility |
| `chat_stream_max_concurrency` | 64 | chat-only capacity limiter |
| `extraction_mode` / `camelot_flavor` | hybrid / lattice | PDF routing |
| `azure_document_intelligence_model` | `prebuilt-read` | OCR only; `prebuilt-layout` adds tables at ~6× cost |
| `azure_openai_embedding_dimensions` | 3072 | `text-embedding-3-large` native |
| `ingest_max_docs_per_run` / `_batch_size` / `_workers` | 0 / 0 / 1 | batch + parallelism controls |
| `worker_sweep_interval_seconds` / `worker_sweep_reconcile` | 3600 / False | background sweep |

`llm_structured_temperature` defaults to **unset**, so structured/parsing calls use
the deployment's own default temperature; pin it if you want strictly deterministic
parsing. Answer generation is pinned at 0.2; paraphrase generation and voting use 0.7.

---

## 9. Known gaps and rough edges (honest list)

- **`answer_format="detailed"` is currently unreachable from the classifier.**
  `_FORMAT_TO_LEGACY` maps the v2 `output_format` values onto
  default/list/table/timeline, and `summary` is only produced for a
  single-document summarization. So the attachment-supplementation pull
  (`_supplement_attachments`, gated on `detailed`) never fires in production today —
  it is built and unit-tested, but effectively dormant until a mapping produces
  `detailed`.
- **Authority is a dead ranking key** — nothing writes `source_authority`, so it is
  a constant. It stays deliberately, as the seam for a corpus that starts stamping it.
- **The qa path has no author scope** (see §6 STEP A) — author-relevant content is
  found semantically, and exact author scoping lives on the catalog path only.
- **Numeric faithfulness is observe-only**; the claim-level verify is off by default.
- **Scoped summaries cap at 30 documents** (a two-level reduce would raise it).
- **`hybrid_use_sparse` is reserved, not implemented** — true sparse vectors need
  ingest-time writes; the keyword leg is the full-text stand-in.
- **Multi-tag scope collapses to one tag** (`RecordFilters.tag`); the planner takes
  the first of `tags`.
- **The Drupal crawl is per-run in-process serialized** — the one-run lock is
  process-local by design (a single private ingestion instance).

---

## 10. Quick file index (where to look)

| I want to understand… | Read |
|---|---|
| The two servers + shared wiring | `app/main.py`, `ingest_main.py`, `app_factory.py` |
| The query spine (route / cache / assemble / SSE) | `app/pipeline/query_pipeline.py` |
| SSE mechanics + the chat limiter | `app/api/chat.py` |
| Intent classification | `app/retrieval/query_processor.py`, `understanding/prompts.py` |
| Facet filters + relaxation policy | `app/retrieval/understanding/filters.py` |
| The retrieval engine | `app/retrieval/retriever.py`, `search/strategies.py` |
| Search primitive + mandatory filter | `app/retrieval/hybrid_search.py` |
| Fusion / banded rerank / volatility / context | `app/retrieval/{fusion,reranker,volatility,context_builder}.py` |
| Catalog "database" tools | `app/retrieval/structured/{planner,tools,entities,filters,resolve,answerer}.py` |
| The prompt text describing the catalog | `app/retrieval/catalog_prompt.py` |
| Answer generation, two-block structure, faithfulness | `app/generation/{answerer,prompts,sections,faithfulness}.py` |
| Scoped summarization | `app/pipeline/summarize.py`, `app/retrieval/scoped_retrieval.py` |
| Semantic cache + partitioning | `app/cache/{semantic_cache,cache_keys}.py` |
| Catalog storage, schema, theme map | `app/catalog/{schema,state,queries,theme_taxonomy,enrichment,log}.py` |
| Ingestion orchestration + batching | `app/ingestion/pipeline.py` |
| Extraction (routing, OCR, tables, cleanup) | `app/ingestion/extractors/*` |
| Chunking | `app/ingestion/chunking/*` |
| Change detection | `app/ingestion/change_detection/{files,drupal,base}.py` |
| Ingest-time abstracts | `app/ingestion/enrich.py`, `enrich_backfill.py` |
| Dates (LLM-supplied bounds) | `app/core/dates.py` |
| Infra clients | `app/core/clients/*` |
| Settings + every tuning knob's rationale | `app/config.py` |
| End-to-end ingestion harness | `app/local_tests/run_ingestion_test.py` |
| The widget (and the mirrored section parsing) | `ui/script.js` |

---

## 11. Glossary

- **RAG** — retrieve relevant text, feed it to an LLM, generate a grounded answer.
- **Multi-label intent** — a query can carry several intents at once (e.g.
  `database` + `qa`), with terminal labels exclusive.
- **Capabilities** — the detected intent labels as the router reads them, to decide
  a combined (catalog + content) answer.
- **Database capability / planner** — the catalog (MySQL) path: a plan of tool calls
  (count / list / lookup / aggregate / list_themes / resolve_entity) returning
  deterministic, rendered answers.
- **Entity Registry** — maps a content-type name (bundle) to its query shape;
  adding a type is a data change.
- **Scope Resolver** — the one place free-text author/theme/tag names are
  canonicalized and dates parsed before they reach SQL.
- **Terminal vs fall-through** — a catalog failure that *is* the answer ("no author
  matching 'X'", "which did you mean?") versus one that hands the turn to semantic
  search.
- **Parent-expand** — search small child chunks, hand the LLM the larger parent.
- **Breadcrumb** — `title › heading` prefixed to a child's embedded text only.
- **RRF** — Reciprocal Rank Fusion: merge ranked lists by `Σ 1/(k+rank)`.
- **Banded ranking** — relevance decides across bands; completeness, then recency,
  then authority decide within one.
- **Volatile topic** — a query about something with a shelf life, which widens the
  relevance band so recency fires more often.
- **Facet relaxation** — retry a zero-result pull without the LLM-guessed facets,
  keeping the user's date scope.
- **Segregated context** — website blocks lead, PDFs follow under their own budget.
- **Two-block answer** — `<website_answer>` then `<pdf_answer>`, only when the
  context genuinely mixes both source kinds.
- **CRAG** — Corrective RAG: detect weak retrieval, reformulate, re-retrieve once.
- **Combined answer** — a deterministic catalog section prefixed onto a grounded
  content answer.
- **Catalog fallback** — offering what the catalog lists when retrieval grounded
  nothing, explicitly framed as *not* the substance asked for.
- **Fail-open** — degrade gracefully on component failure instead of erroring.
- **ACL MatchAny** — a chunk is visible if any of its `acl` values is in the
  caller's groups.

---

*Verified against the code at commit `b9c8f38` (branch `main`, August 2026).
Where an older per-layer doc disagrees with this one, trust the code and then this
guide.*
