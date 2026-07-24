# Database Tool Registry

The concrete, data-model-grounded tool set the [Database Planner](database-planner-architecture.md)
invokes. This document derives the registry from the application's actual schema,
services, and query patterns — not a generic template.

- **Scope:** the `database` capability (structured catalog Q&A). Read-only.
- **Unchanged:** intent layer, QA/RAG vector pipeline, summarizer, generation.
- **Hard constraint:** `app/ingestion/state.py` is under an **ingestion freeze** —
  tools may *call* its read functions but must not edit it; genuinely new SQL
  goes in `app/retrieval/catalog.py`.

---

## 1. What the codebase analysis found

### 1.1 Domain & data model

The assistant serves a TERI knowledge base with two content universes:

- **Unstructured** — PDF + website article *bodies*, chunked and embedded in Qdrant
  (the QA/RAG path). Not this registry's concern.
- **Structured catalog** — MySQL, a rebuildable projection of Drupal. This is what
  the Database capability queries.

Catalog schema (all in `ingest_state*`, see [state.py](../app/ingestion/state.py)):

| Table | Grain | Key columns |
|---|---|---|
| `ingest_state` | one row per document | `document_id` (PK), `source_type`, `bundle`, `entity_type`, `published_at`, `title`, `url`, `raw_meta` |
| `ingest_state_author` | doc × author | `document_id`, `author` |
| `ingest_state_theme` | doc × theme | `document_id`, `theme` |
| `ingest_state_term` | doc × taxonomy term | `document_id`, `term_uuid`, `role` |
| `ingest_state_attachment` | doc × attached PDF | `file_uuid`, `document_id`, `origin`, `url` |
| `taxonomy_term` / `taxonomy_term_alias` | term (rename-proof) | `term_uuid` (PK), `vocabulary`, `name`; aliases keep old names resolvable |

**Entities are content _bundles_, not tables.** The 16 bundles (`article`, `page`,
`research_papers`, `completed_projects`, `ongoing_projects`, `feature_articles`,
`news`, `events`, `press_release`, `policy_brief`, `videos`, `infographics`,
`services`, `report`, `people`, `carousel`) all live in one table as
`source_type='website', entity_type='node'`. A "tender"/"vendor"/"project" query
is a bundle filter, not a new table — so a tool per entity would be 16× redundant.

### 1.2 Access layers (and the freeze)

| Layer | Role | Query-time functions |
|---|---|---|
| [`ingestion/state.py`](../app/ingestion/state.py) | catalog read+write, **frozen for edits** | `count_documents`, `list_documents`, `distribution`, `documents_for_term`, `get` |
| [`retrieval/catalog.py`](../app/retrieval/catalog.py) | read-only retrieval readers | `document_ids_in_scope`, `attachments_for` |
| [`ingestion/terms.py`](../app/ingestion/terms.py) | taxonomy | `resolve_terms` (name→UUID, alias-aware), `get_term` |

### 1.3 How structured data is accessed today

| Caller | Uses | Purpose |
|---|---|---|
| `drupal_router.answer_structured` | `state.count_documents` / `list_documents` / `distribution`, `terms.resolve_terms` | the current `database` answer path (count/list/lookup/distribution + rendering) |
| `summarizer.summarize_scope` | `catalog.document_ids_in_scope`, `terms.resolve_terms` | pick a doc-set for scoped summary |
| `query_processor._theme_condition` | `terms.resolve_terms` | theme filter for **vector** retrieval |
| `rag._supplement_attachments` | `catalog.attachments_for` | website→PDF supplementation (vector path) |

**Two business behaviors emerge** that a generic template would miss:
1. **Rename-proof taxonomy scoping** — theme names must resolve through
   `terms.resolve_terms` (UUIDs + archived aliases) before filtering, with a
   display-name fallback for pre-catalog documents.
2. **Lookup→read chaining** — a title lookup that resolves to exactly one document
   feeds content QA (`drupal_router.resolve_lookup_document`), not just a title+URL.

**Redundancy to consolidate:** filter/theme/date/bundle assembly is reimplemented
in `state._catalog_filters`, `catalog.document_ids_in_scope`,
`drupal_router._theme_scope`/`_date_range`/`_normalize_bundle`. A single scope
resolver removes this.

---

## 2. Design principles for this app

1. **Operations are tools; the bundle is a parameter.** Four operations cover every
   observed catalog query.
2. **Read-only.** The catalog is a projection; writes belong to (frozen) ingestion.
   No CRUD-write tools.
3. **Wrap, don't reimplement.** Tools call the existing `state.*` / `catalog.*`
   readers. New SQL (only if needed) lands in `catalog.py`, never `state.py`.
4. **Business logic lives in shared infrastructure, not in every tool** — the Entity
   Registry and Scope Resolver hold the bundle/taxonomy/date rules once.

---

## 3. The registry

Four tools + two shared infrastructure pieces. The tools are what the planner
selects; the infrastructure is what every tool reuses.

| # | Tool | Kind | Backing (reused) |
|---|---|---|---|
| 1 | `count_records` | generic operation | `state.count_documents` |
| 2 | `list_records` | generic operation | `state.list_documents` |
| 3 | `lookup_record` | operation + business rule (lookup→read) | `state.list_documents` + `resolve_lookup_document` logic |
| 4 | `aggregate_records` | generic operation | `state.distribution` |
| — | **Entity Registry** | shared infra | `DEFAULT_BUNDLES`, `_BUNDLE_SYNONYMS`, `_normalize_bundle`, `_BUNDLE_LABELS` |
| — | **Scope Resolver** | shared infra (holds the business rules) | `terms.resolve_terms`, date/bundle normalization |

### Shared: Entity Registry

- **Why:** bind an entity name to its query shape once, so tools stay entity-agnostic
  and adding a content type is a data change.
- **Problem solved:** no per-bundle tools; free-text bundle names ("press release",
  "person") normalize to canonical bundles; count/list answers get correct
  singular/plural labels.
- **Reuses:** `DEFAULT_BUNDLES` (valid set), `_BUNDLE_SYNONYMS` + `_normalize_bundle`
  (aliasing), `_BUNDLE_LABELS` (display forms) — all already in `drupal_router`.
- **Entry:** `{name, aliases, labels:(singular,plural), source_type='website', entity_type='node'}`.
- **Extensibility:** a non-Drupal source later (e.g. a real `tenders` table) is one
  entry with a different backing binding — tools unchanged.

### Shared: Scope Resolver

- **Why / problem:** the theme→UUID resolution, alias fallback, half-open date
  bounds, and bundle normalization are today duplicated in four places. One
  resolver removes the drift and holds the app's two business rules (§1.3).
- **Reuses:** `terms.resolve_terms` (rename-proof), the date-bound and bundle-normalize
  helpers.
- **Input:** `RecordFilters` (below). **Output:** backing kwargs for `state.*`
  (`bundle`, `term_uuids` | `theme`, `author`, `published_from/to`, `title_contains`).

```jsonc
// RecordFilters — normalized, entity-agnostic (only the columns the catalog supports)
{
  "theme":  null,          // name -> resolved to term_uuids (alias-aware), else theme-name fallback
  "author": null,          // substring match on the author facet
  "title_contains": null,  // substring match on title
  "date_from": null,       // inclusive  ┐ half-open [from, to) on published_at
  "date_to":   null        // exclusive  ┘
}
```

### Tool 1 — `count_records`

- **Why / problem:** "how many research papers in 2024", "how many news items on the
  Climate theme" — the single most common catalog question.
- **Kind:** generic operation-level.
- **Reuses:** `state.count_documents(source_type, bundle, entity_type='node', author, term_uuids|theme, published_from, published_to)`.
- **Input:** `{ entity: str, filters: RecordFilters }`.
- **Output `ToolResult.data`:** `{ "count": int }`. Guardrail (preserved from
  `_answer_count`): an unknown bundle or an unresolvable theme returns `ok=false`
  so the caller can fall through to semantic search rather than answer a misleading 0.

### Tool 2 — `list_records`

- **Why / problem:** "list the 2023 news", "show reports by Dr Sharma" — browse/
  enumerate the catalog with citable title+URL.
- **Kind:** generic operation-level.
- **Reuses:** `state.list_documents(...)` (recent-first, `limit` clamped ≤100).
- **Input:** `{ entity, filters, sort: "recent" (default), limit: int=10 }`.
  *Note:* the backing query sorts by `published_at DESC` only; `sort` is a
  forward-compatible field (add alternatives to `catalog.py`, never `state.py`).
- **Output `ToolResult.data`:** `{ "records": [{document_id, title, url, published_at, bundle}] }`.
  (`authors`/`categories` are intentionally not hydrated by the list query.)
  Citations are built from the records.

### Tool 3 — `lookup_record`

- **Why / problem:** "find the article titled X". This carries the app's
  **lookup→read** business rule: if exactly one document matches and the turn is a
  content question, hand its `document_id` to the QA path instead of returning a
  stub.
- **Kind:** operation-level **with a domain business rule** (the chaining) — justified
  because it encapsulates real logic, not a new noun.
- **Reuses:** `state.list_documents(title_contains=…, limit≈3)` + the single-match
  resolution in `drupal_router.resolve_lookup_document`.
- **Input:** `{ entity, title: str | null, filters: RecordFilters }`.
- **Output `ToolResult.data`:** `{ "records": [...], "chain_document_id": str | null }`
  — `chain_document_id` set only on a unique content-question match.

### Tool 4 — `aggregate_records`

- **Why / problem:** "articles per theme", "how many of each content type", "count by
  year" — grouped breakdowns.
- **Kind:** generic operation-level.
- **Reuses:** `state.distribution(group_by, source_type, bundle, entity_type, published_from, published_to)`; `group_by ∈ {theme→theme, content_type→bundle, author, year}`.
- **Input:** `{ entity: str | null, group_by: "theme"|"content_type"|"author"|"year", aggregation: "count" (default), filters }`.
- **Output `ToolResult.data`:** `{ "groups": [[value, count], …] }` (largest first, ≤100).
- **Note:** `aggregation` is `count` today (the only backing capability). Sum/avg over
  a numeric field would be a new `catalog.py` reader — added under this same tool,
  not a new tool.

### Uniform result envelope

```jsonc
{
  "tool": "count_records",
  "entity": "research_papers",
  "ok": true,
  "data": { "count": 12 },                 // or {records:[…]} / {groups:[…]}
  "citations": [ /* Citation, for list/lookup */ ],
  "rendered": "There are 12 research papers in 2024 matching your query.",
  "error": null
}
```

`rendered` re-homes the existing deterministic renderers (`_answer_count`,
`_render_list_table`, `_render_list_timeline`, `_answer_distribution`) so the
single-capability path stays LLM-free; multi-capability synthesis uses `data` +
`citations` as evidence.

---

## 4. What is deliberately NOT a tool

| Considered | Verdict | Why |
|---|---|---|
| `get_tender_count`, `get_projects`, … (per-bundle) | ✗ | bundle is a parameter (16× redundancy) |
| generic `create/update/delete_record` | ✗ | catalog is read-only; writes are frozen ingestion |
| `document_ids_in_scope`, `attachments_for` | ✗ (not DB-intent tools) | they feed the **vector** pipeline (scoped summary, attachment supplementation); already called directly. Promote to a tool only if the planner must hand a doc-set to vector retrieval — that's multi-label orchestration, not a DB answer |
| `list_terms(vocabulary)` ("what themes do you cover?") | ⏳ candidate | no current access pattern; would need a new read-only `catalog.py` reader over `taxonomy_term`. Add when a use case appears |

---

## 5. Consolidation & footprint

- **6 units total** (4 tools + 2 shared) cover **every** query-time catalog pattern
  found in §1.3.
- The **Scope Resolver** collapses four duplicated filter/theme/date implementations
  into one (the `state.py`-internal `_catalog_filters` stays as-is under the freeze;
  new callers use the resolver + the existing `state.*` kwargs).
- Adding a capability is a **data** change (an Entity Registry entry) or a parameter
  (a new `group_by`/`aggregation`), not a new tool — the registry stays small.

---

## 6. Migration plan (minimal disruption)

New package `app/retrieval/database/` — additive; nothing in `state.py` changes.

**Phase 1 — infrastructure (no behavior change)**
1. `types.py` — `RecordFilters`, `ToolCall`, `ToolResult`, `DatabasePlan`.
2. `entities.py` — Entity Registry seeded from `DEFAULT_BUNDLES` + `_BUNDLE_LABELS`/`_BUNDLE_SYNONYMS`.
3. `filters.py` — the Scope Resolver (wraps `terms.resolve_terms` + date/bundle rules).

**Phase 2 — tools (behavior-preserving)**
4. `tools.py` — `count/list/lookup/aggregate_records`, each wrapping the existing
   `state.*` reader and re-homing its deterministic renderer.

**Phase 3 — planner + swap the router internals**
5. `planner.py` — `plan(analysis) -> DatabasePlan` (deterministic v1: reuse the
   `drupal_router._query_from_analysis` operation→slots mapping) + `execute()` (parallel).
6. Refactor `drupal_router.answer_structured` to: build plan → execute → render.
   **Its signature stays**, so `rag._prepare` is untouched and the change is
   internal. `resolve_lookup_document` becomes `lookup_record`'s chaining.

**Phase 4 — multi-label (later, the only `_prepare` change)**
7. When a query is `database` + `qa`/`summarization`, run the DB plan and
   `retrieve()` in parallel and pass `ToolResult.data` as evidence to the existing
   grounded generation.

Phases 1–3 are behavior-preserving and independently testable; the sole observable
change (multi-source synthesis) is isolated to Phase 4.

### Verification

- Golden queries currently answered by `answer_structured` must return byte-identical
  `rendered` output after Phase 3 (snapshot test on count/list/distribution).
- The existing `tests/test_counting.py` / `tests/test_lookup_chaining.py` /
  `tests/test_scoped_summary.py` exercise the reused readers and should stay green.

---

## 7. Open decisions

1. **Package location** — `app/retrieval/database/` (proposed) vs top-level `app/database/`.
2. **Renderers** — keep them in `tools.py`, or a dedicated `render.py` the tools call?
3. **`answer_structured`** — retire it once `_prepare` calls the planner directly, or
   keep the thin adapter permanently for the single-label path?
