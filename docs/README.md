# Documentation

Documentation for the **Agentic RAG Chatbot** — a FastAPI RAG service over a mixed
corpus of PDFs and website/Drupal articles, served by Azure OpenAI with Qdrant
retrieval, cross-encoder reranking, grounded+cited generation, an intent-routed
structured (MySQL/JSON:API) path, optional Redis caches, Celery ingestion workers,
and observability.

These docs describe how the code that exists *actually* works — modules, functions,
HTTP API, and configuration.

| Doc | Covers |
| --- | --- |
| [setup.md](setup.md) | Prerequisites, install, environment, running the API and workers |
| [architecture.md](architecture.md) | Module map, request lifecycle, the retrieve→rerank→generate pipeline |
| [api-reference.md](api-reference.md) | Every HTTP endpoint, request/response schemas, the SSE event stream |
| [configuration.md](configuration.md) | Every setting in [app/config.py](../app/config.py) / `.env` |
| [ingestion.md](ingestion.md) | Extraction → canonical → chunk → embed → index, change detection, state |
| [retrieval.md](retrieval.md) | Query understanding, hybrid search, reranking, context building, citations, structured path |
| [generation.md](generation.md) | LLM factories, grounding prompts, faithfulness checking |
| [operations.md](operations.md) | Redis caches, Celery/inline workers, observability, health/metrics |
| [website-preference-retrieval.md](website-preference-retrieval.md) | Design + implementation of preferring website content (dual retrieval + segregated, website-first context) |
| [website-preference-testing.md](website-preference-testing.md) | How to enable, verify, tune, and roll back the website-preference feature |

> A few designed-but-not-yet-wired features (server-side sparse/RRF fusion, multi-tenant
> `is_tenant` partitioning) are called out inline where relevant — these docs describe
> current behavior.
