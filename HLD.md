# High-Level Design — TERI Agentic RAG Chatbot

**Revision** `e7b7066` · 2026-08-24
**Detail** [ARCHITECTURE.md](ARCHITECTURE.md) — field-level reference · [end-to-end-flow.pdf](end-to-end-flow.pdf) — one-page diagram

---

## 1. What it is

A question-answering service over TERI's published content. It crawls the
organisation's Drupal site, ingests page text and the PDFs those pages carry, and
answers questions with citations.

**The rule the whole design serves: the model narrates, it never supplies facts.**
Counts come from SQL, relationships from a verified graph, quotes from stored
text, citations from stored metadata. The LLM classifies, rewrites and writes prose.

Three question shapes, three answering strategies:

| Shape | Example | Answered from |
| --- | --- | --- |
| Content | "what did the report say about emissions?" | Qdrant — passage search |
| Catalogue | "how many research papers in 2024?" | MySQL — relational query |
| Relational | "which projects did X lead?" | Neo4j — entity/claim traversal |

---

## 2. Context

```
   user (web widget) ──HTTPS/SSE──┐         ┌──── operator (CLI, ~25 scripts)
                                  ▼         ▼
                    ┌──────────────────────────────────┐
                    │  retrieval server │ ingest server│
                    │  (public, read)   │ (private,    │
                    │                   │  write+sweep)│
                    └───┬──────┬──────┬──────┬─────────┘
                        ▼      ▼      ▼      ▼
                     MySQL  Qdrant  Neo4j  Azure OpenAI / Doc Intelligence
                                              ▲
                                     teriin.org Drupal (crawled, never written)
```

| External | Role | If lost |
| --- | --- | --- |
| MySQL | system of record | ingestion refuses to start |
| Qdrant | passages + answer cache | **no content answers** — no fallback |
| Neo4j | relational surface | graph declines; rest unaffected |
| Azure OpenAI | chat + embeddings | per-call fail-open; embeddings retry with throttle backoff |
| Azure Doc Intelligence | OCR for scanned pages | pages degrade to local text |
| Redis | optional | nothing load-bearing |

---

## 3. Containers

| Container | Exposes | Notes |
| --- | --- | --- |
| **Retrieval server** | `/chat` (SSE), `/search`, `/health`, `/ready`, `/metrics` | public; read-only on content; writes only the answer cache |
| **Ingestion server** | `/ingest/run`, `/ingest/article`, `/reindex`, `/ingest/log` | private + authenticated; hosts the scheduled sweep; MySQL is a readiness requirement |
| **Operator CLIs** | migrations · knowledge builders · evaluation harness | ~25 scripts |

---

## 4. Stores and ownership

```
        MySQL ──────────► system of record
          │               catalogue · crawl state · entities · claims
          ├────► Qdrant   derived — passages, vectors, answer cache
          └────► Neo4j    derived — entities, claims, current-state edges
```

Both derived stores are **rebuildable from MySQL**, which is why an outage in
either is a lag rather than a loss. Qdrant is the only place chunk text lives;
Neo4j holds identifiers and structure, never text. The cross-store key is
`chunk_id`.

Scale: ~15,400 documents · ~3,800 PDFs · ~149,000 vector points · 15 content types.

---

## 5. Write path — the sweep

One corpus-wide run at a time, process-locked.

| # | Step | Key property |
| --- | --- | --- |
| 1 | Crawl | oldest-first, unique tie-break; window floored at the earliest unresolved failure |
| 2 | Detect change | fingerprint match → **stop, free**; most of the corpus, most runs |
| 3 | Extract | page HTML → text; PDF routed *per page* — text / tables / OCR |
| 4 | Resolve date | page date is default **and** fallback; override needs 10 gates |
| 5 | Check content | body-hash match → catalogue only, no re-embed; pipeline-version move → rebuild anyway |
| 6 | Chunk | parent/child; ids from **owned content**, not version or position |
| 7 | Embed | children only (parents are zero-vectors); breadcrumb prefix; unchanged vectors reused |
| 8 | Index | **upsert new, then delete old** — never absent mid-swap |
| 9 | Persist | catalogue + facet + link rows in one transaction |
| 10 | Knowledge | mentions → identity → claims → conflicts → graph *(gated off)* |

**After every sweep, unable to fail it:** knowledge catch-up (bounded) → whole-graph
projection → cross-store reconciliation, which checks ten invariants and
**reports without repairing**.

Two mechanisms worth naming:

- **Pipeline versioning** — content-based change detection meant *code* changes
  never reached the corpus. Chunking, chunk identity, payload and embed-input each
  carry a version; a document whose stamp differs is rebuilt even if byte-identical.
- **Reconciliation** — MySQL vs Qdrant vs Neo4j, read-only. A reconciler that
  acted on its findings would be a second unsupervised write path whose failure
  mode is data loss.

---

## 6. Read path — per request

| # | Step | Key property |
| --- | --- | --- |
| 11 | Understand | one structured call → intents, rewrite, facets, format; **fails open** to a plain question |
| 12 | Route | chitchat · catalogue · scoped summary · content |
| 13 | Cache | near-verbatim question **and** identical facets; self-invalidating on corpus/tuning change |
| 14 | Search | up to 6 legs in parallel, fused by reciprocal rank |
| 15 | Rerank | **relevance band → completeness → recency → authority**; nothing escapes its band |
| 16 | Build context | parent-expand · dedup · token budget · order; graph facts lead, prose keeps reserved slots; stale events dropped for "upcoming" |
| 17 | Generate | prompt chosen by what the context holds; streamed |
| 18 | Verify | markers always · numeric flag always · date-claim guard · entailment optional |
| 19 | Cite | assembled from payloads; only blocks the answer used |

**Six search legs:** graph (relational) · dense pull · website / not-website split ·
title-anchored · lexical (acronyms, years, names) · paraphrases. Wall-clock is the
slowest leg, not the sum.

Two legs exist for measured failures: the **title leg** because canonical hub
pages read as link labels and embed nowhere near the questions they answer; the
**answer plan** because a multi-part question ("mission and vision") was being
answered only in its first part from a page covering both.

---

## 7. Knowledge layer *(built, gated off)*

```
CMS records ─► seed ─► canonical entities, aliases, identifiers
chunk text  ─► extract ─► mentions ─► resolve ─► claims ─► conflicts ─► graph
```

| Stage | Design |
| --- | --- |
| Extract | 5 methods, cheapest-surest first (CMS field → identifier → gazetteer → pattern → LLM). **Every span verified against the chunk text**; no stage assigns identity |
| Resolve | 5 tiers; outcomes `AUTO` / `PROVISIONAL` / `AMBIGUOUS` / `UNRESOLVED`. **A false merge is worse than an unresolved mention** — every threshold fails toward abstention |
| Claims | 7 closed predicates with enforced domain/range. Identity = what the source states, never how it was read, so re-extraction updates rather than forks |
| Conflicts | mechanical, not heuristic: for a *functional* predicate, two active overlapping claims are a contradiction by definition. Nothing is deleted |
| Project | only `stated` / `subject_period` validity earns a current-state edge |

Four stages are inherently **global** (seed, acronyms, ambiguity, PI promotion) and
absent from the per-document path. Consequence accepted and recorded: a newly
ingested project has no canonical identity until the next corpus build, and its
claims are refused as `unknown_subject` rather than guessed.

---

## 8. Graph retrieval *(built, empty until the knowledge layer runs)*

```
question → policy gate → router → reviewed template → Neo4j → ids
                                                                │
                                          Qdrant hydrate → rerank → context
```

**Safety** — four independent controls, all applying to every route:
closed predicate vocabulary · reviewed Cypher template registry (callers pass a
`template_id` + typed parameters, **never a query**) · parameter validation ·
scope check that declines rather than silently dropping a constraint. Labels and
relationship types are code constants, because Cypher cannot parameterise them.

**Availability** — cannot make `/chat` unavailable: 3 s budget on a worker thread,
every exception caught, empty result means "fall back", plus a circuit breaker
(3 failures → 60 s skip) because falling back keeps the endpoint *available* while
still taxing every relational query during an outage. Eleven outcomes counted
separately — **zero results and failure are different things**, and merging them
would let Neo4j degrade silently behind a working fallback.

---

## 9. Design rules

1. **Cheap checks first** — fingerprint before download, hash before embedding,
   rules before a model call. The date resolver settles 92% free; the whole
   corpus cost $0.09.
2. **The model narrates, never supplies facts.**
3. **Closed vocabularies at every model boundary** — entity types, predicates,
   templates, intents. A model may select from a list, never extend one.
4. **Verify model output against source text** — spans must exist at their stated
   offsets; a proposed date must appear in the document, *and* so must the
   statement said to establish it.
5. **Abstain rather than guess** — a false merge, a wrong date and a silently
   chosen ambiguity are each worse than no answer.
6. **Write the new thing before removing the old.**
7. **Deletion requires positive evidence** — reconciliation refuses an
   implausible enumeration; claims are retracted, never deleted.
8. **Derived stores are rebuildable.**
9. **Every cached model-derived value carries a fingerprint of the prompt that
   produced it**, so editing a prompt invalidates it.
10. **Failures stay visible** — retry markers floor the crawl window; a knowledge
    run row is written last so its absence means "did not finish".

---

## 10. Failure model

Everything degrades to the behaviour that preceded the feature, with one log line.

| Isolation guarantee | How |
| --- | --- |
| One ingestion run at a time | process lock; concurrent trigger → HTTP 409 |
| Knowledge cannot break ingestion | runs after commit; return value ignored; delete code not reachable from it |
| Graph cannot break retrieval | budget · breaker · caught exceptions · empty fallback |
| Chat load cannot starve the server | `/chat` on a dedicated capacity limiter |

**Recorded failures that come back:** retry markers (the crawl cursor advanced past
failures that left no trace) · dead-link markers (broken PDFs were refetched
forever) · knowledge run rows · stranded-document recovery · pipeline version.

**Consistency** is eventual, with an explicit hierarchy: MySQL immediate, Qdrant
per-document-swap, Neo4j at most one sweep behind. Reconciliation makes any
divergence visible; the projection carries a timestamp so "stopped projecting" is
distinguishable from "agrees".

---

## 11. Security

**The corpus is public.** Tenant and ACL filtering were removed from retrieval and
from payloads — which removes a class of filter-bypass risk and also means there
is **no document-level access control**.

| Vector | Control |
| --- | --- |
| Prompt injection via corpus text | grounding rule: context is reference, never instructions |
| Fabricated citations | model emits only `[n]`; out-of-range stripped; citations from payloads |
| Cypher injection | template registry; labels/types are code constants; read-only sessions |
| SQL injection | parameterised; table names pass an allow-list guard |
| DOM XSS | full markdown source escaped, quotes included, before any HTML is built |
| Fabricated relationships | closed vocabulary with enforced domain/range |
| Fabricated dates | 10 resolution gates + a post-generation guard (§13) |

| Surface | Control |
| --- | --- |
| `/chat`, `/search` | optional bearer JWT; **anonymous by default** |
| Ingestion control plane | **authenticated by default**, admin group for destructive ops |
| `/metrics` | 404 unless ops detail on or caller in ops group |

**Debt:** a live Neo4j credential was committed and deleted, but **remains in git
history** — rotation required regardless. CORS defaults to wildcard (credentials
always disabled, warns at startup).

---

## 12. Observability and measurement

One instrument — `span(name, **attrs)` — feeding per-stage p50/p95 aggregates
attributed to components (Qdrant, LLM, embedding, rerank, extraction, graph).
Span names are the stable contract, not import paths.

**Evaluation harness** (recently added, and it closes what was the largest gap):
judged retrieval benchmark · end-to-end chat benchmark with graded gold set,
hand corrections and a variance probe · graph routing benchmark · entity
extraction/recognition/resolution evaluations · date-resolution evaluation.
~20 committed reports. Tuning can now be argued from measurement — which is what
the dozen off-by-default features are waiting on.

---

## 13. Publication dates — two distinct facts

Recent and worth stating separately, because it is a correctness distinction the
rest of the system depends on.

All ten TERI annual reports are in-body attachments on **one** Drupal page, so all
ten share `published_at = 2022-02-09`. That is the page's date and the publication
date of no edition.

| Field | Meaning | Used for |
| --- | --- | --- |
| `published_at` | the source / web-page date | **all** ranking, filtering, chronology |
| `document_published_at` | what the document states about itself | nothing yet — recorded only |

`document_published_at` is `NULL` unless the document itself says so — never
inferred from an edition label, a PDF CreationDate, a cover month, an upload time
or a URL path. An audit of all ten reports' front and back matter found no
publication statement in any of them, so all ten are NULL.

Instruction alone did not hold: with both the prompt rule and the header caveat in
place, 4 of 6 sampled answers still claimed the reports were "published on 9
February 2022". So it is **checked, not requested** — a deterministic
post-generation guard catches two failures (asserting a document was published on
a page date, and citing a block that does not carry the claimed date), retries
once, and replaces the sentence with a labelled safe form if the retry fails too.

---

## 14. Configuration posture

Significant capability ships complete, tested, and **switched off** — staged
behind measurement rather than reasoning.

| On by default | Off by default |
| --- | --- |
| website preference · date resolution · ingest auth · corpus reconciliation · post-sweep projection · topic constraint · answer cache | knowledge layer *(master)* · per-document knowledge · claim extraction · graph shadow · enrichment · faithfulness check · multi-query · keyword leg · corrective loop · multi-call planner · entity resolution · public auth · ops detail |

---

## 15. Key decisions

| Decision | Because | Cost accepted |
| --- | --- | --- |
| Drupal is the only source | one path to reason about | no bulk corpus additions |
| Content hash covers body text only | must be reproducible from source bytes, or every sweep re-embeds forever | title edits need a separate payload refresh |
| Chunk ids from owned content | unchanged text keeps its id → vectors reusable | needs a separate pipeline-version signal |
| Relevance bands, recency as tie-break | a weighted blend separates hardest exactly when scores are closest | returned score is not monotone with order |
| Catalogue answers from SQL | a count must be a fact; count and list must agree | a second answering path |
| Neo4j is a projection, never a record | any graph problem is fixed by rebuilding | projection lag |
| Closed predicate vocabulary | a model that can invent a relationship can assert anything | new relations need review |
| Templates, never generated Cypher | the only sound graph injection control | expressiveness limited to reviewed shapes |
| Reconciliation reports, never repairs | an unsupervised second write path fails toward data loss | drift needs an operator |
| Tenant/ACL removed | corpus is public; filters were dead weight | no document-level access control |
| Features ship off | staged behind evidence | capability sits unused |

---

## 16. Risks and open items

| Item | Status |
| --- | --- |
| **`app/retrieval/annual_report_editions.py` does not exist** | its only caller imports it inside `try/except`, so the edition filter logs a warning and returns no conditions on **every** query. Committed call site, missing module — the feature is inert |
| Committed Neo4j credential in git history | **needs rotation** |
| Full corpus reprocess for current chunking | pending; tooling exists (`reprocess_corpus`) |
| Knowledge layer never run in production | complete, unexercised at scale |
| `graph_retrieval_enabled` gates nothing | referenced only in docstrings; the live gate is `graph_routing_enabled`, default **on**. Wire it or remove it |
| No document-level access control | correct today, blocking for restricted content |
| Ingestion does not scale horizontally | process-local run lock |
| Broken PDF links accumulate with no report | markers work; visibility missing |
| Docs under `docs/` reference deleted modules | behaviour descriptions sound, module maps stale |

**Designed, not built:** hybrid sparse+dense search · `source_authority` stamping ·
explicit per-bundle field mapping · roadmap items 5, 6, 8, 9, 10. Item 11 (OCR
repair) is explicitly **not** recommended — it is the only proposal where a
generative model would rewrite text later quoted as a citation.

---

## Where to look

| To understand | Read |
| --- | --- |
| Every field and setting | [ARCHITECTURE.md](ARCHITECTURE.md) |
| The flow on one page | [end-to-end-flow.pdf](end-to-end-flow.pdf) |
| Query orchestration | `app/pipeline/query_pipeline.py` |
| Retrieval legs | `app/retrieval/retriever.py` |
| Ranking policy | `app/retrieval/reranker.py` |
| Ingestion orchestration | `app/ingestion/pipeline.py` |
| Knowledge stages | `app/knowledge/document_pipeline.py` |
| Graph safety | `app/retrieval/graph/policy.py` |
| Cross-store invariants | `app/ingestion/reconcile.py` |
| Why a pipeline bump costs | `app/ingestion/version.py` |
| Date-claim guard | `app/generation/date_claims.py` |
| Measured answer quality | `reports/benchmark/` |
