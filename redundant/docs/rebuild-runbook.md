# Corpus rebuild runbook

How to clear the corpus and re-ingest it from source, on the pipeline as it
stands after the 2026-08-16 audit remediation.

Read this once before starting. Phase 2 is irreversible: it drops the catalog and
the vector collection. Everything before it only reads.

**Assumed working directory:** the repository root, with the project's virtualenv
active. Every command is run from there.

**Shell:** commands are written for PowerShell, which is this deployment's
default. The `python -m …` lines are shell-agnostic; only the file-redirect and
timestamp idioms differ if you use Git Bash instead.

---

## What a rebuild fixes, and what it does not

A rebuild re-ingests every document through the corrected pipeline, so it applies
in one pass:

| Fix | Effect on the rebuilt corpus |
|---|---|
| Chunker corrections (four, landed 2026-08-11) | Applied for the first time to every document |
| Chunk-id scheme (`b38220a`) | Ids consistent corpus-wide, so vector reuse works again |
| Payload cleanup | No `acl` / `tenant_id` / `term_ids` / `theme_ids` / `table_markdown` |
| PDF URL normalisation | ~15 `&amp;` PDFs and 1 whitespace-glued URL become reachable |
| `published_at` for blocks | ~109 previously undated documents carry a date |
| Facet truncation | No duplicate `(document_id, tag)` rows |
| Pipeline version | Every row and every point stamped, so the *next* code change is reachable |

It does **not** change retrieval behaviour, and it does not touch the knowledge
graph (`knowledge_enabled=false` on this deployment).

---

## Phase 0 — Stand down and take a copy

```powershell
# 1. Stop the ingestion server so its scheduler cannot sweep mid-reset.
#    (Ctrl-C the uvicorn process, or stop the service/container running
#     `uvicorn app.ingest_main:app`.)

# 2. Confirm nothing is mid-run: this must list no ingestion process.
Get-CimInstance Win32_Process -Filter "Name like '%python%'" |
  Where-Object { $_.CommandLine -match 'ingest|pipeline' } |
  Select-Object ProcessId, CommandLine

# 3. Back up MySQL. The data is disposable in principle; the backup is what
#    makes phase 2 reversible in practice.
$stamp = Get-Date -Format yyyyMMdd
mysqldump --single-transaction --routines --databases arc_db > "backup-arc_db-$stamp.sql"

# 4. Snapshot the Qdrant collection (server-side, under the Qdrant data dir).
Invoke-RestMethod -Method Post -Uri http://localhost:6333/collections/documents/snapshots

# 5. Confirm the code under test is the code that will run.
python -m pytest tests/ -q
```

Do not continue until the suite is green.

---

## Phase 1 — Record the "before" (reads only)

```bash
# The full cross-store picture. Save it: it is what "after" is compared against.
python -m scripts.verify_corpus --json > before-rebuild.json
python -m scripts.verify_corpus

# What the reprocessor sees (every document is unstamped before a rebuild).
python -m scripts.reprocess_corpus --dry-run

# Documents that failed before retry markers existed.
python -m scripts.recover_stranded --dry-run
```

Expected before a rebuild, on the 2026-08-16 corpus:

```
MySQL documents 11368   Qdrant points 149488
  FAIL indexed_without_points     85
  OK   points_without_catalog_row 0
  OK   duplicate_live_versions    0
  OK   version_mismatch           0
  OK   chunk_id_mismatch          0
  OK   children_without_parent    0
  FAIL catalog_pipeline_drift     11368
  FAIL point_pipeline_drift       11283
  FAIL documents_without_date     109
  skip graph_projection
```

---

## Phase 2 — Clear the corpus (**irreversible**)

### 2a. Drop the vector collection

```bash
python -c "from app.config import get_settings; from app.core.clients import get_qdrant_client; c=get_qdrant_client(); n=get_settings().qdrant_collection; print('deleting', n, c.delete_collection(n))"
```

### 2b. Drop the catalog state tables

Children first — they carry foreign keys to `documents`.

```sql
-- mysql -u <user> -p arc_db
DROP TABLE IF EXISTS documents_attachment;
DROP TABLE IF EXISTS documents_author;
DROP TABLE IF EXISTS documents_tag;
DROP TABLE IF EXISTS documents_theme;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS documents_retry;
DROP TABLE IF EXISTS documents_dead_link;
DROP TABLE IF EXISTS ingest_log;
```

Dropping rather than truncating is deliberate: the tables are recreated from the
current DDL, so they come back with `pipeline_version`, its index and the
`UNIQUE (document_id, value)` facet keys already in place, rather than being
migrated into them.

### What to keep, and why

| Table | Keep | Reason |
|---|---|---|
| `documents_enrichment` (8,337) | **Yes** | An LLM abstract cache keyed by `content_hash`, not by document id. Keeping it means the rebuild does not re-pay for abstracts whose body text is unchanged. `ENRICHMENT_ENABLED=true` on this deployment, so this is real money. |
| `documents_entity`, `_alias`, `_identifier`, `_assertion*` | **Yes** | Seeded from CMS records, not derived from chunks, and carry no foreign key to `documents`. Document ids are Drupal uuids and are reproduced by the rebuild, so their references stay valid. |
| `documents_date_candidate`, `_date_decision` | Optional | Shadow/review output, rewritten per document as it is re-ingested. Clearing them gives a clean review queue; keeping them is harmless. |

---

## Phase 3 — Recreate the shape, before any data lands in it

```bash
# Catalog tables, at the current DDL.
python -c "from app.catalog import schema; schema.ensure_state_table(); schema.ensure_log_table(); schema.ensure_retry_table(); schema.ensure_dead_link_table(); print('schema ready')"

# Collection + all thirteen payload indexes, at the configured vector size.
python -c "from app.core.clients import ensure_collection; ensure_collection(); print('collection ready')"
```

Verify both before ingesting — this is the step that used to be a manual script
nobody remembered:

```bash
python -c "
from app.config import get_settings
from app.core.clients import get_qdrant_client
from app.core.clients.vector_store import PAYLOAD_INDEXES
n = get_settings().qdrant_collection
info = get_qdrant_client().get_collection(n)
have = set(info.payload_schema or {})
print('vectors:', info.config.params.vectors.size)
missing = [f for f in PAYLOAD_INDEXES if f not in have]
print('indexes:', len(have), 'missing:', missing or 'none')
"
```

Expect `vectors: 3072`, thirteen indexes, `missing: none`.

---

## Phase 4 — Full re-ingest

An empty catalog has no high-water mark, so the ordinary crawl is a full crawl.
No special flag is needed and **no reconciliation flag should be passed** — there
is nothing to reconcile against.

```powershell
# Foreground, logging to a file you can tail. ~11,400 documents at the measured
# ~31 docs/min (ingest_workers=4) is roughly 6 hours.
python -m app.ingestion.pipeline 2>&1 | Tee-Object -FilePath "rebuild-$(Get-Date -Format yyyyMMdd).log"
```

Safe to interrupt. The crawl runs oldest-first and the high-water mark only
advances past documents that were processed, so re-running the same command
resumes where it stopped.

To go in controlled batches instead, set these for the run:

```powershell
$env:INGEST_MAX_DOCS_PER_RUN = 500
$env:INGEST_BATCH_SIZE = 50
$env:INGEST_BATCH_PAUSE_SECONDS = 2
python -m app.ingestion.pipeline      # re-run to continue; it resumes
```

Watch for, in the log:

- `ingest_throughput … documents_processed=… documents_per_minute=… errors=… indexed_without_date=…`
- `extracted to nothing; keeping the previous version` — the F1 guard firing. On a
  fresh corpus these documents have no previous version, so they simply do not
  index; they are recorded in `documents_retry` with the reason.

---

## Phase 5 — Verify the rebuild

```bash
python -m scripts.verify_corpus
```

Target state:

| Check | Expected |
|---|---|
| `indexed_without_points` | **0** — the F1 guard makes this unreachable |
| `points_without_catalog_row` | 0 |
| `duplicate_live_versions` | 0 |
| `version_mismatch` | 0 |
| `chunk_id_mismatch` | 0 |
| `children_without_parent` | 0 |
| `catalog_pipeline_drift` | **0** — everything built by the current pipeline |
| `point_pipeline_drift` | **0** |
| `documents_without_date` | Small; only sources that genuinely state no date |
| `graph_projection` | `skip` while `knowledge_enabled=false` |

Then confirm the payload cleanup actually landed. This counts points rather than
sampling one, because these fields sit on a *subset* of the collection and a
single point proves nothing:

```bash
python -c "
from qdrant_client.models import Filter, IsEmptyCondition, PayloadField
from app.config import get_settings
from app.core.clients import get_qdrant_client
c, n = get_qdrant_client(), get_settings().qdrant_collection
total = c.count(n, exact=True).count
print('points:', total)
for field in ('acl', 'tenant_id', 'term_ids', 'theme_ids', 'table_markdown', 'pipeline_version'):
    empty = c.count(n, count_filter=Filter(must=[IsEmptyCondition(is_empty=PayloadField(key=field))]), exact=True).count
    print(f'  {field:16} carried by {total - empty:>7} points')
"
```

Before the rebuild this reports the retired fields still riding ~99% of the
collection, and `pipeline_version` on none of it:

```
points: 149488
  acl              carried by  147996 points
  tenant_id        carried by  147996 points
  term_ids         carried by  123339 points
  theme_ids        carried by  101362 points
  table_markdown   carried by   37178 points
  pipeline_version carried by       0 points
```

After it, the first five must be **0** and `pipeline_version` must equal the
total point count.

And that the previously-broken PDFs came in. Save this as `check-urls.sql` and run
it through the mysql client, which avoids quoting `%` and `&` through two shells:

```sql
SELECT 'urls still carrying &amp;' AS check_name, COUNT(*) AS n
  FROM documents_attachment WHERE url LIKE '%&amp;%'
UNION ALL
SELECT 'urls glued onto the site base', COUNT(*)
  FROM documents_attachment WHERE url LIKE '%/ http%'
UNION ALL
SELECT 'undated documents', COUNT(*)
  FROM documents WHERE published_at IS NULL;
```

```powershell
Get-Content check-urls.sql | mysql -u <user> -p arc_db
```

Expect 0, 0, and a number far below 109.

Finally, a retrieval smoke test — the corpus is only rebuilt if it answers.
Use your usual evaluation query set (`scripts/eval_retrieval.py`), or simply ask
the running `/chat` a question whose answer you know.

---

## Phase 6 — Restore service

```bash
# The ingestion API now requires a bearer token (INGEST_AUTH_ENABLED defaults
# true). Either configure JWT_SECRET and INGEST_ADMIN_GROUP, or bind the server
# to loopback and set INGEST_AUTH_ENABLED=false deliberately.
uvicorn app.ingest_main:app --host 127.0.0.1 --port 8001
```

From here the scheduled sweep keeps the corpus current, and each sweep ends with
a reconciliation whose result is logged (`corpus_reconcile ok=…`) and served on
`/metrics`. Drift stops being something anyone has to go looking for.

---

## Afterwards: applying a future code change

The rebuild is the last time the corpus has to be cleared to pick up a pipeline
change. From now on:

1. Change the code, and bump the matching component in `app/ingestion/version.py`
   in the same commit.
2. Run `python -m scripts.reprocess_corpus --dry-run` to see the scope.
3. Run `python -m scripts.reprocess_corpus --limit 200` to sample it.
4. Run `python -m scripts.reprocess_corpus` to finish, in resumable passes.
5. Confirm with `python -m scripts.verify_corpus`.

No data is cleared at any point in that sequence: each document is replaced by
the swap only once its new version has been indexed.
