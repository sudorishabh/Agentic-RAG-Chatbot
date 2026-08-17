import email.utils
import logging
import threading
import time
from functools import lru_cache

import httpx
from langchain_openai import AzureOpenAIEmbeddings

from app.config import get_settings
from app.observability.metrics import record_event

logger = logging.getLogger(__name__)


class _ThrottleGate:
    """A deployment-wide pause, honoured by every thread sharing this client.

    Retries alone do not stop `ingest_workers` from re-colliding: each worker
    backs off privately, so while one waits the others keep spending the very
    quota it is waiting for, and the deployment stays saturated. The gate makes
    one worker's 429 pause all of them — the quota is a property of the Azure
    deployment, so the backoff has to be too.

    Held as a deadline rather than a countdown so concurrent 429s collapse into
    a single wait instead of stacking into a multiple of it.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._not_before = 0.0

    def hold(self, seconds: float) -> None:
        """Bar requests for `seconds`. Never shortens an existing hold."""
        until = time.monotonic() + seconds
        with self._lock:
            self._not_before = max(self._not_before, until)

    def wait(self) -> float:
        """Block until the hold expires. Returns the seconds actually slept."""
        with self._lock:
            delay = self._not_before - time.monotonic()
        # Deliberately outside the lock: a thread sleeping here must not stop
        # another from recording a longer hold.
        if delay <= 0:
            return 0.0
        time.sleep(delay)
        return delay


_gate = _ThrottleGate()


def _retry_after_seconds(response: httpx.Response, ceiling: float) -> float:
    """`retry-after` as seconds, clamped to `ceiling`.

    The header is either a count of seconds or an HTTP-date; Azure sends the
    former, but both are legal and a misread one would either stall the run or
    fail to hold at all. An absent or unparseable value falls back to the
    ceiling — pausing too long is recoverable, pausing too little is what got
    us throttled.
    """
    raw = response.headers.get("retry-after")
    if raw is None:
        return ceiling
    try:
        seconds = float(raw)
    except ValueError:
        try:
            seconds = email.utils.parsedate_to_datetime(raw).timestamp() - time.time()
        except (TypeError, ValueError):
            return ceiling
    return max(0.0, min(seconds, ceiling))


def _await_gate(request: httpx.Request) -> None:
    """Hold every outgoing embedding request behind the shared pause."""
    slept = _gate.wait()
    if slept > 0:
        logger.info("Held an embedding request %.1fs behind the throttle gate.", slept)


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
        settings = get_settings()
        pause = _retry_after_seconds(
            response, settings.azure_openai_embedding_max_throttle_seconds
        )
        _gate.hold(pause)
        record_event("embedding_http", "throttled")
        logger.warning(
            "Embedding request throttled (429); pausing all embedding for %.1fs. "
            "Retrying within the configured budget of %d.",
            pause,
            settings.azure_openai_embedding_max_retries,
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
        event_hooks={"request": [_await_gate], "response": [_record_response]},
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
