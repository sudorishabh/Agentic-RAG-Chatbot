from __future__ import annotations

import hashlib
from typing import Sequence

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


def _identity_scope(tenant_id: str, user_groups: Sequence[str], top_k: int) -> str:
    return f"{tenant_id}|{','.join(sorted(user_groups))}|{top_k}"


def semantic_partition(
    tenant_id: str, user_groups: Sequence[str], top_k: int, answer_format: str
) -> str:
    """Partition key for the semantic cache: retrieval-preference fingerprint +
    caller identity + answer format. A cached answer is only valid within the
    same partition, so retuning the preference knobs or crossing an ACL/tenant
    boundary self-invalidates it."""
    return _sha(
        _pref_fingerprint(),
        _identity_scope(tenant_id, user_groups, top_k),
        answer_format,
    )
