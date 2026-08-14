# Phase 10 — graph retrieval evaluation and shadow integration

Evaluation and observation only. **Graph retrieval is not routed to for any
user**, and every flag that could do so is off:

```
graph_retrieval_enabled = false     graph_shadow_enabled = false
knowledge_enabled       = false     claim_extraction_enabled = false
```

Verified live: the same three questions, answered with shadow off and shadow on,
produce **identical answer fingerprints** and unchanged latency.

---

## 1. The benchmark

`reports/knowledge/graph_queries_v1.json` — 24 reviewed queries in 8 classes,
built by `scripts/_build_graph_benchmark.py` so the derivation is auditable.

Every expected answer traces to a **human-authored Drupal field**
(`field_ongoing_sponsors`, `field_ongoing_pi_name` and their completed
counterparts) through MySQL and the graph projection. Spot-checked against the
CMS source; no model output anywhere in the gold.

Each query records the expected entities, claims, evidence documents, the
template and mode it should route to, and its acceptable answer characteristics
(`must_not_present_ended_funding_as_current`, `must_not_fabricate_an_employer`,
`must_cite_evidence`, …).

### What the benchmark deliberately does not contain

**No superseded or disputed claims.** All 1,653 claims are `active` — the corpus
has produced no conflict yet. Fabricating one would make the numbers describe
fiction, so those paths are covered by fixtures in `tests/test_graph_shadow.py`.

**No chunk-level evidence.** Every claim is CMS-derived and cites a document.
The chunk path is likewise tested rather than benchmarked, per the same rule.

---

## 2. Graph vs existing retrieval

`answer_coverage` — the fraction of gold answer entities whose name appears in
the retrieved context — is the headline, because it is the only metric that
compares the two methods fairly. Both configurations end at the same reranker,
the same context builder and the same block budget (`k=8`).

| class | n | existing | **graph** | citations | existing ms | graph ms |
|---|---:|---:|---:|---:|---:|---:|
| current_funding | 4 | 0.00 | **1.00** | 1.00 | 1436 | 234 |
| multi_hop | 3 | 0.03 | **1.00** | 1.00 | 623 | 33 |
| leadership | 3 | 0.06 | **1.00** | 1.00 | 598 | 27 |
| historical | 3 | 0.00 | **0.83** | 1.00 | 671 | 28 |
| funders_of_project | 3 | 0.67 | 0.67 | 1.00 | 691 | 14 |
| no_result | 2 | 1.00 | 1.00 | — | 644 | 8 |
| non_relational | 5 | 1.00 | 1.00 | — | 591 | 4 |
| ambiguous | 1 | 1.00 | 1.00 | — | 643 | 1 |

**Routing precision 1.00, recall 0.94.** Zero false routes: every non-relational
and ambiguous question was declined. One missed route (`funder-02`), explained
below.

**Citation validity 1.00** on every class that produced rows — every cited
document still resolves in Qdrant.

The existing pull scores **0.00** on funding and near-zero on leadership not
because it retrieves badly, but because the answers are not in prose. A PI's
name lives in `field_ongoing_pi_name`; no amount of semantic similarity will
surface a name the text never contains.

`evidence_recall` is reported in the JSON but excluded here: the gold documents
are the ones the graph's own claims cite, so it is tautological for the graph and
would be a dishonest comparison.

---

## 3. Two defects the benchmark found

### The graph knew the answer and threw it away

The first run scored graph retrieval **0.00 on multi-hop questions it had
answered perfectly**. The traversal returned twelve principal investigators; the
context contained none of their names.

Hydration returns *evidence*, and for a CMS claim the evidence is a project page
whose body never states the fact. The graph found the right answer, cited the
right document, and passed on a passage that did not contain it.

For a relational question **the rows are the answer and the chunks are the
citation**. `app/retrieval/graph/facts.py` now renders the verified rows as the
leading context block, each line carrying its validity window and `claim_id`:

```
Verified relationships recorded in the knowledge graph for Department of Biotechnology:
- Department of Biotechnology funds "Development of Epicuticular fatty acids…",
  which is led by Dr Alak Chandra Deka (since 2019-03-11) [claim_65c3fe241270bb04f9f8d4d6]
```

An ended relationship reads `until 2021-03-31`; a contradicted one is marked
`[DISPUTED - the sources contradict each other]`. A superseded or disputed fact
therefore cannot be read as a current one.

Effect: multi_hop 0.00 → 1.00, current_funding 0.80 → 1.00.

### Person questions could never route

Leadership queries never routed. PERSON resolution requires corroboration — a
co-occurring employer or project — because one seeded "Ritu Sharma" does not make
every "Ritu Sharma" that person. During ingestion that rule is essential: a wrong
link is written into the graph and outlives the mistake.

**A question is a one-line document.** It has no co-mentions by construction, so
the rule rejected every person question.

The resolver is unchanged. The router now reads its audit trail and accepts a
decision only when the resolver found *exactly one* surviving candidate and
withheld it purely for missing context — uniqueness in the entity store being the
corroboration. Two candidates, any veto, an ineligible entity or a provisional
identity still decline.

Effect: leadership 0.06 → 1.00, and the `no_result` class now routes and
correctly returns nothing.

### One tuning change

Historical templates order by recency, so at the current-state default DBT
returned 6 ended funding relationships of 44; at limit 100, all 44. A historical
question now gets `HISTORICAL_LIMIT = 100` and the facts block allows 50 lines
rather than 25, under a hard 8,000-character ceiling. Historical: 0.21 → 0.83.

---

## 4. Shadow mode

`app/retrieval/graph/shadow.py`. Production retrieval stays authoritative; the
graph runs on the same question and the comparison is logged. The claim is
absolute — *the user's answer is what it would have been with this module
absent* — and it is enforced structurally, not by discipline:

- **`observe` returns `None`.** There is no value a caller could misuse.
- It runs on a **background thread**, so graph latency is never added to the
  request.
- Every exception is swallowed. An unreachable Neo4j cannot fail a request that
  had already succeeded without it.
- Work is **dropped, not queued**, past `MAX_IN_FLIGHT`, so a traffic spike
  cannot grow a backlog.
- The graph package is imported *inside* the hook, so with the flag off it is
  **never loaded** — asserted by a test that imports production retrieval in a
  subprocess and inspects `sys.modules`.

Production retrieval gains exactly one doorway, `_observe_in_shadow`, called at
`retriever.retrieve`'s two exits.

### Live result

```
                                              flag off        flag on
What projects are funded by DBT?          6b253f99d519afbd  6b253f99d519afbd  SAME
Who leads projects funded by DBT?         edb0da780761b454  edb0da780761b454  SAME
Environmental impacts of solar energy?    65352e84a1162707  65352e84a1162707  SAME

  routed=True   projects_funded_by_org                rows=20  novel_docs=20  1141ms
  routed=True   people_leading_projects_funded_by_org rows=12  novel_docs=12   482ms
  routed=False  —                                     rows= 0  novel_docs= 0    97ms
```

`novel_documents` is the number the shadow exists to produce: on both relational
questions the graph surfaced documents production retrieval returned **none** of.
Complete disjointness, not marginal improvement — which is consistent with the
coverage table and is the strongest available argument for routing these classes.

---

## 5. Tests

```
pytest tests/test_graph_retrieval.py tests/test_graph_shadow.py -q  ->  147 passed
pytest -q                                                           -> 1822 passed, 0 failed
```

New in `tests/test_graph_shadow.py` (24 tests), covering the requested list:
Neo4j unavailable, Qdrant unavailable during hydration, no graph result, a graph
result with no renderable rows and no evidence, ambiguous entity, disputed claim,
superseded claim, historical boundary dates, and the chunk-evidence path — which
the corpus cannot exercise, so it is asserted directly: a claim citing a chunk
fetches that span exactly and never falls back to document scrolling.

Shadow safety is tested adversarially: a raising graph, a graph that sleeps 1.5 s
(the caller must return in under 250 ms), saturation, and the flag-off path.

---

## 6. Recommendation — which classes to route

Evidence supports routing **three classes**, on the strength of a 0.00 → 1.00
coverage gap, 1.00 citation validity, zero false routes, and 5–25× lower latency:

| route | class | why |
|---|---|---|
| **yes** | `current_funding` | 0.00 → 1.00. The answer is a CMS field; prose retrieval cannot reach it. |
| **yes** | `multi_hop` | 0.03 → 1.00. Two joins no single retrieval pass can make. |
| **yes** | `leadership` | 0.06 → 1.00. Same field-not-prose argument. |
| **probationary** | `historical` | 0.00 → 0.83, but only 3 queries and coverage bounded by the row cap. Route, and keep watching. |
| **no** | `funders_of_project` | 0.67 both ways — no gain, and long descriptive titles resolve unreliably. |
| **no** | everything else | The graph correctly declines; routing would add risk for no benefit. |

Because routing is a **fallback, not a replacement**: the graph leg costs 0.4 ms
to decline, so it can be attempted on every query and defer to existing retrieval
whenever it does not route.

### What should happen before enabling

1. **Run shadow mode on real traffic.** 24 curated queries justify a hypothesis,
   not a production change. The distribution that matters is the one users
   actually send, and `novel_documents` on live traffic is the number to watch.
2. **Confirm the facts block survives generation.** Coverage measures what
   reaches the prompt, not what the model does with it. No answer-level judging
   has been done.
3. **Fix under-merging first, or accept under-reporting.** The Phase 7.2 audit
   found 60 name-order variant groups, so one person can be several `:Person`
   nodes and "who leads what" under-reports.

---

## 7. Known limits

**`funder-02` does not route** — and should not be "fixed". Its title is
*"A stakeholder forum for key actors in the electricity distribution sector
(Phase-2)"*, which Phase 4's `v_project_name_not_specific` veto rejects as a
descriptive phrase rather than a name. That guard prevents far worse errors than
one missed route; extraction v1.1 is unchanged, as instructed.

**Answer coverage is a proxy.** It measures whether the gold names reached the
context, not whether a model then answered well.

**24 queries is small**, and the seeds are the best-populated entities in the
graph. Sparse entities are under-represented.

**Citation validity is 1.00 today** because the graph was projected from the
current corpus. It is the metric that will degrade first after a re-index, which
is precisely why it is measured.

---

## 8. Files

**New:** `app/retrieval/graph/{facts,shadow}.py`,
`scripts/{_build_graph_benchmark,eval_graph_retrieval}.py`,
`tests/test_graph_shadow.py`, `reports/knowledge/graph_queries_v1.json`,
`reports/knowledge/graph_eval_v1.json`, this report.

**Changed:** `app/retrieval/graph/{router,pipeline}.py` (the two defects above),
`app/config.py` (two flags, both off), `app/retrieval/retriever.py` (one gated
hook), `tests/test_graph_retrieval.py` (isolation test strengthened).

**Unchanged, as instructed:** extraction v1.1, entity resolution and promotion,
claim semantics, the template registry, and default retrieval behaviour. No BM25.
