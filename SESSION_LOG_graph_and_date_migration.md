# Session Log: Graph DB Diagnosis & Cross-Session Date Migration

**Date:** 2026-09-01 to 2026-09-03
**This session:** `agentic-rag-chatbot-a3`
**Peer sessions involved:** `agentic-rag-chatbot-25` (owns the `published_at` → `effective_start_date` rename), `agentic-rag-chatbot-e8` (building a cross-encoder reranker), `agentic-rag-chatbot-c5` (docs/CI work, uninvolved), `agentic-rag-chatbot-6a` (uninvolved)

This log covers two connected pieces of work: (1) diagnosing why the Neo4j knowledge graph wasn't answering queries, and (2) an unplanned, multi-session incident response to a partially-applied database migration that the graph diagnosis exposed.

---

## Part 1 — Why the graph doesn't answer queries

### Starting point

The user reported that graph-backed retrieval "mostly does not respond or doesn't have that data." An earlier turn in this session had already produced an architecture report (`GRAPH_DB_REPORT.md`) covering how the Neo4j knowledge graph is built and queried. This phase diagnosed *why coverage was thin*, using the `code-review-graph` MCP tool to navigate the codebase and live queries against the running stack to get real numbers instead of guessing.

### Findings, in order of impact

1. **Neo4j was not running at all.** Docker daemon was down, no `neo4j` container up. This alone would explain "no response." Fixed by starting Docker Desktop and bringing up the compose-managed `neo4j` service, which attaches to the pre-existing external `neo4j_data` volume (so no data was lost — an old hand-started container with the same name had to be removed first, per the compose file's own documented instructions).

2. **Zero current-state edges, always.** Live query: 1,348 claims in the graph, but `MATCH ()-[r {current:true}]->() RETURN count(r)` returned **0**. Root cause traced through `app/knowledge/claims/conflicts.py::is_current_state_eligible`: every one of the corpus's 1,365 dated claims has a `valid_until` in the past (latest: 2025-03-31) — this is a historical archive of *completed* projects, not a live registry. Structurally, no claim can ever be "current" as of today. Verified live: a plain-tense question ("who leads X") correctly falls back to an unbounded historical template and answers (31/31 sampled questions answered correctly); the same question phrased with "currently" always returns zero rows, because the current-state edge for it can never exist. This is largely already-mitigated behavior (the routing planner defaults ambiguous tense to historical), but explicit "currently/now" phrasing is a dead end by design of the corpus, not a bug.

3. **Only 3 of 7 predicates have any data.** `FUNDED_BY` (957), `LED_BY` (416), `PARTNER_OF` (1) are populated; `WORKS_AT`, `MEMBER_OF`, `PARENT_OF`, `HAS_ROLE` have zero claims. The deterministic CMS-field extractor evidently only mines sponsor/PI fields. LLM-based claim extraction (`CLAIM_EXTRACTION_ENABLED=true` in `.env`) only runs **per-document during ingest** (`app/knowledge/document_pipeline.py`), not as a corpus-wide backfill over already-ingested documents — so most of the corpus was never LLM-mined for the other predicate types.

4. **Entity resolution is brittle for realistic phrasing.** Exact canonical names and short org acronyms ("IREDA") resolved correctly; shortened/paraphrased project titles, and even "TERI" itself (the organization behind the whole corpus), failed to resolve to a canonical entity. This is a gazetteer/resolver coverage gap, not a routing or traversal problem — the underlying query engine works fine once an entity resolves.

5. **Found in passing:** some Organization entities have garbled, comma-concatenated canonical names (multiple CMS sponsor names merged into one entity) — a likely CMS-field parsing bug, noted but not investigated further.

### What was NOT yet done

- Backfilling LLM claim extraction across the existing corpus (to populate the four empty predicates) — scoped as a future step, not executed.
- Expanding the predicate/entity vocabulary — deferred until backfill results show what's actually missing.
- A full `scripts/eval_graph_retrieval.py` run — blocked because no gold query set (`reports/knowledge/graph_queries_v1.json`) exists in the repo; a self-made live sample (31 questions) was used instead.

---

## Part 2 — The detour: an in-flight rename collided with graph maintenance

While attempting routine graph maintenance (refreshing a 12-day-stale projection with `scripts/project_graph.py`), the run failed:

```
pymysql.err.OperationalError: (1054, "Unknown column 'effective_start_date' in 'field list'")
```

Investigation found the working tree had **~100–130 uncommitted file changes** implementing a rename of `published_at` → `effective_start_date` across `app/catalog`, `app/ingestion`, `app/retrieval`, `app/generation`, tests, and docs. This working tree is **shared across multiple Claude Code sessions running on the same machine** (not per-session isolated), so this wasn't something this session created.

### Identifying ownership

Using `ListAgents` and `SendMessage`, four peer sessions were queried. Three (`6a`, `c5`, initially) had nothing to do with it. `agentic-rag-chatbot-25` confirmed ownership: they were mid-refactor, tests green on their side (3727–3744 passing throughout, only 2 pre-existing unrelated failures), no concurrent writes to MySQL/Neo4j/Qdrant from their side at any point.

The rename's migration DDL already existed in `app/catalog/schema.py` (`ensure_state_table()`, using the codebase's standard idempotent `_ensure_column` pattern) — it just hadn't been *run* against the live MySQL database. This was applied (additive, non-destructive, doesn't touch `published_at`), which unblocked the graph projection temporarily — but this is where the real problem surfaced.

---

## Part 3 — The three-way incident: MySQL, Neo4j, and Qdrant fall out of sync

This became a genuine multi-session incident response. The pattern throughout: **a peer proposes a fix, I independently re-verify every claim (file hashes, dry-run numbers, direct database queries) before acting, nothing is written without explicit user approval, and every finding is relayed back to the owning peer.**

### Round 1 — The projection silently wrote nothing

Running the graph projection after the MySQL migration reported `VERIFY: OK`, but this was misleading: the projector reads `effective_start_date` from MySQL (still all `NULL` at that point) and `SET`s it in Cypher — and in Cypher, **setting a property to `NULL` deletes it**. So the projection "succeeded" while writing zero real dates to Neo4j's 973 Document nodes. This wasn't caught until much later, once the underlying data was actually fixed.

### Round 2 — Diagnosing the real gap (`agentic-rag-chatbot-25` and `agentic-rag-chatbot-e8`)

Both peers independently investigated and reported, and every claim was independently re-verified against the live databases before being acted on:

- **MySQL**: 12,003 documents, `effective_start_date` populated on 0, `published_at` populated on all 12,003 (confirmed).
- **Neo4j**: 973 Document nodes, same pattern (confirmed).
- **Qdrant**: `effective_start_date` populated on 0/152,833 points, `published_at` on all 152,833 (confirmed — my first check used the wrong filter condition (`IsNullCondition`, which only matches explicit null, not a missing key) and wrongly reported "populated"; corrected with `IsEmptyCondition` and a raw payload sample).

`agentic-rag-chatbot-e8` additionally found that `reranker._recency_scores` was silently returning a constant tier for every candidate, because it reads a payload key (`effective_start_date`) that didn't exist anywhere in the live index — the recency ranking tier had been dead the whole time, with no error.

### Round 3 — The fix, and the bugs found while verifying it

`agentic-rag-chatbot-25` built `scripts/backfill_bundle_dates.py` (a bundle-date resolution + migration script). Every iteration below followed the same protocol: peer proposes → I verify file hash (SHA-256, first 16 hex chars) → I independently re-run the dry run and compare numbers → I bring the result to the user for explicit approval → only then do I write.

1. **First dry run**: reported 2,296 documents would change. **Bug found by `-25` themselves**: `created_stamps()`/`page_moves()` read the new (empty) columns to recover page creation stamps, so all 8,507 website pages were silently skipped — the real number was masked. Fixed; corrected dry run: **5,154** documents (later refined to **5,152** after two more small bugs — an inverted timezone-naive datetime handling issue, and two `end_without_start` edge cases). Each correction was independently re-verified by me before re-approval.

2. **First `--apply` attempt**: refused cleanly by the script's own preflight guard (a timezone-less value, 2 backwards date ranges) — **no writes occurred**, confirmed by direct MySQL query.

3. **Bug found by `agentic-rag-chatbot-e8`, independently, by reading the code**: `apply()` writes the corrected `effective_start_date` to Qdrant but never deletes the legacy `published_at` key. `migrate_payload_keys()` (meant to rename legacy keys) then runs *after* `apply()`, sees `published_at` still present, and unconditionally overwrites the just-corrected value with the stale one — silently reverting every correction in Qdrant while MySQL stayed correct. Verified line-by-line against the actual code before relaying to `-25`. Fixed by making the key migration order-independent (only carry a legacy value where the new key is still empty).

4. **Second `--apply` attempt (`--expect 5152`)**: got through ~5,500–5,700 documents, then crashed with `zstd decompressor: Allocation error: not enough memory`. Diagnosed as a partial, two-store write: **MySQL ended up fully correct (12,003/12,003) while Qdrant was stuck at 1,171/152,833.** Identified and reported the dangerous failure mode: a naive retry would recompute "0 moves needed" for the already-corrected documents (since MySQL already matched target), permanently stranding ~4,500 documents' Qdrant payloads with no error ever surfacing. **Did not attempt a fix myself** — flagged this to `-25` explicitly as needing the script owner, not an improvisation.

5. **`-25` built `--repair-qdrant`**: a separate, idempotent, MySQL-is-the-authority reconciliation path (not the original move-set logic). Verified hash and dry run (`already_correct 1171`, `points_needing_a_date_write 151662`) before approval.

6. **Repair attempt #1**: crashed again on the same zstd error, but *earlier* this time (first flush, `already_correct` had only reached what the first run left it at). Gathered diagnostics `-25` explicitly asked for (container had 10x memory headroom — 1.045GiB/11.42GiB — ruling out real memory pressure; installed library versions; server logs showing successful scroll responses immediately before the failure) rather than guessing at a fix.

7. **`-25` rewrote the write path** to eliminate scrolling entirely on the write side (per-document `set_payload`, batched precision-key cleanup, one final legacy-key drop, wrapped in retry-with-backoff, resumable via `--start-after`). Verified hash and dry run again.

8. **Repair attempt #2**: got much further (5,500+/12,003) before failing with `httpx.RemoteProtocolError: Server disconnected without sending a response` — a different failure class. Investigation (`docker inspect`) showed the Qdrant container had **actually restarted** (`OOMKilled: false`, `ExitCode: 0`, fresh startup banner in logs) — not a crash, a clean restart. `-25` cross-checked this against the Neo4j container's timestamps: both started **2ms apart**, with `created` dates six weeks apart, `RestartCount: 0` on both — proving something external restarted the whole Docker stack mid-write, not a Qdrant failure. Cause never identified (no Docker events found in the window); flagged as an operational risk for all sessions sharing this machine, not something fixable in application code.

9. **Resume**: `-25` widened retry backoff to survive a ~20–40s stack restart (2s/5s/15s/30s/60s = 112s total) and printed the exact resume command. Verified and ran `--repair-qdrant --apply --start-after <last-confirmed-id>` — **completed successfully**, 6,503 remaining documents written. Verified with a fresh dry run: `already_correct 152833/152833`, `points_needing_a_date_write 0`. `-25` independently cross-verified by comparing every Qdrant payload value directly against its MySQL row (not just re-running the same dry-run tool): `exact_match 152833`, `MISMATCH 0`, `orphan 0` — including the precision-marker contract, not just raw values.

10. **Graph re-projection**: re-ran `scripts/project_graph.py` — `VERIFY: OK`. Independently confirmed all 973 Neo4j Document nodes now have `effective_start_date` populated (was 0 before this entire incident began).

11. **Legacy key cleanup**: an initial full clean-pass attempt was stopped before it wrote anything (output still empty) once `-25` offered a cheaper delete-only `--drop-legacy-payload` flag, to avoid an unnecessary rewrite of all 12,003 documents. Verified hash and dry run, approved by user, executed.

12. **Drop attempt**: exhausted all 5 retries with client-side "timed out" errors — but server logs showed the delete calls actually returned **HTTP 200** six times, each taking ~60.0s, right at the client's default 60-second timeout boundary. **Bug, acknowledged by `-25` as their own**: wrapping a whole-collection mutation in a retry loop designed for small per-document calls meant a slow-but-successful operation was reissued five redundant times, and the resulting load (CPU spiked to 1268%, memory to 4.5GiB) was mistaken for a new failure. `agentic-rag-chatbot-e8` independently corroborated the same "collection briefly unresponsive after the bulk write, then fine" pattern from their own retrieval eval runs. Fixed: the collection-wide delete now fires with `wait=False` and is not retried (matching an existing pattern already documented elsewhere in the codebase, `vector_store.ensure_payload_indexes`, for exactly this class of operation).

### Final status — incident closed

A follow-up dry run (run once, after waiting rather than polling, per `-25`'s explicit instruction) confirmed the drop had landed cleanly server-side: `points_checked 152833`, `points_already_correct 152833`, `points_carrying_a_legacy_key 0`.

- MySQL: fully corrected (5,152 documents), verified.
- Qdrant dates: fully corrected and cross-verified exact-match against MySQL (152,833/152,833 points).
- Qdrant legacy payload keys (`published_at` and friends): **confirmed dropped** — `points_carrying_a_legacy_key 0` on all 152,833 points.
- Neo4j graph: re-projected, Document dates populated, verified.
- Semantic cache: confirmed by `-25` to need no action (collection doesn't currently exist).

### Consolidated cross-store verification (`-25`, independent of the dry-run tooling above)

A value-by-value comparison, not a presence check, run separately from the repair script itself:

| Store | Result |
|---|---|
| MySQL | 12,003 documents, 0 undated, 3,850 with a date range, 0 backwards ranges |
| Qdrant | 152,833 points, 0 mismatches vs MySQL, 0 orphans, 0 legacy keys (includes the precision-marker contract, not just raw values) |
| Neo4j | 973 documents, all dated, 0 disagreeing with MySQL |

### Final cleanup — the stale Neo4j `published_at` property

`-25` had already built `--drop-legacy-graph` (dry run clean: 973 documents, all with `effective_start_date`, all still carrying the legacy `published_at`) before the timeout episode above. Verified hash and dry run independently, approved by the user, applied. Confirmed directly against the graph: `documents 973, with_effective_start_date 973, with_published_at 0`.

**Deliberately left in place, by design, not oversight:**
- The legacy MySQL columns (`documents.published_at`, `published_at_source`, `published_at_precision`, `document_published_at`; `documents_date_decision.current_published_at`, `candidate_date`, `candidate_source`) — kept as the only surviving record of the pre-migration state, until the new dates have been lived with for a while. `--drop-legacy` is ready whenever wanted, and refuses while anything is unmigrated.

**Not resumed after this incident:**
- The original graph-coverage backlog from Part 1 (LLM claim-extraction backfill for the four empty predicates, predicate/entity vocabulary expansion) remains open.

### Written up by `-25` as permanent project documentation

`docs/ingestion/bundle-date-capture-plan.md` — the full architecture spec (bundle→date-field mapping, resolution ladder, range handling, the `published_*`→`effective_*` rename) plus a "what running the migration actually cost" section covering the four defects, the three interruptions, the recovery design (`--repair-qdrant` reconciling against MySQL as authority, no scrolling on the write path, resumable), and a closing table of four cases across two workstreams where a confident, plausible-looking number was wrong and only a read-back caught it. Read and verified in full — an accurate, independent record of this incident, not just this session's account of it.

---

## Coordination protocol used throughout

Every cross-session exchange in this incident followed the same discipline, applied consistently by this session:

1. **Never trust a peer's claim at face value.** Every reported number, file content, or database state was independently re-derived: SHA-256 hashes of shared files before every write, dry runs re-executed and compared line-by-line, direct SQL/Cypher/Qdrant queries run in this session rather than relying on a peer's report.
2. **Never write without the user's explicit, current approval.** Several times a previously-approved action was *not* run because the underlying facts had changed (e.g., the approved `--expect 2296` was withheld and re-confirmed once the real count turned out to be 5,152) — approval is scoped to what was actually approved, not a blanket license.
3. **Never improvise around another session's code.** When bugs were found (the Qdrant payload-clobber ordering bug, the partial-write stranding risk, the retry-on-a-slow-success bug), they were reported with full diagnostics to the owning session rather than patched directly — including explicit refusals to "just fix it" when that would have been faster but riskier.
4. **A peer cannot authorize a write in this session.** All approvals for `--apply`-style commands came from the user via `AskUserQuestion`, never inferred from a peer's message, even when a peer explicitly said "go ahead."
5. **Verify claims about shared, external state too** — e.g., independently confirming via `docker inspect` and container logs that a "crash" was actually an external stack restart, and separately confirming a "timeout failure" was actually a slow success, rather than accepting either characterization from a peer without evidence.
