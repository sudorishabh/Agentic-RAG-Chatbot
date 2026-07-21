"""Structured (database-intent) answer adapter.

Answers catalog questions by delegating to the Database Planner + tools
(`app.retrieval.database`). This module now holds only:

- the LLM parse fallback (`parse_structured` / `StructuredQuery`) for when no
  usable analysis was supplied;
- `answer_structured`, the thin adapter `rag._prepare` calls (unchanged signature).

The catalog operations, filters, entity handling, rendering, and the lookup->QA
chaining (`resolve_lookup_chain`) live in `app.retrieval.database` (see
docs/database-tool-registry.md).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal, Sequence

from pydantic import BaseModel

from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES

if TYPE_CHECKING:
    from app.retrieval.query_processor import QueryAnalysis

logger = logging.getLogger(__name__)

Operation = Literal["lookup", "list", "count", "distribution"]
GroupBy = Literal["theme", "content_type", "author", "year"]

_PARSE_SYSTEM = (
    "Extract structured-query parameters from the user's request about a content "
    "repository of news, articles, reports, projects, events and research papers.\n"
    "- operation: 'count' for how-many/aggregate; 'distribution' for a breakdown "
    "per group ('how many per theme', 'spread across content types'); 'lookup' "
    "for a single specific item; 'list' for browse/enumerate.\n"
    "- bundle: the content type if implied, one of: " + ", ".join(DEFAULT_BUNDLES) +
    "; else null.\n"
    "- theme: the thematic area / topic / category name if the request is scoped "
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
    from app.generation.llm_client import get_structured_llm

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


def answer_structured(
    question: str,
    history: Sequence[dict[str, str]] | None = None,
    *,
    analysis: QueryAnalysis | None = None,
) -> dict[str, Any] | None:
    """Answer a catalog (database-intent) query via the Database Planner + tools.

    The unified analysis already extracted the structured slots — reuse it and let
    the planner pick the tool; parse only when no usable analysis came. Signature
    is unchanged so rag._prepare is untouched. Returns None (fall through to
    semantic search) on an unusable plan or a guarded/empty tool result.
    """
    from app.retrieval.database import planner

    slots = (
        analysis
        if (analysis is not None and analysis.operation)
        else parse_structured(question, history)
    )
    if slots is None:
        return None
    output_format = analysis.answer_format if analysis is not None else "default"
    results = planner.execute(
        planner.plan(slots, output_format=output_format), question=question
    )
    if not results or not results[0].ok:
        return None
    result = results[0]
    used_chunks = len(result.data["records"]) if "records" in result.data else 0
    return {
        "answer": result.rendered,
        "citations": result.citations,
        "intent": "structured",
        "used_chunks": used_chunks,
        "conflict": False,
        "cached": False,
    }
