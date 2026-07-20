from __future__ import annotations

import hashlib
import logging
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


def _pref_fingerprint() -> str:
    """Hash of the retrieval-preference settings so that toggling the feature or
    tuning its knobs self-invalidates both caches (otherwise old-mode answers
    would be served until TTL and pollute before/after tuning comparisons)."""
    s = get_settings()
    return _sha(
        str(s.prefer_website_enabled),
        str(s.website_candidate_k),
        str(s.website_max_slots),
        str(s.website_chunk_floor),
        str(s.retrieval_top_k),
        str(s.retrieval_candidate_k),
        str(s.context_token_budget),
    )


def _identity_scope(tenant_id: str, user_groups: Sequence[str], top_k: int) -> str:
    return f"{tenant_id}|{','.join(sorted(user_groups))}|{top_k}"


def semantic_partition(
    tenant_id: str, user_groups: Sequence[str], top_k: int, answer_format: str
) -> str:
    """Partition key for the semantic cache: corpus version + retrieval-preference
    fingerprint + caller identity + answer format. A cached answer is only valid
    within the same partition, so bumping the corpus, retuning the preference
    knobs, or crossing an ACL/tenant boundary self-invalidates it."""
    return _sha(
        corpus_version(),
        _pref_fingerprint(),
        _identity_scope(tenant_id, user_groups, top_k),
        answer_format,
    )
