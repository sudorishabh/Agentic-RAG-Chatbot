# Local ingestion test

Standalone harness that runs **only the ingestion pipeline** and writes the
**complete raw output** of every stage per document — every parent and child
chunk in full, the full canonical document and metadata, the exact Qdrant
payloads, and a read-back of everything MySQL stored — plus `[PASS]/[FAIL]`
checks that the stored data matches.

Two sources:

- `--source drupal` (default) — crawls live Drupal nodes of one bundle
  (default `article`) **plus the PDFs attached to / linked from them**,
  exactly as the real pipeline would
- `--source pdf` — scans a local folder of PDF files

## What it exercises

The real per-document ingestion path (`app/ingestion/pipeline.py`):

1. **Change detection** — new / changed / unchanged / deleted vs the state table
2. **Extraction** — for PDFs: pages, per-page route (pymupdf / azure / camelot),
   tables, PDF metadata; Drupal node bodies come from the JSON:API crawl
3. **Canonical document** — document_id, title, sections, content hash, facets,
   entity references, file links
4. **Chunking** — parent/child chunks, token stats, the exact payload a chunk
   is indexed with
5. **Indexing** — embeddings + Qdrant upsert (or stubbed, see `--skip-index`)
6. **MySQL catalog** — state row, author/theme facet rows, term/attachment
   links, ingest-log rows, each verified against the canonical data

## Output files

Every run writes a dedicated folder, `results/run-<timestamp>/` by default
(override with `--results-dir`). The console shows only a one-line-per-document
progress log and the final summary; the full raw dumps go to files:

```
results/run-20260720-174500/
  all_documents.txt        full raw dump of every document, concatenated
  summary.json             config + per-document outcomes and every check
  docs/
    01_<document_id>.txt    per-document readable raw dump (full text)
    02_<document_id>.txt
    ...
  raw/
    01_<document_id>.json   per-document raw data (machine-readable, untruncated)
    02_<document_id>.json
    ...
```

Each per-document dump contains, in full and untruncated:

- **Change detection** — status, fingerprint, changed_mark, prior version
- **Extraction** (PDFs) — every page's full text and per-page route, all tables
- **Canonical document** — every field, all entity refs, file links, `raw_meta`,
  and every section's full text
- **Chunking** — every parent and child chunk: full text, all fields, and the
  exact payload upserted to Qdrant
- **MySQL catalog** — the state row, author/theme facet rows, term-link rows,
  attachment rows, and ingest-log rows, all read back from the database
- **Checks** — `[PASS]/[FAIL]` per assertion

## Isolation

Writes never touch the real catalog. Before app settings load, the runner
overrides the environment so everything lands in:

- MySQL: `local_test_ingest_state` (+ `_author`, `_theme`, `_term`,
  `_attachment`) and `local_test_ingest_log`
- Qdrant: `local_test_documents`

`--cleanup` drops these afterwards and refuses to drop anything not prefixed
`local_test_`.

## Prerequisites

- MySQL reachable with the credentials in `.env` (always required)
- Network access to the Drupal JSON:API (`drupal_jsonapi_base`) for
  `--source drupal`
- Qdrant + Azure embedding credentials — only without `--skip-index`
- Azure Document Intelligence — only for scanned PDFs in `hybrid`/`azure_only`
  mode; pass `--extraction-mode local_only` to guarantee no Azure calls

## Usage

```bash
# 3 articles + their attached PDFs, MySQL verified, no embeddings/Qdrant needed
python -m app.local_tests.run_ingestion_test --bundle article --max-docs 3 --skip-index

# Same but with real embeddings + Qdrant indexing
python -m app.local_tests.run_ingestion_test --bundle article --max-docs 3

# Local PDF folder instead of Drupal
python -m app.local_tests.run_ingestion_test --source pdf --make-sample --skip-index

# Run twice: the second run should report the same documents as UNCHANGED
python -m app.local_tests.run_ingestion_test --bundle article --max-docs 3 --skip-index

# Remove the test tables / collection when done
python -m app.local_tests.run_ingestion_test --cleanup
```

Exit codes: `0` all checks passed, `1` a check failed or a document errored,
`2` nothing to ingest, `3` real indexing requested but Qdrant/embeddings
unreachable (re-run with `--skip-index`).

## Files

| File | Purpose |
| --- | --- |
| `run_ingestion_test.py` | Runner: env isolation, pipeline execution, checks |
| `serialize.py` | Turn captured stage artifacts into complete, untruncated dicts |
| `dump.py` | Render a document dict as a readable full text dump |
| `db_checks.py` | MySQL read-back (state row, facets, links, log rows) |
| `reporting.py` | Console + file output (sections, PASS/FAIL checks, sinks) |
| `data/` | PDF source folder for `--source pdf` (git-ignored) |
| `results/` | One folder of raw dumps per run (git-ignored) |
