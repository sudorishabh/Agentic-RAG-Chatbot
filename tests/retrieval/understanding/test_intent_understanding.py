"""Unit tests for the multi-label intent understanding layer.

Covers per-label confidence (agreement vs self-reported), intent resolution
(threshold gate, terminal exclusivity + priority, structured_output-never-alone,
content fallback), primary/ambiguity signals, sample merging, and the legacy
QueryAnalysis derivation the current pipeline consumes. No LLM / network.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.retrieval.understanding import query_processor as qp

IP = qp.IntentPrediction
QU = qp.QueryUnderstanding
QS = qp.QueryScope


def _u(labels, **kw):
    """QueryUnderstanding from (label, confidence[, rationale]) tuples + attrs."""
    kw.setdefault("query_rewrite", "q")
    preds = [
        IP(label=t[0], confidence=t[1], rationale=(t[2] if len(t) > 2 else ""))
        for t in labels
    ]
    return QU(intents=preds, **kw)


def _conf(**labels):
    """Confidence map {label: (confidence, rationale)} for _resolve_intents."""
    return {label: (c, "") for label, c in labels.items()}


# --------------------------------------------------------------------------- #
# _label_confidences — hybrid confidence.
# --------------------------------------------------------------------------- #

def test_label_confidence_is_agreement_fraction_when_voting():
    samples = [
        _u([("database", 0.9, "count"), ("qa", 0.5, "content")]),
        _u([("database", 0.8, "c")]),
    ]
    conf = qp._label_confidences(samples)
    assert conf["database"][0] == 1.0   # 2 of 2 samples
    assert conf["qa"][0] == 0.5         # 1 of 2 samples
    assert conf["database"][1] == "count"  # first-seen rationale


def test_label_confidence_is_self_reported_for_single_sample():
    conf = qp._label_confidences([_u([("summarization", 0.77)])])
    assert conf["summarization"][0] == 0.77


# --------------------------------------------------------------------------- #
# _resolve_intents — the taxonomy rules.
# --------------------------------------------------------------------------- #

def test_resolve_drops_below_threshold():
    r = qp._resolve_intents(_conf(database=0.9, qa=0.3), threshold=0.5)
    assert [p.label for p in r] == ["database"]


def test_resolve_terminal_is_exclusive_and_prioritized():
    r = qp._resolve_intents(
        _conf(safety_policy=0.9, chitchat=0.9, qa=0.9), threshold=0.5
    )
    assert [p.label for p in r] == ["safety_policy"]
    # out_of_scope outranks clarification / chitchat
    r2 = qp._resolve_intents(
        _conf(out_of_scope=0.6, clarification_needed=0.9), threshold=0.5
    )
    assert [p.label for p in r2] == ["out_of_scope"]


def test_resolve_structured_output_rides_with_content_and_is_last():
    r = qp._resolve_intents(_conf(database=0.9, structured_output=0.8), threshold=0.5)
    assert [p.label for p in r] == ["database", "structured_output"]


def test_resolve_structured_output_never_alone():
    # Only the modifier passes -> a content intent (qa) is guaranteed.
    r = qp._resolve_intents(_conf(structured_output=0.9), threshold=0.5)
    assert [p.label for p in r] == ["qa", "structured_output"]


def test_resolve_content_fallback_when_none_pass_threshold():
    r = qp._resolve_intents(_conf(qa=0.3, database=0.2), threshold=0.5)
    assert [p.label for p in r] == ["qa"]  # top content kept


def test_resolve_orders_content_by_confidence():
    r = qp._resolve_intents(
        _conf(qa=0.6, database=0.9, summarization=0.7), threshold=0.5
    )
    assert [p.label for p in r] == ["database", "summarization", "qa"]


# --------------------------------------------------------------------------- #
# _primary_intent / _is_ambiguous.
# --------------------------------------------------------------------------- #

def test_primary_intent_prefers_terminal_then_top_content():
    assert qp._primary_intent(
        [IP(label="database", confidence=0.9, rationale=""),
         IP(label="structured_output", confidence=0.95, rationale="")]
    ) == "database"
    assert qp._primary_intent(
        [IP(label="chitchat", confidence=0.5, rationale=""),
         IP(label="qa", confidence=0.9, rationale="")]
    ) == "chitchat"
    assert qp._primary_intent([]) == "qa"


def test_is_ambiguous_on_near_tie_only():
    near = [IP(label="database", confidence=0.9, rationale=""),
            IP(label="qa", confidence=0.8, rationale="")]
    clear = [IP(label="database", confidence=0.9, rationale=""),
             IP(label="qa", confidence=0.5, rationale="")]
    assert qp._is_ambiguous(near) is True
    assert qp._is_ambiguous(clear) is False
    assert qp._is_ambiguous([IP(label="qa", confidence=0.9, rationale="")]) is False


# --------------------------------------------------------------------------- #
# _merge_understanding — intents + attributes + rewrite.
# --------------------------------------------------------------------------- #

def test_merge_votes_intents_and_attributes():
    samples = [
        _u([("database", 0.9)], query_rewrite="rw1", output_format="table",
           operation="count", scope=QS(theme="Climate")),
        _u([("database", 0.9)], query_rewrite="rw2", output_format="table",
           operation="count", scope=QS(theme="Climate")),
        _u([("database", 0.8), ("qa", 0.6)], query_rewrite="rw3",
           output_format="prose", operation=None, scope=QS(theme=None)),
    ]
    m = qp._merge_understanding(samples, threshold=0.5)
    assert [p.label for p in m.intents] == ["database"]  # qa at 1/3 dropped
    assert m.output_format == "table"                    # 2/3
    assert m.operation == "count"                        # 2/3
    assert m.scope.theme == "Climate"                    # 2/3
    assert m.query_rewrite == "rw1"                       # first sample matching primary


# --------------------------------------------------------------------------- #
# Legacy derivation consumed by the current pipeline.
# --------------------------------------------------------------------------- #

def _mk(labels, **kw):
    kw.setdefault("query_rewrite", "q")
    return QU(intents=[IP(label=l, confidence=c, rationale="") for l, c in labels], **kw)


def test_derive_database_maps_to_structured():
    a = qp._to_legacy_analysis("q", _mk(
        [("database", 1.0), ("structured_output", 0.8)],
        output_format="table", operation="count",
        scope=QS(date_from="2024-01-01", date_to="2025-01-01"),
    ))
    assert a.intent == "structured"
    assert a.answer_format == "table"
    assert a.operation == "count"
    assert a.date_from == "2024-01-01"


def test_derive_summarization_single_doc_is_qa_summary():
    a = qp._to_legacy_analysis("q", _mk(
        [("summarization", 0.9)],
        scope=QS(target="single_document"), title_contains="Thoothukudi",
    ))
    assert a.intent == "qa"
    assert a.answer_format == "summary"
    assert a.title_contains == "Thoothukudi"


def test_derive_summarization_set_is_scoped_summary():
    a = qp._to_legacy_analysis("q", _mk(
        [("summarization", 0.9)], scope=QS(target="document_set", theme="Climate"),
    ))
    assert a.intent == "scoped_summary"
    assert a.theme == "Climate"


def test_derive_comparison_maps_to_qa():
    assert qp._to_legacy_analysis("q", _mk([("comparison", 0.9)])).intent == "qa"


def test_derive_terminals_map_to_chitchat():
    for term in ("chitchat", "clarification_needed", "safety_policy"):
        assert qp._to_legacy_analysis("q", _mk([(term, 0.9)])).intent == "chitchat"


def test_derive_out_of_scope_routes_to_qa():
    # A stochastic out_of_scope verdict must not blindly deflect: route it
    # through retrieval so the corpus (not one LLM sample) decides — a real miss
    # still ends in the grounded refusal downstream.
    assert qp._to_legacy_analysis("q", _mk([("out_of_scope", 0.9)])).intent == "qa"


def test_derive_source_type_uploaded_is_dropped_pdf_kept():
    assert qp._to_legacy_analysis(
        "q", _mk([("qa", 0.9)], scope=QS(source_type="uploaded"))
    ).source_type is None
    assert qp._to_legacy_analysis(
        "q", _mk([("qa", 0.9)], scope=QS(source_type="pdf"))
    ).source_type == "pdf"


def test_derive_unknown_format_degrades_to_default():
    a = qp._to_legacy_analysis(
        "q", _mk([("qa", 0.9), ("structured_output", 0.8)], output_format="csv")
    )
    assert a.answer_format == "default"


def test_derive_search_query_falls_back_to_question():
    a = qp._to_legacy_analysis("the original", _mk([("qa", 0.9)], query_rewrite="  "))
    assert a.search_query == "the original"


# --------------------------------------------------------------------------- #
# process() exposes the full understanding.
# --------------------------------------------------------------------------- #

class _One:
    def __init__(self, obj):
        self._obj = obj

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        return self._obj


def test_process_exposes_understanding(monkeypatch):
    u = _mk([("database", 0.9), ("structured_output", 0.8)],
            output_format="table", operation="count")
    monkeypatch.setattr(qp, "get_structured_llm", lambda: _One(u))
    monkeypatch.setattr(qp, "get_settings", lambda: SimpleNamespace(analysis_votes=1))

    pq = qp.process("show tenders in a table")

    assert pq.understanding is not None
    assert [p.label for p in pq.understanding.intents] == ["database", "structured_output"]
    assert pq.intent == "structured"      # legacy derivation
    assert pq.answer_format == "table"
