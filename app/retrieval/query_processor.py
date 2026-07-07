from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Sequence

from pydantic import BaseModel, Field

from app.generation.llm_client import get_structured_llm

logger = logging.getLogger(__name__)

Intent = Literal["qa", "structured", "chitchat"]
# How the user wants the answer shaped. Detected from the turn; used downstream
# to steer generation (and table-aware retrieval). 'default' = let the model
# choose the natural shape.
AnswerFormat = Literal["default", "list", "table", "summary", "detailed"]

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
    "- answer_format: how the user wants the answer shaped. "
    "'table' if they ask for a table / tabular data / columns / 'in a table' or "
    "compare items across attributes; "
    "'list' if they ask to list / enumerate / give bullet points / steps; "
    "'summary' if they ask for a brief summary / overview / 'in short' / TL;DR; "
    "'detailed' if they ask for an in-depth / comprehensive / thorough explanation; "
    "otherwise 'default'.\n"
    "- source_type: 'pdf' or 'website' ONLY if the user explicitly restricts to "
    "documents/PDFs or to website content (articles/news/pages); otherwise null.\n"
    "- date_from / date_to: inclusive start and exclusive end ISO date (YYYY-MM-DD) "
    "bounding any date or period the user restricts to (e.g. 'in 2024', 'since March "
    "2023', 'on 5 Jan 2024'). For a single day set date_to to the next day; for "
    "'since'/'after' set only date_from; for 'before' only date_to; else both null.\n"
    "- language: a two-letter code ONLY if the user explicitly asks in/about a "
    "specific language; otherwise null."
)


class QueryAnalysis(BaseModel):
    intent: Intent = "qa"
    search_query: str = Field(description="Standalone, pronoun-resolved query.")
    answer_format: AnswerFormat = "default"
    source_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    language: str | None = None


@dataclass
class ProcessedQuery:
    original: str
    search_query: str
    intent: Intent = "qa"
    answer_format: AnswerFormat = "default"
    source_type: str | None = None
    language: str | None = None
    filters: list[Any] = field(default_factory=list)

    @property
    def needs_retrieval(self) -> bool:
        return self.intent != "chitchat"


def _format_history(history: Sequence[dict[str, str]] | None, max_turns: int = 6) -> str:
    if not history:
        return "(no prior conversation)"
    recent = list(history)[-max_turns:]
    return "\n".join(f"{t.get('role', 'user')}: {t.get('content', '')}" for t in recent)


def _parse_bound(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _facet_filters(analysis: QueryAnalysis) -> list[Any]:
    from qdrant_client.models import FieldCondition, MatchAny, MatchValue

    conditions: list[Any] = []
    if analysis.source_type == "pdf":
        # "PDFs" includes documents attached to web articles.
        conditions.append(
            FieldCondition(key="source_type", match=MatchAny(any=["pdf", "pdf_attachment"]))
        )
    elif analysis.source_type in ("website", "article"):
        # "website" is canonical; "article" accepted from the LLM and matched in
        # storage for points indexed before the rename.
        conditions.append(
            FieldCondition(key="source_type", match=MatchAny(any=["website", "article"]))
        )
    if analysis.language:
        conditions.append(
            FieldCondition(key="language", match=MatchValue(value=analysis.language))
        )
    lo, hi = _parse_bound(analysis.date_from), _parse_bound(analysis.date_to)
    if lo is not None or hi is not None:
        from qdrant_client.models import DatetimeRange

        conditions.append(
            FieldCondition(key="published_at", range=DatetimeRange(gte=lo, lt=hi))
        )
    return conditions


def process(question: str, history: Sequence[dict[str, str]] | None = None) -> ProcessedQuery:
    passthrough = ProcessedQuery(original=question, search_query=question, intent="qa")
    try:
        structured = get_structured_llm().with_structured_output(QueryAnalysis)
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
        answer_format=analysis.answer_format,
        source_type=analysis.source_type,
        language=analysis.language,
        filters=_facet_filters(analysis),
    )
