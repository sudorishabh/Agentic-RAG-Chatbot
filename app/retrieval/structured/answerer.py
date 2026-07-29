"""Structured (database-intent) answer adapter.

Answers catalog questions by delegating to the Database Planner + tools
(`app.retrieval.structured`). This module holds only:

- the LLM parse fallback (`parse_structured` / `StructuredQuery`) for when no
  usable analysis was supplied;
- `answer_structured`, the thin adapter the query pipeline calls.

The catalog operations, filters, entity handling, rendering, and the lookup->QA
chaining (`resolve_lookup_chain`) live in `app.retrieval.structured` (see
docs/database-tool-registry.md). The name is source-agnostic on purpose: this
adapter has no Drupal-specific logic — only the underlying bundle list does.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Literal, Sequence

from pydantic import BaseModel

from app.config import get_settings
from app.retrieval.structured.prompt import BUNDLE_LIST, COLLECTIVE_WORD_WARNING, VOCABULARY
from app.retrieval.structured.types import ToolResult

if TYPE_CHECKING:
    from app.retrieval.query_processor import QueryAnalysis

logger = logging.getLogger(__name__)

Operation = Literal["lookup", "list", "count", "distribution", "list_themes"]
GroupBy = Literal["theme", "content_type", "author", "year"]

_PARSE_SYSTEM = (
    "Extract structured-query parameters from the user's request about a content "
    "repository of news, articles, reports, projects, events and research papers.\n"
    + VOCABULARY + "\n"
    "- operation: 'count' for how-many/aggregate; 'distribution' for a breakdown "
    "per group ('how many per theme', 'spread across content types'); 'lookup' "
    "for a single specific item; 'list' for browse/enumerate; 'list_themes' to "
    "enumerate the themes/topics the collection covers ('what themes are there?').\n"
    "- bundle: the specific content type when the user names one, one of: "
    + BUNDLE_LIST + ". " + COLLECTIVE_WORD_WARNING + "\n"
    "- theme: the thematic area / topic / theme name if the request is scoped "
    "to one (e.g. 'under the Climate theme', 'in the Energy area'); else null.\n"
    "- group_by: for 'distribution' only — the dimension to break down by: "
    "'theme', 'content_type', 'author', or 'year'; else null.\n"
    "- title_contains: a title keyword if the user names/quotes a title; else null.\n"
    "- author: an author/person name if specified; else null.\n"
    "- year: a four-digit year if a specific year is referenced; else null.\n"
    "- date_from / date_to: an inclusive start and exclusive end ISO date "
    "(YYYY-MM-DD) bounding any date or period mentioned. For a single day set "
    "date_from to that day and date_to to the next day; for a month or year span "
    "it; for 'since'/'after' set only date_from; for 'before'/'until' set only "
    "date_to; else both null.\n"
    "- limit: how many items to return for list/lookup (default 10)."
)


class StructuredQuery(BaseModel):
    operation: Operation = "list"
    bundle: str | None = None
    theme: str | None = None
    group_by: GroupBy | None = None
    title_contains: str | None = None
    author: str | None = None
    year: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    limit: int = 10


def parse_structured(
    question: str, history: Sequence[dict[str, str]] | None = None
) -> StructuredQuery | None:
    """LLM fallback parse of the structured slots, used when no usable analysis
    was supplied. None on failure."""
    from app.core.clients.llm import get_structured_llm

    convo = ""
    if history:
        convo = "\n".join(f"{t.get('role')}: {t.get('content')}" for t in list(history)[-4:])
    try:
        model = get_structured_llm().with_structured_output(StructuredQuery)
        return model.invoke(
            [
                ("system", _PARSE_SYSTEM),
                ("human", f"Conversation:\n{convo}\n\nRequest: {question}"),
            ]
        )
    except Exception:
        logger.warning("Structured-query parse failed.", exc_info=True)
        return None


# Collective words that mean "everything published", not one content type. The
# classifier inconsistently collapses these onto the research_papers bundle,
# under-counting a person's output (10 papers instead of the 21 papers+articles).
_GENERIC_SCOPE = re.compile(r"\b(publications?|works|writings|output|everything)\b", re.I)


def _spans_all_content(question: str, bundle: str | None) -> bool:
    """True when a generic collective term (not a type the user actually named)
    is what set ``bundle`` — the count/list must then span all content types.

    Detected structurally, so it stays robust to the classifier's nondeterminism:
    a generic term is present AND none of the resolved bundle's own label words
    appear in the question. 'how many publications from X' -> clear the bundle;
    'how many research paper publications' -> keep it (the type was named)."""
    if not bundle or not _GENERIC_SCOPE.search(question):
        return False
    from app.retrieval.structured.entities import entity_label

    label_words = set(re.findall(r"[a-z]+", f"{bundle} {entity_label(bundle, 2)}".lower()))
    question_words = set(re.findall(r"[a-z]+", question.lower()))
    return not (label_words & question_words)


# error_kind values that mean "the filter was understood but could not be
# honored" — the answer is the result's `rendered` message, not a cue to guess
# via semantic search. Every other ok=False (unknown entity, no matching
# records, a query failure) keeps today's fall-through behavior.
_TERMINAL_ERROR_KINDS = frozenset({"unresolved", "ambiguous"})


def _terminal_result(results: list[ToolResult]) -> ToolResult | None:
    """The first failed result whose error is terminal, if any."""
    for result in results:
        if not result.ok and result.error_kind in _TERMINAL_ERROR_KINDS:
            return result
    return None


def _compose(results: list[ToolResult]) -> dict[str, Any]:
    """Merge the successful tool results into one structured answer: stack the
    rendered sections and renumber citations sequentially across them. A single
    result (the v1 deterministic plan) round-trips unchanged."""
    bodies: list[str] = []
    citations: list[dict[str, Any]] = []
    used_chunks = 0
    for result in results:
        if result.rendered:
            bodies.append(result.rendered)
        for citation in result.citations:
            citations.append({**citation, "n": len(citations) + 1})
        used_chunks += len(result.data.get("records", []))
    return {
        "answer": "\n\n".join(bodies),
        "citations": citations,
        "intent": "structured",
        "used_chunks": used_chunks,
        "conflict": False,
        "cached": False,
    }


def answer_structured(
    question: str,
    history: Sequence[dict[str, str]] | None = None,
    *,
    analysis: QueryAnalysis | None = None,
) -> dict[str, Any] | None:
    """Answer a catalog (database-intent) query via the Database Planner + tools.

    The unified analysis already extracted the structured slots — reuse it and let
    the planner pick the tool; parse only when no usable analysis came. Returns
    None (fall through to semantic search) on an unusable plan or a guarded/empty
    tool result — unless `entity_resolution_enabled` is on and every result
    failed with one of them terminal (an unresolved or ambiguous filter), in
    which case its `rendered` message is the answer (see `_terminal_result`).
    The flag gates only this fall-through change; it does not disable the
    catalog tools themselves.
    """
    from app.retrieval.structured import planner

    slots = (
        analysis
        if (analysis is not None and analysis.operation)
        else parse_structured(question, history)
    )
    if slots is None:
        return None
    # A generic "publications / works" ask must count across every content type;
    # drop a bundle the classifier inferred from that collective word so the total
    # is not silently narrowed to one type (see _spans_all_content).
    if _spans_all_content(question, getattr(slots, "bundle", None)):
        slots.bundle = None
    output_format = analysis.answer_format if analysis is not None else "default"
    db_plan = None
    if get_settings().database_multi_call_enabled:
        db_plan = planner.plan_multi(question, output_format=output_format)
    if db_plan is None:  # disabled, or the LLM planner produced nothing usable
        db_plan = planner.plan(slots, output_format=output_format)
    results = planner.execute(db_plan, question=question)
    ok = [r for r in results if r.ok]
    if not ok:
        terminal = _terminal_result(results) if get_settings().entity_resolution_enabled else None
        return _compose([terminal]) if terminal is not None else None
    return _compose(ok)
