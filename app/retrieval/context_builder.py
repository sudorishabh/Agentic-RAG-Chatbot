from __future__ import annotations

import logging
import math
from functools import lru_cache
from typing import Any, Sequence

from app.config import get_settings
from app.core.models.context import ContextBlock
from app.core.clients import get_qdrant_client
from app.retrieval.hybrid_search import Candidate

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4

__all__ = ["ContextBlock", "build_context"]


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


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _ids(payload: dict[str, Any]) -> set[str]:
    return {
        str(payload[k])
        for k in ("document_id", "pdf_id", "article_uuid")
        if payload.get(k)
    }


def _links(payload: dict[str, Any]) -> set[str]:
    return {
        str(payload[k])
        for k in ("linked_pdf_id", "linked_article_uuid")
        if payload.get(k)
    }


def _linked(a: dict[str, Any], b: dict[str, Any]) -> bool:
    ia, ib = _ids(a), _ids(b)
    if ia & ib:
        return True
    return bool(ia & _links(b) or ib & _links(a))


def _fetch_parents(parent_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
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


def _order_for_attention(blocks: list[ContextBlock]) -> list[ContextBlock]:
    if len(blocks) <= 2:
        ordered = list(blocks)
    else:
        head, tail = blocks[0::2], blocks[1::2]
        ordered = head + tail[::-1]
    for i, block in enumerate(ordered, start=1):
        block.n = i
    return ordered


def _is_website(payload: dict[str, Any]) -> bool:
    return payload.get("source_type") == "website"


def _same_source_two_formats(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """True when the pair is a website node and its own attached PDF — the same
    content in two formats, not a genuine conflict."""
    return {a.get("source_type"), b.get("source_type")} == {"website", "pdf_attachment"} and _linked(a, b)


def _admit(
    candidates: Sequence[Candidate],
    *,
    blocks: list[ContextBlock],
    block_vectors: list[list[float]],
    seen_parents: set[str],
    parents: dict[str, dict[str, Any]],
    spent: int,
    limit: int,
    token_budget: int,
    sim_threshold: float,
    max_add: int | None = None,
    floor: float | None = None,
) -> int:
    """Walk candidates in order, admitting each that survives parent-expand, dedup
    and the token budget, until `max_add` are added or `limit` total blocks is
    reached. Mutates blocks/block_vectors/seen_parents in place; returns the
    updated token spend. `floor` skips candidates below a raw-semantic relevance
    bar (used for the website slots)."""
    added = 0
    for cand in candidates:
        if len(blocks) >= limit or (max_add is not None and added >= max_add):
            break
        if floor is not None and cand.semantic_score < floor:
            continue
        key = cand.parent_id or cand.id
        if key in seen_parents:
            continue

        duplicate_of = None
        for kept, kvec in zip(blocks, block_vectors):
            if cand.vector and kvec and _cosine(cand.vector, kvec) >= sim_threshold:
                duplicate_of = kept
                break
        if duplicate_of is not None:
            seen_parents.add(key)
            if _linked(cand.payload, duplicate_of.payload):
                duplicate_of.also_available.append(dict(cand.payload))
            continue

        parent_payload = parents.get(cand.parent_id or "")
        text = (parent_payload or {}).get("chunk_text") or cand.text
        if not text.strip():
            continue
        cost = _count_tokens(text)
        if blocks and spent + cost > token_budget:
            continue
        seen_parents.add(key)
        spent += cost

        blocks.append(
            ContextBlock(
                n=len(blocks) + 1,
                text=text,
                payload=dict(cand.payload),
                score=cand.score,
            )
        )
        block_vectors.append(list(cand.vector))
        added += 1
    return spent


def build_context(
    candidates: Sequence[Candidate],
    *,
    limit: int | None = None,
    token_budget: int | None = None,
    segregate: bool = False,
    website_max_slots: int | None = None,
    website_chunk_floor: float | None = None,
    pdf_max_slots: int | None = None,
    pdf_high_confidence_floor: float | None = None,
) -> list[ContextBlock]:
    settings = get_settings()
    limit = limit or settings.retrieval_top_k
    token_budget = token_budget or settings.context_token_budget
    sim_threshold = settings.dedup_cosine_threshold
    if not candidates:
        return []

    parents = _fetch_parents([c.parent_id for c in candidates if c.parent_id])

    blocks: list[ContextBlock] = []
    block_vectors: list[list[float]] = []
    seen_parents: set[str] = set()
    spent = 0

    if segregate:
        # Website leads (capped + floor-gated); PDFs follow under a hard budget:
        # the top `pmax` PDF chunks unconditionally, then a single extra slot that
        # opens only for a high-confidence candidate — nothing past that is ever
        # admitted. Walking website first makes the final order website-first and
        # lets a website block win a website/PDF near-dup tie (the PDF then lands
        # in its also_available).
        wmax = website_max_slots if website_max_slots is not None else settings.website_max_slots
        floor = website_chunk_floor if website_chunk_floor is not None else settings.website_chunk_floor
        pmax = pdf_max_slots if pdf_max_slots is not None else settings.pdf_max_slots
        pfloor = (
            pdf_high_confidence_floor
            if pdf_high_confidence_floor is not None
            else settings.pdf_high_confidence_floor
        )
        website = [c for c in candidates if _is_website(c.payload)]
        others = [c for c in candidates if not _is_website(c.payload)]
        spent = _admit(
            website, blocks=blocks, block_vectors=block_vectors,
            seen_parents=seen_parents, parents=parents, spent=spent, limit=limit,
            token_budget=token_budget, sim_threshold=sim_threshold,
            max_add=wmax, floor=floor,
        )
        # Top PDFs, admitted unconditionally.
        spent = _admit(
            others, blocks=blocks, block_vectors=block_vectors,
            seen_parents=seen_parents, parents=parents, spent=spent, limit=limit,
            token_budget=token_budget, sim_threshold=sim_threshold,
            max_add=pmax,
        )
        # One extra PDF slot, gated on the high-confidence bar; never a further one.
        _admit(
            others, blocks=blocks, block_vectors=block_vectors,
            seen_parents=seen_parents, parents=parents, spent=spent, limit=limit,
            token_budget=token_budget, sim_threshold=sim_threshold,
            max_add=1, floor=pfloor,
        )
        ordered = blocks  # already website-first
        for i, block in enumerate(ordered, start=1):
            block.n = i
    else:
        _admit(
            candidates, blocks=blocks, block_vectors=block_vectors,
            seen_parents=seen_parents, parents=parents, spent=spent, limit=limit,
            token_budget=token_budget, sim_threshold=sim_threshold,
        )
        ordered = _order_for_attention(blocks)

    _flag_conflicts(ordered)
    return ordered


def _flag_conflicts(blocks: list[ContextBlock]) -> None:
    for i, a in enumerate(blocks):
        for b in blocks[i + 1 :]:
            if _linked(a.payload, b.payload) and not _same_source_two_formats(a.payload, b.payload):
                a.conflict = b.conflict = True
