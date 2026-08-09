# Ingestion Pipeline — Implementation Report

Based on the code after the local-PDF-pipeline removal (2026-08-09). Everything below describes what the code does today; §9 lists where the surrounding docs disagree with it.

> **Drupal is the only source.** The filesystem PDF scan (`PDF_SOURCE_DIRS`), the
> `POST /ingest/pdf` upload route, `GET /source/{id}` and the `indexer --pdf` CLI
> were all removed. PDFs still flow through the pipeline in volume — they just
> arrive as Drupal **attachments** and in-body links rather than off local disk.
> PDF *extraction* (PyMuPDF, Azure OCR, Camelot, normalization) is untouched.

---

## 1. Overall Architecture & Flow

### Two servers, one codebase

| Process | Entry point | Role |
|---|---|---|
| Ingestion server | `app/ingest_main.py` | Background sweep loop + `/ingest/*`, `/reindex`, `/ingest/log` routes |
| Retrieval server | `app/main.py` | `/chat`, `/search` — reads Qdrant + MySQL, never writes them |
| CLI | `python -m app.ingestion.pipeline [--bundle B] [--reconcile]` | Same orchestration, run manually |

`app/ingest_main.py:19` starts `start_sweep_scheduler()`, which runs `app/workers/scheduler.py:11 _sweep_loop` forever: `sweep()` → prune semantic cache → prune ingest log → sleep `worker_sweep_interval_seconds` (default **3600s**). The first sweep runs immediately at boot.

`app/workers/tasks.py sweep()` = `ingest_drupal(reconcile=worker_sweep_reconcile)` (default `False`), returning `{"drupal": {...}}`.

### The pipeline stages

```
                    ┌─────────────────── CHANGE DETECTION ───────────────────┐
Drupal JSON:API ──► detect_drupal_changes()
                                              │
                                              ▼
                                    Iterator[ChangeRecord]
                                              │
                          ┌───────────────────┴───────────────────┐
                          │  pipeline._run(records, build_doc)    │
                          │  (1 crawler thread, N worker threads) │
                          └───────────────────┬───────────────────┘
                                              ▼
                                    pipeline._handle(record)
                                              │
        DELETED ──► delete_document() + state.delete()      [stop]
        UNCHANGED ─► (nothing to do)                        [stop]
        NEW/CHANGED ▼
                        build_doc(record)          ── EXTRACTION
                        ├─ Drupal node   → canonical.from_drupal_record()
                        └─ Drupal PDF    → attachment.build_attachment_doc() → extract_pdf()
                                              ▼
                                   CanonicalDocument
                                              │
                        doc.ensure_content_hash()   (SHA-256 of body text only)
                                              │
                        _enrich(doc, hash)          (optional LLM abstract, cached)
                                              │
                   content_changed(record, hash)? ──no──► persist state (indexed=False)
                                              │              + refresh_document_title()
                                             yes
                                              ▼
                        chunk_canonical(doc)        ── CHUNKING (parent/child)
                                              ▼
                        index_chunks(chunks)        ── EMBED children + UPSERT to Qdrant
                                              ▼
                        delete_document(id, keep_ids=new)   ── swap out old version
                                              ▼
                        state.upsert(StateRecord)   ── MySQL catalog + facet rows
                                              ▼
                        ingest_log.record(LogEntry) ── MySQL audit row
```

### Key modules

| Stage | Module |
|---|---|
| Change detection | `app/ingestion/change_detection/{base,drupal}.py` |
| Drupal crawl | `app/ingestion/extractors/drupal_extractor.py` |
| PDF extraction | `app/ingestion/extractors/{pdf_extractor,pymupdf_local,camelot_tables,text_normalize}.py` |
| Attachment download | `app/ingestion/extractors/attachment.py` |
| Canonicalization | `app/ingestion/canonical.py` → `app/core/models/document.py` |
| Enrichment | `app/ingestion/enrich.py` + `app/catalog/enrichment.py` |
| Chunking | `app/ingestion/chunking/{__init__,segmenter,packer,classifier,config,models,payload}.py` |
| Embed + index | `app/ingestion/indexer.py`, `app/core/clients/{embeddings,vector_store}.py` |
| Catalog (MySQL) | `app/catalog/{state,schema,log,dead_links,enrichment,theme_taxonomy,db}.py` |
| Orchestration | `app/ingestion/pipeline.py`, `app/workers/{tasks,scheduler}.py`, `app/api/ingest.py` |

### Concurrency model

- `pipeline.py:33 _run_lock` — a **process-local** `threading.Lock`. One corpus-wide run at a time; a second raises `IngestBusyError` → HTTP 409 or a logged sweep skip. Two *processes* (CLI while the server runs) are **not** protected.
- `ingest_workers` (default **1**). When > 1, `pipeline.py:352` runs one single-threaded crawler feeding a bounded `ThreadPoolExecutor`; each worker does the full download → extract → embed → upsert → MySQL write for one document. Backpressure caps in-flight futures at `workers * 2`.
- Throttles: `ingest_max_docs_per_run` (0 = unlimited), `ingest_batch_size` + `ingest_batch_pause_seconds`. The budget only counts "worked" outcomes (`indexed`, `deleted`, `skipped`, `error` — `pipeline.py:259`), and never stops mid-node (attachment records are exempt at `pipeline.py:318`).

---

## 2. Drupal Data Retrieval

### Endpoint and auth

Base: `drupal_jsonapi_base`, default `https://teriin.org/jsonapi`. **Anonymous GET only** — no auth header. Header: `Accept: application/vnd.api+json` (`drupal_extractor.py:19`).

Session (`drupal_extractor.py:237 _build_session`): `urllib3.Retry(total=drupal_max_retries (3), backoff_factor=1.0, status_forcelist=(429,500,502,503,504), allowed_methods={"GET"}, respect_retry_after_header=True)`. Timeout `drupal_request_timeout` = 60s. Page size `drupal_page_size` = 50.

### What is crawled

Three entity types, all through `/jsonapi/{entity_type}/{bundle}`:

**`node`** (`DEFAULT_BUNDLES`, `drupal_extractor.py:44`) — 16 bundles:
`article, page, research_papers, completed_projects, feature_articles, ongoing_projects, news, events, press_release, policy_brief, videos, infographics, services, report, people, carousel`

**`taxonomy_term`** (`DEFAULT_TAXONOMIES`, `drupal_extractor.py:25`) — 13 vocabularies:
`themes, extra_pages, regional_centre` (crawled for their `description` prose) plus `tags, partners, programs_units, related_terms, stakeholders, division, division_areas, region, language` (crawled mostly for names).

**`block_content`** (`DEFAULT_BLOCKS`) — `basic` only.

### Query construction (`drupal_extractor.py:164 iter_bundle_records`)

```
GET {base}/{entity_type}/{bundle}
  ?page[limit]=50
  &sort=changed                     # ascending — always, from the crawler
  &include=field_a,field_b,...      # auto-discovered, see below
  &filter[status]=1                 # when published_only
  &filter[changed][condition][path]=changed
  &filter[changed][condition][operator]=>=
  &filter[changed][condition][value]=<high-water unix ts>
```

Pagination follows `links.next.href` (`_iter_pages`, line 252) until absent.

**Ascending sort is deliberate** (`change_detection/drupal.py:88`): the high-water mark `MAX(changed_mark)` then only ever covers documents actually processed, so a capped/interrupted run resumes correctly. Newest-first would strand older documents behind the filter permanently.

**`>=` not `>`** on the changed filter (line 200 comment) so a record edited in the same second as the stored mark isn't skipped; boundary records resolve to UNCHANGED via fingerprint.

### Relationship discovery — a notable weak point

`drupal_extractor.py:277 _discover_relationship_fields` fetches **one record** (`page[limit]=1`) per bundle and takes every relationship key starting with `field_` as the `include=` list. For `taxonomy_term` it additionally forces `parent`.

Consequence: a `field_*` that happens to be absent/empty on that one sampled record is never included, so its target entities never appear in `included` — the referenced file is silently skipped in `_resolve_files` (entity lookup returns `None`) and the ref lands with `label=None`. Which record is sampled depends on default ordering, so coverage can vary run to run.

### Raw JSON:API shape received

```json
{
  "data": [
    {
      "type": "node--report",
      "id": "9a3f...-uuid",
      "attributes": {
        "drupal_internal__nid": 4821,
        "title": "TERI Energy & Environment Data Diary 2023",
        "created": "2023-11-02T06:14:22+00:00",
        "changed": "2024-01-18T09:41:05+00:00",
        "status": true,
        "path": { "alias": "/reports/teddy-2023", "pid": 1, "langcode": "en" },
        "body": {
          "value": "<p>The 2023 edition ...<a href=\"/files/teddy-2023.pdf\">Download</a></p>",
          "processed": "<p>The 2023 edition ...<a href=\"/files/teddy-2023.pdf\">Download</a></p>",
          "summary": "", "format": "full_html"
        },
        "field_publication_year": "2023",
        "field_isbn": "978-93-xxxx"
      },
      "relationships": {
        "field_theme":  { "data": [ { "type": "taxonomy_term--themes", "id": "t-uuid-1" } ] },
        "field_report": { "data": { "type": "file--file", "id": "f-uuid-1",
                                    "meta": { "description": "Full report PDF" } } },
        "field_author": { "data": [ { "type": "node--people", "id": "p-uuid-1" } ] }
      }
    }
  ],
  "included": [
    { "type": "taxonomy_term--themes", "id": "t-uuid-1",
      "attributes": { "name": "Energy Access" } },
    { "type": "file--file", "id": "f-uuid-1",
      "attributes": { "filename": "teddy-2023.pdf", "filemime": "application/pdf",
                      "uri": { "value": "public://2023-11/teddy-2023.pdf",
                               "url": "/sites/default/files/2023-11/teddy-2023.pdf" } } },
    { "type": "node--people", "id": "p-uuid-1",
      "attributes": { "title": "A. Researcher" } }
  ],
  "links": { "next": { "href": "https://teriin.org/jsonapi/node/report?page%5Boffset%5D=50..." } }
}
```

### Filters and exclusions applied at retrieval

| Filter | Where | Effect |
|---|---|---|
| `filter[status]=1` | query param | Unpublished nodes excluded (default `published_only=True`) |
| `changed >= high-water` | query param | Node bundles only; taxonomies/blocks are **full-fetched every run** |
| Boilerplate blocks | `change_detection/drupal.py:123` | `block_content` with body < `drupal_block_min_chars` (200) **and** no PDF → dropped entirely |
| Non-PDF attachments | `drupal_extractor.py:375` | Non-`application/pdf` file refs skipped; `.doc/.docx/.xls/.xlsx/.ppt/.pptx/.csv` get a `WARNING` so the miss is visible |
| External in-body PDFs | `drupal_extractor.py:442` | Skipped unless `drupal_ingest_external_pdfs=true`; internal = `teriin.org` / `teri.res.in` / relative |
| Dead links | `change_detection/drupal.py:171` | Attachments the site previously answered 4xx for are not even yielded, while their fingerprint is unchanged |
| Per-run PDF dedup | `change_detection/drupal.py:155` | `seen_pdf` set keyed by file uuid |
| `virtual` / `missing` refs | `drupal_extractor.py:522` | Dropped — never resolvable |

---

## 3. Content Processing & Transformation

### `_build_record` (`drupal_extractor.py:305`)

Produces a `DrupalRecord(uuid, bundle, nid, title, url, body, created, changed, metadata, files, refs)`.

**Title** (line 327): `attributes.title` → `.name` (taxonomy) → `.info` (block) → `""`.
**URL** (line 544): `{site}{attributes.path.alias}`, or `None` if no alias. Blocks have no URL.
**Site base**: `drupal_jsonapi_base.split("/jsonapi")[0]`.

### Attribute partitioning (`drupal_extractor.py:459 _partition_attributes`)

Every attribute is classified into **body**, **metadata**, or **dropped**:

| Attribute shape | Destination |
|---|---|
| `dict` with `processed`/`value` (formatted text) — *any key, not just `field_*`* | **body**, via `_html_to_text` |
| `field_*` `bool` / `int` / `float` | metadata |
| `field_*` `str` ≤ 255 chars (`LONG_TEXT_THRESHOLD`) | metadata |
| `field_*` `str` > 255 chars | **body**, via `_html_to_text` |
| `field_*` list of scalars | metadata |
| Any non-`field_*` scalar (`langcode`, `sticky`, `promote`, `revision_*`, …) | **dropped** |
| `field_*` list of dicts / nested objects | **dropped** |

Body parts are sorted so `body` comes first (line 490), then joined with `\n\n`.

### HTML → text (`drupal_extractor.py:553 _TextExtractor`)

A `html.parser.HTMLParser` subclass, not BeautifulSoup. It deliberately preserves things a naive strip loses:

- `<a href="X">text</a>` → `text (X)`; in-page anchors (`#…`) and `javascript:` skipped
- `<img alt="X">` → `[image: X]`
- `<iframe src="X">` → `[embedded: X]`
- `<td>`/`<th>` → ` | ` separators (tables stay pipe-delimited)
- Block tags (`p, div, li, tr, h1-h6, …`) → newline
- `<script>`/`<style>` contents dropped
- Final pass collapses intra-line whitespace and squeezes blank-line runs

### Relationship resolution (`drupal_extractor.py:494 _resolve_relationships`)

Walks `field_*` relationships plus `parent` (taxonomy tree). For each target it produces an `EntityRef(field_name, uuid, entity_type, label)` where `label` = `attributes.name` → `display_name` → `title` from the `included` entity, or `None` when not embedded. Refs are kept even without a label; `metadata[field_name] = [labels…]` is written only when at least one label resolved. `file--file` targets are excluded here (handled by `_resolve_files`).

### Facet routing (`canonical.py:97 drupal_facets`)

Substring heuristics over the metadata dict, plus vocabulary-based routing:

| Facet | Rule |
|---|---|
| `categories` (themes) | `_union_list(metadata, "theme")` **plus** any `EntityRef` whose vocabulary ∈ `CATEGORY_VOCABULARIES = ("themes",)` — vocabulary routing beats field-name guessing |
| `tags` | `_union_list(metadata, "tag", "keyword")` |
| `authors` | `_pick_list(metadata, "author")` — **first matching field only**, not a union |

Fields named `category`/`area`/`division` are explicitly **not** themes (comment at `canonical.py:8`); they survive only in `raw_meta`.

`app/ingestion/field_audit.py` is a diagnostic CLI that samples every source and reports which fields land where under exactly these rules.

### The canonical document (`canonical.py:126 _drupal_document`)

```python
CanonicalDocument(
    document_id = uuid,                       # the Drupal node/term UUID
    source_type = "website",
    title       = title.strip() or None,
    sections    = [CanonicalSection(text=body, order=0)],   # ONE section, no pages
    source_url  = url,
    article_uuid= uuid,
    file_url    = first attached PDF's URL,
    tags/categories/authors = facets,
    published_at= created,                    # `created`, not `changed`
    extra       = {"bundle":…, "nid":…, "changed":…},
    entity_refs = refs,                       # catalog + payload term_ids
    raw_meta    = dict(metadata),             # MySQL JSON column only
    file_links  = [FileLink(uuid, origin, url, filename), …],
)
```

**Metadata destinations are strictly separated** (`document.py:74`):
- `entity_refs` → `term_ids`/`theme_ids` in the Qdrant payload (via `_meta_from_canonical`)
- `raw_meta` → MySQL `documents.raw_meta` JSON column **only** — never reaches Qdrant
- `file_links` → MySQL `documents_attachment` rows
- `extra` (`bundle`, `nid`, `changed`) → merged verbatim into the Qdrant payload (`payload.py:50`)

### Content hash (`document.py:95`)

`SHA-256(full_text())` — **body text only**. Title and all metadata are deliberately excluded so the hash is reproducible from source bytes; otherwise every sweep would re-version and re-embed the whole corpus. A title-only edit therefore yields `unchanged_content`, and the title is carried forward by `state.upsert` + `refresh_document_title` (one Qdrant `set_payload`, no re-embed).

---

## 4. PDF Handling

### One source, one extractor

| Source | `source_type` | `document_id` | Entry |
|---|---|---|---|
| Drupal `field_*` file attachment | `pdf_attachment` | the `file--file` UUID | `attachment.py:84 build_attachment_doc` |
| Drupal in-body `<a href="…pdf">` link | `pdf_attachment` | `inbody:<sha1(abs_url)>` | same |

Both call `extract_pdf(content: bytes, filename: str) -> ExtractionResult`. There is
no longer any path that reads a PDF from local disk.

### Download (`attachment.py:23 fetch_attachment`)

For `http://` URLs it tries the `https://` variant **first** (teriin.org stopped answering on port 80; plain http hangs until timeout), falling back to the original. Returns `(content, url_that_succeeded)` — the successful URL becomes `file_url` in the payload. Uses the run-wide shared `requests.Session` so downloads reuse the connection pool.

### Routing — `EXTRACTION_MODE` (default `hybrid`)

```
extract_pdf()                                    pdf_extractor.py:427
  ├─ local_only  → _local_extract()              PyMuPDF text, all pages
  ├─ azure_only  → _azure_with_fallback()        whole doc to Azure; local fallback
  └─ hybrid      → _hybrid_extract()             per-page routing  ◄── default
```

**Hybrid, step by step** (`pdf_extractor.py:346`):

1. `pymupdf_local.classify_document(content)` opens the PDF once with PyMuPDF (`fitz`) and produces one `PageSignal` per page: `page_number`, `char_count`, `scanned`, `has_table`, and **the page text itself** (captured here so local pages never re-parse).
   - `scanned = len(text) < pdf_scanned_char_threshold` (default **100** chars)
   - `has_table`: (a) `page.find_tables()` — the primary, always-on signal; (b) ruled-grid heuristic, requires ≥ `pdf_table_min_grid_lines` distinct horizontal **and** vertical rules — **off by default**; (c) borderless whitespace-column alignment — **off by default**. Both extras are off because on heavily-designed PDFs they fire on nearly every page and over-route everything to Azure.

2. `PageSignal.route` (`pymupdf_local.py:58`) — **scanned wins over table**, because Camelot cannot read an image:
   ```
   scanned   → "azure"
   has_table → "camelot"
   else      → "local"
   ```

3. Per-route extraction:
   - **azure** → `_ocr_pdf(content, azure_pages)` sends the whole byte stream with `pages="1,4-7"` to Azure Document Intelligence (`azure_document_intelligence_model`, default **`prebuilt-read`** — OCR text only, no table structure). Markdown output is requested **only** if the model name contains "layout", because `prebuilt-read` rejects `output_content_format` and the whole call would fail. Page text is sliced out of the flat `result.content` using each page's `spans` offsets. Tables without a bounding region are attached to the first emitted page rather than dropped (`pdf_extractor.py:214`).
   - **camelot** → `camelot_tables.extract_tables(content, table_pages)`. Camelot needs a file path, so the PDF is re-saved through PyMuPDF with `encryption=PDF_ENCRYPT_NONE` to a temp file — this strips owner-password permission flags that would make Camelot's backend refuse the document outright. Flavor `camelot_flavor` (default `lattice`); pages that produce nothing get a second pass with `stream`. Degenerate 1-row/1-col matches are discarded. Table markdown is **appended after the page's PyMuPDF prose** (`_merge_table_text`) into a single page text, because the chunker reads page text only, never the separate `tables` list.
   - **local** → the text already captured during classification.

4. Missing pages are backfilled as `PageContent(text="", extracted_via=EMPTY)`; pages are stitched in `1..total` order.

### Failure/degradation matrix

| Situation | Behaviour |
|---|---|
| Azure not configured (no endpoint/key) | `_di_client()` returns `None`; one WARNING; those pages fall back to **PyMuPDF text** — which for a scanned page is ~empty |
| Azure call raises | `logger.exception`, returns `{}`, same local fallback |
| `classify_document` raises | Whole document sent to Azure (`_azure_with_fallback`); if Azure also unavailable → local text |
| Camelot not installed | WARNING; flagged pages keep only their PyMuPDF text |
| Camelot forbidden by PDF permissions | Detected via `playa.exceptions.PDFTextExtractionNotAllowed`, one WARNING, not a traceback |
| Camelot temp file locked (Windows `WinError 32`) | `gc.collect()` then retry `os.remove` — Camelot's backend holds a handle until finalization |
| Encrypted / corrupt PDF | `fitz.open` raises → propagates out of `extract_pdf` → caught by `pipeline._run.handle` → status `error` |

### Post-extraction normalization (`pdf_extractor.py:446` → `text_normalize.py`)

Applied to **every** page, in place, before the result is returned:

Per page (`normalize_page_text`):
1. Ligature repair — literal glyphs (`ﬁ ﬀ ﬂ ﬃ ﬄ ﬅ ﬆ`) and a curated list of dropped-ligature words (`"e cient"` → `"efficient"`, ~45 entries, deliberately only non-lexical broken forms)
2. Subscript repair — `"MtCO,"` → `"MtCO2"`, `"CO,"` → `"CO2"` only when followed by `emissions|capture|intensity|…`; `"H,"` → `"H2"` before `DRI|blend|injection|…`
3. Strip HTML comments (`<!-- PageBreak -->`, `<!-- PageNumber="22" -->` — Azure Layout artifacts)
4. Unwrap `<figure>` blocks
5. Drop garbage tables — wide (≥6 col) markdown tables that are ≥50% empty cells or have one phrase repeated across ≥40% of cells (infographics Azure rendered as tables)
6. Drop single-cell page-number bars (`| ii |`)
7. Drop "number soup" lines and contiguous chart data regions (`pdf_drop_number_soup`, default **true**) — a block of bare-number lines interleaved with short labels, ≥4 numbers and ≥40% numeric

Cross-page (`strip_running_lines`, `pdf_running_header_min_fraction` default **0.5**): short (≤12 word), non-table lines that recur on ≥ half the pages (min 3, min 4 pages) are treated as running headers/footers and removed everywhere. Detection joins up to 3 consecutive candidate lines into a letters-only key, so a footer fragmented differently per page still matches.

### Canonicalization (`canonical.py:66 from_pdf`)

**One `CanonicalSection` per non-empty page**, `page_start = page_end = page.page_number`, `order = enumeration index`.

```python
CanonicalDocument(
    document_id = <as above>,
    source_type = "pdf" | "pdf_attachment",
    title       = result.source (= the filename)  unless overridden,
    sections    = [ CanonicalSection(text=page.text, page_start=n, page_end=n, order=i), … ],
    pdf_id      = document_id,
    pdf_path    = <local path> / omitted for attachments,
)
```

For **attachments** (`attachment.py:124`) the overrides add: `title = file.description or node.title or filename`, `source_url = node.url`, `file_url = fetched_url`, `linked_article_uuid = node.uuid`, `published_at = node.created`, `extra = {"bundle": node.bundle}`, plus the node's `entity_refs` and full `drupal_facets(...)` — **an attached PDF inherits its node's themes/tags/authors**, so theme-scoped retrieval reaches the PDF content.

### PDF limitations in the current implementation

- **No PDF document metadata is read.** The XMP / Info dictionary (Title, Author, Subject, CreationDate) is never touched. This no longer costs much: an attachment inherits its node's title, themes, tags, authors and date, so nothing depends on the PDF's own metadata.
- **`ExtractionResult.metadata` is discarded.** `extraction_mode`, `route` (`"azure+camelot+local"`), `page_signals` (which pages went where) and `engine` are populated and logged, then dropped — never persisted to MySQL or Qdrant. You cannot query "which documents were OCR'd".
- **Scanned tables are flattened.** With the default `prebuilt-read`, a scanned page carrying a table is OCR'd as prose. Structure requires switching to `prebuilt-layout` (~6× cost).
- **No page or size limit on attachment downloads.** `fetch_attachment` reads the whole response into memory with no cap — a very large PDF on the site is ingested at whatever size it is.
- **A fully scanned PDF with Azure unconfigured indexes as an empty document** and is then pinned there — see §8 and §11.

---

## 5. Chunking

`chunk_canonical(doc)` (`chunking/__init__.py:236`) is the single entry point used by the pipeline.

### Config selection

```python
if doc.is_paginated:                                    # any section has page_start
    n_pages = count of sections with a page number
    config = config_for("small_pdf" if n_pages <= 10 else doc.source_type)
else:
    config = config_for(doc.extra.get("bundle") or doc.source_type)
```

So **PDFs key off page count / source type; Drupal content keys off its bundle** (falling back to `source_type` = `"website"`).

Presets (`chunking/config.py:25`), tokens via `tiktoken` `cl100k_base`:

| Preset | child target | child max | child min | overlap | parent target | parent max |
|---|---|---|---|---|---|---|
| base (fallback) | 400 | 512 | 120 | 60 | 1800 | 2400 |
| `pdf`, `pdf_attachment`, `manual` | 450 | 560 | 120 | 60 | 2000 | 2600 |
| `research_papers` | 480 | 560 | 120 | 48 | 2000 | 2600 |
| `policy_brief` | 400 | 512 | 120 | 60 | 1800 | 2400 |
| `report` | 420 | 540 | 120 | 60 | 1900 | 2500 |
| `article`, `website`, `news`, `events`, `page`, `people`, `videos`, `services`, `press_release`, `infographics`, `completed_projects`, `ongoing_projects`, `feature_articles` | 380 | 480 | 120 | 40 | 1600 | 2200 |
| `small_pdf` (≤10 pages) | 400 | 512 | 120 | 50 | **100 000** | **100 000** |

`small_pdf`'s enormous parent budget means a short PDF becomes **one parent** holding the whole document.

Bundles not in the table (e.g. `carousel`, or any taxonomy vocabulary crawled as `taxonomy_term:themes`) fall through `config_for` to `_BASE`.

If `tiktoken` is unavailable, `Encoder` (`packer.py:18`) degrades to a **~4 chars/token heuristic** with one warning — all budgets then become approximate.

### Pipeline inside the chunker

```
pages/text
  → blocks_from_text(text, page)      segmenter.py:129   typed blocks
  → assemble_sections(blocks)         segmenter.py:190   heading owns following blocks
  → merge_small_sections(...)         segmenter.py:238   < child_min_tokens folded into prev
  → for each section:
        pack(blocks, parent budgets)  packer.py:115      → parent windows
        coalesce_windows(...)         packer.py:139      absorb undersized windows
        pack(parent_blocks, child budgets) → child windows
        coalesce_windows(...)
        apply_overlap(texts, overlap) packer.py:180      prefix carry-over
  → Chunk objects
```

**Block typing** (`segmenter.py:129`): four kinds — `text`, `code` (``` / ~~~ fences), `table` (≥2 consecutive lines with ≥2 `|` each), `heading`.

**Heading detection** (`segmenter.py:86 line_heading_level`) — for PDFs there are no real markdown headings, so headings are *inferred*:
- ATX `## Heading` → level = hash count
- Numbered `4.1 Scope` → level = dot count + 1, but only if the number is plausible (`≤3 dots`, no leading zero, head < 100 — so `0.35` and `250` don't qualify), the title starts with a letter, ≤8 words, and doesn't look like prose
- Labeled (`Section|Chapter|Article|Clause|Appendix|Annex|Part`) → level 2
- At a block start: >85% uppercase letters and ≤8 words → level 2; Title-Cased ≤8 words with no terminal punctuation → level 3
- Rejected as junk: dot leaders (`....`), any `|`, HTML-comment fragments, and OCR symbol-soup (<55% letters among non-space chars)

**Packing** (`packer.py:115`): oversized blocks are first split recursively on `\n\n` → `\n` → `". "` → `" "` → hard token split (code/table blocks get the *hard* cap, text gets the *target* as its cap). Then greedy accumulation: close the current window when adding the next atom would exceed `target` **and** the window already holds ≥ `min_fill`, or would exceed `max_tokens` outright.

**Overlap** (`packer.py:170 overlap_carry`): the last ~`overlap` tokens of the previous child, advanced past the first sentence boundary (regex `(?<=[.!?])\s+(?=[A-Z(])`) so the carry starts on a whole sentence. Applied to **children only** — parents do not overlap.

**Parent elision** (`chunking/__init__.py:138`): a parent that yields exactly **one** child is skipped; the child stands alone with `parent_chunk_id = None`. A parent is a near-duplicate of its only child, so emitting both wastes storage.

### Content type differences

| | Drupal node/term/block | PDF (local or attachment) |
|---|---|---|
| Input | one flat `full_text()` string | one `(page_number, text)` tuple per page |
| Page numbers | `None` throughout → no `page_number`/`page_range` in payload | tracked per block → `page_number`, `page_range` |
| Headings | from `_html_to_text` output — `<h1>`–`<h6>` become plain lines, so headings are **re-inferred** by the same heuristics, not read from HTML tags | inferred from text shape |
| Tables | pipe-delimited from `<td>`/`<th>` flattening → detected as `table` blocks | markdown from Camelot/Azure merged into page text → detected as `table` blocks |
| Config key | bundle name | `small_pdf` / `pdf` / `pdf_attachment` |

Note: `<h2>Foo</h2>` becomes a bare line `Foo`, which only becomes a heading if it passes the ≤8-word Title-Case / ALL-CAPS test. Drupal HTML heading structure is **not** preserved as structure.

### Section classification (`chunking/classifier.py:21`)

Each chunk's text is scanned for non-substantive shape, and the result stored as `section_type` so retrieval can exclude it:
- `toc` — ≥3 dot-leader lines and ≥30% of lines
- `references` — ≥4 citation lines (`http://`, `(2020)`, `Retrieved from`) and ≥40%
- `glossary` — ≥5 `ABBR – definition` lines and ≥40%
- otherwise `None`. Chunks with <4 lines are never classified.

### Chunk IDs

```python
uuid5(NAMESPACE_6f2a1d3e…, f"{document_id}|v{doc_version}|{suffix}")
#   suffix = "parent|{section_idx}.{part}"  or  "child|{child_index}"
```

**Version-scoped and deterministic.** This is what makes the index-new-then-delete-old swap safe: new points never collide with old ones, so the old version stays searchable until the swap, and a mid-index failure leaves it fully intact.

### Metadata attached to each chunk

`DocumentMeta` (copied field-by-field from the canonical doc at `chunking/__init__.py:197`): `document_id, source_type, title, source_url, file_url, pdf_id, pdf_path, article_uuid, linked_pdf_id, linked_article_uuid, tags, categories, authors, term_ids, theme_ids, language, tenant_id, acl, doc_version, is_current, published_at, extra`.

`term_ids` = UUIDs of all `taxonomy_term--*` refs; `theme_ids` = the subset in the `themes` vocabulary. These are **rename-proof filter keys** — the name lists (`categories`, `tags`) are display-only and can go stale between a CMS rename and the next payload refresh.

Per-chunk: `chunk_id, text, is_parent, embed_text, section_heading, section_type, parent_chunk_id, chunk_index, page_number, page_range, token_count, content_hash (SHA-256 of chunk text), has_table, table_markdown`.

---

## 6. Embedding

### Model

`app/core/clients/embeddings.py:9` — a single `@lru_cache`d LangChain `AzureOpenAIEmbeddings`:

```python
AzureOpenAIEmbeddings(
    azure_endpoint    = AZURE_OPENAI_EMBEDDING_ENDPOINT,
    api_key           = AZURE_OPENAI_EMBEDDING_KEY,
    api_version       = AZURE_OPENAI_EMBEDDING_API_VERSION,   # "2024-06-01"
    azure_deployment  = AZURE_OPENAI_EMBEDDING_MODEL,
    dimensions        = AZURE_OPENAI_EMBEDDING_DIMENSIONS,    # default 3072
)
```

`dimensions=3072` is `text-embedding-3-large`'s native size. The config comment notes 1536 (Matryoshka truncation) halves storage/search cost with negligible loss. **Must be left blank for `ada-002`, which rejects the parameter.**

### What is sent

`indexer.py:63`:

```python
children = [c for c in chunks if not c.is_parent]
vectors  = _embed_children([c.embed_text or c.text for c in children], batch_size=128)
```

**Only children are embedded. Parents get a zero vector** (`indexer.py:46`, `zero = [0.0] * dim`) and are retrieved by ID during parent-expand at query time.

`embed_text` (`chunking/__init__.py:158`) is:

```
"{title} › {section_heading}\n\n{chunk_text}"
```

The breadcrumb is capped at `breadcrumb_max_tokens = 32` via `enc.head(...)` so a runaway title or garbled OCR heading can't dominate a short chunk's embedding. It exists because headings are lifted out of the block stream into `Section.heading` and rejoined only onto *parent* text — without the breadcrumb, a child from page 30 of a report would be embedded with no trace of which report or section it came from.

**`embed_text` is never stored.** The payload's `chunk_text` is the bare `text` — what citations quote and what `content_hash` covers. The two are deliberately kept from drifting.

### Batching and retries

`_embed_children` (`indexer.py:18`) loops in slices of 128 (`batch_size`) calling `embeddings.embed_documents(batch)`.

There is **no application-level retry, backoff, or per-batch error handling.** Retries are whatever the underlying `openai` client does by default (`max_retries=2`, exponential backoff on 429/5xx). Anything that escapes propagates up through `index_chunks` → `_handle` → caught by `_run.handle` (`pipeline.py:300`), logged with a traceback, recorded as `status="error"` in `ingest_log`, and counted. **No state row is written**, so the document is retried on the next sweep.

### Dimension probing

`ensure_collection()` (`vector_store.py:31`) calls `embed_query("dimension probe")` **once** to size a new collection. `indexer.py:65 _probe_dim()` is the same call, used only if a chunk set somehow produced zero children.

There is no preprocessing beyond the breadcrumb — no lowercasing, no truncation guard against the model's 8191-token input limit (chunk budgets keep children well under it), no deduplication of identical chunk texts.

---

## 7. Ingestion & Indexing

### Two stores

| Store | What lives there |
|---|---|
| **Qdrant** (`qdrant_collection`, default `documents`) | Every chunk as a point: child = real vector, parent = zero vector; full payload |
| **MySQL** (`ingest_state_table`, default `documents` + child tables) | Ingest state / document catalog, facet rows, attachment links, audit log, enrichment cache, dead-link markers |

### Qdrant collection setup (`vector_store.py:31`)

Created lazily on first use: `VectorParams(size=<probed dim>, distance=Distance.COSINE)`. Then three payload indexes, all best-effort/idempotent:
- `published_at` → `DATETIME` (range filters)
- `term_ids` → `KEYWORD`
- `theme_ids` → `KEYWORD`

A process-local `_ensured_collections` set skips the round-trip after the first call. The set is populated only *after* success, so a transient failure retries.

### The final indexed record

`PointStruct(id=chunk_id, vector=…, payload=…)`. Payload built by `chunking/payload.py:10`, with **`None` / `""` / `[]` values stripped**:

```jsonc
{
  "chunk_id": "3c1b...-uuid5",
  "document_id": "9a3f...-uuid",
  "is_parent": false,
  "source_type": "pdf_attachment",
  "title": "TERI Energy & Environment Data Diary 2023",
  "section_heading": "4.1 Renewable Capacity",
  "section_type": null,                       // stripped when null
  "chunk_text": "…the bare chunk text…",
  "content_hash": "<sha256 of chunk_text>",
  "token_count": 438,
  "has_table": true,
  "table_markdown": "| State | MW |\n| --- | --- |\n| …",
  "doc_version": 3,
  "is_current": true,
  "tenant_id": "default",
  "acl": ["public"],
  "tags": ["renewables"],
  "categories": ["Energy Access"],
  "authors": ["A. Researcher"],
  "term_ids": ["t-uuid-1", "p-uuid-1"],
  "theme_ids": ["t-uuid-1"],
  "language": "en",
  "source_url": "https://teriin.org/reports/teddy-2023",
  "file_url": "https://teriin.org/sites/default/files/2023-11/teddy-2023.pdf",
  "published_at": "2023-11-02T06:14:22+00:00",
  "pdf_id": "f-uuid-1",
  "pdf_path": null,                           // stripped
  "article_uuid": null,                       // stripped (attachment: linked_article_uuid instead)
  "linked_article_uuid": "9a3f...-uuid",

  // children only:
  "parent_chunk_id": "8d2e...-uuid5",
  "chunk_index": 173,
  "page_number": 42,
  "page_range": [42, 43],

  // merged from DocumentMeta.extra:
  "bundle": "report",
  "nid": 4821,
  "changed": "2024-01-18T09:41:05+00:00",

  // stamped by the indexer:
  "created_at": "2026-08-09T10:12:44.881+00:00",   // setdefault — preserved on re-upsert
  "updated_at": "2026-08-09T10:12:44.881+00:00"
}
```

Upsert in batches of 128 (`indexer.py:72`).

### MySQL catalog (`app/catalog/schema.py`)

| Table | Key | Contents |
|---|---|---|
| `documents` | `document_id` (PK) | `source_type, source_key, bundle, entity_type, fingerprint, content_hash, doc_version, changed_mark, published_at, title, url, raw_meta (JSON), indexed_at, updated_at` (the legacy `size` / `mtime_ns` columns survive in the DDL but are no longer read or written) |
| `documents_author` | (doc, author) | one row per author, FK CASCADE |
| `documents_tag` | (doc, tag) | one row per tag, FK CASCADE |
| `documents_theme` | (doc, theme) PK | `theme_type ENUM('primary','sub')`, `parent`, `theme_group ENUM('main','other')` — classified by `theme_taxonomy.classify()` against `app/data.json` |
| `documents_attachment` | (file_uuid, doc) PK | `origin, url, filename` — node → PDF links |
| `documents_enrichment` | `content_hash` PK | `version, abstract, attempts, last_error` — **no FK**, survives a state reset |
| `documents_dead_link` | `document_id` PK | `fingerprint, url, status, attempts, first_seen` — **no FK** |
| `ingest_log` | `id` auto-inc | append-only audit: `run_id, document_id, source_type, source_path, source_url, bundle, tags, title, status, doc_version, chunks_indexed, fingerprint, content_hash, error_message, event_time` |

DDL is applied idempotently at the start of every run (`pipeline.py:263`), including in-place migrations: `migrate_renamed_facets` (`documents_category` → `documents_theme`, column too) and `migrate_theme_hierarchy` (adds `theme_type`/`parent`/`theme_group` + PK).

Writes go through `state.upsert` (`state.py:154`): one `INSERT … ON DUPLICATE KEY UPDATE` for the document row, then **delete-then-insert** of author / tag / theme / attachment rows, all in **one transaction**. `entity_type`, `raw_meta` and `indexed_at` use `COALESCE(VALUES(x), x)` so a NULL never clobbers a stored value.

### The update swap (`pipeline.py:237`)

```python
version = prior.doc_version + 1  (or 1)
doc.doc_version = version
new_chunks = chunk_canonical(doc)
chunks     = index_chunks(new_chunks)                        # 1. upsert new version
delete_document(document_id, keep_ids=[c.chunk_id …])        # 2. delete everything else
_persist(record, doc, content_hash, version, indexed=True)   # 3. catalog row + facets
```

Order matters: the document never disappears from search mid-swap, and a failure at step 1 leaves the previous version fully intact.

`delete_document` (`vector_store.py:84`) is a `FilterSelector` on `document_id`, with `must_not=[HasIdCondition(keep_ids)]`.

### Deletions

| Trigger | Handled? |
|---|---|
| Drupal node deleted / unpublished | ⚠️ **Only when `reconcile_deletes=True`.** Default is `False` (`worker_sweep_reconcile: bool = False`), so by default unpublished/deleted nodes stay searchable indefinitely. When on, `iter_node_uuids` enumerates live UUIDs per bundle and prior rows not in that set yield `DELETED` |
| Taxonomy term / block removed | ✅ under reconcile — these are full-fetched, so the yielded set *is* the live set |
| **Attachment PDF removed from a node** | ❌ **Never.** `detect_drupal_changes` yields `DELETED` only for `source_type="website"`. See §11 |
| Manual | `POST /reindex {"document_id": …}` → `tasks.reindex_document` deletes the Qdrant points and the state row, so the next sweep re-ingests from scratch |

`DELETED` handling (`pipeline.py:189`): `delete_document(id)` then `state.delete([id])` — the FK cascade removes all facet/attachment rows.

### Incremental vs full-refresh

**Incremental, on two levels** (`pipeline.py:196` and `:224`):

1. **Fingerprint match → skip extraction entirely.** Fingerprint = the node's `changed` ISO timestamp (node/term/block), the node's changed mark (attachment), or `inbody:<sha1(url)>` (in-body PDF).
2. **Fingerprint changed but content hash matches → `unchanged_content`.** The fingerprint is refreshed, the catalog row updated (picking up new title/facets/dates), `refresh_document_title` rewrites the payload title, and **nothing is re-embedded**.

Full-refresh paths: taxonomy/block sources are fetched in full every run (cheap, small); truncating `documents` or calling `/reindex` per document forces re-extraction.

### Direct ingest routes (`app/api/ingest.py`)

| Route | Behaviour |
|---|---|
| `POST /ingest/run` | Runs the Drupal crawl, with optional `bundles`/`reconcile` |
| `POST /ingest/article` | Either crawl `bundles`, or index an ad-hoc `{title, body, url, uuid, bundle}` via `from_drupal_export`. **Writes no state row** |
| `GET /ingest/log` | Recent audit rows, filterable |
| `POST /reindex` | `{"sweep": true}` or `{"document_id": …}` |

All corpus-wide routes go through `_run_exclusive`, which maps `IngestBusyError` → **HTTP 409**.

---

## 8. Error Handling & Edge Cases

### Failure containment, by layer

| Failure | Handling | Location |
|---|---|---|
| Drupal HTTP 429/5xx | `urllib3.Retry`, 3 attempts, backoff 1.0, honours `Retry-After` | `drupal_extractor.py:239` |
| Drupal bundle fetch fails after retries | `logger.exception`, **skip the whole bundle**, continue with the next | `drupal.py:189` |
| `_discover_relationship_fields` fails | WARNING, returns `[]` → no `include=` → relationships unresolvable for that bundle this run | `drupal_extractor.py:296` |
| Attachment download **4xx** | One WARNING (no traceback) + a `documents_dead_link` row → suppressed on future runs while the fingerprint holds; document skipped | `attachment.py:105` |
| Attachment download timeout / DNS / 5xx | Full `logger.exception` (so you can see which), document skipped, **retried next sweep** | `attachment.py:113` |
| Attachment body empty | WARNING, `return None` → status `skipped` | `attachment.py:115` |
| Azure OCR fails / unconfigured | WARNING; pages degrade to PyMuPDF text | `pdf_extractor.py:246`, `:276` |
| Camelot missing / forbidden / crashes | WARNING or exception log; page keeps only its PyMuPDF text | `camelot_tables.py:117` |
| `classify_document` raises | Whole document biased to Azure | `pdf_extractor.py:366` |
| `tiktoken` unavailable | WARNING once; ~4 chars/token heuristic | `packer.py:27` |
| **Anything in `_handle`** (extract, chunk, embed, upsert, MySQL) | `logger.exception`, `ingest_log` row with `status="error"` + message, tally `error++`, **no state row written** → retried next sweep | `pipeline.py:300` |
| `ingest_log` write fails | Caught inside `log.record`, logged, ingestion continues — "logging must not break ingestion" | `log.py:69` |
| `ensure_table` for log / enrichment fails | `logger.exception`, run continues without that table | `pipeline.py:266`, `:272` |
| `dead_links.load()` fails | WARNING, empty skip list — falls open to retrying everything | `drupal.py:41` |
| `dead_links.record()` fails | WARNING, link retried next run | `attachment.py:77` |
| Enrichment LLM fails | `record_failure` increments `attempts`; after `enrichment_max_attempts` (3) the document is `exhausted` and never retried at that version | `pipeline.py:146` |
| Enrichment infrastructure fails entirely | Caught, tally `enrich_error`, sweep continues without an abstract | `pipeline.py:173` |
| `refresh_document_title` fails | WARNING; stale display title heals on the next real reindex | `vector_store.py:148` |
| Sweep loop iteration fails | `logger.exception`, retry next interval | `scheduler.py:32` |
| Concurrent run attempt | `IngestBusyError` → 409 or a logged sweep skip | `pipeline.py:41` |

**Design principle throughout: fail open per document.** No single document can stop a sweep. There is **no dead-letter queue** — the failure record is the `ingest_log` row with `status="error"`, queryable via `GET /ingest/log?status=error`.

### Malformed / empty / duplicate / unsupported content

| Case | Behaviour |
|---|---|
| `build_doc` returns `None` (empty attachment, download failure) | status `skipped`, **no state row** → retried next sweep |
| Document with empty body | `sections=[]` → `full_text()=""` → `chunk_canonical` → 0 chunks → `index_chunks` returns 0 → **still recorded as `indexed`** with the hash of the empty string |
| Same in-body PDF linked from many nodes | De-duped per run by `seen_pdf`; fingerprint is URL-derived so it ingests once and inherits the **first-seen** node's facets |
| Boilerplate block (<200 chars, no PDF) | Dropped before yielding a record |
| Non-PDF attachment | Skipped; document types (`.docx`, `.xlsx`, …) get a WARNING so the miss is visible |
| Unresolvable relationship (`virtual`, `missing`) | Dropped |
| Theme value that is the literal string `"False"` / `"none"` / `"null"` | Dropped by `theme_taxonomy._NOT_A_THEME` (the catalog once held 404 such rows) |
| Over-long values | `ingest_log` clips everything (`log.py:28`); `state` clips facet values to 255 and themes to 255 — but **does not clip `source_key`, `title`, `url`, attachment `url`/`filename`** |

---

## 9. Current Implementation vs. Documented Design

`docs/ingestion.md` is broadly accurate on the pipeline's *shape* but has drifted on module layout and on a few claims. Concrete divergences:

| `docs/ingestion.md` says | Actually |
|---|---|
| §Embedding links **`app/ingestion/embedder.py`** | Does not exist. Embeddings live in `app/core/clients/embeddings.py` |
| §Embedding lists **`embed_query_cached(text)` — query embedding with a Redis cache** | No such function anywhere in `app/`. Only `embed_query` (uncached) and `get_embeddings` |
| §Canonical links **`app/core/models.py`** | It is a package: `app/core/models/{document,context}.py` |
| §Chunking: "convenience adapters **`chunk_pdf(...)`** and **`chunk_drupal_record(...)`**" | Neither exists. Only `chunk_canonical`, `chunk_pages`, `chunk_document`. (`chunk_pdf` survives only in a CLI `--help` string at `pdf_extractor.py:487`) |
| §Orchestration: pipeline "…upsert the manifest → **mirror a taxonomy-term record into `terms`**" | The term tables (`terms`, `term_aliases`, `documents_term`) were **retired** (`schema.py:13`). `_persist` only calls `_save_state`. Taxonomy UUIDs now live *only* in Qdrant payloads (`term_ids` / `theme_ids`) |
| §Theme rows: "…reaches the catalog through **`documents_term`** and `raw_meta`" | `documents_term` no longer exists — only `raw_meta` |
| §Drupal: crawling facet vocabularies "populate[s] the **`terms` catalog**"; "a run scoped with `--bundle` leaves `terms` empty and silently breaks theme grouping" | Stale — there is no `terms` table. Theme grouping now reads `documents_theme`, classified statically from `app/data.json` |
| §Manifest lists `state.**high_water()**`, `state.**keys()**`, `state.**iter_records()**`, `state.count_documents(...)`, `state.list_documents(...)` | `high_water`, `keys`, `iter_records` don't exist. `count_documents`/`list_documents` live in `app/catalog/queries.py` (imported as `from app.catalog import queries as state` by retrieval code) |
| §Workers: "exposed as **Celery tasks** with an inline fallback" | **No Celery anywhere.** `app/workers/tasks.py` is plain functions called in-process by the asyncio scheduler and the API routes. (`pipeline.py:32` also mentions "celery mode" in a comment) |
| §Orchestration: tally keys `{new, changed, unchanged, unchanged_content, indexed, deleted, skipped, error}` | `new` and `changed` are **never** tally keys — the tally counts `_handle`'s return values: `indexed`, `deleted`, `skipped`, `unchanged`, `unchanged_content`, `error`, plus `budget_stop` and `enrich_*` |
| §Inline upload "…and **bumps the corpus version so caches refresh**" | `upload.py` does no version bump and touches no cache |
| §PDFs: "All page text is normalized to expand standard ligature glyphs" | Understated — normalization also repairs dropped ligatures and CO₂/H₂ subscripts, strips HTML comments and `<figure>`s, drops page-number bars, garbage tables, number soup and chart regions, and strips cross-page running headers/footers |
| §Change detection: "detects deletes by comparing prior manifest keys" | True for Drupal *nodes/terms/blocks* under reconcile — but **not for attachments**, which are never reconciled |
| §Chunking config: gives only the base defaults (400/512/120/60, 1800/2400) | Ten bundle-specific presets exist; PDFs use 450/560 and `small_pdf` uses a 100 000-token parent |

Also unstated in the docs: the `documents_dead_link` table and its whole suppression mechanism (added in the two most recent commits), and the `carousel` bundle.

---

## 10. End-to-End Example

A Drupal `report` node with an attached PDF. This produces **two documents**.

### Stage 0 — Change detection

`detect_drupal_changes` loads priors, computes `high = MAX(changed_mark)` for `bundle="report"`, and crawls `/jsonapi/node/report?sort=changed&filter[changed]…>=…` ascending.

For the node in §2's raw JSON it yields two `ChangeRecord`s, **node first**:

```python
ChangeRecord(status=NEW, document_id="9a3f...-uuid", source_type="website",
             source_key="https://teriin.org/reports/teddy-2023",
             fingerprint="2024-01-18T09:41:05+00:00", bundle="report",
             changed_mark=1705570865, prior=None, payload=<DrupalRecord>,
             entity_type="node")

ChangeRecord(status=NEW, document_id="f-uuid-1", source_type="pdf_attachment",
             source_key="https://teriin.org/sites/default/files/2023-11/teddy-2023.pdf",
             fingerprint="2024-01-18T09:41:05+00:00",   # the NODE's changed mark
             bundle="report", changed_mark=1705570865, prior=None,
             payload=(<DrupalRecord>, <DrupalFile>), filename="teddy-2023.pdf")
```

### Stage 1a — The node document

`_build_record` → `DrupalRecord`:

```python
DrupalRecord(
  uuid="9a3f...-uuid", bundle="report", nid=4821,
  title="TERI Energy & Environment Data Diary 2023",
  url="https://teriin.org/reports/teddy-2023",
  body="The 2023 edition ...Download (/files/teddy-2023.pdf)",   # link destination preserved
  created="2023-11-02T06:14:22+00:00", changed="2024-01-18T09:41:05+00:00",
  metadata={"field_theme": ["Energy Access"], "field_author": ["A. Researcher"],
            "field_publication_year": "2023", "field_isbn": "978-93-xxxx"},
  files=[DrupalFile(url=".../teddy-2023.pdf", filename="teddy-2023.pdf",
                    description="Full report PDF", uuid="f-uuid-1", origin="attachment")],
  refs=[EntityRef("field_theme","t-uuid-1","taxonomy_term--themes","Energy Access"),
        EntityRef("field_author","p-uuid-1","node--people","A. Researcher")],
)
```

`from_drupal_record` → `CanonicalDocument`:

```python
CanonicalDocument(
  document_id="9a3f...-uuid", source_type="website",
  title="TERI Energy & Environment Data Diary 2023",
  sections=[CanonicalSection(text="The 2023 edition ...", order=0)],   # 1 section, no pages
  source_url="https://teriin.org/reports/teddy-2023",
  article_uuid="9a3f...-uuid",
  file_url=".../teddy-2023.pdf",
  categories=["Energy Access"],        # from the themes-vocabulary ref
  tags=[], authors=["A. Researcher"],
  published_at="2023-11-02T06:14:22+00:00",
  extra={"bundle":"report", "nid":4821, "changed":"2024-01-18T09:41:05+00:00"},
  entity_refs=[…2 refs…],
  raw_meta={"field_theme":["Energy Access"], "field_publication_year":"2023", …},
  file_links=[FileLink("f-uuid-1","attachment",".../teddy-2023.pdf","teddy-2023.pdf")],
  content_hash="a1b2c3…",   # SHA-256 of the body text alone
)
```

`content_changed` → `True` (no prior). `doc_version = 1`.
`config_for("report")` → child 420/540/120/60, parent 1900/2500.
`chunk_canonical` → `chunk_document(full_text())` (not paginated) → say 1 section, 3 children + 1 parent.

**Chunk 0 (child):**
```python
Chunk(chunk_id="uuid5(NS, '9a3f...-uuid|v1|child|0')",
      text="The 2023 edition ...",
      embed_text="TERI Energy & Environment Data Diary 2023\n\nThe 2023 edition ...",
      is_parent=False, parent_chunk_id="uuid5(NS,'9a3f...-uuid|v1|parent|0.0')",
      chunk_index=0, page_number=None, page_range=None,
      token_count=412, content_hash="<sha256 of text>",
      section_heading=None, section_type=None, has_table=False)
```

`index_chunks` embeds the 3 children (`embed_text`) → 3072-dim vectors; the parent gets `[0.0]*3072`. 4 points upserted.

`state.upsert` writes `documents` + 1 `documents_author` row + 1 `documents_theme` row (`theme="Energy Access"`, classified by `theme_taxonomy` against `app/data.json` → likely `theme_type='sub'`, `parent='Energy'`, `theme_group='main'`) + 1 `documents_attachment` row.

### Stage 1b — The attachment document

`build_attachment_doc` GETs the PDF (`https://` preferred), then `extract_pdf(content, "teddy-2023.pdf")`:

```
classify_document → 180 PageSignals
  pages 1, 2 (cover/scan)      → scanned=True   → route "azure"
  pages 34, 91 (ruled tables)  → has_table=True → route "camelot"
  the other 176                → route "local"
```

- Azure `prebuilt-read` called once with `pages="1-2"`
- Camelot `lattice` on `"34,91"`; markdown appended after each page's PyMuPDF prose
- Remaining pages use the text captured during classification
- `_normalize_result` repairs ligatures/subscripts, drops chart-number regions, and strips the running footer that appeared on 140 of 180 pages

```python
ExtractionResult(source="teddy-2023.pdf",
                 pages=[PageContent(1, "…", OCR, []), …,
                        PageContent(34, "prose\n\n| State | MW |…", TEXT, [TableData…]), …],
                 metadata={"extraction_mode":"hybrid", "route":"azure+camelot+local",
                           "page_signals":{"pages":180,"azure":[1,2],
                                           "camelot":[34,91],"local":[3,…]}})
```
⚠️ **`metadata` is dropped from here on** — it never reaches the canonical document, MySQL or Qdrant.

`from_pdf(...)` → 180 sections (one per non-empty page), then attachment overrides:

```python
CanonicalDocument(
  document_id="f-uuid-1", source_type="pdf_attachment",
  title="Full report PDF",                       # file.description wins over node.title
  sections=[CanonicalSection(text="…", page_start=1, page_end=1, order=0), … 180 …],
  pdf_id="f-uuid-1",
  source_url="https://teriin.org/reports/teddy-2023",     # the NODE's page
  file_url="https://teriin.org/sites/default/files/2023-11/teddy-2023.pdf",
  linked_article_uuid="9a3f...-uuid",
  published_at="2023-11-02T06:14:22+00:00",      # the NODE's created date
  extra={"bundle":"report"},
  categories=["Energy Access"], authors=["A. Researcher"],   # inherited from the node
  entity_refs=[…node's refs…],
  content_hash="d4e5f6…",
)
```

180 pages > 10 → `config_for("pdf_attachment")` → the `pdf` preset (450/560/120/60, 2000/2600).
`chunk_pages` → ~412 children + ~86 parents.

**A child from page 42:**
```jsonc
{
  "chunk_id": "uuid5(NS, 'f-uuid-1|v1|child|173')",
  "document_id": "f-uuid-1", "is_parent": false,
  "source_type": "pdf_attachment", "title": "Full report PDF",
  "section_heading": "4.1 Renewable Capacity",
  "chunk_text": "…Installed renewable capacity reached…\n\n| State | MW |\n| --- | --- |\n| …",
  "has_table": true, "table_markdown": "| State | MW |…",
  "token_count": 447, "chunk_index": 173,
  "page_number": 42, "page_range": [42, 43],
  "parent_chunk_id": "uuid5(NS,'f-uuid-1|v1|parent|11.0')",
  "categories": ["Energy Access"], "authors": ["A. Researcher"],
  "theme_ids": ["t-uuid-1"], "term_ids": ["t-uuid-1", "p-uuid-1"],
  "source_url": "https://teriin.org/reports/teddy-2023",
  "file_url": "https://teriin.org/…/teddy-2023.pdf",
  "linked_article_uuid": "9a3f...-uuid",
  "published_at": "2023-11-02T06:14:22+00:00",
  "bundle": "report", "doc_version": 1, "is_current": true,
  "language": "en", "tenant_id": "default", "acl": ["public"],
  "created_at": "2026-08-09T10:12:44+00:00", "updated_at": "2026-08-09T10:12:44+00:00"
}
```

Embedded text = `"Full report PDF › 4.1 Renewable Capacity\n\n…Installed renewable capacity…"`.

### Stage 2 — Next sweep, node body edited

`changed` moves to `2024-03-02T…` → fingerprint differs → `CHANGED`. Body text differs → `content_changed` True → `doc_version = 2` → chunk ids become `uuid5(NS, "9a3f…|v2|child|0")` → new points upserted → `delete_document(id, keep_ids=<v2 ids>)` removes the v1 points → catalog row updated.

The **attachment's** fingerprint is the node's changed mark, so it too becomes `CHANGED` → the PDF is re-downloaded and re-extracted. Its content hash is unchanged → `unchanged_content` → fingerprint refreshed, **no re-embed**. (Cost: one full download + extraction per node edit, per attachment.)

---

## 11. Summary & Gaps

### Architecture at a glance

```
┌────────────────────────────┐
│ Drupal JSON:API            │
│ nodes · taxonomy · blocks  │
│ + their attached PDFs      │
└─────────────┬──────────────┘
              │ iter_bundle_records (changed-since high-water, oldest-first)
              ▼
      detect_drupal_changes                            change_detection/
              │
              ▼  Iterator[ChangeRecord]  (NEW|CHANGED|UNCHANGED|DELETED)
        ┌──────────────────────┐
        │ pipeline._run        │  _run_lock (process-local) │ ingest_workers pool
        └──────────┬───────────┘  ingest_max_docs_per_run / batch pause
                   ▼ pipeline._handle
     ┌─────────────┴──────────────┬──────────────────┐
     ▼                            ▼                  ▼
 DrupalRecord            fetch + extract_pdf    [DELETED]
 _html_to_text            hybrid router:         delete_document
 _partition_attributes    ├ scanned → Azure DI   state.delete
 _resolve_relationships   ├ table   → Camelot
 _resolve_files           └ else    → PyMuPDF
 _extract_inbody_pdfs     + text_normalize
     └──────────┬─────────────────┘
                ▼  CanonicalDocument  (sections, facets, refs, raw_meta)
       ensure_content_hash()  ──► content unchanged? ──► refresh title, persist, STOP
                ▼ changed
       _enrich() ──► documents_enrichment (LLM abstract, off by default)
                ▼
       chunk_canonical()   segmenter → packer → classifier
                ▼  parent/child Chunks, uuid5(doc|version|suffix)
       index_chunks()      embed CHILDREN only (Azure OpenAI, 3072-dim, batch 128)
                ▼          parents = zero vectors
       Qdrant upsert  ──►  delete_document(keep_ids=new)   ← version swap
                ▼
       state.upsert()  ──►  MySQL documents + _author/_tag/_theme/_attachment
       ingest_log.record()
```

### Gaps, technical debt and things to investigate

**Correctness / data-loss risks**

1. **Attachment documents are never deleted.** `detect_drupal_changes` yields `DELETED` only for `source_type="website"` (`drupal.py:219`). Remove a PDF from a node, or delete the node itself, and the `pdf_attachment` document row and all its Qdrant points survive forever. The `documents_attachment` *link* row is correctly rewritten, so the orphan is invisible in the catalog but still retrievable. **This is the most significant gap.**

2. **Delete reconciliation is off by default.** `worker_sweep_reconcile = False`, so the scheduled sweep never reconciles. Unpublished and deleted Drupal nodes remain searchable indefinitely until someone runs `--reconcile` or `POST /ingest/run {"reconcile": true}`.

3. **Pipeline configuration changes invalidate nothing.** Neither the fingerprint nor the content hash reflects `EXTRACTION_MODE`, the Azure DI model, chunking presets, or the embedding model/dimensions. Configure Azure after ingesting a scanned corpus and those PDFs stay at their empty/garbled extraction — the fingerprint hasn't changed, so they never re-extract. Same for a chunk-size retune or an embedding model swap. The only remedy is a manual `/reindex` per document or truncating `documents`. Consider folding an extraction/chunking/embedding version into the state row and treating a mismatch as `CHANGED`. **Now the highest-value fix in this list** — it is the only remaining way content can sit permanently mis-extracted.

4. **A scanned PDF with Azure unconfigured indexes as an empty document**, is marked `indexed` with `chunks_indexed=0`, and is then pinned there by (3). Nothing flags this — `_handle` doesn't check whether chunking produced anything. A zero-chunk `indexed` outcome deserves its own status.

5. **`state.upsert` does not clip over-long values.** `source_key` (1024), `title` (1024), `url` (1024), attachment `url` (1024) / `filename` (255) are passed through unclipped. A long percent-encoded attachment URL raises MySQL 1406 and fails the whole document — the same class of bug the fingerprint column already hit (see the `inbody:` comment at `drupal.py:158`). `ingest_log.record` clips everything; `state.upsert` should too.

**Coverage / silent under-collection**

6. **`_discover_relationship_fields` samples exactly one record per bundle** to build the `include=` list. Any `field_*` empty on that record is never included → its file attachments are silently skipped and its entity refs get `label=None`. Which record is sampled depends on default ordering, so coverage is non-deterministic. Consider sampling N records, or maintaining an explicit per-bundle include map (which is what `field_audit.py` was built to inform).

7. **`ExtractionResult.metadata` is discarded.** Route, OCR page numbers and page signals are computed, logged once, and dropped. There is no way to answer "which documents needed OCR?" or "how many pages went to Azure last month?" from the stores. Cheap to persist into `raw_meta` or the log row.

9. **`authors` uses `_pick_list` (first matching field only), while `categories`/`tags` use `_union_list`.** A bundle with both `field_author` and `field_co_author` loses one. Likely unintentional asymmetry — worth confirming against `field_audit` output.

10. **Drupal HTML heading structure is destroyed then guessed back.** `_html_to_text` renders `<h2>Foo</h2>` as a bare line, which only becomes a section heading if it passes the ≤8-word Title-Case/ALL-CAPS test. Emitting `## Foo` instead would make the segmenter's ATX branch exact for web content.

**Efficiency**

11. **Every node edit re-downloads and re-extracts all its attachments.** Attachments are fingerprinted on the node's `changed` mark, so a typo fix in the body triggers a full PDF download + PyMuPDF/Azure/Camelot pass — which then resolves to `unchanged_content`. An HTTP `ETag`/`Last-Modified` conditional GET, or a `HEAD` size check, would eliminate most of this.

12. **Parents are stored as zero vectors in the same cosine collection.** Roughly 20% of points carry a 3072-float all-zero vector that is never searched (retrieval filters `is_parent`). Cosine similarity against a zero vector is undefined; Qdrant scores it 0, so any unfiltered search silently returns parents at the bottom. A named-vector or separate-collection layout would remove the storage and the footgun.

13. **`_enrich` runs before the content-changed check** (deliberately, per the comment at `pipeline.py:218`), so with enrichment on every sweep does one indexed SELECT per document even when nothing changed.

**Operational**

14. **`_run_lock` is process-local.** Running the CLI while the ingestion server's scheduler is active gives two concurrent runs with no mutual exclusion — double-embedding and racing delete/upsert. The comment acknowledges this and points at "celery mode", which doesn't exist.

15. **No dead-letter queue.** Failures are `ingest_log` rows with `status="error"`; there is no retry budget, no escalation, and no alerting. A document that fails every sweep fails silently forever. (Contrast enrichment, which *does* have an attempt counter, and dead links, which *do* have markers.)

16. **`prior` sets are keyed by bundle name only, ignoring `entity_type`** (`drupal.py:96`). Today `DEFAULT_BUNDLES` and `DEFAULT_TAXONOMIES` don't collide, but a future `node/tags` bundle would silently merge its priors with the `taxonomy_term/tags` vocabulary's and corrupt the high-water mark.

17. **`POST /ingest/article` writes no state row.** An ad-hoc article gets Qdrant points and a log row but no catalog row, so it is invisible to change detection, to `/reindex`, and to catalog count/list queries. It is now the only such path left.

18. **`dead_links.load()` is read once at crawl start**, so markers written during a run aren't honoured until the next one. Harmless at current volumes.

**Worth investigating further**

- Actual per-run tallies from `GET /ingest/log` — specifically the ratio of `unchanged_content` to `indexed` on Drupal sweeps, which measures how much of gap (11) you are paying.
- Whether `include=` with every discovered `field_*` is hitting Drupal's response-size limits on the wide bundles; a bundle-level failure there is logged as `Drupal fetch failed for node/X; skipping bundle` and is easy to miss.
- How many `pdf_attachment` rows in `documents` have no corresponding row in `documents_attachment` — that count is the size of gap (1).
- Whether `carousel` and the ten taxonomy vocabularies are producing useful chunks or just catalog noise; both fall through to the `_BASE` chunking preset.

---

## 12. Change log

**2026-08-09 — local PDF pipeline removed.** Drupal became the only ingestion
source. Six commits, ~700 lines net removed, `pytest` green (856) at every step.

| Removed | Why it existed |
|---|---|
| `change_detection/files.py` | Walked `PDF_SOURCE_DIRS`, size+mtime pre-filter, SHA-256 fingerprints, delete reconciliation |
| `pipeline.ingest_pdfs`, `_build_pdf_doc`, `--pdf`/`--dir` CLI | The local sweep's entry points |
| `tasks.ingest_pdfs`; the PDF leg of `sweep()` | Worker wiring |
| `POST /ingest/pdfs`, `POST /ingest/pdf`, `_read_capped` | HTTP triggers and the upload guard |
| `upload.ingest_upload`, `_pdf_document`, `_text_document` | File-based ad-hoc ingest |
| `GET /source/{id}`, `api/source.py`, `retrieval/source_locator.py`, `citations._pdf_link` | Served PDFs off disk for citation links |
| `indexer --pdf` | Indexed a disk PDF straight into Qdrant, bypassing change detection |
| `ChangeRecord.size/.mtime_ns`, `StateRecord.size/.mtime_ns`, `state.update_stat` | The stat pre-filter's plumbing |
| `pdf_source_dirs`, `pdf_source_path`, `pdf_ignore_globs`, `max_upload_bytes`, `source_base_url` | Settings with no remaining reader |

`from_pdf`'s default `source_type` moved `"pdf"` → `"pdf_attachment"`, so no code
path can mint a `"pdf"` document any more.

**Deliberately kept:** the entire PDF *extraction* stack (`pdf_extractor`,
`pymupdf_local`, `camelot_tables`, `text_normalize`, `canonical.from_pdf`, the
`pdf` / `small_pdf` chunking presets) — attachments depend on all of it. Also the
read-only diagnostics `python -m app.ingestion.extractors.pdf_extractor <file>`
and `python -m app.ingestion.chunking <file>`, which write nothing.

**Deferred:** the `size` / `mtime_ns` columns remain in `documents` (nullable,
unwritten). Dropping them needs a migration and was kept out of a pure-removal
change; see §11 for the rest of the open list.

**Breaking API changes:** `POST /ingest/pdf`, `POST /ingest/pdfs` and
`GET /source/{id}` now return 404; `POST /ingest/run` and
`POST /reindex {"sweep": true}` no longer carry `pdfs` / `pdf_source` keys.
