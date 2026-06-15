"""Query understanding (step 1, §6.1).

Cheap, on-the-hot-path preprocessing of the raw user turn before retrieval:

* **Rewrite** — resolve pronouns / ellipsis against the chat history ("what about
  *it*?" → a standalone search query).
* **Intent routing** — classify the turn as:
    - ``qa``        → semantic Q&A, run the full RAG pipeline;
    - ``structured``→ exact lookup / aggregate, route to the Drupal JSON:API
                      router (§7) instead of vector search;
    - ``chitchat``  → greeting / meta, answer directly, skip retrieval.
* **Filter extraction** — pull only *obvious, controlled-vocabulary* facets
  (source type, language) into hard filters. The doc is explicit: be conservative,
  over-filtering kills recall — so free-text categories/tags are left out.

One structured LLM call does all of it; on any failure we fall back to a safe
passthrough (treat as ``qa``, search the verbatim question, no filters).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

from pydantic import BaseModel, Field

from app.generation.llm_client import get_llm

logger = logging.getLogger(__name__)

Intent = Literal["qa", "structured", "chitchat"]

_ANALYSIS_SYSTEM = (
    "You are the query-understanding stage of a retrieval system over an "
    "enterprise corpus of PDFs and website articles. Given the conversation so "
    "far and the latest user turn, produce a compact analysis.\n"
    "- intent: 'qa' for any question answerable from document content; "
    "'structured' ONLY for exact lookups by field or counting/aggregation "
    "(e.g. 'how many reports were published in 2024', 'show the article titled X'); "
    "'chitchat' for greetings, thanks, or meta questions needing no documents.\n"
    "- search_query: a standalone, self-contained rewrite of the latest turn with "
    "pronouns and references resolved from the history. Keep it faithful; do not "
    "add facts.\n"
    "- source_type: 'pdf' or 'article' ONLY if the user explicitly restricts to "
    "documents/PDFs or to website articles/news; otherwise null.\n"
    "- language: a two-letter code ONLY if the user explicitly asks in/about a "
    "specific language; otherwise null."
)


class QueryAnalysis(BaseModel):
    intent: Intent = "qa"
    search_query: str = Field(description="Standalone, pronoun-resolved query.")
    source_type: str | None = None
    language: str | None = None


@dataclass
class ProcessedQuery:
    original: str
    search_query: str
    intent: Intent = "qa"
    source_type: str | None = None
    language: str | None = None
    # Qdrant FieldConditions derived from the extracted facets (§5.4).
    filters: list[Any] = field(default_factory=list)

    @property
    def needs_retrieval(self) -> bool:
        return self.intent != "chitchat"


def _format_history(history: Sequence[dict[str, str]] | None, max_turns: int = 6) -> str:
    if not history:
        return "(no prior conversation)"
    recent = list(history)[-max_turns:]
    return "\n".join(f"{t.get('role', 'user')}: {t.get('content', '')}" for t in recent)


def _facet_filters(analysis: QueryAnalysis) -> list[Any]:
    """Map the conservative extracted facets to Qdrant conditions (keyword fields)."""
    from qdrant_client.models import FieldCondition, MatchValue

    conditions: list[Any] = []
    if analysis.source_type in ("pdf", "article"):
        conditions.append(
            FieldCondition(key="source_type", match=MatchValue(value=analysis.source_type))
        )
    if analysis.language:
        conditions.append(
            FieldCondition(key="language", match=MatchValue(value=analysis.language))
        )
    return conditions


def process(question: str, history: Sequence[dict[str, str]] | None = None) -> ProcessedQuery:
    """Analyze one user turn into a :class:`ProcessedQuery`. Never raises."""
    passthrough = ProcessedQuery(original=question, search_query=question, intent="qa")
    try:
        structured = get_llm(temperature=0).with_structured_output(QueryAnalysis)
        analysis: QueryAnalysis = structured.invoke(
            [
                ("system", _ANALYSIS_SYSTEM),
                (
                    "human",
                    f"Conversation so far:\n{_format_history(history)}\n\n"
                    f"Latest user turn:\n{question}",
                ),
            ]
        )
    except Exception:
        logger.warning("Query analysis failed; using passthrough.", exc_info=True)
        return passthrough

    search_query = (analysis.search_query or question).strip() or question
    return ProcessedQuery(
        original=question,
        search_query=search_query,
        intent=analysis.intent,
        source_type=analysis.source_type,
        language=analysis.language,
        filters=_facet_filters(analysis),
    )
