# Setup & Running

## Prerequisites

- **Python 3.11+**
- **Docker** (for Qdrant) — or a reachable Qdrant instance
- An **Azure OpenAI** resource with a **chat** deployment and an **embedding**
  deployment.
- Optional: **Redis** (caches + corpus version), **MySQL/MariaDB** (ingest-state
  manifest + structured query path), **Azure Document Intelligence** (OCR for scanned
  PDFs).

## 1. Install dependencies

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# bash/zsh:            source .venv/bin/activate
pip install -r requirements.txt
```

Dependencies are listed in [requirements.txt](../requirements.txt). Celery is optional
(background workers), as are the PDF-extraction extras
(`azure-ai-documentintelligence`, `unstructured`).

## 2. Configure environment

Copy the template and fill in credentials:

```bash
cp .env.example .env
```

Minimum to answer questions (chat + embeddings + Qdrant):

```env
AZURE_OPENAI_MODEL=<chat-deployment>
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-06-01

AZURE_OPENAI_EMBEDDING_MODEL=<embedding-deployment>
AZURE_OPENAI_EMBEDDING_KEY=<key>
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_EMBEDDING_API_VERSION=2024-06-01

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=documents
```

Add Redis / MySQL / Drupal / Document Intelligence settings as needed — the full list
is in [configuration.md](configuration.md).

## 3. Start Qdrant

```bash
docker compose up -d
```

This runs Qdrant from [docker-compose.yml](../docker-compose.yml) on ports `6333`
(HTTP) and `6334` (gRPC), with a persistent `qdrant_storage` volume. Dashboard:
`http://localhost:6333/dashboard`. The application creates the collection on first use.

> Redis and MySQL are not in the compose file — point the app at existing instances via
> `REDIS_URL` and the `MYSQL_*` settings, or run your own containers. Both are optional.

## 4. Run the API

```bash
uvicorn app.main:app --reload                 # development
uvicorn app.main:app --host 0.0.0.0 --port 8000   # production-ish
```

Verify:

```bash
curl http://localhost:8000/health    # {"status":"ok"}
curl http://localhost:8000/ready     # 200 when Qdrant is reachable
```

Interactive API docs: `http://localhost:8000/docs`.

## 5. Ingest content

**Single PDF (HTTP):**

```bash
curl -F "file=@policy.pdf" http://localhost:8000/ingest/pdf
```

**Crawl Drupal bundles (HTTP):**

```bash
curl -X POST http://localhost:8000/ingest/article \
  -H "Content-Type: application/json" \
  -d '{"bundles": ["news", "report"]}'
```

**Incremental sweep (CLI, no broker needed):**

```bash
python -m app.workers.tasks sweep
python -m app.workers.tasks pdfs
python -m app.workers.tasks drupal --bundle news --reconcile
```

PDF directory sweeps read `PDF_SOURCE_DIRS` (and `PDF_IGNORE_GLOBS`). See
[ingestion.md](ingestion.md) for the full pipeline and [operations.md](operations.md)
for running Celery workers instead of inline.

## 6. Ask a question

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our data retention policy for disputes?"}'
```

`-N` disables curl buffering so you see the SSE token stream. See
[api-reference.md](api-reference.md#chat) for the event format.

## Verifying without external services

The offline runners exercise canonicalization, chunking, and PDF extraction without
Qdrant/Redis/Azure:

```bash
python -m app.local_tests.run_all
```

## Where things live

- App config & wiring: [app/main.py](../app/main.py), [app/config.py](../app/config.py)
- Shared clients: [app/deps.py](../app/deps.py)
- Architecture & request flow: [architecture.md](architecture.md)
