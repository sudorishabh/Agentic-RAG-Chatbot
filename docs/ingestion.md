# Ingestion

How documents become searchable: **extract → canonical → chunk → embed → index**,
with incremental change detection backed by a MySQL manifest.

## The canonical model

Everything is normalized to a `CanonicalDocument` ([app/core/models.py](../app/core/models.py))
before chunking, so PDFs and articles flow through one pipeline.

`CanonicalDocument` fields (abridged):

- **Identity:** `document_id`, `source_type` (`pdf` / `article` / …), `title`, `sections[]`.
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

1. **Extract digital text** with `unstructured` (`strategy="fast"`, pdfminer-based).
   Total page count comes from `pypdf`.
2. **pypdf fallback.** A page below `pdf_scanned_char_threshold` (default 100)
   characters is re-read with `pypdf` before being judged *scanned* — `unstructured`
   `fast` returns nothing on some PDFs, so this second reader keeps born-digital
   pages off the (paid, slower) OCR path. A page is sent to OCR only when *both*
   readers come up short.
3. **Digital pages** → `unstructured`/`pypdf` text.
4. **Scanned pages** → Azure Document Intelligence OCR (`prebuilt-layout`), which
   also reconstructs tables (emitted as Markdown).

All page text is normalized to expand standard ligature glyphs (`ﬁ`/`ﬀ`/… →
`fi`/`ff`/…) so words stay matchable in search. Font-specific Private-Use-Area
glyphs and `(cid:N)` markers in some PDFs are *not* recoverable from the text
layer (they need visual OCR) and are left as-is.

`ExtractionResult` exposes `pages`, `page_count`, `text`, `tables`, and
`ocr_page_numbers`. PDF-extraction settings are listed in
[configuration.md](configuration.md#pdf-extraction--ocr).

> Tables are produced only on the OCR path; born-digital pages carry their table
> content as flattened text. Section headings are re-derived from text by the
> chunker, so digital pages without Markdown headings chunk as flat sections.

### Drupal articles — [app/ingestion/extractors/drupal_extractor.py](../app/ingestion/extractors/drupal_extractor.py)

Crawls the JSON:API at `drupal_jsonapi_base`:

- `iter_records(bundles=None, *, published_only=True, changed_since=None, session=None)`
  — yields `DrupalRecord`s across bundles.
- `iter_bundle_records(session, bundle, …)` — paginates one bundle, auto-discovers
  `field_*` relationships, resolves them to labels, and converts HTML bodies to text.
- `iter_node_uuids(session, bundle, …)` — lightweight UUID listing for delete reconciliation.

`DrupalRecord` carries `uuid`, `bundle`, `nid`, `title`, `url`, `body`, `created`,
`changed`, `metadata`, with `to_text()` and `to_metadata()` helpers. Default bundles
include news, feature_articles, completed_projects, events, press_release,
research_papers, ongoing_projects, article, policy_brief, videos, infographics,
services, report, people, page. Retries use exponential backoff on 429/5xx.

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
  — fingerprint is the `changed` timestamp (as Unix epoch), enabling a `changed_since`
  high-water-mark crawl; optional delete reconciliation against live UUIDs.
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
