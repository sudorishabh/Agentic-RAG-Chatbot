# Ingestion

How documents become searchable: **extract → canonical → chunk → embed → index**,
with incremental change detection backed by a MySQL manifest.

## The canonical model

Everything is normalized to a `CanonicalDocument` ([app/core/models.py](../app/core/models.py))
before chunking, so PDFs and articles flow through one pipeline.

`CanonicalDocument` fields (abridged):

- **Identity:** `document_id`, `source_type` (`pdf` / `website` / `pdf_attachment`), `title`, `sections[]`.
  *(`website` covers all Drupal content; it was historically named `article` — the
  migration script `scripts/migrate_source_type_website.py` renames stored data.)*
- **Source refs:** `source_url`, `pdf_id`, `pdf_path`, `article_uuid`,
  `linked_pdf_id`, `linked_article_uuid` (cross-links power dedup/conflict handling).
- **Metadata:** `authors[]`, `tags[]`, `categories[]`, `language` (default `en`),
  `tenant_id` (default `default`), `acl[]` (default `["public"]`), `published_at`,
  `doc_version` (default 1), `is_current` (default true), `content_hash`, `extra{}`.
- **Helpers:** `is_paginated`, `full_text()`, `compute_content_hash()` (SHA-256 of
  `title + full_text`), `ensure_content_hash()` (lazy + cached).

`CanonicalSection`: `text`, `heading`, `page_start`, `page_end`, `order`.

Builders in [app/ingestion/canonical.py](../app/ingestion/canonical.py):

- `from_pdf(result, *, document_id=None, source_type="pdf", **overrides)` — maps
  extracted pages to one section per page (1-indexed).
- `from_drupal_record(record, **overrides)` — from a crawled `DrupalRecord`.
- `from_drupal_export(item, **overrides)` — from an ad-hoc article dict
  (`text`/`title`/`url`/`uuid`/`bundle`). Metadata keys containing tag/keyword/
  category/theme/area/division/author are auto-mapped into the canonical lists.

## Extraction

### PDFs — [app/ingestion/extractors/pdf_extractor.py](../app/ingestion/extractors/pdf_extractor.py)

`extract_pdf(content: bytes, filename: str) -> ExtractionResult`

1. **Classify each page** with PyMuPDF (`pymupdf_local.classify_document`): is it
   *scanned* (extracted text below `pdf_scanned_char_threshold`, default 100
   characters) and/or does it carry a *table* (`find_tables`, plus the optional
   ruled-grid / borderless heuristics)?
2. **Route per page** (`PageSignal.route`), then stitch the pages back in order:
   - **born-digital text** → PyMuPDF text;
   - **born-digital table** → Camelot extracts the table(s) to Markdown
     (`camelot_flavor`, default `lattice`, with a `stream` retry on empty pages);
     the page's prose still comes from PyMuPDF and the table Markdown is merged
     into that page's text;
   - **scanned / image** → Azure Document Intelligence OCR (`prebuilt-read`,
     text only). A scanned page that *also* has a table goes to Azure — Camelot
     cannot read an image — so its table is OCR'd as plain text, not structured.
     Switch `azure_document_intelligence_model` to `prebuilt-layout` (~6x cost)
     if you need tables reconstructed from scanned pages.
3. **Fallbacks.** If Azure is unavailable its pages degrade to PyMuPDF text; if
   Camelot finds nothing on a flagged page that page keeps just its PyMuPDF text.
   `EXTRACTION_MODE` overrides the path: `hybrid` (default, per-page above),
   `azure_only` (whole document to Azure), `local_only` (PyMuPDF text only).

All page text is normalized to expand standard ligature glyphs (`ﬁ`/`ﬀ`/… →
`fi`/`ff`/…) so words stay matchable in search. Font-specific Private-Use-Area
glyphs and `(cid:N)` markers in some PDFs are *not* recoverable from the text
layer (they need visual OCR) and are left as-is.

`ExtractionResult` exposes `pages`, `page_count`, `text`, `tables`, and
`ocr_page_numbers`. PDF-extraction settings are listed in
[configuration.md](configuration.md#pdf-extraction--ocr).

> Tables reach the chunker as Markdown embedded in each page's text (the chunker
> reads page text, not the separate `tables` list) — from Camelot on born-digital
> table pages and from Azure on scanned pages. Section headings are re-derived
> from text by the chunker, so pages without Markdown headings chunk as flat
> sections.

### Drupal — [app/ingestion/extractors/drupal_extractor.py](../app/ingestion/extractors/drupal_extractor.py)

Crawls the JSON:API at `drupal_jsonapi_base`. The crawl is **entity-type aware**:
the same iterators fetch node bundles, taxonomy-term vocabularies, and custom
blocks from `/jsonapi/{entity_type}/{bundle}`.

- `iter_records(bundles=None, *, published_only=True, changed_since=None, session=None)`
  — yields `DrupalRecord`s across node bundles (convenience / CLI entry point).
- `iter_bundle_records(session, bundle, *, entity_type="node", published_only=True, changed_since=None)`
  — paginates one resource, auto-discovers `field_*` relationships, resolves them
  to labels, converts HTML bodies to text, and collects attached + in-body PDFs.
- `iter_node_uuids(session, bundle, *, entity_type="node", …)` — lightweight UUID
  listing for delete reconciliation.

**Resources crawled by default:**

- `DEFAULT_BUNDLES` (nodes): news, feature_articles, completed_projects, events,
  press_release, research_papers, ongoing_projects, article, policy_brief, videos,
  infographics, services, report, people, page, **carousel**.
- `DEFAULT_TAXONOMIES` (`taxonomy_term`): **themes, extra_pages, regional_centre** —
  their `description` prose (thematic / landing-page content that lives nowhere in
  the nodes) is ingested as body text.
- `DEFAULT_BLOCKS` (`block_content`): **basic** — substantial custom-block bodies;
  boilerplate shorter than `drupal_block_min_chars` (with no PDF) is skipped.

Non-node records tag `entity_type` in metadata; the title falls back to `name`
(taxonomy) / `info` (block); blocks have no canonical URL.

`DrupalRecord` carries `uuid`, `bundle`, `nid`, `title`, `url`, `body`, `created`,
`changed`, `metadata`, `files[]`, with `to_text()`, `to_metadata()`, and `pdf_url`
helpers. Retries use exponential backoff on 429/5xx.

**Attached & in-body PDFs → their own documents.** PDFs are collected two ways,
each as a `DrupalFile` (`origin` = `attachment` | `inbody`):

- **Attachments** — referenced `file--file` entities on any `field_*`. Non-PDF
  document attachments (docx/xlsx/pptx/…) are logged and skipped.
- **In-body links** — `<a href="…pdf">` and bare `https://…pdf` URLs scanned across
  *all* rich-text fields (not just `body` — links also appear in
  `field_completed_featured_text`, etc.). Internal (teriin.org) PDFs are always
  harvested; external ones only when `drupal_ingest_external_pdfs=true` (otherwise
  the URL still survives in the body text). Each in-body PDF gets a URL-stable
  synthetic uuid (`inbody:<sha1>`) so a PDF linked from several nodes ingests once.

Each PDF (attachment or in-body) is downloaded, PDF-extracted, and indexed as its
own `pdf_attachment` document linked back to the node (see change detection below).

**HTML → text.** `_html_to_text` flattens body HTML but preserves what a naive
strip would drop: `<a>` destinations as `text (url)`, `<img>` alt as
`[image: alt]`, `<iframe>` src as `[embedded: src]`, and `<td>`/`<th>` as
`|`-separated cells so tables stay legible.

## Chunking — [app/ingestion/chunker.py](../app/ingestion/chunker.py)

Structure-aware, token-based, parent/child.

- `chunk_canonical(doc, *, config=None, small_doc_pages=10)` — main entry. Auto-selects
  a preset by `source_type`/bundle; paginated docs of ≤10 pages use a `small_pdf`
  preset that keeps the whole doc as one parent.
- Lower-level: `chunk_pages(...)`, `chunk_document(...)`, plus convenience adapters
  `chunk_pdf(...)` and `chunk_drupal_record(...)`.

`ChunkingConfig` token budgets (defaults): child target 400 / max 512 / min 120 /
overlap 60; parent target 1800 / max 2400; encoding `cl100k_base` (≈4 chars/token
fallback). Pipeline: parse blocks (headings/code/tables) → assemble sections → merge
small sections → pack into parents → pack children with overlap → deterministic UUIDs
+ per-chunk SHA-256.

A `Chunk` becomes a Qdrant point via `to_payload()`. **Parents are stored as
zero-vectors; only children are embedded** — parents are fetched by id during
parent-expand at query time (see [retrieval.md](retrieval.md)).

## Embedding — [app/ingestion/embedder.py](../app/ingestion/embedder.py)

- `get_embeddings()` — memoized `AzureOpenAIEmbeddings` client.
- `embed_query_cached(text)` — query embedding with a Redis cache (keyed by model+text).

## Indexing — [app/ingestion/indexer.py](../app/ingestion/indexer.py)

- `index_chunks(chunks, *, batch_size=128, stamp=True)` — embeds child chunks in
  batches, builds `PointStruct`s (children with vectors, parents with zero-vectors),
  upserts to Qdrant, and stamps `created_at`/`updated_at`. Returns point count.
- `index_canonical(doc, **chunk_kwargs)` — chunk then index a document.
- `index_documents(docs, **chunk_kwargs)` — loop, catching per-document errors.

## Change detection — [app/ingestion/change_detection.py](../app/ingestion/change_detection.py)

Yields `ChangeRecord`s with status `NEW` / `CHANGED` / `UNCHANGED` / `DELETED`.

- `detect_file_changes(roots=None, ignore_globs=None)` — walks PDF roots; fingerprint
  is the file's SHA-256. De-dupes repeated `document_id`s within a scan; detects deletes
  by comparing prior manifest keys to the current scan.
- `detect_drupal_changes(bundles=None, *, published_only=True, reconcile_deletes=False)`
  — crawls node bundles (incremental via a `changed_since` high-water mark) plus the
  taxonomy and block sources (fetched in full each run). Each node/taxonomy/block
  yields a `website` record fingerprinted on its `changed` timestamp; each attached
  or in-body PDF yields a `pdf_attachment` record. Attachments are fingerprinted on
  the node's changed mark (re-fetched when the node changes); in-body PDFs are
  fingerprinted on their URL and de-duped per run, so a PDF shared across nodes
  ingests once. Boilerplate blocks are skipped; delete reconciliation (against live
  UUIDs) applies to node bundles only. An explicit `bundles` argument is treated as
  node bundles.
- `content_changed(record, content_hash)` — true if no prior or the content hash differs.
- `next_version(record)` — prior `doc_version + 1`, else 1.

**Two-level skipping:** a matching *fingerprint* skips extraction entirely; if the
fingerprint changed but the *content hash* matches, the document is counted
`unchanged_content` and the fingerprint is refreshed without re-indexing.

## Ingest-state manifest — [app/ingestion/state.py](../app/ingestion/state.py)

A MySQL table (`ingest_state_table`, default `ingest_state`) is the source of truth
for what has been ingested. `StateRecord` columns: `document_id` (PK), `source_type`,
`source_key`, `fingerprint`, `content_hash`, `doc_version`, `bundle`, `changed_mark`,
`indexed_at`. Public functions: `ensure_table()`, `load(source_type)`,
`get(document_id)`, `upsert(record, *, mark_indexed=True)`, `delete(document_ids)`,
`high_water(source_type, bundle=None)`, `keys(source_type, bundle=None)`,
`iter_records(source_type)`. Upserts use `INSERT … ON DUPLICATE KEY UPDATE`.

## Orchestration

### Incremental — [app/ingestion/pipeline.py](../app/ingestion/pipeline.py)

- `ingest_pdfs(roots=None, ignore_globs=None) -> Counter`
- `ingest_drupal(bundles=None, *, published_only=True, reconcile_deletes=False) -> Counter`

Each: detect changes → build canonical → check content hash / bump version → delete the
prior version from Qdrant → chunk + embed + index → upsert the manifest. The returned
`Counter` tallies `{new, changed, unchanged, unchanged_content, indexed, deleted,
skipped, error}` (keys present as they occur). Errors are counted per document; the
sweep continues.

### Inline upload — [app/ingestion/upload.py](../app/ingestion/upload.py)

Used by the HTTP ingest routes — no change-detection bookkeeping, indexes immediately
and bumps the corpus version so caches refresh.

- `ingest_upload(filename, content) -> (document_id, point_count)` — PDF (by suffix) or
  plain text.
- `ingest_article(*, title, body, url=None, uuid=None, bundle="article") -> (document_id, point_count)`.

### Workers / CLI

The same orchestration is exposed as Celery tasks with an inline fallback and a CLI —
see [operations.md](operations.md#background-workers).
