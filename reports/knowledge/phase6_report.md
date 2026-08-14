# Phase 6 — Claim extraction and staging

Extraction, validation and MySQL staging only. **No Neo4j writes, no projection,
no current-state relationships, no graph retrieval, no retrieval changes.** All
knowledge flags remain off.

---

## 1. Result

**915 claims staged from CMS metadata, zero rejections, zero eligibility
violations.**

```
FUNDED_BY   915   (915 distinct projects -> 478 distinct organizations)
```

Verified against the live store:

```sql
claims referencing a NON-claim-eligible entity: 0
```

Staged twice → 915 rows. Idempotent.

---

## 2. Claim model

The Python type is `Assertion`, not `Claim`: `faithfulness._Claim` is an
*answer*-level statement, and `Claim` is reserved for the Neo4j label.

| Group | Fields |
|---|---|
| **identity** (stable) | `subject_entity_id`, `predicate`, `object_entity_id` \| `object_literal`, `document_id`, `chunk_id`, `evidence_kind`, `source_field` |
| **evidence** (mutable) | `quote`, `quote_start`, `quote_end` |
| **interpretation** (mutable) | `valid_from`, `valid_until`, `temporal_basis`, `confidence`, `status` |
| **extraction provenance** | `extraction_method`, `extractor_version`, `vocabulary_version`, `model`, `prompt_version` |

Two evidence kinds, both pointing at something real:

- **`chunk`** — chunk id + verbatim quote + chunk-relative offsets.
- **`cms_field`** — document id + the metadata field. **No quote**: the fact
  lives in a field, not in prose, and inventing a quote would fabricate a span.

---

## 3. Predicate vocabulary

Closed, typed, single-direction. Seven predicates, each grounded in something
this corpus carries.

| Predicate | Domain → Range | Functional |
|---|---|---|
| `FUNDED_BY` | PROJECT → ORGANIZATION | no |
| `PARTNER_OF` | PROJECT → ORGANIZATION | no |
| `LED_BY` | PROJECT → PERSON | **yes** |
| `WORKS_AT` | PERSON → ORGANIZATION | **yes** |
| `MEMBER_OF` | PERSON → ORGANIZATION | no |
| `PARENT_OF` | ORGANIZATION → ORGANIZATION | no |
| `HAS_ROLE` | PERSON → `literal:text` | **yes** |

Domain and range are the type system for claims: `TERI LED_BY Delhi` is not
storable. `functional` is recorded now so conflict detection (a later phase) has
its semantics in one place. Directions are single — two spellings of one fact
would have to be kept consistent forever.

`VOCABULARY_VERSION = "predicates-v1"` is stamped on every assertion.

---

## 4. claim_id design — the part worth arguing about

**Revisited as instructed, and the earlier sketch was wrong.**

That sketch hashed `valid_from`/`valid_until` into the id. Those are
*model-derived interpretation*: re-extracting the same sentence with a better
prompt can legitimately read "since 2019" where it previously read nothing. With
validity in the identity, the result is a **second claim asserting the same
thing from the same evidence** — and no later pass can distinguish that from two
genuinely different assertions. Retries stop being safe, which is the one
property a deterministic id exists to provide.

Identity is therefore **what the source states**, and nothing about how it was
read:

```
claim_id = sha256( evidence_key | subject_id | predicate | object_key )

evidence_key  chunk:<chunk_id>              (extracted)
              cms:<document_id>:<field>     (CMS-derived)
object_key    entity:<id>  |  literal:<normalized>
```

- **Excluded on purpose:** validity, temporal basis, confidence, status, the
  quote and its offsets, the model, the extractor version. Re-extraction
  *updates* a row; a better prompt shows up as a changed field, never a fork.
- **Included on purpose:** the chunk. Two chunks asserting the same fact are two
  claims — independent evidence, and collapsing them would lose a corroboration.
- `object_key` is kind-prefixed so an entity id and a literal that share a
  string cannot collide.

Validation **recomputes the id last**, from corrected content, so a claim can
never be stored under an id that disagrees with what it says.

---

## 5. Eligibility rules

The gate Phase 5.1 exists to feed. Two checks, in different places, on purpose:

**The decision, not the id.** Extraction is handed `Decision` objects and reads
`decision.canonical` (which is `AUTO` and nothing else) plus
`decision.claim_eligible`. There is no path accepting a bare `entity_id` — a
provisional row has one too.

**The store, again, at validation.** A decision can be older than the entity's
current trust level, so `claim_eligible` is re-read from the store before
staging. A demotion takes effect without rewriting old decisions.

Consequences for this corpus:

- **PERSON claims are limited to the 8 authoritative people.** The 915
  provisional person rows are names, not people; a claim about a name would
  assert something never established.
- The model only ever *sees* eligible entities, so a hostile passage cannot name
  a provisional person as a subject.

---

## 6. Evidence validation rules

Applied in order — cheapest and most fundamental first.

| Check | Rejection code |
|---|---|
| predicate in the closed vocabulary | `unknown_predicate` |
| subject exists | `unknown_subject` |
| **subject claim-eligible in the store** | `subject_not_claim_eligible` |
| object exists (entity-valued) | `unknown_object` |
| **object claim-eligible** | `object_not_claim_eligible` |
| object shape matches the predicate | `missing_object_entity`, `object_entity_on_literal_predicate`, `object_literal_on_entity_predicate`, `missing_object_literal` |
| subject/object types accepted by the predicate | `type_violation` |
| not a self-reference | `self_reference` |
| document present | `missing_document` |
| chunk present and held by us | `missing_chunk`, `chunk_not_found` |
| quote present, 10–600 chars | `missing_quote`, `quote_length` |
| **quote appears verbatim; offsets recomputed** | `quote_not_in_chunk` |
| CMS claims carry no quote | `cms_claim_with_quote`, `missing_source_field` |
| dates parse and are 1900 ≤ y ≤ now+5 | `bad_valid_from`, `bad_valid_until` |
| `valid_from ≤ valid_until` | `inverted_validity` |
| confidence in range and above the floor | `confidence_out_of_range`, `low_confidence` |

**Model-supplied offsets are never used.** The application locates the quote and
computes them, matching across a line wrap (PDFs break mid-sentence). The
proposal schema has no offset field at all — a test asserts that, which is the
strongest available form of "do not trust model offsets".

Rejections are recorded in `documents_assertion_rejection` with their code, so
"the model produced fewer claims today" is diagnosable.

---

## 7. LLM extraction — untrusted input, flagged off

`claim_extraction_enabled=False`. Five properties, none depending on the model
behaving well:

1. **Cannot name an entity** — subject/object must be ids from the supplied
   eligible list.
2. **Cannot invent a predicate** — outside the vocabulary is dropped; there is
   no vocabulary-extension path a model can trigger.
3. **Cannot cite absent text** — verbatim quote required, offsets recomputed.
4. **Cannot reach beyond its chunk** — per-chunk, passed as delimited data with
   a system prompt saying document text is data, never instructions.
5. **Cannot write** — it returns a proposal; validation and staging are code.

Budgeted by `claim_llm_max_calls_per_run` (200) and `claim_min_confidence`
(0.6). The deterministic CMS extractor needs no flag: it costs nothing.

---

## 8. Storage

| Table | Role |
|---|---|
| `documents_assertion` | staged claims, PK `claim_id` |
| `documents_assertion_rejection` | why assertions were refused, append-only |

Upsert on `claim_id` updates interpretation while preserving identity and
`created_at`. Staging only — projection is a separate pass, so a graph outage
costs a retry rather than a re-extraction, and no transaction spans two
databases.

---

## 9. Tests

```
pytest tests/test_claim_extraction.py -q  ->  59 passed
pytest -q                                 ->  1558 passed, 0 failed
```

Covering every case requested: provisional PERSON rejected (at both the gate and
validation), canonical PERSON accepted, authoritative ORGANIZATION accepted,
invalid entity/predicate/quote/offsets rejected, temporal parsing, `claim_id`
stability under re-interpretation, deterministic reprocessing, duplicate
handling, and prompt-injection-like source text.

Two bugs were found by running against real data:

- `load_index()` did not select `cms_uuid`, so the CMS extractor produced **zero**
  claims silently. Fixed.
- One test expectation of mine was wrong (`missing_object_entity` is the correct,
  more specific code); the test was corrected rather than the code.

---

## 10. Unresolved architectural questions

**1. PERSON claims are nearly unreachable.** Only 8 people are claim-eligible,
so `LED_BY`, `WORKS_AT`, `MEMBER_OF` and `HAS_ROLE` can say almost nothing about
this corpus. The vocabulary is built and tested, but until provisional people
can be promoted, four of seven predicates are close to inert. **Promotion needs
a decision**: what evidence would justify treating a name as a person?

**2. `field_completed_sponsors` — FUNDED_BY or PARTNER_OF?** All 915 claims read
the field as funding. "Sponsor" usually means funder, but some listed
organizations may be delivery partners. The field name is the only evidence, and
one reading had to be chosen.

**3. Temporal basis is always `unknown` today.** CMS claims carry no dates, and
`valid_from` inference from `published_at` is deliberately not implemented —
it would assert a validity window the source never stated. Whether document-date
inference is wanted is a product decision.

**4. No conflict detection yet.** `functional` is recorded on predicates but
nothing acts on it. Two `LED_BY` claims with overlapping validity would both sit
`active`. That is the next phase's work.

**5. No review queue, deliberately.** Rejections are recorded and counted, not
queued, because this repository has no reviewer workflow.

**6. Second-order provenance for CMS claims.** A `cms_field` claim's evidence is
a document and a field name. If that field is later edited, the claim's evidence
silently changes meaning. Chunk-based claims do not have this problem, because a
re-chunk changes `chunk_id` and therefore `claim_id`.
