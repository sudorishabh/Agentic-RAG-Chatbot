from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Standard chat model (e.g. gpt-5-mini) — AZURE_OPENAI_*
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_model: str = ""
    # Reasoning chat model (e.g. gpt-5) — AZURE_OPENAI_REASONING_*
    azure_openai_reasoning_api_key: str = ""
    azure_openai_reasoning_endpoint: str = ""
    azure_openai_reasoning_api_version: str = "2024-06-01"
    azure_openai_reasoning_model: str = ""
    # Embeddings model (e.g. text-embedding-3-large) — AZURE_OPENAI_EMBEDDING_*
    azure_openai_embedding_model: str = ""
    azure_openai_embedding_key: str = ""
    azure_openai_embedding_endpoint: str = ""
    azure_openai_embedding_api_version: str = "2024-06-01"
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
