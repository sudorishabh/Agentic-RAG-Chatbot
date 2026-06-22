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
    pdf_ocr_render_dpi: int = 300
    docling_table_mode: str = "accurate"
    docling_artifacts_path: str = ""
    docling_batch_size: int = 1
    docling_queue_max_size: int = 4
    pdf_extract_images: bool = True
    pdf_image_dir: str = "data/extracted_images"
    pdf_image_min_pixels: int = 64
    pdf_describe_images: bool = True
    pdf_image_caption_max_tokens: int = 256
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
    pdf_ignore_globs: str = ""
    ingest_state_table: str = "ingest_state"
    drupal_reconcile_every: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
