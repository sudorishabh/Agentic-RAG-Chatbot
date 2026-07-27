# Retrieval & Response Generation — Architecture and Implementation Plan

Scope: the query-time layer only (`app/rag.py`, `app/retrieval/*`, `app/generation/*`,
`app/cache/*`, `app/api/chat.py`). The ingestion pipeline is stable and untouched;
this plan builds on what it already stores.

---

## 0. Foundation: what ingestion gives us (as-is, verified)

Retrieval design must exploit exactly what is stored. Verified from
`app/ingestion/state.py`, `terms.py`, `chunker.py`, `canonical.py`, `deps.py`:

### MySQL (authoritative catalog)

| Table | Contents | Retrieval use |
| --- | --- | --- |
| `ingest_state` | One row per document: `document_id`, `source_type` (`website` / `pdf` / `pdf_attachment`), `bundle` (Drupal content type), `entity_type` (`node` / `taxonomy_term` / `block_content`), `published_at`, `title`, `url`, `raw_meta` JSON | Counts, lists, date filters, title lookups |
| `ingest_state_author` / `_theme` | One row per (document, value) facet | Exact author/theme counts via `COUNT(DISTINCT document_id)` |
| `ingest_state_term` | (document_id, term_uuid, role) — rename-proof taxonomy links | Theme/tag scoping by UUID |
| `ingest_state_attachment` | (file_uuid, document_id, origin, url, filename) — node ↔ attached-PDF links | Website→PDF supplementation joins |
| `taxonomy_term` / `taxonomy_term_alias` | Term UUID → vocabulary, name, parent; old names archived on rename | Resolving user phrasing ("Climate", old names) to UUIDs; theme hierarchy |

Existing query helpers already cover the analytic primitives:
`state.count_documents`, `state.list_documents`, `state.distribution`,
`state.documents_for_term`, `terms.resolve_terms`.

### Qdrant (`documents` collection)

- Parent/child chunking: children carry vectors and are searched
  (`is_parent=false` filter); parents are zero-vector payload carriers fetched by
  id for context expansion.
- Child payload fields relevant to retrieval: `document_id`, `source_type`,
  `title`, `chunk_text`, `section_heading`, `section_type` (toc/references/glossary
  flagged non-searchable), `tags`, `categories`, `authors`, `term_ids`, `theme_ids`,
  `language`, `tenant_id`, `acl`, `published_at`, `source_url`, `file_url`,
  `page_number`, `has_table`, `table_markdown`, `is_current`, and cross-source links
  `pdf_id` / `article_uuid` / `linked_pdf_id` / `linked_article_uuid`.
- Payload indexes today: **only** `published_at` (datetime), `term_ids`,
  `theme_ids` (keyword). Everything else filters unindexed — see §10.

### Source linkage

A website node and its attached PDF are separate documents linked both ways:
in MySQL via `ingest_state_attachment`, in Qdrant via
`linked_pdf_id`/`linked_article_uuid` payload fields. The context builder already
uses this to detect "same content, two formats" vs genuine conflict.

---

## 1. Query intent classification

### Current state
One GPT-4o-mini structured-output call (`query_processor.process`) yields
`intent ∈ {qa, structured, chitchat}`, a pronoun-resolved `search_query`,
`answer_format ∈ {default, list, table, summary, detailed}`, plus `source_type`,
`theme`, `date_from/to`, `language`. A **second** LLM call
(`drupal_router.parse_structured`) re-extracts operation/bundle/theme/author/dates
for the structured route.

### Gaps
1. Two sequential LLM parses on every structured query — duplicated extraction,
   ~1 extra roundtrip of latency and tokens.
2. The intent set cannot express **scoped summarization** ("summarize the Climate
   theme", "summarize everything published in March 2024"). These are classified
   `qa` and answered by plain similarity search, which retrieves chunks similar to
   the *word* "summarize theme X" — not a representative sample of the *set*.
3. `author` and `tags` are extracted only on the structured path, never as QA
   facet filters, so "articles by Dr. Sharma about biofuels" under-filters.

### Plan
Merge into **one** unified analysis call returning a superset schema
(`QueryAnalysis` absorbs `StructuredQuery`):

```python
class QueryAnalysis(BaseModel):
    intent: Literal["qa", "structured", "scoped_summary", "chitchat"] = "qa"
    search_query: str
    answer_format: Literal["default", "list", "table", "summary",
                           "detailed", "timeline"] = "default"
    # shared facet scope (used by BOTH paths)
    source_type: str | None; theme: str | None; author: str | None
    tags: list[str] = []; date_from: str | None; date_to: str | None
    language: str | None
    # structured-only
    operation: Literal["count", "list", "lookup", "distribution"] | None
    bundle: str | None; group_by: str | None
    title_contains: str | None; limit: int = 10
```

Routing decision table (deterministic, in code — the LLM only labels):

| intent | Route |
| --- | --- |
| `chitchat` | direct LLM, no retrieval (as today) |
| `structured` | MySQL catalog (count/list/lookup/distribution); **fall through to `qa`** if the parse or query yields nothing (as today) |
| `scoped_summary` | new hybrid route: MySQL selects the document set → Qdrant fetches content → map-reduce summary (§5) |
| `qa` | semantic RAG with facet filters (as today, plus author/tag filters) |

**The `structured` label is about where the data lives, not the answer's shape.**
`structured` applies only when the *subject is the documents themselves* — their
counts, lists, dates, authors, themes — i.e. facts the MySQL catalog holds. A
request like "give me a table of GHG emissions by sector" is **content data**:
the numbers live inside a PDF/article body, so it routes `qa` with
`answer_format="table"` and is served by table-aware retrieval (§8), never by
the catalog. The same holds for `count`-sounding questions about in-document
quantities ("how many MW does the report say…") — content, not catalog. The
classifier prompt carries explicit boundary examples for exactly this (§11.6),
and §4's fall-through guard catches misroutes in code.

Classification stays a single small structured call — GPT-4o-mini handles flat
label+slots schemas reliably; it is *not* asked to plan, only to fill slots.
Keep the existing fail-open behavior (passthrough → `qa`).

Files: `app/retrieval/query_processor.py` (schema + system prompt),
`app/retrieval/drupal_router.py` (accept a pre-parsed analysis instead of
re-calling the LLM), `app/rag.py::_prepare` (routing).

---

## 2. Query routing strategy

```
question ──► response cache (Redis, exact signature) ──hit──► return
   │
   ▼
unified query analysis (1 × GPT-4o-mini structured call)
   │
   ├─ chitchat ────► small-talk LLM reply
   │
   ├─ structured ──► MySQL catalog answer (deterministic, no LLM in the answer path)
   │                   └─ None / no rows → fall through to qa
   │
   ├─ scoped_summary ► MySQL doc-set selection → Qdrant content fetch → map-reduce
   │
   └─ qa ──► embed (Redis-cached) ─► semantic cache (Qdrant, ≥0.97) ──hit──► return
                │
                ▼
        dense search (+facet filters; dual website/PDF pull when enabled)
                ▼
        rerank (semantic + recency + authority + table boost)
                ▼
        context build (parent expand, dedup, token budget, website lead slots)
                ▼
        grounded generation with [n] citations → marker validation → cache + metrics
```

Ordering rationale (unchanged where it already works):
- Response cache before the analysis call — a repeat question costs ~0 LLM tokens.
- Structured route before embedding — count/list answers never pay for a vector.
- Semantic cache after analysis but before search — it needs the rewritten query's
  embedding, and its partition key already includes tenant/ACL/format.

The only routing change is the new `scoped_summary` branch and the collapsed
double-parse.

---

## 3. MySQL vs Qdrant decision framework

Hard rule, encoded in routing (not left to the LLM's judgment at answer time):

| Question needs | Store | Mechanism |
| --- | --- | --- |
| Counts, "how many", aggregates | MySQL | `state.count_documents` / `state.distribution` |
| Publication dates, ranges, "most recent" | MySQL | `published_at` column, `ORDER BY published_at` |
| Author / theme / tag / content-type membership | MySQL | facet child tables + `taxonomy_term` (UUID-joined) |
| Title lookup / "show me the article called…" | MySQL | `title LIKE`, then optionally Qdrant for its content |
| "Which documents exist in scope S" (any metadata scope) | MySQL | `list_documents` → document_id set |
| What a document/theme *says*; topical similarity | Qdrant | dense search over child chunks |
| Tabular/numeric data reported *inside* documents (PDF tables, figures) | Qdrant | dense search + `has_table` boost; `table_markdown` reproduced faithfully (§8) |
| Deep explanation, comparison of content | Qdrant | dense search, parent expansion |
| Metadata scope × content question (hybrid) | Both | MySQL → id set → Qdrant `document_id` filter (§5) |

Two invariants:

1. **Numbers never come from the LLM.** Any count/date/author fact in an answer is
   computed by SQL and inserted verbatim into a deterministic template (already
   true on the structured path — keep it that way; extended by §9's count guard).
2. **The catalog defines set membership; vectors define relevance within a set.**
   When both stores could answer, MySQL wins for *which/how many*, Qdrant for
   *what/why/how*.

Theme resolution is always UUID-first (`terms.resolve_terms`, aliases included)
with display-name fallback — this pattern exists on both paths and stays.

---

## 4. Metadata retrieval strategy (structured route)

### Current state
`drupal_router` answers `count` / `list` / `distribution` from MySQL, scoped to
`source_type="website"`, `entity_type="node"` (so taxonomy/block rows never count
as content — the source-of-truth rule applied to analytics). Theme scoping is
term-UUID-first with category-name fallback. Missing rows → `None` → falls
through to semantic RAG.

### Gaps and plan
1. **Formatting ignores `answer_format`.** A user asking "articles per theme *as a
   table*" gets bullets. Add deterministic renderers (plain Python, no LLM):
   - `count` → sentence (as today).
   - `distribution` → markdown table (`| theme | count |`) when
     `answer_format == "table"`, bullets otherwise.
   - `list` → bullets / table (`| title | date | type |`) / **timeline** (grouped
     by year-month, ordered by `published_at`) per `answer_format`.
2. **`lookup` should chain into content.** "Show me the article titled X" today
   returns title+URL. When the user asks a content question about a named title,
   resolve the id via MySQL then run the QA path filtered to that `document_id` —
   this is the same hybrid primitive as §5.
3. **Distribution with theme scope**: `distribution` currently ignores
   `term_uuids` scoping (only bundle/date). Since `state.py` lives under
   `app/ingestion/` and the freeze covers it, the scoped variant goes in a new
   **retrieval-side reader**, `app/retrieval/catalog.py`, which queries the
   same MySQL tables read-only (SELECTs against `ingest_state*` /
   `taxonomy_term`) without touching any ingestion file. Existing
   `state.count_documents` / `list_documents` calls keep working as-is;
   new query needs land in `catalog.py` from now on.
4. **Author phrasing**: keep `LIKE` substring matching (handles "Dr." prefixes,
   partial names); add a disambiguation response when one name matches many
   authors and the count is small ("Did you mean: …") — deterministic, from the
   facet table.
5. **Count fall-through guard (misrouting safety).** `_answer_count` today
   *always* returns an answer — a content question misclassified as `count`
   ("table of emissions by sector") would get *"There are 0 items matching your
   query"* instead of reaching semantic retrieval. Change: return `None` (→ fall
   through to the QA path) when the parse extracted **no resolvable catalog
   dimension** — no known bundle, no theme that resolves in `taxonomy_term`, no
   author matching the facet table, no date bound. Same guard for `list`:
   zero rows with unresolvable scopes falls through (it already returns `None`
   on empty — extend the principle to `count`).

Everything here is templated output from SQL rows: zero hallucination surface,
single-digit-ms latency, no LLM tokens in the answer path.

### How MySQL is called — mechanics

**No text-to-SQL, ever.** GPT-4o-mini only fills typed slots (§1); Python maps
slots onto a **closed set of parameterized query templates**. Free-form SQL from
an LLM is both a hallucination surface (invented columns, wrong joins) and an
injection surface; the catalog's query space (counts / lists / lookups /
distributions over a fixed schema) is small enough to enumerate, which also
makes results deterministic and testable.

**Connection path** (exists, reused as-is): `app.deps.mysql_connection()` —
a pooled PyMySQL connection (`MySQLPool`, DictCursor, ping+rollback on
checkout, fail-fast checkout timeout). `deps.py` is shared plumbing used, not
modified. All catalog access is SELECT-only; no transactions needed.

**Two layers of query functions:**
1. *Existing readers, called unchanged* (they live under `app/ingestion/` but
   the freeze forbids editing, not calling — `drupal_router` already imports
   them): `state.count_documents`, `state.list_documents`,
   `state.distribution`, `state.documents_for_term`, `terms.resolve_terms`,
   `terms.get_term`. They already assemble JOIN/WHERE dynamically from
   whitelisted dimensions with `%s` placeholders and escaped `LIKE` patterns.
2. *New readers in `app/retrieval/catalog.py`* (SELECT-only, same tables,
   same `mysql_connection()`):
   - `document_ids_in_scope(...) -> list[str]` — the §5 id-set selection
     (same filters as `list_documents`, returns ids only, capped);
   - `distribution_scoped(group_by, term_uuids=..., ...)` — distribution with
     the theme join `state.distribution` lacks;
   - `authors_matching(fragment) -> list[str]` — distinct facet values for
     the §4.4 disambiguation;
   - `attachments_for(document_ids) -> dict[str, list[AttachmentRow]]` — the
     §5C website→PDF supplementation join over `ingest_state_attachment`.

**Slot → SQL resolution order** (per structured query):
1. normalize bundle (synonym map, exists);
2. resolve theme name → `term_uuid`s via `taxonomy_term` (+aliases) —
   case-insensitive exact match, alias fallback;
3. author → escaped `LIKE` against `ingest_state_author`;
4. dates → half-open `[from, to)` on `published_at`;
5. execute the one template matching `operation`, always with
   `source_type='website'`, `entity_type='node'` baked in (website is the
   catalog of record; taxonomy/block rows never count);
6. any resolution failure → return `None` → fall through to semantic RAG
   (never guess, never error the request). MySQL being *down* takes the same
   path: catalog errors are caught, logged, and degrade to RAG (exists).

**Operational notes:** every template hits indexed columns
(`idx_source_type`, `idx_bundle`, facet `idx_val`, `idx_term`), so calls are
single-digit-ms and run synchronously in the request thread. The API process
has its own pool (ingestion runs as a separate process with a separate pool).
One config check at rollout: `mysql_pool_size` (default 5) should be raised
toward the expected number of *concurrent* structured queries — queries are
ms-fast so a small pool goes far, but `chat_stream_max_concurrency=64` can
briefly exceed 5 checkouts under a burst of catalog questions. Config-only.
Freshness needs no cache invalidation: every catalog answer reads live MySQL,
so counts reflect the latest completed ingestion run by construction.

---

## 5. Hybrid retrieval architecture (the main new capability)

**Primitive: catalog-scoped semantic retrieval.**

```
scope (theme/author/bundle/dates/title) 
  → MySQL: list_documents(..., limit=N_docs) → [document_id, title, published_at, url]
  → Qdrant: search/scroll with FieldCondition(key="document_id", MatchAny(any=ids))
  → content chunks guaranteed to be inside the scope
```

This inverts today's approach (vector search + payload facet filter) when the
*set* is what the user defined. Payload facet filters remain for soft topical
scopes; id-scoping is used when MySQL is authoritative for membership.

### Route A — `scoped_summary` ("summarize the Climate theme / March 2024 / author X")

GPT-4o-mini's context is the binding constraint, so summarize hierarchically:

1. MySQL selects the scope set, most recent first (cap: ~30 docs; beyond that,
   summarize the distribution + the top N and say so — honest scoping beats
   silent truncation).
2. For each selected document, fetch its **lead parent chunk** (Qdrant scroll:
   `document_id` + `is_parent=true`, first by section order) — articles' lead
   parents (~1600 tokens max, usually far less) are the best single-chunk
   representation; fall back to first child.
3. **Map**: batch documents into groups that fit ~6k input tokens; one
   GPT-4o-mini call per batch → 3-bullet mini-summary per document (batches run
   concurrently).
4. **Reduce**: final call over the mini-summaries + the MySQL metadata table
   (titles, dates, authors) → thematic summary. Citations = the documents'
   catalog rows (title + URL), not chunk markers.
5. Small scopes (≤ ~5 docs) skip the map stage and go straight to one grounded
   call over lead parents — one LLM call total.

Latency control: map calls in parallel via the existing chat concurrency limiter;
stream only the reduce step. Expected 2–6 s for medium scopes, cacheable by the
existing response/semantic caches.

### Route B — website-first with PDF depth (detailed knowledge queries)

Already designed and implemented behind `prefer_website_enabled` (dual pull +
website lead slots + PDF fill, `docs/website-preference-retrieval.md`). Plan:
run the eval (§12), tune `website_chunk_floor` / `website_max_slots`, then flip
the flag on. No new code.

### Route C — attachment supplementation

When retrieval returns website blocks whose documents have attachments
(`ingest_state_attachment`), and the reranked PDF pool contributed nothing for
that document, the citation already exposes the PDF via `also_available`. Add
one targeted enhancement: if the question's answer_format is `detailed` and the
website block's document has an attachment, issue one extra Qdrant pull filtered
to that attachment's `document_id` (file_uuid) and let rerank decide admission.
Bounded: at most one extra search per answer.

New helper: `app/retrieval/scoped_retrieval.py` (id-set filters, lead-parent
fetch, batching); route wiring in `app/rag.py`.

---

## 6. Source prioritization and conflict resolution

Policy (matches the product rules, mostly already implemented):

1. **Website is primary.** Structured/catalog answers are already website-only
   (`source_type="website"`, `entity_type="node"`). For QA, the dual-pull +
   segregated context puts website blocks first with PDFs as depth — enable after
   eval tuning (§12).
2. **Provenance is visible end-to-end.** Context blocks are labeled
   "— TERI website —" / "— PDF documents —" (exists); citations are typed
   `website` / `pdf` with URL vs page-anchored links (exists). Answer text
   distinguishes them via prompt rule 6 (exists).
3. **Conflict rule tightened.** `_flag_conflicts` marks linked website/PDF pairs
   (excluding same-content-two-formats). Change prompt rule 5 from "lean on the
   more recent / more authoritative source" to the explicit hierarchy:
   *"If a website block and a PDF block disagree, present the website statement
   as current, and note the PDF variant as supplemental/background — cite both."*
   One-line prompt change in `app/generation/prompts.py`.
4. **PDF-only answers are labeled.** When no website block survived to the
   context, prepend nothing — but the citations are all `pdf`-typed and the UI
   shows it. Optionally add a cheap deterministic epilogue when
   `all(type=="pdf")`: "Based on PDF documents; no website coverage found." —
   generated in `_assemble`, not by the LLM.

---

## 7. Response generation pipeline

Current pipeline is sound; keep it:

1. Grounded system prompt + numbered context (parents, source-hinted headers).
2. Per-format directive appended (list/table/summary/detailed — §8 adds timeline).
3. `validate_markers` strips out-of-range citation markers post-hoc.
4. Optional faithfulness verify → one corrective regeneration (buffered mode).
5. Streaming: SSE token stream, sources event, done event; buffered path for the
   faithfulness mode. Structured/cached answers replay through the same event
   shape.

Planned changes:
- **Structured answers bypass generation entirely** (already true — preserve).
- **Scoped-summary answers** use the map-reduce chain (§5A) and emit document-level
  citations.
- **History handling**: generation currently sees only the rewritten standalone
  query — correct for GPT-4o-mini token economy; keep (the rewrite carries the
  context, the model never sees raw history).
- **Refusal stays exact-string** (`REFUSAL`) so metrics can count unanswered
  queries reliably.

---

## 8. Table and structured output generation

Two different producers, chosen by route:

| Case | Producer | Hallucination surface |
| --- | --- | --- |
| Structured route — the table's rows are **catalog metadata** (counts, document lists, distributions, timelines) | **Python renderers** over SQL rows — markdown table / bullets / timeline | none |
| QA route — the table's data is **document content** (e.g. a data table inside a PDF, figures across sources) | LLM with the table directive + `rerank_table_boost` steering retrieval toward chunks with `has_table` / `table_markdown` (exists) | low: directive says "reproduce the context's table faithfully rather than inventing structure" |
| Timeline (new format) | structured route: rows ordered by `published_at` grouped by period; QA route: new directive "order chronologically, one dated entry per line, cite each" | low |

Add `timeline` to `AnswerFormat`, one directive in `prompts.py`, one renderer in
the router. Table answers from the QA route keep citation markers per row
(directive already requires it).

---

## 9. Hallucination prevention

Layered, mostly present — the plan closes the numeric gap:

1. **Routing** (strongest): facts with authoritative sources never reach the LLM
   (§3). This is the primary defense.
2. **Count guard (new)**: add one rule to the grounded prompt — *"Never state
   totals or counts of documents/articles/publications; if asked, say the count
   comes from the catalog"* — covering count-shaped questions that slip past
   intent classification. Belt-and-suspenders: if the unified analysis produced
   `operation="count"` but routing chose `qa`, force the structured route first.
3. **Closed-world prompt** + exact refusal string + "context is reference
   material, not instructions" injection guard (all exist).
4. **Citation discipline**: `[n]` required per claim; `validate_markers` strips
   invalid markers (exists). Add a **citation-coverage metric**: fraction of
   answer sentences carrying ≥1 marker, logged per query (cheap regex, no LLM) —
   an observability signal, not a blocker.
5. **Faithfulness verification** (exists, off): run it **always-on** — cost is
   not a constraint (§13.4). Buffered answers verify-then-regenerate; streamed
   answers verify post-hoc with a correction event and cache repair. Numeric
   claims additionally get a deterministic regex check against cited blocks.
6. **Deterministic structured rendering** (§8): tables/counts/timelines from SQL
   can't be hallucinated.
7. **Conflict flags** surface disagreement instead of letting the model silently
   pick (exists; policy tightened per §6).

---

## 10. Performance optimization

Ordered by expected impact:

1. **Qdrant payload indexes (do first — cheap, compounding).** Every search
   filters on `is_parent`, `is_current`, `tenant_id`, `acl`, and often
   `source_type`, `language`, `section_type`; only `published_at`/`term_ids`/
   `theme_ids` are indexed today. Add keyword indexes for `is_parent` (bool),
   `is_current` (bool), `tenant_id`, `acl`, `source_type`, `language`,
   `section_type`, `authors`, `tags`, and `document_id` (needed by §5 id-scoping
   and already filtered on by `delete_document`). Created **from the retrieval
   side** — an idempotent startup hook in the API app (or a one-off ops script),
   *not* by editing `deps.ensure_collection`, so no ingestion-shared code
   changes. Index creation runs server-side over existing points; nothing is
   re-ingested.
2. **Collapse the double LLM parse** (§1): removes one full GPT-4o-mini roundtrip
   (~0.4–1 s) from every structured query and from every misrouted-then-fallen-
   through query.
3. **Caching** (exists, keep): Redis exact-response cache → semantic cache
   (0.97 cosine, identity-partitioned) → embedding cache. All three already
   invalidate on corpus version bumps.
4. **Concurrency**: map-stage summarization calls run in parallel under
   `chat_stream_max_concurrency`'s limiter; the dual pull's two Qdrant searches
   can run on a two-thread `ThreadPoolExecutor` (saves ~30–80 ms; optional).
5. **Token economy for GPT-4o-mini**: context budget stays at 9000 tokens
   (~5 parent blocks); reranker snippets capped at 600 chars (exists); history
   capped at 6 turns and only fed to the analysis call, never generation
   (exists). Structured answers use zero generation tokens.
6. **MySQL**: all catalog queries hit indexed columns (`idx_source_type`,
   `idx_bundle`, facet `idx_val`, term `idx_term`). Add a composite index
   `(source_type, entity_type, published_at)` if count/list latency ever shows in
   stage metrics — not needed at current corpus size.
7. **Latency budget** (p95 targets, measurable via existing stage metrics):
   cache hit < 50 ms; structured < 1.5 s (one analysis call + SQL); QA first
   token < 2.5 s; scoped summary < 6 s.

---

## 11. Prompt engineering for GPT-4o-mini

Principles (the codebase already follows most — codify them):

1. **One job per call, flat structured output.** Slot-filling schemas with
   literals/optionals (QueryAnalysis) — never free-form JSON, never multi-step
   reasoning in one call. `llm_structured_temperature` pinned (0 recommended in
   deployment env) for deterministic routing.
2. **Rules as short numbered lists** in system prompts; the grounded prompt's 7
   rules stay under ~200 tokens. Format directives are appended only when
   detected — the default path carries no dead instruction weight.
3. **Never ask mini to compute.** No arithmetic, no counting, no date math — SQL
   does it (§3); the analysis call only *extracts* dates the user stated.
4. **Context hygiene**: numbered blocks with one-line source hints
   (type · title · page · section · published) so citations need no full-URL
   repetition; group labels only when segregation happened; middle-loss
   mitigation via `_order_for_attention` on the mixed path (all exist).
5. **Rewrite-then-forget history**: the standalone `search_query` is the only
   thing generation sees — bounded prompts regardless of conversation length.
6. **Few-shot only where labels are confusable**: add 4–6 inline examples to the
   unified analysis prompt for the boundaries that matter. The critical pairs:
   - *catalog vs content data*: "show articles per theme as a table" →
     `structured` + `distribution` + table format; "show a table of GHG emissions
     by sector from the Thoothukudi report" → `qa` + table format (the numbers
     live in document content, not the catalog);
   - *catalog count vs in-document count*: "how many research papers in 2024" →
     `structured`/`count`; "how many MW of capacity does the report cite" → `qa`;
   - *scoped vs single-doc summary*: "summarize the Climate theme" →
     `scoped_summary`; "summarize this article" → `qa` + summary format.
   Keep the example block < 300 tokens.
7. **Injection resistance**: retrieved text declared non-instructional (exists);
   structured answers never echo user text into executable positions; SQL is
   parameterized throughout (exists).

---

## 12. Evaluation

### Harness (new: `scripts/eval/`)
A golden dataset (~150–250 items, versioned in-repo as JSONL) spanning the five
query classes, each item carrying: question, expected route, expected facets,
and (where applicable) ground truth — expected SQL result for analytics items,
relevant document_ids for retrieval items, must-contain / must-not-contain
assertions for generation items. Run offline against a fixed corpus snapshot.

### Metrics

| Dimension | Metric | Method |
| --- | --- | --- |
| Routing | intent / operation / facet extraction accuracy | exact match vs golden labels |
| Analytics accuracy | count / list / distribution correctness | compare rendered numbers vs direct SQL (must be 100%) |
| Retrieval | recall@k, MRR over document_ids; website-lead rate for the preference feature | golden relevant-doc labels |
| Faithfulness | `faithfulness.verify` verdict rate on eval answers; citation-coverage (sentences with markers) | LLM-judge (existing module) + regex |
| Relevance / quality | LLM-judge 1–5 rubric on sampled answers; refusal correctness (refuses when corpus lacks the answer, answers when it doesn't) | judge script + golden "unanswerable" items |
| Latency | p50/p95 per stage (`rag.query_understanding`, `rag.search`, `rag.rerank`, `rag.generate`) and end-to-end; cache hit rates | existing `metrics.py` stage collection — already recorded per query |
| User satisfaction | thumbs up/down on `/chat` responses persisted with the query signature; weekly regression review of down-voted queries | small API addition + metrics log |

### Process
- Eval runs gate the two behavior flips this plan proposes: enabling
  `prefer_website_enabled` and switching to the unified analysis prompt.
- Faithfulness sampling (§9.5) + stage metrics give the production-side signal;
  the golden set gives the pre-deploy signal.

---

## 13. Cost-no-object upgrades

Token/API cost is **not** a constraint for this deployment. That supersedes
several cost-motivated defaults above. Latency and the ingestion freeze still
bind: every upgrade here must fit the §10.7 latency budget, and nothing may
require re-ingesting the corpus.

### 13.1 Real reranking (highest-leverage single change)
The default `reranker_provider="embedding"` just reuses the dense score — the
rerank stage currently adds recency/authority blending but no second-stage
relevance model. The providers are **already implemented** in `reranker.py`;
this is config + eval, no new code:
- Preferred: **Cohere rerank-3.5** or a self-hosted **cross-encoder**
  (BGE-reranker-v2-m3, no external API, not an LLM) — purpose-built,
  ~100–300 ms for 40–100 candidates.
- Fallback if no reranking service may be added at all: the existing LLM rerank
  (`provider="llm"`) on GPT-4o-mini, refactored to parallel pointwise batches
  (§13.2.1) — slower and noisier than a cross-encoder, but still better than
  raw dense scores.
With a real reranker in place, raise `retrieval_candidate_k` 40 → **100** and
`website_candidate_k` 20 → 40 — recall rises and the reranker absorbs the noise
that made a small k prudent for dense-only ranking.

### 13.2 Getting the best out of GPT-4o-mini (the model is fixed)
GPT-4o-mini is the **only** LLM available — no upgrades, ever. Quality then
comes from three levers; all are unlimited-budget-friendly and near-free in
latency:

1. **Decompose every LLM job into a micro-task.** Mini is weak at holistic
   judging but strong at flat slot-filling and binary verdicts — so no stage
   ever asks it for more than one narrow job:
   - query analysis = slot-filling (already);
   - faithfulness = **claim extraction, then one binary "is this claim
     supported by block [n]?" call per claim, run in parallel** — far more
     reliable on mini than the current single holistic verdict;
   - LLM rerank (if used instead of a local cross-encoder) = **pointwise 0–1
     scoring in parallel batches of ~10 passages**, not one 40-passage
     listwise call.
2. **Self-consistency voting on routing.** Run the unified analysis call **3×
   in parallel** (temperature ~0.7) and majority-vote each field; ties fall
   back to `qa` (the safe route — §4's guards catch the rest). Misrouting is
   the most expensive failure mode and mini's weakest point; three concurrent
   calls add ~zero wall-clock and measurably cut label flips. Single-call,
   temperature-0 stays for the low-stakes stages.
3. **Few-shot packs + "context proving" everywhere.** Mini follows
   *demonstrated* behavior far better than *described* behavior:
   - analysis prompt: the §11.6 boundary examples;
   - grounded generation: one compact worked example (tiny numbered context →
     ideally-cited answer) always present, plus one table exemplar appended
     only when `answer_format="table"` and a timeline exemplar for
     `"timeline"` — exemplars are conditional so the default path stays lean;
   - faithfulness: one supported and one unsupported claim example;
   - structured parse: one example per confusable operation.
   Context proving means mini never sees unlabeled text: every block is
   numbered, source-typed, dated and section-titled (exists), every claim must
   carry `[n]` (exists), and the count guard keeps mini away from arithmetic
   entirely (§9).

Context budget: mini's 128k window is not the limit — its attention quality
is. Keep `context_token_budget` at 9000; eval a bump to ~12k only after the
reranker upgrade (§13.1) proves the extra blocks are actually relevant.

### 13.3 Multi-query retrieval (recall expansion)
For `qa` and `scoped_summary`: one extra structured call generates 2–3
paraphrases/decompositions of the search query; embed all (parallel), search all
(parallel), fuse with reciprocal-rank fusion before rerank. Adds ~0.5–1 s and
multiplies retrieval cost — accepted. Gate per-query: skip when the semantic
cache hit, and skip for short factoid queries where the rewrite already
disambiguated. HyDE is a cheaper-signal variant; try multi-query first, HyDE
only if eval shows residual recall gaps.

### 13.4 Always-on faithfulness verification
§9.5's 5% sampling was a cost decision. Instead:
- **Buffered path**: verify every answer, regenerate once on failure (already
  implemented behind `faithfulness_check` — turn it on).
- **Streaming path**: stream tokens as today, run the verifier post-hoc on the
  full answer, and append a `correction` SSE event (and fix the cached copy)
  when claims fail — users get speed *and* a safety net; the cache never serves
  an unverified answer twice.
- Add claim-level numeric verification: extract numbers/dates from the answer
  (regex), check each appears in the cited block's text; flag mismatches in the
  same correction path. Deterministic, no LLM.

### 13.5 Corrective retrieval loop (bounded self-RAG)
After context build, one structured judge call: "does this context suffice to
answer?" If not, reformulate once (judge suggests the missing angle) and
re-retrieve, merging results. Strictly **one** iteration (latency), and only
when the top rerank score is below a threshold — most queries skip it.

### 13.6 Keyword leg without touching ingestion
True sparse vectors (BM25/SPLADE) need vectors written at ingest time — blocked
by the ingestion freeze. The freeze-compatible equivalent: create a Qdrant
**full-text payload index** on `chunk_text` (server-side, built over existing
points, no re-ingest) and add a keyword-filtered pull (`MatchText` on extracted
key phrases) fused via RRF alongside the dense pull. Covers the classic dense
failure modes: acronyms, proper nouns, exact figures. Promote from Phase 4 to
Phase 2.

### 13.7 Scoped summaries at full breadth
Raise the §5A cap from ~30 to **~150 documents** with two-level reduce
(map → group summaries → final). Use *all* parent chunks per document (not just
the lead parent) for scopes ≤ 10 docs when `answer_format="detailed"` — full-
document grounding. Parallel map keeps wall-clock in the 6–10 s range for the
largest scopes; stream the reduce step so the user sees progress.

### 13.8 Semantic cache: accuracy over savings
At 0.97 cosine the semantic cache can return an answer to a *subtly different*
question (a changed year, a different theme) — a wrong-answer risk tolerated to
save LLM calls. With cost free, either disable it (keep the exact-signature
Redis cache, which is risk-free and covers repeats) or raise the threshold to
0.995 and require the cached entry's facet filters to match the new query's.
Recommendation: threshold + facet match; disable if eval ever catches a
mismatch.

### 13.9 Evaluation at full coverage
LLM-judge faithfulness/relevance on **100% of production traffic** (async,
off the request path), not samples; nightly full golden-set runs judged by
GPT-4o-mini using the decomposed claim-level rubric from §13.2 (mini is a
reliable judge when each verdict is binary and scoped to one claim); per-stage
latency dashboards from the existing metrics.

### 13.10 Latency ledger — what each change costs and how it's paid for

The user-facing metric is **time-to-first-token (TTFT)** on the streaming path
and total wall-clock on the buffered path. Every upgrade above is accounted
against them:

| Change | TTFT / wall-clock impact | Mitigation / gate |
| --- | --- | --- |
| Unified analysis call (§1) | **−0.4 to −1 s** on structured + fallen-through queries | pure win — removes a sequential LLM call |
| Qdrant payload indexes (§10.1) | **faster** filtered search, growing with corpus size | pure win |
| Speculative embedding (§10.4) | **−100 to −300 ms**: embed the raw question in parallel with the analysis call; reuse when the rewrite is unchanged (most single-turn queries) | wasted embed when rewritten — costs nothing we care about |
| Structured route (§4) | answers in **SQL time** (~ms) with zero generation tokens | pure win |
| Cohere / cross-encoder rerank (§13.1) | +100–300 ms per QA query | fits budget; prefer Cohere API over LLM-listwise rerank (~1 s+) precisely for speed |
| Self-consistency routing, 3× voting (§13.2) | ≈0 — the three analysis calls run concurrently; wall-clock = slowest call | pure accuracy win; mini streams fast, so even the slowest vote stays ~0.5 s |
| Few-shot packs in prompts (§13.2) | +a few hundred prompt tokens ≈ tens of ms prefill | exemplars are conditional (table/timeline ones only attach when that format was detected) |
| Multi-query retrieval (§13.3) | +300–600 ms when triggered | run the paraphrase call *concurrently* with the base-query search and fuse late; skip on cache hits and short factoids |
| Keyword leg via full-text index (§13.6) | ≈0 | one extra Qdrant query run in parallel with the dense pull |
| Always-on faithfulness (§13.4) | streaming: **0 TTFT impact** (post-hoc verify + correction event); buffered: +1–2 s | streaming is the default UX; numeric regex check is ~0 ms |
| Corrective loop (§13.5) | +1.5–3 s **only** on queries whose top rerank score is below threshold | strictly one iteration; expected to fire on a small minority |
| Scoped summary breadth (§13.7) | large scopes 6–10 s wall-clock | map calls fully parallel; reduce step streams, so perceived latency ≈ first map batch + TTFT |
| Semantic cache hardening (§13.8) | slightly lower hit rate → more full pipeline runs | exact Redis cache unaffected; accuracy is worth it |

Revised p95 targets (supersede §10.7): cache hit < 50 ms · structured < 1 s ·
QA TTFT < 2.5 s (including reranker; < 3 s when multi-query fires) ·
corrective-loop queries < 5 s · scoped summary first streamed token < 6 s.
Stage metrics (`rag.*` spans) already measure every row of this table —
regressions show up per stage, not as an undiagnosable total.

---

## Implementation phases

**Phase 1 — correctness & latency (small diffs, no behavior risk)**
1. Qdrant payload indexes via a retrieval-side startup hook / ops script (§10.1).
2. Unified query analysis; `drupal_router` consumes the parsed analysis (§1).
3. Structured-route renderers: table / timeline / format-aware output (§4, §8).
4. Author/tag facet filters on the QA path; `timeline` answer format (§1, §8).
5. Prompt tightening: website-precedence conflict rule, count guard (§6, §9).

**Phase 1b — cost-no-object config flips (no new code, eval-verified)**
6. Switch `reranker_provider` to Cohere / cross-encoder; raise
   `retrieval_candidate_k` to 100 (§13.1).
7. Self-consistency voting on the analysis call; few-shot packs for every
   prompt (analysis, generation, formats, faithfulness) (§13.2, §11).
8. Enable `faithfulness_check` for the buffered path (§13.4).
9. Semantic-cache hardening: threshold 0.995 + facet match (§13.8).

**Phase 2 — hybrid retrieval & recall**
10. `scoped_retrieval.py`: id-set filters + lead-parent fetch (§5).
11. `scoped_summary` route with map-reduce summarization (§5A, breadth per §13.7).
12. Title-lookup → content chaining; attachment supplementation pull (§4.2, §5C).
13. Multi-query retrieval with RRF fusion (§13.3).
14. Full-text payload index on `chunk_text` + keyword leg via RRF (§13.6 —
    no re-ingest).

**Phase 3 — quality & source preference**
15. Eval harness + golden dataset; 100%-traffic async judging (§12, §13.9).
16. Tune and enable `prefer_website_enabled` (§6).
17. Streaming post-hoc faithfulness with correction events; numeric claim check;
    citation-coverage metric (§13.4, §9).
18. Corrective retrieval loop, gated on low rerank confidence (§13.5).

**Phase 4 — optional**
19. HyDE, if eval shows recall gaps multi-query didn't close (§13.3).
20. Feedback endpoint for satisfaction tracking (§12).

### Risks / notes
- `MatchAny` over large id sets: cap scope sets (~100 ids) and prefer
  count+top-N honesty over unbounded scans.
- The unified analysis prompt grows; watch extraction accuracy in eval before
  cutover (fail-open passthrough already guards total failure).
- **Zero edits under `app/ingestion/` or to ingestion-shared plumbing.** New
  catalog reads live in `app/retrieval/catalog.py` (same tables, SELECT-only);
  Qdrant payload/full-text indexes are created from a retrieval-side startup
  hook; the corpus is never re-embedded or re-ingested.
