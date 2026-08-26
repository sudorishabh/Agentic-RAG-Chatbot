# Agentic RAG Chatbot — Architecture Study Guide (Interview Prep)

A complete, point-wise, diagram-driven walkthrough of the system **as it exists in
the code today** (verified against commit `b9c8f38`, August 2026). This is the
system-level narrative; `INTERVIEW_QUERY_PIPELINE_DEEPDIVE.md` drills into the
query path and holds the question bank, and `CODEBASE_GUIDE.md` is the exhaustive
map.

---

## 0. The 30-second pitch (say this first)

> "It's a production **Retrieval-Augmented Generation** chatbot over TERI's
> corpus — ~11k PDFs plus the teriin.org Drupal website. Two halves: an
> **ingestion pipeline** that turns every PDF and web page into chunked, embedded
> records in Qdrant with a MySQL catalog alongside; and an **agentic query
> pipeline** that classifies each question multi-label, routes it to the right
> strategy (semantic search, a relational catalog lookup, a scoped summary, or a
> combination), retrieves with several fused strategies, and generates a
> **grounded, cited** answer that refuses rather than hallucinate. It's
> multi-tenant, ACL-scoped, and streams over SSE."

**Why "agentic" and not plain RAG:** the LLM makes **control-flow decisions**
(multi-label intent routing, and a tool plan on the catalog path), and there are
**feedback loops** — self-consistency voting on the classification, multi-query
expansion, a corrective re-retrieval loop when hits are weak, facet relaxation on a
total miss, map-reduce summarization, and a claim-level faithfulness check that can
trigger one regeneration.

**Be honest about flags.** Several of those loops are per-deployment toggles that
ship **off** (multi-query, keyword leg, corrective loop, voting, faithfulness
verify, LLM planner v2, terminal entity resolution). Two stories to tell: the lean
default path, and the fully-enabled agentic path. The flag table is §8.

---

## 1. Big picture — system context

```
                         ┌───────────────────────── CLIENTS ─────────────────────────┐
                         │  Embeddable widget / API consumers  (Bearer-JWT: tenant + groups)
                         └───────────────────────────────┬────────────────────────────┘
                                                          │ HTTPS
        ┌─────────────────────────────────────────────────┼──────────────────────────────────────────────┐
        │                                                  ▼                                              │
        │   PUBLIC RETRIEVAL SERVER  (app/main.py)            PRIVATE INGESTION SERVER (app/ingest_main.py)│
        │   POST /chat   (SSE stream)                         POST /ingest/pdf(s), /ingest/run,            │
        │   POST /search (retrieval only)                          /ingest/article, /reindex               │
        │   GET  /source/{id} (cited PDFs)                    GET  /ingest/log                             │
        │   GET  /health /ready /metrics /metrics/timings     + background sweep scheduler                 │
        │        │                                                     │  (network-isolated, NOT public)   │
        └────────┼─────────────────────────────────────────────────────┼──────────────────────────────────┘
                 │                                                     │
      ┌──────────┴───────────┐                              ┌──────────┴──────────┐
      ▼                      ▼                              ▼                     ▼
 ┌─────────┐          ┌──────────────┐               ┌──────────┐         ┌──────────────┐
 │ Qdrant  │          │ Azure OpenAI │               │  MySQL   │         │ Drupal       │
 │ vectors │          │ chat + embed │               │ catalog  │         │ JSON:API     │
 └─────────┘          └──────────────┘               └──────────┘         │ + PDF files  │
                                                                          └──────────────┘
```

**Two servers, one shared factory (`app/app_factory.py`):**

- **Public retrieval server** (`app/main.py`) — what users hit. Identity (tenant +
  groups) comes from a **verified Bearer JWT** when `auth_enabled`, *never* from the
  request body (`QueryRequest` has no tenant field). CORS never enables credentials.
- **Private ingestion server** (`app/ingest_main.py`) — ingest/reindex endpoints
  plus the periodic sweep on its lifespan. Protected by **network isolation**.

**Two data stores + one model service:**

| Store | Role |
| --- | --- |
| **Qdrant** | Semantic vector search over chunked text. Main collection `documents` (child chunks carry real vectors, parents are zero-vectors fetched by id). A second collection backs the semantic answer cache. |
| **MySQL** | The **document catalog**: ingest-state manifest, the facet tables that answer count/list/distribution questions relationally, an append-only ingest audit log, and the enrichment (abstract) cache. |
| **Azure OpenAI** | Chat model (GPT-4o-mini class) + embeddings (`text-embedding-3-large`, 3072-dim). |

Clients are lazy `@lru_cache` singletons in **`app/core/clients/`** — one gateway
layer every package depends on (and the only thing that touches SDKs).

**The layering rule** (worth one sentence in an interview): `retrieval/` never
imports `generation/` and vice versa — they meet only via
`core/models.ContextBlock`; `pipeline/` is the single layer above both;
`catalog/` is written by ingestion and read by retrieval.

---

## 2. The data model — the foundation everything rests on

### 2.1 CanonicalDocument (`app/core/models/document.py`)

Everything — PDF or web page — is normalized to **one** shape before chunking, so a
single pipeline serves both sources.

- **Identity:** `document_id`, `source_type` ∈ {`pdf`, `website`, `pdf_attachment`},
  `title`, `sections[]`
- **Source refs / cross-links:** `source_url`, `file_url`, `pdf_id`, `pdf_path`,
  `article_uuid`, `linked_pdf_id`, `linked_article_uuid` — the cross-links encode
  "this web page and that PDF are the same content in two formats"
- **Facets & scope:** `authors[]`, `tags[]`, `categories[]` (themes), `language`,
  `tenant_id`, `acl[]`, `published_at`, `doc_version`, `is_current`, `content_hash`
- **Catalog-only extras:** `entity_refs[]` (target UUID + JSON:API type, so a later
  rename can't break joins), `file_links[]`, `raw_meta` (lossless source metadata)

**A detail interviewers like:** `compute_content_hash()` hashes the **body text
only** — not the title, not metadata. The hash has to be reproducible from the
source bytes; if a title read off a PDF cover page could change it, every sweep
would re-version and re-embed the whole corpus, silently and at full cost. A drifted
title is instead carried to the catalog and to the payloads by a single
`set_payload` call (`refresh_document_title`) with no re-embed.

### 2.2 The storage split — why two stores

```
                       ┌────────────────────────────────────────────┐
                       │              A DOCUMENT                     │
                       └───────────────┬───────────────┬─────────────┘
                                       │               │
                 unstructured TEXT ────┘               └──── STRUCTURED FACTS
                 "what does it say?"                         "how many / which / when?"
                          │                                          │
                          ▼                                          ▼
             ┌──────────────────────────┐              ┌──────────────────────────────┐
             │  QDRANT  (`documents`)    │              │  MySQL  (`documents` + facet │
             │  • child chunks + vectors │              │  tables)                     │
             │  • parent chunks (0-vec)  │              │  • one row per document      │
             │  • rich payload per chunk │              │  • author / tag / theme /    │
             │                           │              │    attachment rows           │
             └──────────────────────────┘              └──────────────────────────────┘
```

- **Qdrant answers "what does the content say?"** via semantic similarity.
- **MySQL answers "how many / which / when / by whom?"** relationally — exact
  counts and lists a vector search can't do reliably. Count and list read the *same*
  rows, so they can never disagree.

### 2.3 Parent/child chunking (the key retrieval trick)

```
   ┌─ PARENT chunk (~1800-2600 tok)  ── stored in Qdrant as a ZERO vector (payload carrier)
   │     ├─ child chunk (~400-480 tok) ── stored WITH an embedding  ◄── searched
   │     ├─ child chunk (~400-480 tok) ── stored WITH an embedding  ◄── searched
   │     └─ child chunk (~400-480 tok) ── stored WITH an embedding  ◄── searched
```

- **Search hits small children** (precise match); at answer time the winning child
  is **replaced by its parent** ("parent-expand") for fuller context. Best of both.
- Only children are embedded → cheaper. Parents are fetched by id, never searched
  (`is_parent=false` is a mandatory search filter).
- **A single-child section emits no parent** — it would be a near-duplicate; context
  falls back to child text.
- **Only `embed_text` carries a `title › heading` breadcrumb** (≤32 tokens).
  Headings are lifted into `Section.heading` and rejoined only onto *parent* text,
  and parents are never embedded — so without the breadcrumb a heading would reach
  no vector at all. The stored `text` (what citations quote, what `content_hash`
  covers) stays clean.

### 2.4 MySQL catalog tables

| Table | Contents | Used for |
| --- | --- | --- |
| `documents` | one row/doc: ids, source_type, bundle, entity_type, fingerprint, content_hash, doc_version, changed_mark, size/mtime, published_at, title, url, raw_meta | counts, lists, incremental change detection |
| `documents_author` | (doc, author) | author counts (`LIKE`-matched) |
| `documents_tag` | (doc, tag) | tag scope — matched **exactly** (long-tail vocabulary) |
| `documents_theme` | (doc, theme, **theme_type**, **parent**, **theme_group**) | theme scope incl. sub-themes; Main/Other listings |
| `documents_attachment` | (file_uuid, doc, origin, url, filename) | website ↔ attached-PDF joins |
| `documents_enrichment` | (content_hash, version, abstract, attempts) | ingest-time abstracts; **keyed by content, not document** |
| `ingest_log` | one row per doc per run | audit / debugging, retention-pruned |

**Say this if taxonomy comes up:** the old `terms` / `term_aliases` /
`documents_term` tables are **retired**. The catalog is keyed by **name** now, and
taxonomy UUIDs live only in Qdrant payloads (`term_ids` / `theme_ids`). Theme
scoping in SQL is `theme = X OR parent = X`, which is exact *and* picks up
sub-themes — a substring match would both miss children and merge siblings
("Environment" sweeping in "Environment Education" while missing "Air").

### 2.5 Qdrant payload (per chunk)

`document_id`, `is_parent`, `source_type`, `title`, `chunk_text`,
`section_heading`, `section_type` (toc/references/glossary excluded from search),
`content_hash`, `token_count`, `has_table`, `table_markdown`, `tags`, `categories`,
`authors`, `term_ids`, `theme_ids`, `language`, `tenant_id`, `acl`, `published_at`,
`doc_version`, `is_current`, `source_url`, `file_url`, `pdf_id`, `pdf_path`,
cross-links; children add `parent_chunk_id`, `chunk_index`, `page_number`. Empty
values are dropped.

---

## 3. Ingestion pipeline

### 3.1 The stages

```
 SOURCE                EXTRACT            CANONICAL          CHUNK             EMBED+INDEX
 PDF on disk    ─┐
 Drupal JSON:API ┼──►  per-source   ──►  CanonicalDocument ─► parent/child ──► embed children,
 HTTP upload    ─┘     extractor          (one shape)         chunks           upsert to Qdrant
                        ▲                                                            │
                        └──────── change detection + catalog + audit log (MySQL) ─────┘
```

### 3.2 Change detection first (`ingestion/change_detection/`)

Statuses `NEW` / `CHANGED` / `UNCHANGED` / `DELETED`, one shared decision function
for both sources. **Two-level skipping:**

```
 fingerprint match? ──yes──► skip extraction entirely (cheapest)
        │ no
        ▼
 content-hash match? ──yes──► refresh fingerprint (+ payload title if it drifted),
        │ no                  count "unchanged_content", DON'T re-index
        ▼
 re-chunk, re-embed, index the new version
```

- **PDFs:** fingerprint = file SHA-256, behind a **size+mtime pre-filter** so an
  untouched file is never even read.
- **Drupal:** nodes are incremental against a `MAX(changed_mark)` high-water mark
  (`>=`, so a same-second edit isn't skipped); small taxonomy/block sources are
  fetched in full each run. **The crawl is always oldest-first**, which turns the
  high-water mark into a *resume cursor* — a capped or interrupted run continues
  where it stopped instead of stranding older documents behind the filter.
- **Attachments fan out:** every attached *and* in-body PDF becomes its own
  `pdf_attachment` document, yielded right after its node. In-body PDFs get a
  URL-derived uuid, so the same PDF linked from many pages ingests exactly once.

### 3.3 Extraction

**PDFs (`extractors/pdf_extractor.py`) — per-page routing:**

1. **Classify each page** with PyMuPDF: scanned (text under a char threshold)?
   carries a table?
2. **Route per page:** born-digital text → **PyMuPDF**; born-digital table →
   **Camelot** (lattice, per-page fallback to stream) merged with the page's prose;
   scanned/image → **Azure Document Intelligence OCR** (`prebuilt-read`;
   `prebuilt-layout` also reconstructs tables at ~6× cost).
3. **Every failure degrades:** Azure down → those pages fall back to local text;
   Camelot missing/empty → the page keeps its prose; classification itself failing →
   the whole document goes to Azure, then local. `EXTRACTION_MODE` ∈ {`hybrid`
   (default), `azure_only`, `local_only`}.
4. **Then the page text is cleaned** (`text_normalize`): layout HTML comments,
   `<figure>` wrappers, page-number bars, degenerate infographic "tables", chart
   number-soup, ligature repair (`ﬁ`, and `speci c` → `specific`), formula
   subscripts (`CO,` → `CO2`), and **running headers/footers** detected as short
   lines repeated across ≥50% of pages (joined-window matching, so a footer
   fragmented differently per page still matches).

**Drupal (`extractors/drupal_extractor.py`) — entity-type-aware crawl:**

- Crawls **node bundles** (16: article, news, events, reports, research_papers,
  projects, people, carousel…), **taxonomy terms** (their descriptions are real
  content), and **custom blocks** (boilerplate ones below a char threshold are
  skipped unless they carry a PDF).
- Discovers `field_*` relationships per bundle, resolves them to labels **and**
  `EntityRef`s (UUID + JSON:API type), and converts HTML to text preserving link
  URLs, image alts, iframe srcs and table cell boundaries.
- Attributes are partitioned into **body** (formatted-text fields, long strings) vs
  **metadata** (short scalars/lists) — `field_audit.py` audits exactly which fields
  the pipeline keeps or drops, against the same constants the router uses.

### 3.4 Chunking (`ingestion/chunking/`)

Structure-aware and token-based: `segmenter` (typed blocks; heading detection
*rejects* extraction artefacts — ToC dot leaders, HTML-comment fragments,
pipe/formula rows, OCR symbol soup) → `packer` (tiktoken with a chars/4 fallback;
pack parents, then children inside each parent, coalesce undersized windows, apply
**sentence-aware overlap carry**) → `classifier` (toc/references/glossary by line
*shape*, since extraction garbles their headings) → `payload`. Chunk ids are
`uuid5(document_id | vN | suffix)` — deterministic and **version-scoped**. Per-bundle
size presets, plus `small_pdf` (≤10 pages = one giant parent).

### 3.5 Optional ingest-time enrichment

With `enrichment_enabled` (off by default — it costs real money on a first pass),
each document gets a ~200-word **abstract**: one call under 12k tokens, else
notes-per-window then a reduce. Cached in `documents_enrichment` **by
`content_hash`** (survives a state-table reset, shared by identical bodies) and
invalidated **by version** — `abstract_version()` hashes the prompts + model, so a
prompt edit re-enriches transparently. Failures increment `attempts` so a hopeless
document stops being retried. `enrich_backfill.py` is the deliberate `--limit`ed
pass for documents the sweep never re-crawls.

Why it exists: at query time a scoped summary would otherwise represent each
document by its *lead parent chunk* — for a long report, the cover page or ToC.

### 3.6 Safe reindex (an invariant worth quoting)

> **Index the new version's points FIRST, then delete everything else for that
> document.** Chunk ids are version-scoped, so the document never disappears from
> search mid-swap and a crash mid-index leaves the old version fully intact.

Corpus-wide runs are **mutually exclusive** (a concurrent trigger → HTTP 409).
Batch controls: `ingest_max_docs_per_run` stops cleanly at a *document* boundary
(never between a node and its attachments), unchanged scans are free and never
consume the budget, and `ingest_workers > 1` runs a single-threaded crawler feeding
a bounded worker pool.

---

## 4. Query pipeline — the agentic heart

### 4.1 End-to-end flow

```
                         QUESTION (+ chat history, + verified identity)
                                        │
                                        ▼
             ┌──────────────────────────────────────────────────────────────┐
             │ 1. UNDERSTAND (query_processor.process)                       │
             │    ONE structured LLM call → QueryUnderstanding                │
             │    • MULTI-LABEL intents {label, confidence, rationale}        │
             │    • query_rewrite, output_format, scope, database slots       │
             │    • optional self-consistency VOTING (agreement = confidence) │
             │    • FAILS OPEN → plain "qa" on any error                      │
             └───────────────────────────────┬──────────────────────────────┘
                                              │ deterministic routing (code, not LLM)
   ┌──────────────┬───────────────────┬───────┴────────────┬────────────────────────┐
   ▼              ▼                   ▼                    ▼                        ▼
 chitchat     database only      scoped_summary    database + qa/comparison      qa (default)
   │              │                   │                    │                        │
 direct LLM   PLANNER + catalog   MySQL selects a     catalog section computed   SEMANTIC RAG
 no retrieval tools (count/list/  document SET →      CONCURRENTLY with          (§4.4 — the
              lookup/aggregate/   abstracts (or lead  retrieval, then prefixed   big one)
              list_themes)        chunks) → map-      onto the grounded answer
              (falls through to   reduce summary
              qa if it can't answer)
```

Everything after the single classification call is **deterministic code**. That is
the design claim: the LLM *labels*, the router *decides*.

### 4.2 Step 1 — Multi-label query understanding (`retrieval/query_processor.py`)

One structured-output call returns a `QueryUnderstanding`: a **set** of intents,
each with a confidence and a rationale, plus orthogonal attributes.

**Nine labels on three axes:**

| Kind | Labels | Behaviour |
| --- | --- | --- |
| **Content** (combine freely) | `qa`, `database`, `summarization`, `comparison` | multi-label |
| **Format modifier** | `structured_output` | sets `output_format`; never appears alone |
| **Terminal** (exclusive) | `safety_policy` > `out_of_scope` > `clarification_needed` > `chitchat` | one wins, alone |

**The distinction to nail:** `database` is about **where the data lives**, not the
answer's shape. "How many reports?" is a fact about the catalog → `database`. "How
many MW does the report cite?" is a fact inside a document → `qa`. "Give me a table
of emissions by sector" is `qa` + `structured_output` (content, shaped).

**Confidence is hybrid:** with `analysis_votes=1` (default) it's the model's own
score; with `>1` it fires N samples in parallel at temp 0.7 and confidence becomes
the **agreement share**. Then `_resolve_intents` applies the threshold (0.5),
terminal exclusivity + priority, "modifier never alone", and a guaranteed content
fallback. `is_ambiguous` (top-two content intents within 0.2) is surfaced on
`/search` as a debug/clarification signal.

**Three prompt blocks are appended per request**, in this order so the long static
prefix stays prompt-cacheable:

1. **inventory** — which bundles this deployment actually holds, and which
   configured ones have **no rows**, so the model can't confidently pick a content
   type that can only ever answer zero;
2. **coverage** — the catalog's real `published_range`, so "this year" against an
   archive that stops in 2024 scopes to what exists — *and* the rule that **"the
   latest" names no period at all** (ranking already prefers the newest of
   comparable documents; a guessed date bound would *exclude* the answer);
3. **today's date** — because a model left alone resolves "last six months" against
   its training data, and that failure is invisible: the dates come back
   well-formed, just wrong.

**Dates are asked inclusively, converted in code.** The model fills
`date_to_inclusive`; `exclusive_end()` derives the half-open bound. A model
reliably *copies* a date the user typed and unreliably *increments* one — and when
it forgets, a single-day query loses every row. `core/dates.IsoDate` additionally
salvages trailing JSON punctuation (`"2022-01-01},"`), because a dropped bound
silently **widens** the query.

**One deliberate mapping to defend:** `out_of_scope` routes to **`qa`**, not to a
deflection. The classifier is one stochastic sample and often mislabels an in-corpus
question (a pasted title, a domain topic) as out-of-scope; blind deflection hides
content the store actually has. Routing it through retrieval lets **the corpus be
the arbiter** — a genuinely off-topic query retrieves nothing usable and the
grounding prompt returns the standard refusal.

### 4.3 The catalog ("database") capability — `retrieval/structured/`

A **planner + tools** system, not a hand-written router:

```
 database intent ─► plan(slots)  (v1 deterministic)  /  plan_multi(question) (v2 LLM, opt-in)
                    ─► DatabasePlan = [ToolCall, …] ─► execute() in parallel, fail-open
                    ─► ToolResult{ ok, data, citations, rendered, error_kind }
                    ─► compose: stack rendered sections, renumber citations
```

**Principle: operations are tools; the entity (bundle) is a parameter.** Six tools:
`count_records`, `list_records`, `lookup_record` (can **chain into QA** on one
document), `aggregate_records`, `list_themes` (Main/Other split, optional nested
sub-themes), `resolve_entity`. Two shared pieces: the **Entity Registry** (bundle →
query shape, synonyms, labels, availability) and the **Scope Resolver** (the one
place free-text names are canonicalized and dates parsed).

**Where does canonicalization live, and why?** In the Scope Resolver, on the way to
SQL — *not* as a planner step. A plan's calls execute in parallel with no data flow
between them, so a `resolve_entity` call could never hand its result to a sibling
`count_records`. `resolve_entity` remains as a tool for the one thing that path
can't do: asking the user which of several close matches they meant.

**The guard ladder is the interesting part** — every guard exists because some
phrasing produced a confidently wrong number:

- unknown bundle → fall through to semantic search (never a misleading zero);
- a word naming several bundles ("projects" = completed + ongoing) → **ask**, always
  terminal: picking one reports its total as if it were all, omitting it counts
  articles as projects;
- author/theme/tag that resolution couldn't place → still filter, and only call it a
  miss ("No author matching 'X' found") if the query *also* comes back empty — being
  unsure is not proof of absence;
- a bundle registered but absent from this catalog → fall through: "0 reports" would
  be a fact about the vocabulary, not the corpus;
- **zero under a guessed title substring → fall through.** `title LIKE '%…%'`
  searches one column; the subject lives in the body. Unless the question is
  actually about titles ("titled X", a quoted phrase), that zero would claim the
  corpus is silent on a topic when only its titles are;
- a generic collective word ("publications", "works") → clear an inferred bundle so
  the count spans everything (it was reporting 10 papers instead of 21
  papers + articles).

`error_kind` decides **terminal vs fall-through**: an unanswerable-but-understood
filter *is* the answer; everything else hands the turn to semantic search.

Answers state their own interpretation — `_scope_phrase` names every active filter
using the **canonical** names actually filtered on, and a period is described by the
last day it really covers, not the exclusive bound.

### 4.4 Step 2 — the `qa` retrieval core (`retrieval/retriever.py`)

```
 search_query
     │
     ├─(a) DENSE base pull ───────► Qdrant k=40   (or DUAL: website@20 + not-website@40)
     ├─(b) MULTI-QUERY expansion ─► LLM writes 2 paraphrases (temp 0.7) → dense each
     └─(c) KEYWORD leg ──────────► MatchText(chunk_text) on quoted phrases, proper
     │                              nouns, ACRONYMS, years → dense rank within
     ▼
   RRF FUSION (fusion.rrf): score = Σ 1/(60 + rank) — rank-based, so incomparable
     │                       score scales fuse without calibration
     ▼
   FACET RELAXATION — only on a *total* miss under LLM-guessed facets; the user's
     │                 date scope survives the retry
     ▼
   RERANK (reranker.py) — BANDED: relevance ▸ completeness ▸ recency ▸ authority
     ▼
   CORRECTIVE loop (opt-in, one shot) — top raw score < 0.2 → reformulate → 1 pull → RRF → rerank
     ▼
   BUILD CONTEXT (context_builder.py):
     │   1. parent-expand (child → its parent chunk, batched)
     │   2. cosine dedup ≥0.92 (a linked other-format dup → `also_available`)
     │   3. token budget 9000 / top-6 blocks
     │   4. attention reorder  OR  website-first segregation
     │   5. conflict flag (linked blocks disagree — except a page + its own PDF)
     ▼
   ContextBlock[] → generation
```

**Why RRF instead of blending raw scores?** Dense cosine and full-text match scores
live on different scales; averaging them is meaningless. RRF needs only *rank
order*, so heterogeneous legs fuse cleanly. (The reranker restores magnitude
afterwards.)

**Why a keyword leg at all?** Dense retrieval famously misses exact tokens —
acronyms, proper nouns, precise figures. Terms are extracted deterministically
(quoted phrases, Capitalized Bigrams, `[A-Z]{2,}`, `\d{4}`), and if the query has
none the leg is **skipped**, not run over stopwords. It fails open to dense-only —
notably while the full-text index doesn't exist yet.

**Reranking is banded, not blended — this is the change most worth explaining.**
The old weighted blend got the important case backwards: min-max normalizing
semantic scores separates candidates most aggressively exactly when they are
*closest together*, while a recency weight small enough not to overrule a genuinely
better passage is also too small to break the ties it exists for. So:

1. **relevance band** — within `rerank_relevance_tolerance` (0.03) of the band
   *leader* counts as "similarly relevant"; nothing ever climbs out of its band. The
   band widens ×2 for a **volatile** query (pricing, APIs, regulations,
   announcements, or "latest / current / as of"), so recency fires more often on
   topics that go stale — without ever letting recency cross a band.
2. **completeness** — inside a band, a passage holding 1.5× the text of another says
   substantially more and leads it (log-scaled length as the honest proxy; accuracy
   isn't measurable at ranking time, but a chunk cut short carries less of an
   answer). Cut *within* each relevance band, so a long passage from a less relevant
   document can't place the boundary between two similarly relevant ones.
3. **recency** — comparable passages settle on publication date, newest first
   (undated sits mid-set, so an unknown neither leads nor trails).
4. **authority** — a payload override nothing writes today; kept as the lowest key
   so a corpus that starts stamping it gets the behaviour for free.

Net effect: two editions of the same annual report land in one band and the newer
leads unless it's a fragment — while an older passage that actually answers the
question still beats a newer one that merely mentions it.

**Facet relaxation, and why the date survives it.** When a facet-scoped pull returns
nothing, retry once *without* the facets. The distinction is who chose the
constraint: theme/author/source_type are the LLM's guesses at how the corpus happens
to be labelled, so dropping them recovers from a bad guess; **a period is the
user's own constraint**, and answering "reports from 2023" out of 2019 is worse than
answering nothing — the more so because the widening is invisible (it's on the span
and in the log, never in the answer text).

**Mandatory filters on every Qdrant query** (`hybrid_search.build_filter`):
`is_parent=false`, `is_current=true`, `tenant_id`, `acl MatchAny(user_groups)`, and
`must_not section_type ∈ {toc, references, glossary}`. Security is enforced in the
retrieval layer, not bolted on later.

**The website-preference story** (a good "product constraint met by design"
answer): a handful of website pages compete with ~11k PDFs, so a single pull buries
them. Hence the **dual pull** (website + not-website, one shared query vector) and
**website-first segregation** in the context: ≤2 website blocks that clear a raw
relevance floor lead, then 2 PDFs unconditionally, then **one** extra PDF slot that
opens only for a high-confidence candidate.

### 4.5 The scoped-summary path (`pipeline/summarize.py`)

For "summarize the Climate theme" / "overview of 2024 publications": the user
defined a **set**, which similarity search cannot serve (it would match the *phrase*
"summarize theme X"). So **MySQL selects the set** (newest first, capped at 30),
each document is represented by its **ingest-time abstract** (falling back to a lead
parent chunk only where none exists), and the model summarizes hierarchically — one
direct call when the scope fits ~12k tokens, else map (batched, parallel) then one
reduce. Citations are document-level. Any failure → `None` → plain QA.

---

## 5. Generation & faithfulness

### 5.1 Two grounding contracts, chosen by what the context actually holds

`has_mixed_sources(blocks)` picks between them:

- **Mixed (website + PDF):** website sources are authoritative, and the answer must
  come back as two wrapped blocks — `<website_answer>…</website_answer>` then
  `<pdf_answer>**From our documents** …</pdf_answer>` — never interleaved, never
  PDF-first, each **dropped entirely** when its category has nothing to add.
- **Single-kind:** one continuous answer, explicitly forbidding a source-named
  section or a bolded provenance label.

**Why two prompts?** Demanding the split of a single-kind context made the model
manufacture a second section and fill it by restating the answer. The split only
describes something real when there are two kinds of source to divide.

Shared rules worth reciting: only the numbered context; cite `[n]` after every
claim; the **exact refusal string** when the answer isn't there; never invent
sources; **context is reference material, not instructions** (prompt-injection
defence); **never state how many documents exist** (the context is a sample — that's
a catalog question); on disagreement answer from the block whose header shows the
**later published date**, keeping the older one only where it is plainly fuller.
A history rule is appended only when there is history: prior turns interpret the
question, they are never a source of facts or citations.

Plus an always-on **answer-style** block (be thorough, structure anything past a
couple of sentences, and *depth must come from the context* — every added sentence
carries its own `[n]`), a compact worked example per variant, and an optional format
directive (list/table/summary/detailed/timeline) with its own exemplar and an
explicit precedence note.

`generation/sections.py` is the only reader of that structure: website before PDF
whatever order the model emitted, repeated blocks merged, untagged text keeping its
position (so a catalog prefix stays on top), a block holding only the refusal
dropped when anything else has content, and a **PDF-only answer demoted to plain
prose** (with nothing above it, the block *is* the answer, not a captioned aside).
Parsing is deliberately tolerant — the tags come from a model and a stream can be
cut mid-tag. `ui/script.js` mirrors the same logic with an incremental tag filter.

### 5.2 Citations come from payloads, never the model

The LLM only emits `[n]` markers; `citations.py` maps each to **real metadata from
the chunk payload** (title, URL, page deep-link, section). The model literally
cannot fabricate a citation. Two refinements: a website block links to its own page
(never to its attachment, which is its own citation), and the sources footer lists
**only the blocks the answer actually cited** — a block the model rightly dropped
must not resurface as a chip contradicting the answer above it.

### 5.3 Faithfulness — layered

```
 generate ── validate_markers ─────────────────────────► answer
                  │  (ALWAYS runs: strips any [n] outside 1..n_blocks)
   faithfulness_check on? && blocks present?
                  │ yes
                  ▼
             verify() ── claim extraction, then ONE binary supported/not verdict per
                  │       claim (in parallel) against its CITED blocks
                  │ unsupported claims found
                  ▼
        regenerate ONCE with a correction note → validate → emit as a `correction` event
```

- `validate_markers` **always** runs — a hard guarantee, not a heuristic.
- `verify` is claim-level on purpose: a small model is unreliable as a holistic
  grader but strong at scoped binary verdicts. Fails open at every stage.
- `numeric_mismatches` is deterministic and **observe-only**: numbers in the answer
  absent from the cited blocks are logged and reported, never auto-corrected.

### 5.4 Streaming

| Path | Function | Emission |
| --- | --- | --- |
| `POST /chat` | `stream_answer()` | SSE `token`* → (`correction`?) → `sources` → `done`; terminal `error` if it fails mid-stream |
| `POST /search` | `search_blocks()` | ranked blocks + the full multi-label understanding, **no generation** |

Tokens stream at full speed even with faithfulness on; an unfaithful answer is
corrected *after* streaming via a `correction` event (full replacement text), and
the corrected version is what gets cached. Ready-made results (chitchat, catalog
answer, scoped summary, cache hit, refusal) use the same event shape via one
`token`.

**An operational detail worth mentioning:** `/chat` drives the blocking pipeline one
event at a time through `anyio.to_thread` on a **chat-only capacity limiter**. Each
active stream would otherwise pin one of the ~40 shared request-threadpool threads
for the whole generation and starve auth dependencies and probes; extra chats queue
against their own limiter instead. The generator is closed in a `finally`, so a
client disconnect still runs the pipeline's cleanup.

---

## 6. Cross-cutting concerns

### 6.1 Security / multi-tenancy / ACL
- Identity = **verified Bearer JWT** claims (tenant + groups), never the body.
  Algorithms are an allow-list, `exp` required, audience/issuer enforced when set.
- The same identity scopes `/chat`, `/search` **and** `/source/{id}` — a document
  outside your search visibility is a 404, not a download. Source files are further
  confined to the configured PDF roots (path-traversal guard).
- **Every** Qdrant query carries mandatory `tenant_id` + `acl MatchAny(groups)`.
- `top_k` is bounded (1..50) because it's public input; uploads are size-capped and
  magic-byte checked.
- `/metrics` answers **404** unless `ops_detail_enabled` or the caller is in
  `ops_admin_group` — those bodies fingerprint the deployment.

### 6.2 Caching
- **Semantic answer cache** — a dedicated Qdrant collection. A near-verbatim
  rephrasing (cosine ≥ 0.995) reuses a prior answer, *provided* the facet
  fingerprint matches exactly and the scope partition matches (preference-config
  fingerprint + tenant/groups/top_k + answer_format), so retuning the retrieval
  knobs or crossing an ACL boundary self-invalidates. Qdrant has no TTL, so entries
  carry `expires_at`, filtered at lookup and pruned periodically.
- The older **Redis exact-match and embedding caches were removed**; Redis is now
  optional (reported by `/ready`).
- Also worth naming: the **enrichment cache** (content-hash keyed,
  version-invalidated) and short in-process TTL caches for the catalog inventory and
  published range.

### 6.3 Config (`app/config.py`)
`pydantic-settings` from env / `.env`. Every knob is documented **with its
rationale** in the file itself — chunk sizes, candidate_k/top_k, band tolerances,
thresholds, feature flags, token budgets, batch controls. It's a good file to point
at in an interview: the comments are the design record.

### 6.4 Observability (`app/observability/`)
Per-stage `span()`s feed an in-process registry (count / total / avg / p50 / p95 /
max over a 512-sample window) plus **per-component** totals (qdrant / llm /
embedding / rerank / extraction / other), served by `/metrics/timings`; each request
also logs a `rag_metrics` line with its own stage breakdown. Optional OpenTelemetry
export. Caveat: on the streaming path only the pre-token stages reach the
per-request dict (the SSE driver resumes the generator in fresh contexts) — which is
fine, because retrieval time is all pre-token.

### 6.5 Required index migrations (operational gotcha — good to mention)
- `scripts/create_payload_indexes.py` — the fields every query filters on beyond the
  three created at ingest (`published_at`, `term_ids`, `theme_ids`).
- `scripts/create_fulltext_index.py` — the `chunk_text` full-text index the keyword
  leg needs.
- Both idempotent, server-side over existing points (no re-embedding), and must not
  run during an ingestion run.

---

## 7. Key design decisions & trade-offs (the "why" — interviewers dig here)

| Decision | Why | Trade-off |
| --- | --- | --- |
| **Two stores (Qdrant + MySQL)** | Vectors can't do exact counts; SQL can't do semantic match. Use each for its strength. | Two systems to keep consistent — solved by making MySQL the single catalog, so count == list. |
| **Parent/child chunks** | Precise matching on small chunks + rich context from parents. | Extra storage for parents (mitigated: zero-vectors, never embedded). |
| **Breadcrumb on `embed_text` only** | Headings never reach a vector otherwise (they live on unembedded parents). | Stored text and embedded text differ — deliberately, since `text` is what citations quote. |
| **Route deterministically in code** | The LLM only *labels*; routing is testable and predictable. | A mislabel needs guards — hence fall-through, relaxation and the guard ladder. |
| **Multi-label intents** | Real questions are compound ("how many reports, and what do they say?"). | More classification surface; mitigated by the threshold + terminal-priority rules. |
| **`out_of_scope` → qa** | The classifier mislabels in-corpus questions; the corpus is a better arbiter than one stochastic sample. | A genuinely off-topic query costs one retrieval before refusing. |
| **RRF fusion** | Combine dense + keyword + paraphrase rankings without calibrating score scales. | Ignores score magnitude — the reranker restores it. |
| **Banded reranking** | A blend separates candidates most when they're closest, and a safe recency weight is too small to break ties. Bands make the priority explicit. | Two more knobs (band tolerance, substance ratio) to tune. |
| **Inclusive dates from the LLM, exclusive computed in code** | Models copy dates reliably and increment them unreliably; a forgotten +1 day silently drops a whole day. | One more derived property to keep in sync (a `@property`, so it can't drift). |
| **Ask on ambiguity, fall through on ignorance** | A wrong count reads as a fact; a clarification doesn't. | Occasionally an extra turn instead of an answer. |
| **Citations from payloads + always-on marker validation** | Grounding and auditability; the model cannot invent a source. | Nothing meaningful. |
| **Fail-open everywhere** | A degraded LLM/catalog/cache never takes the whole answer down. | Occasionally a weaker path (passthrough qa) instead of a visible error. |
| **Two servers** | Public read path and privileged write path have different threat models. | Two deployables. |
| **Index new version before deleting old** | Zero-downtime reindex, crash-safe. | Brief double storage during the swap. |
| **Content-hash covers body text only** | A derived title would make the hash unstable and re-embed the corpus forever. | Title drift needs its own (cheap) propagation path. |
| **Ingest-time abstracts** | Pay once per content hash instead of per query, and see the whole document rather than its cover page. | Real money on the first pass — hence off by default plus a budgeted backfill CLI. |
| **Feature flags default off** | Each loop adds latency/cost and wants an eval before it ships. | You must be honest that the default path is leaner than the architecture. |

---

## 8. The honest flag table (what's actually on by default)

| Capability | Setting | Default |
| --- | --- | --- |
| Website dual pull + segregated context | `prefer_website_enabled` | **True** |
| Semantic answer cache | `semantic_cache_enabled` | **True** |
| Banded rerank (embedding provider) | `reranker_provider` | **embedding** |
| Parent-expand / dedup / budget / ordering | — | **always** |
| Marker validation | — | **always** |
| Facet relaxation on a total miss | — | **always** |
| Catalog fallback when retrieval grounds nothing | — | **always** |
| Self-consistency voting | `analysis_votes` | 1 (off) |
| Multi-query expansion | `multi_query_enabled` | False |
| Keyword (full-text) leg | `keyword_leg_enabled` | False |
| Corrective loop | `corrective_loop_enabled` | False |
| LLM planner v2 (multi-call) | `database_multi_call_enabled` | False |
| Terminal entity resolution | `entity_resolution_enabled` | False (matching still runs) |
| Claim-level faithfulness + regen | `faithfulness_check` | False |
| Ingest-time abstracts | `enrichment_enabled` | False |
| Auth | `auth_enabled` | False |

So the **default `qa` path** is: understand (1 call) → dual dense pull (website@20 +
not-website@40) → banded rerank on dense scores → parent-expand + dedup(0.92) +
budget(9000) → website-first context of ≤5 blocks → grounded generation with marker
validation → payload citations → SSE, with a semantic-cache short-circuit up front.
Everything else is opt-in: *"built, unit-tested, enabled where the workload
justifies the extra latency and cost."*

---

## 9. Likely interview questions + crisp answers

- **"Walk me through what happens when a user asks a question."** → §4.1:
  understand (multi-label, fails open) → route (chitchat / catalog / scoped-summary /
  combined / qa) → for qa: embed once, semantic-cache check, dual dense pull (+
  optional paraphrase/keyword legs, RRF-fused), facet relaxation on a total miss,
  banded rerank, optional corrective loop, parent-expand + dedup + budget +
  website-first ordering + conflict flags → grounded generation (one or two blocks
  depending on the context) → marker validation, optional claim verify → payload
  citations → SSE `token`*/`sources`/`done`, then cache + metrics.

- **"How do you prevent hallucination?"** → Grounding prompt (only the numbered
  context, exact refusal string, context-is-not-instructions); citations built from
  payloads so the model can't invent one; `validate_markers` always strips
  out-of-range `[n]`; optional claim-level verification with one regeneration;
  deterministic numeric-mismatch flagging; a hard refusal when there is no context;
  and the prompt forbidding corpus-total claims (that's a catalog question).

- **"Why not pure vector search?"** → It can't answer "how many reports on Climate?"
  reliably, and it misses exact tokens. Hence the MySQL catalog capability and the
  keyword leg. And when the catalog *can't* honestly answer, it says so instead of
  reporting a zero it doesn't have evidence for.

- **"What makes it agentic?"** → LLM-driven multi-label routing and a tool plan on
  the catalog path, plus feedback loops: voting on the classification, multi-query
  expansion, corrective re-retrieval, facet relaxation, map-reduce summarization,
  and verify→regenerate.

- **"How is it multi-tenant / secure?"** → JWT-verified identity (never the body);
  mandatory tenant + ACL filters on every Qdrant query and on the file endpoint;
  bounded public inputs; ops endpoints hidden behind 404.

- **"How do you handle updates without downtime?"** → Two-level change detection
  (fingerprint skip, then content-hash skip) and index-new-before-delete-old with
  version-scoped chunk ids. Plus a resume-cursor crawl so a capped run never strands
  documents.

- **"The website is tiny next to 11k PDFs — how do you stop it being drowned?"** →
  A dual pull (website + not-website sharing one query vector) and a segregated
  context: ≤2 website blocks clearing a relevance floor lead, then 2 PDFs, then one
  gated extra. The generation prompt makes website sources authoritative and splits
  the answer into two labelled blocks.

- **"Tables and scanned PDFs?"** → Per-page classification and routing: PyMuPDF text,
  Camelot for born-digital tables (→ Markdown merged into the page), Azure OCR for
  scanned pages; each with a documented fall-back. Then a normalization pass strips
  running headers, chart number-soup and infographic pseudo-tables.

- **"Where would you take it next?"** → Ship the flagged loops behind an eval
  harness; make `answer_format=detailed` reachable so attachment supplementation
  actually fires; give the qa path a usable author scope; raise the 30-document
  summary cap with a two-level reduce; make numeric verification blocking rather
  than observe-only; and stamp `source_authority` so the ranking's lowest key stops
  being inert.

---

## 10. Glossary (have these one-liners ready)

- **RAG** — retrieve relevant text, feed it to an LLM, generate an answer grounded
  in it.
- **Multi-label intent** — one query can carry several intents; terminal labels are
  exclusive.
- **Parent-expand** — search small child chunks, then hand the LLM the larger parent.
- **Breadcrumb** — `title › heading` prefixed to a child's *embedded* text only.
- **RRF** — Reciprocal Rank Fusion: merge ranked lists by `Σ 1/(k+rank)`.
- **Banded ranking** — relevance decides across bands; completeness, then recency,
  then authority decide within one.
- **Volatile topic** — a query whose answer has a shelf life, which widens the
  relevance band so recency fires more often.
- **Facet relaxation** — retry a zero-result pull without the LLM's guessed facets,
  keeping the user's date scope.
- **Segregated context** — website blocks lead, PDFs follow under their own budget.
- **Two-block answer** — `<website_answer>` then `<pdf_answer>`, only when the
  context genuinely mixes both source kinds.
- **CRAG** — Corrective RAG: detect weak retrieval, reformulate, re-retrieve once.
- **Self-consistency** — sample the classifier N times and use agreement as
  confidence.
- **Map-reduce summary** — summarize each document, then summarize the summaries.
- **Terminal vs fall-through** — a catalog failure that *is* the answer, versus one
  that hands the turn to semantic search.
- **Combined answer** — a deterministic catalog section prefixed onto a grounded
  content answer.
- **ACL MatchAny** — a chunk is visible if any of its `acl` values is in the
  caller's groups.
- **Fail-open** — degrade gracefully on component error rather than erroring the
  request.

---

*Verified against the code at commit `b9c8f38` (branch `main`, August 2026). The
query path in depth — with exact defaults, worked traces and a question bank — is in
`INTERVIEW_QUERY_PIPELINE_DEEPDIVE.md`; the exhaustive module map is
`CODEBASE_GUIDE.md`.*
