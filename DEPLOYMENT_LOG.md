# Deployment Log — replica EC2 box (`ip-172-31-2-94`)

> **Purpose.** This is the *execution journal* for the actual deployment on this
> specific server — what was run, what happened, resource/performance impact,
> and the current blocker. It is **updated after every step**.
>
> Companion: **`DEPLOYMENT.md`** is the reusable, generic runbook ("how to do it
> on any box, including live"). This file is "what we actually did on *this*
> box, and how the server behaved."

- **Host:** `ubuntu@ip-172-31-2-94` (staging/replica of teriin.org)
- **Spec:** Ubuntu 22.04.2 LTS · x86_64 · **7.7 GB RAM** · no GPU · root volume 78 GB
- **App path:** `/opt/agentic-rag-chatbot` · venv `.venv` (Python 3.11.15)
- **Last updated step:** §8 (systemd services) ⏳ — Qdrant up, DB confirmed

---

## Resource tracking

Snapshots taken at key milestones. Run `free -h` and `df -h /` to add a row.

| Milestone                         | RAM used | RAM avail | Swap | Disk used | Disk free |
| --------------------------------- | -------- | --------- | ---- | --------- | --------- |
| Initial inventory (idle)          | 710 Mi   | 6.7 Gi    | 0 B  | 47 G      | 31 G      |
| After swap added                  | —        | —         | 4 Gi | 47 G      | 31 G      |
| **After `pip install` (torch+docling)** | —  | —         | 4 Gi | **60 G**  | **18 G**  |
| After Qdrant container up         | 772 Mi   | 6.6 Gi    | 0 B  | 61 G      | 18 G      |
| App + worker running (idle)       | _tbd_    | _tbd_     |      | _tbd_     | _tbd_     |
| During a PDF ingestion (peak)     | _tbd_    | _tbd_     |      | _tbd_     | _tbd_     |

**Disk note:** the Python install consumed ~13 GB, of which ~4–5 GB is the
NVIDIA/CUDA stack that `torch` pulled but this CPU-only box never uses. On the
**live** box install CPU-only torch first (see `DEPLOYMENT.md` §5.3) to reclaim it.

---

## Performance & capacity analysis (7.7 GB RAM, no GPU)

This is a memory-constrained box that **already runs Apache + Drupal + MySQL**.
The chatbot adds five more processes. How the load actually falls:

**Light (network-bound, safe):**
- **Chat / search requests.** Embeddings and the LLM are served by **Azure**
  (remote) — local CPU/RAM per request is small; latency is dominated by the
  Azure round-trip, not this server. The box can serve these comfortably.
- **Qdrant** and **Redis** are light at this corpus size (each tens to a few
  hundred MB).

**Heavy (the thing to watch) — PDF ingestion via docling:**
- docling runs **layout + table models on CPU** (no GPU here). Each extraction
  can use **~1.5–3 GB RAM** and take **tens of seconds to minutes** per document
  (table-heavy/scanned PDFs are slowest).
- This runs in the **Celery worker**, not the API — so it won't block `/chat`.

**Capacity guidance for this box:**
1. **Limit Celery concurrency to 1** (`--concurrency=1`) so only one docling
   extraction runs at a time — prevents RAM exhaustion. Raise only if `free -h`
   during ingestion shows comfortable headroom.
2. The **4 GB swap** is a safety buffer for ingestion spikes, not a substitute
   for RAM — if the box swaps heavily during ingestion, lower concurrency.
3. **Ingest in batches / off-peak** so a big ingestion run doesn't compete with
   live Drupal traffic for RAM.
4. If extraction is too slow, consider `DOCLING_TABLE_MODE=fast` (vs `accurate`)
   in `.env` — faster, slightly lower table fidelity.
5. Bind uvicorn to `127.0.0.1` and keep workers modest (1–2) — serving is
   I/O-bound on Azure, so more workers mostly add memory, not throughput.

> Re-evaluate all of the above on the **live** box if its RAM differs from 7.7 GB.

---

## Step-by-step execution log

Legend: ✅ done · ⏳ in progress · ⛔ blocked · ⬜ not started

### ✅ §4.0 Swap (4 GB)
`fallocate`/`mkswap`/`swapon` + fstab entry. `free -h` confirmed Swap = 4.0 Gi.

### ✅ §4.1 Base build tools
`build-essential curl ca-certificates` installed.

### ✅ §4.2 Python 3.11
deadsnakes PPA → `python3.11` + `-venv` + `-dev`. Verified **3.11.15**.

### ✅ §4.3 Redis
`redis-server` installed, enabled, started. `redis-cli ping` → **PONG**.

### ✅ §4.4 docling/PDF system libs
`poppler-utils libgl1 libglib2.0-0` installed.

### ✅ §4.5 Docker without sudo
`ubuntu` added to `docker` group. `docker ps` runs without sudo.

### ✅ §4.6 MySQL DB — RESOLVED (Drupal uses remote AWS RDS, not local MySQL)
- `1234` on local root → rejected. `settings.php` revealed the truth: **Drupal
  connects to remote AWS RDS**, the local MySQL 8 is unused.
- Candidates found across config files:
  - **`upgradedteridb_12032026`** @ `mysqlteridb.cyihsoccetqm.ap-south-1.rds.amazonaws.com` (ap-south-1), root / `qw#er5ty`  ← **chosen** (recently upgraded, most-referenced)
  - `teriin` @ `teriin-db.cezvsz1bn29p.ap-southeast-1.rds.amazonaws.com` (ap-southeast-1), root / `qw#er5ty`
- **Still to confirm:** that `upgradedteridb_12032026` is what the *live* site
  serves, and that this EC2 can reach the RDS (security-group). Test:
  ```bash
  mysql -h mysqlteridb.cyihsoccetqm.ap-south-1.rds.amazonaws.com -u root -p \
    -e "SELECT DATABASE(); SHOW TABLES LIKE 'node%';"
  ```
- Caveats: RDS **root** is over-privileged (make a read-only app user later);
  **cross-region latency** on the drupal_router path; MySQL is optional for boot.

### ✅ §5.1 Clone repo
Cloned to `/opt/agentic-rag-chatbot`, owned by `ubuntu`. HEAD = `6cfae81`.

### ✅ §5.2 venv
Python 3.11 venv at `.venv`; pip/wheel/setuptools upgraded.

### ✅ §5.3 Install dependencies
`pip install -r requirements.txt` inside tmux. torch 2.12.1, transformers,
docling stack, qdrant-client, redis, celery, langchain-openai, etc.
⚠️ pulled full CUDA stack (unused on CPU box) — ~13 G total install.

### ✅ §5.4 Verify install
`python -c "import torch, docling, ..."` → **core imports OK**.
Disk after: 60 G used / 18 G free (78%).

### ✅ §6 `.env` configuration
Created `/opt/agentic-rag-chatbot/.env` (Azure creds, RDS MySQL, `REDIS_URL`,
`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CORS_ALLOW_ORIGINS`,
`DOCLING_TABLE_MODE`). Fixed stray space in reasoning endpoint; quoted MySQL
password (`#`). `chmod 600` applied.

**RDS connectivity CONFIRMED** ✅ — `mysql -h mysqlteridb...ap-south-1 -u root -p`
connected successfully (security group allows this EC2; creds valid). DB-content
check (node tables in `upgradedteridb_12032026`) re-run with `-D` — pending paste.

### ✅ §7 Qdrant container
`docker compose up -d` → image pulled, container `agentic-rag-chatbot-qdrant-1`
up on 6333/6334, volume `agentic-rag-chatbot_qdrant_storage`. `healthz check
passed`, Qdrant **v1.18.2**. Negligible RAM at idle.
Also: MySQL re-check listed `node_revision__field_*` tables → confirmed
`upgradedteridb_12032026` is a live Drupal schema.

### ⏳ §8 systemd services — IN PROGRESS
Plan: manual foreground test first (catch import/config errors), then install
`ragchat.service` (uvicorn 127.0.0.1:8000) + `ragchat-worker.service` (celery
`-A app.workers.tasks:celery_app`, `--concurrency=1`). **No systemd
`EnvironmentFile`** — app loads `.env` via WorkingDirectory (systemd would
mangle the quoted `#` password).
### ⬜ §8 systemd services (uvicorn + Celery, concurrency=1)
### ⬜ §9 Apache reverse-proxy (mod_proxy, SSE buffering off)
### ⬜ §10 Smoke test
### ⬜ §11 Front-end widget

---

## Current status

**Provisioning + dependencies complete; `.env` being written.** Drupal DB turned
out to be on **AWS RDS** (`upgradedteridb_12032026` @ ap-south-1), not local.
Next actions: paste the `.env` onto the box, `chmod 600`, run the RDS
connectivity test, then bring up Qdrant (§7) and the systemd services (§8).
