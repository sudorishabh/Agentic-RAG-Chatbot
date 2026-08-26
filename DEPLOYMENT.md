# Deployment Runbook — Agentic RAG Chatbot

Deploying the FastAPI RAG service onto the Linux server that mirrors the
**teriin.org** Drupal site. This runbook records every step performed on the
**replica/staging** EC2 box so the same sequence can be repeated on the **live**
server with confidence.

> **Audience:** whoever runs the live deployment. Commands are copy-paste ready
> for **Ubuntu 22.04**. Run blocks in order; verify each before moving on.

---

## 1. Target architecture

The app is not a single process — six components run together on the box:

| Component        | Role                                                        | How it runs                       | Port  |
| ---------------- | ----------------------------------------------------------- | --------------------------------- | ----- |
| **FastAPI app**  | API: `/chat` (SSE), `/search`, `/ingest/*`, `/health`       | systemd service (uvicorn)         | 8000  |
| **Qdrant**       | vector database (hybrid retrieval)                          | Docker container                  | 6333  |
| **Redis**        | response/embedding/semantic caches **+ Celery broker**      | system service (`redis-server`)   | 6379  |
| **MariaDB/MySQL**| Drupal data + ingest-state manifest                         | already installed on the box      | 3306  |
| **Celery worker**| background ingestion                                        | systemd service                   | —     |
| **Apache**       | reverse-proxy so the browser reaches the API same-origin    | already serving the Drupal site   | 80/443|

The browser chat widget (front-end) is served by/through Apache and calls the
FastAPI API. CORS is built into the app (`cors_allow_origins` setting).

---

## 2. Server baseline (replica box, verified)

Captured from the staging EC2 instance on first inventory:

- **OS:** Ubuntu 22.04.2 LTS, x86_64
- **Resources:** 7.7 GB RAM, ~31 GB free disk (before the Python install)
- **Pre-installed:** Docker 29.5 + Compose v5, MySQL 8.0 (on `127.0.0.1:3306`,
  **password-protected** root — not `auth_socket`), **Apache 2.4** serving the
  Drupal site on :80/:443, git 2.34.
- **Was missing (we added):** swap, `gcc`/build tools, Python 3.11, Redis.

> ⚠️ **Do NOT run `apt upgrade`** (full distro upgrade) on the live box — it can
> disrupt the running Drupal / Apache / MySQL. Install only the specific
> packages listed below.

---

## 3. Security notes (read before touching the live box)

- The `.env` holds **live secrets** (Azure OpenAI key, Document Intelligence
  key, MySQL password). It is **gitignored** and must be created by hand on the
  server — it does **not** arrive with `git clone`.
- After deployment, **rotate the Azure OpenAI key** (it was shared during setup)
  and lock the file down: `chmod 600 .env`.
- Never put DB/API passwords on a shell command line (they leak into shell
  history and `ps`). Use interactive prompts (`mysql -u root -p`).

---

## 4. System provisioning  ✅ COMPLETED on replica

### 4.0 Swap (insurance for the PyTorch/docling install) ✅
No swap existed; large wheel installs / `import torch` can spike memory.
```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h            # verify: Swap shows 4.0Gi
```

### 4.1 Base build tools ✅
```bash
sudo apt update
sudo apt install -y build-essential curl ca-certificates
```

### 4.2 Python 3.11 (alongside the system 3.10) ✅
The app requires Python 3.11+. Installed via the deadsnakes PPA:
```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
python3.11 --version      # verified: Python 3.11.15
```

### 4.3 Redis — caches + Celery broker ✅
```bash
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
redis-cli ping            # verified: PONG
```

### 4.4 System libraries for docling / PDF extraction ✅
```bash
sudo apt install -y poppler-utils libgl1 libglib2.0-0
```

### 4.5 Docker usable without sudo ✅
```bash
sudo usermod -aG docker ubuntu
newgrp docker             # or log out / back in
docker ps                 # verified: runs without sudo
```

### 4.6 MySQL — Drupal DB is on AWS RDS, not local  ✅ RESOLVED
Key finding: the **local** MySQL 8 on this box is **not** what Drupal uses.
`settings.php` shows Drupal connects to **remote AWS RDS**. Two candidates appear
across the site's config files:

| DB name | RDS host | Region | Creds |
|---|---|---|---|
| `upgradedteridb_12032026` | `mysqlteridb.cyihsoccetqm.ap-south-1.rds.amazonaws.com` | ap-south-1 | root / `qw#er5ty` |
| `teriin` | `teriin-db.cezvsz1bn29p.ap-southeast-1.rds.amazonaws.com` | ap-southeast-1 | root / `qw#er5ty` |

**Use the DB the *live* site actually serves from.** Working assumption:
`upgradedteridb_12032026` (recently upgraded, referenced by most config files).
Confirm with the connectivity test (also proves the RDS security group allows
this EC2 — required, since the app reaches RDS over the network):
```bash
mysql -h mysqlteridb.cyihsoccetqm.ap-south-1.rds.amazonaws.com -u root -p \
  -e "SELECT DATABASE(); SHOW TABLES LIKE 'node%';"     # enter qw#er5ty
```
> ⚠️ Using RDS **root** for the app is broad — create a read-only app user later.
> ⚠️ Cross-region latency affects the structured-query (drupal_router) path.
> MySQL is optional: the app starts without it; only the Drupal lookup path needs it.

---

## 5. Application code + Python dependencies  ✅ COMPLETED on replica

### 5.1 Clone the repo ✅
Deployed to `/opt/agentic-rag-chatbot`, owned by `ubuntu`:
```bash
sudo mkdir -p /opt/agentic-rag-chatbot
sudo chown ubuntu:ubuntu /opt/agentic-rag-chatbot
git clone https://github.com/sudorishabh/Agentic-RAG-Chatbot.git /opt/agentic-rag-chatbot
cd /opt/agentic-rag-chatbot
git log -1 --oneline      # verified: 6cfae81 add markdown rendering...
```
> Private repo → use a GitHub **Personal Access Token** as the password at the
> prompt (account passwords are not accepted).

### 5.2 Python 3.11 virtualenv ✅
```bash
cd /opt/agentic-rag-chatbot
python3.11 -m venv .venv
source .venv/bin/activate
python --version          # verified: 3.11.15
pip install --upgrade pip wheel setuptools
```

### 5.3 Install dependencies ✅ (verify imports — see §5.4)
Run inside `tmux` so an SSH drop doesn't abort the multi-GB install:
```bash
tmux new -s install
cd /opt/agentic-rag-chatbot && source .venv/bin/activate
pip install -r requirements.txt
# detach with Ctrl-b then d ; reattach with: tmux attach -t install
```
Installed torch 2.12.1, transformers, docling stack, qdrant-client, redis,
celery, langchain-openai, etc.

> 💡 **Live-server optimization:** the default `torch` wheel drags in ~4–5 GB of
> NVIDIA CUDA libraries this CPU-only box never uses. To skip them, install
> CPU-only torch **before** the requirements file:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> pip install -r requirements.txt
> ```

### 5.4 Verify the install  ✅ VERIFIED
```bash
cd /opt/agentic-rag-chatbot && source .venv/bin/activate
python -c "import torch, docling, qdrant_client, celery, redis, fastapi, langchain_openai; print('core imports OK')"
df -h /                   # confirm disk headroom remains
```
Result: `core imports OK`. Disk after install: **60 G used / 18 G free (78%)** —
the torch+CUDA stack consumed ~13 G (avoidable with CPU-only torch, §5.3).

---

## 6. Environment configuration (`.env`)  ⬜ UPCOMING

The cloned repo has **no** `.env`. Create `/opt/agentic-rag-chatbot/.env` from
`.env.example` and fill in the Azure credentials. Beyond what the current local
`.env` contains, the live `.env` **must add** the lines that enable the services
we provisioned (Redis cache, Celery broker, CORS):

```ini
# --- caches + Celery broker (Redis we installed) ---
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# --- restrict CORS to the Drupal origins (defaults to "*") ---
CORS_ALLOW_ORIGINS=https://teriin.org,https://www.teriin.org

# --- Qdrant (default is fine for the local container) ---
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=documents

# --- MySQL: Drupal DB lives on AWS RDS (see §4.6), NOT localhost ---
MYSQL_HOST=mysqlteridb.cyihsoccetqm.ap-south-1.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD='qw#er5ty'      # quote — contains '#'
MYSQL_DATABASE=upgradedteridb_12032026
```
Then: `chmod 600 .env`

> ❓ To validate before relying on it: the Azure **embedding endpoint** in the
> current `.env` is a full `/embeddings?api-version=...` URL rather than the base
> endpoint — confirm langchain-openai accepts it (the readiness/ingest smoke test
> in §10 will surface any issue).

---

## 7. Qdrant vector database  ⬜ UPCOMING

The repo ships a `docker-compose.yml` that runs Qdrant with a persistent volume:
```bash
cd /opt/agentic-rag-chatbot
docker compose up -d
docker compose ps                       # qdrant healthy, ports 6333/6334
curl -s http://localhost:6333/healthz   # expect: healthz check passed
```

---

## 8. systemd services (uvicorn + Celery)  ⬜ UPCOMING (drafts)

Run the app and worker as managed services that survive reboots/crashes.
Drafts — to be finalized and installed in this phase:

`/etc/systemd/system/ragchat.service`
```ini
[Unit]
Description=Agentic RAG Chatbot (uvicorn)
After=network.target redis-server.service docker.service

[Service]
User=ubuntu
WorkingDirectory=/opt/agentic-rag-chatbot
ExecStart=/opt/agentic-rag-chatbot/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/ragchat-worker.service`
```ini
[Unit]
Description=Agentic RAG Chatbot (Celery worker)
After=network.target redis-server.service

[Service]
User=ubuntu
WorkingDirectory=/opt/agentic-rag-chatbot
ExecStart=/opt/agentic-rag-chatbot/.venv/bin/celery -A app.workers.tasks:celery_app worker --loglevel=info --concurrency=1
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ragchat ragchat-worker
sudo systemctl status ragchat
```
> **No `EnvironmentFile`** — the app reads `.env` itself via `WorkingDirectory`;
> systemd would mishandle the quoted MySQL password (`#`).
> Bind uvicorn to `127.0.0.1` (not `0.0.0.0`) — only Apache should reach it.
> Celery app object is `celery_app` in `app.workers.tasks`; concurrency=1 on this
> RAM-constrained box (docling is memory-heavy). The periodic `sweep` needs a
> separate `celery beat` process — add later if you want scheduled re-ingest.

---

## 9. Apache reverse-proxy  ⬜ UPCOMING

Apache already serves Drupal on 80/443; add a proxy so the browser reaches the
API same-origin (e.g. `https://teriin.org/chat-api/`). Requires `mod_proxy`,
`mod_proxy_http`; **SSE needs buffering off**. Exact vhost path/config to be
finalized after inspecting the existing Apache site config. Sketch:
```apache
# inside the Drupal SSL vhost
ProxyPreserveHost On
ProxyPass        /chat-api/ http://127.0.0.1:8000/
ProxyPassReverse /chat-api/ http://127.0.0.1:8000/
# disable buffering for the streaming endpoint
<Location /chat-api/chat>
    SetEnv proxy-sendchunked 1
    SetEnv no-gzip 1
</Location>
```
```bash
sudo a2enmod proxy proxy_http
sudo apache2ctl configtest && sudo systemctl reload apache2
```

---

## 10. Smoke test  ⬜ UPCOMING

```bash
curl -s http://127.0.0.1:8000/health           # liveness
curl -s http://127.0.0.1:8000/ready            # Qdrant reachable? (503 until up)
curl -s http://127.0.0.1:8000/metrics          # collection size, wiring
# ingest a doc then ask:
curl -X POST http://127.0.0.1:8000/ingest/article -H "Content-Type: application/json" \
  -d '{"title":"Test","body":"The pilot connected 1240 households.","url":"https://example.org/a"}'
curl -N -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
  -d '{"question":"How many households did the pilot connect?"}'
```
Then verify the same through Apache (`https://.../chat-api/health`) and that the
browser widget can call it without CORS errors.

---

## 11. Front-end widget  ⬜ UPCOMING

The repo's `ui/` shell is a standalone chat page. Turning it into the
bottom-right floating widget embedded in Drupal pages is a separate front-end
task, done after the API is live and reachable through Apache.

---

## Progress summary

| Phase | Status |
| ----- | ------ |
| 4. System provisioning (swap, tools, Python 3.11, Redis, libs, Docker) | ✅ done |
| 4.6 MySQL DB on AWS RDS (resolved; confirm which DB live) | ✅ done |
| 5. Code clone + venv + dependencies | ✅ done |
| 5.4 Import verification | ✅ done |
| 6. `.env` configuration | ⬜ upcoming |
| 7. Qdrant container | ⬜ upcoming |
| 8. systemd services | ⬜ upcoming |
| 9. Apache reverse-proxy | ⬜ upcoming |
| 10. Smoke test | ⬜ upcoming |
| 11. Front-end widget | ⬜ upcoming |
