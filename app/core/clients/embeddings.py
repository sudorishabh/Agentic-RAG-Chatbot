import logging
from functools import lru_cache

import httpx
from langchain_openai import AzureOpenAIEmbeddings

from app.config import get_settings
from app.observability.metrics import record_event

logger = logging.getLogger(__name__)


def _record_response(response: httpx.Response) -> None:
    """Count every embedding response, and say so when Azure throttles.

    The SDK swallows a retried 429: the call succeeds and nothing upstream ever
    learns the deployment is at its quota, until the retry budget runs out and
    a document lands in ``documents_retry`` instead. This is the hook that makes
    throttling visible while it is still only costing time.

    Called by httpx before the body is read, so it touches the status and
    headers only — reading the payload here would consume a streamed response.
    """
    if response.status_code == 429:
        record_event("embedding_http", "throttled")
        logger.warning(
            "Embedding request throttled (429); Azure asked for %s seconds. "
            "Retrying within the configured budget of %d.",
            response.headers.get("retry-after", "an unstated number of"),
            get_settings().azure_openai_embedding_max_retries,
        )
    elif response.status_code >= 400:
        record_event("embedding_http", "error")
    else:
        record_event("embedding_http", "ok")


@lru_cache
def get_embeddings() -> AzureOpenAIEmbeddings:
    settings = get_settings()
    # Supplying the transport is what buys the hook above, so it also takes on
    # the SDK's own defaults — reusing its constants rather than restating them,
    # so this client stays configured like every other one the SDK builds.
    from openai._constants import DEFAULT_CONNECTION_LIMITS, DEFAULT_TIMEOUT

    http_client = httpx.Client(
        timeout=DEFAULT_TIMEOUT,
        limits=DEFAULT_CONNECTION_LIMITS,
        event_hooks={"response": [_record_response]},
    )
    return AzureOpenAIEmbeddings(
        http_client=http_client,
        azure_endpoint=settings.azure_openai_embedding_endpoint,
        api_key=settings.azure_openai_embedding_key,
        api_version=settings.azure_openai_embedding_api_version,
        azure_deployment=settings.azure_openai_embedding_model,
        dimensions=settings.azure_openai_embedding_dimensions,
        max_retries=settings.azure_openai_embedding_max_retries,
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
