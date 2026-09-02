# How the Knowledge Graph (Neo4j) Works in This App — End to End

## 1. What it is

The app runs **two** databases side by side for retrieval:

- **Qdrant** — the vector store, holds chunk text + embeddings (the "what does the source say" store).
- **Neo4j** — the knowledge graph, holds canonical **entities**, **aliases**, **claims** (facts extracted from documents) and their **provenance** (the "who/what is related to whom, and since when" store).

The graph is a **rebuildable projection of MySQL, never a system of record**. MySQL (`app.catalog`) is where entities and staged claims actually live; Neo4j only ever mirrors what MySQL currently says is true and eligible. If Neo4j is wiped or goes down, nothing is lost — it's rebuilt from MySQL with `scripts.project_graph --rebuild`. This single design decision explains almost every other choice in the subsystem (fail-open everywhere, MERGE-based idempotent writes, a "sweep and retire" reconciliation model instead of deletes/updates).

There's a **master kill switch**, `knowledge_enabled` (default `False`). With it off, nothing in the app opens a Neo4j connection at all — ingestion and retrieval behave exactly as if the graph didn't exist. Several other flags nest under it (see §6).

## 2. The moving parts (file map)

```
app/core/clients/graph.py        Neo4j driver + read/write session gateway
app/knowledge/graph/
    schema.py                    DDL: constraints, indexes, fulltext indexes
    writer.py                    Parameterized Cypher statements + safe MERGE batching
    project.py                   MySQL -> Neo4j projector (the ETL)
    verify.py                    Diff MySQL vs graph; rebuild-from-scratch
app/ingestion/graph_sync.py      Triggers projection after an ingestion sweep
app/retrieval/graph/
    router.py                    Question -> entity + predicate -> Route
    intent.py, plans.py          Predicate/temporal parsing, template selection
    templates.py                 The closed, reviewed registry of Cypher templates
    traverse.py                  Executes one template against Neo4j (read-only)
    hydrate.py                   Graph ids -> Qdrant chunks/documents (source text)
    facts.py                     Renders graph rows into a "facts" context block
    pipeline.py                  Orchestrates: route -> traverse -> hydrate -> rerank -> context
    policy.py                    Production gate: class allow-list, circuit breaker, budget
    shadow.py                    Runs the graph off the request path, just to log comparisons
scripts/project_graph.py         Manual/cron entry point for projection
```

## 3. The write path — how facts get INTO the graph

**Trigger.** After an ingestion sweep finishes (`app/workers/tasks.py`), `app.ingestion.graph_sync.project_after_sweep()` runs. This is deliberately a **sweep-level** step, not per-document: projection is a whole-graph pass over "everything MySQL currently says is projectable," and running it per document would just repeat that pass wastefully. It never breaks ingestion — MySQL and Qdrant are already durably written by the time this runs, so any Neo4j failure here just gets logged and the graph is a sweep behind, nothing more.

**Schema first.** `ensure_graph_schema()` applies idempotent (`IF NOT EXISTS`) `CREATE CONSTRAINT`/`CREATE INDEX` statements — uniqueness constraints on `entity_id`, `claim_id`, `chunk_id`, `document_id`, `predicate name`, `alias_key`; range/composite indexes for the hot lookup paths (alias resolution, claim status/predicate/validity-window filtering); two fulltext indexes for operator entity lookup. Neo4j **Community edition** (confirmed in the code: server measured at `2026.07.1 Community`) lacks `NODE KEY` and existence constraints, so the model works around both: a derived single-property `alias_key` (SHA-256 hash of `entity_id|normalized|alias_type`, joined with a non-printable separator so no two different triples can collide) stands in for a composite key, and required-property enforcement moves into application code (`schema.REQUIRED_PROPERTIES`).

**Projection (`project.py`).** Reads from MySQL:
- **Entities** — only `claim_eligible=1, status='active'` ones. Provisional identities never reach the graph, so no traversal can ever arrive at an unvetted name and mistake it for a real entity.
- **Claims** — *every* staged claim regardless of status, because history matters ("who led this in 2019" needs a superseded claim).
- **Current-state edges** — the narrowest cut: only claims that are `active`, non-disputed, currently valid, and eligible on both ends become an actual graph relationship asserting "this is true now."

Every write goes through `writer.py`, which enforces three structural guarantees:
1. **Always parameterized** — no value is ever string-formatted into Cypher; data flows in as `$rows`.
2. **Labels/relationship types come only from a code-side allow-list** (`safe_label`, `safe_relationship`) — Cypher can't parameterize a label or relationship type, so this is literally the injection defense for the graph's write side.
3. **Idempotent via `MERGE` on a deterministic key** (`entity_id`, `claim_id`, `chunk_id`, `document_id`, `alias_key`) — re-running a projection updates rather than duplicates, batched 1000 rows per round trip (`UNWIND $rows AS row MERGE ...`).

**Retirement (the hard part).** MERGE alone isn't enough — a row that *stops* being projectable (e.g., an entity demoted from `pi_attested` to `provisional`) is never visited again by a MERGE-only pass, so it would linger forever advertising stale eligibility. This was measured on the live graph as 2 stranded entities, 17 claims, 2 aliases. The fix: every write stamps `projection_version` (a per-run generation id), and a whole-corpus pass finishes by deleting anything that *didn't* get re-stamped this generation — current-state edges, then Claims, then Entities, then orphaned Alias/Chunk/Document evidence stubs. This is explicitly framed as **synchronization, not pruning**: MySQL keeps every claim ever staged forever; only what MySQL no longer says is projectable leaves the graph.

There's also a **scoped variant**, `project_claims()` (per-document, used by `knowledge_project_per_document`), which must NOT use the whole-corpus retirement logic (that would wipe the rest of the corpus's edges) — it retires only by explicit claim id.

**Verification & repair (`verify.py`).** `verify()` diffs MySQL against the graph: counts, but also — critically — per-entity trust/eligibility/status comparison (catches a demotion the projector silently missed), that no disputed claim backs a current-state edge, and that every current-state edge's `claim_id` still resolves. `rebuild()` is the "always available" fix: drop everything, re-apply schema, re-project from MySQL. Safe by construction, because nothing in the graph is authoritative.

## 4. The graph data model

- `(:Entity)` — also carries a typed label `:Person` / `:Organization` / `:Project`. Properties: `entity_id`, `canonical_name`, `normalized_name`, `entity_type`, `trust`, `cms_uuid`, `status`.
- `(:Alias)` — `(e:Entity)-[:HAS_ALIAS]->(a:Alias)`, identity-keyed by the hashed `alias_key`.
- `(:Claim)` — `predicate`, `subject_id`, `object_id`/`object_literal`, `valid_from`/`valid_until`, `status`, `confidence`, `evidence_kind`, plus provenance (`document_id`, `chunk_id`, `quote`/`quote_start`/`quote_end`). Linked `-[:SUBJECT]->`, `-[:OBJECT]->`, `-[:USES_PREDICATE]->(:Predicate)`, `-[:SUPPORTED_BY]->(:Chunk|:Document)`.
- `(:Chunk)`/`(:Document)` — thin provenance stubs (id + join key only; **no text, no vectors** — that's Qdrant's job, kept out of the graph on purpose so it never becomes a second text store).
- `(:Claim)-[:CONTRADICTS|:SUPERSEDES]->(:Claim)` — conflict/version links.
- **Derived current-state edges**: `(Entity)-[:<PREDICATE_NAME> {claim_id, current:true, projection_version, valid_from, valid_until}]->(Entity)` — a relationship literally named after the predicate (e.g. `FUNDED_BY`, `LEADS`). Every one carries the `claim_id` that produced it, so `edge -> claim -> chunk/document -> Qdrant -> source text` is always walkable — full explainability from any graph fact back to its citation.

## 5. The read path — how a question gets answered FROM the graph

```
question -> route (entity + predicate) -> template -> Neo4j -> ids -> Qdrant -> rerank -> context
```

**1. Routing (`router.py`).** Deterministic, not LLM-driven — this is an explicit security choice: *a model may one day pick a template id, but nothing here builds Cypher from model output, ever.* Routing needs two things to agree:
   - an entity the question names resolves to a canonical, claim-eligible identity (reuses the **same** resolver ingestion uses, with a narrow, carefully justified query-side relaxation for cases like unambiguous person names that ingestion's corroboration rule would otherwise always reject in a single-sentence question);
   - the question is relational (asks about a relationship, not just "tell me about X").

   Two strategies, tried in order: the **schema-derived planner** (reads a predicate from the closed vocabulary, a direction from that predicate's declared domain/range, a validity window from the question's wording — so any predicate approved into the vocabulary becomes askable automatically, no new code needed) and a **legacy pattern table** (hand-written regexes) as fallback for phrasings the planner doesn't recognize yet. Entity name spans are **masked out** before cue-matching, because this corpus is full of org names like "Department of Biotechnology" that would otherwise self-trigger a structural-relationship cue.

**2. Traversal (`traverse.py`).** The *only* module that talks to the graph on the read path. It accepts a `template_id` + typed parameters — **never raw Cypher** — opens a `read_session` (enforced read-only at the driver level, since Neo4j Community has no RBAC to do it for you), runs the fixed template, and returns structured rows (ids only, never text). Every query is capped by `LIMIT $limit` and a 5-second timeout. Any exception degrades to an empty result with `.error` set — it never raises past this boundary.

**3. Templates (`templates.py`).** A closed, reviewed registry — this is the actual Cypher-injection defense, structural rather than "be careful": no fixed-length-path is even expressible (`[*]` variable-length paths are disallowed), labels/relationship types are literals in reviewed text, predicates are bound as `$parameter` values (never interpolated), and parameters are validated against a closed vocabulary/regex before ever reaching the driver (e.g. `entity_id` must match `^(?:person|org|project)_[0-9a-f]{12}$`). Templates come in two flavors: **current** (reads the derived `{current:true}` edges — cheap) and **historical** (reads `Claim` nodes and their validity windows, including superseded/disputed ones, each row carrying `status` so a caller can flag a disputed answer).

**4. Hydration (`hydrate.py`).** The graph only returns ids. This module is "the bridge the whole architecture rests on" — it turns `chunk_id`s into real text via an exact Qdrant `retrieve()` by point id (no search, no scoring — the graph already decided relevance), falling back to a scoped Qdrant `scroll()` by `document_id` for claims whose evidence is a CMS field rather than prose (currently *all* claims, since none have been LLM-extracted yet). Batched, deduplicated, and fairness-balanced across cited documents so one large document can't starve the others' evidence.

**5. Orchestration (`pipeline.answer`)**. Wires it together: route → traverse → hydrate → the *existing* reranker → the *existing* context builder. Deliberately reuses the standard `ContextBlock`/reranker machinery rather than inventing a parallel generation path. A `facts` block (the verified graph rows, rendered) is placed *before* the evidence passages — "the rows are the answer, the passages are the citation" — because for CMS-derived claims the cited passage frequently doesn't literally contain the fact (it lived in a structured field), so stating the verified fact first is what keeps the answer both correct and checkable. Every stage failure (no route, unreachable graph, empty result, failed hydration) returns an empty answer and the caller falls back to ordinary retrieval — **the graph is an enrichment, never a hard dependency.**

**6. Production integration (`policy.py` + `retriever.graph_blocks_for`).** This is the gate between "the pipeline can answer" and "production is allowed to use that answer":
   - a **capability class allow-list** (`graph_routing_classes`, default = all classes) — originally scoped for staged rollout, now mostly a rollback/debugging knob since routing derives from the approved-predicate vocabulary rather than a fixed template list;
   - a **circuit breaker** — consecutive graph failures trip it and skip graph routing for a cooldown, so a struggling Neo4j degrades gracefully instead of adding latency to every request;
   - a **wall-clock budget** (`graph_routing_budget_seconds`, default 3s) enforced via a worker-thread + future timeout, so a pathological query costs a bounded amount, never blocks `/chat`.
   
   `app/retrieval/retriever.py` calls `graph_blocks_for()` as one leg alongside ordinary semantic retrieval; **both legs run and are merged** (`_merge_graph_and_retrieval`, reserving a minimum slot count for prose evidence) rather than the graph ever fully replacing retrieval — an earlier design where the graph's answer *replaced* retrieval lost real content (e.g., "TERI was established in 1974" prose that funding-relationship rows never surfaced).

**7. Shadow mode (`shadow.py`)** — a separate, lower-stakes path: runs the graph pipeline on a background thread purely to log a comparison against what production actually returned (`document_overlap`, `novel_documents`, etc.), used to gather evidence before trusting a new capability class in production. It is provably inert on the user-visible answer: `observe()` returns `None`, so there is no value a caller could even accidentally use.

## 6. Feature flags (all in `app/config.py`)

| Flag | Default | Effect |
|---|---|---|
| `knowledge_enabled` | `False` | Master switch — off means zero Neo4j connections anywhere |
| `knowledge_process_after_index` | `False` | Build entities/claims incrementally per document during ingest |
| `knowledge_project_per_document` | `True` | Project that document's claims into Neo4j right away (else caught up at next sweep) |
| `graph_project_after_sweep` | `True` | Refresh the whole-corpus projection at the end of each ingestion sweep |
| `graph_projection_max_age_seconds` | 86400 | Threshold for the projection being reported "stale" |
| `graph_retrieval_enabled` | `False` | Gate on the graph being built/verified enough to be queried at all |
| `graph_routing_enabled` | `True` | **The kill switch** for graph-backed retrieval — false means zero queries answered from the graph, and the graph package isn't even imported on the request path |
| `graph_routing_classes` | unset (= all) | Optional allow-list to narrow which query "shapes" may route |
| `graph_routing_budget_seconds` | 3.0 | Per-request wall-clock budget for the whole graph attempt |
| `graph_shadow_enabled` | `False` | Run the graph off-path just to log comparisons, no answer impact |
| `claim_extraction_enabled` | `False` | Turns on the (expensive) LLM claim extractor; the deterministic CMS-field extractor needs no flag |

## 7. Why it's built this way (the throughline)

Every non-obvious design choice in this subsystem traces back to one sentence in `project.py`'s docstring: **"Neo4j is a rebuildable projection, never a system of record."** That single fact justifies:
- fail-open everywhere on the read path (an outage costs a log line, never a broken chat turn),
- MERGE + generation-stamped retirement instead of ordinary CRUD (a rebuild must always be safe and cheap),
- the closed template registry and code-side label/relationship allow-lists (since there's no RBAC in Community edition, application code *is* the security boundary),
- and the graph being additive to retrieval rather than a replacement for it (it's an accelerant for relational questions, not a new source of truth).
