from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_chat_deployment: str = ""
    azure_openai_embedding_deployment: str = ""
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "documents"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
