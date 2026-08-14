# Phase 4 — Entity mention extraction

Mentions only. No entity resolution, no canonical entity ids, no claims, no
graph writes, no retrieval change. All knowledge flags remain off.

---

## 1. What a mention is here

A **sighting**: this span of this chunk looks like a name of this type. The
`Mention` type deliberately has no `entity_id` field, so extraction cannot
invent identity even by accident — deciding which canonical entity a sighting
denotes is resolution's job, in its own phase with its own audit trail.

Every mention carries the requested fields, and offsets are **chunk-relative**:

```
chunk_id  document_id  start_offset  end_offset  surface_text  normalized_text
entity_type  extraction_method  extractor_version  confidence
```

Chunk-relative because there is no single text a document-level offset could
index into: a website body is one blob while a PDF is paginated sections. It is
also the only form that can be *verified* — `surface_text` must equal
`chunk_text[start:end]`, checked for every mention from every stage before it is
returned.

---

## 2. Grounding, as the data actually is

The corpus was inspected before anything was written, and it revised the
starting assumption in one important way.

| Type | CMS grounding | Source |
|---|---|---|
| ORGANIZATION | **strong** | `field_completed_sponsors` (481 distinct), `field_news_source` (396), `field_division` (28) |
| PROJECT | **strong for codes** | `field_completed_project_code` — 932 distinct, format `2004BS22` |
| PROJECT | **weak for titles** | titles are often descriptive, not naming |
| PERSON | **weak** | `people` bundle holds **8** nodes; `field_authors` 226; `documents_author` 975 and noisy |

**ORGANIZATION grounding survived taxonomy removal.** Sponsors, news sources and
divisions are plain text in `raw_meta` — not taxonomy references — so removing
taxonomy did not touch them. This was worth verifying rather than assuming.

**Project codes exist**, answering a question the earlier plans left open. They
make PROJECT the one type with a genuine Tier-0 identifier, matched exactly.

**PERSON is the open-world case, as expected** — 8 authoritative records against
975 noisy author strings (`A.`, `A. K.`, `& Sharma`, `Asha Ram Sihag2`).

Gazetteer built from the live catalog: **3,648 names, 3,609 linkable**
(ORGANIZATION 905, PERSON 975, PROJECT 1,768).

---

## 3. Stages

| # | Method | Source | Confidence |
|---|---|---|---|
| 0 | `cms_field` | names this document's own CMS asserts | 0.98 |
| 1 | `identifier` | project codes, exact pattern | 0.97 |
| 2 | `gazetteer` | names known corpus-wide from CMS fields | 0.85 |
| 3 | `pattern` | honorific+name, org suffix, acronym gloss | 0.60 |
| 4 | `llm` | model proposal, span-verified | 0.50 |

Stage 4 is **off by default** and fires only when a chunk of real prose (≥200
chars) yielded no deterministic mention at all.

---

## 4. Extraction quality by entity type

Measured against `gold_mentions_v1.json` — **8 chunks, 44 mentions, exhaustively
annotated**. Every PERSON/ORGANIZATION/PROJECT mention in each chunk is listed
independent of what the extractor found, which is what makes recall real rather
than circular. Locations, technologies, measurement acronyms and role titles are
deliberately absent: they are outside the closed vocabulary.

Category coverage: acronym glosses, bare acronyms, line-wrapped organization
names, titles and initials, a project code in body text, descriptive project
titles, repeated-boilerplate PDF captions, and negative cases (`BOT`, `CCU`,
`WASP`, `PM2.5`).

### Frozen deterministic v1.1

| Type | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| PERSON | **1.000** | **1.000** | **1.000** | 11 | 0 | 0 |
| PROJECT | **1.000** | **1.000** | **1.000** | 2 | 0 | 0 |
| ORGANIZATION | **0.955** | 0.677 | 0.792 | 21 | 1 | 10 |

Progression during the review (ORGANIZATION): F1 **0.553 → 0.583 → 0.769 → 0.792**.

### Fixes made, each supported by a reviewed example

| Defect | Example | Fix |
|---|---|---|
| Person name ran past the line end | `Mr. Srinivas` + blank line + `Picture No. 24` → `"Srinivas  Picture No"` | person separators forbid newlines |
| Organization truncated at a line wrap | `Hindalco` / `Industries Ltd` split over two lines → `"Industries Ltd"` | one line wrap allowed inside org names |
| Acronym gloss missed across a line | `Institute` then `(TERI)` on the next line | gloss separator allows one wrap |
| Acronym gloss missed after a period | `Developers Ltd. (MLDL)` | optional `.` before the bracket |
| `Group` not an indicator | `International Copper Study Group` | added to the weak list |

The line-wrap change is the largest single win: it removed three false positives
(`Industries Ltd`, `Developers Ltd`, `Water Supply and Sewerage Board`) and six
false negatives at once, because a truncation produces *both* errors from one
name.

### False positives (1)

- `"Storage  JSW Steel Limited"` — a heading (`…Utilisation, and Storage`)
  followed by a name on the next line. **This is the known cost of allowing line
  wraps**, and it also suppresses the `JSW Steel Limited` mention beneath it.
  Left unfixed deliberately: a heading ending in `Storage` followed by `JSW…`,
  and a name split as `Hindalco` / `Industries…`, are structurally identical —
  no rule separates them without a dictionary, and the change is strongly
  net-positive.

### False negatives (10), all ORGANIZATION

| Cause | Examples |
|---|---|
| Bare acronym, no gloss in that chunk | `TERI`, `IOCL`, `KMC`, `CEB` |
| Name carries no structural indicator | `Tata Chemicals`, `JSW Steel`, `Larsen and Toubro`, `L&T` |
| Suppressed by the FP above | `JSW Steel Limited` |

Both causes are deliberate. A bare all-caps pattern would catch the acronyms and
also every unit, standard and heading in the corpus; a bare capitalised-bigram
pattern would catch the indicator-less names and also every place name. Recall
here is the resolution phase's to recover — from an alias index seeded by the
glosses actually observed — not extraction's to guess at.

## 5. Performance

The naive implementation ran every one of 3,609 surfaces against every chunk:

```
before   109.3 ms/chunk   ->  4.5 hours for 149,403 chunks
after     23.0 ms/chunk   ->    57 minutes
```

A first-token containment prefilter cuts the tested surfaces from 3,609 to ~482
per chunk. It is **exact, not approximate** — a surface can only match if its
first token appears literally — and a test asserts the prefiltered set is a
superset of what an exhaustive scan finds.

---

## 6. Storage

MySQL only. Nothing was written to Neo4j.

| Table | Role |
|---|---|
| `documents_entity_mention` | one row per sighting; `UNIQUE(chunk_id, start_offset, end_offset, normalized_text)` |
| `documents_entity_extraction` | cost cache keyed by `content_hash` + extractor version + gazetteer fingerprint |

Idempotency is structural: `INSERT IGNORE` against the unique span key means
re-running a sweep writes the same rows and creates no duplicates — verified end
to end. The cache is keyed on `content_hash` rather than `chunk_id` deliberately:
chunk ids are version-scoped, so re-indexing changes every id while most
paragraphs are untouched, and hashing the text keeps those hits.

---

## 7. Reproducing

```bash
python -m scripts.eval_entity_extraction --sample 40   # draft labels to review
python -m scripts.eval_entity_extraction               # score (refuses if unreviewed)
python -m scripts.eval_entity_extraction --force       # circular numbers, for debugging
```

The evaluator **refuses to report** against unreviewed labels, because the draft
is the extractor's own output and scoring against it is circular — it would
print precision 1.000 and mean nothing.

## 8. Next

Recall needs the draft labels corrected by someone who knows the corpus:
add the mentions the extractor missed, delete the ones it should not have made,
set `"reviewed": true`. PERSON is where that review is worth most — it is the
type with the least grounding and the one whose false merges would do the most
damage in the resolution phase.
