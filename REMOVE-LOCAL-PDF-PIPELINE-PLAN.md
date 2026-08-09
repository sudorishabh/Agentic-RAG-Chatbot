# Plan — Remove the Local PDF Ingestion Pipeline

**Goal:** Drupal becomes the single source of truth. The filesystem scan of `PDF_SOURCE_PATH` / `PDF_SOURCE_DIRS` and everything that exists only to serve it is deleted.

**Status: DONE (2026-08-09).** Executed in six commits. Phase 6 (the data purge) was
not needed — the source folder was empty, so the sweep's own delete reconciliation
had already cleared any rows. See §12 of `INGESTION-PIPELINE-REPORT.md` for what
actually shipped, including one path this plan missed (`indexer --pdf`).
**Baseline:** `main` @ `5c27c95`.

---

## 0. Read this first — the boundary

The word "PDF" appears all over this codebase, and most of it **must survive**. There are two distinct PDF paths:

| | Local PDF pipeline (**REMOVE**) | Drupal attachment pipeline (**KEEP**) |
|---|---|---|
| `source_type` | `"pdf"` | `"pdf_attachment"` |
| Discovery | `os.walk` over `PDF_SOURCE_PATH` | `field_*` file refs + in-body `<a href="*.pdf">` on Drupal nodes |
| Change detection | `detect_file_changes` (size/mtime → SHA-256) | `detect_drupal_changes` (node `changed` mark) |
| Bytes come from | `path.read_bytes()` | `session.get(url)` |
| Extraction | `extract_pdf()` | `extract_pdf()` ← **same code** |
| Chunking | `pdf` / `small_pdf` preset | `pdf_attachment` → aliases the `pdf` preset |
| Citation link | `/source/{id}#page=N` (served off disk) | the remote `file_url` |
| Catalog facets | none — no themes, no authors, no `published_at` | inherited from the parent node |

**The entire extraction stack stays untouched.** `pdf_extractor.py`, `pymupdf_local.py`, `camelot_tables.py`, `text_normalize.py`, Azure Document Intelligence, Camelot, PyMuPDF, `canonical.from_pdf`, the `pdf`/`small_pdf` chunking presets — all of it is shared with attachments and is *more* used by them than by the local path.

*Reasoning: the local pipeline is a **source adapter**, not a format handler. We are deleting the adapter (how bytes are discovered and fetched), not the handler (what happens to the bytes).*

---

## 1. Decision points — answer these before Phase 3

### D1. The `POST /ingest/pdf` upload route — remove it too?

`/ingest/pdf` lets a user POST a PDF file over HTTP. It is **not** part of the filesystem sweep, but it is the other producer of `source_type="pdf"` documents.

**Recommendation: remove it.** Reasoning, in order of weight:

1. **Its citations are already broken.** `upload._pdf_document` stores `pdf_path = filename` — a bare filename like `"report.pdf"`, not an absolute path. `source_locator._within_roots` resolves that against the CWD and rejects it as outside `pdf_source_dirs`, so `GET /source/{id}` already returns 404 for every uploaded PDF. Uploaded documents have no `file_url` either, so `citations._primary_url` returns a link that cannot be opened. This is a live defect today, not a consequence of this change.
2. **It writes no state row** (gap #17 in `INGESTION-PIPELINE-REPORT.md`), so uploads are invisible to change detection, `/reindex`, and every catalog count/list query.
3. **Keeping it forces us to keep the scaffolding** we are otherwise deleting: `PDF_SOURCE_DIRS` (for `_allowed_roots`), `source_locator.py`, `api/source.py`, `citations._pdf_link` — all of which only serve a code path that is already non-functional.

If you want to keep an upload capability, the correct shape is a **follow-up piece of work**, not a carve-out from this one: upload → object storage → a real `file_url` → a state row. That is a feature, not a deletion.

**If you decide to keep `/ingest/pdf` as-is**, Phase 4 is skipped and you must keep `pdf_source_dirs`/`pdf_source_path` in config purely as the `/source/` allow-list — accepting that it serves nothing.

### D2. Existing `source_type="pdf"` data — delete or leave?

`.env` currently has `PDF_SOURCE_PATH=D:\...\rag_test_sample_500`, so **this pipeline is live and has almost certainly ingested documents.** Phase 6 measures the blast radius before anything is deleted.

**Recommendation: delete the data.** Reasoning: once the pipeline is gone, those documents can never be updated, re-indexed, or deleted through any code path — no change detection covers them and no citation link resolves to them. They would be permanently frozen, un-openable search results. If any of that content matters, it should be published in Drupal and re-ingested as an attachment.

### D3. Drop the `size` / `mtime_ns` columns?

They exist solely for the local PDF stat pre-filter and become permanently NULL. **Recommendation: drop the code that reads/writes them in Phase 3, but leave the DB columns until a later cleanup.** Reasoning: dropping columns is irreversible and buys nothing; leaving two nullable BIGINTs costs nothing. Keep the schema change out of a removal PR so a rollback is pure code.

---

## 2. Inventory — every touchpoint

### 2a. Delete entirely

| Path | Lines | Reasoning |
|---|---|---|
| `app/ingestion/change_detection/files.py` | 162 | The whole filesystem source adapter: root parsing, ignore globs, `os.walk`, the size/mtime pre-filter, SHA-256 fingerprinting, delete reconciliation against the manifest. **Nothing else imports it except the pipeline entry point we are also removing.** |

### 2b. Edit — core pipeline

| Path | What goes | Reasoning |
|---|---|---|
| `app/ingestion/change_detection/__init__.py` | `from ...files import _parse_roots, detect_file_changes`; `"detect_file_changes"` from `__all__`; the "two independent sources" line in the docstring | The package re-exports a module that no longer exists. `_parse_roots` is also imported by `source_locator.py` — see Phase 4. |
| `app/ingestion/pipeline.py:373` `_build_pdf_doc` | whole function | The `DocBuilder` for local PDFs. Its only caller is `ingest_pdfs`. |
| `app/ingestion/pipeline.py:397` `ingest_pdfs` | whole function | The public entry point. Removing it is what actually deletes the source. |
| `app/ingestion/pipeline.py:116` `_log` → `is_pdf` | the branch | `is_pdf = record.source_type == "pdf"` is only ever true for local PDFs (attachments are `"pdf_attachment"`). With them gone, `source_path` is always `None` and `source_url` is always `record.source_key`. Collapse the ternaries — leaving them is a permanently-false branch that reads like it still does something. |
| `app/ingestion/pipeline.py:199` `_handle` → `update_stat` branch | the `if` block | Guarded by `record.size is not None`, which only `files.py` ever sets. Dead code the moment `files.py` is gone. |
| `app/ingestion/pipeline.py:441` `_main` | `--pdf`, `--dir` args; the `if args.pdf:` block; make `--drupal` non-optional (drop the "choose at least one" check) | The CLI advertises a mode that no longer exists. |
| `app/ingestion/change_detection/base.py:33` | `ChangeRecord.size`, `ChangeRecord.mtime_ns` | Set only by `files.py`, read only by `pipeline._handle`'s `update_stat` branch and `_save_state`. Both go. |

### 2c. Edit — orchestration & API

| Path | What goes | Reasoning |
|---|---|---|
| `app/workers/tasks.py:11` `ingest_pdfs` | whole function | Thin wrapper over `pipeline.ingest_pdfs`. |
| `app/workers/tasks.py:28` `sweep` | the `pdfs = ingest_pdfs()` call and the `"pdfs"` key | The scheduled sweep is the main consumer. After this, `sweep()` returns `{"drupal": {...}}` — **this is a response-shape change for `POST /reindex {"sweep": true}`**; note it in the changelog. |
| `app/workers/tasks.py:57` CLI | `"pdfs"` from `choices` and the dispatch dict | Same reason as the pipeline CLI. |
| `app/api/ingest.py:67` `POST /ingest/pdfs` | whole route | Its only job is triggering the filesystem sweep. **Breaking API change** — anything calling it gets a 404. |
| `app/api/ingest.py:79` `POST /ingest/run` | the `source` lookup, the conditional `ingest_pdfs` call, `pdf_source=`/`pdfs=` in the response | Becomes a plain "crawl Drupal" trigger. Keep the route — it is the documented manual-trigger endpoint. |
| `app/schemas/ingest.py:20` `PdfIngestRunResponse` | whole model | Only used by the deleted `/ingest/pdfs`. |
| `app/schemas/ingest.py:32` `DirectIngestResponse` | `pdf_source`, `pdfs` fields | **Breaking response-shape change** for `/ingest/run`. |

### 2d. Edit — configuration

| Path | What goes | Reasoning |
|---|---|---|
| `app/config.py:250-254` | `pdf_source_dirs`, `pdf_source_path`, `pdf_ignore_globs` | *Gated on D1/Phase 4* — `source_locator._allowed_roots` reads these. Remove them **after** `/source/` is gone, or the app fails at import. |
| `.env` | `PDF_SOURCE_PATH=D:\...\rag_test_sample_500` (line 45) and the commented variant (43) | Currently pointing at a live folder. `extra="ignore"` in `SettingsConfigDict` means a stale key won't crash anything, but leaving it implies a source that no longer exists. |
| `.env.example` | `PDF_SOURCE_PATH`, `PDF_SOURCE_DIRS`, `PDF_IGNORE_GLOBS` (lines 32-34) | Same. |

### 2e. Edit — catalog (the stat pre-filter's storage)

| Path | What goes | Reasoning |
|---|---|---|
| `app/catalog/state.py:214` `update_stat` | whole function + `__all__` entry | Its only caller is the `_handle` branch we are deleting. |
| `app/catalog/models.py:35` `StateRecord` | `size`, `mtime_ns` | Only ever populated from a local-PDF `ChangeRecord`. Keep `_row_to_record` tolerant of the columns still existing in the DB (they'll just be ignored). |
| `app/catalog/schema.py` | **nothing** — see D3 | Leave the `size` / `mtime_ns` columns and their `_ensure_column` calls. Dropping columns is irreversible and buys nothing; a rollback then stays pure code. |

### 2f. Edit — local test harness

| Path | What goes | Reasoning |
|---|---|---|
| `app/local_tests/run_ingestion_test.py:127` `make_sample_pdf` | whole function | Generates a sample PDF into the local data dir — only used by `--source pdf`. |
| `app/local_tests/run_ingestion_test.py:164` | the `elif rec.source_type == "pdf": cap.doc = pipeline._build_pdf_doc(rec)` branch | Calls a function that no longer exists. |
| `app/local_tests/run_ingestion_test.py:279` | `--source` choices → drop `"pdf"`; drop `--dir`, `--make-sample` | The harness's PDF mode. |
| `app/local_tests/run_ingestion_test.py:325` `_iter_records` | the `if args.source == "pdf":` branch | Calls `cd.detect_file_changes`. |
| `app/local_tests/run_ingestion_test.py:389` | `"pdf_dir"` in the run manifest | Field has no source. |
| `app/local_tests/README.md` | the `--source pdf` documentation | Keep docs honest. |

**Note:** the harness still exercises attachment PDFs end-to-end via `--source drupal`, so PDF extraction coverage is not lost.

### 2g. Documentation

| Path | What |
|---|---|
| `docs/ingestion.md` | §Change detection `detect_file_changes` bullet; §Orchestration `ingest_pdfs` signature; `source_type` list; `pdf_path` in the canonical-model field list |
| `docs/configuration.md:193-195` | the three `pdf_source_*` rows |
| `docs/api-reference.md:210` | `/ingest/pdfs` section |
| `docs/operations.md:45` | the `ingest_pdfs` worker-task row |
| `docs/architecture.md:45`, `README.md:38` | the `source_locator.py` tree line — *gated on Phase 4* |
| `CODEBASE_REPORT.md` | lines 46, 54-55, 199, 285 |
| `INGESTION-PIPELINE-REPORT.md` | §1 diagram (drop the `Local filesystem` arm), §4 source table, §7 delete table, §11 diagram + gaps #8, #17 |

---

## 3. What explicitly STAYS — do not touch

Listing these because they all contain the string "pdf" and a search-and-destroy pass would break the attachment pipeline.

| Keep | Why |
|---|---|
| `app/ingestion/extractors/**` (all 6 modules) | Shared with attachments. This is the format handler, not the source adapter. |
| `canonical.from_pdf` | Attachments call it (`attachment.py:124`). **Change its default `source_type="pdf"` → `"pdf_attachment"`** so a defaulted call can't mint an orphan type. |
| `chunking/config.py` `"pdf"` and `"small_pdf"` presets | `_PRESETS.setdefault("pdf_attachment", _PRESETS["pdf"])` — deleting the `pdf` preset silently drops every attachment to `_BASE`. Renaming it is pointless churn. |
| `pdf_id`, `pdf_path` payload fields; `DocumentMeta`/`CanonicalDocument` attributes | `pdf_id` is still set for attachments (`from_pdf` sets it to the doc id) and `source_locator` matches on it. `pdf_path` becomes permanently absent from payloads — harmless, since `build_payload` strips `None`. Leaving the field costs nothing and keeps old points readable. |
| `retrieval/understanding/filters.py:66` — `source_type == "pdf"` → `MatchAny(["pdf", "pdf_attachment"])` | This is the **user-facing query vocabulary** ("only search PDFs"), not a stored value. It must keep working for attachments. Keeping `"pdf"` in the `MatchAny` is harmless and covers legacy points if you defer D2. |
| `retrieval/query_processor.py:115` `Literal["pdf","website","uploaded"]` | Same — the analysis schema's vocabulary. |
| `generation/sections.py:26` `PDF = "pdf"`; `generation/prompts.py:404` | Display/grouping labels ("Web pages" vs "PDFs" in the answer), not source types. |
| `citations.py` `type="pdf"` | Citation display type. |
| `tests/**` | **Zero test files reference `detect_file_changes`, `ingest_pdfs`, `pdf_source`, `resolve_source_file`, or `_build_pdf_doc`.** The ~16 tests that use `source_type="pdf"` do so as an arbitrary fixture label for chunking/hashing/enrichment units that never touch change detection. They pass unchanged. |

---

## 4. Phased execution

Each phase leaves the tree in a working, committable state.

### Phase 1 — Stop the bleeding (config only, instantly reversible)
1. Comment out `PDF_SOURCE_PATH` in `.env`.
2. Restart the ingestion server; confirm the sweep logs `No PDF source dirs configured (pdf_source_dirs); nothing to scan.` and the Drupal leg runs normally.

*Reasoning: proves nothing downstream depends on local PDFs being ingested, before a line of code changes. If something breaks here, you learn it with a one-line revert available.*

### Phase 2 — Measure (read-only)
Run the queries in §5 and record the numbers. **Do not proceed to Phase 6 without them.**

### Phase 3 — Remove the ingestion path (§2a, 2b, 2c, 2e, 2f)
One commit. Delete `files.py`, unwire the entry points, drop `size`/`mtime_ns` from the code, fix the harness.

*Reasoning: this is the actual deliverable and it is self-contained. `/source/` and `/ingest/pdf` still work at this point (against existing data), so the blast radius is exactly "no new local PDFs are discovered."*

Config note: **do not** remove `pdf_source_dirs`/`pdf_source_path` from `app/config.py` in this phase — `source_locator._allowed_roots` still reads them, and `_parse_roots` still lives in the deleted module. Either move `_parse_roots` into `source_locator.py` (~15 lines, self-contained) or do Phase 4 in the same commit.

### Phase 4 — Remove the serving path *(gated on D1 = "remove the upload route")*
| Delete | Reasoning |
|---|---|
| `app/api/source.py` | The `/source/{id}` route exists only to serve disk PDFs. |
| `app/retrieval/source_locator.py` | Its whole job is `document_id → on-disk path`, ACL- and root-guarded. |
| `app/main.py:4,14` | Unregister `source_router`. |
| `app/api/ingest.py:52` `POST /ingest/pdf`; `_read_capped` | See D1. |
| `app/ingestion/upload.py` — `ingest_upload`, `_pdf_document`, `_text_document` | Keep `ingest_article` + `_index` + `_log_doc` — `/ingest/article` still uses them. |
| `app/schemas/ingest.py` `IngestResponse` | Only used by the deleted upload route. |
| `app/config.py` — `pdf_source_dirs`, `pdf_source_path`, `pdf_ignore_globs`, `max_upload_bytes`, `source_base_url` | Now genuinely unreferenced. |
| `app/retrieval/citations.py:10` `_pdf_link` + its call in `_primary_url` | The `/source/` fallback. After this, an attachment cites its `file_url` (always set by `attachment.py:130`) and a document with neither gets `url=None` — an honest absent link instead of a dead one. |

### Phase 5 — Documentation (§2g)

### Phase 6 — Data purge *(gated on D2)* — see §5

---

## 5. Data migration

### Measure first (Phase 2)

```sql
-- How many local-PDF documents exist, and are they real content?
SELECT source_type, COUNT(*) AS docs, MIN(indexed_at), MAX(indexed_at)
FROM documents GROUP BY source_type;

-- Sample them — is this the rag_test_sample_500 folder, or real corpus?
SELECT document_id, title, source_key, doc_version, indexed_at
FROM documents WHERE source_type = 'pdf' ORDER BY indexed_at DESC LIMIT 25;

-- Do any carry facets worth preserving? (expected: zero — the local path
-- sets no categories/authors/published_at)
SELECT COUNT(*) FROM documents_theme  t JOIN documents d USING (document_id) WHERE d.source_type='pdf';
SELECT COUNT(*) FROM documents_author a JOIN documents d USING (document_id) WHERE d.source_type='pdf';
```

Qdrant point count:
```python
from qdrant_client.models import FieldCondition, Filter, MatchValue
from app.core.clients import get_qdrant_client
from app.config import get_settings
c, s = get_qdrant_client(), get_settings()
print(c.count(s.qdrant_collection, count_filter=Filter(
    must=[FieldCondition(key="source_type", match=MatchValue(value="pdf"))]), exact=True))
```

### Purge (Phase 6)

**Order matters: Qdrant first, then MySQL.** A crash between the two leaves an orphan catalog row (invisible, harmless, re-purgeable). The reverse leaves searchable points with no catalog row — the worse failure.

```python
# 1. Qdrant — delete every point whose source_type is the local-PDF type.
from qdrant_client.models import FilterSelector, Filter, FieldCondition, MatchValue
from app.core.clients import get_qdrant_client
from app.config import get_settings
c, s = get_qdrant_client(), get_settings()
c.delete(collection_name=s.qdrant_collection, points_selector=FilterSelector(
    filter=Filter(must=[FieldCondition(key="source_type", match=MatchValue(value="pdf"))])))
```

```sql
-- 2. MySQL — the FK CASCADE clears documents_theme / _author / _tag / _attachment.
DELETE FROM documents WHERE source_type = 'pdf';

-- 3. Optional: prune orphaned enrichment rows (no FK by design — see schema.py).
DELETE e FROM documents_enrichment e
LEFT JOIN documents d ON d.content_hash = e.content_hash
WHERE d.content_hash IS NULL;
```

**Take a MySQL dump and a Qdrant snapshot before step 1.** These deletes are not reversible from within the application.

The `ingest_log` rows are left alone — it is an append-only audit log and its retention prune (`ingest_log_retention_days`, 90) will age them out.

---

## 6. Verification checklist

After Phase 3:
- [ ] `python -c "import app.ingest_main, app.main"` — no `ImportError`
- [ ] `pytest -q` — expect the same pass count as baseline (no test touches this path)
- [ ] `grep -rn "detect_file_changes\|ingest_pdfs\|_build_pdf_doc\|update_stat" app/ tests/` → **no hits**
- [ ] `grep -rn "pdf_source_dirs\|pdf_source_path\|pdf_ignore_globs" app/` → only `source_locator.py` + `config.py` (until Phase 4), then none
- [ ] Start the ingestion server; the sweep completes and logs `{"drupal": {...}}` only
- [ ] `POST /ingest/run` returns `{"drupal": {...}}` with no `pdf_source`/`pdfs` keys
- [ ] `POST /ingest/pdfs` returns **404**
- [ ] `python -m app.ingestion.pipeline --drupal --bundle report` runs
- [ ] `python -m app.local_tests.run_ingestion_test --source drupal --bundle report --max-docs 2 --skip-index` still captures an attachment PDF through `extract_pdf` — **this is the regression guard that PDF extraction survived**

After Phase 4:
- [ ] `GET /source/{any-id}` → 404 (route gone)
- [ ] `POST /ingest/pdf` → 404
- [ ] `POST /ingest/article` still works
- [ ] A chat answer citing an attachment PDF still returns an openable `url` (the remote `file_url`) with `#page=N`

After Phase 6:
- [ ] `SELECT COUNT(*) FROM documents WHERE source_type='pdf'` → 0
- [ ] Qdrant count with `source_type="pdf"` → 0
- [ ] A representative chat query still returns citations and none of them 404

---

## 7. Rollback

| Phase | Rollback |
|---|---|
| 1 | Uncomment `PDF_SOURCE_PATH`, restart |
| 3–5 | `git revert` the commit(s). Because Phase 3 touches no schema and Phase 6 hasn't run, the data is still there and the next sweep re-adopts it |
| 6 | **Restore from the dump/snapshot** — there is no code-level undo |

This is why Phase 6 is last and separately gated: everything before it is a `git revert`.

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Content only reachable as a local PDF disappears from the corpus | **Depends entirely on D2 measurements.** `.env` points at `rag_test_sample_500`, whose name suggests test data — but confirm in Phase 2 | Phase 2 sampling before Phase 6; keep the dump |
| An external caller uses `POST /ingest/pdfs` or reads `DirectIngestResponse.pdfs` | Low (internal ops endpoints) | Flag as breaking in the changelog; grep the `ui/` folder and any deploy scripts |
| Over-deletion — someone removes `extract_pdf` or the `pdf` chunking preset with it | Medium; this is the main way the change goes wrong | §3 is the explicit keep-list; the `--source drupal` harness run is the guard |
| `sweep()` return shape changes and something parses it | Low | It is logged and returned by `/reindex {"sweep":true}`; note in the changelog |
| Removing `pdf_source_*` from config before Phase 4 crashes `source_locator` at import | Medium — easy sequencing mistake | Explicitly sequenced in Phase 3's config note |

---

## 9. Net effect

**Deleted:** ~162 lines (`files.py`) + ~120 lines of entry points, routes, schemas and CLI wiring. With Phase 4: a further ~260 lines (`source_locator.py`, `api/source.py`, upload paths) and 5 settings.

**Gained:**
- One source of truth. Every document in the corpus is traceable to a Drupal entity, has a real public URL, inherits themes/authors/dates, and participates in delete reconciliation.
- Three of the gaps in `INGESTION-PIPELINE-REPORT.md` §11 disappear rather than needing fixes: **#8** (local PDFs have no metadata), **#17** (upload writes no state row — if D1 = remove), and half of **#3** (nothing left that is un-reindexable by a filesystem path).
- `ChangeRecord` loses two fields, `_handle` loses a branch, and the ingestion story becomes one sentence.

**Unchanged:** every line of PDF *extraction*. Attachments still go through PyMuPDF classification, Azure OCR, Camelot tables and the full normalization stack.
