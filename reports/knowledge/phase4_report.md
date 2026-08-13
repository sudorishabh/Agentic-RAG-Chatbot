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

Measured by hand over a 40-chunk real-corpus sample (`gold_mentions_v1.draft.json`),
judging each unique surface. **These are precision estimates on a small sample;
recall is not yet measurable** — that requires the labels a human adds for what
the extractor *missed*, which is exactly what the draft file is for.

| Type | Mentions | Unique | Judged correct | Precision (est.) |
|---|---|---|---|---|
| ORGANIZATION | 36 | 28 | ~24 | **~0.86** |
| PERSON | 25 | 21 | ~20 | **~0.95** |
| PROJECT | 2 | 2 | 2 | **~1.00** (tiny n) |

Precision was raised from a much worse starting point by five fixes, each
prompted by reading the actual output:

| Defect found | Fix | Effect |
|---|---|---|
| Org pattern ran across line breaks, swallowing prose (`"Tata Chemicals\nsuccessfully commissioned a"`) | separators forbid newlines | removed |
| Acronym gloss read every concept as a body (`"Land Degradation and Drought (DLDD)"`, `"...plant (CCU)"`) | expansion must end in an org indicator | removed |
| Gloss middle words unconstrained — swallowed a whole sentence (`"India has the third largest emissions while the European Union (EU)"`) | inner words must be capitalised or closed-list connectors | removed |
| Project titles are descriptive (`"Steel"`, `"Summary"`, `"fly ash"`, `"energy security"`) | titles need ≥3 tokens and ≥12 chars to autolink | PROJECT 9 → 2 |
| Short CMS names collide with nouns (`"Medium"`, `"Water Resources"`, `"the environment"`) | ≤3-token surfaces match case-sensitively | removed |
| Method rank truncated names (publication `"Hindustan"` beat `"Hindustan Copper Ltd"`) | dedupe ranks length before method | corrected |
| Lowercase connectors cut names (`"Resources Institute"` from *The Energy and Resources Institute*) | connectors admitted inside the run | corrected |

### Known remaining limitations

- **Truncated org names** where the head is not adjacent: `"Industries Ltd"`,
  `"Services Limited"`. The head is usually a proper noun the pattern cannot
  reach past punctuation.
- **`"Medium"`** — a real publication in `field_news_source` that also matches
  "Micro, Small and **Medium** Enterprises". Only resolution can settle this.
- **PROJECT recall is near zero from titles.** Deliberate: descriptive titles
  produced almost only false positives, so the code pattern carries the type.
- **Recall is unmeasured for every type.**

---

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
