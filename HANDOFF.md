# Remediation Handoff

Continuation notes for the security/quality remediation of the Agentic-RAG-Chatbot.
Use this to resume in a fresh chat: it captures the architecture boundaries, the
working conventions, everything already done, the current git state, and the
remaining work (a docs pass + the outstanding review backlog).

---

## 1. Architecture boundaries (authoritative — keep in mind for every change)

- **Ingestion pipeline is always private** — reachable only by authorized internal
  systems, never exposed to the public internet. Network isolation is the control;
  it does not need in-app auth.
- **Retrieval layer is public-facing** (`/chat`, `/search`, `/source`, `/health`).
- **Authn/authz are owned by the RAG platform** (its own frontend + backend), **not
  delegated to any host website**. The host page is an external integration point.
- **The frontend (`ui/`) is a separate project** — embeddable into any site, but
  still part of the RAG platform (it manages auth).

## 2. Working conventions (follow these)

- **Small steps.** One logical change at a time; keep the repo working at every step.
- **Provide the commit message as text; do NOT run `git commit`.** The user commits
  manually. One short line, no body, no "Step N" narration, **no attribution / no
  Claude name / no Co-Authored-By**.
- **Wait for approval between steps.**
- **Run tests after each change:** `./.venv/Scripts/python.exe -m pytest -q`
  (baseline: **85 passing**). Also import-check touched modules.
- **Use the code-review-graph MCP tools first** for exploration (see CLAUDE.md).
- Windows + PowerShell; Python venv at `.venv/`.

## 3. Current git state

All work is committed **except the final H6 step**, which is in the working tree:

```
 M app/retrieval/drupal_router.py
```

**Pending commit (run this first in the new chat, or have the user commit):**
```
feat(retrieval): answer structured list/lookup from local catalog
```

Recent history (newest first): `feat(backfill): populate catalog title/url…`,
`feat(ingestion): store document title/url…`, `feat(state): add title/url…`,
`perf(ingestion): skip re-hashing unchanged PDFs…`, `fix(api): cap and validate PDF
uploads…`, `fix(deps): stop MySQL pool leaking slots…`, `feat(workers): prune expired
semantic cache…`, `feat(cache): back semantic cache with Qdrant…`,
`feat(cache): add Qdrant-backed semantic cache module`,
`feat(config): add Qdrant semantic cache collection settings`,
`feat(rag): serve streaming chat via cached, measured answer pipeline`,
`refactor(rag): extract shared answer pipeline…`,
`fix(cache): scope semantic cache to caller identity…`,
`fix(ui): escape quotes and allowlist link schemes…`,
`feat(auth): scope retrieval to authenticated principal…`,
`feat(auth): add JWT bearer principal dependency…`,
`feat(config): add JWT auth settings…`.

## 4. What has been completed

Origin: a full-codebase review produced findings ranked Critical/High/Medium/Low.
Addressed so far:

### Critical
- **C1 — client-asserted ACL/tenant (broken access control).** Retrieval identity now
  comes from a backend-verified **Bearer JWT** (`app/api/auth.py`, `require_principal`
  → `Principal`), not the request body. `tenant_id`/`user_groups` removed from
  `QueryRequest`/`SearchRequest`. Feature-flagged: `auth_enabled=False` ⇒ anonymous
  `public`/`default` principal (safe default; body still cannot assert identity).
  Wired into `/chat` and `/search`.
- **C3 — DOM XSS in the frontend.** `escapeHtml` now also escapes `"`/`'` (kills the
  markdown-link attribute-injection across every `renderMarkdown` path); `resolveUrl`
  restricted to `http(s)`/protocol-relative/root-relative (this also closed **H7** —
  `javascript:`/`data:` citation URLs now render as inert text).
- **C2 — unauthenticated ingestion endpoints.** Intentionally **out of scope**:
  covered by the private ingestion network boundary.

### High
- **H1 — streaming `/chat` bypassed caching/faithfulness/metrics; `answer_query` was
  dead.** Converged both entrypoints onto one shared pipeline in `app/rag.py`
  (`_prepare` / `_assemble` / `_persist` / `_record` / `_stream_result` +
  `_Generation`). `/chat` now reads/writes response + semantic cache, records metrics
  (incl. cache hits), and honors faithfulness (buffers-then-emits when
  `faithfulness_check` is on; streams token-by-token otherwise).
- **Semantic cache → Qdrant** (chosen backend). New `app/cache/semantic_cache.py`
  (`lookup`/`store`/`prune`) using a dedicated Qdrant collection: nearest-neighbor on
  the query embedding, cosine `score_threshold`, identity-scoped partition
  (`redis_cache.semantic_partition`), `expires_at` TTL + prune. Old Redis-list scan
  (`_cosine`/`_sem_key`/`semantic_lookup`/`semantic_store`) and `semantic_cache_max`
  removed. `redis_cache` now owns only the response + embedding caches. `prune()` runs
  after each ingestion sweep (`app/workers/scheduler.py`) plus opportunistically in
  `store`.
- **H3 — MySQL pool leaked slots on connect failure and blocked forever.**
  `app/deps.py MySQLPool` now reserves a slot then connects **outside the lock**,
  rolls back the reservation on failure, and waits at most `mysql_pool_timeout` (30s)
  for a free connection before raising `TimeoutError`.
- **H4 — every PDF re-read + SHA-256 hashed each scan.** `detect_file_changes`
  `stat()`s first and skips read+hash when `size`+`mtime_ns` match. New `size`/
  `mtime_ns` columns on `ingest_state` (idempotent), persisted on ingest via
  `_save_state`, refreshed on a touched-but-identical file. Existing rows hash once
  then go cheap (self-healing).
- **H5 — unbounded/unvalidated upload.** `/ingest/pdf` enforces `.pdf` suffix, reads
  in 1 MiB chunks aborting at `max_upload_bytes` (50 MiB → 413), and requires the
  `%PDF-` magic bytes (415).
- **H6 — structured list/lookup hit `teriin.org` live at query time.** Now served from
  the **local catalog**: `ingest_state` gained `title`/`url` (populated on ingest),
  `state.list_documents()` mirrors `count_documents`, and `drupal_router` list/lookup
  calls it (no `requests`, no JSON:API paging, no private-extractor imports). `count`
  and `list` now read the same source. Existing rows need the one-time backfill (below).
- **H7 — `javascript:`/`data:` citation URLs.** Closed as part of C3.

## 5. Remaining work

### 5a. Immediate operational steps
1. **Commit** the pending `app/retrieval/drupal_router.py` change (message in §3).
2. **Run the one-time catalog backfill** so existing website docs have `title`/`url`
   (new ingests populate them automatically):
   ```
   python -m app.ingestion.backfill
   ```

### 5b. Docs pass (the "remaining step") — update stale docs
The code changed under these docs; do a focused pass (grep each for the terms noted):

- **docs/architecture.md** — semantic cache is now **Qdrant-backed** (not a Redis
  list); add the **auth boundary** (Bearer JWT on public retrieval); structured
  list/lookup now reads the **local catalog**, not live Drupal.
- **docs/configuration.md** — settings changes: **add** `auth_enabled`, `jwt_secret`,
  `jwt_algorithms`, `jwt_audience`, `jwt_issuer`, `jwt_tenant_claim`,
  `jwt_groups_claim`, `mysql_pool_timeout`, `max_upload_bytes`,
  `semantic_cache_collection`, `semantic_cache_prune_every`; **remove**
  `semantic_cache_max`; clarify Redis now = response + embedding cache only.
- **docs/operations.md** — semantic-cache prune runs in the sweep loop; run the
  title/url backfill; MySQL pool now fails fast (`mysql_pool_timeout`).
- **docs/retrieval.md** — structured list/lookup from local catalog (no live site);
  semantic cache on Qdrant.
- **docs/api-reference.md** — public retrieval requires a **Bearer JWT** when
  `auth_enabled`; `tenant_id`/`user_groups` **removed** from request bodies;
  `/ingest/pdf` size cap + `.pdf`/`%PDF-` validation (413/415).
- **docs/setup.md** — auth env vars + how to mint/verify a JWT; new settings.
- **docs/README.md** — high-level: auth, Qdrant semantic cache, local structured
  answers.
- Check **docs/website-preference-retrieval.md** / **docs/website-preference-testing.md**
  for any semantic-cache mentions.

### 5c. Outstanding review backlog (not yet done)
From the original review, still open (decide scope with the user):

- **H2 — `/source/{id}` serves any PDF with no ACL check** (path traversal itself is
  already guarded in `source_locator`). Add auth + ACL/tenant re-check against the
  point payload. *(High)*
- **Medium:** duplicate pure-Python `_cosine` in `context_builder` (vectorize / de-dup);
  per-query `collection_exists()` round-trip + full-vector fetch in `hybrid_search`;
  3× PDF re-parse on hybrid extraction; `ensure_collection()` per indexed doc;
  ingest-log write per doc incl. unchanged (+ unbounded growth); non-atomic
  delete-then-reindex; per-attachment `requests.Session`; Drupal high-water strict `>`
  misses same-second edits; `_coalesce_windows` O(n²); threadpool starvation
  (sync chat stream + ingest in request thread); no sweep/ingest mutual exclusion;
  CORS default `*` (mitigated: credentials off); `/ready`+`/metrics` info disclosure;
  UI (no request cancellation on New-chat; O(n²) streaming render; mixed-content
  `http` API base; dead `ui/styles.css` + README drift).
- **Low:** `_split_text_recursive` O(n²); `lstrip("www.")` mangles hosts; parent
  all-zero vectors in a cosine collection; Azure DI page-0 tables dropped; empty
  `app/ingestion/extractors/ocr.py`; SSE mid-stream error truncates silently; `top_k`
  unbounded in schema; reranker dead import / per-call Cohere client; UI `data-title`
  ignored, reader not released on error, no CSP; oversized files (chunker, script.js).

## 6. Verify

```
./.venv/Scripts/python.exe -m pytest -q          # expect 85 passed
```
End-to-end `/chat` needs Azure OpenAI + Qdrant + Redis + MySQL, so it isn't
exercisable in the dev sandbox; rely on tests + import checks there.

## 7. Key files (touched / added this effort)

- `app/config.py` — auth/JWT settings, `mysql_pool_timeout`, `max_upload_bytes`,
  `semantic_cache_collection`, `semantic_cache_prune_every` (removed `semantic_cache_max`).
- `app/api/auth.py` *(new)* — `Principal`, `require_principal` (JWT via PyJWT, lazy import).
- `app/api/chat.py`, `app/api/search.py` — depend on `require_principal`.
- `app/schemas/query.py` — dropped `tenant_id`/`user_groups`.
- `app/api/ingest.py` — `_read_capped` + PDF validation on `/ingest/pdf`.
- `app/rag.py` — shared pipeline (`_prepare`/`_assemble`/`_persist`/`_record`/
  `_stream_result`/`_Generation`); streaming converged.
- `app/cache/redis_cache.py` — response+embedding cache only; `semantic_partition`;
  removed Redis semantic scan.
- `app/cache/semantic_cache.py` *(new)* — Qdrant semantic cache.
- `app/workers/scheduler.py` — prune after sweep.
- `app/deps.py` — `MySQLPool` reserve-then-connect + bounded wait.
- `app/ingestion/state.py` — `size`/`mtime_ns`/`title`/`url` columns, `update_stat`,
  `list_documents`, `backfill_facets` title/url.
- `app/ingestion/change_detection.py` — stat pre-filter.
- `app/ingestion/pipeline.py` — persist size/mtime/title/url; touched-file stat refresh.
- `app/ingestion/backfill.py` — backfill title/url from Qdrant payloads.
- `app/retrieval/drupal_router.py` — list/lookup from local catalog *(pending commit)*.
- `requirements.txt` — added `PyJWT`.
- `ui/script.js` — `escapeHtml` quote-escaping + `resolveUrl` scheme allowlist.
