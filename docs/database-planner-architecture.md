# Database Planner Architecture

How the **Database capability** is fulfilled after intent classification. The
intent layer decides *that* a query needs structured/catalog data; this layer
decides *how* — by planning calls to a small set of **parameterized, operation-
level tools**.

- **Scope of change:** the Database path only.
- **Unchanged:** the intent classification layer (labels, taxonomy, prompt), the
  QA/RAG vector pipeline (`retrieve()`), the summarizer, reranking, context
  building, and the grounded-generation prompts.
- **Related:** [intent-classification-design.md](intent-classification-design.md) · [retrieval-and-generation-flow.md](retrieval-and-generation-flow.md)

---

## 1. Principles

1. **Intent decides *what*, the planner decides *how*.** The `database` intent is a
   capability signal; the planner owns tool selection and argument construction.
2. **Operations are tools; entities are parameters.** A small, fixed set of tools
   (`count` / `list` / `lookup` / `aggregate`) parameterized by `entity` and
   `filters`. No `get_tender_count()` / `get_vendor()` — those don't scale.
3. **A new capability is data, not code.** Adding an entity = registering it in the
   Entity Registry. A new *tool* is added only when it encapsulates genuinely new
   business logic, not a new noun.
4. **The LLM plans tool calls; it never writes SQL.** Tools own the queries; the
   planner only chooses tools and fills validated arguments. This is the trust
   boundary (arg validation, entity allow-list, ACL/tenant, capped limits).
5. **Multi-label = parallel + synthesize.** When a query is `database` *and* `qa`
   (or `summarization`), the planner's tools and the existing retrieval pipeline
   run in parallel, and the LLM synthesizes both into one grounded answer.
6. **Preserve deterministic answers.** A pure count/list stays deterministic and
   LLM-free (as today); the LLM is only added to *synthesize* multi-source results.

---

## 2. Target architecture

```
                         User query + history
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │  Intent Classification    │  (unchanged)
                     │  multi-label + scope      │
                     └────────────┬─────────────┘
             capability set: {qa, database, summarization, …}
                                  │
        ┌─────────────────────────┼──────────────────────────────┐
        ▼                         ▼                               ▼
   qa capability          database capability             summarization capability
        │                         │                               │
        ▼                         ▼                               ▼
  Vector retrieval        ┌───────────────┐                 Summarizer
  (retrieve(), unchanged) │ DATABASE       │                 (unchanged)
        │                 │ PLANNER        │                       │
        │                 │ query+analysis │                       │
        │                 │  → DatabasePlan│                       │
        │                 └──────┬────────┘                       │
        │                        │ [ToolCall, ToolCall, …]         │
        │                        ▼                                 │
        │              ┌────────────────────┐                      │
        │              │ TOOL EXECUTION      │  parallel            │
        │              │ count_records       │  partial-failure     │
        │              │ list_records        │  tolerant            │
        │              │ lookup_record       │                      │
        │              │ aggregate_records   │                      │
        │              └─────────┬──────────┘                      │
        │                        │ [ToolResult, …]                  │
        └───────────┬────────────┴───────────────┬─────────────────┘
                    ▼   (results run in parallel across capabilities)
          ┌──────────────────────────────────────────────┐
          │  SYNTHESIS                                     │
          │  • single capability, simple op → deterministic│
          │  • multi-capability → grounded LLM synthesis   │
          │    (reuses existing generation + citations)    │
          └──────────────────────────────────────────────┘
```

---

## 3. Components

### 3.1 Entity Registry — the extensibility mechanism

A registry mapping an **entity name** to how it is queried. Today's entities are
the Drupal content bundles (`news`, `research_papers`, `events`, …), all backed by
the ingested catalog in [`app/ingestion/state.py`](../app/ingestion/state.py).

Each entry declares:

| Field | Purpose |
|---|---|
| `name` | canonical entity id (e.g. `news`) |
| `aliases` | free-text synonyms → canonical (reuses today's `_BUNDLE_SYNONYMS`, `_normalize_bundle`) |
| `backing` | the query binding — for bundles: `state.*` with `source_type="website"`, `entity_type="node"`, `bundle=name` |
| `filter_map` | how normalized `RecordFilters` map to backing kwargs (theme→`term_uuids`/`category`, author, dates, `title_contains`) |
| `labels` | singular/plural display forms (reuses today's `_BUNDLE_LABELS`) |
| `authz` | optional per-entity ACL/tenant rule |

**Adding an entity later** (e.g. a `tenders` table) = one registry entry with its
backing query + filter map. No new tools, no planner change, no intent change.

### 3.2 Operation-level tools

> The concrete, data-model-grounded registry (per-tool justification, input/output
> schemas, and reused code) is specified in
> [database-tool-registry.md](database-tool-registry.md). This section is the shape.

A fixed, small, orthogonal set. Each takes an `entity` + normalized `filters`,
resolves the entity via the registry, executes the backing query, and returns a
`ToolResult` (structured data + citations + a deterministic text rendering).

| Tool | Signature | Backing (today) |
|---|---|---|
| `count_records` | `(entity, filters) -> ToolResult` | `state.count_documents(...)` |
| `list_records` | `(entity, filters, sort=None, limit=10) -> ToolResult` | `state.list_documents(...)` |
| `lookup_record` | `(entity, id=None, filters=None) -> ToolResult` | `state.list_documents(..., limit≈3)` + single-match resolution |
| `aggregate_records` | `(entity, aggregation, group_by, filters) -> ToolResult` | `state.distribution(group_by, ...)` (v1: `aggregation="count"`) |

Notes:
- `aggregate_records` generalizes today's `distribution`; v1 supports
  `aggregation="count"` (per-group counts). Other aggregations (sum/avg over a
  numeric field) are added per-entity later without new tools.
- `lookup_record` preserves the current "lookup → content QA" chaining
  (`resolve_lookup_document`): when a title lookup resolves to exactly one
  document and the turn asks about content, the result carries that
  `document_id` so the orchestrator can chain into the QA path.
- The deterministic renderers (`_render_list_table`, `_render_list_timeline`,
  count/distribution phrasing) move **out of `drupal_router`** and become the
  tools' text rendering — re-homed, not rewritten.

### 3.3 Database Planner

**Responsibility:** turn a database-intent query into a `DatabasePlan` — an ordered
list of `ToolCall`s. The planner is the *owner* of the operation→tool decision.

**Input:** the query, the conversation history, and the intent-layer analysis
(scope facets + the operation/db-slot hints it already extracts).

**Output:** `DatabasePlan = [ToolCall(tool, entity, args), …]`.

Two implementations behind one interface:

- **v1 — deterministic (default, zero extra LLM cost).** Translate the intent
  analysis directly: `operation` → tool, db slots → args, scope facets →
  `filters`. This is exactly today's `_query_from_analysis` + dispatch, refactored
  behind the planner interface. One tool call per query.
- **v2 — LLM multi-tool (opt-in).** A dedicated planning call that can emit
  *several* tool calls for compound database asks ("counts of news **and** reports
  per year"). Emits a **structured plan object** (not a free-form agent loop) so
  the plan can be validated, guardrailed, parallelized, and logged before
  execution.

> The v1/v2 split keeps the component boundary clean: consumers depend on
> `plan()`, not on how the operation was chosen. Starting at v1 means **no new
> LLM call and no behavior change** for the common single-operation case.

### 3.4 Execution

`execute(plan) -> list[ToolResult]`:
- Independent `ToolCall`s run **in parallel** (thread pool, mirroring the existing
  multi-query executor in `rag.retrieve`).
- **Partial-failure tolerant:** a failing tool yields an empty/error `ToolResult`;
  the rest still return (fail-open, consistent with the current router's
  `None`-on-error behavior).
- Every `ToolCall` is **validated before execution**: entity in the registry
  allow-list, filters well-formed, `limit` capped, ACL/tenant applied.

### 3.5 Synthesis

- **Single capability, simple op** (`database` only, one count/list/distribution):
  return the tool's deterministic rendering — unchanged from today, exact and
  LLM-free.
- **Multi-capability** (`database` + `qa`/`comparison`) — **sectioned composition**:
  keep the tool's exact deterministic rendering as one section and prefix it onto
  the grounded, cited content answer (in `rag._assemble` / `stream_answer`).
  Faithfulness and numeric checks run on the grounded content only, so the catalog
  count stays exact. If content retrieval comes up empty, the catalog section is
  returned alone rather than a refusal.

---

## 4. Multi-label orchestration

The only pipeline touch-point is [`app/rag.py::_prepare`](../app/rag.py), which
today branches on a single `intent`. The new shape (capabilities from the
multi-label intent set):

```
caps = capabilities(pq)                      # from the intent layer

run in parallel:
   if "database" in caps:      db_results  = execute(planner.plan(q, analysis))
   if "qa" in caps:            doc_blocks  = retrieve(...)          # unchanged
   if "summarization" in caps: summary     = summarize_scope(...)   # unchanged

compose (sectioned):
   db-only            → db_results[0].rendered                   # deterministic, complete
   database + content → db_prefix (deterministic) + "\n\n" + generate(doc_blocks)
   content-only       → generate(doc_blocks)                     # unchanged QA path
```

- QA retrieval (`retrieve()`) is **called, not modified**.
- Terminal intents (`chitchat` / `out_of_scope` / `safety_policy` /
  `clarification_needed`) still short-circuit in the intent layer, before the
  planner is ever reached.

---

## 5. Data contracts

```jsonc
// RecordFilters — normalized, entity-agnostic
{
  "theme": null, "author": null, "tags": [],
  "title_contains": null,
  "date_from": null, "date_to": null      // half-open [from, to)
}

// ToolCall — one planned operation
{
  "tool": "count_records",                 // count | list | lookup | aggregate _records
  "entity": "research_papers",
  "args": { "filters": { "date_from": "2024-01-01", "date_to": "2025-01-01" } }
}

// DatabasePlan
{ "calls": [ /* ToolCall, … */ ], "rationale": "count over research_papers in 2024" }

// ToolResult — structured data + evidence + rendering
{
  "tool": "count_records",
  "entity": "research_papers",
  "ok": true,
  "data": { "count": 12 },                 // or { "records": [...] } / { "groups": [...] }
  "citations": [ /* Citation, … */ ],
  "rendered": "There are 12 research papers in 2024 matching your query.",
  "error": null
}
```

---

## 6. Components to change

| Component | Change | Disruption |
|---|---|---|
| `app/retrieval/query_processor.py` (intent layer) | **none** | — |
| `app/retrieval/hybrid_search.py`, `retrieve()`, `reranker`, `context_builder`, `summarizer` | **none** | — |
| `app/generation/*` (prompts, generation) | **none** (evidence adapted to existing shape) | — |
| **NEW** `app/retrieval/database/types.py` | `RecordFilters`, `ToolCall`, `ToolResult`, `DatabasePlan` | additive |
| **NEW** `app/retrieval/database/entities.py` | Entity Registry (seed with Drupal bundles; reuse `_BUNDLE_LABELS`, `_normalize_bundle`, `_theme_scope`, term resolution) | additive |
| **NEW** `app/retrieval/database/tools.py` | `count/list/lookup/aggregate_records` wrapping `state.*`; re-home renderers | additive |
| **NEW** `app/retrieval/database/planner.py` | `plan()` (v1 deterministic) + `execute()` (parallel) | additive |
| `app/retrieval/drupal_router.py` | refactor: rendering → tools; `answer_structured` delegates to planner+tools (kept as thin adapter for back-compat) | low — re-home, not rewrite |
| `app/rag.py::_prepare` | orchestration: database → planner; multi-label → parallel + combined synthesis | **the one pipeline change** |

---

## 7. Guardrails & safety

- **No LLM SQL** — tools construct parameterized queries only.
- **Entity allow-list** — an unknown `entity` is rejected (never a silent full-table
  scan); mirrors today's "unknown bundle → None → fall through", now explicit.
- **Filter validation** — dates parsed to half-open ranges; `limit` capped;
  unknown filter keys dropped.
- **AuthZ** — tenant/ACL applied per entity at execution, same principal model as
  the retrieval path.
- **Fail-open** — a failed/empty tool degrades gracefully (partial results or
  fall-through to semantic search), never a hard error.

---

## 8. Extensibility — the payoff

| To add… | You do… | You do NOT touch… |
|---|---|---|
| A new content type / data source (e.g. `tenders`) | register one Entity entry (backing query + filter map + labels) | tools, planner, intent layer |
| A new operation (e.g. `sum` of a numeric field) | extend `aggregate_records` args, or add one tool if the logic is genuinely new | intent layer, existing tools |
| A domain tool with real business logic (e.g. `rank_vendors_by_sla`) | add a dedicated tool (justified: new logic, not a new noun) | intent layer, other tools |

---

## 9. Recommended improvements (beyond the ask)

1. **Move operation extraction fully into the planner (later).** The intent layer
   currently also extracts `operation`/`group_by`/etc. Once the planner is in
   place, those DB slots can leave the intent prompt, shrinking it and removing the
   redundancy — a clean-up, deferred to respect "don't change the intent layer now."
2. **Plan cache.** The `DatabasePlan` is deterministic data; cache it per
   (normalized query + facets) to skip re-planning on repeats.
3. **Tool-result caching** for hot aggregates (e.g. corpus-wide distributions).
4. **Typed entity schemas** so the planner/validator can reject impossible filters
   per entity (e.g. `author` on an entity that has none).
5. **Observability** — log the `DatabasePlan` and per-tool timings/row counts;
   add a metrics dimension for tool usage, mirroring the intent exposure.

---

## 10. Phased plan

1. **Contracts + registry** — `types.py`, `entities.py` seeded with current bundles.
2. **Tools** — `count/list/lookup/aggregate_records` wrapping `state.*`; re-home renderers.
3. **Planner v1 (deterministic)** + parallel `execute()`.
4. **Router refactor** — `answer_structured` delegates to planner+tools (behavior-preserving).
5. **Orchestration** — `_prepare` runs the database capability via the planner; add multi-label parallel + combined synthesis.
6. *(Later)* Planner v2 (LLM multi-tool), plan/result caching, the §9 cleanups.

Steps 1–4 are behavior-preserving and independently testable; the observable
change (multi-source synthesis) lands only at step 5.

---

## 11. Open decisions

1. **Package location** — `app/retrieval/database/` (proposed) vs a top-level
   `app/database/`?
2. **`answer_structured` fate** — keep as a thin back-compat adapter, or migrate
   callers to the planner and remove it?
3. **Planner v2 timing** — ship v1 (deterministic) now and defer the LLM
   multi-tool planner until a compound-database use case appears? (Recommended.)
