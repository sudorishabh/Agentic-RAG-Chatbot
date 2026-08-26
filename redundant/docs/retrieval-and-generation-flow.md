# Retrieval & Generation — End-to-End Flow

A plain-language walkthrough of what happens between a user asking a question and
the answer streaming back. Read this top-to-bottom; every stage links to the code
that runs it.

The pipeline lives in [`app/rag.py`](../app/rag.py), with the query-understanding
brain in [`app/retrieval/query_processor.py`](../app/retrieval/query_processor.py),
the structured/catalog capability in [`app/retrieval/database/`](../app/retrieval/database/),
and helpers under [`app/retrieval/`](../app/retrieval/) and
[`app/generation/`](../app/generation/).

---

## 1. The big picture

```
   user question + history
            │
            ▼
   stream_answer()  →  _prepare()          (app/rag.py)
            │
            ▼
   STEP A  UNDERSTAND — process()          (query_processor.py)
     multi-label QueryUnderstanding: intents[] (+confidence +rationale),
     query_rewrite, output_format, scope
        → collapsed to a legacy route (pq.intent) + capability set (pq.understanding)
            │
            ▼
   STEP B  ROUTE
     ├─ chitchat                  → plain LLM reply (no retrieval)          → done
     ├─ database (only)           → Database Planner → catalog tools        → done
     ├─ scoped_summary            → summarizer (empty scope → falls to qa)  → done
     ├─ database + qa/comparison  → DB section (deterministic) ▸ prefixed ▸ QA answer
     └─ qa (default / fallbacks)  → FULL RAG ┐
                                             ▼
                    STEP C embed + cache · STEP D retrieve
                    STEP E generate · STEP F verify + store
```

Two layers do the routing:

1. **`process()`** turns the turn into a multi-label **`QueryUnderstanding`** (a set
   of intents with confidences, plus `query_rewrite`, `output_format`, `scope`). For
   back-compat it collapses this to a single legacy **`pq.intent`** (the route) and
   exposes the full set on **`pq.understanding`**.
2. **`_prepare()`** routes on that intent and — when the intent set includes both
   `database` and a content intent — composes a **sectioned** answer.

Deep dives: [intent-classification-design.md](intent-classification-design.md),
[database-planner-architecture.md](database-planner-architecture.md),
[database-tool-registry.md](database-tool-registry.md).

---

## 2. The intent taxonomy (multi-label)

Intent is decided by an LLM, and a query may carry **several** intents at once
(e.g. `database` + `qa`). The full set with confidences lives on `pq.understanding`;
for routing it collapses to one legacy `pq.intent`.

**Content intents** — combine freely:

| Intent | Meaning | Collapses to route |
| --- | --- | --- |
| `qa` | answerable from document *content* (default) | `qa` (full RAG) |
| `database` | about the *catalog* — count / list / lookup / aggregate | `structured` (Database Planner) |
| `summarization` | overview of a doc set / conversation | `scoped_summary` (a set) or `qa`+summary (one named doc) |
| `comparison` | contrast ≥2 entities / periods / sources | `qa` |
| `structured_output` | wants a shaped answer (table/list/json/csv/…) | sets `output_format` (a modifier) |

**Terminal intents** — exclusive (suppress everything else):

| Intent | Meaning | Route today |
| --- | --- | --- |
| `chitchat` | greetings / thanks / meta | `chitchat` (no retrieval) |
| `clarification_needed` / `out_of_scope` / `safety_policy` | too vague / off-domain / unsafe | **interim:** mapped to the non-retrieving `chitchat` route — dedicated refusal/clarify handling is deferred |

> **Rule of thumb:** data *inside* a document is `qa`; facts *about the catalog*
> (how many reports) are `database`. Summarizing **one named** document is
> `qa`+summary; a **set** is `summarization` → `scoped_summary`.

---

## 3. STEP A — Query understanding

**Code:** [`query_processor.py::process`](../app/retrieval/query_processor.py) → returns a `ProcessedQuery`.

A structured-output LLM call guided by `_UNDERSTANDING_SYSTEM` (definitions,
decision boundaries, priority, and a few-shot bank) emits a **`QueryUnderstanding`**:

| Field | Meaning |
| --- | --- |
| `intents` | list of `{label, confidence, rationale}` (multi-label) |
| `query_rewrite` | standalone, pronoun-resolved rewrite of the turn |
| `output_format` | `prose`/`list`/`table`/`csv`/`json`/`markdown`/`diagram`/`timeline` |
| `scope` | `source_type`, `target`, `theme`, `author`, `tags`, `date_from/to`, `language` |
| database slots | `operation`, `group_by`, `bundle`, `title_contains`, `limit` |

### 3a. Confidence & voting (hybrid)

Controlled by `analysis_votes`:

- **`== 1`** → one call; each label's confidence is the model's **self-reported** score.
- **`> 1`** → [`_voted_understanding`](../app/retrieval/query_processor.py) fires N
  samples at temp 0.7; [`_label_confidences`](../app/retrieval/query_processor.py) sets
  each label's confidence to its **agreement share** across samples.

[`_resolve_intents`](../app/retrieval/query_processor.py) then applies the taxonomy
rules: a **threshold** gate (`intent_confidence_threshold`), **terminal exclusivity +
priority** (`safety_policy > out_of_scope > clarification_needed > chitchat`),
`structured_output`-never-alone, and a guaranteed content fallback.
[`_merge_understanding`](../app/retrieval/query_processor.py) majority-votes the scalar
attributes via [`_vote`](../app/retrieval/query_processor.py).

### 3b. Collapse to the legacy route + exposure

[`_to_legacy_analysis`](../app/retrieval/query_processor.py) maps the merged
understanding onto the fields the current pipeline consumes: a single `intent` (via
[`_primary_intent`](../app/retrieval/query_processor.py)), `answer_format` (from
`output_format`), `source_type`, `language`, `filters` (facets → Qdrant conditions
via `_facet_filters`), and the structured slots. The full multi-label result stays on
`pq.understanding` — exposed on the `/search` response and logged per query.

### 3c. Never hard-fails

Any exception (or all votes failing) → **passthrough**: `intent="qa"`, raw query, no
filters, `understanding=None`. Understanding can degrade quality but never breaks a request.

---

## 4. STEP B — Routing

**Code:** [`_prepare`](../app/rag.py). Returns a **finished result** (chitchat,
database answer, scoped summary, cache hit, refusal) or a `_Generation` (a grounded
answer still has to be produced).

```
pq.intent  (+ capabilities from pq.understanding)
   │
   ├─ chitchat                 → _chitchat()                            → finished
   │
   ├─ structured (db only)     → Database Planner → catalog tools       → finished
   │       a lookup naming ONE title on a content question →
   │       resolve_lookup_chain() adds a document_id filter, falls through to QA
   │
   ├─ scoped_summary           → summarize_scope()  (empty scope → QA)
   │
   ├─ database + qa/comparison → _db_section() deterministic catalog answer,
   │       carried as db_prefix, then continue the QA path (sectioned answer)
   │
   └─ qa (default + fallbacks) → STEP C onward
```

- **Database path** — [`drupal_router.answer_structured`](../app/retrieval/drupal_router.py)
  delegates to the [Database Planner](database-planner-architecture.md):
  [`plan()`](../app/retrieval/database/planner.py) maps the extracted slots to a tool
  call, [`execute()`](../app/retrieval/database/planner.py) runs it, and one of
  `count/list/lookup/aggregate_records` returns a deterministic, LLM-free answer (or
  `None` → fall through to semantic search).
- **Combined (`database` + content)** — the deterministic catalog answer is computed
  first ([`_db_section`](../app/rag.py)) and carried as `db_prefix`; the QA path then
  produces the grounded content answer, and STEP F composes `db_prefix` ▸ then ▸ the
  content answer. *(The two run sequentially today, not in parallel.)*
- **Lookup→read chaining** — [`resolve_lookup_chain`](../app/retrieval/database/tools.py)
  (in the database package) replaces the former `resolve_lookup_document`.

---

## 5. STEP C — Embed + cache (qa path only)

**Code:** [`_prepare`](../app/rag.py).

1. **Embed** the `search_query` once (`embed_query`) — the vector is reused
   everywhere downstream so we never embed the same query twice.
2. **Semantic cache lookup** ([`app/cache/semantic_cache.py`](../app/cache/semantic_cache.py))
   keyed by the query vector + tenant + user groups + `answer_format` + a facet
   fingerprint. A hit returns the stored answer immediately with `cached: true` — no
   retrieval, no generation.

---

## 6. STEP D — Retrieval (the heart of RAG)

**Code:** [`retrieve()`](../app/rag.py). Turns a query + vector + filters into a
short list of `ContextBlock`s ready to feed the LLM.

### 6.1 Decide which retrieval strategies to enable

Three booleans are computed up front from intent/format/scope:

| Flag | Turns on when… | Effect |
| --- | --- | --- |
| `dual` | website-preference on, **no** pinned `source_type`, format ≠ `table` | Two pulls (website + "not website") so the website's best chunks aren't drowned out by PDFs — [`_dual_search`](../app/rag.py) |
| `multi` | multi-query on, **intent == `qa`**, no `source_type`, no `filters`, query ≥ 5 words | Recall expansion via LLM paraphrases |
| `keyword_terms` | `keyword_leg_enabled` and the query has salient terms | Adds an exact-match (full-text) leg |

This is the one place the (legacy) **intent** itself gates retrieval: paraphrase
expansion is reserved for open-ended `qa`. The rest is driven by `answer_format` / scope.

### 6.2 The searches (run in parallel, then fused)

```
                 base pull  ─────────────┐
  (dual? website + not-website)          │
                                         ├──►  RRF fusion  ──►  candidate list
  paraphrase pulls (if multi) ───────────┤   (rank-based,        (up to ~40)
                                         │    fusion.py)
  keyword pull (if terms) ───────────────┘
```

- **Dense search** — [`hybrid_search.py::search`](../app/retrieval/hybrid_search.py):
  Qdrant `query_points` over the query vector. A **mandatory** filter always applies
  ([`build_filter`](../app/retrieval/hybrid_search.py)): `is_parent=false`,
  `is_current=true`, tenant match, ACL match over `user_groups`, and it excludes
  non-searchable sections (TOC / references / glossary). Facet filters from STEP A
  are appended here.
- **Multi-query** — [`_paraphrases`](../app/rag.py) asks the LLM for N alternative
  phrasings (temp 0.7), each searched with [`_paraphrase_search`](../app/rag.py).
- **Keyword leg** — [`_extract_key_terms`](../app/rag.py) pulls quoted phrases,
  Capitalized Bigrams, ACRONYMs, and years (the things dense vectors handle worst),
  then [`_keyword_search`](../app/rag.py) does a `MatchText` pull. Fails open to `[]`.
- **Fusion** — [`fusion.py::rrf`](../app/retrieval/fusion.py) merges all rankings by
  **rank** (`score = Σ 1/(60 + rank)`), so incomparable scores (cosine vs full-text)
  combine cleanly. Skipped when there's only the base pull.

### 6.3 Rerank

**Code:** [`reranker.py::rerank`](../app/retrieval/reranker.py).

Re-scores candidates with a **semantic** score from the configured provider
(`embedding` dense score / `cross_encoder` / `cohere` / `llm`), then ranks them
**relevance first, recency as the tie-break**: scores within
`rerank_relevance_tolerance` of each other form a *band*, and inside it are
banded again on passage length (a passage holding `rerank_substance_ratio` times
the text of another leads it) before being ordered by `published_at`, then a
neutral authority, then relevance. Across bands relevance always wins. The
relevance tolerance is multiplied by
`rerank_volatile_tolerance_multiplier` for queries about topics that go stale
(`app/retrieval/volatility.py`), so the tie-break fires more often there. A
`table_boost` is added to a table-bearing chunk's
relevance when `answer_format == "table"`, so it can lift the chunk a band.
Candidates below `rerank_score_threshold` are dropped. Each survivor keeps its
**raw** semantic score in `semantic_score` for the website floor later.

### 6.4 Corrective loop (one shot)

**Code:** [`_corrective_requery`](../app/rag.py).

If the corrective loop is enabled **and** the top result's semantic score is below
`corrective_min_score`, the system reformulates the query once (aim at what the
weak results missed), searches again, RRF-fuses with the current ranking, and
reranks once more. Strictly **one** iteration; any failure keeps the original.

### 6.5 Build the context

**Code:** [`context_builder.py::build_context`](../app/retrieval/context_builder.py).

Walks ranked candidates and admits each block subject to:

- **Parent expansion** — a child chunk is replaced by its larger parent chunk text
  (better context for the LLM), fetched via [`_fetch_parents`](../app/retrieval/context_builder.py).
- **De-duplication** — near-duplicate blocks (cosine ≥ `dedup_cosine_threshold`)
  are dropped; if the dup is a *linked* other-format copy it's recorded in
  `also_available` instead.
- **Token budget** — stops once `context_token_budget` is reached.
- **Website segregation** (when `dual`): website blocks lead (capped by
  `website_max_slots`, gated by a `website_chunk_floor` on raw relevance), PDFs fill
  the rest; final order is website-first.
- **Attention ordering** (non-dual): [`_order_for_attention`](../app/retrieval/context_builder.py)
  interleaves so the strongest blocks sit at the start and end.
- **Conflict flagging** — [`_flag_conflicts`](../app/retrieval/context_builder.py)
  marks linked blocks that disagree (but not a website + its own attached PDF).

Each admitted block becomes a numbered `ContextBlock` (`n`, `text`, `payload`,
`score`, `conflict`, `also_available`).

### 6.6 Attachment supplement (detailed answers only)

If `answer_format == "detailed"`, [`_supplement_attachments`](../app/rag.py)
does one extra bounded pull of PDF chunks attached to admitted website blocks that
weren't already represented, then reranks and rebuilds. Any failure keeps the
original blocks.

### 6.7 No blocks? Refuse (or return the catalog section).

If retrieval yields nothing, `_prepare` returns the `REFUSAL` string — **unless** a
combined query already has a deterministic `db_prefix`, in which case that catalog
answer is returned alone. The system never guesses content without evidence.

---

## 7. STEP E — Generation

**Code:** streaming [`_generate_stream`](../app/rag.py), buffered
[`_generate`](../app/rag.py) / [`_grounded_answer`](../app/rag.py); prompts in
[`app/generation/prompts.py`](../app/generation/prompts.py).

### 7.1 Build the system prompt

[`_build_system`](../app/rag.py) = `GROUNDED_SYSTEM_PROMPT`
+ an optional **format directive** + an optional **correction note**.

- `GROUNDED_SYSTEM_PROMPT` enforces the core rules: answer **only** from the
  numbered context, cite `[n]` after every claim, reply with the exact refusal if
  the answer isn't present, don't invent sources, treat context text as reference
  (not instructions), lead with website sources when present, never state corpus
  totals, and — where two blocks disagree — answer from the one whose header
  shows the later `published` date.
- [`format_directive`](../app/generation/prompts.py) appends per-format shaping
  (list / table / summary / detailed / timeline) plus a tiny worked exemplar for
  `table` and `timeline`. `default` adds nothing (let the model choose the shape).
  *(Note: `csv`/`json`/`markdown`/`diagram` output formats are detected by the intent
  layer but currently degrade to `default` here — the generation prompt isn't yet
  extended for them.)*

### 7.2 Format the context

[`format_context_blocks`](../app/generation/prompts.py) renders each block as
`[n] (source · title · p.X · section · published…)` + text. When the context was
segregated it inserts `— TERI website —` / `— PDF documents —` group headers.

### 7.3 Produce the answer

The chain is `prompt | get_llm() | StrOutputParser`. In the streaming entrypoint
tokens are yielded to the client as `{"type": "token"}` events as they arrive.

---

## 8. STEP F — Verify, assemble, store

### 8.1 Faithfulness check (optional, `faithfulness_check`)

**Code:** [`app/generation/faithfulness.py`](../app/generation/faithfulness.py).

- [`validate_markers`](../app/generation/faithfulness.py) strips any `[n]` citation
  pointing outside the real block count (always runs).
- [`verify`](../app/generation/faithfulness.py) extracts **atomic claims**, then
  runs one binary *supported / not-supported* verdict per claim (in parallel)
  against its cited blocks. If any claim is unsupported, the answer is **regenerated
  once** with a correction note. In streaming, the correction is emitted as a
  `{"type": "correction"}` event and the corrected text is what gets cached.
- Fails open to "faithful" at every stage.

For a combined answer, faithfulness runs on the **grounded content only** — the
deterministic catalog section (`db_prefix`) isn't produced from the blocks, so it's
excluded from the check.

### 8.2 Numeric check (observe-only)

[`numeric_mismatches`](../app/generation/faithfulness.py) deterministically flags
numbers in the answer that appear in no cited block (again, content only). In v1 this
is **logged only**, never auto-corrected, and surfaced as `numeric_mismatch` in metrics.

### 8.3 Assemble, cache, record

- [`_assemble`](../app/rag.py) builds the final dict: `answer`, `citations`
  ([`build_citations`](../app/retrieval/citations.py)), `intent`, `answer_format`,
  `used_chunks`, `conflict`, `numeric_mismatch`, `cached: false`. For a combined
  query it composes `db_prefix` + `"\n\n"` + the grounded answer.
- [`_persist`](../app/rag.py) stores the composed result in the semantic cache (keyed
  as in STEP C) so an equivalent future query short-circuits.
- [`_record`](../app/rag.py) emits query metrics (latency, intent, chunk count,
  citations present, answered vs refused, conflict, cached, per-stage timings).

### 8.4 The SSE event sequence (streaming)

```
{"type":"token", "text": "..."}          # DB section first (combined), then the
                                          # grounded answer streams token by token
{"type":"correction", "text":"...",       # only if faithfulness triggered a rewrite
 "reason":"faithfulness"}
{"type":"sources", "citations":[...],     # final metadata
 "intent":"qa", "answer_format":"...",
 "used_chunks":N, "conflict":false}
{"type":"done"}
```

Finished results from STEP B/C (chitchat, database answer, scoped summary, cache hit,
refusal) are emitted through the same shape via
[`_stream_result`](../app/rag.py) — one token event with the whole answer, then
sources + done.

---

## 9. Fallbacks & safety nets (why it rarely breaks)

| Stage | If it fails… |
| --- | --- |
| Query understanding / voting | Passthrough: `intent="qa"`, raw query, no filters |
| Below-threshold / competing intents | `_resolve_intents` keeps the top content intent; terminals resolve by priority |
| Database answer (`answer_structured`) | `None` → fall through to semantic QA |
| Combined query, content retrieval empty | Returns the deterministic catalog section alone (not a refusal) |
| Scoped summary, empty scope | Falls through to qa |
| Term resolution (theme filter) | Degrades to name-only filter |
| Multi-query / keyword / corrective / attachment legs | Each fails open to `[]` / the prior ranking |
| Rerank provider (llm / cross-encoder / cohere) | Falls back to dense score |
| Parent fetch | Falls back to child chunk text |
| Retrieval empty (pure qa) | Returns the exact `REFUSAL` string |
| Faithfulness at any stage | Assumes faithful (never blocks the answer) |

---

## 10. Key settings (knobs)

All in [`app/config.py`](../app/config.py) / `.env`:

| Setting | Controls |
| --- | --- |
| `analysis_votes` | 1 = single understanding call (self-reported confidence); >1 = N-way self-consistency vote (agreement confidence) |
| `intent_confidence_threshold` | minimum per-label confidence to keep a multi-label intent |
| `retrieval_top_k` / `retrieval_candidate_k` | final blocks / candidates pulled per search |
| `prefer_website_enabled`, `website_candidate_k`, `website_max_slots`, `website_chunk_floor` | dual pull + website-first context |
| `multi_query_enabled`, `multi_query_paraphrases` | paraphrase recall expansion |
| `keyword_leg_enabled` | exact-match full-text leg |
| `reranker_provider`, `rerank_model`, `rerank_score_threshold`, `rerank_relevance_tolerance`, `rerank_table_boost` | reranking |
| `corrective_loop_enabled`, `corrective_min_score` | one-shot corrective requery |
| `context_token_budget`, `dedup_cosine_threshold` | context building |
| `faithfulness_check` | claim-level verify + one regeneration |

---

## See also

- [intent-classification-design.md](intent-classification-design.md) — multi-label taxonomy, boundaries, confidence, schema
- [database-planner-architecture.md](database-planner-architecture.md) — planner + tools + combined-answer composition
- [database-tool-registry.md](database-tool-registry.md) — the concrete catalog tools
- [retrieval.md](retrieval.md) — reference-style module detail
- [generation.md](generation.md) — LLM factories & grounding prompts
- [architecture.md](architecture.md) — module map & request lifecycle
- [website-preference-retrieval.md](website-preference-retrieval.md) — the dual-pull design
```
