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
| `source_type` | `pdf` / `article` if the user was explicit, else None |
| `language` | two-letter code if explicit, else None |
| `filters` | Qdrant `FieldCondition`s derived from the facets above |
| `needs_retrieval` | property — false only for `chitchat` |

Intents route differently (see [architecture.md](architecture.md#query-lifecycle)):
`chitchat` answers directly, `structured` tries the Drupal router, `qa` runs full RAG.

## 2. Hybrid search — [app/retrieval/hybrid_search.py](../app/retrieval/hybrid_search.py)

`search(query, *, limit=None, tenant_id="default", user_groups=None, extra_filter=None,
query_vector=None, with_vectors=True) -> list[Candidate]`

- Embeds the query (or reuses a passed `query_vector`) and queries Qdrant for up to
  `limit` candidates (default `retrieval_candidate_k` = 40).
- `build_filter(...)` constructs the **mandatory** filter: `is_parent=false`,
  `is_current=true`, `tenant_id` match, plus an ACL `MatchAny` over `user_groups`
  (default `["public"]`), plus any `extra` facet filters from query understanding.

`Candidate`: `id`, `score`, `payload`, `vector`, with convenience properties
`parent_id` (`payload["parent_chunk_id"]`) and `text` (`payload["chunk_text"]`).

> **Today this is dense-only.** `hybrid_use_sparse` is reserved; server-side sparse +
> RRF fusion is designed but not yet wired in.

## 3. Reranking — [app/retrieval/reranker.py](../app/retrieval/reranker.py)

`rerank(query, candidates, *, top_n=None) -> list[Candidate]`

Computes a **semantic** score (per provider), normalizes it to [0,1], then blends it
with recency and authority:

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

Authority defaults by source type: `pdf` 1.0, `report`/`policy` 0.95, `article` 0.65,
else 0.5 (a payload `source_authority` overrides). Recency is derived from `published_at`.

## 4. Context building — [app/retrieval/context_builder.py](../app/retrieval/context_builder.py)

`build_context(candidates, *, limit=None, token_budget=None) -> list[ContextBlock]`

1. **Parent-expand** — replace each winning child with its parent chunk (fetched from
   Qdrant by `parent_chunk_id`) for fuller context.
2. **Cosine dedup** — drop blocks ≥ `dedup_cosine_threshold` (default 0.92) similar to
   one already kept; if the duplicate is a *linked* document, record it under
   `also_available` so it can still be cited as a secondary source.
3. **Conflict flag** — mark blocks that are linked to another selected block
   (`conflict=True`) so generation can surface discrepancies.
4. **Attention ordering** — interleave strongest-first/strongest-last to mitigate
   "lost in the middle"; renumber `n` accordingly.
5. **Token budget** — keep within `context_token_budget` (default 8000) and at most
   `limit`/`retrieval_top_k` blocks.

`ContextBlock`: `n`, `text`, `payload`, `score`, `conflict`, `also_available[]`.

## 5. Citations — [app/retrieval/citations.py](../app/retrieval/citations.py)

`build_citations(blocks) -> list[Citation]`

Built **entirely from payloads** — the LLM never produces a citation, only a `[n]`
marker. Per block:

- **article** → `title` + `source_url` (linked directly).
- **pdf** → `title` + a deep link `"/viewer?doc=<pdf_id>#page=<page>"` (pdf_id from
  `pdf_id` or `document_id`), plus `page` and `section`.
- Any `also_available` entries become secondary `CitationSource`s.

`Citation` (in [app/schemas/query.py](../app/schemas/query.py)): `n`, `type`, `title`,
`url`, `page`, `section`, `document_id`, `also_available[]`.

## Structured path — [app/retrieval/drupal_router.py](../app/retrieval/drupal_router.py)

For `intent == "structured"` queries (exact lookups, counts, filtered lists) that are
better answered relationally than semantically.

- `parse_structured(question, history=None) -> StructuredQuery | None` — LLM parses the
  question into `{ operation: lookup|list|count, bundle, title_contains, author, year,
  limit }`.
- `answer_structured(question, history=None) -> dict | None` — executes against the
  Drupal JSON:API and returns an answer dict shaped like the RAG response
  (`answer`, `citations`, `intent="structured"`, `used_chunks`, `conflict=false`,
  `cached=false`), or `None` if it can't handle the query — in which case
  [app/rag.py](../app/rag.py) falls through to the normal RAG pipeline.

Query shapes:

| Operation | Behavior |
| --- | --- |
| `count` | paginates matching items across bundles → "There are N … matching your query." |
| `list` | enumerates up to `limit` items (sorted most-recently-changed), optional author filter |
| `lookup` | a single item (list with limit 1) |

Filters map to JSON:API conditions: `title_contains` → `CONTAINS` on `title`; `year`
→ a `created` date range; `status=1` (published) is always applied. Config:
`drupal_jsonapi_base`, `drupal_page_size`, `drupal_request_timeout`, `drupal_max_retries`.
