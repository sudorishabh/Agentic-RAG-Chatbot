from __future__ import annotations

import hashlib
import json
import logging
import math
from typing import Any, Sequence

from app.config import get_settings

logger = logging.getLogger(__name__)

_NS = "rag"
_CORPUS_KEY = f"{_NS}:corpus_version"


def _client() -> Any | None:
    from app.deps import get_redis

    try:
        return get_redis()
    except Exception:  # pragma: no cover - misconfigured redis
        logger.warning("Redis unavailable; caching disabled.", exc_info=True)
        return None


def _sha(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def corpus_version() -> str:
    client = _client()
    if client is None:
        return "0"
    try:
        return client.get(_CORPUS_KEY) or "0"
    except Exception:  # pragma: no cover
        return "0"


def bump_corpus_version() -> None:
    client = _client()
    if client is None:
        return
    try:
        client.incr(_CORPUS_KEY)
    except Exception:  # pragma: no cover
        logger.warning("Could not bump corpus version.", exc_info=True)


def _get_json(key: str) -> Any | None:
    client = _client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception:  # pragma: no cover
        logger.warning("Cache read failed for %s", key, exc_info=True)
        return None


def _set_json(key: str, value: Any, ttl: int) -> None:
    client = _client()
    if client is None:
        return
    try:
        client.set(key, json.dumps(value), ex=ttl)
    except Exception:  # pragma: no cover
        logger.warning("Cache write failed for %s", key, exc_info=True)


def get_embedding(text: str) -> list[float] | None:
    settings = get_settings()
    if not settings.embedding_cache_enabled:
        return None
    key = f"{_NS}:emb:{_sha(settings.azure_openai_embedding_model, text)}"
    return _get_json(key)


def set_embedding(text: str, vector: Sequence[float]) -> None:
    settings = get_settings()
    if not settings.embedding_cache_enabled:
        return
    key = f"{_NS}:emb:{_sha(settings.azure_openai_embedding_model, text)}"
    _set_json(key, list(vector), settings.embedding_cache_ttl)


def response_signature(
    question: str, *, tenant_id: str, user_groups: Sequence[str], top_k: int
) -> str:
    scope = f"{tenant_id}|{','.join(sorted(user_groups))}|{top_k}"
    return _sha(corpus_version(), question.strip().lower(), scope)


def get_response(signature: str) -> dict[str, Any] | None:
    if not get_settings().response_cache_enabled:
        return None
    return _get_json(f"{_NS}:resp:{signature}")


def set_response(signature: str, payload: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.response_cache_enabled:
        return
    _set_json(f"{_NS}:resp:{signature}", payload, settings.response_cache_ttl)


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _sem_key() -> str:
    return f"{_NS}:sem:{corpus_version()}"


def semantic_lookup(query_vector: Sequence[float]) -> dict[str, Any] | None:
    settings = get_settings()
    client = _client()
    if client is None or not settings.semantic_cache_enabled or not query_vector:
        return None
    try:
        entries = client.lrange(_sem_key(), 0, settings.semantic_cache_max - 1)
    except Exception:  # pragma: no cover
        return None
    best, best_sim = None, settings.semantic_cache_threshold
    for raw in entries:
        try:
            entry = json.loads(raw)
        except Exception:
            continue
        sim = _cosine(query_vector, entry.get("v", []))
        if sim >= best_sim:
            best, best_sim = entry.get("p"), sim
    return best


def semantic_store(query_vector: Sequence[float], payload: dict[str, Any]) -> None:
    settings = get_settings()
    client = _client()
    if client is None or not settings.semantic_cache_enabled or not query_vector:
        return
    key = _sem_key()
    try:
        client.lpush(key, json.dumps({"v": list(query_vector), "p": payload}))
        client.ltrim(key, 0, settings.semantic_cache_max - 1)
        client.expire(key, settings.response_cache_ttl)
    except Exception:  # pragma: no cover
        logger.warning("Semantic cache store failed.", exc_info=True)
