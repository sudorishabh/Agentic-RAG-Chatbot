# Database Tool Registry

The concrete, data-model-grounded tool set the [Database Planner](database-planner-architecture.md)
invokes. This document derives the registry from the application's actual schema,
services, and query patterns — not a generic template.

> **Status:** §§1–2 and §§5–7 below are the original design proposal and describe
> package paths (`app/retrieval/database/`, `drupal_router.py`, `app/rag.py`) that
> shipped under different names (`app/retrieval/structured/`,
> `app/pipeline/query_pipeline.py`) — kept as historical rationale, not a map of the
> tree. §3 and §4 are kept current below. For the natural-language resolution layer
> (fuzzy matching, `resolve_entity`, tags, Main/Other themes, the terminal-answer
> split) added after this proposal shipped, see
> [database-retrieval-redesign.md](database-retrieval-redesign.md), the current
> source of truth for that surface.

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

Catalog schema (DDL in [schema.py](../app/catalog/schema.py), writes in
[state.py](../app/catalog/state.py)). The tables were renamed from their legacy
`ingest_state*` / `taxonomy_term*` forms; the document table's name still follows
the `ingest_state_table` setting, which defaults to `documents`:

| Table | Grain | Key columns |
|---|---|---|
| `documents` | one row per document | `document_id` (PK), `source_type`, `bundle`, `entity_type`, `published_at`, `title`, `url`, `raw_meta` |
| `documents_author` | doc × author | `document_id`, `author` |
| `documents_theme` | doc × theme | `document_id`, `theme`, `theme_type` (`primary`/`sub`), `parent` — see [ingestion.md](ingestion.md#theme-rows--documents_theme) |
| `documents_term` | doc × taxonomy term | `document_id`, `term_uuid`, `role` |
| `documents_attachment` | doc × attached PDF | `file_uuid`, `document_id`, `origin`, `url` |
| `terms` / `term_aliases` | term (rename-proof) | `term_uuid` (PK), `vocabulary`, `name`, `parent_uuid`; aliases keep old names resolvable |

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

Six tools + two shared infrastructure pieces (as shipped — see the status note
above for where each landed). The tools are what the planner selects; the
infrastructure is what every tool reuses.

| # | Tool | Kind | Backing (reused) |
|---|---|---|---|
| 1 | `count_records` | generic operation | `state.count_documents` |
| 2 | `list_records` | generic operation | `state.list_documents` |
| 3 | `lookup_record` | operation + business rule (lookup→read) | `state.list_documents` + `resolve_lookup_document` logic |
| 4 | `aggregate_records` | generic operation | `state.distribution` |
| 5 | `list_themes` | structural listing (vocabulary-wide, no entity/filter scope) | `terms.list_themes` + `theme_taxonomy.group_of` |
| 6 | `resolve_entity` | fuzzy name → canonical candidate resolution | `app.retrieval.structured.resolve` (no catalog read) |
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
  "tag":    null,          // name -> resolved to term_uuids; no fallback column exists (see below)
  "author": null,          // substring match on the author facet
  "title_contains": null,  // substring match on title
  "date_from": null,       // inclusive  ┐ half-open [from, to) on published_at
  "date_to":   null        // exclusive  ┘
}
```

`tag` was added after this document's original proposal, mirroring `theme`'s
resolution with one deliberate asymmetry: an unresolved theme still has the
free-text `documents_theme` facet to fall back on, but tags have no equivalent
facet table, so an unresolved tag is always a terminal miss rather than a
degraded partial match — see §5 "Tag filtering" in
[database-retrieval-redesign.md](database-retrieval-redesign.md).

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

### Tool 5 — `list_themes`

- **Why / problem:** "what themes do you cover?", "how many themes are there?" —
  the theme vocabulary itself, not a per-document filter.
- **Kind:** structural listing — vocabulary-wide, takes no `entity`/`filters`.
- **Reuses:** `terms.list_themes` (canonical, includes zero-document themes) +
  `theme_taxonomy.group_of` to label each name Main or Other.
- **Output `ToolResult.data`:** `{ "themes": [...], "main_themes": [...], "other_themes": [...] }`,
  rendered as two labelled sections, Main first. A theme the static taxonomy map
  doesn't recognize (added in the CMS since) lists under Other rather than being
  dropped. Asking about one *specific* theme is a normal filtered query on
  another tool — this Main/Other split only applies to the "list every theme"
  case. See [database-retrieval-redesign.md §6](database-retrieval-redesign.md).

### Tool 6 — `resolve_entity`

- **Why / problem:** users write loose, synonym-heavy, sometimes misspelled names
  ("rishab negi", "climate", "env theme") that a substring `LIKE` match can't
  resolve. This tool maps free text to a ranked, scored candidate before another
  tool filters by it.
- **Kind:** resolution utility — wraps `app.retrieval.structured.resolve`
  (`difflib` + a hand-rolled token-set/prefix scorer over each type's small
  candidate set), not a catalog read.
- **Input:** `{ query: str, type: "author" | "bundle" | "theme" | null }` —
  deliberately **not** `tag` (see the `RecordFilters.tag` note above).
- **Output:** three bands, never a silent guess: a confident top match accepts
  (`ok=true`, `data.resolved`); a genuine near-tie is `ok=false`,
  `error_kind="ambiguous"`, rendered as a numbered clarification asking the user
  to pick; nothing plausible is `ok=false`, `error_kind="unresolved"`, rendered
  as an explicit "no `<type>` matching '`<query>`' found."
- **Gated by:** `entity_resolution_enabled` (config) — off by default; when off,
  `resolve_entity` still functions, but an all-failed plan falls through to
  semantic search exactly as before this tool existed, rather than surfacing the
  ambiguous/miss message. See
  [database-retrieval-redesign.md §4](database-retrieval-redesign.md).

### Uniform result envelope

```jsonc
{
  "tool": "count_records",
  "entity": "research_papers",
  "ok": true,
  "data": { "count": 12, "applied": { "entity": "research_papers", "author": "…" } },
  "citations": [ /* Citation, for list/lookup */ ],
  "rendered": "There are 12 research papers in 2024 matching your query.",
  "error": null,
  "error_kind": null
}
```

`rendered` re-homes the existing deterministic renderers (`_answer_count`,
`_render_list_table`, `_render_list_timeline`, `_answer_distribution`) so the
single-capability path stays LLM-free; multi-capability synthesis uses `data` +
`citations` as evidence. `data.applied` (added post-proposal) echoes every
non-null filter actually in effect — the structured counterpart to `rendered`
naming the same interpretation in prose, so a wrong match is catchable either
way.

`error_kind` (added post-proposal) splits `ok=false` into two situations that
used to be indistinguishable: `"unresolved"` / `"ambiguous"` mean the filter was
*understood but could not be honored* — `rendered` is the answer itself (e.g.
"no theme matching 'X' found"), not a cue to fall through. Every other
`ok=false` (`"no_records"`, `"unknown_entity"`, `"query_failed"`, or unset)
keeps this document's original fall-through-to-semantic-search behavior
unchanged. See [database-retrieval-redesign.md §7](database-retrieval-redesign.md).

---

## 4. What is deliberately NOT a tool

| Considered | Verdict | Why |
|---|---|---|
| `get_tender_count`, `get_projects`, … (per-bundle) | ✗ | bundle is a parameter (16× redundancy) |
| generic `create/update/delete_record` | ✗ | catalog is read-only; writes are frozen ingestion |
| `document_ids_in_scope`, `attachments_for` | ✗ (not DB-intent tools) | they feed the **vector** pipeline (scoped summary, attachment supplementation); already called directly. Promote to a tool only if the planner must hand a doc-set to vector retrieval — that's multi-label orchestration, not a DB answer |
| `list_terms(vocabulary)` ("what themes do you cover?") | ✓ shipped as **Tool 5, `list_themes`** | now includes the Main/Other split (§3.2 above) |
| a `tag` type on `resolve_entity` | ✗ | tags are a long-tail, freeform CMS vocabulary (~237 terms over ~224 documents in a dev-DB sample) — the shape fuzzy ranking would constantly flag as ambiguous, not a curated set worth resolving. `tag` stays a direct, exact-match `RecordFilters` field instead |

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
