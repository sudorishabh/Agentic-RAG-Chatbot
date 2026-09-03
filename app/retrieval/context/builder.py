from __future__ import annotations

import logging
import math
from functools import lru_cache
from typing import Any, Sequence

from app.config import get_settings
from app.core.models.context import ContextBlock, source_kind
from app.core.clients import get_qdrant_client
from app.observability import retrieval_log
from app.retrieval.search.hybrid_search import _NON_SEARCHABLE_SECTIONS, Candidate

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
    with retrieval_log.qdrant_call(
        "retrieve",
        stage="parent_fetch",
        request=lambda: {
            "collection": settings.qdrant_collection,
            "ids": ids,
            "requested": len(ids),
        },
    ) as call:
        try:
            records = client.retrieve(
                collection_name=settings.qdrant_collection, ids=ids, with_payload=True
            )
        except Exception as exc:  # pragma: no cover - parent missing / store hiccup
            call.fail(exc)
            logger.exception("Parent fetch failed; falling back to child text.")
            return {}
        call.qdrant_results(records)
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


# Page fields that describe the *child* chunk specifically, and are therefore
# wrong for a block that carries its parent's text instead.
_CHILD_PAGE_FIELDS = ("page_number", "page_range", "overlap_page_range")


def _is_excluded(payload: dict[str, Any] | None) -> bool:
    """Whether this chunk is one of the non-substantive sections search drops.

    Shares ``hybrid_search``'s list rather than repeating it: the query filter
    and this check have to name the same sections, or the exclusion holds on the
    way in and leaks on the way out.
    """
    return bool(payload) and payload.get("section_type") in _NON_SEARCHABLE_SECTIONS


def _admissible_text(
    cand: Candidate, parents: dict[str, dict[str, Any]]
) -> tuple[str, dict[str, Any] | None] | None:
    """The text this candidate contributes and the parent it came from, or None.

    Section exclusion has to be decided on the text that ends up in the block,
    not on the candidate that carried it. ``build_filter`` drops toc /
    references / glossary chunks from every search, but parent expansion then
    replaces the matched text wholesale — so a body child inside a bibliography
    window used to carry the whole bibliography past a filter that had already
    excluded it.

    Order of preference, each step falling to the next:

    1. the parent's text, when there is a parent and it is substantive;
    2. the child's own text, when *it* is substantive — this is both the orphan
       case and the excluded-parent case, where the child is the largest
       admissible passage available;
    3. nothing: neither is substantive, so the candidate contributes no context.

    An excluded child under a substantive parent still expands (case 1). The
    classifier reads content rather than headings, so a citation-dense run
    inside a findings section is a fragment of that section; the section is what
    the block carries, and it is admissible.
    """
    parent = parents.get(cand.parent_id or "") or None
    parent_text = (parent or {}).get("chunk_text") or ""
    if parent_text and not _is_excluded(parent):
        return parent_text, parent
    if _is_excluded(cand.payload):
        return None
    return cand.text, None


def _block_payload(
    child: dict[str, Any], parent: dict[str, Any] | None
) -> dict[str, Any]:
    """The child's payload, re-pointed at the pages of the text being shown.

    Identity stays the child's — the chunk that matched is the chunk the
    citation resolves to — but provenance has to follow the text. Parent
    expansion swaps in a passage spanning the whole parent window, and citing
    the child's single page for it claims a narrower source than the evidence:
    the reader is pointed at page 7 for a statement that may live on page 9.

    A parent that carries no ``page_range`` (an unpaginated source) leaves the
    block with no page at all, rather than keeping the child's. That is the only
    honest option — the alternative is stretching one page number over text it
    does not describe.
    """
    payload = dict(child)
    if parent is None:
        return payload
    for field_name in _CHILD_PAGE_FIELDS:
        payload.pop(field_name, None)
    span = parent.get("page_range")
    if isinstance(span, (list, tuple)) and len(span) == 2:
        payload["page_range"] = list(span)
        payload["page_number"] = span[0]
    return payload


def _same_document(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """True when both payloads describe one and the same document."""
    return bool(_ids(a) & _ids(b))


def _same_source_two_formats(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """True when the pair is a website node and its own attached PDF — the same
    content in two formats, not a genuine conflict.

    Compares the *normalized* kind, so a legacy ``article`` point pairs with its
    attachment exactly as a ``website`` one does; matching on the raw value let
    that pair through as a contradiction.
    """
    return {source_kind(a), source_kind(b)} == {"website", "pdf_attachment"} and _linked(a, b)


def _conflicting(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Whether two blocks are sources that might contradict each other.

    A conflict is a disagreement *between sources*, so it takes two distinct
    documents. ``_ids`` unions ``document_id``/``pdf_id``/``article_uuid``, and
    an overlap on any of them means one document reached two ways — most often
    two sections of one report, since ``_admit`` deduplicates by parent rather
    than by document. Flagging those marked the majority of live answers as
    self-contradictory, which is both wrong and load-bearing: the flag reaches
    the API response and the prompt's "prefer the later page date" rule.

    Sharing a *parent node* is deliberately not a conflict. Editions of one
    publication do arrive that way — separate attachment documents under a
    single node — but so does every catalogue page, and on this corpus the
    latter dominates: the largest such nodes carry 69 financial statements, 68
    announcements, 43 brochures. The two shapes are indistinguishable from the
    payload (same node, same title, same ``effective_start_date``), so treating the
    relationship as a disagreement flagged roughly a quarter of answers, mostly
    wrongly. Separating them needs a content signal and a threshold measured
    against a labelled set, not guessed; until then the honest reading of two
    files on one page is that they are two files on one page.
    """
    if _same_document(a, b):
        return False
    if _same_source_two_formats(a, b):
        return False
    return _linked(a, b)


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

        # Which text won decides whose provenance the block carries, so the two
        # are resolved together and never separately.
        admissible = _admissible_text(cand, parents)
        if admissible is None:
            continue
        text, parent_payload = admissible
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
                payload=_block_payload(cand.payload, parent_payload),
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
            if _conflicting(a.payload, b.payload):
                a.conflict = b.conflict = True
