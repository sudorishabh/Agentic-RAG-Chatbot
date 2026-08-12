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


def embedding_version() -> str:
    """Identity of the configuration a stored vector was produced by.

    Stamped on every child point and compared before a vector is reused, so
    repointing the deployment or changing the output dimension re-embeds instead
    of leaving the collection a silent mix of two models' vectors. Mirrors
    ``app.ingestion.enrich.abstract_version``, which does the same for cached
    abstracts.

    Deliberately readable rather than a digest: both parts are short and not
    secret, so the index says which model produced each point. The endpoint and
    api-version are left out — moving region or bumping the wire protocol does
    not change what a vector means, and folding them in would re-embed the
    corpus for an infrastructure move. The key is left out because rotating a
    secret must not invalidate vectors.

    Lives beside :func:`get_embeddings`, reading the same settings, so the
    identity cannot drift from the client it describes. The one thing it cannot
    see is a deployment repointed *in place* to a different model: the name and
    dimension are unchanged, so that still requires clearing the collection.
    """
    settings = get_settings()
    return (
        f"{settings.azure_openai_embedding_model}:"
        f"{settings.azure_openai_embedding_dimensions or 'native'}"
    )


def embed_query(text: str) -> list[float]:
    return get_embeddings().embed_query(text)
