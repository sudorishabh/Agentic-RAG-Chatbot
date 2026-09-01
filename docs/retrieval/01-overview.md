# 01 — Read Path Overview

## What the read path does

It turns a question into a cited, grounded answer.

Concretely: it decides what the question actually means and how to filter for
it, checks whether the answer is already cached, tries the routes that can
answer exactly (chit-chat, a catalog fact, a knowledge-graph relationship, a
scoped summary) before falling back to retrieval, pulls and ranks candidate
passages from Qdrant when it does fall back, assembles the passages the model
is allowed to see, generates an answer, checks that answer against its own
evidence, and streams the result back with citations. It runs once per
request, in-process, with no queue and no state carried between questions
except the conversation history the caller sends.

## Why it exists

Ingestion (`docs/ingestion/`) is the only path that writes the corpus. The read
path is the only path that reads it back as an answer rather than as rows. Every
retrieval defect a user notices — a wrong citation, an unfounded date, a
refusal where an answer existed — is downstream of a decision made here, on a
corpus that is otherwise already correct.

Three properties drove most of the design:

1. **A question is ambiguous until it is understood.** The same words can be
   chit-chat, a request for one document's content, a request for a catalog
   fact ("how many..."), a comparison, or "summarize everything about X" — and
   the corpus uses inconsistent surface forms for the same entities. So
   understanding runs exactly once per question (`app/retrieval/understanding/`)
   and every later stage acts on that one decision — an `intent`, a rewritten
   `search_query`, and a set of filters — rather than re-deriving it.
2. **Some questions are arithmetic, not similarity.** "How many policy briefs
   are there?" has an exact answer sitting in MySQL; running it as a vector
   search would return the six most similar-sounding passages instead of a
   count. So a question the catalog can answer exactly is routed to
   `app/retrieval/structured/` (and, for verified relationships,
   `app/retrieval/graph/`) instead of ever reaching embedding search.
3. **A generated answer can misstate what it was given.** The model can cite a
   number that isn't in its context, or attribute a report's own date to the
   page that merely links it — the latter survived two rounds of prompt work
   and still misdated 4 of 6 sampled answers. So a generated answer is checked
   against the blocks that grounded it before the user sees it: deterministically
   where the failure is specific and mechanical (dates), by entailment where it
   is a judgement call (faithfulness, off by default), and merely observed where
   correction risks being wrong itself (numeric claims).

## The major components

```
                              question
                                 |
                                 v
                     +-----------------------+
                     |  semantic cache lookup |----- hit ----> cached answer
                     |  app/cache/            |
                     +-----------+-----------+
                                 | miss
                                 v
                     +-----------------------+
                     |     understanding/     |   QueryAnalysis: intent,
                     |  app/retrieval/         |   search_query, filters
                     |  understanding/         |
                     +-----------+-----------+
                                 |
        chitchat --------------+--------------- scoped_summary
           |                    |                     |
           v                    | structured           v
    direct reply       +--------+--------+     app/pipeline/summarize.py
    (no retrieval)      |  structured/    |     (map-reduce over a
                        |  catalog answer |      catalog-selected scope)
                        +--------+--------+
                                 | no catalog match, or qa/comparison
                                 v
                     +-----------------------+        +----------------+
                     |       search/          |<------>|    graph/      |
                     |  fetch + fuse + rerank |        | (flag; off by  |
                     +-----------+-----------+        |  default path) |
                                 v                     +----------------+
                     +-----------------------+
                     |       context/          |   Candidate[] -> ContextBlock[]
                     |  builder + citations    |
                     +-----------+-----------+
                                 v
                     +-----------------------+
                     |      generation/        |   streamed tokens, then
                     |  answerer + verifiers   |   faithfulness / date-claim
                     +-----------+-----------+   verification
                                 v
                    citations + sources event + done
                                 |
                                 v
                  semantic cache store, retrieval trace, rag_metrics
```

| Component | Module | Role |
| --- | --- | --- |
| Query pipeline | `app/pipeline/query_pipeline.py` | The read path end to end: cache lookup → understanding → routing → search → rerank → context → generation → citations → metrics. **Start here to understand how a query is answered.** |
| Scoped summarizer | `app/pipeline/summarize.py` | Map-reduce summary over a catalog-selected document set, for "summarize X" questions the vector index cannot serve because the user named a set, not a topic. |
| Query understanding | `app/retrieval/understanding/` | The entry point's data contract: intent, rewritten query, facet filters, language, ambiguity. |
| Hybrid search | `app/retrieval/search/` | Candidate fetch across legs, reciprocal-rank fusion, reranking into authority/recency/substance bands, temporal gating. |
| Context builder | `app/retrieval/context/` | Which candidate text is admitted, in what order, with what page attribution; and how those same blocks are described back to the user as citations. |
| Structured answers | `app/retrieval/structured/` | Questions the catalog answers exactly — counts, listings, comparisons — planned and executed against MySQL, not Qdrant. |
| Knowledge graph retrieval | `app/retrieval/graph/` | Verified relationships with provenance from Neo4j. Isolated by construction: nothing on the default path imports it. |
| Generation | `app/generation/` | Prompt construction, streaming, and post-generation faithfulness / date-claim / numeric-mismatch checks. |
| Semantic cache | `app/cache/semantic_cache.py`, `app/cache/cache_keys.py` | Whole-answer cache keyed on the query vector, `top_k`, `answer_format`, a facet fingerprint and the indexed corpus revision. |
| API surface | `app/api/chat.py`, `app/api/search.py` | The SSE and buffered entry points. See [02](02-triggers-and-api.md). |
| Retrieval trace | `app/observability/retrieval_log/` | An optional, complete per-query JSON record of everything above; see `docs/retrieval-logging.md`. |

`retriever.py` (`app/retrieval/retriever.py`) is the orchestrator inside the
search/context stages: it runs understanding's output through search then
context, and consults `graph/` behind a flag. It is `query_pipeline.py` that
decides *whether* a question reaches it at all — `structured/` and
`scoped_summary` can answer and return before retrieval is ever called.

## The complete lifecycle

One question, end to end, as `app/pipeline/query_pipeline.py` runs it:

1. **Trigger.** A request arrives at `POST /chat` (streamed) or `POST /search`
   (buffered), authenticated by `require_principal`. Chat requests additionally
   queue on a dedicated capacity limiter so a burst of long generations cannot
   starve the shared request threadpool that auth checks and health probes also
   use. See [02](02-triggers-and-api.md).
2. **Understanding.** `process(question, history)` (span `rag.query_understanding`)
   returns a `ProcessedQuery`: the rewritten `search_query`, the `intent`, the
   multi-label `capabilities` set, Qdrant `filters`, `source_type`, `language`
   and `is_ambiguous`. This is traced immediately via `retrieval_log.note_query`
   — the first fact worth knowing about any query is what was actually
   understood, whatever happens next.
3. **Short-circuits, tried in this order:**
   - **`chitchat`** → a direct reply, no retrieval at all.
   - **`structured`** → first, whether the question names one document by title
     closely enough to resolve a lookup chain — if so, the question is answered
     from *that document's own chunks* (a Qdrant filter on `document_id`) rather
     than a title-and-URL answer, because "tell me about the 2023 annual report"
     wants content, not a pointer. Otherwise the catalog is asked directly
     (`answer_structured`). A structured hit still gets one more chance to be
     answered as a **graph relationship** before it is returned — measured at 4
     of 14 graph-answerable benchmark questions where the catalog said
     "'projects' matches more than one content type" and the graph held the
     rows outright, all of them the "which projects did PERSON lead" shape the
     graph's query-side resolution exists to serve.
   - **`scoped_summary`** → `summarize_scope` (`app/pipeline/summarize.py`):
     the catalog selects the document set the question named, and the model
     summarizes it hierarchically. Falls through to plain retrieval when the
     scope is empty, unresolvable, or held no summarizable text.
4. **Cache lookup.** The query is embedded exactly once (`embed_query`, span
   `rag.embed_query`) and that one vector is reused for the semantic-cache
   lookup, for retrieval, and — if nothing else has answered — for the cache
   write at the end. `semantic_cache.lookup` is keyed on the vector, `top_k`,
   `answer_format` and a facet fingerprint of the question's filters. A hit
   returns immediately, `cached: true`, and skips every stage below.
5. **Retrieval and the answer plan run together.** Three things share no data
   until each is done — requirement extraction for genuinely multi-part
   questions (`answer_plan.extract_requirements`), the deterministic catalog
   section for a *combined* database-and-content question (`_db_section`), and
   content retrieval itself (`retriever.retrieve`) — so they run in a
   two-worker thread pool and the request pays whichever is slowest, not their
   sum.
6. **Empty retrieval is not automatically a refusal.** A combined query with
   nothing from content retrieval but a catalog prefix returns that prefix
   alone. A query the catalog hasn't already been asked about gets one more
   try at a catalog *listing* — titles and facets, explicitly framed so a list
   of titles is never mistaken for the substance the user asked for. Only then
   is the fixed refusal text returned.
7. **Generation.** The admitted blocks feed `generate_stream` or
   `generate_answer` (`app/generation/answerer.py`), grounded by
   `generation/prompts.py`'s formatting and, for multi-part questions, the
   plan's `directive`. The streaming entry point (`stream_answer`) yields
   `token` events as they arrive from the model; a combined answer's catalog
   prefix is emitted first.
8. **Post-generation verification**, run against the fully assembled answer
   text:
   - **Date claims** (always on): a deterministic check that the answer never
     attributes a document's own publication date to the page that merely
     links it. One regeneration with a correction note; if that still fails, a
     mechanical rewrite replaces just the offending sentences. This is the one
     check that is never left uncorrected.
   - **Faithfulness** (`faithfulness_check`, off by default): an entailment
     check against the cited blocks. One regeneration on failure, emitted as a
     `correction` event; if the retry also fails or errors, the original
     streamed draft stands.
   - **Numeric mismatches**: computed and logged, never auto-corrected —
     observe-only, because an automatic "fix" to a number is exactly the kind
     of confident wrong answer this whole stage exists to prevent.
9. **Assembly and persistence.** The final citations cover only the blocks the
   answer actually cites (falling back to all of them if citation-marker
   extraction finds none), the semantic cache is written under the same key
   the lookup used, and the retrieval trace and the `rag_metrics` log line
   record the outcome — intent, chunk and citation counts, conflict and
   mismatch flags, latency, per-stage timing.
10. **Done.** The stream emits `sources` then `done`. The buffered `/search`
    entry point (`search_blocks`) stops after step 5 — it returns retrieved
    blocks directly, with no generation and no cache read or write, and exists
    for inspection and evaluation rather than as a second answer surface.

## Vocabulary

These terms are used precisely throughout the set.

| Term | Meaning |
| --- | --- |
| **`ProcessedQuery`** | Understanding's output: `search_query`, `intent`, `filters`, `source_type`, `language`, `is_ambiguous`, plus the raw `QueryAnalysis`/`QueryUnderstanding` it was derived from. |
| **`Candidate`** | One retrieved passage plus its score and payload, the type every module in `search/` passes around. |
| **`ContextBlock`** | One piece of admitted context as the model (and the citations) sees it — text, page span, source metadata. Lives in `app/core/models/context.py`, not in `retrieval/`, so `generation/` never imports a retrieval implementation module. |
| **Intent** | The single label the pipeline routes on: `chitchat`, `structured`, `scoped_summary`, `qa`, `comparison`, … |
| **Capabilities** | The full multi-label set understanding detected (`caps`), used to decide whether a query is *combined* (needs both a catalog fact and grounded content), not just to pick the one `intent`. |
| **Combined query** | `"database" in caps and caps & {"qa", "comparison"}` — a question needing both a deterministic catalog fact and a grounded content answer, assembled as one prefixed response. |
| **Chained** | A `structured` query resolved to a specific document by title and rerouted onto the content path via a `document_id` filter, rather than answered as a title/URL lookup. |
| **`db_consulted`** | Whether the catalog has already been asked about this question, so the empty-retrieval fallback doesn't re-ask it for a listing that would just repeat "nothing". |
| **Facet fingerprint** | A hash of a query's filters, part of the semantic cache key — two questions with the same text but different filters must not share a cached answer. |
| **Structured route** | `app/retrieval/structured/` — exact catalog arithmetic (counts, listings, comparisons) executed against MySQL. |
| **Graph route** | `app/retrieval/graph/` — verified relationships from Neo4j, reached only from inside `retriever.retrieve` and from the one `structured`-fallback described above, always behind a flag. |
| **Answer plan / directive** | `app/generation/answer_plan.py`'s extracted sub-requirements for a multi-part question, and the prompt directive derived from them; a no-op for an ordinary single-part question. |
| **Cited blocks** | The subset of retrieved `ContextBlock`s the generated answer's `[n]` markers actually reference — what the citations footer lists, not everything retrieval fetched. |

## Cross-cutting invariants

Everything in the rest of this set upholds these.

1. **Identity never scopes retrieval.** The corpus is public; every
   authenticated or anonymous caller reads all of it. The authenticated
   `Principal` exists to gate the API, not to filter results.
2. **One embedding call per query.** The same vector serves the cache lookup,
   retrieval, and the cache write — never recomputed mid-request.
3. **An alternative route is a return-or-`None` contract, not an exception
   boundary.** `structured`, the graph fallback, and `scoped_summary` each
   either produce a complete answer or hand back nothing; a failure inside one
   of them degrades to the next route rather than failing the request.
4. **A specific, mechanical falsehood is always corrected; a judgement call is
   corrected once and then accepted.** Date-claim errors are rewritten
   outright if the regeneration doesn't fix them. Faithfulness gets one
   regeneration and, on continued failure, is left as the model's best
   attempt rather than silently dropped or endlessly retried.
5. **The read path never writes the corpus.** `retrieval/`, `pipeline/` and
   `generation/` import none of `app.ingestion`; the only mutation reachable
   from this path is the semantic cache, which the ingestion side also
   invalidates by revision (see `docs/ingestion/08-persistence-and-catalog.md`).
6. **Every stage's timing is captured whether or not the trace is on.** The
   `span()` context managers feed both the in-process `rag_metrics` aggregate
   and, only when `is_retrieval_log` is set, the per-query trace — so turning
   observability off costs nothing but the trace itself.

---

Next: [02 — Triggers and the API Surface](02-triggers-and-api.md)
