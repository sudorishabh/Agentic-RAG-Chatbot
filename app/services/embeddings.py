from functools import lru_cache

from langchain_openai import AzureOpenAIEmbeddings

from app.core.config import get_settings


@lru_cache
def get_embeddings() -> AzureOpenAIEmbeddings:
    settings = get_settings()
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_embedding_deployment,
    )
