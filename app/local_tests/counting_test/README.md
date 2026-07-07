# Catalog counting test (MySQL integration)

Asserts the **exact numbers** behind "how many `<bundle>` / by `<author>` / on
`<date>`" — i.e. `state.count_documents` plus the write / backfill /
delete-cascade plumbing — against a **real MySQL**.

It creates a throwaway table `ingest_state_counttest` (+ `_author` / `_category`
children), seeds known ground truth via `state.upsert`, runs the checks, and
drops the tables. The real `ingest_state` is never touched.

Needs **MySQL configured** (`MYSQL_HOST/PORT/USER/PASSWORD/DATABASE`). Needs no
Qdrant, Azure, or network. The pure/routing logic (bundle normalization, date
range, filter wiring) is covered separately and DB-free in `tests/test_counting.py`.

## Run

```bash
python -m app.local_tests.counting_test.run
```

Exit code `0` = all checks passed, `2` = a check failed or MySQL was unreachable.

## What it checks

| Phase | Covers |
|-------|--------|
| A — reads | bundle scoping; unknown bundle → 0 (not all); `COUNT(DISTINCT)` author with multi-author dedup and substring match; half-open date bounds (Mar-16 excluded); year span; combined bundle+author+date; NULL `published_at` excluded from date filters; non-website docs ignored |
| B — re-index | re-`upsert` replaces a document's author rows (no duplicates, old authors gone) |
| C — delete | `state.delete` cascades to the author/category child rows |
| D — backfill | `backfill_facets` returns False for an unknown id (no orphan rows), True for an existing one, and is idempotent on re-run |
