# Phase 1 Implementation Handoff — Retrieval & Response Layer

Self-contained context for implementing Phase 1 of
`docs/retrieval-response-architecture-plan.md`. A fresh session should be able
to work from this document alone. All file/function facts below were verified
against the code on 2026-07-10 (branch `main`).

---

## 1. Hard constraints (non-negotiable)

1. **Ingestion is frozen.** Zero edits to any file under `app/ingestion/`
   (including `state.py`, `terms.py`) and zero edits to ingestion-shared
   plumbing (`app/deps.py`, `app/config.py` additions are allowed only if
   purely retrieval-side settings — prefer not to touch config in Phase 1).
   **Calling** existing ingestion read functions is fine — the retrieval layer
   already does (`drupal_router` imports `state` and `terms`).
2. **An ingestion run is IN PROGRESS against Qdrant.** No step may write to or
   alter the `documents` collection while it runs. Phase 1 has exactly one
   Qdrant-altering item — payload-index creation — which must be delivered as a
   **standalone script that is written but NOT executed** (the user runs it
   after ingestion completes). Everything else only *reads* Qdrant or doesn't
   touch it at all.
3. **GPT-4o-mini is the only LLM.** No model upgrades. Quality comes from:
   micro-task decomposition, few-shot examples, tight context ("context
   proving"), structured outputs, temperature pinned for parsing.
4. **Numbers never come from the LLM.** Counts/dates/authors are SQL results
   inserted into deterministic templates. No text-to-SQL — the LLM fills typed
   slots; Python maps slots to a closed set of parameterized queries.
5. **Latency matters.** The main Phase 1 latency win is removing the second
   LLM parse on structured queries.

## 2. Working protocol with the user

- Implement **one small step at a time**.
- After each step: run the relevant tests, then give the user a **commit
  message** — one short line, no body, no attribution/name, no "Step N"
  narration (e.g. `feat(query): unified query analysis schema`). The **user
  commits manually**; do not run `git commit`.
- **Wait for the user's explicit approval before starting the next step.**
- Write clean code that matches the codebase idiom (see §5).

## 3. System snapshot (verified)

### Architecture
FastAPI app. Query pipeline in `app/rag.py`:
`_prepare()` = shared front-matter for both `answer_query` (buffered) and
`stream_answer` (SSE): response cache (Redis exact signature) → query
understanding (`process()`) → chitchat short-circuit → structured route
(`answer_structured()`, falls through to RAG on `None`) → embed (Redis-cached)
→ semantic cache (separate Qdrant collection `semantic_cache`) → `retrieve()`
→ `_Generation` dataclass handed to the generation step.

`retrieve()` (rag.py): optional dual pull (website / not-website) behind
`prefer_website_enabled` (currently **False**) → `rerank()` →
`build_context()` (parent expansion, cosine dedup, token budget 9000,
conflict flagging).

### Key files
| File | Role | Phase 1 touches? |
| --- | --- | --- |
| `app/retrieval/query_processor.py` (150 ln) | LLM query analysis → `ProcessedQuery` + Qdrant facet filters | YES (steps 1, 5) |
| `app/retrieval/drupal_router.py` (268 ln) | structured route: 2nd LLM parse → MySQL count/list/distribution | YES (steps 2, 3, 4) |
| `app/rag.py` (435 ln) | orchestration | YES (step 2, small) |
| `app/generation/prompts.py` (105 ln) | grounded/chitchat prompts, format directives | YES (steps 5, 6) |
| `app/retrieval/hybrid_search.py` | Qdrant dense search + mandatory filter | no |
| `app/retrieval/context_builder.py` | parent expand, dedup, budget, website slots | no |
| `app/retrieval/reranker.py` | providers: embedding (default) / llm / cross_encoder / cohere | no |
| `app/retrieval/citations.py`, `app/schemas/query.py` | citation building / API models | no |
| `app/ingestion/state.py`, `terms.py` | MySQL readers (CALL ONLY, never edit) | call only |
| `app/deps.py` | Qdrant client, `ensure_collection` (indexes: only `published_at`, `term_ids`, `theme_ids`), MySQL pool | do NOT edit |
| `scripts/` | ops scripts | YES (step 7, new file) |

### MySQL catalog (read via `app.deps.mysql_connection()`, pooled PyMySQL, DictCursor)
- `ingest_state`: document_id PK, source_type (`website`/`pdf`/`pdf_attachment`),
  bundle, entity_type (`node`/`taxonomy_term`/`block_content`), published_at,
  title, url, raw_meta JSON.
- `ingest_state_author`, `ingest_state_category`: (document_id, value) facet rows.
- `ingest_state_term`: (document_id, term_uuid, role).
- `ingest_state_attachment`: (file_uuid, document_id, origin, url, filename).
- `taxonomy_term` (term_uuid PK, vocabulary, name, parent_uuid) +
  `taxonomy_term_alias` (old names).
- Existing readers (signatures matter):
  - `state.count_documents(source_type=None, bundle=None, *, entity_type=None,
    author=None, term_uuids=None, category=None, published_from=None,
    published_to=None) -> int`
  - `state.list_documents(... same + title_contains=None, limit=10) ->
    list[StateRecord]` (StateRecord has .title .url .document_id .published_at
    .bundle)
  - `state.distribution(group_by, source_type="website", bundle=None, *,
    entity_type=None, published_from=None, published_to=None, limit=20) ->
    list[(value, count)]` — group_by ∈ {bundle, author, category, year};
    **no term_uuids param** (that gap is Phase 2, new module
    `app/retrieval/catalog.py`).
  - `terms.resolve_terms(name, vocabulary=None) -> [{term_uuid, name}]` —
    case-insensitive exact match, alias fallback.

### Qdrant `documents` collection
Child chunks searched (`is_parent=false` in mandatory filter, plus
`is_current=true`, tenant, ACL MatchAny, must_not section_type ∈
toc/references/glossary). Payload fields available for filters:
`document_id, source_type, title, tags, categories, authors, term_ids,
theme_ids, language, published_at, has_table, table_markdown, page_number,
section_heading, section_type, parent_chunk_id, source_url, file_url,
linked_pdf_id, linked_article_uuid`.

### Current query_processor shape (before step 1)
- `QueryAnalysis(BaseModel)`: intent(`qa|structured|chitchat`), search_query,
  answer_format(`default|list|table|summary|detailed`), source_type, theme,
  date_from, date_to, language.
- `ProcessedQuery(dataclass)`: original, search_query, intent, answer_format,
  source_type, language, filters(list of Qdrant FieldConditions).
- `process(question, history)` — one structured call via
  `get_structured_llm().with_structured_output(QueryAnalysis)`; **fails open**
  to passthrough (`intent="qa"`, no filters) on any exception.
- `_facet_filters(analysis)` builds: theme condition (term_uuids OR display
  names), source_type match (`pdf`→ `["pdf","pdf_attachment"]`,
  `website`→`["website","article"]`), language, published_at DatetimeRange.

### Current drupal_router shape (before step 2)
- `StructuredQuery(BaseModel)`: operation(`lookup|list|count|distribution`),
  bundle, theme, group_by(`theme|content_type|author|year`), title_contains,
  author, year, date_from, date_to, limit.
- `parse_structured(question, history)` — the **second LLM call** to remove.
- `_normalize_bundle` (synonyms: person→people, paper→research_papers, …;
  unknown key stays as-is so it counts zero, never widens).
- `_theme_scope(sq)` → `{"term_uuids": [...]}` or `{"category": name}`.
- `_answer_count` → **always returns a result dict** (even total=0) unless the
  DB errors → the §4-guard defect to fix in step 3.
- `_answer_list` → None when no rows (correct); `_answer_distribution` → None
  when no rows (correct).
- All catalog calls hardcode `source_type="website"`, `entity_type="node"`.
- `answer_structured(question, history)` → parse → normalize → dispatch;
  returns None → rag.py falls through to semantic RAG. rag.py then does
  `structured.setdefault("answer_format", pq.answer_format)`.

### Bundles (for prompts)
`DEFAULT_BUNDLES` in `app/ingestion/extractors/drupal_extractor.py:44`:
news, feature_articles, completed_projects, events, press_release,
research_papers, ongoing_projects, article, … (import it, don't copy).

### LLM plumbing
`app/generation/llm_client.py`: `get_llm(temperature=None, streaming=False)`
(lru_cached), `get_structured_llm()` uses `llm_structured_temperature` setting.
AzureChatOpenAI; deployment = `azure_openai_model` (GPT-4o-mini).

## 4. Tests you must keep green (and extend)

Run: `python -m pytest tests/ -q` (no MySQL/Qdrant/LLM needed — all faked).

- `tests/test_counting.py` — covers `_normalize_bundle`, `_date_range`,
  `_period_label`, `_count_result` grammar, `_answer_count` catalog kwargs
  (exact dict assert — **adding kwargs to the count_documents call will break
  `test_answer_count_passes_catalog_filters`**; update deliberately),
  `answer_structured` with `parse_structured` monkeypatched, `_facet_filters`
  datetime range.
- `tests/test_theme_queries.py` — `terms.resolve_terms` via `_FakeCursor`/
  `_FakeConn` (monkeypatch `module.mysql_connection`), catalog SQL shapes,
  `_theme_scope`, `_answer_distribution`, `qp._theme_condition`.
- Pattern for new tests: monkeypatch `dr.parse_structured` / `state.count_documents`
  / `terms.resolve_terms`; never invoke the real LLM. Follow the docstring
  style at the top of each test file.
- Note: `tests/test_router.py` is the **PDF extraction** router, unrelated.

## 5. Code style expectations (observed idiom)

- `from __future__ import annotations`; dataclasses for internal carriers,
  Pydantic for LLM-structured outputs and API schemas.
- Lazy imports inside functions for optional/heavy deps (qdrant models, LLM).
- Fail-open everywhere: LLM/DB errors are caught, logged
  (`logger.warning(..., exc_info=True)`), and degrade (passthrough / None /
  fallback) — never 500 the request.
- Comments only for non-obvious constraints/rationale, matching existing
  density. Parameterized SQL with `%s`; `_like()` escaping for LIKE.
- Short module docstrings describing purpose.

## 6. Phase 1 steps (in order; one commit each; wait for approval between)

Reordered so Qdrant-neutral steps come first; the only Qdrant-touching
artifact (index script) is written last and **never executed by you**.

### Step 1 — Unified analysis schema (`query_processor.py`)
Extend `QueryAnalysis` with the structured slots so one LLM call serves both
paths: `operation: Literal["count","list","lookup","distribution"] | None`,
`bundle: str | None`, `group_by: Literal["theme","content_type","author","year"] | None`,
`title_contains: str | None`, `author: str | None`, `tags: list[str] = []`,
`limit: int = 10`. Add `"timeline"` to `AnswerFormat`.
Extend `_ANALYSIS_SYSTEM` with: slot descriptions (adapt from
`drupal_router._PARSE_SYSTEM`, import `DEFAULT_BUNDLES` for the bundle list),
the **catalog-vs-content boundary** ("`structured` only when the subject is
the documents themselves; data *inside* documents — e.g. a table of emissions
from a PDF — is `qa` with the matching answer_format"), and 4–6 compact
boundary examples (see plan §11.6: catalog table vs PDF-data table; catalog
count vs in-document quantity). Carry the full analysis on
`ProcessedQuery.analysis: QueryAnalysis | None = None` (None on passthrough).
Do not change filter behavior in this step.
Tests: extend test_counting.py minimally (ProcessedQuery carries analysis;
schema defaults). Commit msg suggestion:
`feat(query): unified analysis schema with structured slots`

### Step 2 — Router consumes the analysis (kill the second LLM call)
`drupal_router.answer_structured(question, history=None, *, analysis=None)`:
when `analysis` is provided and `analysis.operation` is set, build
`StructuredQuery` from its fields (map `date_from/to`; no `year` field — the
unified prompt asks for explicit dates; keep `year` on StructuredQuery for
back-compat) and skip `parse_structured`; otherwise fall back to the existing
parse (keeps old callers/tests working). In `rag.py::_prepare`, pass
`analysis=pq.analysis`. Keep `structured.setdefault("answer_format", ...)`.
Tests: analysis-provided path builds the right StructuredQuery; fallback path
still parses. Commit msg suggestion:
`feat(retrieval): structured route reuses unified analysis, drops second LLM parse`

### Step 3 — Count fall-through guard (`drupal_router.py`)
`_answer_count` returns `None` (→ semantic fallback) when **no resolvable
catalog dimension** exists: no known bundle (after `_normalize_bundle`, check
membership in `DEFAULT_BUNDLES`), no theme that resolved to term_uuids AND no
category fallback hit (a theme that resolves to `{"category": name}` counts as
unresolved only if you can cheaply verify; acceptable v1: theme present but
`resolve_terms` empty → treat as unresolved), no author, no date bounds.
A bare "how many items?" (no dimensions at all) may still answer the total —
decide: answer totals only when the question had no scoping nouns; simplest
rule: `operation=="count"` with zero extracted dimensions AND bundle None →
still answer (it's a genuine corpus-size question). Guard specifically the
case: *unknown bundle* (normalized key not in DEFAULT_BUNDLES) or *unresolved
theme* → None. Update `test_answer_count_*` accordingly and add cases.
Commit msg suggestion:
`fix(retrieval): unresolvable count scopes fall through to semantic search`

### Step 4 — Format-aware structured renderers (`drupal_router.py`)
Pass `answer_format` into the dispatch (`answer_structured` already knows the
analysis). Deterministic Python renderers:
- `distribution` + `table` → GitHub markdown table (`| <label> | count |`).
- `list` + `table` → `| title | published | type |` (+ URL in title link).
- `list` + `timeline` → group by year (desc), `- YYYY-MM: title (url)` lines.
- default shapes unchanged (bullets / sentence).
Keep citations behavior as-is (list route builds Citation rows already).
Tests: renderer unit tests per shape. Commit msg suggestion:
`feat(retrieval): structured answers honor table and timeline formats`

### Step 5 — QA facet filters for author/tags + timeline directive
`query_processor._facet_filters`: add `authors` MatchAny when
`analysis.author` set (payload field `authors` holds display names — match the
raw string; substring matching isn't possible in Qdrant MatchAny, note this
limitation in a comment), and `tags` MatchAny for `analysis.tags`.
`prompts.py`: add `"timeline"` to `_FORMAT_DIRECTIVES` ("order
chronologically, one dated entry per line, each with its citation").
Tests: filter construction. Commit msg suggestion:
`feat(query): author/tag facet filters and timeline directive`

### Step 6 — Grounded prompt tightening (`prompts.py`)
- Rule 5 → explicit hierarchy: website statement is current; PDF variant is
  supplemental/background; cite both.
- New rule: never state corpus-level counts of documents/articles; such totals
  come from the catalog.
Keep the prompt under ~250 tokens total; it's sent on every QA query.
Tests: none needed beyond existing (prompt is a constant); eyeball length.
Commit msg suggestion:
`feat(generation): website-precedence conflict rule and count guard`

### Step 7 — Payload-index script (NEW FILE, DO NOT RUN)
`scripts/create_payload_indexes.py`: idempotent; uses
`app.deps.get_qdrant_client()` + `get_settings().qdrant_collection`; creates
keyword indexes for `is_parent` (BOOL), `is_current` (BOOL), `tenant_id`,
`acl`, `source_type`, `language`, `section_type`, `authors`, `tags`,
`document_id` (KEYWORD); prints what it created vs already existed; `--dry-run`
flag. Mirror the try/except style of `deps._ensure_keyword_index` but do NOT
modify deps.py. **Tell the user to run it only after the current ingestion run
completes.** Commit msg suggestion:
`feat(scripts): idempotent qdrant payload index creation`

## 7. Explicitly out of scope for Phase 1

`scoped_summary` route and `app/retrieval/catalog.py` (Phase 2); multi-query,
full-text keyword leg, corrective loop, always-on faithfulness, self-consistency
voting (Phase 1b/2/3 per plan); `prefer_website_enabled` flip (Phase 3, after
eval); reranker provider switch (Phase 1b, config decision with user);
anything touching `app/ingestion/` or `deps.py`.

## 8. Open decisions to confirm with the user before/while implementing

1. Step 3: should a fully unscoped "how many items do you have?" answer the
   corpus total, or also fall through? (Recommended: answer the total.)
2. Step 5: author matching in Qdrant is exact-value only (display names like
   "Dr R K Sharma") — acceptable v1, or defer author QA filtering to the
   Phase 2 catalog id-scoping (which supports LIKE)? (Recommended: ship exact
   match now, note limitation.)
3. Step 7: confirm when ingestion finishes so the index script can be run.
