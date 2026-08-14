# Phase 5 — Entity resolution (with the 5.1 identity-model redesign)

```
Mention -> candidate generation -> scoring -> decision -> MySQL
```

No claims, no relationships, no graph writes, no retrieval change. All knowledge
flags remain off. Nothing in this phase touches Neo4j.

---

## 1. Safety result

**Zero false merges and zero canonical leaks across all three types.**

| Type | n | **false-merge** | **leak** | precision | auto | provisional | ambiguous | unresolved |
|---|---|---|---|---|---|---|---|---|
| PERSON | 34 | **0.000** | **0.000** | 1.000 | 0.176 | 0.235 | 0.235 | 0.353 |
| ORGANIZATION | 10 | **0.000** | **0.000** | 1.000 | 0.900 | 0.000 | 0.000 | 0.100 |
| PROJECT | 8 | **0.000** | **0.000** | 1.000 | 0.250 | 0.000 | 0.000 | 0.750 |

* **false-merge** — linked to the wrong entity, or linked at all where nothing
  should link.
* **leak** — asserted a *canonical* identity for a provisional one. This is the
  metric Phase 5.1 added, and it is the one that guards the claim layer.

PERSON asserts a canonical identity for only **17.6%** of cases. That is the
design working, not a shortfall: 8 of 923 person entities are authoritative, so
almost nothing about people in this corpus can be asserted as identity.

---

## 2. The identity problem 5.1 fixes

Phase 5 seeded every author name as a canonical person. The resolver scored a
clean zero false merges — but that measured the *resolver*, not the seed. Two
different people called "Arun Kumar" had already become one entity **before**
resolution ran, and nothing downstream could tell.

The corpus cannot distinguish them: the author facet supplies names, not people.
So the fix is not to un-conflate — that evidence does not exist — but to **stop
claiming an identity that has not been established**.

### Three identity levels

| Trust | Meaning | Claim-eligible | Count |
|---|---|---|---|
| `authoritative` | a CMS record asserts this thing exists and is distinct | yes | PERSON 8, PROJECT 1,623 |
| `derived` | no CMS record, but the name is discriminative — one name denotes one thing | yes | ORGANIZATION 887 |
| `provisional` | a name the corpus attests, **not** shown to denote one real thing | **no** | PERSON 915 |

`claim_eligible` is a column on `documents_entity`, denormalized onto every
decision row, and carried on `Candidate` and `Decision`. The asymmetry between
ORGANIZATION (`derived`, eligible) and PERSON (`provisional`, not) is
evidence-based: "Ministry of External Affairs" names one ministry; "Arun Kumar"
does not name one person.

### A fourth decision state

| State | Meaning |
|---|---|
| `AUTO` | linked to a **canonical** identity — may carry claims, may be a graph target |
| `PROVISIONAL` | linked to a *name*, grouping sightings; asserts no identity |
| `AMBIGUOUS` | plausible, undecided |
| `UNRESOLVED` | no candidate, or every candidate vetoed |
| `NEW` | reserved for deliberate promotion; never written |

`CANONICAL_DECISIONS = (AUTO,)`. Claims and graph projection read
`Decision.canonical`, never a raw `entity_id`, so a provisional link cannot slip
through as an identity. Every link is built by one function (`_link`), so a new
tier cannot forget the distinction.

---

## 3. Expanded PERSON evaluation

52 cases, **34 PERSON**, covering every category requested:

| Category | Cases | Outcome |
|---|---|---|
| authoritative + corroborated | 5 | AUTO — the only canonical people |
| authoritative + no context | 1 | AMBIGUOUS — corroboration required even here |
| authoritative + contradicted | 1 | UNRESOLVED |
| provisional + corroborated | 4 | **PROVISIONAL** — grouped, never canonical |
| provisional + no context | 4 | AMBIGUOUS |
| shared surname, full name | 2 | PROVISIONAL — two Singhs stay distinct |
| bare surname (`Sharma`, `Kumar`, `Singh`) | 3 | UNRESOLVED — 17, 24, 28 people share them |
| initials (`A. K.`, `R K`, `M S`, `S S`) | 4 | UNRESOLVED |
| honorific variants (`Prof`, `Shri`) | 2 | PROVISIONAL — folding does not change the verdict |
| contradictory context | 2 | UNRESOLVED |
| organization / project context only | 2 | AMBIGUOUS — neither is evidence of *which person* |
| junk, unknown, single token | 3 | UNRESOLVED |

Two results worth naming. `M S` is refused even though it shares initials with
the authoritative *M S Unnikrishnan* — initials are never an identity. And
`S S` hits the candidate cap (33 people share those initials) and is refused as
"surface too common" rather than picked from a truncated list.

---

## 4. Reviewed ORGANIZATION debatables

Three cases were semantically debatable and are now settled and documented:

| Case | Verdict | Reasoning |
|---|---|---|
| `Water Resources` | link | a real TERI division. What protects prose is **extraction's case-sensitivity** for short surfaces, not resolution refusing a correctly-cased mention |
| `Medium` | link | a real publication in `field_news_source`, and also an ordinary noun — same reasoning |
| `Forbes` | link | a real publication, short but unambiguous |

The guard against these polluting prose sits in Phase 4 (≤3-token surfaces match
case-sensitively), which is the right layer: resolution should not second-guess a
mention that extraction was careful about.

---

## 5. Bugs found by evaluation

| Bug | Effect | Fix |
|---|---|---|
| A mention corroborated **itself** | PERSON's corroboration requirement was silently always satisfied; every name auto-linked | exclude self from context; drop `f_co_mention` from `CORROBORATING` |
| Descriptive project titles bypassed the Phase 4 guard | `Steel` resolved via canonical name, which consults no alias flag | `v_project_name_not_specific` veto |
| `& Sharma` seeded as a person | 8 facet fragments became entities | require every name token to start with a letter |
| Seed-level PERSON conflation | name-level rows presented as canonical people | the whole of §2 |

Four eval labels of my own were wrong and were corrected rather than "fixed" in
the resolver: two entity ids keyed by name instead of CMS uuid, and two project
titles (`Water Sustainability Assessment of` Chennai and Gurugram) that turn out
to be **PDF attachments inheriting a project bundle**, not project nodes. Both
are now `NO_LINK` cases, which makes them useful tests.

One tempting "fix" was **reverted**: restricting the gazetteer to project *nodes*
would align it with the seeder, but it dropped a real mention and bought nothing,
because junk titles like `"Download"` are already excluded by the minimum-token
rule. An unresolvable mention is not a bug — extraction reports sightings,
resolution decides identity, and `UNRESOLVED` is that working.

---

## 6. Tiers and thresholds

| Tier | Rule | Evidence |
|---|---|---|
| 0 | project code | `(scheme, value)` primary key — a database invariant |
| 1 | exact canonical name, unambiguous | CMS-asserted |
| 2 | exact alias, autolinkable | CMS-asserted or observed gloss |
| 3 | name + corroborating context | CMS metadata agrees |
| 4 | score ≥ threshold **and** margin ≥ threshold | scored |
| 5 | LLM adjudication | **not implemented**, flagged off |

| Type | auto score | auto margin | corroboration required |
|---|---|---|---|
| PERSON | 0.92 | 0.20 | **yes** |
| ORGANIZATION | 0.85 | 0.12 | no |
| PROJECT | 0.85 | 0.12 | no |

**No review queue.** This repository has no reviewer workflow, so a case that
would be queued is left `AMBIGUOUS` — the safe direction anyway.

### Vetoes

`v_type_conflict` · `v_ambiguous_alias` · `v_alias_not_autolinkable` ·
`v_initials_only` · `v_cms_names_someone_else` · `v_project_name_not_specific`

Vetoes beat scores: a perfect name match with contradictory context does not link.

---

## 7. Seeded store

```
PROJECT       1,623 authoritative   932 project-code identifiers (4 conflicts, first kept)
ORGANIZATION    887 derived         176 acronym aliases mined from observed glosses
PERSON            8 authoritative   915 provisional (not claim-eligible)
                                  8,587 aliases, 54 marked ambiguous
```

Acronym glosses are mined in **both directions**: whichever side of
"Full Name (ACR)" the CMS seeded, the other becomes an alias. TERI is why — the
sponsor field lists it as `TERI`, so the full name needed the alias.

---

## 8. Known limitations

**PERSON identity is still name-level; it is now labelled as such.** Two people
sharing a name remain one row. Nothing asserts they are one person, and nothing
downstream may treat them as one — but the underlying ambiguity has not gone
away, and promoting a provisional identity will need evidence the corpus does not
currently carry.

**The evaluation set is 52 cases and I wrote it.** Every case names a real seeded
entity or a real corpus surface, and 35 of 52 are safety cases (`NO_LINK` or
`NO_CANONICAL`). It is still my reading rather than a domain expert's.

**Corroboration for PERSON is one signal** — the document's own `field_authors`.
Organization and project context are deliberately *not* corroboration: neither
says which person a name denotes. That is why the PERSON auto-rate is 17.6%.

**Tier 5 is unimplemented.** The ambiguous cases are exactly its input.

---

## 9. Reproducing

```bash
python -m scripts.seed_entities --rebuild        # seed, mine acronyms, mark ambiguity
python -m scripts._build_resolution_gold         # regenerate the reviewed case set
python -m scripts.eval_entity_resolution         # metrics + safety gate
python -m scripts.eval_entity_resolution --type PERSON
```

## 10. Gate status

```
SAFETY GATE: false-merge 0.000, canonical-leak 0.000 (both must be <= 0.000) -> PASS
```

The gate now covers both failure modes: linking to the wrong entity, and
asserting a canonical identity for something that is only a name. **Claims may
attach to `AUTO` decisions only** — PERSON claims are therefore limited to the 8
authoritative people until a promotion path exists.
