from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.clients.llm import get_llm, get_structured_llm
from app.core.dates import IsoDate, current_date_directive, exclusive_end
from app.retrieval.catalog_prompt import (
    catalog_coverage_directive,
    catalog_inventory_directive,
)
from app.retrieval.understanding.filters import (
    _facet_filters,
    _parse_bound,
    _theme_condition,
)
from app.retrieval.understanding.prompts import UNDERSTANDING_SYSTEM as _UNDERSTANDING_SYSTEM

logger = logging.getLogger(__name__)

Intent = Literal["qa", "structured", "scoped_summary", "chitchat"]
# How the user wants the answer shaped. Detected from the turn; used downstream
# to steer generation (and table-aware retrieval). 'default' = let the model
# choose the natural shape.
AnswerFormat = Literal["default", "list", "table", "summary", "detailed", "timeline"]
Operation = Literal["count", "list", "lookup", "distribution", "list_themes"]
GroupBy = Literal["theme", "content_type", "author", "year"]


class QueryAnalysis(BaseModel):
    intent: Intent = "qa"
    search_query: str = Field(description="Standalone, pronoun-resolved query.")
    answer_format: AnswerFormat = "default"
    # shared facet scope (used by both the structured and qa paths)
    source_type: str | None = None
    theme: str | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    date_from: IsoDate = None
    date_to: IsoDate = None
    language: str | None = None
    # structured-only slots (null/defaults on the qa path)
    operation: Operation | None = None
    bundle: str | None = None
    group_by: GroupBy | None = None
    # list_themes: the user asked for sub-themes/children rather than the
    # top-level themes.
    theme_children: bool = False
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
    # IsoDate, not str: the model routinely trails JSON punctuation into these
    # values ("2022-01-01},"), which reaches SQL as a dropped bound and the
    # answer text as a visible artefact. See app.core.dates.
    date_from: IsoDate = None
    # The LLM is asked for the last date to INCLUDE, never the exclusive bound —
    # copying a date is reliable, incrementing one is not. `date_to` below derives
    # the half-open bound the query layers actually take.
    date_to_inclusive: IsoDate = None
    language: str | None = None

    @property
    def date_to(self) -> str | None:
        """Exclusive upper bound — a property, so it stays out of the schema the
        LLM fills and cannot drift from `date_to_inclusive`."""
        return exclusive_end(self.date_to_inclusive)


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
    theme_children: bool = Field(
        default=False,
        description="For list_themes: true when the user asked for sub-themes / "
        "children rather than the top-level themes.",
    )
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
    # Full multi-label understanding (v2) for exposure/debugging; None on the
    # passthrough fallback. Downstream still routes on `intent`/`analysis`.
    understanding: QueryUnderstanding | None = None

    @property
    def is_ambiguous(self) -> bool:
        """Near-tie between the top content intents — a debug/clarification
        signal. False on the passthrough fallback (no understanding)."""
        return _is_ambiguous(self.understanding.intents) if self.understanding else False


def _format_history(history: Sequence[dict[str, str]] | None, max_turns: int = 12) -> str:
    if not history:
        return "(no prior conversation)"
    recent = list(history)[-max_turns:]
    return "\n".join(f"{t.get('role', 'user')}: {t.get('content', '')}" for t in recent)


def _vote(values: Sequence[Any]) -> Any:
    """Majority value across samples; ties take the first non-null value in vote
    order. Used to merge the scalar attributes of understanding samples."""
    keyed = [tuple(v) if isinstance(v, list) else v for v in values]
    counts = Counter(keyed)
    top = max(counts.values())
    leaders = {k for k, n in counts.items() if n == top}
    if len(leaders) == 1:
        winner = next(iter(leaders))
    else:
        winner = next((k for k in keyed if k in leaders and k is not None), None)
    return list(winner) if isinstance(winner, tuple) else winner


# ── Multi-label merge + hybrid confidence (v2) ───────────────────────────────
# Terminal intents are exclusive: the highest-priority one present wins alone.
# Content intents are co-equal, ranked by confidence. `structured_output` is a
# modifier that only rides alongside a content intent. See
# docs/intent-classification-design.md (sections 6-8).
_TERMINAL_PRIORITY: tuple[IntentLabel, ...] = (
    "safety_policy", "out_of_scope", "clarification_needed", "chitchat",
)
_CONTENT_INTENTS: frozenset[str] = frozenset(
    {"qa", "database", "summarization", "comparison"}
)


def _label_confidences(
    samples: Sequence[QueryUnderstanding],
) -> dict[str, tuple[float, str]]:
    """Per-label confidence + a representative rationale (the hybrid scheme):
    with several samples, confidence is the agreement fraction (vote share);
    with a single sample it is the model's own reported confidence."""
    n = len(samples)
    grouped: dict[str, list[float]] = {}
    rationale: dict[str, str] = {}
    for sample in samples:
        for pred in sample.intents:
            grouped.setdefault(pred.label, []).append(pred.confidence)
            rationale.setdefault(pred.label, pred.rationale)
    out: dict[str, tuple[float, str]] = {}
    for label, confs in grouped.items():
        conf = confs[0] if n <= 1 else len(confs) / n
        out[label] = (round(float(conf), 3), rationale.get(label, ""))
    return out


def _resolve_intents(
    confidences: dict[str, tuple[float, str]], *, threshold: float
) -> list[IntentPrediction]:
    """Apply the taxonomy rules to per-label confidences: terminal exclusivity +
    priority, the threshold gate, a guaranteed content intent, and the
    structured_output-never-alone modifier rule."""
    kept = {label: cr for label, cr in confidences.items() if cr[0] >= threshold}

    # Terminal intents are exclusive — the highest-priority one present wins.
    for term in _TERMINAL_PRIORITY:
        if term in kept:
            conf, why = kept[term]
            return [IntentPrediction(label=term, confidence=conf, rationale=why)]

    # Content path: guarantee at least one content intent survives.
    content = {lbl: cr for lbl, cr in kept.items() if lbl in _CONTENT_INTENTS}
    if not content:
        pool = {lbl: cr for lbl, cr in confidences.items() if lbl in _CONTENT_INTENTS}
        if pool:
            top = max(pool, key=lambda lbl: pool[lbl][0])
            content = {top: pool[top]}
        else:
            content = {"qa": (0.5, "fallback: no content intent detected")}

    ordered = sorted(content, key=lambda lbl: content[lbl][0], reverse=True)
    result = [
        IntentPrediction(label=lbl, confidence=content[lbl][0], rationale=content[lbl][1])
        for lbl in ordered
    ]
    # structured_output rides along only when a content intent is present.
    if "structured_output" in kept:
        conf, why = kept["structured_output"]
        result.append(
            IntentPrediction(label="structured_output", confidence=conf, rationale=why)
        )
    return result


def _primary_intent(intents: Sequence[IntentPrediction]) -> IntentLabel:
    """Single-label view for back-compat: highest-priority terminal, else the
    highest-confidence content intent, else qa."""
    labels = {p.label for p in intents}
    for term in _TERMINAL_PRIORITY:
        if term in labels:
            return term
    content = [p for p in intents if p.label in _CONTENT_INTENTS]
    if content:
        return max(content, key=lambda p: p.confidence).label
    return "qa"


def _is_ambiguous(intents: Sequence[IntentPrediction], *, margin: float = 0.2) -> bool:
    """True when the top two content intents are within `margin` of each other —
    a genuine multi-way call worth surfacing (and a clarification signal)."""
    content = sorted(
        (p for p in intents if p.label in _CONTENT_INTENTS),
        key=lambda p: p.confidence, reverse=True,
    )
    if len(content) < 2:
        return False
    return (content[0].confidence - content[1].confidence) < margin


def _merge_understanding(
    samples: Sequence[QueryUnderstanding], *, threshold: float
) -> QueryUnderstanding:
    """Merge N understanding samples into one: agreement-voted intents (see
    _label_confidences / _resolve_intents), majority-voted attributes, and a
    query_rewrite drawn from a sample that matches the merged primary intent.
    Assumes at least one sample."""
    confidences = _label_confidences(samples)
    intents = _resolve_intents(confidences, threshold=threshold)

    def vote(getter: Any) -> Any:
        return _vote([getter(s) for s in samples])

    scope = QueryScope(
        source_type=vote(lambda s: s.scope.source_type),
        target=vote(lambda s: s.scope.target) or "whole_corpus",
        theme=vote(lambda s: s.scope.theme),
        author=vote(lambda s: s.scope.author),
        tags=vote(lambda s: s.scope.tags) or [],
        date_from=vote(lambda s: s.scope.date_from),
        date_to_inclusive=vote(lambda s: s.scope.date_to_inclusive),
        language=vote(lambda s: s.scope.language),
    )
    primary = _primary_intent(intents)
    rewrite = next(
        (s.query_rewrite for s in samples
         if s.query_rewrite.strip() and any(p.label == primary for p in s.intents)),
        samples[0].query_rewrite,
    )
    return QueryUnderstanding(
        query_rewrite=rewrite,
        intents=intents,
        output_format=vote(lambda s: s.output_format) or "prose",
        scope=scope,
        operation=vote(lambda s: s.operation),
        group_by=vote(lambda s: s.group_by),
        bundle=vote(lambda s: s.bundle),
        title_contains=vote(lambda s: s.title_contains),
        # Any slot added to QueryUnderstanding must be voted here too: this
        # rebuilds the object field by field, so an omission silently resets the
        # slot to its default instead of failing.
        theme_children=bool(vote(lambda s: s.theme_children)),
        limit=vote(lambda s: s.limit) or 10,
    )


def _understanding_messages(
    question: str, history: Sequence[dict[str, str]] | None
) -> list[tuple[str, str]]:
    return [
        (
            "system",
            _UNDERSTANDING_SYSTEM
            + catalog_inventory_directive()
            + catalog_coverage_directive()
            + current_date_directive(),
        ),
        (
            "human",
            f"Conversation so far:\n{_format_history(history)}\n\n"
            f"Latest user turn:\n{question}",
        ),
    ]


def _voted_understanding(
    question: str, history: Sequence[dict[str, str]] | None, votes: int
) -> list[QueryUnderstanding]:
    """N concurrent understanding samples at exploratory temperature. Errored
    samples are dropped; the caller merges the survivors."""
    from concurrent.futures import ThreadPoolExecutor

    messages = _understanding_messages(question, history)

    def sample(_: int) -> QueryUnderstanding | None:
        try:
            model = get_llm(temperature=0.7).with_structured_output(QueryUnderstanding)
            return model.invoke(messages)
        except Exception:
            logger.warning("Understanding vote failed; dropping it.", exc_info=True)
            return None

    with ThreadPoolExecutor(max_workers=votes) as pool:
        return [r for r in pool.map(sample, range(votes)) if r is not None]


# v2 output_format -> legacy AnswerFormat. csv/json/markdown/diagram have no
# legacy equivalent yet, so they degrade to 'default' (the structured_output
# intent still records the exact shape on `understanding` for later use).
_FORMAT_TO_LEGACY: dict[str, AnswerFormat] = {
    "prose": "default", "list": "list", "table": "table", "timeline": "timeline",
    "csv": "default", "json": "default", "markdown": "default", "diagram": "default",
}


def _legacy_intent_and_format(u: QueryUnderstanding) -> tuple[Intent, AnswerFormat]:
    """Collapse the multi-label understanding onto the single-label route the
    current pipeline consumes.

    `out_of_scope` is deliberately routed to `qa`, not chitchat: the classifier
    is a single stochastic sample that frequently mislabels an in-corpus question
    (a pasted document title, a domain topic) as out-of-scope, and a blind
    deflection then hides content the store actually contains. Routing it through
    retrieval lets the corpus be the arbiter — a genuinely off-topic query
    retrieves nothing usable and the grounding prompt returns the standard
    refusal, while a misjudged one gets answered. `chitchat` /
    `clarification_needed` / `safety_policy` stay on the non-retrieving path."""
    primary = _primary_intent(u.intents)
    fmt: AnswerFormat = _FORMAT_TO_LEGACY.get(u.output_format, "default")
    if primary in ("chitchat", "clarification_needed", "safety_policy"):
        return "chitchat", fmt
    if primary == "database":
        return "structured", fmt
    if primary == "summarization":
        # One named document keeps the old qa+summary behavior; a set or the whole
        # corpus uses the scoped-summary path.
        if u.scope.target == "single_document" or u.title_contains:
            return "qa", (fmt if fmt != "default" else "summary")
        return "scoped_summary", fmt
    return "qa", fmt  # qa, comparison, or a lone modifier


def _to_legacy_analysis(question: str, u: QueryUnderstanding) -> QueryAnalysis:
    """Derive the downstream QueryAnalysis contract from the v2 understanding."""
    intent, answer_format = _legacy_intent_and_format(u)
    source_type = (
        u.scope.source_type if u.scope.source_type in ("pdf", "website") else None
    )
    return QueryAnalysis(
        intent=intent,
        search_query=(u.query_rewrite or question).strip() or question,
        answer_format=answer_format,
        source_type=source_type,
        theme=u.scope.theme,
        author=u.scope.author,
        tags=list(u.scope.tags or []),
        date_from=u.scope.date_from,
        date_to=u.scope.date_to,
        language=u.scope.language,
        operation=u.operation,
        bundle=u.bundle,
        group_by=u.group_by,
        theme_children=u.theme_children,
        title_contains=u.title_contains,
        limit=u.limit,
    )


def process(question: str, history: Sequence[dict[str, str]] | None = None) -> ProcessedQuery:
    passthrough = ProcessedQuery(original=question, search_query=question, intent="qa")
    settings = get_settings()
    votes = max(1, int(settings.analysis_votes))
    threshold = float(getattr(settings, "intent_confidence_threshold", 0.5))
    try:
        if votes > 1:
            samples = _voted_understanding(question, history, votes)
        else:
            model = get_structured_llm().with_structured_output(QueryUnderstanding)
            samples = [model.invoke(_understanding_messages(question, history))]
    except Exception:
        logger.warning("Query analysis failed; using passthrough.", exc_info=True)
        return passthrough

    samples = [s for s in samples if s is not None]
    if not samples:
        logger.warning("All analysis votes failed; using passthrough.")
        return passthrough

    understanding = _merge_understanding(samples, threshold=threshold)
    analysis = _to_legacy_analysis(question, understanding)
    logger.info(
        "intent: %s -> route=%s%s",
        [f"{p.label}:{p.confidence}" for p in understanding.intents],
        analysis.intent,
        " (ambiguous)" if _is_ambiguous(understanding.intents) else "",
    )
    return ProcessedQuery(
        original=question,
        search_query=analysis.search_query,
        intent=analysis.intent,
        answer_format=analysis.answer_format,
        source_type=analysis.source_type,
        language=analysis.language,
        filters=_facet_filters(analysis),
        analysis=analysis,
        understanding=understanding,
    )
