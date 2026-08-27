# 04 — Change Detection and Versioning

**Purpose.** Do the least work that leaves the corpus correct. Decide, per
document, whether to skip it, refresh a cheap marker, rebuild it, or delete it.

**Inputs.** The crawl's fingerprint for each record, the catalog's prior state,
retry markers, and the running `PIPELINE_VERSION`.

**Outputs.** A `ChangeStatus` per record, the incremental crawl window per bundle,
and a set of `DELETED` records.

**Components.** `app/ingestion/change_detection/base.py` (the decision),
`app/ingestion/change_detection/drupal.py` (the window and deletes),
`app/ingestion/version.py` (the code-change signal), `app/catalog/retries.py`,
`app/catalog/state.py`.

---

## Two independent change signals

A document is rebuilt when **the content changed** or **the code changed**. Both
are necessary, and the second was missing for a long time with a measurable cost:
four chunker correctness fixes, a chunk-id scheme change and a payload cleanup all
landed after the corpus was built and **none of them ever reached it**, because
`content_hash` covers body text and body text had not changed. Roughly 99% of
stored chunks came from a chunker with known, fixed defects, and no mechanism
existed to re-apply them.

| Signal | Stored as | Compares | Answers |
| --- | --- | --- | --- |
| Fingerprint | `documents.fingerprint` | the source's `changed` (or the in-body uuid) | "has the source been touched?" |
| Content hash | `documents.content_hash` | SHA-256 of body text | "is the text actually different?" |
| Pipeline version | `documents.pipeline_version` | `PIPELINE_VERSION` | "did the code that built this change?" |

They are checked at three different depths, cheapest first.

---

## The status decision

```python
def compute_status(prev, fingerprint):
    if prev is None:                      return NEW
    if prev.fingerprint != fingerprint:   return CHANGED
    if pipeline_stale(prev):              return CHANGED
    return UNCHANGED
```

`pipeline_stale(prev)` is `prev is not None and prev.pipeline_version != PIPELINE_VERSION`.
A stored version of `None` — a row written before versions were stamped — is
deliberately **not** current: unknown must read as stale, or the corpus that most
needs rebuilding is the one that never gets it. A document with no row at all is
not stale; it is unseen, and is built anyway.

Including the version check *here* is what makes it reachable. An `UNCHANGED`
record is never built, so its content hash and its stored version are never
compared to anything — a chunker fix would still never reach a document whose
source has not been edited since. The cost is deliberate and bounded: after a
version bump, every document the crawl *reaches* is rebuilt, and which documents
it reaches is still decided by the incremental window.

### Two-level skipping

**Level 1 — the fingerprint.** A matching fingerprint (and a current pipeline
version) stops the work *before* extraction: no download, no OCR, no embedding.
On an incremental sweep this is almost every document, which is why unchanged
scans cost nothing and are excluded from the batch budget.

**Level 2 — the content hash.** A *changed* fingerprint with a matching content
hash and a current pipeline version is the `unchanged_content` outcome: the
catalog row and fingerprint are refreshed, the payload title is refreshed if it
moved, and **nothing is re-embedded**. This is the common case for an editorial
touch that did not change the body.

```python
def content_changed(record, content_hash):
    return record.prior is None or record.prior.content_hash != content_hash

def needs_rebuild(record, content_hash):
    return content_changed(record, content_hash) or pipeline_changed(record)

def next_version(record):
    return record.prior.doc_version + 1 if record.prior else 1
```

When the content is unchanged but the pipeline moved, the pipeline logs it
explicitly:

> Rebuilding %s: content unchanged but pipeline version moved %s -> %s.

because during a corpus reprocess that is *every* document, and "why is it
re-embedding unchanged content?" should be answerable from the log.

---

## The content hash, and why it covers only body text

```python
def compute_content_hash(self):
    return sha256(self.full_text().encode("utf-8")).hexdigest()
```

`full_text()` is the sections' headings and text, joined. The title, the facets,
the dates and every other metadata field are **excluded**.

This is not a simplification, it is a correctness requirement: the hash has to be
reproducible from the source bytes alone. Any field that could be *derived* rather
than read — a title taken off a PDF cover page, a date the resolver decided —
would make the hash unstable across runs. `content_changed` would then fire on
every sweep, re-versioning, re-embedding and re-upserting the whole corpus
forever, silently and at full cost.

Metadata still reaches storage; it just does not gate re-indexing:

- The catalog takes the new title via `_save_state` on the `unchanged_content`
  path.
- The chunk payloads take it via `refresh_document_title(document_id, title)` —
  one `set_payload` call, no embedding.

---

## Pipeline version: the second change signal

```python
CHUNKING = 1; CHUNK_IDENTITY = 1; PAYLOAD = 1; EMBED_INPUT = 1
PIPELINE_VERSION = f"c{CHUNKING}.i{CHUNK_IDENTITY}.p{PAYLOAD}.e{EMBED_INPUT}"
```

Four components rather than one number, so a reader can see *what* changed and so
reconciliation can say "these points predate the payload change" rather than only
"these points are old".

### When to bump

Bump the component whose behaviour changed, **in the same commit as the change**.
The test is: *would identical input now produce different output?*

| Component | Bump when you change |
| --- | --- |
| `CHUNKING` | segmentation, packing, overlap, heading handling, section classification — different chunks for the same text |
| `CHUNK_IDENTITY` | how a chunk id is derived — different ids for the same chunks, which also means stored vectors can no longer be found for reuse |
| `PAYLOAD` | the fields written to each point — a reader expecting a field old points lack, or points carrying a field the code no longer writes |
| `EMBED_INPUT` | the exact string handed to the embedder (breadcrumb, overlap carry) — different vectors for the same chunk |

Do **not** bump for a refactor, a log line, a comment or a performance change that
leaves output identical. Every bump costs a full corpus reprocess, so a bump that
changes nothing is a bill with no benefit.

### Where it is written

- `documents.pipeline_version`, but **only on a write that actually re-chunked**.
  `_save_state` passes `PIPELINE_VERSION if indexed else None`, and the upsert
  `COALESCE`s it, so a fingerprint refresh leaves the stored value alone and a
  document that has not been rebuilt keeps reading as stale until it is.
- Every point payload, via `build_payload`. On the payload *as well as* the catalog
  row, because "which points predate the chunker fix" is a question about points,
  and the catalog cannot answer it for a document whose row says one thing while
  its points say another. Reconciliation checks both sides
  (`catalog_pipeline_drift`, `point_pipeline_drift`).

### Reaching documents the crawl cannot see

A code change moves nothing in Drupal, so a document last edited in 2018 stays
outside every incremental window forever. That is what
`app/ingestion/reprocess.py` exists for — it selects from the **catalog** and hands
the crawl a widened window. See
[12, Rebuild the corpus](12-operations-and-troubleshooting.md#rebuild-the-corpus-after-a-code-change).

---

## The incremental crawl window

Per node bundle:

```python
prior = {rows of `documents` for this bundle}
high  = max(changed_mark for rows with one)          # the high-water mark
floor = retry_floor.get(bundle)                      # earliest unresolved failure
if high is not None and floor is not None:
    high = min(high, floor)
filter: changed >= high
```

Three things to notice.

**`>=`, not `>`.** A record edited in the same second as the stored mark must not
be skipped. The boundary-second records re-fetched each run are cheap and resolve
to `UNCHANGED` on their fingerprint.

**The mark is a maximum over successes.** A row exists only when a document was
written, so `MAX(changed_mark)` is a resume cursor — but only if *every* document
below it succeeded too. One error or skip in the middle breaks that, and
oldest-first ordering does not help: the documents *after* the failure still raise
the mark above the hole.

**The floor is the repair.** `retries.floors()` asks for exactly what the crawl
needs:

```sql
SELECT bundle, MIN(changed_mark) FROM documents_retry
WHERE bundle IS NOT NULL AND changed_mark IS NOT NULL GROUP BY bundle
```

The window is pulled back to the earliest unresolved failure, so it stays inside
the window. It only ever *lowers* the bound, so the crawl can return more than
before but never less. Everything already indexed inside the widened window
resolves `UNCHANGED` on its fingerprint, which costs no work and no batch budget.

**Block sources have no window.** `incremental=False` means `changed_since=None`:
the whole (small) set is fetched every run and change-detected purely on
fingerprints.

**`extra_floors`.** `detect_drupal_changes(extra_floors={bundle: mark})` widens the
window for named bundles exactly as a retry marker does — the lowest floor wins.
It is how a catalog-driven pass reaches documents the cursor has long since passed,
without writing a marker row per document or bypassing the ordinary crawl.

### Diagram to include: the crawl window

A horizontal timeline of a bundle's `changed` values. Mark: the high-water mark;
one failed document sitting *below* it; the retry floor pulling the left edge back
to that document; and the shaded window `[floor, ∞)`. Annotate the region between
the floor and the mark as "re-fetched, resolves UNCHANGED, costs a fingerprint
comparison". This single picture explains most of the retry design.

---

## Retry markers

`documents_retry` — one row per document that reached processing and did not come
out indexed.

```sql
document_id VARCHAR(255) PRIMARY KEY,
source_type VARCHAR(32) NOT NULL,
bundle      VARCHAR(128),
changed_mark BIGINT,
outcome     VARCHAR(16) NOT NULL,
attempts    INT NOT NULL DEFAULT 1,
error       TEXT,
first_seen  DATETIME NOT NULL,
updated_at  DATETIME NOT NULL,
KEY idx_retry_floor (bundle, changed_mark)
```

### Who writes them

`_track_retry(record, outcome, pending, error)` runs in the `handle` wrapper —
**the only place that sees every outcome, the raised ones included**.

| Outcome set | Members | Action |
| --- | --- | --- |
| `_UNRESOLVED_OUTCOMES` | `error`, `skipped` | `retries.record(...)` |
| `_RESOLVED_OUTCOMES` | `indexed`, `unchanged_content`, `deleted` | `retries.clear(...)` — **only if** the id was already pending |
| neither | `unchanged` | nothing |

`unchanged` is in neither set on purpose: it never reached a build, and a document
that is unchanged already has the catalog row that positions the cursor.

The "only if already pending" condition is why `pending` is read once per run: a
healthy sweep issues no `DELETE` per document, because a document that was never
failing has nothing to clear.

`_track_retry` fails open with one warning — an unreachable database costs the
behaviour that predates the floor.

### The `error` string

The reason a document is unresolved is captured wherever it was decided.
`_handle` reports the reasons it can name (via a `fail` callback), and the
`except` in `handle` reports the ones it cannot. Both end up on the retry row.
Without it the retry queue is a list of ids that says nothing about whether they
are one broken host, one bad extractor or ninety separate problems — the
difference between a queue an operator can triage and one they can only stare at.

### `outcome` values you will see

| Value | Written by | Meaning |
| --- | --- | --- |
| `error` | `_track_retry` | The document raised, or extracted to nothing |
| `skipped` | `_track_retry` | The document could not be built (download or extraction returned nothing) |
| `reindex` | `workers.tasks.reindex_document` | An operator asked for it back — the document did not fail |
| `recover` | `app.ingestion.recovery` | A historical failure that predates retry markers |

Distinct values because a queue that cannot tell a fresh failure from an operator
request from a historical one cannot be triaged.

### There is no attempt cap

`attempts` is counted but never enforced. A document that fails forever holds its
bundle's floor down forever — the cost is a larger scan per run, **not** lost work.
That is the deliberate trade for "a temporary failure stays visible without anyone
editing the source".

The operational consequence: a permanently broken document makes every sweep scan
its whole bundle. Watch the queue (`SELECT bundle, COUNT(*), MIN(first_seen) FROM
documents_retry GROUP BY bundle`) and fix or remove the source.

Rows with no `changed_mark` cannot position a cursor and are left out of
`floors()`; they are still retried whenever their bundle is crawled.

### Why not a row in `documents`?

A placeholder there would be counted as a catalogued document by every analytical
read — bundle counts, document lists, theme distributions — which is precisely the
claim a failed document must not make.

---

## Delete reconciliation

Only runs when `reconcile_deletes=True` **and** the bundle has prior rows.

### Establishing the live set

| Source type | Live set |
| --- | --- |
| Incremental (node) | `iter_node_uuids(...)` — UUIDs only, `fields[node--B]=drupal_internal__nid`, sorted by that unique serial id, **no `changed` filter**. This is the complete live set, not the incremental window. |
| Full-fetch (block) | The records just yielded **are** the live set. |

The enumeration is sorted by the serial id alone because it is unique, so the
ordering is total and offset pagination cannot shuffle rows between pages.
Reconciliation removes whatever this walk fails to return, which makes an
exhaustive walk a **correctness requirement**, not a nicety.

An enumeration failure logs and `continue`s — the bundle's deletes are skipped
entirely for that run.

### Gate 1 — is the enumeration believable?

```python
missing = prior_uuids - live_uuids
if missing and not _deletions_are_plausible(...): continue
```

`_deletions_are_plausible` refuses on either of two rules, both per bundle so one
bad source cannot stop the others:

1. **A live set that is empty while the catalog is not is never believed.**
   Whatever emptied a whole bundle at once is worth a human look.
2. Otherwise the missing share may not reach
   `ingest_reconcile_max_missing_ratio` (default 0.10), with an absolute
   allowance of `ingest_reconcile_min_deletions` (default 2) so a genuinely small
   bundle can still lose one or two. That allowance sits far below
   `drupal_page_size`, so it cannot mask the truncation it is guarding against.

On refusal it logs, at WARNING, the counts and what to do:

> Refusing to reconcile deletes for node/news: 34.0% of the bundle is missing, at
> or above the 10.0% limit. Catalogued 812, live 536, missing 276. No documents
> were deleted; the rest of the run is unaffected. Re-check the source, then raise
> ingest_reconcile_max_missing_ratio if the drop is real.

The gate runs **before anything is yielded**, so a suspicious bundle loses nothing
at all — not even the deletions that would have been correct. That is the
deliberate choice: a fetch that *fails* already skips the bundle, and this exists
for responses that arrive successfully and incomplete (a renamed bundle, a filter
that stopped matching, a cache serving an empty page, a walk that lost one page of
fifty).

### Gate 2 — did it move, rather than disappear?

`_safe_to_delete(uuid, bundle)` re-reads the catalog **per candidate**, against the
state as it stands *now* rather than as it stood when the run began:

- Row missing → nothing left to protect, delete proceeds.
- `current.bundle != bundle` → **not deleted**, logged: the document moved bundles
  rather than disappearing. The prior snapshot is read once at the start of a run,
  so it keeps filing a document under the bundle it has since left; if the new
  bundle was crawled earlier in this same run the document has already been
  re-indexed under it, and deleting on the strength of the stale snapshot would
  take a live, freshly indexed document straight back out.
- Read fails → **not deleted**. Not deleting costs one more sweep; deleting
  wrongly costs a document out of the index until then.

This gate only ever *removes* candidates from a batch the completeness guard has
already approved, so it cannot loosen that check.

### What a delete actually does

In `_handle`:

```python
linked = state.attachment_ids_for(document_id)   # BEFORE the delete
delete_document(document_id)                     # all Qdrant points
state.delete([document_id])                      # catalog row + FK cascades
log "deleted"
_delete_orphaned_attachments(linked, record, run_id)
```

The link rows cascade away with the document row, so the attachment ids have to be
read first or not at all. See
[08, Orphan collection](08-persistence-and-catalog.md#orphaned-attachment-collection).

### Unpublishing is deliberately identical to deletion

Not by choice: the site's JSON:API serves an anonymous client only published
content, so an unpublished document is simply **absent** and indistinguishable
from a removed one. The index is meant to hold what the site currently publishes,
so absent means gone from search.

Nothing records the document as *permanently* gone. The catalog row goes and its
retry marker is cleared, so republishing brings it back through the ordinary crawl
as `NEW` — and republishing saves the node, which moves `changed` to now, above
any bundle's high-water mark, so the very next run picks it up.

### The dry run

```bash
python -m app.ingestion.pipeline --dry-run-reconcile [--bundle B]...
```

`reconcile_dry_run` runs the real thing as far as the decision and stops: the same
crawl, the same enumeration, the same completeness guard, the same per-candidate
bundle-move confirmation, and the same `orphaned_attachments` query (with
`ignoring_parents`, which answers "which attachments *would* this orphan" without
deleting anything to find out). What it does not do is hand any record to
`_handle`, which is where every write lives — so no document is indexed, no row is
written or deleted, no vector is touched, no retry marker moves, and the
high-water mark, derived from rows that do not change, stays put.

It takes the run lock: this walks the whole site, and doing that alongside a real
sweep helps nobody.

One adjustment is needed for bundle moves. The real run re-indexes a moved document
under its new bundle and the confirmation step reads that back; a dry run indexes
nothing, so the catalog still files it under the bundle it left. But the crawl has
already yielded it live under the *new* bundle by the end of the run, so the record
of the run is enough to tell a move from a disappearance — that is what the
`moved` list in the report is.

The report:

```json
{"dry_run": true,
 "documents": [{"document_id": "...", "bundle": "news", "source_key": "..."}],
 "attachments": ["file-uuid", ...],
 "moved": [{"document_id": "...", "from_bundle": "news", "to_bundle": "report"}],
 "by_bundle": {"news": 3},
 "linked_attachments_surviving": 12}
```

**Always run this before enabling `worker_sweep_reconcile` on a corpus you care
about.**

---

## Idempotency and replay

The pipeline is safe to re-run at any point, and every mechanism that makes it so
is a deterministic key:

| Write | Key | Effect of a replay |
| --- | --- | --- |
| Chunk point upsert | `chunk_id = uuid5(namespace, "doc|kind|hash(owned)|ordinal")` | Same ids, same payloads; an unchanged chunk also reuses its stored vector |
| `documents` row | `document_id` primary key, `INSERT … ON DUPLICATE KEY UPDATE` | Overwritten in place |
| Facet rows | delete-then-insert per document, inside the same transaction | Rewritten wholesale, so a reindex heals drift |
| Attachment links | delete-then-insert, first link wins per file | Same set |
| `documents_retry` | `document_id` PK, `attempts = attempts + 1` | Attempt counted, `first_seen` preserved |
| `documents_dead_link` | `document_id` PK, attempts reset on a *different* fingerprint | Same |
| `documents_enrichment` | `content_hash` PK | Cache hit; no model call |
| `documents_date_decision` | `document_id` PK | Overwritten (a current-state snapshot, not an audit trail) |
| `ingest_log` | auto-increment id | **Appends** — the log is deliberately append-only, which is what makes `recovery.py` possible |
| Knowledge mentions | `UNIQUE(chunk_id, start_offset, end_offset, normalized_text)` | `INSERT IGNORE` — no duplicates |
| Knowledge claims | `claim_id` upsert | Re-derived |

The two things replay does *not* undo: the ingest log grows (bounded by retention),
and `doc_version` increments on every real rebuild. Neither is a correctness
problem — `doc_version` is a monotonic counter, not a content identity.

## Ordering and out-of-order events

There is no event stream, so there are no out-of-order *deliveries* — but there are
several ordering guarantees the pipeline depends on, and one it deliberately does not
provide.

### Guaranteed

| Guarantee | Enforced by | Why it matters |
| --- | --- | --- |
| Records arrive oldest-first within a bundle | `sort=changed,drupal_internal__nid` | Makes `MAX(changed_mark)` a resume cursor |
| The sort is total | The serial-id tiebreaker | Without it, offset pagination silently skipped 137 of 1,167 records and duplicated 126 |
| A node's attachments follow it immediately | The crawl yields them in that order | The node's state row would otherwise hide them from the next crawl |
| A run never stops between a node and its attachments | `budget_reached` returns `False` for `pdf_attachment` | Same |
| Facets are committed with their document | One transaction in `state.upsert` | A document and its facets are never observably out of step |
| New points exist before old ones are deleted | The swap in `_handle` | The document never disappears mid-update |
| Link rows are read before they are rewritten | `_persist` ordering | `state.upsert` replaces them wholesale |
| Orphan checks run after the write commits | `_persist` ordering | `orphaned_attachments` uses its own connection and sees only committed rows |
| Knowledge runs only after the document is fully indexed and logged | The hook's position in `_handle` | Its failure cannot unmake an indexed document |
| Knowledge catch-up runs before graph projection | `sweep()` ordering | Anything staged lands in this sweep's refresh |
| Reconciliation runs last | `sweep()` ordering | It reports the stores as they stand after everything else |
| Decisions are dropped before mentions | The `supersede` stage | The decision log has no `document_id`; mentions are what identify the chunks |
| Conflict statuses are applied before links are saved | The `conflicts` stage | The safe residue of an interruption is a suppressed claim missing its audit link |

### Not guaranteed

**Bundles are processed in list order, not in global `changed` order.** Two documents
edited seconds apart in different bundles can be ingested in either order, and a
capped run may process an older document in bundle 15 after a newer one in bundle 1.
Nothing depends on cross-bundle ordering: the window, the high-water mark and the
retry floor are all **per bundle**, and each document's own `changed` value is what
positions it.

**Under `ingest_workers > 1`, documents complete out of order.** The crawler stays
single-threaded so the node-before-attachment *submission* order holds, but
completion order is whatever the pool produces. That is safe because documents are
independent across MySQL (per-document transactions) and Qdrant (per-document
points) — with one exception the code handles explicitly: a document that moved
bundle may be re-indexed under its new bundle *earlier in the same run* than the
delete candidate list is examined, which is exactly what `_safe_to_delete` re-reads
the catalog to catch.

### The one genuinely late signal

A document edited *while* a run is in flight may be crawled with its old `changed`
value, or missed entirely if its bundle has already been walked. The `>=` boundary
condition and the fact that an edit moves `changed` to now — above the bundle's
high-water mark — mean the very next run picks it up. Freshness is bounded by
`worker_sweep_interval_seconds`, not by ordering.

## Deduplication: every mechanism in one place

The pipeline de-duplicates at six different levels, for six different reasons.

| Level | Mechanism | Prevents |
| --- | --- | --- |
| **Document identity** | An in-body PDF's id is `inbody:<sha1(absolute URL)>` | The same PDF linked from several pages becoming several documents |
| **Within a run** | `seen_pdf` set in the crawl | The same file being downloaded and extracted once per referencing page |
| **Within a record** | `_resolve_files` keys on the resolved absolute URL; `_extract_inbody_pdfs` de-duplicates against files already found | One PDF reached both as a `file--file` attachment and as an in-body link |
| **Within a rich-text field** | Anchors keyed by URL, **longest text wins** | A thumbnail `<a>` with no text blanking the captioned link's description |
| **Chunk identity** | `uuid5(namespace, "doc\|kind\|sha256(owned)\|ordinal")` | An unchanged chunk churning its id — and the `ordinal` prevents genuinely repeated text collapsing two chunks onto one id |
| **Embedding** | `embed_hash` + `embed_model` reuse key | Re-paying for a vector whose input did not change |
| **Enrichment** | Cache keyed by `content_hash` | Re-paying for an abstract of identical body text under a different document id |
| **Facet values** | Truncate to 255 **then** de-duplicate, plus a UNIQUE key the database enforces under its own collation | 144 duplicate `(document, tag)` pairs, and a repeated tag failing the whole document's transaction |
| **Attachment links** | First link wins per `file_uuid` | An in-body sighting overwriting an explicit attachment reference's url/filename |
| **Knowledge mentions** | `UNIQUE(chunk_id, start_offset, end_offset, normalized_text)` with `INSERT IGNORE` | Re-extraction duplicating knowledge |

Note the deliberate ordering in the facet rule: **truncate first, de-duplicate
second.** The other order de-duplicates strings the database will never hold.

## Failure scenarios

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| Retry table unreadable at start | `except` in `_pending_retries` | `logger.exception`; empty pending set. Failures this run are still *recorded*, they just are not *cleared* | Next run |
| Retry floors unreadable | `except` in `_load_retry_floors` | Warning; no floors. The crawl behaves as it did before floors existed — failures may stay out of the window | Next run |
| Retry write fails | `except` in `_track_retry` | One warning: "the crawl cursor may skip it" | `scripts.recover_stranded` reads the log and rebuilds the markers |
| A document fails forever | `attempts` grows in `documents_retry` | Its bundle's floor stays down; every sweep scans more of that bundle | Fix the source, or delete the retry row deliberately |
| Live enumeration truncated | `_deletions_are_plausible` | Bundle's deletes refused with a WARNING naming counts and the setting to change | Investigate the source; raise the ratio only if the drop is real |
| Live enumeration empty | Same | Never believed | Investigate |
| A document moved bundle | `_safe_to_delete` | Spared, INFO logged | None needed |
| Catalog read fails during the move check | `except` in `_safe_to_delete` | Spared | Next sweep |
| Pipeline version bumped by mistake | Everything the crawl reaches rebuilds | — | Revert the bump; already-rebuilt documents are correct, just re-embedded |
| Pipeline version *not* bumped after a real change | Silent. Old and new chunks coexist | — | Bump it and run `scripts.reprocess_corpus`; `point_pipeline_drift` in reconciliation is the detector |

## Monitoring

- Run tally keys: `unchanged`, `unchanged_content`, `indexed`, `deleted`,
  `skipped`, `error`, `budget_stop`.
- `Rebuilding %s: content unchanged but pipeline version moved …` — a version bump
  is in flight.
- `Refusing to reconcile deletes for %s/%s: …` — **alert on this**.
- Reconciliation checks `catalog_pipeline_drift` and `point_pipeline_drift` — see
  [11](11-observability-and-monitoring.md).
- Useful queries:

```sql
-- The retry queue, by bundle and by age
SELECT bundle, outcome, COUNT(*), MIN(first_seen), MAX(attempts)
FROM documents_retry GROUP BY bundle, outcome ORDER BY 3 DESC;

-- How far back each bundle's window currently reaches
SELECT bundle, MIN(changed_mark) FROM documents_retry
WHERE changed_mark IS NOT NULL GROUP BY bundle;

-- Pipeline drift, per bundle
SELECT bundle, COUNT(*) FROM documents
WHERE pipeline_version IS NULL OR pipeline_version <> 'c1.i1.p1.e1'
GROUP BY bundle ORDER BY 2 DESC;
```

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `worker_sweep_reconcile` | `false` | Whether the scheduled sweep reconciles deletes at all. |
| `ingest_reconcile_max_missing_ratio` | `0.10` | Share of a bundle one run may never remove. |
| `ingest_reconcile_min_deletions` | `2` | Absolute allowance below that ratio. |
| `ingest_state_table` | `documents` | Table prefix. Validated by `safe_table()`. |

## Hand-off

An actionable record (`NEW`/`CHANGED`) now goes to the document builder — the
extraction stage in [05](05-extraction-and-normalisation.md) and the canonical
model in [06](06-canonical-document-and-dates.md).

---

Previous: [03 — Triggers and the Control Plane](03-triggers-and-control-plane.md) · Next: [05 — Extraction and Normalisation](05-extraction-and-normalisation.md)
