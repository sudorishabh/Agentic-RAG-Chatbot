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
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k: int = 4
    # MySQL/MariaDB source — the Drupal CMS database holding website content.
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = ""
    mysql_connect_timeout: int = 10
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
