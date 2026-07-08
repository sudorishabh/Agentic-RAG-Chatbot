# Retrieval

The query-time pipeline: **understand → search → rerank → build context → cite**,
plus the structured (non-RAG) path. Orchestrated by `retrieve()` and friends in
[app/rag.py](../app/rag.py).

## 1. Query understanding — [app/retrieval/query_processor.py](../app/retrieval/query_processor.py)

`process(question, history=None) -> ProcessedQuery`

A structured-output LLM call (via `get_structured_llm`) classifies and rewrites the
question over up to the last ~6 turns of history. It **fails open**: on any LLM error
it returns the original question with `intent="qa"`.

`ProcessedQuery`:

| Field | Meaning |
| --- | --- |
| `original` | unmodified user input |
| `search_query` | pronoun-resolved, standalone query for retrieval |
| `intent` | `qa` \| `structured` \| `chitchat` |
| `source_type` | `pdf` / `website` if the user was explicit, else None. Also gates the website-preference dual pull (see §6): when set, retrieval uses a single filtered pull, not the dual pull |
| `language` | two-letter code if explicit, else None |
| `filters` | Qdrant `FieldCondition`s derived from the facets above — may include a `source_type` match, a `language` match, and a `published_at` `DatetimeRange` (from `date_from`/`date_to`) |
| `needs_retrieval` | property — false only for `chitchat` |

Intents route differently (see [architecture.md](architecture.md#query-lifecycle)):
`chitchat` answers directly, `structured` tries the Drupal router, `qa` runs full RAG.

## 2. Hybrid search — [app/retrieval/hybrid_search.py](../app/retrieval/hybrid_search.py)

`search(query, *, limit=None, tenant_id="default", user_groups=None, extra_filter=None,
extra_must_not=None, query_vector=None, with_vectors=True) -> list[Candidate]`

- Embeds the query (or reuses a passed `query_vector`) and queries Qdrant for up to
  `limit` candidates (default `retrieval_candidate_k` = 40).
- `build_filter(...)` constructs the **mandatory** filter: `is_parent=false`,
  `is_current=true`, `tenant_id` match, plus an ACL `MatchAny` over `user_groups`
  (default `["public"]`), plus any `extra` facet filters from query understanding.
  `extra_must_not` adds negated conditions — used by the "not website" pull of the
  website-preference feature (§6) so every chunk is reachable by exactly one pull.

`Candidate`: `id`, `score`, `payload`, `vector`, `semantic_score`, with convenience
properties `parent_id` (`payload["parent_chunk_id"]`) and `text`
(`payload["chunk_text"]`). `semantic_score` carries the raw (pre-blend) relevance
score that `rerank()` populates, so the context builder can apply the website
relevance floor.

> **Today this is dense-only.** `hybrid_use_sparse` is reserved; server-side sparse +
> RRF fusion is designed but not yet wired in.

## 3. Reranking — [app/retrieval/reranker.py](../app/retrieval/reranker.py)

`rerank(query, candidates, *, top_n=None, table_boost=0.0) -> list[Candidate]`

Computes a **semantic** score (per provider), normalizes it to [0,1], then blends it
with recency and authority (and adds `table_boost` to table-bearing chunks when the
answer format is `table`). Each returned `Candidate` also carries its **raw** semantic
score in `semantic_score` (used downstream for the website relevance floor):

```
ws = max(0, 1 - rerank_recency_weight - rerank_authority_weight)
blended = ws*semantic_norm + rerank_recency_weight*recency + rerank_authority_weight*authority
```

Candidates below `rerank_score_threshold` are dropped; the rest are sorted and the top
`top_n` (default `retrieval_top_k`) returned with `score` set to the blended value.

Providers (`reranker_provider`):

| Provider | How it scores | Notes |
| --- | --- | --- |
| `embedding` *(default)* | reuses the Qdrant dense similarity | no extra model/infra |
| `llm` | one structured-output call scores all passages 0..1 | capped at ~40 candidates |
| `cross_encoder` | sentence-transformers CrossEncoder over (query, text) | default model `BAAI/bge-reranker-v2-m3`, cached |
| `cohere` | Cohere Rerank API | default model `rerank-3.5` |

Authority is **neutral** (0.5 for all source types) unless a payload carries an
explicit `source_authority` override. The old source-type authority map (which
penalized website content) was **removed** — website preference is now handled by the
dual pull + segregation (§6), not by a scoring tilt. Recency is derived from
`published_at`.

## 4. Context building — [app/retrieval/context_builder.py](../app/retrieval/context_builder.py)

`build_context(candidates, *, limit=None, token_budget=None, segregate=False,
website_max_slots=None, website_chunk_floor=None) -> list[ContextBlock]`

Admission (via the shared `_admit` walker) applies, per candidate:

1. **Parent-expand** — replace each winning child with its parent chunk (fetched from
   Qdrant by `parent_chunk_id`) for fuller context.
2. **Cosine dedup** — drop blocks ≥ `dedup_cosine_threshold` (default 0.92) similar to
   one already kept; if the duplicate is a *linked* document, record it under
   `also_available` so it can still be cited as a secondary source.
3. **Token budget** — keep within `context_token_budget` (default 9000) and at most
   `limit`/`retrieval_top_k` blocks (the first block is always admitted).

Then, depending on `segregate`:

- **`segregate=False`** (default; single-pull / explicit-intent / table queries):
  walk candidates in ranked order, then **attention-order** (interleave
  strongest-first/strongest-last to mitigate "lost in the middle") and renumber `n`.
- **`segregate=True`** (website-preference dual pull, §6): two-pass admission —
  website candidates first (in ranked order, admitting each that clears
  `website_chunk_floor`, capped at `website_max_slots`), then everything else fills
  the remaining slots. Final order is **website-first, then PDF**; `n` renumbered in
  that order (this replaces attention ordering for these queries).

**Conflict flag** — after admission, blocks linked to another selected block are
marked `conflict=True`, **except** a website node paired with its own attached PDF
(`{website, pdf_attachment}` linked pair) — that's the same content in two formats,
not a genuine conflict.

`ContextBlock`: `n`, `text`, `payload`, `score`, `conflict`, `also_available[]`.

## 5. Citations — [app/retrieval/citations.py](../app/retrieval/citations.py)

`build_citations(blocks) -> list[Citation]`

Built **entirely from payloads** — the LLM never produces a citation, only a `[n]`
marker. Per block:

- **website** → `title` + the page URL (`file_url` if an attached file exists, else
  `source_url`).
- **pdf** → `title` + a deep link `"{source_base_url}/source/<pdf_id>#page=<page>"`
  (pdf_id from `pdf_id` or `document_id`; `file_url` used directly when present),
  plus `page` and `section`.
- Any `also_available` entries become secondary `CitationSource`s.

`Citation` (in [app/schemas/query.py](../app/schemas/query.py)): `n`, `type`, `title`,
`url`, `page`, `section`, `document_id`, `also_available[]`.

Citations are built in block order, so when the context is segregated (§6) the list
arrives **website citations first, then PDF**. The `type` field (`website`/`pdf`) lets
the frontend render two labeled sections ("TERI website" / "PDF documents") with no
backend schema change.

## 6. Website-content preference (dual retrieval)

Feature-flagged by `prefer_website_enabled` (default **off**). Full design and
rationale: [website-preference-retrieval.md](website-preference-retrieval.md).

The corpus is ~11k PDFs vs a small amount of Drupal website content, so a single
similarity pull is almost all PDF and website content often never enters the
candidate set. When enabled, `retrieve()` (in [app/rag.py](../app/rag.py)) runs
**two pulls sharing one query vector** and merges them before the single rerank:

- **website pull** — `source_type == "website"`, `website_candidate_k` (= 20)
- **not-website pull** — `source_type != "website"` (via `extra_must_not`),
  `retrieval_candidate_k` (= 40)

The union is reranked once (scores are comparable — same query vector), then
`build_context(..., segregate=True)` produces a **website-first** context: a concise
website lead (capped at `website_max_slots` = 2, each clearing `website_chunk_floor`)
followed by PDF depth (the majority). Generation is told to lead with website content
and supplement with PDF detail; citations come out website-first.

The dual pull is **skipped** (single-pull path, `segregate=False`) when:

- `prefer_website_enabled` is off, or
- the user pinned a `source_type` (explicit intent — honor their filter; a
  "not website" pull would contradict an explicit `website` filter), or
- the answer format is `table` (tables live in PDFs — don't force a website lead).

Sizing note: `context_token_budget` was raised to 9000 so ~5 blocks fit (2 website +
~3 PDF); at the old 6000 only ~3 fit, which starved PDF depth. Both caches key on a
preference-config fingerprint (see [operations.md](operations.md#caching)) so toggling
or tuning the feature self-invalidates stale answers.

## Structured path — [app/retrieval/drupal_router.py](../app/retrieval/drupal_router.py)

For `intent == "structured"` queries (exact lookups, counts, filtered lists) that are
better answered relationally than semantically. **Answered entirely from the local
catalog** — the `ingest_state` table in MySQL
([app/ingestion/state.py](../app/ingestion/state.py)), which stores each ingested
document's bundle, title, url, authors, categories, and publish date. No live
website/JSON:API calls happen at query time, so `count` and `list` read the same
source and always agree.

- `parse_structured(question, history=None) -> StructuredQuery | None` — LLM parses the
  question into `{ operation: lookup|list|count, bundle, title_contains, author, year,
  limit }`.
- `answer_structured(question, history=None) -> dict | None` — runs the operation over
  the catalog and returns an answer dict shaped like the RAG response
  (`answer`, `citations`, `intent="structured"`, `used_chunks`, `conflict=false`,
  `cached=false`), or `None` if it can't handle the query — in which case
  [app/rag.py](../app/rag.py) falls through to the normal RAG pipeline.

Query shapes:

| Operation | Behavior |
| --- | --- |
| `count` | `state.count_documents(...)` by bundle / author / date range → "There are N …" |
| `list` | `state.list_documents(...)` — up to `limit` items, most recent first, with title/url citations |
| `lookup` | a single item (list with limit 1) |

Existing deployments need the one-time `python -m app.ingestion.backfill` so
pre-catalog documents carry `title`/`url` (see
[operations.md](operations.md#maintenance-notes)); new ingests populate them
automatically.
