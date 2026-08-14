# Phase 7.2 — Promotion audit

Measurement only. No change to extraction v1.1, retrieval, claim semantics,
Neo4j or the promotion rule.

**Question:** for how many of the 192 `pi_attested` identities could the row
actually be more than one real person?

**Answer: none observed.** The corpus's failure mode runs the other way.

---

## 1. Result

| Risk band | Count |
|---|---|
| high | **3** |
| medium | 139 |
| low | 50 |
| **total promoted** | **192** |

A 40-row sample was taken, **deliberately biased toward the risky end** — ranked
by near-duplicate names, shared surnames, shared given-name-plus-surname, and
project count. A uniform sample would have been dominated by one-project
three-token names and would have flattered the result.

**Exactly one identity in 192 has a near-duplicate person entity**, and
investigation showed it is not conflation (§3). The other two "high" rows are
high on *blast radius* — 10 and 25 dependent projects — not on any evidence of
covering two people.

---

## 2. What the risk bands mean

The bands rank *observable signals that would betray* a name covering more than
one person. They are not evidence that it does.

| Signal | What it would mean |
|---|---|
| `same_name_candidates` | another person entity with the same bare name — the strongest available signal |
| `prefix_shared` | another person sharing given name **and** surname |
| `surname_shared` | the "Amit Kumar" shape |
| `pi_projects` | blast radius: how many `LED_BY` claims depend on this identity |
| `career_years` | a long span on a crowded surname is the compound risk |
| `authoritative_match` | a CMS person record with the same name — *reduces* risk |

Three-token names are treated as safer than two-token ones even with a crowded
surname, because the middle token is itself discriminating. The sample bears
this out: `Dr Braj Raj Singh` shares a surname with **30** people and carries no
real ambiguity, while `Mr Manish Shrivastava` shares one with a single person and
is the only genuine flag.

---

## 3. The one flagged case — fragmentation, not conflation

```
Dr Manish Kumar Shrivastava   manish kumar shrivastava   provisional   field_authors
Mr Manish Shrivastava         manish shrivastava         pi_attested   field_completed_pi_name
Shrivastava M  K              shrivastava m k            provisional   documents_author
Shrivastava Manish Kumar      shrivastava manish kumar   provisional   documents_author
```

Four entities that are almost certainly **one person**, split by name-order and
middle-name variation. The promoted row has 1 project, 1 code, 1 division and a
0-year span — nothing suggesting it covers two people.

The near-duplicate flag fired on a *fragment of the same person*, not a different
person. **This is the opposite of the failure the promotion rule guards
against.**

---

## 4. The corpus's actual failure mode

Measured across all 1,003 person entities:

| Signal | Count |
|---|---|
| **name-order variant groups** (`adholeya alok` / `alok adholeya`) | **60** |
| names that are a shorter form of another (middle token dropped) | 2 |
| promoted names resembling a fragment of a longer name | 22 of 192 |

The `documents_author` facet writes surname-first while `field_authors` and the
PI fields write given-name-first, so the same person routinely appears twice.

**This is under-merging, and under-merging is a recall problem, not a correctness
one.** Claims about one person attach to several entities; no false claim is
created. Given the standing rule that a false merge is worse than an unresolved
mention, this is the correct direction of error — but it means "who leads what"
will under-report until name-order variants are reconciled.

---

## 5. Verdict

**No material systematic conflation problem.** The promotion rule is not
modified: no individual example justified a change, and the audit found no
pattern that did either.

Two things it did not and could not establish:

- **This is not ground truth.** It ranks signals the corpus exposes. Two real
  people who share a name, pass the surname test and work in one division are
  invisible to every signal here, and would remain so to any measurement this
  corpus supports.
- **The 139 "medium" rows are medium because of name shape**, mostly two tokens
  with a modestly shared surname. That is the population's normal condition, not
  a finding.

Reproduce with:

```bash
python -m scripts.audit_pi_promotions --size 40
```

Full per-row detail, including project codes and divisions, is in
`reports/knowledge/pi_promotion_audit.json`.

**Proceeding to Phase 8 — Neo4j projection.**
