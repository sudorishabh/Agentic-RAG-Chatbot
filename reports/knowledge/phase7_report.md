# Phase 7 — Claim semantics, temporal normalization, conflict detection

Semantics and staging only. **No Neo4j projection, no graph retrieval, no
retrieval changes.** All flags off.

Phase 6 invariants preserved: `claim_id` is still
`sha256(evidence_key | subject_id | predicate | object_key)`; validity,
confidence, status, quote, offsets and versions remain outside it; claims still
reach entities only through `Decision.canonical` + `claim_eligible`; provisional
PERSON entities still cannot be subjects or objects; evidence spans are still
chunk-relative and model offsets still untrusted. Tests re-assert each.

---

## 1. Pipeline result

```
built 1,780  ->  accepted 1,064  ->  staged 1,064
rejections   {'object_not_claim_eligible': 716}
predicates   {'FUNDED_BY': 1059, 'LED_BY': 5}
statuses     {'active': 1064}
bases        {'subject_period': 1062, 'unknown': 2}
conflicts    examined 5, groups 5, disputed 0, superseded 0
current-state eligible  145
```

**The 716 rejections are the eligibility gate working.** They are principal
investigators whose PERSON identity is *provisional* — a name from the author
facet, not an established person. Phase 5.1's guarantee reaches the claim layer
exactly as designed: only 5 `LED_BY` claims survive, all naming Dr Vibha Dhawan,
one of the 8 authoritative people.

Re-running the whole pipeline is idempotent: same 1,064 rows, identical conflict
verdict, zero stale claims.

---

## 2. New CMS sources found

Inspecting project nodes before implementing turned up four fields the Phase 6
extractor was not using:

| Field | Count | Use |
|---|---|---|
| `field_ongoing_sponsors` | 377 | `FUNDED_BY` — was being missed entirely |
| `field_completed_pi_name` | 497 | `LED_BY` |
| `field_ongoing_pi_name` | 414 | `LED_BY` |
| `field_completed_start_date` / `_end_date` | 1,030 each | closed validity intervals |
| `field_ongoing_start_date` | 593 | open-ended validity |

`field_ongoing_stakeholders` (517) is **deliberately unused**: its values are
audience categories — "Policy Makers", "Businesses", "Academicians" — not
organizations, so no relationship can be built from it.

---

## 3. (A) Temporal normalization

### Three clocks, kept apart

`valid_from`/`valid_until` = true in the world · `asserted_at` = when the system
learned it · `created_at` = when the row was written. A 2024 article describing a
2019 partnership does not make the partnership start in 2024.

### "Present" is open-ended, not forever

| Shape | Meaning |
|---|---|
| `valid_from` set, `valid_until` **None** | **open-ended** — true from then on, no stated end |
| both **None** | no temporal information at all |

The two are distinguishable, and conflict detection treats them differently: an
open-ended window overlaps everything after its start; an **unknown window
overlaps nothing**, because treating "undated" as "always" would make every
undated claim conflict with every other.

The corpus makes this concrete — a completed project has start *and* end (closed
interval); an ongoing project has start and **no end**, which is the corpus's own
way of saying "current".

### Explicit source language

Parses `since 2019`, `from March 2019`, `until 2021`, `2019-2021`,
`2019 to present`, `between 2015 and 2018`, `w.e.f. 2020-04-01`.

Deliberately **refuses** to read a bare year as validity: this corpus is full of
years that are citations, measurements and targets, so `"published in 2024"` and
`"reached 2030 targets"` yield nothing. An inverted phrase is refused rather than
reordered — reordering would invent a reading the source did not have.

### The one approved inference

| Basis | Meaning | Used |
|---|---|---|
| `stated` | the source states the relationship's own dates | yes |
| `subject_period` | **the project's own CMS-stated period scopes relationships to it** | yes |
| `document` | inferred from `published_at` | **never** |
| `unknown` | nothing known | yes |

`subject_period` is the explicit, documented rule you asked for, and it is kept
as its own basis so nothing mistakes it for the source having dated the
relationship. `document` exists as a constant and is used nowhere — it is the
inference that turns "reported in 2024" into "true from 2024".

### Real examples

```
open-ended (ongoing project = current)
  Exploiting beneficial algal-microbial…  --FUNDED_BY--> Department of Biotechnology
      [2020-02-04 .. present]  subject_period

closed (completed project = history)
  Evaluation of micro credit scheme…      --FUNDED_BY--> Karnataka Evaluation Authority
      [2016-02-22 .. 2016-10-22]
```

---

## 4. (B) Conflict detection

Mechanical, driven by `Predicate.functional`. Only **active** claims of
**functional** predicates are examined — a non-functional predicate cannot
conflict on multiplicity, and a project having many funders is several facts, not
a contradiction.

**Nothing is ever discarded.** A conflict changes *status*; the claim, its
evidence and its window are untouched. So history stays queryable, and the system
under-reports rather than mis-reports.

### The ladder

1. **Non-overlapping → not a conflict.** Bob until 2026-03, then Alice from
   2026-03, is a succession. Both stay `active`. Adjacent intervals do not
   overlap: the boundary belongs to the later claim.
2. **Overlapping, stronger basis wins** → weaker becomes `superseded`.
3. **Overlapping, equal basis, later start wins** → earlier becomes `superseded`.
4. **Overlapping, equal basis, no ordering** → **both `disputed`**, neither
   projects.

An already-disputed claim is never downgraded to superseded: an unresolved
contradiction is not cured by a third claim outranking one side of it.

**On this corpus: 5 functional claims, 5 groups, 0 conflicts.** Each project has
one PI. Notably, Dr Vibha Dhawan leads several projects with *overlapping*
windows — no conflict, because grouping is by `(subject, predicate)` and each
project is a different subject. `LED_BY` is functional per project, not per
person.

---

## 5. (C) Supersession

A claim supersedes another when both are active, functional, same subject and
predicate, **different objects**, **overlapping validity**, and one of: a
stronger temporal basis, or a strictly later stated start.

The superseded claim keeps its status, window, object, quote and row. It is
history, and a test asserts it stays queryable.

Links live in `documents_assertion_link` (`from`, `to`, `kind`, `reason`) rather
than as columns — a claim may contradict several others, and a contradiction is
worth inspecting on its own rather than being implied by two status flags.

---

## 6. (D) Current-state eligibility

A single predicate, `is_current_state_eligible`, so the projection phase has
nothing to decide. Five conditions:

1. `status == active` — disputed must not become a confident edge; superseded
   and retracted are history
2. basis ∈ {`stated`, `subject_period`} — undated is not evidence about *now*,
   and `document` was never approved
3. the window is open at `as_of`
4. entity-valued predicates have an entity object
5. the predicate is still in the vocabulary

**Necessary, not sufficient**: projection must additionally re-check that both
entities are still claim-eligible, which only the entity store can answer.

**145 of 1,064 claims qualify today** — the rest are completed projects whose
period has ended. That ratio is the point: most of what the corpus states is
history.

---

## 7. (E) CMS-field provenance — reviewed

**Content hashing is not required for identity integrity, and adding it would be
the wrong fix.**

The field's value already reaches `claim_id` through the **object**. Editing a
sponsor from Org A to Org B produces a *different* `claim_id`, so an existing
claim's meaning cannot silently change. A test asserts this.

What an edit *can* do is leave the old claim behind, still asserting a sponsor
that was corrected away. The correct treatment is **retraction**, not hashing:
`stale_claim_ids()` finds staged `cms_field` claims for a (document, field) the
current pass covered but no longer produces, and they are marked `retracted` —
never deleted, because the claim was true of the source as it stood.

A field the pass never looked at is not judged stale, which a test pins.

Two columns were added for **explainability only**, explicitly outside identity:
`source_value` (the literal CMS value that produced the claim) and
`source_value_hash`. They answer "why does the system believe this?" and let a
re-extraction tell an edited value from a removed one.

---

## 8. (F) Predicate semantics — reviewed

| Predicate | Domain → Range | Functional | Temporal behaviour | CMS source |
|---|---|---|---|---|
| `FUNDED_BY` | PROJECT → ORGANIZATION | no | scoped by project period | **1,059 claims** |
| `PARTNER_OF` | PROJECT → ORGANIZATION | no | scoped by project period | none — see §9 |
| `LED_BY` | PROJECT → PERSON | **yes** | succession expected | **5 claims** |
| `WORKS_AT` | PERSON → ORGANIZATION | **yes** | succession expected | none |
| `MEMBER_OF` | PERSON → ORGANIZATION | no | multiple concurrent | none |
| `PARENT_OF` | ORGANIZATION → ORGANIZATION | no | rarely dated | none |
| `HAS_ROLE` | PERSON → `literal:text` | **yes** | succession expected | none |

`LED_BY` is functional **per project**, not per person: one project has one
leader at a time; one person may lead many projects. Confirmed against real data.

`HAS_ROLE` is the only literal-valued predicate. Roles ("Senior Director") denote
no thing of their own, so making them entities would create thousands of
identities nothing could resolve.

---

## 9. (G) `field_completed_sponsors` → FUNDED_BY — decided

**Keeping `FUNDED_BY`.** The evidence:

1,292 sponsor values, 661 distinct. The most frequent are unambiguously funding
bodies:

```
64  Department of Biotechnology          21  The World Bank
25  Ministry of New and Renewable Energy 21  Ministry of Environment and Forests
22  European Commission                  18  Department of Science & Technology
17  Asian Development Bank               16  Ministry of External Affairs
15  United Nations Environment Programme 15  Maharashtra Pollution Control Board
```

50% match funder vocabulary (ministry, department, fund, bank, commission,
grant); 21% are companies, and a company sponsoring a TERI project is normally
paying for it.

**Should some be `PARTNER_OF`?** There is no evidence to split on. The CMS has
**no partner field** — the nearest candidate, `field_ongoing_stakeholders`, holds
audience categories, not organizations. Splitting would require reading intent
from the organization's name, which is exactly the kind of inference this layer
refuses elsewhere.

`PARTNER_OF` therefore stays in the vocabulary with **no CMS source**, available
for text extraction where a passage says "in partnership with".

---

## 10. Tests

```
pytest tests/test_claim_semantics.py -q   ->  52 passed
pytest tests/test_claim_extraction.py -q  ->  59 passed
pytest -q                                 ->  1610 passed, 0 failed
```

Every required case: non-overlapping succession, overlapping conflict,
non-functional multiplicity, superseded history queryable, invalid ranges,
present/current handling, source-field edit provenance, dispute blocking
projection, `claim_id` stability under reinterpretation, changed evidence
yielding a distinct claim, no provisional entity ever a claim, full idempotency.

**One real bug found by running against live data:** MySQL returns `DATE` columns
as `datetime.date` while extraction produces strings, and every comparison here is
lexical — the two met in conflict detection and raised. Fixed with a single
coercion point, `temporal.as_iso`, with a test.

---

## 11. Open questions

**1. PERSON claims remain nearly unreachable.** 716 of 1,780 CMS claims were
rejected because their PI is provisional. That is correct, but it means `LED_BY`
captures 5 of ~900 real project-leadership facts. **Promotion still needs a
decision:** what evidence justifies treating an author-facet name as a person?
The PI field itself is arguably that evidence — a CMS field naming a project's
principal investigator is a stronger assertion than an author string — and
promoting PI names specifically would unlock ~900 claims. Not done here because
it changes the entity layer.

**2. `field_ongoing_project_code` (420 values) is not seeded.** Phase 5 only used
`field_completed_project_code`. That is 420 missing Tier-0 identifiers. An
entity-layer fix, noted rather than made.

**3. No conflicts exist to observe.** Detection is tested exhaustively against
constructed cases, but the corpus currently produces none, so the ladder is
unexercised by real data. It will matter once text extraction adds claims that
compete with CMS ones.

**4. `subject_period` may be too generous for `LED_BY`.** A PI is recorded once
per project, so the claim inherits the whole project period — including any time
before that person took over. Fine while there is one PI per project; wrong the
moment a project records a succession.

**5. Retraction is implemented but never triggered.** `stale_claim_ids` returns
zero on an unchanged corpus. It needs a real CMS edit to exercise end to end.
