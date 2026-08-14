# Phase 8 — Neo4j projection

Projection only. **Graph retrieval and production retrieval remain disabled**;
`git diff` on `app/retrieval`, `app/pipeline` and `app/cache` is empty, and
nothing in the retrieval path imports the graph.

Preceded by the Phase 7.2 promotion audit, which found no systematic conflation
and cleared the gate (`reports/knowledge/phase7_2_audit.md`).

---

## 1. The graph

```
nodes                          relationships
  Alias         4,228            HAS_ALIAS        4,228
  Entity        2,710            SUBJECT          1,653
  Claim         1,653            OBJECT           1,653
  Project       1,623            USES_PREDICATE   1,653
  Document      1,256            SUPPORTED_BY     1,653
  Organization    887            LED_BY (current)   269
  Person          200            FUNDED_BY (current) 144
  Predicate         7
```

`VERIFY: OK` — MySQL and the graph agree on every count, and every invariant
below holds.

**Person is 200, not 1,003.** The 803 provisional identities are not in the
graph at all, so no traversal can reach a name-level identity and mistake it for
a person.

### A question the layer can now answer

```
MATCH (o:Organization)<-[:FUNDED_BY {current:true}]-(p:Project)
      -[:LED_BY {current:true}]->(person:Person)
```
```
The World Bank                funds  Technology Evaluation for Gree…  led by Ms Sonia Rani
Department of Biotechnology   funds  Banana fiber extraction by myc…  led by Ms Indrani Sarma
Science and Engineering Res…  funds  Metatranscriptomics driven iso…  led by Dr Sushmita Gupta
```

That is a four-hop question answered in four hops, which is the reason the
current-state projection exists alongside the claim nodes.

---

## 2. What is projected, and what is refused

| | Rule |
|---|---|
| **Entities** | only `status='active'` **and** `claim_eligible=1`, filtered in SQL at the source |
| **Trust** | carried onto the node — `pi_attested` (192) stays distinguishable from `authoritative` (8) |
| **Aliases** | for projected entities only, with `autolink` and `is_ambiguous` preserved |
| **Claims** | **every status**, because history is the point |
| **Evidence** | chunk claims → `(:Chunk)`; CMS claims → `(:Document)` |
| **Chunk stubs** | only for chunks that carry a claim — never one per corpus chunk |
| **Conflicts** | `CONTRADICTS` and `SUPERSEDES` between claim nodes |
| **Current state** | active, non-disputed, currently valid, both ends eligible |

A claim is refused at projection if either end is no longer eligible — the
entity store is authoritative at project time, so a demotion takes effect
without rewriting claims.

Superseded and disputed claims **are** projected. They are the answer to "who
led this in 2019", and deleting them would destroy the history the conflict
layer was built to preserve. What they do not get is a current-state edge.

---

## 3. Provenance — walked end to end

```
edge      To develop energy efficient building materia… --LED_BY--> Ms Sonia Rani
leader    trust=pi_attested
validity  2018-12-10 .. present
claim_id  claim_6c0d710f4932e5d26ef9ccda
evidence  cms_field:field_ongoing_pi_name
document  ce1386c7-867f-43e5-b97c-2207538a1135
-> Qdrant 1 chunk retrievable for that document
```

Every current-state edge carries `claim_id`, so the chain
**edge → claim → chunk/document → Qdrant → source text** is walkable for
anything the graph asserts. Neo4j holds no text and no vectors: chunk and
document nodes carry join keys and filter fields only, because duplicating text
would make the graph a second text store.

---

## 4. Safety invariants, checked on the live graph

```
provisional people present:              0
non-active claims with a current edge:   0
current edges lacking claim_id:          0
Person nodes by trust:  {pi_attested: 192, authoritative: 8}
```

### Injection surface

Cypher cannot parameterize a label or a relationship type, so those are the one
thing that must be interpolated — and they come only from
`safe_label` / `safe_relationship`, which raise on anything outside the
code-side allow-list. The relationship allow-list is *exactly* the structural
relationships plus the closed predicate vocabulary, so **a predicate that is not
in the vocabulary cannot become an edge type**.

Every value travels as a parameter. `projection_version` is a parameter too,
not a format argument — a test asserts it.

---

## 5. Idempotency and rebuild

```
nodes,rels before: (9854, 11253)
after re-project:  (9854, 11253)   idempotent: True
```

Every write is `MERGE` on a deterministic key (`entity_id`, `claim_id`,
`chunk_id`, `document_id`, `alias_key`), so re-projection is an update. A test
asserts no statement uses `CREATE`.

`projection_version` stamps each generation, and current-state edges from an
older generation are deleted after a run — which is how a claim that stopped
being current loses its edge without anything having to remember it existed.

**Full rebuild** (`--rebuild`) drops every node, re-applies the schema and
projects again from MySQL. It is always safe because nothing in the graph is a
system of record: a rebuild loses nothing, which is what made adopting a second
database acceptable.

```bash
python -m scripts.project_graph            # project / refresh
python -m scripts.project_graph --rebuild  # drop and rebuild
python -m scripts.project_graph --verify   # diff only, writes nothing
```

---

## 6. Verification

`verify()` diffs MySQL against the graph and reports rather than repairing. Two
of its four checks are the ones worth having, because a recount would not catch
them:

- **a non-active claim backing a current-state edge** — the exact failure the
  conflict layer exists to prevent;
- **a current-state edge citing a claim that does not exist**.

Plus: counts for Entity / Claim / Alias / current edges, and any ineligible
entity present in the graph at all.

`scripts.project_graph` runs verification after every projection and exits
non-zero on a mismatch.

---

## 7. Tests

```
pytest tests/test_graph_projection.py -q  ->  45 passed
pytest -q                                 ->  1675 passed, 0 failed
```

No live Neo4j: a fake session records the statements and parameters that would
be sent. That is deliberate — asserting on the **emitted Cypher** makes the
safety properties structural. A statement that interpolated a value, or a
projection that leaked a provisional identity, fails in the suite rather than in
review.

Covered: label/relationship allow-lists including injection-shaped inputs
(`"Person) DETACH DELETE (n"`), ineligible entities refused, trust carried,
typed labels, claims of every status projected, chunk vs document evidence,
chunk stubs only where claims exist, contradiction/supersession links, disputed
claims producing no current edge, expired claims as history, literal claims never
becoming edges, `claim_id` on every current edge, stale-generation removal,
`projection_version` as a parameter, MERGE-only writes, and repeated projection
emitting identical rows.

---

## 8. Files

**New:** `app/knowledge/graph/{writer,project,verify}.py`,
`scripts/project_graph.py`, `scripts/audit_pi_promotions.py`,
`tests/test_graph_projection.py`, `tests/test_pi_promotion.py`, this report and
the audit report.

**Unchanged:** extraction v1.1, retrieval, claim semantics, the resolver, the
promotion rule.

---

## 9. Open questions

**1. Graph retrieval is deliberately absent.** Nothing reads the graph on the
query path, and `graph_retrieval_enabled` is off. The read side — templates, the
router, evidence hydration by `chunk_id`, ACL-free but still bounded — is Phase 9.

**2. `FUNDED_BY` current edges are 144 of 1,059 claims.** Most funding
relationships belong to completed projects whose period has ended, so they are
history. That ratio is correct but worth stating: the current-state graph is a
small, recent slice of what the corpus knows.

**3. Neo4j Community has no RBAC**, so the read-only boundary for retrieval will
remain code-enforced (`read_session`, a fixed template registry). Recorded again
here because Phase 9 is where it starts to matter.

**4. No conflicts exist yet**, so `CONTRADICTS` and `SUPERSEDES` are projected
by tested code that has never run on real data. They will matter once text
extraction adds claims that compete with CMS ones.

**5. The 60 name-order variant groups** found in the audit mean one person can
appear as several `:Person` nodes. Under-merging, not conflation — safe, but it
will make "who leads what" under-report until variants are reconciled.
