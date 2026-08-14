# Phase 9 — graph retrieval

Read side only. **The default retrieval path is untouched**: `git diff` over
`app/retrieval` (excluding the new `graph/` package), `app/pipeline`,
`app/cache` and `app/main.py` is empty, nothing outside
`app/retrieval/graph/` imports it, and all three flags stay off.

```
graph_retrieval_enabled = false     knowledge_enabled = false
claim_extraction_enabled = false
```

The whole phase is two additions: `app/retrieval/graph/` and
`tests/test_graph_retrieval.py`.

---

## 1. The flow

```
question
  │  router.route         resolve entities + match a relational shape
  ▼
Route(template_id, {entity_id: …})       ← never Cypher, only an id
  │  traverse.run_template               read_session, parameters validated
  ▼
GraphResult: rows of ids                 claim_id, chunk_id, document_id, entity_id
  │  hydrate.hydrate                     Qdrant: retrieve by point id / scroll by document
  ▼
Candidates (real source text)
  │  rerank  →  build_context            the existing ones, unchanged
  ▼
ContextBlocks
```

### Walked end to end, live

```
1 route    people_leading_projects_funded_by_org
           "Department of Biotechnology" -> org_fe5c9534f61e   mode=current
2 neo4j    12 rows, 24 claims, 12 documents, 0 chunks
3 row      Dr Alak Chandra Deka  leads  "Development of Epicuticular fatty acid…"
           claim_65c3fe241270bb04f9f8d4d6   doc 8969a1fc-55dd-4177-a3ac-6a0efe35b750
4 qdrant   14 candidates, first point 0f8b8a3d-cc1b-5d4f-97c8-fa988685642c
5 context  5 blocks, disputed=False
           "DBT-TERI Centre of Excellence in Advanced Biofuels and Bio-commodities"
```

That is the four-hop question — *org funds project, project led by person* —
answered in two `MATCH` clauses and hydrated back to real corpus text.

### Example queries

| Question | Template | Mode |
|---|---|---|
| Who leads projects funded by the Department of Biotechnology? | `people_leading_projects_funded_by_org` | current |
| What projects are funded by DBT? | `projects_funded_by_org` | current |
| Who funded *«project»*? | `funders_of_project` | current |
| What projects did DBT fund previously? | `org_funding_history` | historical |
| What is the history of *«project»*? | `project_history` | historical |
| Who led *«project»* in 2019? | `claims_as_of` | historical |
| What are the environmental impacts of solar energy? | — no route — | |
| Tell me about DBT | — no route — | |

---

## 2. Latency

Warm, median of three runs after discarding a cold one, `top_k=5`:

| Question | Total | route | neo4j | qdrant | rerank | context |
|---|---:|---:|---:|---:|---:|---:|
| multi-hop (4 hops) | **59 ms** | 1 | 9 | 33 | 0 | 27 |
| current, 1 hop | **51 ms** | 1 | 8 | 31 | 0 | 21 |
| historical | **54 ms** | 1 | 8 | 27 | 0 | 10 |
| no route | **0.4 ms** | 0 | — | — | — | — |

Two things worth noting. Neo4j is the cheapest stage, not the most expensive —
the current-state projection turned a four-hop traversal into an indexed lookup.
And **a question that does not route costs 0.4 ms**, which matters because
that is the common case: the graph leg can be attempted on every query without
a latency budget.

First call in a process is ~2 s (driver handshake, gazetteer, entity index).

---

## 3. Security

The requirement was to allow no user- or model-generated Cypher while keeping
the layer useful. The defence is structural rather than a matter of care.

**No Cypher enters.** `run_template` takes a `template_id` and a parameter dict.
There is no function anywhere in the package that accepts a query string. A
Cypher string passed where a template id belongs is an unknown id:

```python
run_template("MATCH (n) DETACH DELETE n", {...})
#  -> error="no such query template", nothing reached the session
```

**The registry is closed and enumerated by the tests**, so a template added
later inherits every rule the moment it exists:

- every value arrives as `$param` — a test parses every map literal in every
  template and asserts each value is a parameter, a boolean, or a bound property;
- no variable-length path (`[*…]`) is expressible, so **depth is fixed by the
  reviewed query text**, not by the data;
- every template ends `LIMIT $limit`, clamped to `MAX_LIMIT = 100`;
- labels and relationship types — the two things Cypher cannot parameterize —
  are checked against `schema.ENTITY_LABELS`, `PROVENANCE_RELATIONSHIPS` and the
  closed predicate vocabulary.

**Parameters are validated before the driver sees them.** `entity_id` must match
`^(?:person|org|project)_[0-9a-f]{12}$`; `as_of` must be an ISO date; a
`predicate` is checked against the vocabulary even though it travels as a value.
Injection-shaped input fails validation, so it never reaches Neo4j at all:

```
org_1') DETACH DELETE (n      rejected: malformed entity_id
Person) DETACH DELETE (n      rejected: malformed entity_id
org_AEEEB2A91BDD              rejected (ids are lowercase hex)
2020-13-01' RETURN 1 //       rejected: malformed as_of date
FUNDED_BY'] AS x MATCH …      rejected: unknown predicate
```

**Sessions are read-only.** `read_session` is the only way in, which matters
because Neo4j Community has no RBAC to enforce it — as recorded in Phase 8, the
boundary is code-enforced by construction.

A model may later *choose a `template_id`*; that is the one degree of freedom the
design allows. Today routing is deterministic pattern matching, which is free,
testable, and cannot be talked into a template by the question text.

---

## 4. Truth-telling

**Disputed claims are never presented as current fact.** Current-state templates
read `{current: true}` edges, and Phase 8's projection withholds that edge from
any claim that is disputed, non-active or expired. A disputed claim is therefore
*unreachable* by a present-tense question — not filtered out, but structurally
absent.

**Historical questions still see it.** The history templates traverse `:Claim`
nodes and return `status` on every row, and a test asserts they never filter on
it. `GraphResult.has_disputed` flags the answer so a caller must label it. Hiding
a contradiction is worse than showing one, provided it is marked.

**Superseded claims remain queryable.** They are the answer to "who led this in
2019". `claims_as_of` uses a half-open window — `valid_from <= $as_of` and
`valid_until > $as_of` — so a claim that ends on the queried date is already
over, and a handover day is not counted twice. A `NULL` bound means open-ended,
not excluded.

**Provisional people are unreachable.** They were never projected, so no
traversal can reach a name-level identity and mistake it for a person.

**Ambiguity yields no answer.** Routing resolves entities with the *same*
resolver ingestion uses, so a surface too ambiguous to link there is equally
unusable here. "TERI" is attested both as an organization (a sponsor) and as a
person (an author string), so it does not autolink and questions naming it do
not route — a miss, deliberately, rather than a guess.

---

## 5. Two defects found by running it

**Current-state templates could not cite their evidence.** They returned
`claim_id` but no `chunk_id` or `document_id`, so a traversal returned 12 rows
and hydration returned nothing — an answer with no source text. Each current
template now reaches through the claim behind the edge to its evidence, and a
test enumerates the registry to assert every template returns both fields.

**A long document could starve the others.** `hydrate_documents` issued one
`scroll` per batch with a budget of `documents × per_document`; `scroll` has no
fairness, so a chunk-heavy document consumed the whole budget and every other
cited document contributed nothing. Hydration now keeps the broad scroll — it
usually covers everything in one round trip — and adds a second pass that fetches
directly, one document at a time, only for documents the first pass missed
entirely. Document count is capped at `MAX_DOCUMENTS = 20`, since the context
builder keeps a handful of blocks and the rest would be round trips spent on
discarded candidates.

Both were caught by running against the live corpus, not by review.

---

## 6. Hydration

Neo4j holds no text. The hop to Qdrant is `chunk_id`, which has been the Qdrant
point ID since long before the graph existed — no new key, no duplicated text.

| Evidence | Lookup |
|---|---|
| chunk claim | `retrieve` by point id — **exact**, no embedding, no scoring |
| CMS claim | `scroll` by `document_id` through the existing `build_filter` |

Document evidence is the fallback, and today it is the *only* path: all 1,653
claims are CMS-field claims, and a metadata fact has no span to point at. Reusing
`build_filter` means a graph answer cannot surface a parent chunk or a superseded
version that ordinary retrieval would exclude — a test asserts the filter keys.

Both lookups are batched at 150 ids. Duplicate chunk ids are fetched once (a
graph result routinely names one chunk twice, from two claims in one document).
A chunk the graph cites but Qdrant no longer holds is **dropped, never invented** —
re-indexing changes chunk ids, so a stale citation is expected rather than
exceptional.

---

## 7. Failure is a value

No question fails because the graph was unavailable. An unreachable Neo4j, an
empty traversal, a failed hydration and an unroutable question all return an
empty result with a reason, and the caller falls back to ordinary retrieval. The
graph is an enrichment; nothing in the answer path depends on it.

---

## 8. Tests

```
pytest tests/test_graph_retrieval.py -q  ->  122 passed
pytest -q                                ->  1797 passed, 0 failed
```

Covering the requested list: graph-only and multi-hop queries, current and
historical modes, temporal boundary semantics, superseded and disputed claims,
empty results, ambiguous entities, multi-row de-duplication, graph → chunk ids,
batched hydration, missing and duplicate chunks, bounded traversal, injection-
shaped ids/predicates/dates/labels, arbitrary-Cypher rejection, `claim_id` and
current-edge provenance, and Neo4j-failure fallback. Plus the two defects above,
and an isolation test that walks `app/retrieval` and `app/pipeline` asserting
nothing imports the graph package.

Unit tests use a fake session, per repo convention. **`test_live_graph_smoke`
runs every template against a real Neo4j** and skips when none is reachable —
it catches Cypher that is valid text but invalid to the server (a syntax error,
a renamed property), which a fake cannot. It passes against the live graph and
skips cleanly without one.

---

## 9. Open questions

**1. Nothing is wired to production.** The router, templates, traversal and
hydration exist and work; no request reaches them. Choosing *when* to attempt the
graph leg and how to fuse it with RRF is the next phase, and it is the one that
changes default behaviour.

**2. `CONTRADICTS` has never fired on real data.** No conflicts exist yet, so the
disputed-claim path is exercised only by tests. It starts to matter when text
extraction adds claims that compete with CMS ones.

**3. Routing coverage is narrow by construction.** Eight patterns over three
entity types. A question just outside them does not route, and costs 0.4 ms to
find that out — the right trade while the graph leg is additive.

**4. The 60 name-order variant groups** from the Phase 7.2 audit still mean one
person can appear as several `:Person` nodes, so "who leads what" under-reports.
Under-merging, not conflation — safe, but visible in these answers.

**5. `chunk_id` hydration is untested against real data**, because no claim
carries a chunk yet. The code path is tested; the corpus has not exercised it.
