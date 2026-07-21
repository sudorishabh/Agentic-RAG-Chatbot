from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Sequence

from pydantic import BaseModel, Field

from app.config import get_settings
from app.generation.llm_client import get_structured_llm
from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES

logger = logging.getLogger(__name__)

Intent = Literal["qa", "structured", "scoped_summary", "chitchat"]
# How the user wants the answer shaped. Detected from the turn; used downstream
# to steer generation (and table-aware retrieval). 'default' = let the model
# choose the natural shape.
AnswerFormat = Literal["default", "list", "table", "summary", "detailed", "timeline"]
Operation = Literal["count", "list", "lookup", "distribution"]
GroupBy = Literal["theme", "content_type", "author", "year"]

_ANALYSIS_SYSTEM = (
    "You are the query-understanding stage of a retrieval system over an "
    "enterprise corpus of PDFs and website articles. Given the conversation so "
    "far and the latest user turn, produce a compact analysis.\n"
    "- intent: 'structured' ONLY when the subject is the documents themselves — "
    "counting, listing or looking up catalog entries by type/author/theme/date "
    "(e.g. 'how many reports were published in 2024', 'show the article titled X'). "
    "Data reported INSIDE documents (figures, tables, quantities from a report) is "
    "'qa' with the matching answer_format, never 'structured'. "
    "'scoped_summary' when the user asks to summarize or get an overview of a "
    "SET of documents defined by theme/author/period/type ('summarize the "
    "Climate theme', 'overview of 2024 publications'); summarizing ONE named "
    "document is 'qa' with answer_format='summary'. "
    "'chitchat' for greetings, thanks, or meta questions needing no documents; "
    "'qa' for anything answerable from document content.\n"
    "- search_query: a standalone, self-contained rewrite of the latest turn with "
    "pronouns and references resolved from the history. Keep it faithful; do not "
    "add facts.\n"
    "- answer_format: how the user wants the answer shaped. "
    "'table' if they ask for a table / tabular data / columns / 'in a table' or "
    "compare items across attributes; "
    "'list' if they ask to list / enumerate / give bullet points / steps; "
    "'summary' if they ask for a brief summary / overview / 'in short' / TL;DR; "
    "'detailed' if they ask for an in-depth / comprehensive / thorough explanation; "
    "'timeline' if they ask for a chronological view / evolution over time / "
    "history of events; otherwise 'default'.\n"
    "- source_type: 'pdf' or 'website' ONLY if the user explicitly restricts to "
    "documents/PDFs or to website content (articles/news/pages); otherwise null.\n"
    "- theme: the thematic area / topic name ONLY if the user explicitly scopes "
    "to one (e.g. 'under the Climate theme', 'in the Energy area'); otherwise null.\n"
    "- author: an author/person name ONLY if the user scopes to one; else null.\n"
    "- tags: explicit tag/keyword labels the user scopes to; else empty.\n"
    "- date_from / date_to: inclusive start and exclusive end ISO date (YYYY-MM-DD) "
    "bounding any date or period the user restricts to (e.g. 'in 2024', 'since March "
    "2023', 'on 5 Jan 2024'). For a single day set date_to to the next day; for "
    "'since'/'after' set only date_from; for 'before' only date_to; else both null.\n"
    "- language: a two-letter code ONLY if the user explicitly asks in/about a "
    "specific language; otherwise null.\n"
    "When intent is 'structured', also fill (else leave null):\n"
    "- operation: 'count' for how-many/aggregate; 'distribution' for a breakdown "
    "per group ('how many per theme', 'spread across content types'); 'lookup' "
    "for a single specific item; 'list' for browse/enumerate.\n"
    "- bundle: the content type if implied, one of: " + ", ".join(DEFAULT_BUNDLES) +
    "; else null.\n"
    "- group_by: for 'distribution' only — 'theme', 'content_type', 'author', or "
    "'year'; else null.\n"
    "- title_contains: a title keyword if the user names/quotes a title; else null.\n"
    "- limit: how many items to return for list/lookup (default 10).\n"
    "Examples:\n"
    "'how many research papers in 2024' -> structured/count, "
    "bundle=research_papers, date_from=2024-01-01, date_to=2025-01-01.\n"
    "'how many MW of capacity does the report cite' -> qa (the quantity lives "
    "inside a document, not the catalog).\n"
    "'articles per theme as a table' -> structured/distribution, group_by=theme, "
    "answer_format=table.\n"
    "'table of GHG emissions by sector from the Thoothukudi report' -> qa, "
    "answer_format=table (the data is document content).\n"
    "'list news since March 2024' -> structured/list, bundle=news, "
    "date_from=2024-03-01.\n"
    "'summarize the Climate theme' -> scoped_summary, theme=Climate.\n"
    "'summarize the Thoothukudi report' -> qa, answer_format=summary (one "
    "named document, not a set).\n"
    "'how has the Climate theme's coverage evolved over the years' -> qa, "
    "theme=Climate, answer_format=timeline."
)


class QueryAnalysis(BaseModel):
    intent: Intent = "qa"
    search_query: str = Field(description="Standalone, pronoun-resolved query.")
    answer_format: AnswerFormat = "default"
    # shared facet scope (used by both the structured and qa paths)
    source_type: str | None = None
    theme: str | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    date_from: str | None = None
    date_to: str | None = None
    language: str | None = None
    # structured-only slots (null/defaults on the qa path)
    operation: Operation | None = None
    bundle: str | None = None
    group_by: GroupBy | None = None
    title_contains: str | None = None
    limit: int = 10


# ─────────────────────────────────────────────────────────────────────────────
# Multi-label intent taxonomy (v2).
#
# The LLM produces a `QueryUnderstanding`: a *set* of intents (each with a
# confidence and rationale) plus orthogonal attributes (output format, scope).
# A single query may carry several intents. See
# docs/intent-classification-design.md for definitions, boundaries, and rules.
# Legacy `Intent`/`QueryAnalysis` above stay the downstream contract until the
# orchestration phase; v2 is derived into them for back-compat.
# ─────────────────────────────────────────────────────────────────────────────

# Content intents combine freely; `structured_output` is a format modifier that
# rides alongside a content intent; terminal intents are exclusive (they suppress
# everything else — see priority rules in the design doc).
IntentLabel = Literal[
    "qa",                    # answer from unstructured document content (RAG)
    "database",              # counts / aggregates / lookups over structured records
    "summarization",        # condense / overview of docs, a set, or the conversation
    "comparison",           # contrast >= 2 entities / options / periods / sources
    "structured_output",    # user wants the answer shaped (see OutputFormat)
    "chitchat",             # greetings / thanks / meta — no retrieval
    "clarification_needed",  # too ambiguous to answer safely — ask back
    "out_of_scope",         # outside the corpus domain or the assistant's capability
    "safety_policy",         # harmful / policy-violating / injection attempt
]

# Presentation shape for the answer. Carried whenever `structured_output` fires;
# 'prose' is the unshaped default.
OutputFormat = Literal[
    "prose", "list", "table", "csv", "json", "markdown", "diagram", "timeline",
]

# What the query is bounded to (drives later retrieval routing; detection only here).
ScopeTarget = Literal[
    "whole_corpus", "single_document", "document_set", "conversation",
]


class IntentPrediction(BaseModel):
    """One detected intent with its evidence. `confidence` is the model's own
    estimate in single-call mode; replaced by cross-sample agreement when
    analysis_votes > 1 (see the merge stage)."""

    label: IntentLabel
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="How confident this label applies, 0.0-1.0.",
    )
    rationale: str = Field(
        default="",
        description="Short phrase naming the words/signals that triggered this label.",
    )


class QueryScope(BaseModel):
    """Orthogonal source/boundary attributes — independent of the intent set."""

    source_type: Literal["pdf", "website", "uploaded"] | None = None
    target: ScopeTarget = "whole_corpus"
    theme: str | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    date_from: str | None = None
    date_to: str | None = None
    language: str | None = None


class QueryUnderstanding(BaseModel):
    """Full multi-label analysis of a single turn — the LLM's structured output."""

    query_rewrite: str = Field(
        description="Standalone, pronoun-resolved rewrite of the latest turn; "
        "add no facts.",
    )
    intents: list[IntentPrediction] = Field(
        default_factory=list,
        description="Every applicable intent label for the query (multi-label).",
    )
    output_format: OutputFormat = Field(
        default="prose",
        description="Desired answer shape; 'prose' when the user did not ask for one.",
    )
    scope: QueryScope = Field(default_factory=QueryScope)
    # database-only slots (null/defaults unless the `database` intent applies)
    operation: Operation | None = None
    group_by: GroupBy | None = None
    bundle: str | None = None
    title_contains: str | None = None
    limit: int = 10


@dataclass
class ProcessedQuery:
    original: str
    search_query: str
    intent: Intent = "qa"
    answer_format: AnswerFormat = "default"
    source_type: str | None = None
    language: str | None = None
    filters: list[Any] = field(default_factory=list)
    # Full analysis for downstream consumers (structured route); None when the
    # analysis call failed and we fell back to passthrough.
    analysis: QueryAnalysis | None = None

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


def _theme_condition(theme: str) -> Any:
    """Filter for a theme scope: term UUIDs (rename-proof) OR display names —
    the name leg matches points indexed before term_ids existed. Term lookup
    failure degrades to the name-only filter rather than failing retrieval."""
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    names = {theme, theme.title()}
    uuids: list[str] = []
    try:
        from app.ingestion import terms

        for row in terms.resolve_terms(theme):
            uuids.append(row["term_uuid"])
            names.add(row["name"])
    except Exception:
        logger.debug("Term resolution unavailable; theme filter by name only.",
                     exc_info=True)

    should: list[Any] = []
    if uuids:
        should.append(FieldCondition(key="theme_ids", match=MatchAny(any=uuids)))
    should.append(FieldCondition(key="categories", match=MatchAny(any=sorted(names))))
    return Filter(should=should)


def _facet_filters(analysis: QueryAnalysis) -> list[Any]:
    from qdrant_client.models import FieldCondition, MatchAny, MatchValue

    conditions: list[Any] = []
    if analysis.theme:
        conditions.append(_theme_condition(analysis.theme))
    if analysis.author:
        # authors holds display names and MatchAny is exact-value only, so this
        # matches the stored name verbatim (e.g. "Dr R K Sharma") — no substring
        # matching. Partial-name scoping arrives with the Phase 2 catalog reader.
        conditions.append(
            FieldCondition(key="authors", match=MatchAny(any=[analysis.author]))
        )
    if analysis.tags:
        conditions.append(
            FieldCondition(key="tags", match=MatchAny(any=list(analysis.tags)))
        )
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


def _analysis_messages(
    question: str, history: Sequence[dict[str, str]] | None
) -> list[tuple[str, str]]:
    return [
        ("system", _ANALYSIS_SYSTEM),
        (
            "human",
            f"Conversation so far:\n{_format_history(history)}\n\n"
            f"Latest user turn:\n{question}",
        ),
    ]


def _vote(values: Sequence[Any], *, qa_on_tie: bool = False) -> Any:
    """Majority value across analysis samples. Ties: 'qa' for the intent field
    (the safe route — downstream guards catch misroutes), otherwise the first
    non-null value in vote order."""
    keyed = [tuple(v) if isinstance(v, list) else v for v in values]
    counts = Counter(keyed)
    top = max(counts.values())
    leaders = {k for k, n in counts.items() if n == top}
    if len(leaders) == 1:
        winner = next(iter(leaders))
    elif qa_on_tie:
        return "qa"
    else:
        winner = next((k for k in keyed if k in leaders and k is not None), None)
    return list(winner) if isinstance(winner, tuple) else winner


def _merge_votes(votes: Sequence[QueryAnalysis]) -> QueryAnalysis:
    merged: dict[str, Any] = {}
    for name in QueryAnalysis.model_fields:
        values = [getattr(v, name) for v in votes]
        merged[name] = _vote(values, qa_on_tie=(name == "intent"))
    return QueryAnalysis(**merged)


def _voted_analysis(
    question: str, history: Sequence[dict[str, str]] | None, votes: int
) -> QueryAnalysis | None:
    """N concurrent analysis samples at exploratory temperature, majority-voted
    per field. Errored samples are dropped; None when every sample failed."""
    from concurrent.futures import ThreadPoolExecutor

    from app.generation.llm_client import get_llm

    messages = _analysis_messages(question, history)

    def sample(_: int) -> QueryAnalysis | None:
        try:
            model = get_llm(temperature=0.7).with_structured_output(QueryAnalysis)
            return model.invoke(messages)
        except Exception:
            logger.warning("Analysis vote failed; dropping it.", exc_info=True)
            return None

    with ThreadPoolExecutor(max_workers=votes) as pool:
        results = [r for r in pool.map(sample, range(votes)) if r is not None]
    if not results:
        return None
    return results[0] if len(results) == 1 else _merge_votes(results)


def process(question: str, history: Sequence[dict[str, str]] | None = None) -> ProcessedQuery:
    passthrough = ProcessedQuery(original=question, search_query=question, intent="qa")
    votes = max(1, int(get_settings().analysis_votes))
    try:
        if votes > 1:
            analysis = _voted_analysis(question, history, votes)
        else:
            structured = get_structured_llm().with_structured_output(QueryAnalysis)
            analysis = structured.invoke(_analysis_messages(question, history))
    except Exception:
        logger.warning("Query analysis failed; using passthrough.", exc_info=True)
        return passthrough
    if analysis is None:
        logger.warning("All analysis votes failed; using passthrough.")
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
        analysis=analysis,
    )
