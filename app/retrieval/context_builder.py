"""Context selection & window optimization (step 5, §6.4).

Turns the ranked candidate children into the numbered context blocks the LLM
sees:

1. **Parent-expand** — replace each winning child with its parent section, so the
   model reads the full section, not a 400-token sliver ("search small, read big").
2. **Deduplicate** — children that resolve to the same parent collapse to one
   block (and, later, near-duplicate parents across PDF/article are dropped, §9.2).
3. **Budget** — cap the total retrieved context in tokens (§6.4) and at ``limit``
   blocks; more context isn't automatically better.
4. **Number** — label each block ``[1] … [n]`` so the LLM cites by marker and the
   citation builder can map markers back to payloads.

Each block keeps the originating **child** payload for citation (it carries the
precise page number / source url / section) while showing the **parent** text to
the model.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Sequence

from app.config import get_settings
from app.deps import get_qdrant_client
from app.retrieval.hybrid_search import Candidate

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4


@dataclass
class ContextBlock:
    """One numbered unit of context handed to the LLM and mapped to a citation."""

    n: int
    text: str
    payload: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    # Set when this block disagrees with another top block (§9.3).
    conflict: bool = False
    # Alternate sources for the same material (dedup, §9.1) — list of payloads.
    also_available: list[dict[str, Any]] = field(default_factory=list)


@lru_cache(maxsize=1)
def _encoder() -> Any:
    try:
        import tiktoken

        return tiktoken.get_encoding("cl100k_base")
    except Exception:  # pragma: no cover - offline
        return None


def _count_tokens(text: str) -> int:
    enc = _encoder()
    if enc is not None:
        return len(enc.encode(text))
    return max(1, math.ceil(len(text) / _CHARS_PER_TOKEN))


def _fetch_parents(parent_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    """Fetch parent chunks by id → ``{parent_id: payload}`` (one Qdrant round-trip)."""
    ids = [pid for pid in dict.fromkeys(parent_ids) if pid]
    if not ids:
        return {}
    settings = get_settings()
    client = get_qdrant_client()
    try:
        records = client.retrieve(
            collection_name=settings.qdrant_collection, ids=ids, with_payload=True
        )
    except Exception:  # pragma: no cover - parent missing / store hiccup
        logger.exception("Parent fetch failed; falling back to child text.")
        return {}
    return {str(r.id): (r.payload or {}) for r in records}


def build_context(
    candidates: Sequence[Candidate],
    *,
    limit: int | None = None,
    token_budget: int | None = None,
) -> list[ContextBlock]:
    """Select, parent-expand, dedup, and budget the candidates into context blocks."""
    settings = get_settings()
    limit = limit or settings.retrieval_top_k
    token_budget = token_budget or settings.context_token_budget
    if not candidates:
        return []

    parents = _fetch_parents([c.parent_id for c in candidates if c.parent_id])

    blocks: list[ContextBlock] = []
    seen_parents: set[str] = set()
    spent = 0
    for cand in candidates:
        if len(blocks) >= limit:
            break
        # Dedup: one block per parent (children of the same section collapse).
        key = cand.parent_id or cand.id
        if key in seen_parents:
            continue
        seen_parents.add(key)

        parent_payload = parents.get(cand.parent_id or "")
        text = (parent_payload or {}).get("chunk_text") or cand.text
        if not text.strip():
            continue
        cost = _count_tokens(text)
        if blocks and spent + cost > token_budget:
            continue  # over budget — skip this one, a later block may still fit
        spent += cost

        blocks.append(
            ContextBlock(
                n=len(blocks) + 1,
                text=text,
                payload=dict(cand.payload),  # child payload → precise citation
                score=cand.score,
            )
        )
    return blocks
