from functools import lru_cache

from langchain_openai import AzureChatOpenAI

from app.config import get_settings


@lru_cache
def get_llm(temperature: float | None = None, streaming: bool = False) -> AzureChatOpenAI:
    """Standard chat model"""
    settings = get_settings()
    return _build_llm(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_model,
        temperature=temperature,
        streaming=streaming,
    )


@lru_cache
def get_reasoning_llm(
    temperature: float | None = None, streaming: bool = False
) -> AzureChatOpenAI:
    """Reasoning chat model"""
    settings = get_settings()
    return _build_llm(
        endpoint=settings.azure_openai_reasoning_endpoint,
        api_key=settings.azure_openai_reasoning_api_key,
        api_version=settings.azure_openai_reasoning_api_version,
        deployment=settings.azure_openai_reasoning_model,
        temperature=temperature,
        streaming=streaming,
    )


def get_structured_llm(streaming: bool = False) -> AzureChatOpenAI:
    """Chat model for structured/deterministic extraction calls (query
    understanding, routing, rerank, faithfulness).

    Uses the configured ``llm_structured_temperature``; when that is ``None`` the
    temperature parameter is omitted entirely, which reasoning models (gpt-5 /
    o-series) require — they reject any value other than the default.
    """
    return get_llm(
        temperature=get_settings().llm_structured_temperature, streaming=streaming
    )


def _build_llm(
    *,
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment: str,
    temperature: float | None,
    streaming: bool,
) -> AzureChatOpenAI:
    kwargs = {
        "azure_endpoint": endpoint,
        "api_key": api_key,
        "api_version": api_version,
        "azure_deployment": deployment,
        "streaming": streaming,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return AzureChatOpenAI(**kwargs)
