# Retrieval

The query-time pipeline: **understand → search → rerank → build context → cite**,
plus the structured (non-RAG) path. Orchestrated by `retrieve()` in
[app/retrieval/retriever.py](../app/retrieval/retriever.py), called from the query
pipeline in [app/pipeline/query_pipeline.py](../app/pipeline/query_pipeline.py).

## 1. Query understanding — [app/retrieval/query_processor.py](../app/retrieval/query_processor.py)

`process(question, history=None) -> ProcessedQuery`

A structured-output LLM call produces a **multi-label** `QueryUnderstanding` — a set
of intents (each with a confidence + rationale) plus orthogonal attributes (output
format, scope). With `analysis_votes > 1` it runs N concurrent samples at exploratory
temperature and confidence is the cross-sample agreement share; at `votes = 1` it is a
single pinned-temperature call using the model's own confidence. It **fails open**: on
any error it returns the original question with `intent="qa"`. The multi-label result
is then collapsed to the single-label route the rest of the pipeline consumes. Full
taxonomy, boundaries, and rules: [intent-classification-design.md](intent-classification-design.md).

`ProcessedQuery`:

| Field | Meaning |
| --- | --- |
| `original` | unmodified user input |
| `search_query` | pronoun-resolved, standalone query for retrieval |
| `intent` | derived single-label route: `qa` \| `structured` \| `scoped_summary` \| `chitchat` |
| `answer_format` | `default` \| `list` \| `table` \| `summary` \| `detailed` \| `timeline` |
| `source_type` | `pdf` / `website` if the user was explicit, else None. Also gates the website-preference dual pull (see §6): when set, retrieval uses a single filtered pull, not the dual pull |
| `language` | two-letter code if explicit, else None |
| `filters` | Qdrant `FieldCondition`s derived from the facets above — may include a `source_type` match, a `language` match, and a `published_at` `DatetimeRange` (from `date_from`/`date_to`) |
| `needs_retrieval` | property — false only for `chitchat` |
| `is_ambiguous` | property — true when the top content intents are a near-tie |
| `analysis` | derived `QueryAnalysis` (structured slots for the Drupal router) |
| `understanding` | full multi-label `QueryUnderstanding` (intents + confidence + rationale + scope), for inspection |

The derived `intent` routes as before (see [architecture.md](architecture.md#query-lifecycle)):
`chitchat` answers directly, `structured` goes to the Drupal router, `scoped_summary`
to the summarizer, `qa` runs full RAG. The new terminal intents (`out_of_scope`,
`safety_policy`, `clarification_needed`) currently map to the non-retrieving `chitchat`
route pending dedicated handling. The multi-label `intents` and `is_ambiguous` are
exposed on the `/search` response for inspection.

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

Computes a **semantic** score (per provider), then ranks on it in priority order:
**relevance first, recency only as a tie-break.**

Candidates whose relevance sits within `rerank_relevance_tolerance` of each other are
"similarly relevant" and share a **band**; the ranking key is then:

```
(band, -recency, -authority, -relevance)      # band 0 = most relevant
```

A band starts at its leader and holds everything within the tolerance of *it* (not of
the previous candidate, so a chain of small steps cannot drift a weak candidate into
the top band). Across bands relevance always wins, however old the winner is; inside a
band the newest document leads. Two editions of the same annual report land in one band
and the newer one leads, while an older passage that actually answers the question
still outranks a newer one that merely mentions it.

This replaced a weighted blend of the *normalized* semantic score with recency and
authority. Normalizing first meant the blend separated candidates most aggressively
exactly when their scores were closest — when the relevance difference means least —
so a recency weight small enough not to overrule a better passage was also too small to
break the ties it existed for.

`table_boost` is added to a table-bearing chunk's relevance (not to a final score) when
the answer format is `table`, so it can lift a chunk a band: still a nudge, not a
filter, and inert below the tolerance.

Candidates below `rerank_score_threshold` are dropped; the top `top_n` (default
`retrieval_top_k`) are returned with `score` set to the banded relevance and the **raw**
semantic score in `semantic_score` (used downstream for the website relevance floor).
`score` is deliberately *not* monotone with the returned order — inside a band the order
is by date.

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
dual pull + segregation (§6), not by a scoring tilt. Nothing writes `source_authority`
today, so authority is a constant and cannot reorder anything; it stays as the
lowest-priority key so a corpus that starts stamping it needs no further change.

Recency is derived from `published_at`, scaled across the candidate set so that an
**undated** candidate reads as mid-set — neutral, neither leading nor trailing its band
on a fact we do not have. Note that loose PDFs carry no `published_at` at all
(`from_pdf` does not set one), so recency cannot separate them.

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
candidate set. When enabled, `retrieve()` (in
[app/retrieval/retriever.py](../app/retrieval/retriever.py)) runs
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

## Structured path — [app/retrieval/structured/answerer.py](../app/retrieval/structured/answerer.py)

For `intent == "structured"` queries (exact lookups, counts, filtered lists) that are
better answered relationally than semantically. **Answered entirely from the local
catalog** — the `documents` table in MySQL
([app/catalog/state.py](../app/catalog/state.py), read via
[app/catalog/queries.py](../app/catalog/queries.py)), which stores each ingested
document's bundle, title, url, authors, categories, and publish date. No live
website/JSON:API calls happen at query time, so `count` and `list` read the same
source and always agree. The catalog operations, filters, and rendering live in
[app/retrieval/structured/](../app/retrieval/structured/) (see
[database-tool-registry.md](database-tool-registry.md)); `answerer.py` is the thin
adapter the query pipeline calls.

- `parse_structured(question, history=None) -> StructuredQuery | None` — LLM parses the
  question into `{ operation: lookup|list|count, bundle, title_contains, author, year,
  limit }`.
- `answer_structured(question, history=None) -> dict | None` — runs the operation over
  the catalog and returns an answer dict shaped like the RAG response
  (`answer`, `citations`, `intent="structured"`, `used_chunks`, `conflict=false`,
  `cached=false`), or `None` if it can't handle the query — in which case
  [app/pipeline/query_pipeline.py](../app/pipeline/query_pipeline.py) falls through to
  the normal RAG pipeline.

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
