# Query Pipeline — Deep Dive + Question Bank (Interview Prep)

Companion to `INTERVIEW_ARCHITECTURE_GUIDE.md`. This expands the **query path** to
the level of the actual code in `app/pipeline/`, `app/retrieval/` and
`app/generation/`, then ends with a **question bank** (§11–§13). Every number here
is the real default from `app/config.py`, verified at commit `b9c8f38`
(August 2026).

> **Read this framing first — it matters in an interview.** Several advanced legs
> (multi-query, keyword leg, corrective loop, self-consistency voting, faithfulness
> verify, LLM planner v2, terminal entity resolution, ingest-time enrichment) are
> **feature-flagged OFF by default**. Each is built and unit-tested; each is a
> per-deployment toggle. So there are two honest stories: the **default path**
> (lean, one classification call + one dual pull) and the **fully-enabled path**
> (the agentic showcase). §8 is the flag table. What *is* on by default and often
> gets missed: the **website dual pull**, **banded reranking**, **facet
> relaxation**, the **catalog fallback**, and the **semantic answer cache**.

---

## 0. The whole pipeline on one page

```
POST /chat  ──►  stream_answer()                         POST /search ──► search_blocks()
                     │                                                        │
                     ▼                                                        ▼
        ┌──────────────────────────── _prepare() — SHARED FRONT-MATTER ───────────────────────────┐
        │  1. process(question, history) → ProcessedQuery                                          │
        │       (multi-label understanding + legacy route + facet filters)                         │
        │  2. chitchat  → direct LLM reply, return                                                 │
        │  3. capabilities → is this a COMBINED (database + qa/comparison) query?                  │
        │  4. structured route:                                                                    │
        │       title lookup that is really a content question → add document_id filter, go to QA  │
        │       database-only → answer_structured() from the MySQL catalog, return (or fall thru)   │
        │  5. scoped_summary → summarize_scope(), return (or fall thru to QA)                       │
        │  6. embed_query(search_query)            [one embedding, reused by every leg]             │
        │  7. semantic_cache.lookup(vector + scope partition + facet fingerprint) → return on hit    │
        │  8. COMBINED? run the catalog section CONCURRENTLY with retrieve()                        │
        │     else retrieve(...) → ContextBlock[]                    (THE QA CORE — §2)             │
        │  9. no blocks → catalog section alone │ catalog listing fallback │ REFUSAL                │
        └────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                      ▼
                       ANSWER STEP: stream tokens → validate markers
                       → [optional faithfulness verify + 1 regen → `correction` event]
                       → citations from payload (cited blocks only)
                       → SSE: token* → sources → done ; persist to semantic cache ; record metrics
```

`/chat` and `/search` share `_prepare`'s understanding + retrieval; `/search` stops
there (no generation, no cache) and additionally exposes the full multi-label
result and the `is_ambiguous` flag for debugging.

---

## 1. Stage 1 — Query understanding (`retrieval/query_processor.py`)

One structured-output LLM call turns the raw turn (+ up to 12 history messages)
into a `QueryUnderstanding`. **This is the only place the LLM makes a routing
decision** — everything after is deterministic code.

### 1.1 The schema the model fills

```python
query_rewrite:  str                     # standalone, pronoun-resolved; add no facts
intents:        list[IntentPrediction]  # {label, confidence 0..1, rationale} — MULTI-LABEL
output_format:  "prose"|"list"|"table"|"csv"|"json"|"markdown"|"diagram"|"timeline"
scope:          source_type ("pdf"|"website"|"uploaded"), target ("whole_corpus"|
                "single_document"|"document_set"|"conversation"), theme, author,
                tags[], date_from, date_to_inclusive, language
# database slots (null unless the `database` intent applies)
operation:      "count"|"list"|"lookup"|"distribution"|"list_themes"
group_by:       "theme"|"content_type"|"author"|"year"
bundle, title_contains, theme_children, limit=10
```

Nine intent labels on three axes — content (`qa`, `database`, `summarization`,
`comparison`), the `structured_output` modifier, and terminal
(`safety_policy` > `out_of_scope` > `clarification_needed` > `chitchat`).

### 1.2 Three prompt blocks appended per request (order matters)

`UNDERSTANDING_SYSTEM` (static, ~150 lines of decision rules + a compact few-shot
bank) then, in this order so the long stable prefix stays **prompt-cacheable**:

1. **`catalog_inventory_directive()`** — "this catalog currently holds only X, Y;
   these are configured but have NO records". Without it the model confidently sets
   a content type that can only ever answer a flat zero, and a zero reads as a fact
   about the corpus when it's a fact about the vocabulary.
2. **`catalog_coverage_directive()`** — "every document was published between A and
   B; nothing is newer than B". Two consequences it states explicitly: a bound past
   B matches nothing (so "this year" on an archive that stops in 2024 scopes to what
   exists), and **"the latest" / "most recent" names no period at all** — leave both
   dates null, because ranking already prefers the newest of the documents that
   answer the question, whereas a guessed bound would *exclude* them.
3. **`current_date_directive()`** — today's date in UTC, with "this year", "last
   year" and rolling windows spelled out. Called per request, not baked into a
   module constant, because the API process can stay up for weeks.

Both catalog directives return `""` on a MySQL blip — an outage falls back to the
configured list / today's-date reasoning rather than claiming the catalog is empty.

### 1.3 Dates: asked inclusively, converted in code

The model fills `date_to_inclusive` (the **last day to include**);
`QueryScope.date_to` is a `@property` that derives the half-open bound via
`core.dates.exclusive_end`. Why: a model reliably *copies* a date the user typed and
unreliably *increments* one — and when it forgets, the last day silently disappears
(for a single-day query, every row does). Making it a property means it cannot drift
from the field the LLM fills.

`core.dates.IsoDate` sanitizes at the model boundary: the observed failure is
trailing JSON punctuation swallowed into the string (`"2022-01-01},"`), and a bound
that fails to parse is *dropped*, which silently **widens** the query ("between 2020
and 2021" answering as "since 2020"). Anything still unreadable is logged, so a bad
bound leaves a trace instead of vanishing.

### 1.4 Self-consistency voting (`analysis_votes`, default **1**)

- `== 1`: one call on the structured LLM; per-label confidence is the model's own
  reported score.
- `> 1`: N samples in parallel at **temperature 0.7**; per-label confidence becomes
  the **agreement fraction** (`len(confs)/n`), and scalar attributes are
  majority-voted (`_vote`, ties take the first non-null in vote order). Errored
  samples are dropped; if all fail → passthrough.

`_resolve_intents` then applies, in order: the `intent_confidence_threshold` (0.5)
gate → terminal exclusivity + priority (the highest-priority terminal label present
wins **alone**) → a guaranteed content intent (fall back to the best content label
below threshold, else `qa` at 0.5) → `structured_output` appended last, never alone.

`_merge_understanding` rebuilds the object **field by field**, which is a
maintenance trap worth naming: a slot added to the schema and not voted here
silently resets to its default (there's a comment saying exactly that, and
`test_merge_votes_every_understanding_slot` guards it).

### 1.5 Collapsing to the legacy route

`_legacy_intent_and_format` produces the single-label route the pipeline acts on:

| Primary intent | Route | Notes |
| --- | --- | --- |
| `chitchat` / `clarification_needed` / `safety_policy` | `chitchat` | no retrieval |
| **`out_of_scope`** | **`qa`** | deliberate — see below |
| `database` | `structured` | catalog planner + tools |
| `summarization` + (`single_document` or a title) | `qa` with `answer_format="summary"` | one named doc |
| `summarization` (a set / whole corpus) | `scoped_summary` | map-reduce over a catalog scope |
| `qa` / `comparison` / a lone modifier | `qa` | full RAG |

**Why `out_of_scope` → `qa`:** the classifier is one stochastic sample and
frequently mislabels an in-corpus question (a pasted document title, a domain topic)
as out-of-scope; a blind deflection then hides content the store actually holds.
Routing it through retrieval lets **the corpus be the arbiter** — a genuinely
off-topic query retrieves nothing usable and the grounding prompt returns the
standard refusal, while a misjudged one gets answered.

`output_format` maps to the legacy `answer_format` via `_FORMAT_TO_LEGACY`
(prose→default, list, table, timeline; csv/json/markdown/diagram degrade to
`default` while the exact shape stays on `understanding`).

### 1.6 Fail-open

Any exception, or all votes failing → a passthrough `ProcessedQuery` with the
original text, `intent="qa"`, no filters, `analysis=None`, `understanding=None`.
Downstream reads that as "no capabilities", which is treated as QA. A degraded
classifier never errors the request; worst case you get plain semantic search.

### 1.7 Facet scope → Qdrant conditions (`understanding/filters.py`)

| Scope | Condition built |
| --- | --- |
| `theme` | `Filter(should=[categories MatchAny(name variants)])` — **name-only**. The term tables are retired, so there is no MySQL lookup to translate a name into UUIDs; casing variants are ORed because payloads store whatever the CMS supplied. |
| `tags` | `tags MatchAny(tags)` |
| `source_type=pdf` | `source_type MatchAny(["pdf","pdf_attachment"])` — "PDFs" includes attachments |
| `source_type=website` | `source_type MatchAny(["website","article"])` — accepts the pre-rename value |
| `language` | `language MatchValue(code)` |
| `date_from`/`date_to` | `published_at DatetimeRange(gte, lt)`, tz-aware UTC — **half-open `[from, to)`** |
| **`author`** | **deliberately not applied** |

**The author omission is a good "we measured it" story.** The stored `authors`
payload field is a *keyword* index (exact value, no substring), populated on only
~20% of chunks, holding full display names ("Ms Meena Sehgal", "TERI Web Desk").
The classifier extracts a loose form ("TERI", "Sharma") that almost never equals a
stored value — so as a hard `AND` it excluded the ~80% of the corpus with no author
at all and then missed the rest, turning strong matches into **false refusals**.
Author scoping stays on the catalog path, which `LIKE`-matches its own facet table;
on the qa path, author names in titles and body text already surface author-relevant
content semantically.

`date_conditions(filters)` extracts just the date subset — that's what makes §2.4's
relaxation policy possible.

---

## 2. THE QA PATH — `retrieve()` in depth (the part you'll be grilled on)

```
 search_query, filters, answer_format, source_type, capabilities
        │
        ▼
 ┌─ Decide which legs run (flags + query shape) ───────────────────────────────────────┐
 │  dual  = prefer_website_enabled(True) AND no explicit source_type AND format != table│
 │  multi = multi_query_enabled AND content intent AND no source_type AND no filters     │
 │          AND len(query.split()) >= 5                                                  │
 │  keyword_terms = extract_key_terms(query)   (only if keyword_leg_enabled)             │
 └──────────────────────────────────────────────────────────────────────────────────────┘
        │
        ▼  the query embedding is passed in from _prepare (embedded exactly once)
 ┌─ CANDIDATE GENERATION (one ThreadPoolExecutor, max_workers=4) ───────────────────────┐
 │  (a) BASE pull  ── dense, candidate_k=40  (or DUAL: website@20 + not-website@40)      │
 │  (b) KEYWORD leg ─ MatchText(chunk_text = salient terms) + dense ranking within        │
 │  (c) MULTI-QUERY ─ LLM writes 2 paraphrases (temp 0.7) → dense search each            │
 └──────────────────────────────────────────────┬──────────────────────────────────────┘
        │  if any extra leg ran:
        ▼
 RRF FUSION ── rrf([base, keyword, para1, para2], k=60): score = Σ 1/(k+rank)
        │
        ▼
 FACET RELAXATION ── zero candidates under LLM-guessed facets? retry once without them,
        │             KEEPING any date scope (§2.4)
        ▼
 RERANK ── BANDED: relevance ▸ completeness ▸ recency ▸ authority   (§2.5)
        │
        ▼
 CORRECTIVE LOOP (opt-in; top raw semantic < corrective_min_score=0.2):
        │   reformulate → 1 extra search → RRF-fuse → rerank once more   (strictly one shot)
        ▼
 BUILD CONTEXT ── parent-expand → cosine dedup(0.92) → token budget(9000) →
        │           attention-reorder (single pull) OR website-first segregation (dual)
        │           → conflict flag
        ▼
 ATTACHMENT SUPPLEMENT (answer_format == "detailed" only — currently unreachable, §2.8)
        ▼
 ContextBlock[]
```

### 2.1 Which legs run — the gating logic (and *why* each guard exists)

- **`dual`** (website-preference pull): on unless the user pinned a `source_type`
  (a "not-website" pull would contradict an explicit `website` filter) or the answer
  wants a `table` (tables live in PDFs — don't force a website lead).
- **`multi`** (multi-query): only for an **open-ended content search**
  (`capabilities ∩ {qa, comparison}`, or the degraded passthrough with no
  capabilities at all — a pure catalog lookup doesn't benefit), with **no**
  `source_type` and **no** facet filters already narrowing the pull, and **≥5
  words** — short factoids are already unambiguous, so paraphrasing only buys
  latency.
- **`keyword_terms`**: extracted deterministically; a query with no salient tokens
  **skips** the leg rather than running it over stopwords.

### 2.2 Candidate generation legs

**(a) Base pull** — `hybrid_search.search`, `limit=retrieval_candidate_k=40`, with
the facet filters. If `dual`, `dual_search` issues **two** pulls sharing one query
vector: `source_type == website` at `website_candidate_k=20`, and a "not website"
pull (`extra_must_not=[website]`) at 40, both keeping any non-source filters. Their
union guarantees the small website's best chunks are fetched even though ~11k PDFs
dominate the corpus.

**(b) Keyword leg** — `extract_key_terms` pulls out exactly what dense vectors
handle worst, by regex: **quoted phrases**, **Capitalized Bigrams** (proper nouns),
**ACRONYMS** (`[A-Z]{2,}`), and **years** (`\d{4}`), deduped case-insensitively.
Those become a Qdrant `MatchText(key="chunk_text")` filter, and dense similarity
ranks *within* the keyword matches. **Fails open to `[]`** — notably while the
full-text index doesn't exist (`scripts/create_fulltext_index.py`), which is why the
flag can ship off without breaking anything.

**(c) Multi-query** — `paraphrases()` asks the LLM at **temp 0.7** (diversity is the
point) for `multi_query_paraphrases=2` alternative phrasings, drops any equal to the
original, and each gets its own dense pull. Any failure degrades to the base query.

> **Latency design:** all legs share one `ThreadPoolExecutor(max_workers=4)`.
> Paraphrase *generation* and the keyword pull overlap the base pull, so the added
> wall-clock is essentially just the paraphrase searches that follow generation.

### 2.3 RRF fusion (`fusion.py`) — *the* hybrid-search question

```python
score(id) = Σ over each ranking of  1 / (k + rank)      # k = 60, rank is 1-based
```

- Combines base + keyword + paraphrase lists into one ranking **by rank position,
  not raw score**.
- **Why rank-based?** Dense cosine (~0..1) and full-text `MatchText` ranking live on
  different scales; averaging them is meaningless. RRF needs only the *order* each
  leg produced, so heterogeneous strategies fuse with no calibration and one leg's
  score distribution can't dominate.
- Deterministic: the candidate object is kept from its **first sighting**, ties break
  on id, and the fused score replaces `.score`. Only runs when at least one extra leg
  produced results — otherwise the base list passes straight through untouched.

### 2.4 Facet relaxation (always on) — and why the date survives

```
kept = date_conditions(filters)
if no candidates AND filters AND len(kept) < len(filters):
        retry the pull with `kept` only        # span rag.search_relaxed
```

Facet filters are **LLM-extracted** and applied as hard `AND` conditions. When the
model lifts literals straight out of the question — a title query parsed into
`theme="SDG 7"`, `author="TERI"` — those rarely equal the stored metadata, and their
intersection can be empty even when the corpus plainly answers the question. A total
miss under facets is never better than the plain semantic pull, so retry once.

Three properties to state precisely:

- **Precision-preserving:** it fires only on *zero* results, so a non-empty
  facet-scoped result is left exactly as-is.
- **The user's date scope survives.** Theme/author/source_type are guesses at how
  the corpus happens to be *labelled*; a period is what the user actually **asked
  for**. Answering "reports from 2023" out of 2019 is worse than answering nothing —
  the more so because the widening is invisible (recorded on the span and the log,
  never in the answer text).
- **An all-dates filter set skips the retry** entirely: it would re-run the pull that
  just came back empty. When the window genuinely holds no chunks, empty is honest
  and the refusal path is correct.

### 2.5 Reranking (`reranker.py`) — banded, not blended

**The argument for the change** (learn this one; it's the best "I fixed a real
ranking bug" story in the codebase): ordering used to be a weighted blend of a
min-max-normalized semantic score, recency and authority. A blend gets the case that
matters backwards — normalizing first means it separates candidates **most
aggressively exactly when their scores are closest together**, i.e. when the
relevance difference means least — while a recency weight small enough not to
overrule a genuinely better passage is also too small to break the ties it exists
for.

So candidates are **banded**, and ranked on the bands in priority order:

```python
_sort_key(r) = (relevance_band,        # 0 = most relevant; nothing ever climbs out
                substance_band,        # 0 = fullest, cut WITHIN the relevance band
                -recency,              # newest first
                -authority,            # payload override; inert today
                -relevance)            # deterministic last resort, sub-tolerance by construction
```

| Tier | Mechanism | Default |
| --- | --- | --- |
| **1. relevance** | `_bands()`: greedy down the sorted order, each band measured from its **leader** (so a long chain of small steps can't drift a weak value into the top band) | `rerank_relevance_tolerance = 0.03` |
| | ×multiplier when `volatility.is_volatile(query)` — pricing, APIs, regulations, announcements, or "latest/current/as of" | `rerank_volatile_tolerance_multiplier = 2.0` |
| **2. completeness** | `log1p(len(text))`, banded *inside* each relevance band; tolerance = `log(ratio)`, so the knob reads as a **ratio** ("1.5× the text says substantially more"). Log scale survives the fact that chunks are already near-uniform, where min-max would inflate 1400 vs 1500 chars into a decisive gap | `rerank_substance_ratio = 1.5` |
| **3. recency** | `published_at` scaled across the candidate set; undated = 0.5 (mid-set, so an unknown neither leads nor trails) | — |
| **4. authority** | `source_authority` payload override; nothing writes it, so it's a constant that cannot reorder anything. Kept as the lowest key for a corpus that starts stamping it | — |

Consequences worth saying out loud:
- Two editions of the same annual report land in one relevance band and, unless one
  is a fragment, **the newer leads**.
- An older passage that actually **answers** the question still outranks a newer one
  that merely mentions it — relevance decides *across* bands, always.
- Widening the band never lets recency cross a band; it only changes how *often* the
  lower keys are reachable.
- `rerank_table_boost` (0.15) is added to **relevance**, not to a final score, so a
  table-bearing chunk can climb a band when the answer wants a table — and it's inert
  when smaller than the band tolerance. Still a nudge, not a filter.
- Returned candidates carry the band basis in `score` and the raw provider score in
  `semantic_score`. **`score` is not monotone with the returned order** (inside a
  band, recency decides) — the context builder's floors and the corrective trigger
  read `semantic_score` for exactly that reason.
- `rerank_score_threshold` (0.0 = off) drops candidates on the **raw** score.

**Providers** (`reranker_provider`, default `embedding`):

| provider | semantic score source |
| --- | --- |
| `embedding` *(default)* | reuse the Qdrant dense similarity — no extra model, no extra latency |
| `llm` | one structured call scores each passage 0..1 (only when ≤40 candidates, 600-char snippets) |
| `cross_encoder` | `sentence-transformers` CrossEncoder, default `BAAI/bge-reranker-v2-m3`, cached per process |
| `cohere` | Cohere Rerank API, default `rerank-3.5`, cached client (constructing one per call rebuilds a connection pool) |

Every non-default provider **falls back to the dense score** on any error. Note for
the tuning question: the band tolerance is sized for the 0..1 scale that
`embedding`/`llm`/`cohere` return — `cross_encoder` emits unbounded logits, so raise
it there.

### 2.6 Corrective loop (`corrective_requery`) — CRAG, one shot

- **Trigger:** `corrective_loop_enabled` AND the top result's **raw semantic score**
  `< corrective_min_score` (0.2) — even the best hit looks weak.
- **Action:** ask the structured LLM for **one** reformulation aimed at what the
  top-3 passages *missed* (their first 200 chars are the evidence); search once; if
  it surfaces any **new** ids, RRF-fuse with the current ranking and rerank again.
- **Bounded and instrumented:** strictly one iteration; a failed, echoing, or
  nothing-new reformulation keeps the original ranking. The span records
  `score_before`, `score_after` and `improved`, so the loop can be *judged* before
  it's trusted — that's why it ships off.

### 2.7 Context building (`context_builder.py`)

Admission (`_admit`) walks candidates in order and applies per candidate:

1. **Relevance floor** (segregated path only) — skip a candidate below the floor for
   the slot class it's competing for, on the **raw** `semantic_score`.
2. **Parent-expand** — the winning child's text is replaced by its **parent chunk**
   (all parents fetched in one batched `retrieve`). Seen-tracking is keyed on
   `parent_id or id`, so two children of the same parent can't both be admitted.
3. **Cosine dedup** — drop a block ≥ `dedup_cosine_threshold` (**0.92**) similar to
   one already kept; if the near-duplicate is a **linked** document, record it on the
   kept block's `also_available[]` so it can still be cited as a secondary source.
4. **Token budget** — stay within `context_token_budget` (**9000**, tiktoken-counted)
   and `retrieval_top_k` (**6**) blocks. The **first block is always admitted** even
   if oversized; a later oversized one is skipped (not a `break`), so a smaller
   candidate behind it can still get in.

Then ordering, one of two modes:

- **Single pull (`segregate=False`):** `_order_for_attention` interleaves
  strongest-first / strongest-last (`head = blocks[0::2]`, `tail = blocks[1::2][::-1]`,
  then `head + tail`) to fight **"lost in the middle"**, renumbering `[n]`.
- **Dual pull (`segregate=True`, the default path):** three admission passes —
  **website** first (≤`website_max_slots`=2, each clearing
  `website_chunk_floor`=0.30), then the top `pdf_max_slots`=2 PDFs
  **unconditionally**, then **one** extra PDF slot that opens only for a candidate
  clearing `pdf_high_confidence_floor`=0.5, and nothing past it. Final order is
  website-first (which also lets a website block win a website/PDF near-dup tie, the
  PDF landing in its `also_available`). This *replaces* attention ordering.

Finally **conflict flagging** (`_flag_conflicts`): any two admitted blocks that are
cross-linked get `conflict=True` — **except** a website node paired with its own
attached PDF (`{website, pdf_attachment}` + linked), which is the same content in two
formats, not a disagreement. `conflict` propagates to the response so the UI can
surface "sources disagree".

### 2.8 Attachment supplementation — built, tested, currently dormant

When admitted **website** blocks have attached PDFs that contributed nothing, do
**one** extra id-scoped pull over those `file_uuid`s
(`scoped_retrieval.search_within_documents`, `_MAX_IDS=150` cap), merge genuinely
new chunks, rerank, and rebuild the context. Bounded to one Qdrant query; any
failure keeps the original blocks.

**Be precise if asked:** it is gated on `answer_format == "detailed"`, and
`_FORMAT_TO_LEGACY` never produces `"detailed"` from the current v2 classifier
(`summary` is produced only for a single-document summarization). So the leg is
unreachable in production today — exercised by `tests/test_attachment_supplement.py`
and waiting on a mapping that emits `detailed`. Naming that yourself is much stronger
than being caught describing a dormant feature as live.

### 2.9 The security filter is on EVERY search (`build_filter`)

Every `search()` — base, dual legs, keyword, each paraphrase, corrective, id-scoped —
carries the same mandatory filter:

```
must:      is_parent  == false      # never surface a parent as a search hit
           is_current == true       # only the live version
           tenant_id  == <caller>   # hard tenant isolation
           acl MatchAny(<groups>)   # row-level ACL, default ["public"]
must_not:  section_type in {toc, references, glossary}   # extract-clean, retrieval-noise
```

`exclude_non_searchable` is a parameter with exactly one caller that turns it off:
`scoped_retrieval.lead_parents`, whose job is to return *something* for a document
rather than the best thing to search (a report whose first chunk is its ToC used to
vanish from a summary scope silently). Collection existence is verified once per
process, so steady state is a single `query_points` per pull.

---

## 3. The catalog ("database") path — `retrieval/structured/`

Answered **entirely from MySQL** — no live JSON:API calls at query time, so `count`
and `list` read the same rows and can never disagree.

### 3.1 Plan → execute → compose

```
 answer_structured(question, history, analysis)
   ├─ slots = analysis (if it carries an operation) else parse_structured()   # one LLM fallback
   ├─ generic collective word? clear an inferred bundle (_spans_all_content)
   ├─ plan  = plan_multi(question)  if database_multi_call_enabled  (v2 LLM, ≤4 calls)
   │          else plan(slots)                                       (v1 deterministic)
   ├─ results = execute(plan, question)      # parallel (≤4 workers), every tool fail-open
   └─ ok results? compose them : terminal failure? its `rendered` IS the answer : None → QA
```

**v1** maps `operation → tool` deterministically: `count`→`count_records`,
`distribution`→`aggregate_records`, `lookup`→`lookup_record`,
`list_themes`→`list_themes`, else `list_records`. Two details:
naming a theme in a "list themes" question implies its **children** ("what's under
Environment?"), and `list_themes` is passed `THEME_VOCABULARY_LIMIT=200` explicitly
rather than the content-row `limit` (10) — otherwise "how many themes are there?"
reports a truncated count as if it were the total.

**v2** (`database_multi_call_enabled`, off) lets an LLM decompose a compound
question ("2023 vs 2024", a count paired with a list) into up to 4 calls; any
failure or empty plan falls back to v1. `_PlannedCall` deliberately omits `offset`
(paging needs conversation state this pipeline doesn't have, and a hallucinated
offset silently hides rows) and takes `date_to_inclusive`, not the exclusive bound.

`_compose` stacks the `rendered` sections and **renumbers citations sequentially**
across them, so a multi-call answer has one coherent citation list.

### 3.2 The six tools

| Tool | Backing | Notes |
| --- | --- | --- |
| `count_records` | `queries.count_documents` | `COUNT(DISTINCT document_id)` when a facet join could fan out |
| `list_records` | `queries.list_documents` | recent-first; renders bullets / Markdown table / year-grouped timeline by `output_format`; per-row citations; `fields` narrows `data` only, never `rendered` |
| `lookup_record` | `list_documents` + `_resolve_chain` | returns `chain_document_id` when a **content** question names a title matching exactly one document |
| `aggregate_records` | `queries.distribution` | group by theme / content_type / author / year; only the `count` aggregation is backed |
| `list_themes` | `queries.theme_vocabulary` | three shapes: top-level themes split **Main / Other**; the same with sub-themes nested; or one named parent's children |
| `resolve_entity` | `structured/resolve.py` | ranked fuzzy match over author / bundle / theme (not tag) |

### 3.3 Fuzzy resolution (`resolve.py`) — no new infrastructure

Plain normalization + `difflib` over each type's small candidate set (16 bundles,
~200 themes, low hundreds of authors). `score()` = max of a whole-string ratio, a
word-order-insensitive token-set ratio, a single-token prefix/abbreviation score
(discounted by how much of the candidate that one token covers, so "environment"
prefers "Environment" over "Environment and Public Health"), and a length-aware
substring boost. Filler words ("theme", "bundle", "type"…) are stripped from the
*query* side only, and never down to nothing.

`classify_band(top, runner_up)`:

```
ACCEPT     top >= 0.90                                  # near-exact, stands alone
       or  top >= 0.60 AND (top - runner_up) >= 0.30    # moderate but dominant
AMBIGUOUS  top >= 0.60                                  # a genuine near-tie → ASK
MISS       otherwise
```

Tuned against worked examples: `"climate"` → *Climate Change* must accept;
`"rishab"` → *Rishabh Negi* / *Rishab Nigam* must **not**. `plausible()` only offers
candidates at or above the ambiguity floor, because with a small pool the 3rd-best
match can be an unrelated name (~0.38 against a 0.75 tie) and offering it implies a
similarity that doesn't exist.

**Tags are matched exactly instead** (`queries.find_tag`, exact then a
case-insensitive fallback so the index is used first): a dev-DB sample found ~237
freeform tag terms over ~224 tagged documents — long-tail CMS tagging, where
similarity ranking would flag an ambiguity on almost every query.

**Where canonicalization happens, and why it isn't a planner step:** in the Scope
Resolver (`filters.resolve_filters`), on the way to SQL. A plan's calls execute in
parallel with no data flow between them, so a `resolve_entity` call could never hand
its result to a sibling `count_records`. Resolving on the way to SQL means every
tool benefits regardless of plan shape. Matching runs **unconditionally** —
`entity_resolution_enabled` only decides what happens to an imperfect match.

### 3.4 The guard ladder (where the correctness lives)

| Stage | Situation | Result |
| --- | --- | --- |
| pre-query | unknown bundle | `ok=False` → fall through to semantic search |
| pre-query | a word naming several bundles ("projects") | **terminal** clarification (`ambiguous_entity`) |
| pre-query | a name matching several entities closely (strict mode) | **terminal** "which did you mean?" |
| post-query | empty **and** author/theme/tag resolution missed | "No author matching 'X' found" (`unresolved`) |
| post-query | empty **and** the bundle is registered but absent from this catalog | fall through (a zero would describe the vocabulary, not the corpus) |
| post-query | empty **and** the title filter was a *guess* | fall through (§3.5) |
| post-query | empty, everything resolved | an honest `0` |

Two rules behind the table:

- **Unresolved is checked *after* querying, never before.** A name matching couldn't
  place is still used as a filter, so the query may well find rows anyway — matching
  works from the names documents carry, and it being unsure is not proof of absence.
  Only an empty result leaves "unknown name" and "genuinely nothing" indistinguishable.
- **Ambiguity is asked, never guessed.** Collapsing "projects" onto one project type
  reports that type's total as if it were every project; leaving the type off counts
  articles and papers as projects. Both are confidently wrong, so the answer is a
  question.

`error_kind` decides terminal vs fall-through: `unresolved`/`ambiguous` are terminal
only while `entity_resolution_enabled` is on (they come from fuzzy matching, which
wants an eval first); `ambiguous_entity` is terminal **unconditionally** — it comes
from a curated list of words, nothing fuzzy about it, and every alternative to asking
is a wrong answer.

### 3.5 `_title_guess_zero` — my favourite guard

`title_contains` becomes `title LIKE '%…%'` over **one column**, so zero under it
means "no title holds this phrase" — never "the corpus holds nothing on this
subject". But the intent layer fills that slot from whatever the question is *about*,
so "how many reports about quantum teleportation" arrives as a title substring — and
the body text it never searched is exactly where a subject lives. Answering 0 there
states the corpus is silent on a topic when only its titles are.

So: a zero under a title filter falls through to semantic search **unless** the
question is genuinely about titles — `\b(titles?|titled|called|named|headlines?)\b`
or a double-quoted phrase. An absent question counts as a guess: falling through
costs one semantic pull, a wrong zero costs the answer.

### 3.6 Answers that state their own interpretation

`_scope_phrase` names every active filter using the **canonical** names resolution
matched ("There are 12 research papers by Dr Suneel Pandey on 'Waste' in 2024
matching your query"), so a wrong match is visible rather than hidden behind a bare
number. `_period_label` collapses a whole calendar year to "in 2024" and otherwise
names the **last day actually covered** (`inclusive_end`) instead of echoing the
exclusive bound — "between 2020-01-01 and 2022-01-01" would claim a day the query
excludes. `_applied_filters` is the same set structurally, so a caller can check the
interpretation programmatically.

### 3.7 Two chaining/fallback paths worth knowing

- **Lookup → QA chaining** (`resolve_lookup_chain`): a `lookup` naming a title, with
  a *content* question around it (an interrogative verb, or `summary`/`detailed`
  shape), that matches **exactly one** catalog document → the pipeline appends a
  `document_id` filter and answers from that document's chunks instead of returning
  title + URL.
- **Catalog fallback** (`catalog_fallback`): when retrieval grounds nothing and the
  catalog hasn't already answered nothing for this query, offer what the catalog
  *lists* for the question's scope, prefixed with `NO_CONTENT_WITH_CATALOG` ("I don't
  have content that answers that. The closest I can offer is what the catalogue lists
  for it."). It requires a **subject** facet (theme / tags / author / title_contains)
  — a bundle or a date alone would offer "the 10 most recent reports", implying a
  relevance the rows don't have — forces `operation=list` (a count answers nothing for
  a content question), never spends an LLM parse (it's on a path that already failed
  once), and fails open to the plain refusal.

---

## 4. Scoped-summary path (`pipeline/summarize.py` + `retrieval/scoped_retrieval.py`)

For "summarize the Climate theme" / "overview of 2024 publications" — the user
defined a **set**, which similarity search can't serve (it would match the *phrase*
"summarize theme X", not a representative sample of the set).

```
 analysis.scope ──► _scope_filters (theme canonicalized; bundle kept only if it is a real
        │            bundle — a summary scope is soft, unlike the count guard; author;
        │            title; dates)       → None if nothing scopes the set → fall to QA
        ▼
 catalog.document_ids_in_scope(limit=_SCOPE_DOC_CAP=30)      # newest-first, capped
        ▼
 _collect_docs: catalog.abstracts_for(ids)  → the INGEST-TIME ABSTRACT per document
        │        scoped_retrieval.lead_parents(missing) → lead parent chunk, only for
        │        documents not yet enriched (so only those cost a Qdrant round-trip)
        ▼
 Σ est. tokens <= _DIRECT_TOKEN_BUDGET (12_000)?
   ├─ yes → ONE grounded call over all documents, cite [n]        ← the usual case with abstracts
   └─ no  → MAP: _batch_documents (~6000 tok/batch) → 4 parallel workers →
                 structured 2–3 bullets per document, document_id copied verbatim
             REDUCE: one call → cohesive thematic overview citing [n], naming the period
        ▼
 document-level Citations ;  any failure → None → plain QA
```

**Why abstracts changed this stage:** an abstract is built from the whole document;
the lead parent chunk is only its *first section* — for a long report, the cover page
or table of contents. Once abstracts exist, a 30-document scope fits one call and
the map stage disappears (the old threshold was a document count, `_DIRECT_DOC_LIMIT
= 5`; it's now a token budget).

**`lead_parents` escalates**, which is the interesting bit: children carry
`chunk_index` and parents don't, so it scrolls each document's earliest *usable*
child then hops to `parent_chunk_id` in one batched retrieve. "Usable" matters
because the mandatory filter excludes toc/references/glossary — a report whose first
chunk is its ToC used to match nothing and **disappear from the scope silently**
(the caller only ever sees a shorter dict). It now tries `chunk_index == 0`, then
chunks 1–4, then chunk 0 with the exclusion lifted, so the common case is still
exactly one point per document.

---

## 5. Combined answers (database + content)

When `capabilities` holds `database` **and** one of `{qa, comparison}`:

```
 catalog section (deterministic)  ─┐
                                   ├─► both run CONCURRENTLY (1-worker pool + copy_context())
 content retrieval + generation   ─┘    so the request pays the SLOWER, not the sum
        ▼
 stream: db_prefix token first, then the grounded answer's tokens
        ▼
 _assemble: final = f"{db_prefix}\n\n{answer}"
```

Three details that make it correct:

- `copy_context()` keeps the worker's span inside this request's stage breakdown.
- Faithfulness and the numeric check run on the **grounded part only** — the catalog
  section is deterministic, not derived from the blocks, so it must never be
  "corrected" by a claim checker.
- If content retrieval comes up empty, the catalog answer is still returned alone
  rather than a blanket refusal. And a *cached* combined answer already carries its
  section, so the cache short-circuit skips rebuilding it.
- The lookup→QA chain sets `chained`, which suppresses the catalog section (the
  catalog already placed the document; only its content is missing).

---

## 6. Semantic answer cache (`cache/semantic_cache.py`, `cache/cache_keys.py`)

- A **dedicated Qdrant collection**, looked up in `_prepare` *after* understanding
  (so the rewritten query is what's embedded) and before retrieval. Nearest
  neighbour on the query vector with `score_threshold = semantic_cache_threshold`
  (**0.995** — near-verbatim rephrasings only; at the old 0.97 a subtly different
  question, another year or theme, could return the wrong cached answer).
- **Scope partition** (`semantic_partition`) = sha256 of the
  **retrieval-preference fingerprint** (`prefer_website_enabled`,
  `website_candidate_k`, `website_max_slots`, `website_chunk_floor`, `pdf_max_slots`,
  `pdf_high_confidence_floor`, `retrieval_top_k`, `retrieval_candidate_k`,
  `context_token_budget`) + identity (`tenant | sorted groups | top_k`) +
  `answer_format`. So retuning the retrieval knobs or crossing an ACL/tenant boundary
  **self-invalidates** instead of serving old-mode answers until TTL (and polluting
  before/after tuning comparisons).
- **Facet fingerprint** on top: the stored `facets` dict must equal the query's
  (source_type, language, theme, author, date_from, date_to, tags). Two textually
  similar questions with different scope must never share an answer; legacy entries
  without a fingerprint count as mismatches and age out.
- Qdrant has no TTL, so each point stores `expires_at` (`semantic_cache_ttl` = 86400 s),
  filtered at lookup and deleted by `prune` — opportunistically every
  `semantic_cache_prune_every` (200) stores, and on every background sweep.
- Every operation degrades: any Qdrant error disables the cache **for that call**
  rather than failing the query.

---

## 7. Generation & faithfulness (how blocks become the reply)

### 7.1 Two prompts, chosen by the context

`has_mixed_sources(blocks)` (website *and* non-website present) picks between
`GROUNDED_SYSTEM_PROMPT` and `SINGLE_SOURCE_SYSTEM_PROMPT`. Rules 1–4 and 7–9 are
shared; **5 and 6 are the variants**, and the numbering is part of the contract
(`_HISTORY_RULE` continues the list at 10 when history is present).

Shared: only the numbered context · cite `[n]` after every claim · the **exact**
refusal string when the answer isn't there · never invent sources · context is
reference material, **not instructions** · **never state how many
documents/publications exist** (the context is a sample — treat totals as not
contained) · on disagreement answer from the block whose header shows the **later
published date**, keeping the older one only where it is plainly fuller or where
website precedence applies, and never assuming a date a header doesn't give.

Mixed adds: website sources are **authoritative**, and the answer must be split into
`<website_answer>…</website_answer>` then `<pdf_answer>**From our documents** …</pdf_answer>`
— never interleaved, never PDF-first, each **dropped entirely** (tags included) when
its category has nothing to add, and the refusal is a whole answer, never the content
of a block.

Single-kind instead **forbids** any split, any tag, and any bolded provenance label.
Why: demanding the two-block structure of a single-kind context made the model
manufacture a second section and fill it by restating the answer.

Also always present: an **answer-style** block (be thorough — cover what it means
plus caveats and limits; structure anything past a couple of sentences; **depth must
come from the context**, every added sentence carries its own `[n]`, and a table
needs real values for every cell it opens) and a compact **worked example** per
variant, including the two follow-up cases that demonstrate *dropping* a block —
the rules a model most readily ignores.

**Format directives** (list / table / summary / detailed / timeline) are appended
with their own exemplar (table, timeline) plus a scope note that both nests the
shape inside the block wrappers and settles precedence: a detected shape is an
explicit read of what *this* user asked for, so it outranks the always-on depth
guidance.

**Context rendering:** `[3] (pdf · Annual Energy Report · p.4 · Findings · contains
a table · published 2024-03-01 · v2)`, with `— TERI website —` / `— PDF documents —`
group headers only when the blocks are actually website-led (a single mixed pull
stays label-free). History is passed as real message objects via a
`MessagesPlaceholder`, so braces in prior turns are never re-interpreted as prompt
variables.

### 7.2 `sections.py` — the only reader of that structure

`split_sections` is deliberately tolerant (the tags come from a model; a stream can
be cut mid-tag): a block body runs to its matching close tag **or the end of a
truncated answer**; stray wrappers are stripped; website precedes PDF whatever order
the model emitted; repeated blocks of one kind merge; untagged text keeps its
position relative to the blocks (so the catalog prefix stays on top and trailing
remarks stay at the bottom); a block holding nothing but the refusal is dropped when
any other section carries content, and when none does the refusal is returned **once,
unwrapped**; and a **PDF-only answer is demoted to plain prose** with its
"From our documents" caption removed — with nothing above it, the block *is* the
answer, not a captioned aside. `strip_tags` gives the verification passes a
tag-free body. `ui/script.js` mirrors all of this, plus an incremental tag filter so
a partially-streamed tag never flashes on screen.

### 7.3 Faithfulness, in layers

- **`validate_markers` ALWAYS runs** — strips any `[n]` outside `1..len(blocks)`. A
  hard guarantee, not a heuristic.
- **`verify` (`faithfulness_check`, default off)** — extract atomic claims (with
  their cited markers), then **one binary supported/not verdict per claim, in
  parallel (4 workers), against that claim's cited blocks** (all blocks when it cites
  none). Claim-level on purpose: a small model is unreliable as a holistic grader but
  strong at scoped binary verdicts. Fails open at every stage (extraction failure →
  faithful; a per-claim error → that claim is skipped, not flagged).
- **One regeneration** with a correction note that points back at "the answer
  structure required above" rather than naming one — the rewrite runs through the
  same prompt, so a single-source answer must not be told to preserve blocks it never
  had. Streamed as a `correction` event (full replacement text) and it is the
  corrected version that gets cached.
- **`numeric_mismatches`** — deterministic, no LLM: numbers in the answer (citation
  markers stripped first, thousands separators normalized) that appear in no cited
  block. **Observe-only**: logged, reported on the response as `numeric_mismatch`,
  never auto-corrected.
- **`citation_coverage`** exists as a deterministic ratio helper (share of sentences
  carrying a marker) for evaluation work.

### 7.4 Citations

Built from payloads in `citations.py`, never from the model: a website block links to
its **own page** (`source_url`) — never to its attachment, which is its own citation
in the PDF group — and a PDF to `file_url#page=N`, falling back to the local
`/source/{pdf_id}#page=N` (absolute when `source_base_url` is set, so a
separate-origin frontend can open it). Near-duplicate linked sources ride along as
`also_available`.

**The footer lists only what the answer cited** (`_cited_blocks`): a retrieved block
the model rightly dropped — an off-topic PDF, say — must not resurface as a chip
contradicting the answer above it. Falls back to every block if the answer cites
nothing, so provenance is never silently lost.

### 7.5 SSE contract

`token`* → (`correction`?) → `sources` → `done`, plus a terminal `error` event if the
stream fails mid-response — by then the 200 and headers are on the wire, so a bare
disconnect would render as a *complete* answer. Ready-made results (chitchat, catalog
answer, scoped summary, cache hit, refusal) use the same shape via one `token`.
`sources` carries `citations`, `intent`, `answer_format`, `used_chunks`, `conflict`,
`numeric_mismatch`.

---

## 8. Default vs fully-enabled (the honest flag table)

| Capability | Setting | Default | On the default path? |
| --- | --- | --- | --- |
| Query understanding (1 structured call) | — | — | **yes** |
| Catalog inventory / coverage / date prompt blocks | — | — | **yes** |
| Self-consistency voting | `analysis_votes` | **1** | no (single call) |
| Dense base search | — | — | **yes** |
| **Website dual pull** | `prefer_website_enabled` | **True** | **yes** |
| Multi-query expansion | `multi_query_enabled` | **False** | no |
| Keyword (full-text) leg | `keyword_leg_enabled` | **False** | no |
| RRF fusion | — | — | only if a leg above is on |
| Facet relaxation on a total miss | — | — | **yes** |
| Banded rerank (relevance ▸ completeness ▸ recency) | `reranker_provider` | `embedding` | **yes** |
| Volatile-topic band widening | `rerank_volatile_tolerance_multiplier` | 2.0 | **yes** |
| Corrective loop | `corrective_loop_enabled` | **False** | no |
| Parent-expand / dedup / budget | — | — | **yes** |
| Website-first segregated context | (with the dual pull) | — | **yes** |
| Attachment supplement | `answer_format == "detailed"` | — | **no** (unreachable, §2.8) |
| Two-block answer structure | (when the context mixes sources) | — | **yes** |
| Marker validation | — | — | **yes** |
| Faithfulness verify + 1 regen | `faithfulness_check` | **False** | no |
| Numeric mismatch flagging | — | — | **yes** (observe-only) |
| Catalog fallback on empty retrieval | — | — | **yes** |
| Semantic answer cache | `semantic_cache_enabled` | **True** | **yes** |
| LLM planner v2 (catalog) | `database_multi_call_enabled` | **False** | no (v1 deterministic) |
| Terminal entity resolution | `entity_resolution_enabled` | **False** | matching runs; only the outcome differs |
| Ingest-time abstracts | `enrichment_enabled` | **False** | affects scoped summaries |

**So the DEFAULT `qa` path is:** understand (1 call) → semantic-cache check → dual
dense pull (website@20 + not-website@40, one embedding) → banded rerank on the dense
scores → parent-expand + dedup(0.92) + budget(9000) → website-first context (≤2
website + ≤2 PDF + 1 gated PDF) → grounded generation (one or two blocks depending on
the mix) with marker validation → payload citations for the cited blocks → SSE →
cache + metrics. Everything else is an opt-in toggle you can describe as *"built,
unit-tested, enabled where the workload justifies the extra latency and cost."*

---

## 9. Config quick-reference (real defaults)

| Setting | Default | Meaning |
| --- | --- | --- |
| `retrieval_candidate_k` | 40 | candidates per pull before rerank |
| `retrieval_top_k` | 6 | context blocks kept (a segregated context usually lands at ≤5) |
| `context_token_budget` | 9000 | max tokens of context (~5 parent blocks) |
| `dedup_cosine_threshold` | 0.92 | near-duplicate drop bar |
| `reranker_provider` | `embedding` | rerank scorer |
| `rerank_relevance_tolerance` | 0.03 | relevance band width |
| `rerank_volatile_tolerance_multiplier` | 2.0 | band widening on stale-prone topics |
| `rerank_substance_ratio` | 1.5 | "substantially more text" ratio (completeness tier) |
| `rerank_score_threshold` | 0.0 | raw-semantic drop bar (off) |
| `rerank_table_boost` | 0.15 | added to relevance for a table chunk when format=table |
| `prefer_website_enabled` | True | the dual pull |
| `website_candidate_k` | 20 | website pull size |
| `website_max_slots` / `website_chunk_floor` | 2 / 0.30 | website lead cap / raw-score floor |
| `pdf_max_slots` / `pdf_high_confidence_floor` | 2 / 0.5 | PDF slots / the gated 3rd slot |
| `multi_query_enabled` / `multi_query_paraphrases` | False / 2 | paraphrase expansion |
| `keyword_leg_enabled` | False | full-text leg (needs the index) |
| `corrective_loop_enabled` / `corrective_min_score` | False / 0.2 | CRAG trigger |
| `analysis_votes` / `intent_confidence_threshold` | 1 / 0.5 | voting / per-label gate |
| `database_multi_call_enabled` | False | LLM planner v2 |
| `entity_resolution_enabled` | False | terminal unresolved/ambiguous answers |
| `faithfulness_check` | False | claim verify + one regen |
| `semantic_cache_threshold` / `_ttl` / `_prune_every` | 0.995 / 86400 / 200 | cache hit cosine / lifetime / prune cadence |
| `chat_stream_max_concurrency` | 64 | chat-only capacity limiter |
| `llm_structured_temperature` | unset | parsing calls use the deployment default unless pinned |
| — | 0.2 | answer generation temperature (hard-coded) |
| — | 0.7 | paraphrase / voting temperature (hard-coded) |
| `azure_openai_embedding_dimensions` | 3072 | `text-embedding-3-large` native |

---

## 10. Worked traces (rehearse saying these out loud)

**Q: "How many research papers were published in 2024?"**
→ Understanding: `intents=[database]`, `operation=count`, `bundle=research_papers`,
`date_from=2024-01-01`, `date_to_inclusive=2024-12-31` → `date_to=2025-01-01`.
Route: `structured`, not combined, no chain → `answer_structured` → v1 plan
`count_records` → the Scope Resolver canonicalizes nothing to canonicalize here →
`count_documents(source_type="website", entity_type="node", bundle=…, published_from,
published_to)` → *"There are 37 research papers in 2024 matching your query."* No
Qdrant, no generation, no cache write on this path. `count` and `list` agree because
both read the same rows.

**Q: "How many publications are there from rishab negi?"**
→ `operation=count`, `author="rishab negi"`, and the classifier may have guessed
`bundle=research_papers`. `_spans_all_content` sees the collective word
"publications" with none of that bundle's label words in the question → **clears the
bundle**, so the count spans every content type (this is the 10-vs-21 bug).
Resolution scores "rishab negi" against every distinct author: *Rishabh Negi* at
~0.93 → ACCEPT, so the filter runs on the canonical name and the answer names it
back. Had *Rishab Nigam* also scored ~0.75, the band would be AMBIGUOUS → with
`entity_resolution_enabled` the answer becomes "which did you mean?"; without it, the
best candidate is taken quietly.

**Q: "What does the Thoothukudi report say about coastal erosion funding?"**
(multi-query + corrective enabled)
→ `intents=[qa]`, rewrite = "coastal erosion funding in the Thoothukudi report".
Embed once. Cache miss. Legs in one pool: dual base pull ∥ 2 paraphrase pulls ∥ the
keyword leg ("Thoothukudi" as a proper noun). RRF fuse → banded rerank. Say the top
raw semantic is 0.15 < 0.2 → the corrective loop reformulates toward what the top-3
missed ("budget allocation for coastal erosion protection"), one more pull, RRF +
rerank, and the span records whether it actually helped. Context: parent-expand,
dedup, website-first segregation, ≤5 blocks. Generation: context is PDF-only → the
**single-source** prompt, one continuous answer, `[n]` per claim; markers validated;
citations deep-link to the PDF pages; sources footer lists only the blocks cited.

**Q: "What's the latest on the waste-to-energy policy?"**
→ Understanding leaves **both dates null** (the coverage directive says "the latest"
names no period). `volatility.is_volatile` matches *policy* and *latest* → the
relevance band widens ×2, so among comparable passages the newest leads — while a
2019 passage that actually answers still beats a 2024 one that only mentions it.

**Q: "How many reports are there on the Climate theme, and what do they cover?"**
→ `intents=[database, qa]` → **combined**. The catalog section
(`count_records` + theme scope, `theme = X OR parent = X` so sub-themes count) runs
concurrently with the content retrieval; the request pays the slower. The answer is
the exact count, then the grounded content answer beneath it; faithfulness would run
only on the second part.

**Q: "Summarize the Climate theme."**
→ `intents=[summarization]`, `target=document_set`, `theme=Climate` →
`scoped_summary`. `resolve_theme("Climate")` → *Climate Change*;
`document_ids_in_scope(theme=…, limit=30)` → say 18 ids. `abstracts_for` returns 15
abstracts; `lead_parents` fills the other 3. Total ≈ 5k tokens ≤ 12k → **one**
grounded call, document-level citations. Un-enriched corpus instead: 18 lead parents
≈ 30k tokens → map (batches ~6k, 4 workers) then reduce. Theme resolving to nothing,
or no summarizable text → `None` → plain QA (and the empty-retrieval path may then
offer the catalog listing).

**Q: "How many reports about quantum teleportation?"**
→ `operation=count`, and the intent layer funnels the subject into
`title_contains="quantum teleportation"`. Count = 0. `_title_guess_zero`: the
question isn't about titles and quotes nothing → **fall through to semantic search**
rather than answering a corpus-wide zero. Retrieval finds nothing either → the
catalog listing needs a subject facet (`title_contains` counts) → whatever the
catalog lists for it, framed as "not the substance you asked for", else the refusal.

---

## 11. Question bank — retrieval

- **"Is this hybrid search?"** → With the keyword leg on, yes: a dense leg and a
  full-text `MatchText` leg fused by RRF. By default it's dense-only (plus the
  website dual pull, which is two *dense* pulls, not a hybrid). Be precise —
  claiming hybrid-by-default is the kind of thing that gets checked.
- **"Why RRF and not weighted score fusion?"** → Dense cosine and full-text scores
  aren't on the same scale, so any weighting needs calibration that drifts with the
  corpus. RRF is rank-based: it needs only each leg's order, is robust to one leg's
  score distribution, and is deterministic (ties on id). The reranker restores
  magnitude afterwards.
- **"Walk me through your reranker."** → §2.5: bands, not a blend. Lead with *why* the
  blend was wrong (normalization separates most when scores are closest; a safe
  recency weight is too small to break ties), then the four tiers, then the two
  invariants — nothing crosses a relevance band, and completeness is only ever cut
  *within* one.
- **"How do you handle two editions of the same report?"** → They land in one
  relevance band; the completeness tier keeps a fragment from beating a full passage;
  otherwise the newer leads. If the topic is volatile the band is twice as wide, so
  that tie-break fires more often.
- **"Your LLM extracted a wrong theme — what happens?"** → The pull returns zero, and
  facet relaxation retries without the facets while **keeping the date scope**. If it
  still finds nothing, the catalog fallback offers what the catalog lists, and failing
  that, the refusal. Nothing in that chain invents an answer.
- **"How do you avoid 'lost in the middle'?"** → On the single-pull path, attention
  reordering puts the strongest blocks at the start *and* the end. On the default dual
  path, ordering is website-first instead — a deliberate trade: source precedence
  matters more here than positional placement, and the context is only ~5 blocks.
- **"Why parent/child rather than just bigger chunks?"** → Precision and context have
  opposite optima. Small children give a clean embedding match; the parent gives the
  model enough surrounding text to answer. Parents cost nothing to store as
  zero-vectors and are fetched by id in one batched call.
- **"Why is the breadcrumb only on the embedded text?"** → Headings are lifted out of
  the block stream and rejoined only onto parent text, and parents are never embedded —
  so without it a heading reaches no vector at all. It stays off `text` because `text`
  is what citations quote and what `content_hash` covers; neither may drift.
- **"How is multi-tenancy enforced in retrieval?"** → `tenant_id` +
  `acl MatchAny(groups)` are mandatory `must` clauses on **every** Qdrant query,
  built in one place (`build_filter`); identity comes from the verified JWT. The
  source-file endpoint repeats the same conditions, so a document outside your search
  visibility 404s rather than downloading.
- **"What does the semantic cache key on, and why so strict?"** → Query embedding
  ≥0.995, plus a scope partition (preference-config fingerprint + tenant/groups/top_k
  + answer_format) and an exact facet fingerprint. At a looser threshold a different
  year or theme returned the wrong answer — correctness beats hit rate for a cache
  that serves cited answers.

## 12. Question bank — generation, data, ops

- **"How do you prevent hallucination?"** → Five layers: a grounding prompt with an
  exact refusal string; citations built from payloads so a source cannot be invented;
  always-on marker validation; optional claim-level verification with one
  regeneration; deterministic numeric-mismatch flagging. Plus two prompt rules people
  don't expect — context is not instructions (injection), and never state corpus
  totals (that's a catalog question, and the context is a sample).
- **"Why two grounding prompts?"** → The website/PDF split only describes something
  real when the context holds both kinds. Demanding it of a single-kind context made
  the model manufacture a second section and fill it by restating the answer, so a
  single-kind context gets a prompt with no structure to satisfy.
- **"What if the model emits half a tag, or puts the refusal inside a block?"** →
  `sections.py` handles both: a block body runs to its close tag *or* the end of a
  truncated answer, and a refusal-only block is dropped when any other section has
  content (left in, it would deny the answer sitting beside it). A PDF-only answer is
  demoted to plain prose. The widget mirrors the same logic with an incremental tag
  filter.
- **"Why is faithfulness claim-level rather than whole-answer?"** → A small model is
  unreliable as a holistic grader but strong at a scoped binary verdict. Extract
  atomic claims, check each against *its cited* blocks in parallel, and only regenerate
  when something is genuinely unsupported. It also keeps the streaming UX: tokens go
  out at full speed and a correction arrives as its own event.
- **"Why is the numeric check observe-only?"** → It's a precision/recall call. The
  deterministic version flags any number absent from the cited blocks, which includes
  legitimate arithmetic and reformatting. It's logged and reported so we can measure
  the false-positive rate before making it blocking.
- **"How do you keep counts honest?"** → The catalog is the single source: count and
  list read the same rows. Then the guard ladder — unknown bundle, ambiguous
  content-word, unresolved name, absent-but-configured bundle, guessed title
  substring — each of which turns a would-be confident zero into either a
  clarification, an explicit miss, or a fall-through to semantic search.
- **"Why ask on ambiguity instead of picking the top match?"** → Because a wrong
  count reads as a fact and a clarification doesn't. "Projects" spanning two bundles
  is the canonical case: pick one and you report its total as if it were every
  project; omit the type and you count articles as projects.
- **"How do updates work without downtime?"** → Two-level change detection
  (fingerprint skip, then content-hash skip), then index-new-before-delete-old with
  version-scoped chunk ids, so a document is never missing from search and a crash
  mid-index leaves the old version intact. A title-only edit doesn't re-index at all —
  it rewrites one payload field.
- **"What stops a big re-ingest from running away?"** → One corpus-wide run at a time
  (409 otherwise); a per-run document cap that stops at a document boundary and never
  between a node and its attachments; unchanged scans don't consume the budget; an
  oldest-first crawl so the changed high-water mark is a **resume cursor**; optional
  batch pauses and a bounded worker pool.
- **"Where does the time go, and how do you know?"** → Per-stage spans
  (`rag.query_understanding`, `rag.embed_query`, `rag.semantic_cache`, `rag.search`,
  `rag.rerank`, `rag.context_build`, `rag.faithfulness`, …) feed an in-process
  registry with p50/p95 over a 512-sample window, rolled up **per component**
  (qdrant / llm / embedding / rerank / extraction), served by `/metrics/timings`;
  each request also logs its own breakdown. Caveat I'd volunteer: on the streaming
  path only pre-token stages reach the per-request dict, which is fine because
  retrieval is all pre-token.
- **"What's the throughput/concurrency story for `/chat`?"** → The pipeline is
  blocking (Qdrant, MySQL, LLM clients), so each stream is driven one event at a time
  through `anyio.to_thread` on a **chat-only capacity limiter**. Without it, enough
  concurrent chats would pin the shared ~40-thread request pool for whole
  generations and starve auth dependencies and probes.
- **"Give me a failure story from this codebase."** → Pick one: 404 theme rows whose
  value was the literal string `"False"` (an upstream boolean leaking into the theme
  facet — now rejected at ingest, with a reclassify script for existing rows); the
  in-body PDF fingerprint that blew past `VARCHAR(128)` and failed with MySQL 1406
  (now the URL-hash uuid); Camelot leaking a temp PDF per page on Windows because its
  backend held an open handle until finalization (`gc.collect()` then retry); or the
  author filter that turned strong matches into false refusals.

## 13. Question bank — trade-offs and "what would you change"

- **"What's the weakest part of the system?"** → Honest list: `answer_format="detailed"`
  is unreachable, so attachment supplementation never fires; the qa path has no author
  scope at all; authority is a dead ranking key; numeric verification is observe-only;
  scoped summaries cap at 30 documents; multi-tag scope collapses to one tag; and the
  most valuable loops are off by default because they haven't been through an eval
  harness.
- **"Why are so many features flagged off?"** → Each adds latency, cost and variance,
  and the honest position is that none of them should ship on a claim rather than a
  measurement. The flags exist so a deployment can turn one on and compare — and the
  corrective loop's span even records whether it improved the top score, which is the
  measurement the decision needs.
- **"What would you build next?"** → An offline eval harness (a labelled query set
  scored on retrieval recall, citation coverage and refusal correctness) so the flags
  can be decided rather than argued; then flip multi-query and the keyword leg if they
  win; make `detailed` reachable; and give the reranker a cross-encoder tier for the
  top ~20 candidates only, which is where a real reranker pays for itself.
- **"Where would this fall over at 10× the corpus?"** → `distinct_authors` is a full
  scan by design (a fuzzy match can't be prefiltered by `LIKE`), which is fine at low
  hundreds and not at tens of thousands; the theme vocabulary is loaded per resolution
  call; and the scoped-summary cap would need the two-level reduce. Retrieval itself
  scales with Qdrant, provided the payload indexes exist.
- **"What would you cut?"** → `hybrid_use_sparse` is a reserved setting with no
  implementation; the `authority` tier is inert; and the buffered `answer_query`
  entrypoint is gone already — the streaming path is the only answer path, which is
  one fewer thing to keep in sync.
- **"How do you know a change didn't break retrieval?"** → 51 test modules, and
  they're behavioural rather than snapshot-based: ranking priority
  (`test_reranker_ranking`), facet relaxation, guard ladder (`test_counting`,
  `test_database_tools`), section parsing (`test_answer_sections`), date salvaging
  (`test_dates`), cache fingerprinting, batch budgets, per-page routing. Plus
  `app/local_tests/run_ingestion_test.py`, which runs the real ingestion path into
  isolated `local_test_*` tables and a throwaway collection and dumps every stage per
  document.

---

*Verified against the code at commit `b9c8f38` (branch `main`, August 2026). System
narrative: `INTERVIEW_ARCHITECTURE_GUIDE.md`. Exhaustive module map:
`CODEBASE_GUIDE.md`.*
