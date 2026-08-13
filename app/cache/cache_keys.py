from __future__ import annotations

import hashlib

from app.config import get_settings


def _sha(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _pref_fingerprint() -> str:
    """Hash of the retrieval-preference settings so that toggling the feature or
    tuning its knobs self-invalidates the semantic cache (otherwise old-mode
    answers would be served until TTL and pollute before/after tuning
    comparisons)."""
    s = get_settings()
    return _sha(
        str(s.prefer_website_enabled),
        str(s.website_candidate_k),
        str(s.website_max_slots),
        str(s.website_chunk_floor),
        str(s.pdf_max_slots),
        str(s.pdf_high_confidence_floor),
        str(s.retrieval_top_k),
        str(s.retrieval_candidate_k),
        str(s.context_token_budget),
    )


def semantic_partition(top_k: int, answer_format: str) -> str:
    """Partition key for the semantic cache: retrieval-preference fingerprint +
    result width + answer format. A cached answer is only valid within the same
    partition, so retuning the preference knobs self-invalidates it.

    Caller identity is deliberately absent. The corpus is public and every
    caller retrieves over all of it, so two callers asking the same question
    are owed the same answer — partitioning by identity would only fragment
    the cache."""
    return _sha(_pref_fingerprint(), str(top_k), answer_format)
