# Drupal extraction test

Runs the full Drupal extraction flow over the live JSON:API corpus
(`DRUPAL_JSONAPI_BASE`) and writes a categorised result folder per node — all
output stays inside this directory under `results/`.

Flow exercised:

```
iter_records(bundles)       ->  DrupalRecord   (live JSON:API crawl)
chunk_drupal_record(record) ->  list[Chunk]    (canonical doc -> hierarchical chunks)
```

## Run

```bash
# the default bundles (drupal_extractor.DEFAULT_BUNDLES)
python -m app.local_tests.drupal_extraction_test.run

# specific bundles
python -m app.local_tests.drupal_extraction_test.run news events

# cap records per bundle (live crawls can be large)
python -m app.local_tests.drupal_extraction_test.run news --limit 5

# include unpublished nodes; skip embedding (vectors left null)
python -m app.local_tests.drupal_extraction_test.run news --include-unpublished --no-embed
```

## Output layout

```
results/
  _index.md            run overview table across all records
  _index.json          same, machine-readable
  <bundle>/<nid>_<slug>/
    00_summary.txt      headline stats + chunk breakdown
    00_summary.json
    01_record.md        title + url + extracted body text
    02_chunks.md        chunking output (parents + children)
    03_metadata.md      record metadata + canonical (chunking input) metadata
    03_metadata.json
    04_qdrant_points.json  exact id+vector+payload points upserted to Qdrant
    04_qdrant_points.md    readable preview (vectors truncated, chunk_text clipped)
    full_text.md        full record text (DrupalRecord.to_text())
    ERROR.txt           present only if that record failed (with traceback)
```

`results/` contents are git-ignored. A failure on one record is recorded in its
own `ERROR.txt` and does not stop the rest of the run; a bundle that fails to
fetch is skipped (logged) by `iter_records`. `04_qdrant_points.*` mirror
`index_chunks`: each child carries its real embedding vector, each parent a zero
vector, and the payload is exactly `Chunk.to_payload()` plus created_at /
updated_at. Embedding is best-effort — without the Azure OpenAI embedding config
the vectors are left `null` (or pass `--no-embed`) so the payloads are still
inspectable.
