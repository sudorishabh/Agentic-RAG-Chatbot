# Phase 7.1 — PI-aware resolution

Resolution and staging only. **No Neo4j projection, no graph retrieval, no
retrieval changes, extraction v1.1 untouched.** All flags off.

---

## 1. Headline

**`LED_BY` claims: 5 → 594. Zero false merges, zero canonical leaks.**

| Metric | Before | After |
|---|---|---|
| CMS assertions built | 1,780 | 1,942 |
| **staged claims** | 1,064 | **1,653** |
| **`LED_BY`** | **5** | **594** |
| `FUNDED_BY` | 1,059 | 1,059 |
| **rejected PI claims** | **716** | **289** |
| current-state eligible | 145 | 413 |
| **PERSON false-merge rate** | 0.000 | **0.000** |
| **canonical-leak rate** | 0.000 | **0.000** |
| conflicts / disputes | 0 | 0 |
| idempotent re-run | yes | yes |

289 PI claims are still rejected, and that is the design working: those PIs did
not survive the discriminating tests, so they stay provisional.

---

## 2. Why a PI field is stronger evidence — measured, not assumed

| | `documents_author` | PI fields |
|---|---|---|
| distinct names | 975 | **258** |
| on a project carrying an authoritative code | n/a | **257 of 258** |

An author facet accumulates every name printed on anything. A PI field is a
curated CMS assertion about one specific project — smaller, structured, and
anchored to a project the CMS identifies by code.

Two further measurements say the PI population behaves like real individuals
rather than conflated names:

- **No PI name spans more than 30 years** of project start dates (105 span under
  a decade, 44 under two, one under three).
- **129 of 143** PI names with a division recorded stay inside a single division
  area.

If "Arun Kumar" were three different people, wide spans and scattered divisions
are exactly what would show. They do not. That is the empirical basis for
treating PI evidence as stronger — and the same two signals become the tests
that refuse the names where it *does* show.

---

## 3. The promotion rule

**PI membership earns consideration, never eligibility.** A name must then
survive every test:

| # | Test | Failure mode it targets |
|---|---|---|
| 1 | not initials-only | "A K" identifies nobody |
| 2 | ≥2 name tokens | "Neha" is a real PI value |
| 3 | normalized name not marked ambiguous | already known to denote >1 thing |
| 4 | two-token names: surname shared by <5 others | **the "Amit Kumar" guard** (23 other Kumars) |
| 5 | ≥1 project carries an authoritative project code | no authoritative anchor |
| 6 | career span ≤ 35 years | one name covering two people |
| 7 | projects sit in ≤1 division area | one senior person, or two unrelated ones |

Test 4 applies only to two-token names: length is itself discriminating, so
"Alak Chandra Deka" passes where "Amit Kumar" does not.

Promoted names get their own trust level, **`pi_attested`** — claim-eligible,
but never conflated with `authoritative`, which means a CMS person record with a
real UUID. The distinction is preserved so a promotion stays auditable and
reversible, and `apply_promotions` only ever raises rows whose trust is
`provisional`.

### Identity model now

```
ORGANIZATION  derived         eligible=1     887
PERSON        provisional     eligible=0     803
PERSON        pi_attested     eligible=1     192   <- new
PERSON        authoritative   eligible=1       8
PROJECT       authoritative   eligible=1   1,623
```

**192 of 254 considered PI names promoted; 62 refused** — 28 for spanning
multiple divisions, 20 for a crowded surname, the rest for name shape.

### Real decisions, both directions

```
PROMOTED  Dr Shailly Kedia   13 projects, 9 coded, 1 division, 12-year span
PROMOTED  Dr Ritu Mathur     10 projects, 10 coded, 1 division, 15-year span
REFUSED   Dr Debajit Palit   spans 2 division areas
REFUSED   Mr Amit Kumar      surname shared with 23 other people
REFUSED   Dr Anandita Singh  surname shared with 28 others
REFUSED   Dr Alok Adholeya   spans 2 division areas
```

---

## 4. Safety rules — all preserved

| Rule | How |
|---|---|
| 1. Never bypass canonical/claim_eligible | unchanged; validation still re-reads `claim_eligible` from the store |
| 2. PI membership alone never promotes | six further tests must pass; a test asserts stripping the evidence refuses the same name |
| 3. Ambiguous/common names still rejected | tests 3 and 4; 20 names refused on surname alone |
| 4. Candidate cap preserved | `MAX_CANDIDATES` untouched; `S S` still refused as "surface too common" |
| 5. False-merge and leak gates | both **0.000** across 64 cases, 46 of them PERSON |
| 6. Project codes used wherever available | **both** code fields now seeded: identifiers 932 → **1,330** |
| 7. Extraction v1.1 unmodified | `git diff` on `extract.py`/`gazetteer.py` is empty |
| 8. Retrieval unmodified | `git diff` on retrieval/pipeline/cache is empty |
| 9. No Neo4j | no graph import anywhere in the claim or promotion layer |

**Promotion changes entity trust, not resolution thresholds.** A promoted PI
mentioned in prose still needs corroboration before it links — `require_
corroboration` for PERSON is untouched. What promotion unlocks is the *CMS*
claim path, where the CMS itself names the PI.

---

## 5. Evaluation

64 cases, **46 PERSON**, including 12 new PI-specific ones.

```
type             n  FALSE-MERGE   LEAK    prec    auto    prov   ambig   unres
ORGANIZATION    10        0.000  0.000   1.000   0.900   0.000   0.000   0.100
PERSON          46        0.000  0.000   1.000   0.261   0.196   0.217   0.326
PROJECT          8        0.000  0.000   1.000   0.250   0.000   0.000   0.750
```

PERSON auto-resolution rose 0.176 → 0.261; provisional, ambiguous and unresolved
together still account for **74%** of cases.

New PI cases cover: unique PI name + project context, PI + project code,
three-token name, PI with no context (still `NO_CANONICAL` — promotion does not
remove the corroboration requirement), contradictory project context, common
name, common surname, multi-division, initials, PI with organization context, and
no candidate.

### Four stale labels corrected — not gates weakened

Three cases flagged as canonical leaks on the first run. Investigation showed
they were **stale Phase 5.1 expectations**, not real leaks: Shailly Kedia and
Ritu Mathur had been labelled `NO_CANONICAL` while they were only author-facet
names, and are now well-evidenced promotions. The labels were corrected *with
their justification recorded*, and Debajit Palit was re-labelled to test the
multi-division refusal — so the same case now guards the discriminating half of
the rule.

---

## 6. Temporal and conflict behaviour after promotion

Unchanged and still correct.

```
conflicts: examined 594 | groups 594 | disputed 0 | superseded 0
```

594 `LED_BY` claims across 594 distinct `(subject, predicate)` groups — one PI
per project, so no conflicts. `LED_BY` is functional **per project**, not per
person, which is why one person leading 13 projects with overlapping windows
produces no dispute.

Validity comes from `subject_period` as before: completed projects give closed
intervals, ongoing projects give open-ended ones. Current-state eligible claims
rose 145 → 413, all through the same rules.

Re-running the whole pipeline is idempotent: same rows, identical verdict, zero
stale claims.

---

## 7. Side effect: project codes

Seeding both code fields raised identifiers from 932 to **1,330** — the 398
`field_ongoing_project_code` values flagged as a gap in the Phase 7 report.

This also surfaced **21 identifier conflicts** (up from 4): distinct CMS records
claiming the same project code. Reported and the first kept, never guessed —
Tier 0 must stay a lookup. Worth a data-quality look, since a duplicated code is
a CMS error rather than a modelling one.

---

## 8. Tests

```
pytest tests/test_pi_promotion.py -q  ->  20 passed
pytest -q                             ->  1630 passed, 0 failed
```

Covering every requested case, with the refusal tests carrying the weight: PI
membership alone insufficient, crowded surname, initials, single token, ambiguous
name, no coded project, multi-division, implausible career span, plus the trust
model (`pi_attested` is eligible but not authoritative; promotion only ever
raises provisional rows).

---

## 9. Assessment and what remains

**PI evidence can safely promote a substantial minority of people.** 192 of
1,003 person entities are now claim-eligible, up from 8, with no measured
regression in false merges or leaks. 803 remain provisional, which is the honest
answer for names the corpus cannot distinguish.

Remaining limitations:

**1. The rule is heuristic, and its thresholds are judgement calls.** "Surname
shared by fewer than 5" and "at most one division area" are calibrated against
this corpus's shape, not derived from ground truth. No labelled set of
"same-name different people" exists to measure the false-merge rate *within* the
promoted cohort — the 0.000 above measures the resolver against 46 reviewed
cases, not the promotion rule against reality.

**2. A promoted identity is still name-level.** If two real people share a name,
pass the surname test, and both appear as PIs in one division, they are one
entity. The rule reduces that risk; it cannot eliminate it.

**3. 289 PI claims still rejected**, mostly for crowded surnames. Distinguishing
them needs evidence the CMS does not carry — a staff identifier, an email, an
ORCID.

**4. `subject_period` may over-scope `LED_BY`.** A PI inherits the whole project
period, including any time before they took over. Harmless while there is one PI
per project; wrong the moment a project records a succession.

**5. 21 duplicate project codes** are a data-quality issue worth raising with
whoever maintains the CMS.
