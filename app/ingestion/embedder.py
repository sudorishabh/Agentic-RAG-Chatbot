from functools import lru_cache

from langchain_openai import AzureOpenAIEmbeddings

from app.config import get_settings


@lru_cache
def get_embeddings() -> AzureOpenAIEmbeddings:
    settings = get_settings()
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_embedding_endpoint,
        api_key=settings.azure_openai_embedding_key,
        api_version=settings.azure_openai_embedding_api_version,
        azure_deployment=settings.azure_openai_embedding_model,
        dimensions=settings.azure_openai_embedding_dimensions,
    )


def embed_query(text: str) -> list[float]:
    return get_embeddings().embed_query(text)
