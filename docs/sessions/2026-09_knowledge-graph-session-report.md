# Session Report — Knowledge Graph Diagnosis, Date Migration, and Claim-Extraction Backfill

**Period:** 2026-09-01 → 2026-09-04
**Primary session:** `agentic-rag-chatbot-a3`
**Peer sessions involved:** `agentic-rag-chatbot-25`, `agentic-rag-chatbot-e8`, `agentic-rag-chatbot-c5`, `agentic-rag-chatbot-6a`
**Working tree:** shared across all sessions on one machine (not per-session worktrees) — this matters repeatedly below.

---

## 0. How to read this document

The session began as a single question — *"why doesn't the knowledge graph answer my queries?"* — and produced three separate bodies of work:

| Part | Subject | Outcome |
| --- | --- | --- |
| A | Graph architecture & coverage diagnosis | Diagnostic only; produced `GRAPH_DB_REPORT.md` and the findings that drove everything else |
| B | Cross-session date-migration incident | Fully resolved; all three stores consistent |
| C | LLM claim-extraction backfill | Root-caused, fixed, and partially executed (~16% of the backlog) |

Parts B and C each uncovered defects that were fixed in code. Part D lists every commit, Part E every data change, Part F what remains open.

A companion file, `SESSION_LOG_graph_and_date_migration.md` (repo root, committed as `6a775de`), covers Parts A and B in narrative form. This document supersedes it in scope by also covering Part C and the code changes that followed.

---

## Part A — Graph architecture and coverage diagnosis

### A.1 What was asked

Two successive questions: first, *"explain end to end how the graph DB works in this app"*; then, *"why does it mostly not respond, or not have the data?"*

### A.2 Architecture, as documented

Produced `GRAPH_DB_REPORT.md` covering the full picture. The load-bearing facts:

- **Neo4j is a rebuildable projection of MySQL**, never a system of record. Everything it holds is re-derivable, which is why the whole subsystem fails open and why `scripts/project_graph.py --rebuild` is always a valid repair.
- **Write path**: `app/ingestion/graph_sync.py` → `app/knowledge/graph/project.py` → `app/knowledge/graph/writer.py`. All writes are parameterized `MERGE`s on deterministic keys, with labels/relationship types drawn only from a code-side allow-list (`safe_label` / `safe_relationship`), because Cypher cannot parameterize either.
- **Generation-stamped retirement**: each pass stamps `projection_version`; a whole-corpus pass then deletes anything it did *not* re-stamp. This is how a demoted entity or a no-longer-projectable claim leaves the graph without anything having to remember it existed.
- **Read path**: `app/retrieval/graph/` — deterministic routing (`router.py`) → a closed registry of reviewed Cypher templates (`templates.py`, the actual injection defense — no raw Cypher is ever accepted) → read-only execution (`traverse.py`) → hydration of ids into text from Qdrant (`hydrate.py`) → the existing reranker and context builder.
- **Production gating**: `policy.py` adds a capability-class allow-list, a circuit breaker, and a wall-clock budget. `retriever.graph_blocks_for` runs the graph as one leg *alongside* semantic retrieval and merges both, rather than replacing retrieval.

### A.3 Why queries were failing — five findings

Established by live queries against the running stack, not by reading code alone.

1. **Neo4j was not running at all.** Docker daemon was down. Started it; the compose-managed service attached to the pre-existing external `neo4j_data` volume, so no data was lost.

2. **Zero current-state edges, structurally.** 1,348 claims existed; `MATCH ()-[r {current:true}]->()` returned **0**. Traced to `app/knowledge/claims/conflicts.py::is_current_state_eligible`: every one of the corpus's 1,365 dated claims has a `valid_until` in the past (latest 2025-03-31). This is an archive of *completed* projects, so no claim can be "true now." Verified behaviourally: plain-tense questions correctly fall back to unbounded historical templates and answer (31/31 sampled), while "currently"-phrased questions can never return anything.

3. **Only 3 of 7 predicates had any data.** `FUNDED_BY` (957), `LED_BY` (416), `PARTNER_OF` (1). `WORKS_AT`, `MEMBER_OF`, `PARENT_OF`, `HAS_ROLE` were empty. This drove all of Part C.

4. **Entity resolution brittle for realistic phrasing.** Exact canonical names and org acronyms resolved; paraphrased/shortened project titles and — startlingly — **"TERI" itself** did not. Fixed later (§C.6).

5. **Noted in passing:** some `ORGANIZATION` entities have garbled comma-concatenated names (multiple sponsors merged into one). Investigated in §C.5.

---

## Part B — The cross-session date-migration incident

### B.1 How it started

Routine maintenance — refreshing a 12-day-stale projection — failed:

```
pymysql.err.OperationalError: (1054, "Unknown column 'effective_start_date' in 'field list'")
```

The shared working tree held ~130 uncommitted files implementing a rename of `published_at` → `effective_start_date` across ingestion, catalog, retrieval, generation, tests and docs. Ownership was established by messaging all four peer sessions: `agentic-rag-chatbot-25` owned it.

### B.2 The core problem

The date lives in **three stores** — MySQL, Qdrant payloads, Neo4j `Document` nodes — and the migration is only correct if its steps run in one order. Nothing enforced that. Four defects resulted, each of which produced a *plausible number rather than an error*:

| # | Defect | Why it was invisible |
| --- | --- | --- |
| 1 | **Silent no-op projection.** `ensure_state_table()` is additive — it created the new columns *empty*. The graph projection then read `NULL` for every row and, because Cypher **removes** a property set to `NULL`, reported success while writing no dates at all. | Reported `VERIFY: OK` |
| 2 | **A dry run that measured nothing.** `page_moves()` read the new (empty) columns to recover each page's creation stamp, but the copy that fills them ran *after* the move set was computed. On a half-migrated DB every page was silently skipped. | Reported "2,296 documents would change" — actually 0 of 8,507 pages were examined |
| 3 | **Pre-flight refusal that was correct.** 31 moves carried no timezone (a naive MySQL `DATETIME` read back), and 2 would have stored a backwards range. | Looked like a blocker; was a real guard |
| 4 | **Payload clobber.** `apply()` wrote the corrected date under the new key but left the legacy key on the point; `migrate_payload_keys()` then read the legacy name and wrote it back **over** the correction. MySQL and Neo4j would have looked right while Qdrant silently reverted on ~5,150 documents. | No error anywhere |

### B.3 Additional discovery — the recency tier was dead

`agentic-rag-chatbot-e8` found independently, and this session verified against live Qdrant, that `effective_start_date` was populated on **0 of 152,833 points** while `published_at` was on all of them. Consequence: `reranker._recency_scores` read a key that did not exist, hit `if not known: return [_UNKNOWN] * len(candidates)`, and returned a constant. **Tier 4 of the ranking priority was inert in production, silently.**

### B.4 Three interruptions during recovery

| # | Cause | Response |
| --- | --- | --- |
| 1–2 | Client-side zstd allocation error decompressing scroll responses (container using a tenth of its memory — not real pressure) | Removed the scroll from the write path entirely; the catalogue already held the answer |
| 3 | The whole compose stack was stopped and started underneath the run — both containers started 2 ms apart, `RestartCount 0`, `ExitCode 0`, verified via `docker inspect` | Retry backoff widened to 112 s so a restart is sat out; resume hint printed on failure |

A fourth apparent failure — the legacy-key drop "failing" all 5 retries — turned out to be a **slow success**: server logs showed six `HTTP 200` responses at ~60.0 s each, exactly at the client's default 60 s timeout. The retry wrapper had reissued a 150k-point mutation five redundant times, and the resulting load (CPU 1268%, memory 4.5 GiB) was mistaken for a new failure.

### B.5 The recovery design

`--repair-qdrant` was built to be driven by the **catalogue**, not by a move set: MySQL is the authority, every point is reconciled to its row, and the run is idempotent and resumable. It never promotes a legacy value, because for an uncorrected document `published_at` holds the *old* date. Progress was monotonic and durable across all three interruptions — 1,171 → 10,508 → 60,382 → 152,833 points — precisely because every write is idempotent.

### B.6 Final verification

`agentic-rag-chatbot-25` ran a value-by-value cross-store comparison (not a re-run of the same dry-run tool):

| Store | Result |
| --- | --- |
| MySQL | 12,003 documents, 0 undated, 3,850 with a date range, 0 backwards ranges |
| Qdrant | 152,833 points, 0 mismatches vs MySQL, 0 orphans, 0 legacy keys — including the precision-marker contract, not just raw values |
| Neo4j | 973 documents, all dated, 0 disagreeing with MySQL |

**Deliberately left in place:** the legacy MySQL columns (`documents.published_at`, `published_at_source`, `published_at_precision`, `document_published_at`; `documents_date_decision.current_published_at`, `candidate_date`, `candidate_source`) — kept as the only surviving record of the pre-migration state. `--drop-legacy` is ready when wanted and refuses while anything is unmigrated.

---

## Part C — LLM claim-extraction backfill

### C.1 Root cause: extraction was structurally inert

The graph had zero claims for four of seven predicates. The assumption was "the backfill was never run." The reality, found by running the pipeline on a real news article and reading the stage report:

```
"mentions":   skipped: true
"resolution": skipped: true
"claims":     llm_calls: 0
```

**`with_mentions` is hardcoded `False` in `StageOptions`, with no settings flag, and nothing in the automatic paths overrides it.** LLM claim extraction can only name entities it is handed a pre-resolved `entity_id` for — that is its core safety property (`extract_llm.py`: *"It cannot name an entity"*). With mention extraction skipped, it is handed nothing and makes zero calls.

So `CLAIM_EXTRACTION_ENABLED=true` had **never produced a single claim, on any document, ever** — confirmed corpus-wide: across 11,238 `status='ok'` knowledge runs, every bundle except `completed_projects` (which gets claims from the free deterministic CMS-field path) showed exactly **zero** claims staged.

`scripts/knowledge_document.py --with-mentions` was the existing, documented override. Its `--pending N` mode could not reach these documents because they are already marked `"ok"`, not pending — so a real backfill needed an explicit document list.

### C.2 Pilots

| Stage | Documents | LLM calls | Proposed | **Accepted** | Notes |
| --- | --- | --- | --- | --- | --- |
| Dry run 1 | 32 | 33 | 18 | 3 | First evidence the mechanism works at all |
| Dry run 2 | 177 | 229 | 115 | 41 | Broader bundle mix, randomized |
| Real (targeted) | 23 | — | — | 38 | Only documents already known to yield |

A key correction surfaced here: **`claims_built` (proposed) is not `claims_staged` (accepted)**. Validation is a *shape* gate (does the quote exist verbatim, do the types match), not a *truth* gate. Roughly 57% of documents never reached the LLM at all, because no eligible resolved entity was found in them.

### C.3 Defect 1 — `PARENT_OF` (excluded)

Inspecting the 22 staged `PARENT_OF` claims rather than trusting the accepted count:

- **Direction inconsistent on the same fact**: `TERI -> Water Resources` (correct) appeared alongside `Water Resources -> TERI` (backwards).
- **Outright wrong**: `United Nations Department of Economic and Social Affairs -> United Nations` (a sub-body asserted as parent of the UN), `Bureau of Energy Efficiency -> ACC Limited`, `Finance Commission -> Planning Commission`.
- All at **confidence 0.8–1.0**, well above `claim_min_confidence=0.6` — the confidence score does not discriminate good from bad here.

Excluded at extraction (`2ded030`); the 22 bad claims deleted from MySQL.

### C.4 Defect 2 — `PARTNER_OF` (excluded)

Found at 500-document scale. Of 12 claims, roughly 8 were wrong or built on bad data:

- `Lighting a Billion Lives -> TERI` (×2) — TERI's *own* flagship initiative asserted as partnering with TERI.
- `Electricity pricing and the willingness to pay for electricity in India -> TERI` (×3) — a **research paper title** resolved as a `PROJECT`, then asserted to partner with its own publisher.
- `Micropropagation Technology Park -> Sustainable Agriculture` / `-> Renewable Energy Technologies` — both objects are **topic strings mistyped as `entity_type: ORGANIZATION`**, `trust: derived`, no `cms_uuid`, upstream of this extraction.

Excluded at extraction (`5714ddd`); the 12 claims deleted. One further individually-bad `FUNDED_BY` claim was also removed — `ACCCRN -> TERI`, whose quote ("appointed as National Policy Advisor") establishes an advisory role, not funding.

### C.5 Defect 3 — entity typing (fixed at the validation layer)

Investigating why `PARTNER_OF` failed led to `app/knowledge/seed.py`:

```python
_ORG_FIELDS = ("field_completed_sponsors", "field_news_source", "field_division")
```

All three feed the **same** organization-seeding path, with nothing downstream telling them apart. Two distinct bugs:

**Bug 1 — TERI's own divisions typed as external organizations.** `field_division` holds an internal unit name ("Resource Efficiency & Governance", "Water Resources") and is seeded identically to a genuine external sponsor. Exactly the confusion behind both excluded predicates.

Fixed in `app/knowledge/claims/validate.py` (`c32744d`). The tag already existed — `source='field_division'` on exactly 26 of 524 organizations, already loaded into the entity index — nothing downstream had ever checked it. The new rule is deliberately general rather than predicate-name-hardcoded:

```python
if object_type == "ORGANIZATION" and "PERSON" not in predicate.domain:
    # a division is a valid employer/membership target for a PERSON,
    # but not a peer organization for PARENT_OF/PARTNER_OF/FUNDED_BY
```

This preserves the legitimate and useful case (`WORKS_AT` / `MEMBER_OF` pointing at a division) while blocking the category error. It has since fired **3 times in production batches**, catching real cases.

**Bug 2 — comma-joined multi-org strings.** ~30 of 524 organizations merge multiple sponsors into one entity, some severely (`"Adnani Energy Ltd.,Essar Oil Ltd.,Reliance Industries Limited,TERI,…"` — 13 organizations). Verified this is **not** an ingestion-code bug: `_json_values()` correctly splits a real JSON array. For those records, Drupal's `field_completed_sponsors` was itself entered as a single free-text string with embedded commas. **Diagnosed, deliberately not fixed** — a splitting heuristic has real false-positive risk (`"Department of Environment, Government of N.C.T. of Delhi"` is one legitimate name containing a comma).

### C.6 Defect 4 — "TERI" unrecognisable (fixed)

The corpus's flagship organization could not be recognised in any plain question about it. Traced precisely:

1. `extract_mentions("What does TERI do?")` returned **0 mentions**.
2. `gaz.lookup('teri')` returned the `ORGANIZATION` entry as `autolink=False, is_ambiguous=True` — contradicting the alias table, which had it correctly as `autolink=1, is_ambiguous=0`.
3. The gazetteer is built independently of the alias table. `load_rows()` pulls the `documents_author` facet with **zero filtering**, and some TERI reports carry the institution's own name as the byline. That created a spurious single-token `PERSON` entry for "teri".
4. `finalize()` marks ambiguity as `len({e.entity_type for e in bucket}) > 1` — so the bogus `PERSON` entry, *already too weak to autolink on its own* (`_MIN_PERSON_TOKENS = 2`), still disarmed the correct `ORGANIZATION` entry.

**First attempt was wrong and was reverted.** Changing `finalize()` to only count autolink-eligible entries broke `test_a_name_attested_for_two_types_stops_autolinking` — a test protecting a deliberate general safety property (a cross-type collision matters even when one sense is individually weak). Weakening that to fix one case was the wrong trade.

**Correct fix** (`e1e85b0`), in `load_rows()` rather than `finalize()`: filter `documents_author` to ≥2 tokens, mirroring the check `app/knowledge/seed.py` **already applies** when seeding real `PERSON` entities (which is why no phantom `PERSON` entity for "TERI" ever existed in the entity table — only in the gazetteer). This enforces a fact the codebase already established elsewhere rather than inventing a new exception; general cross-type ambiguity is untouched.

Verified end-to-end: `router.route("Who leads TERI?")` changed from *"no entity in the question resolved to a canonical identity"* to *"entity resolved but the question is not relational"*. The resolution bug is gone; the remaining decline is a separate, expected vocabulary gap (no organization-leadership predicate exists). Scope-checked: only 1 entity corpus-wide was affected by this exact pattern — but it is the most important one.

### C.7 Backfill execution

| Batch | Docs | LLM calls | Proposed | Accepted | Notes |
| --- | --- | --- | --- | --- | --- |
| Pilot (real) | 23 | — | — | 38 | `PARENT_OF` found and removed |
| Batch 1 | 500 | 489 | 177 | 41 | `PARTNER_OF` found and removed |
| Batch 2 | 500 | 470 | 130 | 45 | `object_is_internal_division` fired ×2 |
| Batch 3 | 500 | 772 | 183 | 36 | `object_is_internal_division` fired ×1; zero errors |

**Cumulative:** ~1,709 of ~11,000 backlog documents (~16%). Each batch was projected to Neo4j with `VERIFY: OK`.

**Residual noise noted at the time:** `HAS_ROLE` occasionally captures a quote-attribution verb as a role (`"says"`, `"writes"`, `"acknowledges it was a mistake"`) — ~5–10%, consistent across all three batches. Deferred then as materially less severe than the excluded predicates; fixed later in C.9.

### C.8 Why a re-ingest would have wasted its best opportunity

Asked whether re-ingesting the corpus would resolve the outstanding issues. Answer: almost none of them, and one thing was worth fixing *first*.

`with_mentions` was hardcoded `False` in `StageOptions`, and the per-document ingest path (`knowledge_sync.process_after_index`) uses `StageOptions.from_settings()`, which never overrode it. A full re-ingest would therefore have re-processed all ~12,000 documents with claim extraction still inert — paying the whole cost for zero claims. Worse, had the re-ingest cleared the knowledge tables, the 127 claims built by hand would have been destroyed with no automatic way to regenerate them.

Fixed by making it configuration (`knowledge_extract_mentions`, default off, so current behaviour is preserved). With it on, an ordinary sweep builds the claim layer across the whole corpus in one pass instead of ~20 more manual batches. A test now pins that `from_settings` reads it, because the original failure mode was a silent default that produced no error and no claims.

### C.9 `HAS_ROLE` actions (fixed)

The noise pattern from C.7, revisited because it matters far more at 12,000 documents than at 500. All 51 distinct staged literals were reviewed: four were quote-attribution verbs (`says`, `writes`, `provided an explanation`, `acknowledges it was a mistake`) — the model reading the predicate of "…says Dr X" as what Dr X *is*. Nothing else in the gate catches them: the quote is verbatim, types check out, confidence is 0.9–1.0.

Rejected now on the first token against a curated verb list, following `gazetteer._PROSE_MARKERS`'s precedent of a small auditable list over a tagger. First-token-only so a weak but genuine role (`"commentary author"`, `"member of the research team"`) still passes. Validated against all 51 literals: the 4 rejected, no false positives. The four already staged were deleted and the graph re-projected.

### C.10 Bug 2 — joined sponsor values (fixed)

The bug diagnosed in C.5 but deferred there on false-positive risk. Resolved by finding a discriminator in the data rather than guessing at one: **split only on a comma with no space after it**. That is what separates a machine-joined value from a name a person typed, and it holds across the corpus — `"Bennett, Coleman & Co. Limited"` and `"Department of Environment, Government of N.C.T. of Delhi"` keep their comma-space and stay whole, including when embedded *inside* a joined value, where they come back out intact.

Measured over all 524 organizations before any code changed: 70 split into 207 names, zero corporate-form fragments (`Ltd`, `Inc`) produced. Seeding goes **524 → 935 organizations**. Applied in `gazetteer.load_rows` too, which reads the same CMS fields independently and would otherwise still hold the blob as one unmatched surface.

Around nine joined values use comma-space (`"WHO, PHFI"`) and are deliberately left alone: no rule separates them from a legitimate name containing a comma, and a missed split leaves today's behaviour while a wrong split invents an organization.

### C.11 Project titles named in part (fixed)

The brittleness from A.3 finding 4, diagnosed and closed. Gazetteer matching requires the *complete* stored title in the text, so a question naming a real project the ordinary way produced no mention at all and resolution was never reached:

    "Who leads the Yamuna River Water project?"
    stored: "Heavy metal assessment of Yamuna River Water"   -> nothing

Fixed query-side, per the rule `approved_aliases` states for itself: *"widening what ingestion links would change what is asserted; widening what a question may look up changes only what can be found."* A new `partial_titles` module matches a contiguous run of the question against the indexed titles, and the mention it emits carries the project's canonical name so the unchanged resolver still decides identity, trust and every veto.

Two guards, and the second exists because the first was not enough:

* **Uniqueness** — the run must occur in exactly one title. A phrase two projects share identifies neither.
* **Distinctiveness** — the run must contain a token rare across titles. Uniqueness alone admitted `"the project on"`, which occurs in exactly one title and names no project. Measured document frequency separates the cases cleanly (`on` 188, `the` 172, `project` 67, `solar` 38 against `yamuna` 4, `films` 2, `ireda` 1), so the floor sits at 1% of titles.

Measured over the 1,054 claim-eligible projects: **83% of truncated titles now match** (from 0%), every match resolves to the correct project, and 14 generic questions produce none. Verified end to end — the Yamuna question now returns a real claim with three hydrated evidence chunks.

### C.12 `graphify-out` removed

`app/graphify-out/` and the repo-root `graphify-out/` were gitignored artifact directories written by the graphify skill (~9.8 MB, untracked). The one inside `app/` was picked up by `tests/test_architecture.py` as an undeclared package, and its two failures had been carried as the accepted test baseline for over a week.

Both deleted. **The suite is now green: 3,769 passed, 0 failed.** The `.gitignore` entry is kept deliberately — the skill regenerates the directory if run, and the entry is what keeps the artifacts out of git.

---

## Part D — What changed, by file

### D.1 This session's code changes

| Commit | File | Change |
| --- | --- | --- |
| `2ded030` | `app/knowledge/document_pipeline.py` | Exclude `PARENT_OF` from LLM extraction, with evidence in the comment |
| `5714ddd` | `app/knowledge/document_pipeline.py` | Also exclude `PARTNER_OF`; hoist to a module-level `_DISABLED_PREDICATES` frozenset |
| `c32744d` | `app/knowledge/claims/validate.py` | Reject a `field_division`-sourced entity as an org-level claim object |
| `e1e85b0` | `app/knowledge/gazetteer.py` | Filter `documents_author` to ≥2 tokens before it reaches the gazetteer |
| `c6781cc` | `tests/retrieval/understanding/test_shared_prompt.py` | Fix a stale `published_range` mock target |
| `09a8a9a` | `tests/ingestion/dates/` ×3 | Finish the effective-date rename in three test modules (see D.3) |
| `6a775de` | `SESSION_LOG_graph_and_date_migration.md` | Session log (companion to this document) |
| `20e34cf` | `app/config.py`, `app/knowledge/document_pipeline.py` | `knowledge_extract_mentions` setting; `with_mentions` was hardcoded (see C.8) |
| `4a91bc2` | `app/knowledge/claims/validate.py` | Reject a `HAS_ROLE` literal that is really a quote-attribution verb (see C.9) |
| `bbe465e` | `app/knowledge/normalize.py`, `seed.py`, `gazetteer.py` | Split sponsor values naming several organizations (see C.10) |
| `38bc714` | `app/retrieval/understanding/partial_titles.py` (new), `app/retrieval/graph/router.py` | Recognise a project named by part of its title (see C.11) |

### D.2 Commits made on behalf of peer work

The shared tree meant this session committed work authored by other sessions, in reviewed groups:

| Commit | Scope | Author session |
| --- | --- | --- |
| `d97a5ac` | The date-model rename — 126 files across catalog, ingestion, retrieval, knowledge graph, scripts, docs, tests | `-25` |
| `92dd189` | Cross-encoder reranker provider — `config.py`, `reranker.py`, `requirements.txt`, eval/judge scripts, docs, tests | `-e8` |
| `39f2ab1` | Reranker benchmark reports and re-judged gold set (9 files) | `-e8` |

### D.3 A defect introduced and then fixed during committing

`d97a5ac` captured **stale, pre-rename content** in the three files that were `git mv`'d: the rename was staged at mv time, but their later content edits were not. The committed tests still imported `_published_at_for`, which no longer exists — an `ImportError` at collection, which aborts the entire suite.

Caught by `-25` and verified independently here (direct comparison of committed content against `canonical.py`, then `tests/ingestion/dates/` → 487 passed against the corrected content). Fixed in `09a8a9a`. Checked whether the same `git-mv-then-edit` pattern hit anything else: those three were the only renames across all commits.

### D.4 Peer session changes, for the record

**`agentic-rag-chatbot-25`** — owned the `published_at` → `effective_start_date` rename (~130 files). During this session they additionally: fixed the `page_moves()` half-migrated read (`COALESCE(new, legacy)`), fixed naive-datetime timestamps, fixed the backwards-range resolver case, fixed the Qdrant payload-clobber ordering, built `--repair-qdrant` (catalogue-driven, idempotent, resumable, no scroll on the write path), built `--drop-legacy-payload` and `--drop-legacy-graph`, widened retry backoff to 112 s, and wrote up the operational history in `docs/ingestion/bundle-date-capture-plan.md`.

**`agentic-rag-chatbot-e8`** — built the cross-encoder reranker; found the dead recency tier from the Qdrant side; found the `migrate_payload_keys()` clobber by reading the code; corrected their own earlier chunk-id staleness warning once they verified it didn't apply; fixed two of their own failing tests once the ambient `.env` provider was identified as the cause.

**`agentic-rag-chatbot-c5`** and **`-6a`** — confirmed uninvolved; both helped establish ownership of the uncommitted rename.

---

## Part E — Data state

All figures verified live at the close of the session.

### E.1 MySQL

| Metric | Value |
| --- | --- |
| Documents | 12,003 |
| With `effective_start_date` | 12,003 |
| With `effective_end_date` | 3,850 |
| Total claims | 1,495 |
| — from CMS fields (deterministic) | 1,372 |
| — from LLM extraction | **123** (was 0 at session start) |
| Documents contributing LLM claims | 71 |

### E.2 Qdrant

| Metric | Value |
| --- | --- |
| Points | 152,833 |
| `effective_start_date` populated | 152,833 (was **0**) |
| Legacy `published_at` remaining | 0 |

### E.3 Neo4j

| Node / edge | Count |
| --- | --- |
| Claim | 1,469 |
| Alias | 2,793 |
| Entity — Project / Organization / Person | 1,071 / 524 / 131 |
| Document | 1,043 (all dated; 0 legacy `published_at`) |
| Chunk | 79 |

Claims by predicate:

| Predicate | Session start | Now |
| --- | --- | --- |
| `FUNDED_BY` | 957 | 967 |
| `LED_BY` | 416 | 390 |
| `HAS_ROLE` | **0** | **75** |
| `WORKS_AT` | **0** | **19** |
| `MEMBER_OF` | **0** | **18** |
| `PARENT_OF` | 0 | 0 (excluded) |
| `PARTNER_OF` | 1 | 0 (excluded) |

Current-state edges: **3** (`FUNDED_BY`) — the graph's first, where before there were none.

*(The `LED_BY` drop of 26 matches the projection's `claim_entity_not_eligible: 26` — pre-existing entity-eligibility drift, unrelated to this session's work.)*

---

## Part F — Open items

1. **The re-ingest.** The reason C.8 was worth doing first: with `KNOWLEDGE_EXTRACT_MENTIONS=true`, an ordinary sweep builds the claim layer across all ~12,000 documents instead of needing ~20 more manual batches. All four late fixes (C.8–C.11) land at seed or extract time, so a re-ingest is exactly when they take effect — 935 organizations rather than 524, no garbled entities, no junk roles.
2. **No gold query set.** `reports/knowledge/graph_queries_v1.json` does not exist, so `scripts/eval_graph_retrieval.py` cannot run as designed. Every quality judgement in this report is a manual spot-check rather than a repeatable benchmark — which is the weakest part of the work here, given how many of the defects found were things that *looked* right.
3. **Backfill continuation** — ~16% of the backlog processed by hand. Largely moot if the re-ingest runs with mentions enabled.
4. **Legacy MySQL date columns** retained deliberately as the pre-migration record; `--drop-legacy` is ready when wanted.

### Known and accepted, not defects

* **Zero current-state edges** beyond the three from LLM-extracted claims. Inherent to the corpus: every CMS validity window has closed, so "currently" questions can never match. Plain-tense questions correctly read history instead.
* **`PARENT_OF` and `PARTNER_OF` stay excluded** pending the underlying problems in C.3 and C.4. The `field_division` typing behind much of C.4 is fixed (C.5), but neither predicate has been re-measured since.
* **~9 comma-space joined sponsor values** left unsplit (C.10). No rule separates them from a legitimate name containing a comma.

---

## Part G — Practices that mattered

Recorded because they repeatedly changed the outcome, not as general advice.

**Inspect the data, never the accepted-count.** Both excluded predicates passed every structural gate. `PARENT_OF` was caught only by reading the 22 claims; `PARTNER_OF` only by reading all 12. Validation checks shape, not truth.

**A confident number deserves more suspicion than an error.** Four separate cases this session returned a plausible value where the thing being measured had not run: a dry run reporting 2,296 moves having examined 0 of 8,507 pages; a projection reporting `VERIFY: OK` having removed every node's date; an eval scoring a confident 0.000 on a timed-out call; two sequence-length runs scoring identically because one inherited the other's config. The useful question is not *"is this plausible?"* but *"what would this read if the thing it measures hadn't run at all?"*

**Re-derive a number before carrying it.** Every figure from a peer session was reproduced locally before being acted on or relayed. The 2,296 that turned out to be a bug would otherwise have gone into a database.

**Checksum a shared artifact immediately before running it.** The migration script changed four times mid-review; hashes were verified before each `--apply`.

**Don't improvise around another session's in-flight code.** Four separate times — the partial-write stranding, the payload clobber, the repeated crashes, the scoped-diff idea that would have stranded ~11,350 documents — the finding was reported to the owning session with diagnostics rather than patched directly.

**A failing test may be protecting something.** The first "TERI" fix was reverted because it broke a test guarding a deliberate design property. The second fix targeted the bad input instead and left that property intact.

**A peer cannot authorise a write.** Every `--apply` came from the user; none was inferred from a peer message, including where a peer explicitly said to proceed.
