# Local ingestion test

Standalone harness that runs **only the ingestion pipeline** against a folder
of PDFs and prints a stage-by-stage report per document, ending with a
read-back of everything MySQL stored and `[PASS]/[FAIL]` checks.

## What it exercises

The real per-document ingestion path (`app/ingestion/pipeline.py`):

1. **Change detection** — new / changed / unchanged / deleted vs the state table
2. **Extraction** — pages, per-page route (pymupdf / azure / camelot), tables, PDF metadata
3. **Canonical document** — document_id, title, sections, content hash, facets
4. **Chunking** — parent/child chunks, token stats, the exact payload a chunk is indexed with
5. **Indexing** — embeddings + Qdrant upsert (or stubbed, see `--skip-index`)
6. **MySQL catalog** — state row, author/category facet rows, term/attachment
   links, ingest-log rows, each verified against the canonical data

## Isolation

Writes never touch the real catalog. Before app settings load, the runner
overrides the environment so everything lands in:

- MySQL: `local_test_ingest_state` (+ `_author`, `_category`, `_term`,
  `_attachment`) and `local_test_ingest_log`
- Qdrant: `local_test_documents`

`--cleanup` drops these afterwards and refuses to drop anything not prefixed
`local_test_`.

## Prerequisites

- MySQL reachable with the credentials in `.env` (always required)
- Qdrant + Azure embedding credentials — only without `--skip-index`
- Azure Document Intelligence — only for scanned PDFs in `hybrid`/`azure_only`
  mode; pass `--extraction-mode local_only` to guarantee no Azure calls

## Usage

```bash
# Cheapest full pass: generated sample PDF, no Azure/Qdrant needed
python -m app.local_tests.run_ingestion_test --make-sample --skip-index --extraction-mode local_only

# Your own PDFs (drop them in app/local_tests/data or point --dir anywhere)
python -m app.local_tests.run_ingestion_test --dir "path/to/pdfs" --skip-index

# Full pipeline including embeddings + Qdrant indexing
python -m app.local_tests.run_ingestion_test --make-sample

# Run twice: the second run should report every document as UNCHANGED
python -m app.local_tests.run_ingestion_test --skip-index

# Remove the test tables / collection when done
python -m app.local_tests.run_ingestion_test --cleanup
```

Exit codes: `0` all checks passed, `1` a check failed or a document errored,
`2` nothing to ingest.

## Files

| File | Purpose |
| --- | --- |
| `run_ingestion_test.py` | Runner: env isolation, pipeline execution, report |
| `db_checks.py` | MySQL read-back (state row, facets, links, log rows) |
| `reporting.py` | Console formatting (sections, tables, PASS/FAIL checks) |
| `data/` | Default PDF source folder (contents git-ignored) |
