# Phase 5 — Entity resolution

```
Mention -> candidate generation -> scoring -> decision -> MySQL
```

No claims, no relationships, no graph writes, no retrieval change. All knowledge
flags remain off. Nothing in this phase touches Neo4j.

---

## 1. Safety result

**Zero false merges across all three entity types. The gate passes.**

| Type | n | **false-merge** | precision | auto | ambiguous | unresolved |
|---|---|---|---|---|---|---|
| PERSON | 13 | **0.000** | 1.000 | 0.308 | 0.154 | 0.538 |
| ORGANIZATION | 6 | **0.000** | 1.000 | 0.833 | 0.000 | 0.167 |
| PROJECT | 5 | **0.000** | 1.000 | 0.200 | 0.000 | 0.800 |

Auto-rate is deliberately low and is **not** a target. PERSON links only 31% of
cases, and PROJECT only 20% — in both cases because the resolver declined rather
than guessed. That is the intended direction of error.

`scripts/eval_entity_resolution.py` exits non-zero when any type's false-merge
rate exceeds zero, so this is a gate rather than a report.

---

## 2. What was built

| Module | Role |
|---|---|
| `app/knowledge/seed.py` | canonical entities, aliases, identifiers from CMS |
| `app/knowledge/candidates.py` | bounded, deterministic candidate generation |
| `app/knowledge/scoring.py` | features, vetoes, per-type thresholds |
| `app/knowledge/resolver.py` | tiers, decision states, audit |
| `app/catalog/entities.py` | MySQL persistence |
| `scripts/seed_entities.py` | repeatable seeding pipeline |
| `scripts/eval_entity_resolution.py` | per-type metrics + safety gate |

Named `resolver.py`, not `resolve.py`: `app/retrieval/structured/resolve.py`
already exists and means query-time facet matching.

### Seeded store

```
PROJECT       1,623 entities   932 project-code identifiers
ORGANIZATION    887 entities   176 acronym aliases mined from observed glosses
PERSON          923 entities     8 authoritative, the rest derived
                              8,587 aliases total, 54 marked ambiguous
```

Four project codes are claimed by two CMS records each. Reported and the first
kept — never guessed, because Tier 0 must remain a lookup.

---

## 3. Tiers

| Tier | Rule | Evidence |
|---|---|---|
| 0 | project code | `(scheme, value)` primary key — a database invariant |
| 1 | exact canonical name, unambiguous | CMS-asserted |
| 2 | exact alias, autolinkable | CMS-asserted or observed gloss |
| 3 | name + corroborating context | CMS metadata agrees |
| 4 | score ≥ threshold **and** margin ≥ threshold | scored |
| 5 | LLM adjudication | **not implemented**, flagged off |

Decisions are `AUTO` / `AMBIGUOUS` / `UNRESOLVED` / `NEW`. **There is no REVIEW
state and no review queue** — this repository has no reviewer workflow, so a case
that would be queued is left `AMBIGUOUS`, which is the safe direction anyway.
`NEW` is never written: the resolver does not mint identities.

### Per-type thresholds

| Type | auto score | auto margin | corroboration required |
|---|---|---|---|
| PERSON | 0.92 | 0.20 | **yes** |
| ORGANIZATION | 0.85 | 0.12 | no |
| PROJECT | 0.85 | 0.12 | no |

---

## 4. Two real bugs the evaluation caught

**A mention corroborated itself.** `resolve_mentions` added every mention's own
normalized name to the shared co-occurrence set, so a candidate always matched a
"co-mention" — its own. PERSON's entire corroboration requirement was silently
satisfied by every mention, and all five PERSON mentions in the Phase 4 gold
chunks auto-linked on name alone. Fixed by excluding a mention from its own
context and by removing `f_co_mention` from the corroborating set entirely: a
candidate is always the same type as its mention, so a co-mention of that name
*is* the name repeating. Cross-entity corroboration ("this person beside their
employer") needs a relationship the claim layer has yet to supply.

**Descriptive project titles bypassed the Phase 4 guard.** Extraction refuses to
match `Steel` or `Summary` in text, but the resolver reached those entities
through their *canonical name*, which consults no alias flag. Added as a veto,
`v_project_name_not_specific`, using the same thresholds. Project codes are
unaffected — they resolve at Tier 0, before scoring.

**A seeding defect:** `& Sharma`, a real `documents_author` value left by a split
on "and", became a PERSON entity. Eight such fragments were seeded. Now rejected
by requiring every token of a name to begin with a letter. This mattered more
than it looks: the seeder decides which identities *exist*, and the resolver
cannot un-merge what the seed already collapsed.

---

## 5. Vetoes

| Veto | Guards against |
|---|---|
| `v_type_conflict` | a corrupted index |
| `v_ambiguous_alias` | a surface claimed by two entities |
| `v_alias_not_autolinkable` | a surface too generic to link on |
| `v_initials_only` | `A.`, `A. K.` — names nobody in particular |
| `v_cms_names_someone_else` | the document says it is by a different person |
| `v_project_name_not_specific` | `Steel`, `Summary` as project identities |

Vetoes beat scores: a perfect name match with contradictory context does not
link.

---

## 6. Declined cases — the evidence the design works

**PERSON (9 of 13 declined):**

| Case | Outcome | Why |
|---|---|---|
| `Shailly Kedia`, no document context | AMBIGUOUS | one seeded name is not proof every mention is that person |
| `Dr Shailly Kedia`, document by someone else | UNRESOLVED | `v_cms_names_someone_else` |
| `A. K.`, `R K` | UNRESOLVED | `v_initials_only` |
| `Sharma`, `Kumar` | UNRESOLVED | bare surnames shared by 17 and 24 people |
| `& Sharma` | UNRESOLVED | no longer seeded |

**PROJECT (4 of 5 declined):** `Steel` and `Summary` refused as descriptive
titles; `2099ZZ99` is well-formed but unseeded; `Environmental status report for
Navi Mumbai` is shared by three CMS nodes, so there is no basis to choose.

**ORGANIZATION (1 of 6):** an invented name with no candidate.

---

## 7. Known limitations

**PERSON entities are name-level, not person-level.** The seeder keys derived
people by normalized name, so two different real people called "Arun Kumar"
became one entity *at seed time*. That is a conflation the resolver cannot see
or undo. It is the honest reading of what the corpus supports — the author facet
gives names, not people — but it means the false-merge rate above measures the
**resolver**, not the seed. Distinguishing same-name people needs evidence the
corpus does not currently carry.

**The evaluation set is 24 cases and I wrote it.** Every case names a real
seeded entity or a real corpus surface, and 14 are `NO_LINK` safety cases, but it
is small and reflects my reading rather than a domain expert's.

**Corroboration for PERSON is currently one signal only** — the document's own
`field_authors`. That is why PERSON's auto-rate is 31%: most mentions appear in
documents whose metadata does not name them.

**Tier 5 (LLM adjudication) is unimplemented.** The ambiguous cases above are
exactly its input, but it stays off until there is reason to spend on it.

---

## 8. Reproducing

```bash
python -m scripts.seed_entities --rebuild        # seed, mine acronyms, mark ambiguity
python -m scripts.eval_entity_resolution         # metrics + safety gate
python -m scripts.eval_entity_resolution --type PERSON
```

## 9. Gate status

```
SAFETY GATE: false-merge rate 0.000 <= 0.000 -> PASS
```

Phase 5 may proceed to Neo4j projection on this evidence, with the limitation in
§7 recorded: the gate measures resolver behaviour, and same-name conflation in
the PERSON seed is a separate, known exposure.
