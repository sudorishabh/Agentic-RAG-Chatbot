## Qdrant Schema Design

### 5.1 Single collection vs multiple collections

**Use a single collection.** Reasons:

- Most queries should retrieve across PDFs _and_ articles simultaneously; one collection makes that a single search. Multiple collections force you to query each and merge — more code, harder ranking.
- `source_type` as an indexed payload field gives you the separation you’d get from collections, on demand, via a filter.
- Operationally simpler: one set of HNSW params, one snapshot, one place to optimize.

**When multiple collections _are_ justified:** hard multi-tenant isolation (a tenant’s data must be physically separable / individually deletable for compliance), or radically different vector configs per corpus. For multi-tenancy at moderate tenant counts, prefer **payload partitioning** (`tenant_id` + the `is_tenant` index, see §10.8) over a collection per tenant — Qdrant is explicitly designed for this and a collection-per-tenant explodes operationally past a few dozen tenants.

### 5.2 Collection configuration

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(url="http://qdrant:6333", api_key=QDRANT_API_KEY)

client.create_collection(
    collection_name="docs_v1",
    vectors_config={
        "dense": models.VectorParams(
            size=1024,                              # BGE-M3 dense
            distance=models.Distance.COSINE,
            # store full vectors on disk, keep HNSW graph in RAM (big collections)
            on_disk=True,
        ),
    },
    sparse_vectors_config={
        "sparse": models.SparseVectorParams(
            index=models.SparseIndexParams(on_disk=True),
        ),
    },
    hnsw_config=models.HnswConfigDiff(
        m=16,                 # graph degree; 16 is a good default, 32–64 for higher recall
        ef_construct=200,     # build-time quality
        on_disk=True,
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True,  # keep quantized vectors in RAM for fast first pass
        ),
    ),
    optimizers_config=models.OptimizersConfigDiff(default_segment_number=4),
)
```

`docs_v1` is referenced through an **alias** `docs_current` so you can re-index into `docs_v2` and flip atomically (see §2.7).

### 5.3 Payload indexes (required for fast filtering)

Qdrant only filters efficiently on **indexed** payload fields. Create these:

```python
for field, schema in [
    ("source_type", models.PayloadSchemaType.KEYWORD),
    ("tenant_id",   models.PayloadSchemaType.KEYWORD),   # see is_tenant note in §10.8
    ("categories",  models.PayloadSchemaType.KEYWORD),
    ("tags",        models.PayloadSchemaType.KEYWORD),
    ("language",    models.PayloadSchemaType.KEYWORD),
    ("acl",         models.PayloadSchemaType.KEYWORD),
    ("document_id", models.PayloadSchemaType.KEYWORD),
    ("is_current",  models.PayloadSchemaType.BOOL),
    ("is_parent",   models.PayloadSchemaType.BOOL),
    ("doc_version", models.PayloadSchemaType.INTEGER),
    ("published_at",models.PayloadSchemaType.DATETIME),
]:
    client.create_payload_index("docs_v1", field_name=field, field_schema=schema)
```

### 5.4 Filtering strategy

Qdrant applies filters **during** the HNSW search (filterable vector search), so you don’t lose recall the way naive post-filtering does. Standard query filter:

```python
base_filter = models.Filter(
    must=[
        models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id)),
        models.FieldCondition(key="is_current", match=models.MatchValue(value=True)),
        models.FieldCondition(key="is_parent", match=models.MatchValue(value=False)),  # search children only
        models.FieldCondition(key="acl", match=models.MatchAny(any=user_groups)),       # RBAC
    ],
    # query-derived optional filters appended here (categories, language, date range...)
)
```

### 5.5 Hybrid search setup

Use Qdrant’s **Query API with prefetch + fusion** to run dense and sparse in one request and fuse with RRF server-side:

```python
results = client.query_points(
    collection_name="docs_current",
    prefetch=[
        models.Prefetch(query=dense_vec,  using="dense",  limit=40, filter=base_filter),
        models.Prefetch(query=sparse_vec, using="sparse", limit=40, filter=base_filter),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),  # reciprocal rank fusion
    limit=40,            # fused candidates to hand to the reranker
    with_payload=True,
).points
```

This gives you semantic recall (dense) + exact-term/keyword precision (sparse/BM25) in a single call, fused and filtered — the backbone of §6.

---

## 6. Retrieval Pipeline

```
User Query
   │
   ▼
[1] Query understanding ── rewrite, expand, extract hard filters, detect intent
   │
   ▼
[2] Metadata filter build ── tenant + ACL + is_current + query-derived facets
   │
   ▼
[3] Hybrid search (Qdrant) ── dense + sparse, RRF-fused, filtered  → ~40 candidates
   │
   ▼
[4] Rerank (cross-encoder) ── score each candidate vs query  → keep top 5–8
   │
   ▼
[5] Context selection ── parent-expand, dedup, conflict-flag, fit to budget
   │
   ▼
[6] LLM generation ── grounded answer + inline citation markers
   │
   ▼
[7] Citation assembly ── build structured sources from chunk payloads → response
```

### 6.1 Query understanding (step 1)

- **Rewrite/expand:** resolve pronouns from chat history (“it”, “that policy”), and optionally generate 1–3 paraphrases or a HyDE-style hypothetical answer to widen recall. Keep this cheap (small/fast model) — it’s on the hot path.
- **Filter extraction:** lightweight — pull obvious facets from the query (“2024”, “policy”, a category name) into structured filters. Be conservative; over-filtering kills recall. When unsure, don’t filter.
- **Intent routing:** classify whether this is (a) semantic Q&A → full pipeline, (b) a structured/aggregate question (“how many articles did Jane publish in 2023?”) → route to MySQL (see §7), or (c) chit-chat → answer directly, skip retrieval.

### 6.2 Top-K values (steps 3–4)

- **Retrieve wide, rerank narrow.** Pull **K ≈ 30–50** candidates from hybrid search (each leg fetches ~40, fused to ~40). Vector search has imperfect precision; the reranker needs enough candidates to find the gems.
- **Rerank down to N ≈ 5–8** chunks for the LLM. More than ~8 rarely helps and often hurts (the “lost in the middle” effect — models under-attend to the middle of long contexts) while costing tokens and latency.
- These are starting points — **tune K and N on your eval set** (§10.5).

### 6.3 Reranking (step 4)

A cross-encoder reads (query, chunk) _together_ and scores true relevance — far more accurate than the bi-encoder similarity used for first-stage retrieval. This is usually the second-biggest quality lever after chunking.

- **Self-hosted:** **BGE-reranker-v2-m3** (multilingual, pairs naturally with BGE-M3, runs on the same GPU).
- **Managed:** **Cohere Rerank 3.5** or **Voyage rerank-2** — excellent quality, no infra.

```python
pairs = [(query, p.payload["chunk_text"]) for p in candidates]
scores = reranker.compute_score(pairs)            # cross-encoder
ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
top = [c for c, s in ranked if s >= SCORE_THRESHOLD][:N]   # drop weak hits entirely
```

Apply a **score threshold**: if nothing clears it, return “I don’t have information on that” rather than forcing weak context into the LLM. This is a primary hallucination guard (§10.6).

### 6.4 Context selection & window optimization (step 5)

1. **Parent-expand:** replace each winning child chunk with its parent (full section) for richer context.
2. **Deduplicate:** if several children resolve to the same parent, include it once. If a PDF and its linked article cover the same material, keep the higher-ranked one and note the alternate as a secondary citation (§9).
3. **Order:** put the strongest chunks first _and_ last (mitigates lost-in-the-middle).
4. **Budget:** cap total context (e.g., ~6–10k tokens of retrieved material) regardless of model max — more context = more cost, more latency, and diluted attention, not automatically better answers.
5. **Attach citation IDs:** label each context block (`[1]`, `[2]`, …) so the LLM can cite by marker and you can map markers back to payloads.

### 6.5 Generation (step 6)

System-prompt contract (see §10.6 for the full version): _answer only from the provided context; cite the block number for every claim; if the context doesn’t contain the answer, say so._ Stream tokens to the UI.

### 6.6 How many chunks to the LLM

**5–8 parent chunks** after reranking, within the ~6–10k-token context budget. Start at 5, raise only if eval shows recall misses. Quality comes from _reranking precision_, not from stuffing the window.

---

## 7. Database (MySQL) Context Strategy

Since most content originates in Puddle, be deliberate about what gets embedded vs queried.

### 7.1 Should DB records be embedded directly?

**Embed the unstructured text fields** (article body, paragraphs, titles, descriptions) — that’s what users ask about in natural language. **Do not embed structured/relational fields** (ids, dates, author FKs, category ids, counts) — embedding a date or an author id is meaningless and pollutes retrieval. Those stay in MySQL for exact filtering and aggregation.

### 7.2 Should articles be stored as chunks in Qdrant?

**Yes.** Article bodies are chunked and embedded exactly like PDFs (§3), sharing the collection and embedding model, so a single query retrieves across both. The CMS article URL rides along as `source_url` for citation.

### 7.3 Should structured fields stay in MySQL?

**Yes — MySQL is the system of record** for all relational/structured data and the full original text. Qdrant holds chunk text + a _denormalized subset_ of metadata for filtering/citation. This split lets each store do what it’s good at: Qdrant for semantic similarity, MySQL for exact/relational/aggregate queries and as the durable source of truth.

### 7.4 When should the chatbot query MySQL directly vs Qdrant?

Route by **intent** (from §6.1):

| Query shape                          | Route                                                        | Example                                                           |
| ------------------------------------ | ------------------------------------------------------------ | ----------------------------------------------------------------- |
| Semantic / “what does X say about Y” | **Qdrant** (full RAG)                                        | “What’s our data-retention policy for disputes?”                  |
| Exact lookup by structured field     | **MySQL**                                                    | “Show the article titled ‘Q4 Earnings’.”                          |
| Aggregate / count / filter / sort    | **MySQL**                                                    | “How many policy PDFs were published in 2024?”                    |
| Filter + semantic (hybrid)           | **Qdrant with payload filters** (facets mirrored from MySQL) | “What do our _2024 policy_ docs say about retention?”             |
| Relational / multi-hop               | **MySQL then Qdrant**                                        | “Find articles by Jane, then summarize what they say about GDPR.” |

Implement the structured path either via **predefined parameterized queries** keyed to detected intents (safer, recommended) or a guarded **text-to-SQL** layer (more flexible, must be sandboxed: read-only DB user, allow-listed tables/columns, statement timeouts, never interpolate raw LLM output into SQL — use parameters). Start with parameterized queries; add text-to-SQL only if the question space genuinely demands it.

### 7.5 How relational data should be represented

- **Keep relations in MySQL** (articles↔︎categories↔︎tags↔︎authors↔︎pdfs join tables). Don’t try to model joins inside Qdrant.
- **Denormalize the _display/filter_ slice into the payload** (`categories`, `tags`, `authors` as arrays) so common filters need no DB join at query time.
- For multi-hop relational questions, resolve the relation in MySQL first (get the set of `document_id`s / `article_id`s), then either fetch their text or pass them as a Qdrant filter (`document_id IN [...]`) for a semantic pass within that set.
- Mirror the **70–80% PDF↔︎article links** as `linked_pdf_id` / `linked_article_id` in both MySQL and the payload — this powers dedup (§9).

### 7.6 Recommended architecture (summary)

> **MySQL** = durable source of truth + structured/relational/aggregate queries.
> **Qdrant** = semantic retrieval over chunked unstructured text + denormalized filter/citation metadata.
> **Object storage** = PDF binaries.
> An **intent router** sends each query to the right store (or both). Facets used for filtering are mirrored from MySQL into the payload so the hot path rarely needs a join.

---

## 8. Citations and Source Links

This is the feature that makes an enterprise RAG trustworthy. **The golden rule: citations are built from retrieved-chunk payloads in code, never generated by the LLM.** The LLM only emits markers (`[1]`, `[2]`); your code maps each marker to the real metadata. This eliminates fabricated URLs/pages.

### 8.1 What to store at ingest (so citations are possible)

Everything needed is already in the payload (§1.5): `title`, `source_type`, `source_url` (articles), `pdf_path` + `page_number`/`page_range` + `section_heading` (PDFs), `document_id`, `article_id`/`pdf_id`. If it’s not captured at ingest, you can’t cite it later — so capture page numbers and headings during parsing, non-negotiably.

### 8.2 How to produce each citation type

- **Website article URL:** read `source_url` from the payload → link directly.
- **PDF reference:** read `title` + `pdf_path`. Serve the binary from object storage via a signed URL, ideally deep-linked to the page: `https://yourapp/viewer?doc=<pdf_id>#page=<page_number>`.
- **Page numbers:** read `page_number` / `page_range` (preserved at parse time).
- **Section names:** read `section_heading`.

### 8.3 Producing and rendering citations

The LLM is prompted to put a marker after each claim. Your code does the rest:

```python
def build_citations(context_blocks):
    citations = []
    for i, blk in enumerate(context_blocks, start=1):
        p = blk.payload
        if p["source_type"] == "article":
            citations.append({
                "n": i, "type": "article",
                "title": p["title"], "url": p["source_url"],
                "section": p.get("section_heading"),
            })
        else:  # pdf
            citations.append({
                "n": i, "type": "pdf",
                "title": p["title"],
                "page": p.get("page_number"),
                "section": p.get("section_heading"),
                "link": f"/viewer?doc={p['pdf_id']}#page={p.get('page_number')}",
            })
    return citations
```

Return both the answer (with `[n]` markers) and this structured list so the frontend can render footnotes/cards and the markers stay clickable. Your desired output falls straight out:

```
Answer: Customer records must be retained for at least seven years [1], and
records under active dispute are held until resolution [2].

Source 1:
  Article: Data Retention Overview
  URL: https://example.com/data-retention

Source 2:
  PDF: Corporate Policy Guide 2024
  Page: 42
  Section: 4.2 Data Retention Requirements
```

### 8.4 Merging citations across web articles and PDFs

Because both source types share one payload schema, merging is uniform: collect the payloads of the chunks actually used, build one numbered list, and let each entry render per its `source_type`. If two sources support the _same_ claim, cite both under one claim (`[1][2]`). De-duplicate identical sources (same `document_id` + page) so the list stays clean. Optionally group by source type in the UI (“Articles” / “Documents”) while keeping a single global numbering.

### 8.5 Guarantee correctness

- Only include sources for chunks **actually sent** to the LLM (don’t list the whole candidate set).
- Validate every marker the LLM emits maps to a real block; drop or flag stray markers.
- For high-stakes domains, optionally run a verification pass: check each cited claim is entailed by its cited chunk (an NLI model or a cheap LLM call) before showing it.

---

## 9. Handling Mixed Sources (PDF + Article overlap)

Your 70–80% overlap makes this central, not an edge case.

### 9.1 Info exists in both a PDF and an article

Often the _same_ content (the article is the web version of the PDF). Strategy:

1. **Detect the relationship** via `linked_pdf_id`/`linked_article_id` (from the CMS links) and/or near-duplicate text detection (high cosine between chunks, or MinHash/SimHash on chunk text).
2. **Pick a canonical source per duplicate cluster.** A sensible default policy: prefer the **PDF** when the question is about the authoritative/official document (policies, manuals) and prefer the **article** when recency or a shareable web link matters. Make this a config knob.
3. Send the canonical chunk to the LLM, but **keep the alternate as a secondary citation** (“also available as: …”) so the user gets both the web link and the PDF page.

### 9.2 Duplicated content across sources

Deduplicate at **two stages**:

- **Ingest-time (coarse):** cluster near-identical documents via content hash + fuzzy match; record cluster membership so you don’t index 5 copies of the same memo as 5 independent docs.
- **Query-time (fine):** after rerank, drop chunks whose text is ≥ ~0.9 cosine similar to an already-selected chunk, keeping the higher-ranked one. This stops the context window filling with paraphrases of one fact and stops citation lists from repeating the same source.

```python
def dedup(ranked, sim_threshold=0.9):
    kept = []
    for cand in ranked:                      # already in rerank order
        if all(cosine(cand.dense, k.dense) < sim_threshold for k in kept):
            kept.append(cand)
    return kept
```

### 9.3 Conflicting information between PDF and article

The dangerous case (e.g., an outdated web article contradicts the current PDF). Handle it explicitly:

1. **Detect:** when two top chunks are topically aligned (high similarity / same `linked_*` cluster) but the LLM-or-an-NLI-check finds contradiction.
2. **Resolve by precedence,** in this order: **recency** (`published_at` / `doc_version` — newest wins), then **authority** (official PDF > web article, or a per-category trust ranking you define), then **explicit surfacing**.
3. **Surface, don’t silently pick.** Best practice for enterprise: have the LLM **present the discrepancy and cite both**, leaning on the more authoritative/recent one: _“The 2024 Policy Guide states seven years [1]; an older article states five years [2]. The current policy is seven years.”_ Silent suppression erodes trust and hides real source problems.
4. **Feed signals into the prompt:** pass `published_at`, `doc_version`, and a `source_authority` score with each context block so the LLM can reason about precedence rather than guess.

### 9.4 Ranking strategy for mixed sources

Blend, in the reranker/selection stage: **semantic relevance** (rerank score, dominant) → **recency** (boost newer) → **authority** (boost official sources / higher-trust categories) → **diversity** (the dedup pass). A simple weighted score works well; keep semantic relevance the dominant term and treat recency/authority as tie-breakers and conflict-resolvers.

---

## 10. Production Considerations

### 10.1 Scalability for millions of chunks

- **Qdrant scales horizontally** via sharding + replication. Start single-node (20 GB of PDFs fits comfortably on one well-provisioned node), enable replication for HA, shard when a single node’s RAM/QPS is the bottleneck.
- **RAM is the constraint, not disk.** The HNSW graph and (optionally) quantized vectors live in RAM. Use **on-disk full vectors + INT8 scalar quantization in RAM** (§5.2): the quantized first pass stays fast and small, full vectors are fetched from disk only for rescoring. For tens of millions of vectors, consider **binary quantization** (huge memory savings, with rescoring to recover accuracy).
- **Batch ingestion** (upsert in batches of 64–256) and run embedding on GPU; ingestion, not query, is where you’ll feel scale during the initial 20 GB backfill.

### 10.2 Qdrant optimization checklist

- INT8 (or binary) quantization with `always_ram=True`; full vectors `on_disk=True`.
- Payload indexes on every filtered field (§5.3) — unindexed filters are slow.
- Tune `hnsw_config.m` (16→32 for higher recall) and search-time `ef` (`hnsw_ef` / `params.exact=False`) per your latency/recall target.
- `default_segment_number` ≈ number of CPU cores for parallel search.
- For multi-tenant, set the `is_tenant=true` index on `tenant_id` so segments are physically grouped by tenant (faster filtered search).
- Snapshot regularly for backup; use aliases for zero-downtime re-index (§2.7).

### 10.3 Caching strategy (Redis)

- **Semantic query cache:** embed the query, check Qdrant/Redis for a past query within ~0.95–0.97 cosine; if hit and underlying docs unchanged, return the cached answer+citations. Big latency/cost win for FAQ-style traffic. Invalidate on document updates touching those sources.
- **Embedding cache:** cache embeddings keyed by `content_hash` so re-ingesting unchanged chunks (and repeated queries) skips the model.
- **Retrieval cache:** cache (filtered query → candidate IDs) for short TTLs.
- **LLM response cache:** exact-match cache for identical (query, context) pairs.
- Cache citations _with_ the answer so cached responses stay fully sourced.

### 10.4 Monitoring & observability

- **System metrics:** end-to-end + per-stage latency (rewrite, search, rerank, LLM), QPS, error rates, token usage/cost, Qdrant RAM/segment health, queue depth/ingestion lag.
- **RAG quality metrics (logged per query):** retrieval hit (did a relevant chunk make the cut), rerank score distribution, number of chunks used, % answers with citations, % “I don’t know” responses, conflict-detected rate.
- **Tracing:** instrument the pipeline (OpenTelemetry / Langfuse / Phoenix) so you can replay any query and see exactly which chunks were retrieved, reranked, and cited.
- **Feedback loop:** capture thumbs up/down + which citations users click → a labeled set for evaluation and tuning.

### 10.5 Evaluation metrics

Maintain a **golden eval set** (representative questions + known-good answers + the chunks that should be retrieved). Measure:

- **Retrieval:** Recall@K, Precision@K, MRR, nDCG (did we fetch the right chunks?).
- **Generation (RAGAS-style):** **faithfulness/groundedness** (is every claim supported by retrieved context?), **answer relevancy**, **context precision/recall**, **citation accuracy** (do cited sources actually support the claim?).
- **End-to-end:** human/LLM-judge correctness on the golden set.
- Run the eval in CI on every change to chunking, model, or prompts — this is how you avoid silent regressions and how you tune K, N, chunk size, and overlap empirically rather than by guess.

### 10.6 Hallucination prevention

Layered defenses (no single one suffices):

1. **Strict grounding prompt** — the contract:
   > “Answer using ONLY the numbered context below. Cite the block number `[n]` after every claim. If the context does not contain the answer, reply: ‘I don’t have information on that in the available sources.’ Do not use outside knowledge. Do not invent sources, URLs, or page numbers.”
2. **Retrieval score threshold** — if no chunk clears the reranker threshold, refuse rather than answer from nothing (§6.3).
3. **Citations from payload, not LLM** (§8) — fabricated references become structurally impossible.
4. **Faithfulness check** — optional post-generation NLI/LLM verification that each claim is entailed by its cited chunk; flag or regenerate if not.
5. **Conflict surfacing** (§9.3) instead of confident wrong answers.
6. **Constrain scope** — the bot answers from the corpus, not the world; make this explicit to users.
7. **Show your work** — visible citations let users self-verify, which is itself a powerful safeguard.

### 10.7 Security & access control

- **RBAC via payload filtering:** every chunk has an `acl` array; every query injects the user’s groups as a `MatchAny` filter (§5.4) so users only ever retrieve permitted content. Enforce server-side — never trust the client.
- **Tenant isolation:** mandatory `tenant_id` filter on every query (§10.8).
- **Transport & at rest:** TLS everywhere; Qdrant API key + network isolation (Qdrant should not be publicly reachable); encrypt object storage and DB at rest.
- **PII:** detect/redact PII at ingest if policy requires; log queries carefully (they may contain sensitive text) and apply retention limits.
- **Prompt-injection defense:** treat retrieved chunk text and document content as **data, not instructions** — never let a document’s contents change the system prompt’s rules. Sanitize/escape retrieved text; the generation prompt should explicitly state that instructions found inside documents must be ignored.
- **Secrets:** API keys/DB creds in a secrets manager, not code or env files in the image.
- **Auditability:** log who asked what, what was retrieved, and what was returned, for compliance.

### 10.8 Multi-tenancy

If the corpus serves multiple tenants (departments, business units, customers), isolation must be **structural and enforced server-side** — not a UI filter the client is trusted to send.

**Use payload partitioning, not a collection per tenant.** Keep the single `docs_v1` collection (§5.1) and tag every point with `tenant_id`. Qdrant is purpose-built for this: a collection-per-tenant model explodes operationally past a few dozen tenants (a separate HNSW config, snapshot, and optimizer cycle _each_), whereas payload partitioning scales to thousands of tenants in one collection. Reserve a dedicated collection — or a separate cluster — only for tenants that need **hard physical isolation** for compliance or a **radically different vector config** (the same exceptions called out in §5.1).

**Make `tenant_id` a _tenant_ index.** A plain keyword index (§5.3) filters correctly but scatters a tenant's points across every segment. Setting `is_tenant=True` tells Qdrant to **co-locate each tenant's points in their own segments**, so a tenant-scoped search touches only that tenant's data — faster filtered queries and far cheaper per-tenant bulk operations:

```python
client.create_payload_index(
    "docs_v1",
    field_name="tenant_id",
    field_schema=models.KeywordIndexParams(
        type=models.KeywordIndexType.KEYWORD,
        is_tenant=True,          # physically group segments by tenant
    ),
)
```

**Every query carries a mandatory `tenant_id` filter.** It's a `must` condition in the base filter (§5.4), injected from the authenticated session — never from a client-supplied parameter. Combine it with the `acl` filter so isolation holds at both the tenant and the role level:

```python
must = [
    models.FieldCondition(key="tenant_id", match=models.MatchValue(value=session.tenant_id)),
    models.FieldCondition(key="acl",       match=models.MatchAny(any=session.groups)),   # RBAC, §5.4
    # ... is_current / is_parent / query-derived facets
]
```

**Fail closed.** If a request reaches retrieval without a resolved tenant context, **refuse** — never fall back to an unfiltered search. A missing `tenant_id` filter is a data-leak bug, not a degraded-results bug. Build the filter in one shared helper so no code path can construct a tenant-less query.

**Per-tenant lifecycle.** Because each tenant is a payload partition, offboarding and compliance ("right to erasure") deletes are a single filtered delete — and the `is_tenant` index keeps it cheap because the points are already segment-local:

```python
client.delete(
    collection_name="docs_current",
    points_selector=models.FilterSelector(
        filter=models.Filter(must=[
            models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id)),
        ]),
    ),
)
```

**Isolation is only as strong as its weakest store.** Carry the same tenant scoping everywhere: MySQL rows (§7) filtered by `tenant_id`, object-storage paths namespaced per tenant, and every Redis cache key (§10.3) prefixed with `tenant_id` so one tenant can never be served another's cached answer or embedding.

**When to escalate.** Promote a tenant to a dedicated collection/cluster when it needs legally mandated physical separation, its own encryption keys, or a custom vector config; **shard** (§10.1) when aggregate volume — or a single large tenant — outgrows one node. `is_tenant` partitioning and sharding compose cleanly, so this is a capacity decision, not a redesign.
