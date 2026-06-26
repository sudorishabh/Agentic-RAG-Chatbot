from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_model: str = ""
    azure_openai_reasoning_api_key: str = ""
    azure_openai_reasoning_endpoint: str = ""
    azure_openai_reasoning_api_version: str = "2024-06-01"
    azure_openai_reasoning_model: str = ""
    llm_structured_temperature: float | None = None
    azure_openai_embedding_model: str = ""
    azure_openai_embedding_key: str = ""
    azure_openai_embedding_endpoint: str = ""
    azure_openai_embedding_api_version: str = "2024-06-01"
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
    azure_document_intelligence_model: str = "prebuilt-layout"
    pdf_scanned_char_threshold: int = 100
    # PDF extraction routing (app/ingestion/extractors): "hybrid" classifies each
    # page and sends the whole doc to Azure if any page is scanned or has a table;
    # "azure_only" always uses Azure Layout; "local_only" uses PyMuPDF text only.
    extraction_mode: str = "hybrid"
    # Per-page table detection (PyMuPDF). find_tables() is the primary, reliable
    # signal — it handles both ruled and borderless tables. The two extra
    # heuristics below are OFF by default: on heavily-designed PDFs (banners,
    # side panels, page borders, multi-column text) they fire on nearly every
    # page and over-route everything to Azure. Enable them only for simpler
    # corpora where biasing harder toward Azure is worth the false positives.
    pdf_detect_ruled_grid: bool = False
    pdf_table_min_grid_lines: int = 3
    pdf_detect_borderless_tables: bool = False
    pdf_borderless_min_aligned_rows: int = 4
    pdf_borderless_min_columns: int = 3
    # A text line repeated on >= this fraction of a document's pages is treated as
    # a running header/footer and stripped from every page (0 disables).
    pdf_running_header_min_fraction: float = 0.5
    # Drop chart/axis "number soup" lines (e.g. "2020 2030 2040 2050") — bare
    # numeric runs from figures that carry no semantic signal.
    pdf_drop_number_soup: bool = True
    # STEP 5 (optional, off): hybrid already sends only flagged pages to Azure;
    # when True, expand table pages to adjacent pages so a table spanning a page
    # break stays whole. See _hybrid_extract for the TODO.
    extraction_azure_page_ranges: bool = False
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "documents"
    redis_url: str = ""
    response_cache_enabled: bool = True
    response_cache_ttl: int = 86400
    embedding_cache_enabled: bool = True
    embedding_cache_ttl: int = 604800
    semantic_cache_enabled: bool = True
    semantic_cache_threshold: float = 0.97
    semantic_cache_max: int = 200
    chunk_size: int = 1000
    chunk_overlap: int = 200
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    worker_sweep_interval_seconds: int = 3600
    worker_sweep_reconcile: bool = False
    retrieval_top_k: int = 6
    retrieval_candidate_k: int = 40
    hybrid_use_sparse: bool = False
    reranker_provider: str = "embedding"
    rerank_model: str = ""
    rerank_score_threshold: float = 0.0
    rerank_recency_weight: float = 0.05
    rerank_authority_weight: float = 0.05
    dedup_cosine_threshold: float = 0.92
    context_token_budget: int = 8000
    faithfulness_check: bool = False
    metrics_log_enabled: bool = True
    cors_allow_origins: str = "*"
    otel_enabled: bool = False
    otel_service_name: str = "agentic-rag"
    otel_exporter_otlp_endpoint: str = ""
    langfuse_enabled: bool = False
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = ""
    mysql_connect_timeout: int = 10
    mysql_pool_size: int = 5
    drupal_jsonapi_base: str = "https://teriin.org/jsonapi"
    drupal_request_timeout: int = 60
    drupal_page_size: int = 50
    drupal_max_retries: int = 3
    pdf_source_dirs: str = ""
    # Single folder scanned by the PDF-only ingestion API. Used as the PDF
    # source when pdf_source_dirs is not set.
    pdf_source_path: str = ""
    pdf_ignore_globs: str = ""
    ingest_state_table: str = "ingest_state"
    drupal_reconcile_every: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
