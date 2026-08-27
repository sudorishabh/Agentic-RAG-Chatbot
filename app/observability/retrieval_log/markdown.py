"""The same trace, written out for a person to read.

``trace.json`` is the record; ``report.md`` is the explanation that sits beside
it. Both are rendered from the *same dictionary*, so they can never disagree —
the markdown adds no data of its own, only ordering, prose and the standing
explanation of what each part of the pipeline is.

What the prose adds is the thing a JSON file cannot: **why a section exists.**
``website_pull`` means nothing until something says it is the website half of a
deliberately split pull; a filter line means nothing until something says every
search carries those mandatory conditions. Those explanations are constants here
(:data:`STAGE_NOTES`, :data:`RETRIEVER_NOTES`, :data:`INTENT_NOTES`), keyed by the
names the pipeline already uses, so a reader gets them without knowing the
codebase.

Rendering is *fail-open*, like the rest of this package: if a section cannot be
built the report says so and the rest is still written, because a partial
explanation beside a complete trace is worth more than neither.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

#: What each retriever is, in the words of what it holds rather than of its
#: technology.
RETRIEVER_NOTES: dict[str, str] = {
    "qdrant": "vector search over the document chunks — the passages themselves",
    "graph": "Neo4j relationships — who funded what, who led what, and when",
    "mysql": "the document catalog — titles, themes, authors, dates, and the "
             "vocabularies used to resolve a question",
}

#: What each leg of retrieval is for. These are the ``stage`` values the
#: instrumentation records; a name missing here still appears, just unexplained.
STAGE_NOTES: dict[str, str] = {
    "website_pull":
        "the website half of the deliberately split pull — website pages lead the "
        "answer with a concise summary (prefer_website_enabled)",
    "not_website_pull":
        "the other half: everything that is not a website page, which is where "
        "the PDF depth comes from",
    "dense_pull":
        "the plain dense pull, used when the website/PDF split is switched off "
        "or the caller pinned a source type",
    "keyword_leg":
        "a lexical pull over the salient query terms, fused with the dense "
        "results — it catches exact names and codes that vectors blur",
    "content_term_leg":
        "a second lexical pull over the query's plain content words, kept apart "
        "from the precise terms because OR-ing a ubiquitous term with a "
        "selective one keeps the ubiquitous match",
    "title_leg":
        "chunks of documents whose *title* matches the question — a canonical "
        "page whose body is mostly link labels cannot be found any other way",
    "multi_query_leg":
        "one LLM paraphrase of the question, searched separately to widen recall",
    "corrective_pull":
        "one reformulated retry, fired because the best result was below the "
        "confidence floor",
    "scoped_pull":
        "a search restricted to a document set the catalog already chose",
    "attachment_pull":
        "chunks of PDFs attached to an admitted website page, pulled for a "
        "detailed answer",
    "lead_child_scroll":
        "the opening chunk of each document in scope, for summarization",
    "parent_fetch":
        "the parent chunk behind each admitted child — the model is given the "
        "wider passage, not the narrow chunk that matched",
    "semantic_cache_lookup":
        "a nearest-neighbour lookup for a near-identical question already "
        "answered; a hit returns the stored answer and skips retrieval",
    "graph_routing":
        "the decision about whether this question can be answered from "
        "relationships at all",
    "graph_traversal":
        "the Cypher template that was run, and the rows it returned",
    "graph_chunk_hydration":
        "turning the graph's chunk ids into their source text, from Qdrant",
    "graph_document_hydration":
        "the same, for claims whose evidence is a whole document rather than a "
        "passage",
    "catalog":
        "a SQL statement against the document catalog",
}

#: What the route the question took means for the answer.
INTENT_NOTES: dict[str, str] = {
    "qa": "answer from document content",
    "comparison": "answer by comparing documents",
    "database": "answer from catalog facts (counts, listings, breakdowns)",
    "structured": "a catalog lookup — titles and facets rather than passages",
    "scoped_summary": "summarize a set of documents the catalog selects",
    "chitchat": "conversational, no retrieval",
    "out_of_scope": "outside the corpus",
}

#: The graph's outcomes, which are the whole story on a query it declined.
GRAPH_OUTCOME_NOTES: dict[str, str] = {
    "answered": "the graph answered, and its rows are in the context",
    "not_routed": "not a relationship-shaped question — nothing to ask the graph",
    "class_disabled": "routed, but that capability is switched off",
    "zero_result": "the graph ran and the corpus knows of no such relationship "
                   "(this is a real answer, not a failure)",
    "no_evidence": "rows came back but none could be rendered or hydrated",
    "failed": "the graph could not answer — an error, not an absence",
    "timed_out": "the graph exceeded its budget and was abandoned",
    "circuit_open": "skipped: the graph is failing, so it is not being waited on",
    "scope_unsupported": "the question was narrowed in a way no template can "
                         "honour, so answering would silently drop the constraint",
    "index_warming": "the entity index was still being built; declined on purpose",
    "disabled": "graph routing is switched off",
}


def _ms(value: Any) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{value / 1000:.2f} s" if value >= 1000 else f"{value:.0f} ms"


def _n(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "-"


def _cell(value: Any, limit: int = 300) -> str:
    """A value safe to put in a markdown table cell."""
    text = "" if value is None else str(value)
    text = text.replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render(trace: dict[str, Any]) -> str:
    """The whole report. Never raises: a section that fails is noted and skipped."""
    out: list[str] = []
    for section in (
        _heading,
        _understanding,
        _retrievers,
        _per_retriever_detail,
        _context,
        _outcome,
        _timings,
        _errors,
        _footer,
    ):
        try:
            out.extend(section(trace))
        except Exception:  # pragma: no cover - a report is best-effort
            logger.debug("Could not render a report section.", exc_info=True)
            out.append(f"\n> _(the `{section.__name__.strip('_')}` section of this "
                       f"report could not be rendered; the JSON holds the data)_\n")
    return "\n".join(out).rstrip() + "\n"


def _heading(trace: dict[str, Any]) -> list[str]:
    timings = trace.get("timings", {})
    outcome = trace.get("outcome", {})
    entry = trace.get("entrypoint", "")
    entry_note = {
        "chat.stream": "the streaming `/chat` endpoint — retrieval and generation",
        "search": "the `/search` endpoint — retrieval only, no answer generated",
    }.get(entry, entry)

    verdict = "-"
    if outcome:
        if outcome.get("cached"):
            verdict = "answered from the semantic cache"
        elif outcome.get("answered") is False:
            verdict = "**refused** — the answer was the “no information” fallback"
        elif outcome.get("answered"):
            verdict = (f"answered in {_n(outcome.get('answer_chars'))} characters, "
                       f"citing {_n(outcome.get('citations'))} source(s)")
    return [
        f"# {trace.get('question') or '(no question)'}",
        "",
        "|  |  |",
        "| --- | --- |",
        f"| Request id | `{trace.get('request_id', '')}` |",
        f"| When | {trace.get('timestamp', '')} |",
        f"| Entry point | `{entry}` — {entry_note} |",
        f"| Total time | {_ms(timings.get('total_latency_ms'))}, of which "
        f"{_ms(timings.get('retrieval_latency_ms'))} inside retrievers |",
        f"| Outcome | {verdict} |",
        "",
        "> This file explains the trace in `trace.json` beside it. Both are "
        "rendered from the same record, so they cannot disagree; the JSON is the "
        "one to parse, this one is the one to read.",
        "",
    ]


def _understanding(trace: dict[str, Any]) -> list[str]:
    query = trace.get("query", {})
    if not query:
        return []
    lines = [
        "## 1. What the question was taken to mean",
        "",
        "Before anything is retrieved, query understanding rewrites the question "
        "for search and picks the route. Everything below follows from this: a "
        "wrong intent sends the question to the wrong store, and a wrong filter "
        "narrows every pull.",
        "",
    ]
    search = query.get("search_query")
    if search and search != trace.get("question"):
        lines.append(f"- **Searched for**: `{_cell(search)}`  \n  "
                     f"  _(rewritten from the question above)_")
    elif search:
        lines.append(f"- **Searched for**: `{_cell(search)}` _(unchanged)_")
    intent = query.get("intent")
    if intent:
        note = INTENT_NOTES.get(intent, "")
        lines.append(f"- **Route**: `{intent}`" + (f" — {note}" if note else ""))
    for label, key in (
        ("Answer format", "answer_format"),
        ("Pinned source type", "source_type"),
        ("Language", "language"),
        ("Top-k requested", "top_k"),
    ):
        if query.get(key) not in (None, ""):
            lines.append(f"- **{label}**: `{query[key]}`")
    intents = query.get("intents") or []
    if intents:
        spelled = ", ".join(
            f"`{i.get('label')}` ({i.get('confidence')})" for i in intents
            if isinstance(i, dict)
        )
        lines.append(f"- **All detected intents**: {spelled}")
        rationale = next(
            (i.get("rationale") for i in intents
             if isinstance(i, dict) and i.get("rationale")), None
        )
        if rationale:
            lines.append(f"  - _why_: {_cell(rationale, 400)}")
    filters = query.get("filters")
    if filters:
        lines.append(f"- **Facet filters applied to every pull**: `{_cell(filters)}`")
    else:
        lines.append("- **Facet filters**: none — the pulls below were unfiltered "
                     "apart from the mandatory shape conditions")
    if query.get("is_ambiguous"):
        lines.append("- ⚠️ **Ambiguous**: the top intents were near-tied, so the "
                     "route was a close call")
    lines.append("")
    return lines


def _retrievers(trace: dict[str, Any]) -> list[str]:
    totals = (trace.get("retrievers") or {}).get("totals") or {}
    if not totals:
        return ["## 2. Which retrievers ran", "",
                "None — this query was answered without touching a store "
                "(chit-chat, or a cache hit).", ""]
    lines = [
        "## 2. Which retrievers ran",
        "",
        "| Retriever | Calls | Results | Time | Failures | What it holds |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name, bucket in sorted(
        totals.items(), key=lambda kv: -(kv[1].get("latency_ms") or 0)
    ):
        lines.append(
            f"| `{name}` | {_n(bucket.get('calls'))} | {_n(bucket.get('results'))} "
            f"| {_ms(bucket.get('latency_ms'))} | {_n(bucket.get('errors'))} "
            f"| {RETRIEVER_NOTES.get(name, '-')} |"
        )
    lines.append("")
    notes = trace.get("notes") or {}
    if notes.get("candidates") is not None:
        lines.append(
            f"After fusing the legs, **{_n(notes['candidates'])} candidate "
            f"chunks** went into reranking"
            + (f", of which **{_n(notes.get('rerank_survivors'))}** survived"
               if notes.get("rerank_survivors") is not None else "")
            + "."
        )
    legs = notes.get("legs")
    if isinstance(legs, dict):
        on = [k for k, v in legs.items() if v]
        lines.append(f"Legs enabled for this query: "
                     f"{', '.join(f'`{k}`' for k in on) or 'none'}.")
    if notes.get("facets_relaxed"):
        lines.append(
            "⚠️ **The facet filters matched nothing and were dropped for a retry** "
            f"(`{_n(notes.get('relaxed_candidates'))}` candidates on the second "
            "attempt). The answer is therefore broader than the question asked "
            "for — this is invisible in the answer itself."
        )
    if notes.get("graph_blocks"):
        lines.append(
            f"The graph contributed {_n(notes['graph_blocks'])} block(s), merged "
            f"with retrieval into {_n(notes.get('merged_blocks'))}."
        )
    lines.append("")
    return lines


def _per_retriever_detail(trace: dict[str, Any]) -> list[str]:
    events = trace.get("events") or []
    if not events:
        return []
    lines = [
        "## 3. Every call, in the order it was made",
        "",
        "One entry per call a retriever received. `results` is what came back, "
        "capped for the log — `result_count` is always the true total.",
        "",
    ]
    for index, event in enumerate(events, start=1):
        retriever = event.get("retriever", "?")
        stage = event.get("stage") or event.get("operation") or "-"
        lines.append(
            f"### {index}. `{retriever}` · {stage} — "
            f"{_n(event.get('result_count'))} result(s) in "
            f"{_ms(event.get('latency_ms'))}"
        )
        note = STAGE_NOTES.get(stage)
        if note:
            lines += ["", f"_{note}_"]
        lines.append("")
        lines += _request_lines(event.get("request") or {})
        error = event.get("error")
        if error:
            lines += [
                "",
                f"**This call failed** — `{error.get('type')}`: "
                f"{_cell(error.get('message'), 500)}. The pipeline is built to "
                f"degrade rather than fail, so the query continued without it.",
            ]
        lines += _result_lines(event)
        lines.append("")
    return lines


def _request_lines(request: dict[str, Any]) -> list[str]:
    if not request:
        return []
    lines = ["**Asked for:**", ""]
    for key, value in request.items():
        if value in (None, "", [], {}):
            continue  # an empty field says nothing; the JSON still has it
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value)
        if key == "sql":
            lines += ["", "```sql", str(value), "```"]
        elif key == "cypher":
            lines += ["", "```cypher", str(value), "```"]
        elif key == "filter":
            lines.append(f"- `filter`: `{_cell(value, 600)}`  \n  "
                         f"  _(every search carries the mandatory shape "
                         f"conditions: current, non-parent, searchable chunks)_")
        else:
            lines.append(f"- `{key}`: {_cell(value, 400)}")
    return lines


def _result_lines(event: dict[str, Any]) -> list[str]:
    results = event.get("results")
    count = event.get("result_count") or 0
    metrics = event.get("metrics") or {}
    lines: list[str] = []
    if metrics:
        lines += ["", "**Measured:** " + ", ".join(
            f"`{k}`={_cell(v, 200)}" for k, v in metrics.items()
        )]
    if metrics.get("rows_sampled") is False:
        lines += [
            "",
            f"**Returned:** {_n(count)} rows, not sampled — this is a bulk "
            f"vocabulary load (the whole gazetteer, read to resolve the "
            f"question), so its size and timing are the useful record, not its "
            f"contents.",
        ]
        return lines
    if not results:
        if count:
            lines += ["", f"**Returned:** {_n(count)} result(s), not captured."]
        else:
            lines += ["", "**Returned nothing.**"]
        return lines
    kept = len(results)
    header = f"**Returned** {_n(count)} result(s)"
    if event.get("results_truncated"):
        header += f", of which the first {kept} were kept for the log"
    lines += ["", header + ":", ""]
    if all(isinstance(r, str) for r in results):
        # The compact rendering: one line per item, already ordered by rank.
        lines.append("```text")
        lines += [str(r) for r in results]
        lines.append("```")
    else:
        lines += _result_table(results)
    return lines


def _result_table(results: list[Any]) -> list[str]:
    """The full (structured) rendering as a table."""
    lines = [
        "| # | Score | Source | Passage |",
        "| --- | --- | --- | --- |",
    ]
    for item in results:
        if not isinstance(item, dict):
            lines.append(f"|  |  |  | {_cell(item)} |")
            continue
        metadata = item.get("metadata") or {}
        where = " · ".join(
            str(metadata[k]) for k in ("title", "source_type", "page_number")
            if metadata.get(k) is not None
        )
        score = item.get("score")
        lines.append(
            f"| {item.get('rank', '')} | {'' if score is None else score} "
            f"| {_cell(where, 120)} | {_cell(item.get('text'), 200)} |"
        )
    return lines


def _context(trace: dict[str, Any]) -> list[str]:
    context = trace.get("context") or {}
    if not context:
        return ["## 4. What the LLM was given", "",
                "Nothing — no context was built for this query.", ""]
    lines = [
        "## 4. What the LLM was given",
        "",
        "These are the blocks the answer was generated from, **in the order the "
        "model sees them**. The `[n]` here is the `[n]` in the answer's citation "
        "markers. Everything in section 3 that is not listed here was retrieved "
        "and then discarded by fusion, reranking or the context budget.",
        "",
        f"- **Blocks**: {_n(context.get('block_count'))}",
        f"- **Characters of passage text**: {_n(context.get('total_chars'))}",
    ]
    if context.get("prompt_chars"):
        lines.append(
            f"- **Characters actually sent**: {_n(context['prompt_chars'])} "
            f"— the blocks plus the per-block headers and source hints that "
            f"generation adds around them"
        )
    if context.get("blocks_truncated"):
        lines.append("- _(only the first blocks are listed below; the count above "
                     "is the true one)_")
    lines.append("")
    for block in context.get("blocks") or []:
        where = block.get("source") or _cell(block.get("metadata"), 200)
        head = f"#### [{block.get('n')}] {_cell(where, 200)}"
        lines += [head, ""]
        facts = [f"{_n(block.get('text_chars'))} chars"]
        if block.get("score") is not None:
            facts.append(f"rank score {block['score']}")
        if block.get("conflict"):
            facts.append("**conflicts with another block**")
        lines += [f"_{' · '.join(facts)}_", ""]
        text = block.get("text")
        if text:
            for paragraph in str(text).split("\n"):
                lines.append(f"> {paragraph}" if paragraph.strip() else ">")
        else:
            lines.append("> _(text not captured — RETRIEVAL_LOG_INCLUDE_TEXT is off)_")
        lines.append("")
    return lines


def _outcome(trace: dict[str, Any]) -> list[str]:
    outcome = trace.get("outcome") or {}
    if not outcome:
        return []
    lines = ["## 5. How it ended", ""]
    if outcome.get("answered") is False:
        lines += [
            "**The answer was the refusal** — “I don't have information on that "
            "in the available sources.”",
            "",
        ]
        if (trace.get("context") or {}).get("block_count"):
            lines += [
                "Note that context *was* built for this query (section 4). "
                "Retrieval found passages and generation declined to use them, "
                "which is a generation problem rather than a retrieval one.",
                "",
            ]
    lines += ["| | |", "| --- | --- |"]
    for key, value in outcome.items():
        lines.append(f"| {key} | {_cell(value, 200)} |")
    lines.append("")
    return lines


def _timings(trace: dict[str, Any]) -> list[str]:
    stages = (trace.get("timings") or {}).get("stages_ms") or {}
    if not stages:
        return []
    lines = [
        "## 6. Where the time went",
        "",
        "Per pipeline stage, in milliseconds. Parent stages contain their "
        "children, so these overlap by design.",
        "",
        "| Stage | Time |",
        "| --- | --- |",
    ]
    for name, value in sorted(stages.items(), key=lambda kv: -(kv[1] or 0)):
        lines.append(f"| `{name}` | {_ms(value)} |")
    lines.append("")
    return lines


def _errors(trace: dict[str, Any]) -> list[str]:
    errors = trace.get("errors") or []
    failed_events = [e for e in (trace.get("events") or []) if e.get("error")]
    if not errors and not failed_events:
        return ["## 7. Failures", "", "None.", ""]
    lines = ["## 7. Failures", ""]
    for event in failed_events:
        error = event.get("error") or {}
        lines.append(
            f"- `{event.get('retriever')}` / {event.get('stage')}: "
            f"**{error.get('type')}** — {_cell(error.get('message'), 500)}"
        )
    for entry in errors:
        lines.append(
            f"- `{entry.get('where')}` at {entry.get('at')}: "
            f"**{entry.get('type')}** — {_cell(entry.get('message'), 500)}"
        )
    lines.append("")
    return lines


def _footer(trace: dict[str, Any]) -> list[str]:
    return [
        "---",
        "",
        f"_Retrieval trace, schema version {trace.get('schema_version')}. "
        f"Generated because `is_retrieval_log=true`; see "
        f"docs/retrieval-logging.md. Logging never alters retrieval or the "
        f"answer._",
    ]
