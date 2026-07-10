# Phase 2 Implementation Handoff — Hybrid Retrieval & Recall

Self-contained context for implementing Phase 2 of
`docs/retrieval-response-architecture-plan.md` (§5, §13.3, §13.6, §13.7).
Companion to `docs/phase1-implementation-handoff.md` — read that first for the
system snapshot (MySQL schema, Qdrant payload, pipeline flow, code idiom,
test patterns); this document does not repeat it.

**Precondition:** Phase 1 is implemented and committed. Phase 1 was executed
step-by-step with user approval, so the code may differ in detail from what
this document assumes — **verify §2 below against the actual code before
writing anything** (read `app/retrieval/query_processor.py`,
`app/retrieval/drupal_router.py`, `app/rag.py`, `app/generation/prompts.py`,
`scripts/`).

---

## 1. Hard constraints (unchanged from Phase 1)

1. **Ingestion frozen**: zero edits under `app/ingestion/` and to
   `app/deps.py`. Calling ingestion read functions is fine. Additive,
   retrieval-only settings in `app/config.py` are acceptable in Phase 2 (new
   fields with safe defaults, nothing ingestion reads).
2. **Qdrant collection safety**: an ingestion run may be in progress at any
   time. Phase 2 code only *reads* the `documents` collection. The one
   collection-altering artifact (full-text index on `chunk_text`, step 7) is a
   **script that is written but never executed by the assistant** — the user
   runs it when no ingestion run is active.
3. **GPT-4o-mini only.** Map-reduce summarization, paraphrase generation, and
   any judging are decomposed micro-tasks with few-shot examples, structured
   outputs, pinned temperature for parsing.
4. **Numbers never from the LLM**; no text-to-SQL. New SQL lives in a closed
   set of parameterized templates in `app/retrieval/catalog.py`.
5. **Latency matters**: parallelize (bounded ThreadPoolExecutor), gate optional
   pulls, keep TTFT low. Fail-open everywhere — a failing new component
   degrades to the existing pipeline, never errors the request.

## 2. Assumed post-Phase-1 state (VERIFY FIRST)

- `QueryAnalysis` (query_processor.py) carries structured slots: `operation`
  (`count|list|lookup|distribution|None`), `bundle`, `group_by`,
  `title_contains`, `author`, `tags`, `limit`; `AnswerFormat` includes
  `"timeline"`; `ProcessedQuery.analysis: QueryAnalysis | None`.
- `drupal_router.answer_structured(question, history=None, *, analysis=None)`
  consumes the unified analysis (no second LLM parse when provided);
  `_answer_count` falls through (returns None) on unresolvable scopes;
  structured renderers honor table/timeline formats.
- `_facet_filters` adds `authors`/`tags` MatchAny conditions.
- Grounded prompt has the website-precedence conflict rule and the
  corpus-count guard; `_FORMAT_DIRECTIVES` has `"timeline"`.
- `scripts/create_payload_indexes.py` exists (keyword indexes incl.
  `document_id`). **Ask the user whether it has been run** — id-set filtering
  (this phase) works without the `document_id` index but is slower; production
  rollout should have it.

## 3. What Phase 2 builds

```
                        ┌── (A) catalog.py ──────────────┐
question → analysis ────┤   MySQL id-set / joins         │
   │                    └────────────┬───────────────────┘
   ├─ scoped_summary ► ids ► lead parents ► map-reduce ► doc-level citations
   ├─ lookup+content  ► resolve title → id ► QA scoped to that document
   ├─ qa (detailed)   ► normal RAG + attachment supplementation pull
   └─ qa              ► multi-query paraphrases ∥ base search → RRF → rerank
                        (+ keyword leg via full-text index, once created)
```

New modules: `app/retrieval/catalog.py`, `app/retrieval/scoped_retrieval.py`,
`app/retrieval/fusion.py` (RRF), plus wiring in `rag.py` /
`query_processor.py` / `drupal_router.py` and one script.

## 4. Working protocol with the user (same as Phase 1)

One small step at a time → run tests (`python -m pytest tests/ -q`) → give a
**one-line commit message** (no body, no attribution, no "Step N") → **wait
for explicit approval** before the next step. The user commits manually.

## 5. Steps (in order; one commit each)

### Step 1 — `app/retrieval/catalog.py` (MySQL readers, SELECT-only)
Uses `app.deps.mysql_connection()`; table name via
`get_settings().ingest_state_table` (mirror `state._table()` guard logic
locally — do not import private helpers; small local `_like()` escaper too).
All queries bake in `source_type='website'`, `entity_type='node'` unless a
param overrides.

```python
def document_ids_in_scope(*, bundle=None, term_uuids=None, category=None,
    author=None, title_contains=None, published_from=None, published_to=None,
    limit=150) -> list[str]           # ORDER BY published_at DESC; capped [1, 300]
def authors_matching(fragment: str, limit: int = 10) -> list[str]
    # SELECT DISTINCT author FROM `{t}_author` WHERE author LIKE %s ORDER BY author
def attachments_for(document_ids: Sequence[str]) -> dict[str, list[dict]]
    # rows from `{t}_attachment` keyed by document_id: {file_uuid, origin, url, filename}
def distribution_scoped(group_by, *, term_uuids, bundle=None,
    published_from=None, published_to=None, limit=20) -> list[tuple[str, int]]
    # the theme-scoped breakdown state.distribution lacks (join `{t}_term`)
```
Fail-open: DB errors → log warning, return empty. Tests: `_FakeCursor`/
`_FakeConn` pattern from `tests/test_theme_queries.py` (monkeypatch
`catalog.mysql_connection`); assert SQL shape + params like the existing
catalog tests do.
Commit: `feat(retrieval): read-only mysql catalog readers`

### Step 2 — `app/retrieval/scoped_retrieval.py` (Qdrant reads, id-scoped)
Read-only against `documents`. Key functions:

```python
def search_within_documents(query_vector, document_ids, *, limit,
    tenant_id="default", user_groups=None) -> list[Candidate]
    # hybrid_search.search(...) with extra_filter=[FieldCondition("document_id",
    # MatchAny(any=ids))]; ids capped (~150) — caller pre-caps via catalog limit
def lead_parents(document_ids, *, tenant_id="default", user_groups=None)
    -> dict[str, dict]   # document_id -> best single payload for summarization
```
`lead_parents` mechanics (children carry `chunk_index`, parents don't):
scroll/query children filtered `document_id ∈ ids` + `chunk_index == 0`
(one per doc), then `client.retrieve` their `parent_chunk_id`s in one batch;
payload fallback = the child itself when it has no parent (single-child docs
skip parent emission — verified chunker behavior). Respect ACL/tenant via
`hybrid_search.build_filter`. Fail-open: errors → `{}`.
Tests: fake qdrant client object (duck-typed `query_points`/`retrieve`) —
no network.
Commit: `feat(retrieval): document-scoped qdrant fetch and lead parents`

### Step 3 — `scoped_summary` route (schema + rag wiring + map-reduce)
1. `query_processor`: add `"scoped_summary"` to `Intent`; extend
   `_ANALYSIS_SYSTEM`: *scoped_summary = summarize a SET of documents defined
   by theme/author/period/type ("summarize the Climate theme", "overview of
   2024 publications"); qa = content question or single-document summary*.
   Add the boundary example pair.
2. New `app/retrieval/summarizer.py`:
   - `summarize_scope(analysis, *, tenant_id, user_groups) -> dict | None`
   - resolve scope via `terms.resolve_terms` + `catalog.document_ids_in_scope`
     (cap ~30 docs v1; **ask user** before raising toward §13.7's 150).
   - fetch `scoped_retrieval.lead_parents`.
   - ≤5 docs: one grounded call over numbered lead-parent blocks (reuse
     `format_context_blocks` shape; cite [n]).
   - >5 docs: **map** — batch docs into ~6k-token groups, one structured
     GPT-4o-mini call per batch → per-doc 2–3 bullet mini-summaries, batches
     run on a bounded `ThreadPoolExecutor(max_workers=4)`; **reduce** — one
     call over mini-summaries + a metadata line per doc (title · date ·
     bundle) → final summary. Few-shot: one worked mini-summary example in the
     map prompt.
   - Citations: document-level `Citation(type="website", title, url,
     document_id)` for every doc actually summarized. Result dict mirrors the
     structured-route shape (`intent="scoped_summary"`, `used_chunks=len(docs)`).
   - Empty scope / any failure → `None`.
3. `rag.py::_prepare`: route `pq.intent == "scoped_summary"` →
   `summarize_scope(...)`; `None` → continue into normal QA path. Returned
   result flows through the existing response-cache/`_stream_result`
   machinery unchanged (buffered v1 — streaming the reduce step is a later
   enhancement).
Tests: batching math, ≤5-doc path uses one call, empty scope → None, result
shape; LLM stubbed.
Commit: `feat(retrieval): scoped summary route with map-reduce over catalog scope`

### Step 4 — Title-lookup → content chaining
In `drupal_router`: when `operation == "lookup"` and `title_contains` is set,
resolve via `state.list_documents(title_contains=..., limit=3)`. If exactly
one confident match **and** the question asks about content (heuristic:
`analysis.answer_format in ("summary","detailed")` or the original question
contains an interrogative beyond "show/find"), return a **marker** result
`{"chain_document_id": <id>, ...}` — or cleaner: expose
`resolve_lookup_document(analysis) -> str | None` and do the chaining in
`rag.py`: run `retrieve()` with an extra
`FieldCondition("document_id", MatchValue(value=id))` filter, then normal
generation (grounded, cited). Multiple/no matches → existing list behavior.
Keep it simple; this step must not complicate `_prepare` beyond one branch.
Tests: resolution + branch selection; no LLM.
Commit: `feat(retrieval): lookup queries chain into document-scoped answers`

### Step 5 — Attachment supplementation pull (§5C)
In `rag.py::retrieve` (or a helper): after `build_context`, when
`answer_format == "detailed"`: collect website blocks' `document_id`s →
`catalog.attachments_for(ids)` → for attachments whose file_uuid is **not**
already represented among admitted blocks (`document_id`/`linked_pdf_id`
checks), run **one** extra `search_within_documents(query_vector,
attachment_file_uuids, limit=10)`, rerank the union, rebuild context.
Strictly one extra Qdrant query; skip when no website blocks or no
attachments. Fail-open: errors → keep original blocks.
Tests: supplementation triggers only under the right conditions (fakes).
Commit: `feat(retrieval): attached-pdf supplementation for detailed answers`

### Step 6 — Multi-query retrieval with RRF (§13.3)
1. `app/retrieval/fusion.py`: `rrf(rankings: Sequence[Sequence[Candidate]],
   k: int = 60) -> list[Candidate]` — fuse by candidate id, keep
   payload/vector from first sighting, fused score into `.score`.
2. Paraphrase generation: structured call → `class Paraphrases(BaseModel):
   queries: list[str]` (2–3, few-shot with one example); temperature ~0.7.
3. `rag.py::retrieve`: when enabled and not gated off — run base search and
   paraphrase generation **concurrently** (ThreadPoolExecutor); embed
   paraphrases via `embed_query_cached`; run their searches in parallel;
   RRF-fuse all candidate lists → rerank as usual.
   Gates (skip multi-query): query short (< ~5 words), or
   `pq.intent != "qa"`, or explicit `source_type`/heavy filters already set.
4. Config (additive): `multi_query_enabled: bool = False`,
   `multi_query_paraphrases: int = 2`. Launch OFF; flip after eval.
Tests: RRF math (stable, id-dedup), gating logic; LLM stubbed.
Commit: `feat(retrieval): multi-query expansion with reciprocal rank fusion`

### Step 7 — Full-text index script + keyword leg (§13.6) — script NOT run
1. Extend `scripts/create_payload_indexes.py` (or new
   `scripts/create_fulltext_index.py`): TEXT payload index on `chunk_text`
   (`PayloadSchemaType.TEXT` with word tokenizer, lowercase); idempotent,
   `--dry-run`. **Do not execute; user runs it when no ingestion is active.**
2. Keyword leg in `retrieve()` (behind existing `hybrid_use_sparse` setting or
   new `keyword_leg_enabled: bool = False`): deterministically extract salient
   terms from `search_query` (quoted phrases, ALL-CAPS acronyms, 4-digit
   years/numbers, capitalized bigrams); if any, one extra search with
   `FieldCondition("chunk_text", MatchText(text=...))` in parallel with the
   dense pull; RRF-fuse via `fusion.rrf`. Skip silently when the index doesn't
   exist yet (Qdrant errors → fail-open, dense-only).
Tests: term extraction, fusion wiring, fail-open when MatchText errors.
Commit: `feat(retrieval): full-text keyword leg fused with dense search`

## 6. Latency accounting (respect these)

- scoped_summary: ≤5 docs ≈ one LLM call (~2–3 s); >5 docs: parallel map
  (batches of ~6k tokens, 4 workers) + one reduce — target < 6–10 s.
- multi-query: paraphrase call overlaps base search → net +300–600 ms, gated.
- attachment pull: +1 Qdrant query (~50 ms), only on `detailed`.
- keyword leg: parallel with dense pull ≈ +0.
- Everything else is SQL-speed. Add `span(...)` tracing blocks around each new
  stage (`rag.scoped_summary`, `rag.multi_query`, `rag.keyword_leg`, …) so the
  existing stage metrics capture them.

## 7. Out of scope for Phase 2

Eval harness / golden set, `prefer_website_enabled` flip, reranker provider
switch, always-on faithfulness, self-consistency voting, corrective loop,
streaming the scoped-summary reduce step, feedback endpoint — Phases 1b/3
per the plan. Anything editing `app/ingestion/` or `app/deps.py`.

## 8. Open decisions to confirm with the user

1. **Scope cap** for scoped_summary v1: 30 docs (recommended) or straight to
   §13.7's 150 with two-level reduce?
2. **Multi-query default**: launch OFF behind config (recommended) and flip
   after Phase 3 eval, or ON immediately?
3. **Keyword-leg flag**: reuse the reserved `hybrid_use_sparse` setting or add
   a new, honestly-named `keyword_leg_enabled` (recommended: new flag; sparse
   vectors may come later and the reserved name should keep meaning that)?
4. **Step 7 timing**: confirm when ingestion is idle so the full-text index
   script can be run (index build on `chunk_text` is the heaviest index this
   plan creates).
5. Has `scripts/create_payload_indexes.py` (Phase 1) been run yet? Needed
   before id-set filtering ships to production traffic.
