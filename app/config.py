from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Standard chat model (gpt-5-mini) — AZURE_OPENAI_*
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_model: str = ""
    # Reasoning chat model (gpt-5) — AZURE_OPENAI_REASONING_*
    azure_openai_reasoning_api_key: str = ""
    azure_openai_reasoning_endpoint: str = ""
    azure_openai_reasoning_api_version: str = "2024-06-01"
    azure_openai_reasoning_model: str = ""
    # Embeddings model (text-embedding-3-large) — AZURE_OPENAI_EMBEDDING_*
    azure_openai_embedding_model: str = ""
    azure_openai_embedding_key: str = ""
    azure_openai_embedding_endpoint: str = ""
    azure_openai_embedding_api_version: str = "2024-06-01"
    # Azure Document Intelligence — OCR/layout for scanned PDFs. "prebuilt-layout"
    # recovers tables + structure as Markdown; "prebuilt-read" is plain-text OCR.
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
    azure_document_intelligence_model: str = "prebuilt-layout"
    # --- PDF extraction (app/ingestion/extractors/pdf_extractor.py) ---
    # Per-page text-layer length (chars) below which a page is treated as
    # scanned and routed to Azure OCR instead of Docling.
    pdf_scanned_char_threshold: int = 100
    # DPI used to rasterise a scanned page before sending it to Azure OCR.
    pdf_ocr_render_dpi: int = 300
    # Docling table-structure model: "accurate" (slower, better) or "fast".
    docling_table_mode: str = "accurate"
    # Directory of pre-downloaded Docling models; empty = default Hugging Face
    # cache (downloaded on first run). Set this for offline/air-gapped hosts.
    docling_artifacts_path: str = ""
    # Figure/image handling.
    pdf_extract_images: bool = True
    # Where extracted figures are written (a per-document subfolder is created).
    pdf_image_dir: str = "data/extracted_images"
    # Skip images whose largest side is below this many pixels (icons, rules).
    pdf_image_min_pixels: int = 64
    # Caption figures with the Azure OpenAI vision model (AZURE_OPENAI_*, must be
    # a multimodal deployment) so charts/diagrams become searchable text.
    pdf_describe_images: bool = True
    pdf_image_caption_max_tokens: int = 256
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "documents"
    # Redis — shared cache / coordination. Empty disables it (get_redis() -> None).
    redis_url: str = ""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    # --- Retrieval pipeline (app/retrieval/*) ---
    # Final number of reranked context blocks handed to the LLM (N, §6.6).
    retrieval_top_k: int = 6
    # Wide candidate pool pulled from hybrid search before reranking (K, §6.2).
    retrieval_candidate_k: int = 40
    # Collection is dense-only today; flip on once sparse vectors are indexed (§5.5).
    hybrid_use_sparse: bool = False
    # Reranker (§6.3 / §9.4). "embedding" blends the dense score with recency +
    # authority + MMR diversity (no extra model); "llm" uses the chat model as a
    # cross-encoder; "cross_encoder"/"cohere" use an external reranker if available;
    # "none" passes candidates through on dense score alone.
    reranker_provider: str = "embedding"
    rerank_model: str = ""
    # Drop any context block whose blended relevance is below this (hallucination
    # guard, §6.3 / §10.6). 0 disables the guard.
    rerank_score_threshold: float = 0.0
    # §9.4 tie-breakers, applied on top of the dominant semantic score.
    rerank_recency_weight: float = 0.05
    rerank_authority_weight: float = 0.05
    # Query-time fine dedup: drop a block ≥ this cosine-similar to a kept one (§9.2).
    dedup_cosine_threshold: float = 0.92
    # Cap on retrieved context handed to the LLM, in tokens (§6.4).
    context_token_budget: int = 8000
    # MySQL/MariaDB source — the Drupal CMS database holding website content.
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = ""
    mysql_connect_timeout: int = 10
    # Max pooled MySQL connections shared across the process (app.deps pool).
    mysql_pool_size: int = 5
    # Drupal JSON:API source — the public website content API. Used by the
    # ingestion job to pull published nodes (news, articles, projects, ...).
    drupal_jsonapi_base: str = "https://teriin.org/jsonapi"
    drupal_request_timeout: int = 60
    drupal_page_size: int = 50
    drupal_max_retries: int = 3
    # --- Change detection / incremental ingestion (app/ingestion/change_detection.py) ---
    # Filesystem roots holding PDFs to ingest. Multiple roots are separated by the
    # OS path separator (";" on Windows, ":" on POSIX). Walked recursively.
    pdf_source_dirs: str = ""
    # Glob patterns (matched against each PDF's path relative to its root, with
    # "/" separators) to skip while walking — e.g. "archive/**, **/_drafts/**".
    # Comma- or newline-separated.
    pdf_ignore_globs: str = ""
    # Manifest table (created in the MySQL database above) recording what has been
    # ingested: per-document fingerprint, content hash, and version.
    ingest_state_table: str = "ingest_state"
    # Re-enumerate every live Drupal node id once per this many incremental runs to
    # detect deletions/unpublishes (0 disables the reconcile pass).
    drupal_reconcile_every: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
