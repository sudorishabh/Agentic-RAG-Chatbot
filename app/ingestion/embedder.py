from functools import lru_cache
from langchain_openai import AzureOpenAIEmbeddings
from app.config import get_settings


@lru_cache
def get_embeddings() -> AzureOpenAIEmbeddings:
    """Azure OpenAI embeddings"""
    settings = get_settings()
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_embedding_endpoint,
        api_key=settings.azure_openai_embedding_key,
        api_version=settings.azure_openai_embedding_api_version,
        azure_deployment=settings.azure_openai_embedding_model,
    )


def embed_query_cached(text: str) -> list[float]:
    """Embed a query, served from the Redis embedding cache when present (§10.3).

    Falls straight through to the model when Redis isn't configured.
    """
    from app.cache import redis_cache

    cached = redis_cache.get_embedding(text)
    if cached is not None:
        return cached
    vector = get_embeddings().embed_query(text)
    redis_cache.set_embedding(text, vector)
    return vector
