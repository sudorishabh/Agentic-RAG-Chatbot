"""The /search debug path exposes the full multi-label understanding.

process() and retrieve() are stubbed, so this asserts only the exposure wiring
in search_blocks (no Qdrant / LLM).
"""

from __future__ import annotations

from app.pipeline import query_pipeline as pipe
from app.retrieval.understanding import query_processor as qp


def _pq(labels, **kw):
    kw.setdefault("query_rewrite", "q")
    u = qp.QueryUnderstanding(
        intents=[
            qp.IntentPrediction(label=lbl, confidence=c, rationale=r)
            for lbl, c, r in labels
        ],
        **kw,
    )
    analysis = qp._to_legacy_analysis("q", u)
    return qp.ProcessedQuery(
        original="q",
        search_query=analysis.search_query,
        intent=analysis.intent,
        answer_format=analysis.answer_format,
        analysis=analysis,
        understanding=u,
    )


def test_search_blocks_exposes_intents(monkeypatch):
    pq = _pq(
        [("database", 0.9, "count"), ("structured_output", 0.8, "table")],
        output_format="table", operation="count",
    )
    monkeypatch.setattr(pipe, "process", lambda q, h: pq)
    monkeypatch.setattr(pipe, "retrieve", lambda *a, **k: [])

    out = pipe.search_blocks("show tenders in a table")

    assert out["intent"] == "structured"  # single-label route unchanged
    assert [i["label"] for i in out["intents"]] == ["database", "structured_output"]
    assert out["intents"][0]["confidence"] == 0.9
    assert out["intents"][0]["rationale"] == "count"
    assert out["is_ambiguous"] is False


def test_search_blocks_flags_ambiguous(monkeypatch):
    pq = _pq([("database", 0.9, "x"), ("qa", 0.8, "y")])
    monkeypatch.setattr(pipe, "process", lambda q, h: pq)
    monkeypatch.setattr(pipe, "retrieve", lambda *a, **k: [])

    out = pipe.search_blocks("q")

    assert out["is_ambiguous"] is True
