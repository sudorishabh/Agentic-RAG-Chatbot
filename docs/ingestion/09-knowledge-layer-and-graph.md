# 09 — The Knowledge Layer and Graph

**Purpose.** Derive structured knowledge — entity mentions, canonical identities and
claims — from documents that have just been indexed, and project it into Neo4j.

**Inputs.** A successfully indexed document: its chunks (already in memory), its
CMS metadata, its authors.

**Outputs.** Rows in the knowledge tables, a run report in
`documents_knowledge_run`, and nodes/relationships in Neo4j.

**Components.** `app/ingestion/knowledge_sync.py` (the ingest hook and the catch-up
sweep), `app/ingestion/graph_sync.py` (the sweep-level projection),
`app/knowledge/document_pipeline.py` (the stages),
`app/knowledge/document_loader.py` (rebuilding a document from the stores),
`app/catalog/knowledge_runs.py` (the report table).

**This layer ships inert.** `knowledge_enabled` defaults to `false`, and the
per-document hook is additionally gated by `knowledge_process_after_index`, which
also defaults to `false`. With either off, nothing here imports `app.knowledge`,
opens a connection, or costs a document anything measurable.

---

## Why it is in this documentation set at all

Because it runs **on the ingest path**, and the thing you most need to know about it
is that it **cannot break an ingestion**. If you are debugging a failed sweep, this
is a layer you can rule out structurally rather than by inspection.

---

## Where the hook is, and why exactly there

`pipeline._handle`, immediately before it returns `"indexed"`. By that point five
things have already happened, and none of them can be undone by anything in the
knowledge layer:

1. the chunks were built,
2. Qdrant holds the new version's points,
3. the previous version's points have been swapped out,
4. the catalog row and its facet rows are committed,
5. the ingest log records the document as indexed.

So the document's fate is **settled** before this module is entered.

It is called for `indexed` and nothing else — not `deleted`, `unchanged`,
`unchanged_content`, `skipped` or `error`. Those are either not a successful index
or, for `unchanged_content`, a document whose chunks did not change and whose
knowledge is therefore already whatever the last run made it.

```python
if knowledge_sync.enabled():
    knowledge_sync.process_after_index(
        document_id=..., doc_version=version, chunks=new_chunks,
        source_type=..., bundle=..., content_hash=...,
        raw_meta=getattr(doc, "raw_meta", None),
        authors=tuple(getattr(doc, "authors", ()) or ()),
        run_id=run_id,
    )
```

The `enabled()` guard is **not an optimisation**. Argument evaluation happens at the
call site, outside anything `knowledge_sync` can catch, so with the feature off this
is the difference between "inert" and "inert unless one of these attributes is
missing". `raw_meta` and `authors` are read defensively with `getattr` for the same
reason: nothing about *assembling* this call may cost a document that is already
indexed.

The return value is deliberately discarded.

### Why it cannot break ingestion — structurally, not by care

- Every entry point **returns rather than raises**, and the outermost body is a bare
  `except Exception`.
- `_handle` ignores the return value, so there is no path by which a report becomes
  an outcome.
- `"indexed"` is in `_RESOLVED_OUTCOMES`, so no retry marker is written whatever
  happens here.
- **Nothing in this module or in `document_pipeline` imports `index_chunks` or
  `delete_document`.** A knowledge failure cannot remove a vector, because the code
  to remove one is not reachable from it.

A knowledge failure therefore costs a log line and a row in
`documents_knowledge_run` saying so:

> The knowledge stage failed for <id>; the document is indexed and unaffected. It is
> re-runnable with `python -m scripts.knowledge_document <id>`.

`enabled()` itself never raises: it is called *before* the arguments are assembled,
so it is the outermost guard and has to hold even if configuration cannot be read at
all — in which case the honest answer is "not enabled".

---

## Chunks are passed, not re-read

`DocumentInput.from_chunks` takes ingestion's own `Chunk` objects, already in
memory. That is not only cheaper: it **guarantees the knowledge layer reads exactly
the text that was just indexed**, with no window in which a concurrent write could
change the answer underneath it.

Parents are dropped (`is_parent = False`): a parent chunk is an assembly of its
children's text, so extracting from both would double every mention and stage the
same claim from two spans. This is the same filter the corpus builder applies when
it scrolls Qdrant.

A document whose every chunk was a parent returns `None` — nothing to extract from,
and not a failure.

---

## The stages

`process_document(doc, options)` runs a prelude and then eight steps. **Every step
is independently guarded**: a step that raises past its own handling costs itself
and nothing else, because every step before it has already committed on its own
connection.

```
prelude   -> entity index, per-document context, gazetteer, knowledge_version
             (the ONE fatal failure: nothing downstream is meaningful without it)
supersede -> retract claims citing chunks that no longer exist; drop stale
             mentions and decisions
mentions  -> per-chunk mention extraction, skipping what the extraction cache covers
resolution-> which canonical entity each mention denotes
claims    -> CMS-field claims (deterministic) + LLM-proposed claims (budgeted)
validate  -> the gate; nothing reaches storage without passing every check
persist   -> stage accepted claims, record refusals, record pending predicates
conflicts -> supersession and dispute verdicts, over this document AND its siblings
project   -> scoped projection of touched claims into Neo4j
```

Then `_record` writes the run row — **last**, and never fatal.

### The budget

`knowledge_stage_budget_seconds` (default 30) is checked before every step. Exceeding
it marks the remaining steps skipped with `BUDGET_EXCEEDED` and ends the run as
`partial` rather than raising: **what already landed is valid and a retry resumes.**
The mention stage also checks it per chunk.

`knowledge_llm_max_calls_per_document` (default 8) bounds the model separately.

### `supersede`, and why claims are retracted rather than deleted

Chunk ids are version-scoped in the *claim* id (`claim_id` embeds the chunk), so
re-indexing a document strands everything keyed by them: mentions whose spans point
at text that no longer exists, decisions about those spans, and claims citing
evidence nobody can fetch.

Claims are **retracted, never deleted**: the claim was true of the source as it
stood, and that history is worth keeping. Retracted claims still need projecting —
that is how their current-state edge is removed.

Order matters inside the step: **decisions first, then mentions.** The decision log
has no `document_id` — a decision is about a *span* — so the document's own mention
rows are what identify its chunks, and deleting those first would leave nothing to
join against.

Skipped entirely on `doc_version <= 1`.

### `claims`

Two sources:

- **CMS fields** — deterministic, free, and the largest true source. Requires a
  canonical subject entity for the document.
- **LLM-proposed** — gated by `claim_extraction_enabled` and budgeted. The model may
  only reference entities **this document's own resolution marked canonical**, so a
  provisional identity is unreachable from a prompt: the eligibility filter runs
  *before* the call, not after it.

### What is deliberately *not* here

Four stages the corpus builder (`scripts.build_knowledge`) runs are absent, and
their absence is the design rather than an omission:

| Stage | Why it cannot run per document |
| --- | --- |
| `seed` | Reads the whole catalog to mint canonical entities. |
| `acronyms` | Pairs corpus-wide glosses against seeded names. |
| `ambiguity` | A single global `UPDATE` whose correctness depends on seeing every alias at once. The moment a second "Sharma" exists, the shared surface must stop autolinking **for everyone**, and a per-document pass cannot know that. |
| `pi-promotion` | Weighs a name against the whole PI population. |

Running any of them per document would either repeat global work once per document
or — worse — take a global decision on partial evidence, which is how false merges
get committed.

So a newly ingested project may have **no canonical PROJECT entity yet**, and its
CMS claims are refused as `unknown_subject` until the next
`scripts.build_knowledge`. That refusal is **recorded rather than silent**
(`stage.notes` carries `NOT_SEEDED`), and it is the correct answer: the alternative
is inventing an identity.

### `conflicts` — scoped to siblings, not to the document

Scoping this to one document would be **wrong, not merely incomplete**. A functional
predicate's contradictions are inherently cross-document — two documents naming
different principal investigators for one project is the case the detector exists for
— and a batch holding only this document's claims would never see the pair.

So every `(subject, predicate)` this document touched is re-read from the store and
detection runs over the union. This run's freshly validated objects win over their
stored rows: the store may not have them yet under `--dry-run`, and where it does
they are identical by construction.

Statuses are applied **before** links are saved: if the run is interrupted between
them, the safe residue is a suppressed claim missing its audit link, not an
unsuppressed claim that projects an edge it should not.

### `project` — scoped, never the whole corpus

`project_claims(touched_claims)`, not `project()`. The whole-corpus pass finishes by
deleting every current-state edge it did not re-stamp, which **per document would
erase the rest of the corpus's graph**. The scoped form retires edges by name
instead.

Fail-open in every direction. Neo4j unreachable → `projection_status="unreachable"`
and a note that MySQL is authoritative and the graph catches up at the next
`project_after_sweep`. Any exception → `projection_status="failed"`.

Gated by `knowledge_project_per_document` (default `true`, but inert because its
parent flag is off). Off means MySQL still gets the claims and the graph catches up
at the next sweep — **a lag, never a loss.**

### Idempotency

Every write is idempotent on a deterministic key — `INSERT IGNORE` on a mention
span, upsert on a decision span, upsert on `claim_id`, `MERGE` on a graph key — so a
retry re-derives rather than duplicates. The stage adds no bookkeeping of its own
beyond the run row, which is written last **precisely so its absence marks a run
that never finished**.

The extraction cache is recorded in the *resolution* stage, not the mention stage,
so an interruption between the two re-runs the chunk instead of marking it done on a
half-finished pass.

---

## The catch-up sweep

`knowledge_sync.catch_up(limit=25)` runs after every sweep, before graph projection.

Two populations, both from `knowledge_runs.pending`:

1. Runs that ended `partial` or `failed` and are still under
   `knowledge_stage_max_attempts` (default 3) — the ordinary retry.
2. **Indexed documents with no run row at all** for their current version — a stage
   that never ran, or one that crashed before it could report. The row is written
   last precisely so this absence is detectable.

Ordered oldest-first (`COALESCE(k.updated_at, d.indexed_at) ASC`) so a backlog drains
in the order it accumulated rather than starving its head.

**Bounded on purpose.** A backlog is drained across sweeps rather than in one
unbounded pass that would make an ingestion run's duration depend on how long the
knowledge layer had been broken.

It runs **before** the projection so anything it stages is in this sweep's graph
refresh rather than the next one.

Never raises — including a failed import or an unreadable setting, not only the store
calls that have their own handlers.

### Rebuilding a document the hook did not see

`document_loader.load_document(document_id)` reconstructs a `DocumentInput` from the
two stores that hold it: the catalog for metadata, **Qdrant for the text of its
current chunks**.

Qdrant is the right source for the text. It is authoritative for chunk text and
vector evidence, and reading the chunk that is *actually indexed* is what keeps a
claim's `chunk_id` pointing at something a citation can fetch. **Re-chunking the
document here would produce different ids and silently break that chain.**

Three details:

- Filters on `is_parent=False`, `is_current=True` and the catalogued `doc_version`,
  and orders by `chunk_index` — unordered scroll results would make two runs of the
  same document report their chunks differently for no reason.
- `raw_meta` is read separately via `state.raw_meta_for(document_id)`, **not** from
  the `StateRecord`. `state._row_to_record` never fills that field — the blob is far
  too large to carry on every record `state.load` builds — so taking it from the
  record would silently always be `None`, and every CMS claim on this path would
  vanish without an error to explain it.
- `authors` come from `state.authors_for(document_id)` (the `documents_author`
  facet), not from the metadata blob. Author names were moved to the facet and
  `raw_meta.field_authors` is empty corpus-wide, so the blob alone leaves PERSON
  resolution with no corroboration. The **raw** value is returned, not
  `author_norm`, because the knowledge layer applies its own normalisation and
  folding twice through two schemes would not round-trip.
- Returns `None` when the document is not catalogued, or has no current chunks —
  both ordinary answers rather than errors. A document deleted between being queued
  for retry and being retried is exactly the first case, and the caller should move
  on rather than fail.

Tables of contents and bibliographies are deliberately **not** filtered out.
Retrieval excludes them because they pollute *search*; a bibliography is exactly
where author names live, so extraction wants them.

Manual re-run:

```bash
python -m scripts.knowledge_document <document_id>
python -m scripts.build_knowledge --dry-run | --limit 500   # the corpus pass
```

---

## Sweep-level graph projection

`graph_sync.project_after_sweep()` runs once, after the sweep, on the same thread the
sweep finished on.

### Why sweep-level, not per document

Projection is a **whole-graph pass**: it reads the staged entities and claims,
rewrites the current-state edges and removes the previous generation. Running it per
document would repeat that pass once per document — and a document is not even the
unit it operates on; **claims are**. It also has to be able to fail without the
document failing, which a synchronous step inside `_handle` cannot offer.

### Why it cannot break ingestion

Neo4j is a **derived store**. Everything it holds is re-derivable from MySQL, which
is why `scripts.project_graph --rebuild` is always a valid repair — so an unreachable
graph is a degraded knowledge layer and nothing more. Every entry point returns
rather than raises, and the sweep's result is computed and logged **before** any of
this runs.

```python
if not knowledge_enabled or not graph_project_after_sweep:  return None
if not graph_available():                                   warn and return None
ensure_graph_schema()          # constraints before the first MERGE
report = project().as_dict()
```

The unreachable path logs, explicitly:

> Neo4j is unreachable; the knowledge graph was not refreshed and is now behind the
> corpus. Ingestion is unaffected — the graph rebuilds from MySQL with
> scripts.project_graph.

### Freshness

`freshness()` reports rather than raises in every direction, because **disabled,
unreachable, never projected, and projected-at-a-known-time are four different
answers and each one is useful**:

```json
{"enabled": true, "reachable": true, "projected_at": "...", "age_seconds": 3600, ...}
```

`is_stale(report)` is specifically "it *was* projected, and that was too long ago"
— older than `graph_projection_max_age_seconds` (default 86400). A graph that is
disabled, unreachable or has never been projected is **not** stale; those are their
own conditions, reported separately. Staleness is the one that says the *scheduled
projection has stopped happening*.

Reconciliation's `graph_projection` check folds both in: the graph's own MySQL-vs-graph
diff (`knowledge.graph.verify.verify()`), **plus** a staleness problem — because
content agreeing is not the same as the projection still running. A graph that
stopped being projected months ago agrees with MySQL about everything it was told,
and is wrong about everything since. A graph with no projection stamp at all is
flagged as possibly never projected.

The check is **skipped, never failed**, when the knowledge layer is off or the graph
is unreachable: a graph outage must not make a healthy corpus look broken, and must
certainly not make anything destructive happen.

---

## `documents_knowledge_run`

One row per `(document_id, doc_version)`, upserted. It answers three questions
nothing else could:

- Did this document's knowledge stage run, and what did it produce?
- Which documents need retrying, and how often have we already tried?
- **Which knowledge rules was a document processed under?** — the
  `knowledge_version` fingerprint, so a rule change is a query rather than
  archaeology.

Counter columns are declared once in `COUNTER_COLUMNS` and the `StageReport` field
names match them, so a counter added to the report reaches the table by adding the
column, not by teaching a mapper about it.

`record()` swallows its own failure: a report row that cannot be written must not be
the thing that turns a successful knowledge run into a failed one.

---

## Security notes for this layer

Neo4j Community offers no role-based access control, so **the read-only boundary for
retrieval is enforced in code** (`app/core/clients/graph.py` exposes `read_session`
and `write_session` separately) rather than by a restricted database user. Community
also supports exactly one user database, named `neo4j`.

The container image is **pinned** (`neo4j:2026.07.1-community`) rather than `:latest`,
because the schema in `app/knowledge/graph/schema.py` is written against what this
edition actually supports — Community rejects `NODE KEY` and existence constraints,
and the schema designs around that. A silent major-version bump would change which
DDL is legal.

The compose volume is declared `external` with an explicit name so adopting compose
keeps an existing graph rather than starting an empty one. Stop and remove any
hand-started container before `docker compose up`, or the port bindings collide.

---

## Failure scenarios

| Scenario | Detection | Response | Recovery |
| --- | --- | --- | --- |
| Knowledge layer off | `enabled()` | Nothing runs, nothing imported | — |
| Entity index unavailable | `_prelude` raises | The **one** fatal failure: run ends, status `failed`, run row written | Catch-up sweep, or `scripts.knowledge_document` |
| One stage raises | per-step `except` | That stage fails, the run continues, status `partial` | Catch-up sweep |
| Budget exhausted | `over_budget()` | Remaining stages skipped, status `partial`, everything written is valid | Catch-up sweep resumes |
| One chunk's extraction fails | per-chunk `except` | That chunk only; the id is reported so the run can be repeated | Re-run |
| Claim staging fails | `except` in `_persist` | `accepted` cleared so conflicts and projection **stand down rather than acting on a phantom set**; retractions already committed keep their scope | Catch-up sweep |
| Document not seeded yet | `context.subject_for(...)` is `None` | `NOT_SEEDED` note; CMS claims refused | `scripts.build_knowledge` |
| Neo4j unreachable | `graph_available()` | `projection_status="unreachable"`, note; sweep unaffected | `project_after_sweep`, or `scripts.project_graph --rebuild` |
| Projection raises | `except` in `_project` / `project_after_sweep` | Logged; sweep unaffected | Same |
| Projection stopped running | `graph_sync.is_stale` via reconciliation | `graph_projection` drift reported | Check `graph_project_after_sweep` and the scheduler |
| Run row cannot be written | `except` in `knowledge_runs.record` | Swallowed | The absence makes the document `pending`, so catch-up picks it up |
| Knowledge queue unreadable | `except` in `_catch_up` | Warning; catch-up skipped | Next sweep |
| Backlog grows | `status()["pending"]` | Drained 25 per sweep | Run `scripts.build_knowledge`, or raise the limit deliberately |

## Observability

- Per document: `knowledge_document id=… v=… status=… claims=… pending=… proj=… 1.23s`
- Per sweep: `knowledge_catch_up {'examined': 4, 'ok': 3, 'failed': 1}`
- Per sweep: `graph_projection version=… nodes=… relationships=…`
- `GET /metrics` → `knowledge` block, from `knowledge_sync.status()`:
  `knowledge_version`, run status counts, `pending` depth, the five latest runs, and
  the five most recent errors. Only reachable from `/metrics`, which is already
  hidden behind the ops visibility gate — run counts, document ids and error strings
  are deployment detail with no business on a public response.
- `GET /metrics` → `neo4j` block: enabled / reachable / node and relationship counts.
- `GET /ready` (with `ops_detail_enabled`) includes the `neo4j` probe, which reports
  reachability as a **value rather than an exception** — the graph being down is a
  degraded knowledge layer, never an unready service.

```sql
SELECT status, COUNT(*) FROM documents_knowledge_run GROUP BY 1;
SELECT knowledge_version, COUNT(*) FROM documents_knowledge_run GROUP BY 1;
SELECT document_id, doc_version, attempts, LEFT(last_error, 200)
FROM documents_knowledge_run WHERE status IN ('failed','partial')
ORDER BY updated_at DESC LIMIT 20;
```

## Configuration

| Setting | Default | Effect |
| --- | --- | --- |
| `knowledge_enabled` | `false` | Master switch. Off means no Neo4j connection is ever opened and ingestion behaves exactly as it does without the layer. |
| `knowledge_process_after_index` | `false` | Build knowledge on the ingest path. A separate decision with a separate cost — a deployment may reasonably want only the corpus-level `scripts.build_knowledge`. |
| `knowledge_project_per_document` | `true` | Scoped projection at the end of a document's stage. Inert while its parent flag is off. |
| `knowledge_stage_budget_seconds` | `30.0` | Wall-clock budget per document. |
| `knowledge_llm_max_calls_per_document` | `8` | Model call budget per document. |
| `knowledge_stage_max_attempts` | `3` | Retries before catch-up leaves a document alone. |
| `claim_extraction_enabled` | `false` | LLM claim extraction. |
| `claim_min_confidence` | `0.6` | Validation floor. |
| `graph_project_after_sweep` | `true` | Sweep-level projection. Gated by `knowledge_enabled`. |
| `graph_projection_max_age_seconds` | `86400` | Staleness tolerance. |
| `neo4j_uri` / `_user` / `_password` / `_database` | `bolt://localhost:7687`, `neo4j`, — , `neo4j` | Connection. |
| `neo4j_connection_timeout` | `10.0` | Handshake timeout. |

---

Previous: [08 — Persistence and the Catalog](08-persistence-and-catalog.md) · Next: [10 — Failures, Retries and Recovery](10-failures-retries-and-recovery.md)
