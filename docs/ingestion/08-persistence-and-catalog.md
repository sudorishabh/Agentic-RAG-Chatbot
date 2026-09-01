# 08 — Persistence and the Catalog

**Purpose.** Record, durably and transactionally, what each document is, where it
came from, when it was last seen, what facets it carries, which files it links to,
and what happened to it on every run.

**Inputs.** A `CanonicalDocument`, its `ChangeRecord`, the content hash, the
version, and whether this write actually re-indexed.

**Outputs.** Rows in `documents` and its child tables, an appended `ingest_log`
row, and — as a consequence — the crawl cursor for the next run.

**Components.** `app/catalog/` (schema, state, log, retries, dead_links,
enrichment, theme_taxonomy, date_decisions, author_names, queries),
`app/core/clients/database.py`.

---

## Why MySQL exists here at all

Qdrant holds the content. MySQL holds everything you cannot ask a vector store:

- **The crawl cursor.** `MAX(changed_mark)` per bundle is the incremental window.
- **Change detection.** Fingerprints and content hashes, per document.
- **Provenance.** Where a date came from, which pipeline built the document, which
  files a page links to.
- **Exact counts.** "How many documents does theme X have?" is a `COUNT(DISTINCT
  document_id)` over a facet table, not an approximation over payloads.
- **The audit trail.** An append-only log of every event, which is what makes
  historical failures recoverable at all.

The ingestion server is therefore **not ready without MySQL**
(`require_for_readiness("mysql")`), while the retrieval server deliberately is.

---

## Table inventory

All names are prefixed by `ingest_state_table` (default `documents`) or
`ingest_log_table` (default `ingest_log`). Both are passed through
`safe_table(name, default)`, which requires alphanumerics-plus-underscore — a bad
setting cannot become a SQL-injection vector via f-string interpolation.

| Table | Grain | Lifecycle |
| --- | --- | --- |
| `documents` | one row per document | upserted; deleted on removal |
| `documents_author` | one row per (document, author) | replaced wholesale per ingest; FK cascade |
| `documents_tag` | one row per (document, tag) | same |
| `documents_theme` | one row per (document, theme) + hierarchy | same |
| `documents_attachment` | one row per (file_uuid, document_id) | same |
| `documents_retry` | one row per unresolved document | written on failure, deleted on success. **No FK** |
| `documents_dead_link` | one row per 4xx attachment | written on 4xx, expires by fingerprint. **No FK** |
| `documents_enrichment` | one row per `content_hash` | cache. **No FK** |
| `documents_date_decision` | one row per document | the date audit trail and review queue |
| `documents_knowledge_run` | one row per (document, doc_version) | knowledge-stage report |
| `documents_entity_mention` etc. | knowledge layer | see [09](09-knowledge-layer-and-graph.md) |
| `ingest_log` | one row per event per run | **append-only**, retention-pruned |

### `documents`

```sql
document_id      VARCHAR(255)  PRIMARY KEY
source_type      VARCHAR(32)   NOT NULL      -- website | pdf_attachment
source_key       VARCHAR(1024) NOT NULL      -- page URL, or the PDF URL
bundle           VARCHAR(128)
entity_type      VARCHAR(32)                 -- node | block_content
fingerprint      VARCHAR(128)  NOT NULL
content_hash     VARCHAR(64)   NOT NULL DEFAULT ''
doc_version      INT           NOT NULL DEFAULT 1
pipeline_version VARCHAR(32)                 -- NULL reads as "not current"
changed_mark     BIGINT                      -- the crawl cursor
published_at     DATETIME
document_published_at  DATETIME
published_at_source     VARCHAR(16)          -- created | cms_field | document_text
published_at_precision  VARCHAR(8)           -- year | month | day
title            VARCHAR(1024)
url              VARCHAR(1024)
raw_meta         JSON
indexed_at       DATETIME
updated_at       DATETIME      NOT NULL
KEY idx_source_type, idx_bundle (source_type, bundle), idx_pipeline_version
```

`idx_pipeline_version` exists because the corpus reprocessor's whole query is
"which documents are not on the current version".

`title` and `url` are on the row so structured list/lookup queries can be answered
from the catalog with no live site fetch.

### `documents_author`, `documents_tag`

```sql
document_id VARCHAR(255) NOT NULL,
{facet}     VARCHAR(255) NOT NULL,
UNIQUE KEY uq_{facet} (document_id, {facet}),
KEY idx_val ({facet}),
FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
```

The unique key is what says the facet is a **set**. Nothing else did: with only the
two lookup keys, a writer that emitted the same pair twice was simply believed, and
every `COUNT` over the table was wrong by the duplication. It also subsumes the old
`idx_doc` — `document_id` is its leftmost column, so per-document lookups and the
foreign key are served by it alone.

`documents_author` additionally carries `author_norm`. `author` is exactly what
Drupal sent and is never rewritten — it is what an answer displays and what makes a
count traceable to the source. `author_norm` is the formatting-normalised form
(`app/catalog/author_names.py`), which is what a *distinct name* count should group
on: "Dr Jayanta Mitra" and "Dr. Jayanta Mitra" are one name written two ways. It is
emphatically **not** a person id — two people called "Arun Kumar" share a normalised
form here exactly as they already share a raw one.

### `documents_theme`

```sql
document_id VARCHAR(255) NOT NULL,
theme       VARCHAR(255) NOT NULL,
theme_type  ENUM('primary','sub') NOT NULL DEFAULT 'sub',
parent      VARCHAR(255),
theme_group ENUM('main','other'),
PRIMARY KEY (document_id, theme),
KEY idx_val (theme), KEY idx_parent (parent), KEY idx_group (theme_group),
FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
```

Its own DDL rather than the generic facet one, because it carries hierarchy. See
[06, Theme classification](06-canonical-document-and-dates.md#theme-classification)
for what fills it.

### `documents_attachment`

```sql
file_uuid   VARCHAR(255)  NOT NULL,
document_id VARCHAR(255)  NOT NULL,
origin      VARCHAR(16)   NOT NULL,      -- attachment | inbody
url         VARCHAR(1024),
filename    VARCHAR(255),
PRIMARY KEY (file_uuid, document_id),
KEY idx_doc (document_id),
FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
```

The composite key is the whole point: **one in-body PDF can be linked from several
nodes** — 84 of them are. The PDF's own catalog row is keyed by `file_uuid` in
`documents`, so this table is purely the many-to-many claim table, and it is what
`orphaned_attachments` asks.

### Tables with no foreign key, and why

`documents_retry`, `documents_dead_link` and `documents_enrichment` are deliberately
**not** children of `documents`.

- **`documents_retry`.** A placeholder row in `documents` would count as a
  catalogued document in every analytical read — bundle counts, document lists,
  theme distributions — which is precisely the claim a failed document must not make.
- **`documents_dead_link`.** A dead link never becomes a document row, so there is
  no parent to hang off.
- **`documents_enrichment`.** Three reasons: it has to survive a state-table reset
  (the usual way to force a reindex, and exactly when re-paying for enrichment
  hurts most); documents whose body text is identical share one row and enrich
  once; and nothing may cascade-delete it when a document row goes away, because
  the same content may come back under a different id. The trade is that orphan
  rows have to be pruned rather than cascaded — they are small and act as a cache
  for re-added content, so pruning is a maintenance task, not a correctness one.

### `ingest_log`

```sql
id BIGINT AUTO_INCREMENT PRIMARY KEY,
run_id VARCHAR(64), document_id VARCHAR(255) NOT NULL,
source_type VARCHAR(32) NOT NULL, source_path VARCHAR(1024), source_url VARCHAR(1024),
bundle VARCHAR(128), tags VARCHAR(1024), title VARCHAR(512),
status VARCHAR(32) NOT NULL, doc_version INT, chunks_indexed INT,
fingerprint VARCHAR(128), content_hash VARCHAR(64), error_message TEXT,
event_time DATETIME NOT NULL,
KEY idx_document, idx_source_type, idx_event_time, idx_run
```

Append-only, one row per document per run, separate from the overwrite-in-place
`documents` table. `status` takes the outcome vocabulary. Every value is clipped to
its column width by `_clip` before insert, so an over-long title cannot fail a write.

`log.record` **never raises**: logging must not break ingestion. A failure is
`logger.exception`-ed and the pipeline continues. It is also a no-op when
`ingest_log_enabled` is false.

---

## Schema management

`app/catalog/schema.py` only ever `CREATE`s or `ALTER`s — it never touches rows. Each
`ensure_*` function is idempotent and called once per process (via
`state.ensure_table()`, `log.ensure_table()`, etc.).

`ensure_state_table()` does, in order: the main DDL, then `_ensure_column` for every
column added after the original DDL (`published_at`, `document_published_at`,
`published_at_source`, `published_at_precision`, `title`, `url`,
`raw_meta`, `entity_type`, `pipeline_version`), then `_ensure_index` for
`idx_pipeline_version`, then the facet migrations, then the child tables.

Ordering matters in two places:

- `migrate_author_names` runs **before** `migrate_facet_uniqueness`, because
  collapsing a duplicated author pair has to carry `author_norm` with it.
- `_STATE_THEME_DDL` is created **then** `migrate_theme_hierarchy` runs: a fresh
  install gets the hierarchy from the DDL and the migration no-ops; a legacy table
  survives `CREATE TABLE IF NOT EXISTS` untouched and gets its columns from the
  migration.

### Historical renames

- Table names were simplified from `ingest_state*` to `documents*`. A deployment
  with existing data must run `python -m scripts.rename_catalog_tables` **once**
  before or at deploy, or the new tables are created empty beside the old ones.
- The theme facet was renamed from `category`. That one is handled here, in
  `migrate_renamed_facets`, rather than by the script, because it also has to rename
  the child table's **value column** and must work for whatever
  `ingest_state_table` prefix the process is configured with. `CREATE TABLE IF NOT
  EXISTS` cannot do it: a deployment can sit on `documents_theme` while its value
  column is still `category`.
- The taxonomy-term tables (`terms`, `term_aliases`, `documents_term`) were retired
  and dropped. The catalog is keyed by name, so themes live in `documents_theme` and
  tags in `documents_tag`; taxonomy no longer reaches storage at all.
- `source_type` was renamed `article` → `website`. Change detection loads **both**
  (`{**state.load("article"), **state.load("website")}`) so it stays incremental
  across the transition; `python -m scripts.migrate_source_type_website` completes it.

---

## The write path

### `_persist` — the ordering is the trick

```python
previously_linked = _linked_attachments(record)     # 1. read the OLD links
_save_state(record, doc, content_hash, version, indexed=indexed)   # 2. write
still_claimed = {link.uuid for link in doc.file_links}
released = [f for f in previously_linked if f not in still_claimed]
_delete_orphaned_attachments(released, record, run_id)              # 3. re-examine
```

`state.upsert` replaces a document's link rows **wholesale**, so once it has run
there is no record of what the document used to reference — the old links have to be
read first or not at all.

Step 3 must come **after** the write. `orphaned_attachments` asks the catalog on its
own pooled connection and can only see committed rows; run before the write it would
still find the old link and conclude the attachment is spoken for.

`_linked_attachments` is skipped entirely when `record.prior is None`: link rows are
foreign-keyed to the document, so one that has no row can have no links, and a first
ingestion should not pay for a lookup that can only come back empty. It fails open
with a warning — "any it drops in this update will be left in place".

### `state.upsert` — one transaction

```sql
INSERT INTO documents (...) VALUES (...)
ON DUPLICATE KEY UPDATE
  source_type = VALUES(source_type),
  source_key  = VALUES(source_key),
  bundle      = VALUES(bundle),
  entity_type = COALESCE(VALUES(entity_type), entity_type),
  fingerprint = VALUES(fingerprint),
  content_hash = VALUES(content_hash),
  doc_version = VALUES(doc_version),
  pipeline_version = COALESCE(VALUES(pipeline_version), pipeline_version),
  changed_mark = VALUES(changed_mark),
  published_at = VALUES(published_at),
  document_published_at = COALESCE(VALUES(document_published_at), document_published_at),
  published_at_source    = VALUES(published_at_source),
  published_at_precision = VALUES(published_at_precision),
  title = VALUES(title), url = VALUES(url),
  raw_meta   = COALESCE(VALUES(raw_meta), raw_meta),
  indexed_at = COALESCE(VALUES(indexed_at), indexed_at),
  updated_at = VALUES(updated_at)
```

then, in the **same transaction**, `_replace_authors`, `_replace_facet("tag")`,
`_replace_themes`, `_replace_attachment_links`, then one `commit()`.

So a document and its facets are never observably out of step: either the whole
update lands or none of it does.

#### `COALESCE` vs `VALUES`, field by field

This is the subtlest part of the schema, and each choice is load-bearing.

| Column | Rule | Why |
| --- | --- | --- |
| `entity_type` | `COALESCE` | A caller that does not know passes NULL; a stored value must not be erased. |
| `pipeline_version` | `COALESCE` | Only a write that actually re-chunked may claim the version. A fingerprint refresh passes NULL, so a document that has not been rebuilt still reads as **stale** and is rebuilt later. |
| `raw_meta` | `COALESCE` | Same: a path that has no metadata must not blank it. |
| `indexed_at` | `COALESCE` | An `unchanged_content` write (`mark_indexed=False`) passes NULL and must not clear the fact that the document *is* indexed. |
| `document_published_at` | `COALESCE` | Only a path that actually resolved a document-stated date may write this. |
| `published_at` | `VALUES` | Overwritten outright — it is the resolved value for this run. |
| `published_at_source`, `published_at_precision` | **`VALUES`, not `COALESCE`** | These *describe* `published_at`, which is itself overwritten. A provenance that outlived the value it describes would be worse than none, because it would read as evidence for a date it was never about. |

#### Timestamp normalisation

`_to_datetime(value)` parses ISO (tolerating a trailing `Z`) and converts to
**naive UTC**. That is why `source_dates.as_published_at` emits midnight **UTC** —
see [06, Timezone](06-canonical-document-and-dates.md#timezone-ist-and-why-it-is-not-optional).
An unparseable value becomes `NULL` rather than raising.

### Facet replacement

Every facet is rewritten wholesale on every ingest — delete-then-insert per
document. Two payoffs: **a reindex heals drift**, and a document that loses its last
theme is cleaned up rather than keeping a stale row.

#### `_stored_values` — truncate first, de-duplicate second

```python
return list(dict.fromkeys(v[:255] for v in values if v))
```

The other order de-duplicates strings the database will never hold: two tags
differing only past character 255 are distinct as read and identical as written, so
the old order emitted two rows the table then had no constraint to reject. **144
duplicate (document, tag) pairs came from exactly that.**

Order is preserved — it is the order the source listed them in, and a facet list
that reshuffles itself between ingests is noise in every diff.

#### `_KEEP_FIRST` — letting the database decide sameness

```sql
INSERT ... ON DUPLICATE KEY UPDATE document_id = document_id
```

MySQL compares the unique key under the **column collation** —
`utf8mb4_0900_ai_ci` here, which folds case and accents. `_stored_values`
de-duplicates in Python, which folds neither, so a source that tags one document
both "Climate Variability" and "climate variability" offers two values the index
accepts as one. Without this clause the second row raises error 1062 and takes the
**whole document's transaction** down with it — the document does not persist at all
over a repeated tag.

Letting the database decide which values are the same string is the point: Python
cannot restate that rule without reimplementing Unicode collation, and would drift
from it the moment the column is altered. First spelling wins, and `_stored_values`
preserves source order, so which one that is stays stable across ingests.

`document_id = document_id` rather than `INSERT IGNORE`: this absorbs a duplicate
key and **nothing else**. `IGNORE` would equally downgrade a foreign-key violation
or an over-long value to a warning, hiding real corruption.

#### Attachment links: first link wins

```python
seen: dict[str, AttachmentLink] = {}
for link in links:
    if link.file_uuid and link.file_uuid not in seen:
        seen[link.file_uuid] = link
```

An explicit `field--file` attachment reference carries `url` and `filename` and
outranks a later in-body sighting of the same PDF.

---

## Orphaned attachment collection

A PDF is its own document, and one PDF is often reachable from several pages. So
deleting a page must **not** delete its attachments — only end that page's claim on
them. The attachment goes when the last claim does.

```sql
SELECT d.document_id FROM documents d
WHERE d.document_id IN (...)
  AND d.source_type = 'pdf_attachment'
  AND NOT EXISTS (SELECT 1 FROM documents_attachment a
                  WHERE a.file_uuid = d.document_id [AND a.document_id NOT IN (...)])
```

`documents_attachment` holds every claim, and the deleted parent's rows have already
cascaded away by the time this runs, so **an id with no rows left has no parent
left**. The query is restricted to ids that are `pdf_attachment` documents in their
own right, so a file that was linked but never successfully ingested costs no delete
call.

`ignoring_parents` answers the same question a step earlier — "treat these parents as
though they were already gone" — which is what lets the reconcile dry run report the
attachments a deletion *would* orphan, using this query rather than a second copy of
its reasoning.

### Two ways an attachment loses its last parent

`_delete_orphaned_attachments` covers both:

1. **The page is deleted outright.** `_handle`'s `DELETED` branch reads
   `attachment_ids_for(document_id)` **before** the delete (the link rows cascade
   away with the row), then calls the collector.
2. **The page simply stops referencing it.** The link row is no longer written, and
   nothing else in the pipeline would ever notice — the crawl only reaches an
   attachment *through* a parent it no longer has. `_persist` computes
   `previously_linked - still_claimed` and calls the collector on the difference.

Without this, an attachment outlives every page that referenced it and stays
searchable forever.

Each orphan gets `delete_document(orphan)` + `state.delete([orphan])` and a
**synthetic `deleted` log row**, so the removal is auditable even though no crawl
record produced it. The log line reports both numbers:

> Deleted 2 attachment(s) orphaned by <uuid>; 3 still linked elsewhere.

**Fails open at every step.** An attachment that survives a failure here is the
behaviour that predates the function, and is worth far less than the parent delete
that already succeeded.

### Diagram to include: attachment claim graph

Three page nodes and two PDF nodes, with claim edges from `documents_attachment`.
Show PDF-A claimed by pages 1 and 2, PDF-B claimed by page 2 only. Then two panels:
"page 2 deleted" (PDF-A survives on page 1; PDF-B is orphaned and deleted) and
"page 2 edited to drop PDF-B" (identical outcome, reached through `_persist` rather
than the delete branch). This is the clearest way to show why both call sites exist.

---

## The enrichment cache

Optional (`enrichment_enabled`, default **off**), and worth documenting here
because its storage design is unusual.

`pipeline._enrich` runs **before** the content-changed branch, so an
unchanged-content document that predates enrichment still picks up an abstract as it
is re-crawled; a cache hit costs one indexed lookup.

```
cached = enrichment.get(content_hash, version=abstract_version())
  hit (abstract present)          -> "hit"
  row exists, attempts >= max     -> "exhausted"
  generate_abstract raises
        interpreter shutdown      -> "aborted"     (no attempt owed)
        otherwise                 -> record_failure -> "failed"
  generate_abstract returns None  -> "skipped"     (too short; never retried)
  otherwise                       -> put(...)      -> "stored"
```

**Keyed by `content_hash`, not `document_id`**, which is what makes it survive a
state-table reset and be shared by documents whose body text is identical (the same
PDF reached by two URLs, or linked from several nodes).

**Invalidated by version, not TTL.** Enrichment of immutable input does not go
stale, but a changed prompt, schema or model makes it wrong. `abstract_version()`
hashes the three prompts, both sizing constants and the chat deployment, so editing
a prompt invalidates every cached abstract automatically. A version mismatch reads
as a miss; `record_failure` restarts the attempt count on a new version, because a
new prompt deserves a fresh attempt budget.

**Failures are recorded, not just dropped.** Without a counter, a document that
always fails is retried at full cost on every sweep forever.
`enrichment_max_attempts` (default 3) stops it.

`generate_abstract` is adaptive: bodies under 600 characters are skipped (a `people`
record, a video stub — summarizing buys a paraphrase and a hallucination surface for
no gain); a document within 12,000 tokens gets one call; longer ones are windowed at
~6,000 tokens, mapped in parallel (4 workers) and reduced once. It **raises** on a
model failure so the caller can count it, and returns `None` only for a deliberate
skip.

The one raise the caller must *not* count is the shutdown race:
`is_shutdown_error(exc)` recognises `RuntimeError("... interpreter shutdown ...")`,
which is what an ingest worker thread hits when the main thread has already exited
(a Ctrl-C during a long extraction). The model was never asked, so counting it would
spend the budget on a Ctrl-C and could leave a big document permanently
abstract-less.

Outcomes are tallied per run as `enrich_hit` / `enrich_stored` / `enrich_skipped` /
`enrich_failed` / `enrich_exhausted` / `enrich_error` / `enrich_aborted`, because
**this cache's failure mode is silently re-paying for every document.** Nothing here
can stop a sweep.

The backfill for documents that never change:

```bash
python -m app.ingestion.enrich_backfill --limit 200 [--dry-run]
```

Kept as its own CLI rather than folded into the sweep on purpose: it is the one
operation here that can spend a lot of money quickly, so it should be something a
human runs with a `--limit` and watches, not something a scheduled job discovers at
2am. For the same reason it ignores `enrichment_enabled` — you may well want to
backfill *before* turning the sweep on. It reconstructs document text from the
vector store (concatenating child chunks in order) rather than re-extracting from
source, so no PDF is re-downloaded and no site is re-crawled; the reconstruction has
some overlap duplication but is close enough for a summary, and an abstract written
here is interchangeable with one the sweep would have written for the same content
hash.

---

## Connection management

`MySQLPool` (`app/core/clients/database.py`) is a hand-rolled LIFO pool:

- `mysql_pool_size` (default 5) connections, created lazily.
- `mysql_pool_timeout` (default 30s) is how long a caller waits for a free
  connection before `TimeoutError` — **fail fast instead of blocking forever**.
- On checkout: `ping(reconnect=True)` and `rollback()`, so a connection that died
  while idle is replaced and no transaction state leaks between callers.
- `_open_new` releases the reserved slot if the connect fails — otherwise a
  transient outage permanently shrinks the pool until every checkout blocks forever.
- The connect happens **outside** the lock, so a slow handshake never serialises
  checkouts.
- On any exception in the `with` block, the connection is **discarded** rather than
  returned, because its state is unknown.

`DictCursor`, so every read in the catalog layer is `row["column"]`.

**Keep `ingest_workers` below `mysql_pool_size`.** A worker holds a connection for
the duration of a catalog write; exhausting the pool turns into per-document
`error` outcomes.

Each catalog module opens its **own** connection per call and commits. There is no
cross-module transaction, and that is deliberate: it is what lets every write on the
ingest path fail open independently.

---

## Validation at this stage

| Check | On failure |
| --- | --- |
| Table name is alphanumeric-plus-underscore | falls back to the default name |
| Facet values truncated to 255 before de-duplication | over-long values stored truncated |
| Duplicate facet key under collation | absorbed by `_KEEP_FIRST`; first spelling wins |
| FK to `documents` on facet/link rows | a facet row cannot exist without its document |
| `document_id` non-empty | row skipped (`retries.record`, `dead_links.record`) |
| Log field widths | clipped by `_clip` |
| Timestamp parses | stored as `NULL` |
| Theme is not a bucket / stringified boolean | row dropped |

## Failure scenarios

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| MySQL unreachable at run start | `state.ensure_table()` raises | The run fails; the scheduler logs it | Next interval |
| MySQL unreachable mid-run | `state.upsert` raises inside `_handle` | `error` outcome, retry marker attempted (also fails open), previous version intact | Next sweep |
| Pool exhausted | `TimeoutError` | Per-document `error` | Lower `ingest_workers` |
| Duplicate facet under collation | error 1062, absorbed | Row skipped | — |
| Over-long fingerprint (in-body URL) | Was MySQL 1406 | Prevented: in-body records are fingerprinted on their uuid, not their URL | — |
| Log write fails | `except` in `log.record` | `logger.exception`; ingestion continues | The event is lost. `documents` is still correct |
| Log grows without bound | table size | `prune()` after each sweep, in 10,000-row batches so a large backlog never holds one long row-lock transaction | Set `ingest_log_retention_days` |
| Orphan check fails | `except` in `_delete_orphaned_attachments` | Warning; attachments left in place | Next sweep, or a manual `delete_document` |
| Link read fails before a rewrite | `except` in `_linked_attachments` | Warning; dropped links stay in place | Next sweep |
| Enrichment table unreachable | `except` in `_enrich` | `enrich_error` counted; document ingested without an abstract | Next sweep, or the backfill |
| Legacy table names still in place | New tables created empty | — | `python -m scripts.rename_catalog_tables` |
| `documents_theme` value column still `category` | `migrate_renamed_facets` | Renamed automatically on `ensure_state_table` | — |
| Enrichment orphan rows accumulate | Table size | Not cascaded, by design | Prune as maintenance |

## Observability

Run-level:

- `Deleted %s (%s)` / `Deleted %d attachment(s) orphaned by %s; %d still linked elsewhere.`
- `Unchanged content for %s; fingerprint refreshed.`
- `%s %s -> v%d` — status, id, new version.

Useful queries:

```sql
-- Corpus shape
SELECT source_type, bundle, COUNT(*) FROM documents GROUP BY 1, 2 ORDER BY 3 DESC;

-- Freshness
SELECT source_type, MAX(updated_at), MAX(indexed_at) FROM documents GROUP BY 1;

-- The crawl cursor, per bundle
SELECT bundle, FROM_UNIXTIME(MAX(changed_mark)) FROM documents
WHERE source_type = 'website' GROUP BY bundle;

-- Documents claimed indexed but never indexed
SELECT COUNT(*) FROM documents WHERE indexed_at IS NULL;

-- This run's outcomes
SELECT status, COUNT(*) FROM ingest_log WHERE run_id = '<run_id>' GROUP BY 1;

-- Recent errors, most useful first
SELECT event_time, document_id, bundle, LEFT(error_message, 200)
FROM ingest_log WHERE status IN ('error','skipped')
ORDER BY id DESC LIMIT 50;

-- Shared attachments
SELECT file_uuid, COUNT(*) c FROM documents_attachment
GROUP BY file_uuid HAVING c > 1 ORDER BY c DESC;

-- Theme distribution
SELECT theme, theme_type, theme_group, COUNT(DISTINCT document_id) n
FROM documents_theme GROUP BY 1,2,3 ORDER BY n DESC;

-- Enrichment cache health
SELECT version, COUNT(*), SUM(abstract IS NOT NULL), SUM(attempts)
FROM documents_enrichment GROUP BY version;
```

Over HTTP: `GET /ingest/log?limit=100&status=error&source_type=pdf_attachment`
(authenticated; newest first by insertion order, capped at 1000).

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `mysql_host` / `_port` / `_user` / `_password` / `_database` | — | Connection. |
| `mysql_connect_timeout` | `10` | Handshake timeout. |
| `mysql_pool_size` | `5` | Pooled connections. Keep above `ingest_workers`. |
| `mysql_pool_timeout` | `30` | Fail-fast checkout wait. |
| `ingest_state_table` | `documents` | Prefix for the state table and every child table. |
| `ingest_log_table` | `ingest_log` | Audit log table. |
| `ingest_log_enabled` | `true` | Whether events are recorded. |
| `ingest_log_unchanged` | `false` | Whether `UNCHANGED` gets a row. |
| `ingest_log_retention_days` | `90` | Prune window; `0` disables. |
| `enrichment_enabled` | `false` | Ingest-time abstracts. |
| `enrichment_max_attempts` | `3` | Failures before a document is left alone. |

## Downstream handoff and consumption

Ingestion has no callback to retrieval and no notification step. The hand-off is
**the state of the two stores**, and the contract is the payload schema plus the
catalog schema. Retrieval reads them independently, on the next query, with no
coordination.

That is what makes the invariants in this set matter: a payload field that stops
being written, or a payload index that was never created, degrades retrieval
silently.

### What reads the Qdrant payload

| Consumer | Reads | Consequence if ingestion gets it wrong |
| --- | --- | --- |
| Every search | `is_parent` (excluded), `is_current` | Parent points would be returned as hits |
| Filters | `source_type`, `language`, `section_type`, `categories`, `tags`, `authors`, `published_at` | An unindexed field means a full scan; a missing value means the document is invisible to that filter |
| The lexical leg | `chunk_text` via `MatchText` | Without the **text** index the keyword leg silently does nothing |
| Context expansion | `parent_chunk_id`, `chunk_index` | A dangling `parent_chunk_id` degrades to the child alone |
| Citations | `chunk_text`, `title`, `page_number`, `page_range`, `overlap_page_range`, `source_url`, `file_url` | A payload `chunk_id` that disagrees with the point id cites the wrong chunk |
| Recency and date ranges | `published_at`, `published_at_precision` | An undated document is **invisible**, not merely ranked low; a year marker read as a day invents a January publication |
| Prompt building and rerank | `has_table` | Tables are not boosted |
| Scoped retrieval and summarisation | `document_id`, `chunk_index` | Neighbour expansion breaks |
| The knowledge document loader | `document_id`, `is_parent`, `is_current`, `doc_version`, `chunk_index`, `chunk_text`, `content_hash` | Claim evidence points at text a citation cannot fetch |
| Drift detection | `pipeline_version`, `doc_version`, `chunk_id` | — |

**Anything added to `build_payload` is replicated once per chunk.** That is why the
table markdown is not stored (it is already inside `chunk_text`), why `raw_meta`
never leaves the catalog, and why the chunker copies fields into `DocumentMeta`
explicitly rather than spreading the canonical document.

### What reads the catalog

| Consumer | Reads | Purpose |
| --- | --- | --- |
| Change detection | `documents.fingerprint`, `content_hash`, `pipeline_version`, `changed_mark`, `doc_version`, `bundle` | The next run's window and decisions |
| The corpus reprocessor | `pipeline_version`, `changed_mark` per bundle | Which documents are stale and how far back to reach |
| Reconciliation | `doc_version`, `indexed_at`, `published_at`, `pipeline_version`, `raw_meta` | Cross-store invariants |
| Structured / analytical answers (`app/catalog/queries.py`) | facet tables, `documents.title`/`url`/`published_at` | Exact counts and document lists — `COUNT(DISTINCT document_id)`, not an approximation over payloads |
| The title-anchored retrieval leg | `state.website_titles()` — every website node's `(document_id, title, bundle)` | Finding the page a question names when that page's *text* is a list of link labels no embedding matches. Deliberately the whole set rather than a filtered slice: a `LIKE` per term spends its row budget on the organisation's own name, which appears in thousands of titles, and the first version returned two rows for "annual reports" and neither was the Annual Reports page |
| The "upcoming events" gate | `state.event_start_dates(ids)` — one batched `JSON_EXTRACT` | Gating a temporal question against the candidate set in one round trip rather than a per-block query storm |
| The knowledge layer | `state.raw_meta_for(id)`, `state.authors_for(id)` | CMS claims and PERSON corroboration. Both are read per document rather than carried on `StateRecord`, because `state.load` builds a record for every document of a source type and the metadata blob is by far the largest column |
| The semantic answer cache | `queries.corpus_revision()` — `MAX(indexed_at)` and `COUNT(*)` on `documents`, TTL-cached in-process | Self-invalidates a cached answer the moment ingestion changes what it was grounded in |
| Operators | `ingest_log`, `documents_retry`, `documents_dead_link`, `documents_date_decision`, `documents_knowledge_run` | Everything in [10](10-failures-retries-and-recovery.md) and [11](11-observability-and-monitoring.md) |

### The lineage chain

For any answer, the provenance is walkable end to end:

```
citation
  -> point payload: chunk_id, document_id, doc_version, pipeline_version,
                    page_number, source_url, file_url, published_at
  -> documents:     fingerprint (what the source looked like),
                    content_hash (what the text was),
                    published_at_source + _precision (where the date came from),
                    changed_mark (where it sat in the crawl),
                    indexed_at, raw_meta (the source record, verbatim)
  -> documents_date_decision: which rule decided the date, the quoted evidence,
                    the confidence, the model verdict, the prompt version
  -> ingest_log:    every run that touched it, its run_id, its outcome,
                    the chunk count, any error string
  -> documents_knowledge_run: which knowledge rules processed it
                    (knowledge_version), and what they produced
```

Four version stamps make that chain answerable rather than merely present:
`doc_version` (which generation of the document), `pipeline_version` (which code
built it), `embed_model` (which model produced its vectors), and
`knowledge_version` (which knowledge rules read it).

### What ingestion does *not* hand off

- **No notification.** Retrieval discovers new content on the next query.
- **Cache invalidation is indirect, through a read.** Ingestion does not push an
  invalidation; the semantic answer cache's partition key includes
  `app.catalog.queries.corpus_revision()` — `MAX(indexed_at)` plus the row count of
  `documents` — so a cached answer stops being reachable the moment a sweep actually
  re-chunks or adds/deletes a document, without ingestion knowing the cache exists.
  A fingerprint-only refresh (`unchanged_content`) does not move `indexed_at` and so
  does not invalidate anything, correctly: nothing retrievable changed. See
  `app.cache.cache_keys.semantic_partition`.
- **No access control.** `tenant_id` and `acl` are not written and not indexed. The
  corpus is public; every caller reads all of it.
- **No schema negotiation.** Adding a payload field is safe (readers strip absent
  keys); *relying* on a new field is not, until a `PAYLOAD` version bump and a
  reprocess have put it on every point.

## Hand-off

Once the catalog row and its facets are committed and the log says `indexed`, the
document's fate is settled and — only then — the optional knowledge layer may look
at it. See [09](09-knowledge-layer-and-graph.md).

---

Previous: [07 — Chunking, Embedding and Indexing](07-chunking-embedding-indexing.md) · Next: [09 — The Knowledge Layer and Graph](09-knowledge-layer-and-graph.md)
