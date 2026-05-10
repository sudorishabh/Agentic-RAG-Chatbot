# Agentic RAG Chatbot

FastAPI-based RAG service using Azure OpenAI, LangChain, and Qdrant.

## Architecture

```
app/
├── main.py              FastAPI app, router wiring
├── core/
│   └── config.py        Settings loaded from environment / .env
├── api/routes/
│   ├── ingest.py        POST /ingest  (file upload)
│   └── query.py         POST /query   (ask a question)
├── schemas/
│   ├── ingest.py        IngestResponse
│   └── query.py         QueryRequest, QueryResponse, SourceChunk
└── services/
    ├── embeddings.py    Azure OpenAI embeddings client
    ├── vector_store.py  Qdrant client, collection bootstrap, vector store
    ├── ingestion.py     Document loading, chunking, upsert
    └── rag.py           Retrieval + generation chain
```

## Prerequisites

- Python 3.11+
- Docker (for Qdrant)
- An Azure OpenAI resource with a chat deployment and an embedding deployment

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env` with your Azure OpenAI credentials and deployment names.

Start Qdrant:

```bash
docker compose up -d
```

## Run

```bash
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
- Qdrant dashboard: http://localhost:6333/dashboard

## Usage

Ingest a document (PDF or plain text):

```bash
curl -X POST http://127.0.0.1:8000/ingest -F "file=@document.pdf"
```

Ask a question:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What does the document say about X?\"}"
```

Response:

```json
{
  "answer": "...",
  "sources": [
    {"source": "document.pdf", "content": "..."}
  ]
}
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `AZURE_OPENAI_API_KEY` | — | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_VERSION` | `2024-06-01` | API version |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | — | Chat model deployment name |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | — | Embedding model deployment name |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `QDRANT_API_KEY` | — | Qdrant API key (optional for local) |
| `QDRANT_COLLECTION` | `documents` | Collection name |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between adjacent chunks |
| `RETRIEVAL_TOP_K` | `4` | Chunks retrieved per query |
