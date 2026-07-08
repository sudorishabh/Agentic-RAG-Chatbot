# Remediation Handoff

Status notes for the security/quality remediation of the Agentic-RAG-Chatbot.
**The review backlog is complete** — Critical, High, Medium, and the actionable
Low items are fixed and committed, and the docs are aligned. What remains is
operational (see §4).

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

## 3. What was fixed (summary)

- **Critical:** client-asserted ACL/tenant → backend-verified Bearer JWT
  (`app/api/auth.py`); DOM XSS in the widget (`escapeHtml` quotes + `resolveUrl`
  scheme allowlist). C2 (unauthenticated ingestion) is covered by the private
  network boundary.
- **High:** streaming `/chat` converged onto the shared cached/measured pipeline;
  semantic cache moved to Qdrant (`app/cache/semantic_cache.py`, TTL + prune);
  MySQL pool reserve-then-connect with bounded wait; PDF stat pre-filter before
  hashing; upload cap + `%PDF-` validation (413/415); structured list/lookup
  answered from the local catalog (`state.list_documents`/`count_documents`);
  `/source/{id}` scoped to the caller's tenant/ACL (H2).
- **Medium:** Drupal high-water `>=`; shared HTTP session for attachment
  downloads; `ensure_collection`/`collection_exists` once per process; O(n²)
  window-coalescing fixed; PDF parsed once in hybrid extraction (text captured at
  classification; `test_router.py` asserts outputs); ingest-log unchanged-row
  gating + retention pruning; index-new-then-delete reindex swap (keep-ids
  filter); one-ingestion-run-at-a-time (`IngestBusyError` → 409 / sweep skip);
  `/ready`+`/metrics` detail behind `ops_detail_enabled`; chat streaming on a
  dedicated thread limiter (`chat_stream_max_concurrency`); CORS narrowed to
  GET/POST + Content-Type/Authorization with a wildcard warning; UI: New-chat
  aborts the in-flight request (epoch guard), frame-batched delta rendering,
  https upgrade for the api base, dead `styles.css` removed + README rewritten.
- **Low (actionable subset):** `lstrip("www.")` → `removeprefix`; `top_k`
  bounded 1–50; empty `ocr.py` deleted; reranker dead imports + cached Cohere
  client; SSE terminal `error` event + UI truncation detection + reader release
  + `data-title`; Azure DI tables without a bounding region kept (first page).
  Deliberately skipped: `_split_text_recursive` O(n²) (ingestion-time),
  parent zero-vector redesign, CSP (host-page concern), file splitting.
- **Docs:** all of `docs/` + root README + `ui/README.md` + `.env.example`
  aligned with the above (two servers, auth, Qdrant semantic cache, local
  catalog, ops flags, SSE `error`, endpoint tables).

## 4. Remaining work (operational — no code)

1. **Run the one-time catalog backfill** so pre-catalog docs have `title`/`url`:
   ```
   python -m app.ingestion.backfill
   ```
2. **Rotate the local MySQL password.** A real password was previously committed
   in `.env.example` (now blanked); it remains in git history — treat it as
   disclosed.
3. **End-to-end test** (needs Azure OpenAI + Qdrant + MySQL; Redis optional):
   start Qdrant, run `app.main:app` (:8000) + `app.ingest_main:app` (:8001),
   ingest a PDF via `/ingest/pdf`, then `/search` → `/chat`. See
   `docs/setup.md`.
4. At deployment: pin `CORS_ALLOW_ORIGINS`; decide `AUTH_ENABLED` + `JWT_*`;
   set `OPS_DETAIL_ENABLED=true` only on private/dev instances.

## 5. Verify

```
./.venv/Scripts/python.exe -m pytest -q          # expect 85 passed
```
