"""Phase 4b: combined (database + content) answers.

Covers the capability read, the deterministic catalog section, and the sectioned
composition in _assemble. The full _prepare/stream integration hits Qdrant/LLM
and is out of scope here; these test the composition seams. No network.
"""

from __future__ import annotations

from app.pipeline import query_pipeline as pipe
from app.retrieval import query_processor as qp
from app.retrieval.context_builder import ContextBlock


def _pq(labels=None, **kw):
    understanding = None
    if labels is not None:
        understanding = qp.QueryUnderstanding(
            query_rewrite="q",
            intents=[
                qp.IntentPrediction(label=lbl, confidence=c, rationale="")
                for lbl, c in labels
            ],
        )
    kw.setdefault("original", "q")
    kw.setdefault("search_query", "q")
    kw.setdefault("intent", "qa")
    return qp.ProcessedQuery(understanding=understanding, **kw)


def _gen(db_prefix=""):
    blocks = [
        ContextBlock(
            n=1, text="Rooftop solar grew 1.2 GW in 2023.",
            payload={"source_type": "pdf", "title": "Report"},
        )
    ]
    return pipe._Generation(
        pq=_pq(intent="qa"), blocks=blocks, query_vector=[0.0], top_k=6, db_prefix=db_prefix,
    )


# --------------------------------------------------------------------------- #
# _capabilities
# --------------------------------------------------------------------------- #

def test_capabilities_reads_understanding():
    pq = _pq([("database", 0.9), ("qa", 0.8)], intent="structured")
    assert pipe._capabilities(pq) == {"database", "qa"}


def test_capabilities_empty_on_passthrough():
    assert pipe._capabilities(_pq(labels=None)) == set()


# --------------------------------------------------------------------------- #
# _db_section
# --------------------------------------------------------------------------- #

def test_db_section_uses_analysis_slots(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.structured.answerer.answer_structured",
        lambda q, h, *, analysis: {"answer": "There are 12 reports matching your query."},
    )
    pq = _pq(
        [("database", 0.9), ("qa", 0.8)],
        analysis=qp.QueryAnalysis(search_query="q", operation="count", bundle="report"),
    )
    assert pipe._db_section(pq, "q", None) == "There are 12 reports matching your query."


def test_db_section_empty_without_operation():
    pq = _pq([("qa", 0.9)], analysis=qp.QueryAnalysis(search_query="q"))
    assert pipe._db_section(pq, "q", None) == ""


def test_db_section_empty_when_structured_fails(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.structured.answerer.answer_structured", lambda q, h, *, analysis: None
    )
    pq = _pq(
        [("database", 0.9)],
        analysis=qp.QueryAnalysis(search_query="q", operation="count", bundle="report"),
    )
    assert pipe._db_section(pq, "q", None) == ""


# --------------------------------------------------------------------------- #
# _assemble composition
# --------------------------------------------------------------------------- #

def test_assemble_prefixes_db_section():
    out = pipe._assemble(
        "Rooftop solar grew 1.2 GW in 2023 [1].",
        _gen(db_prefix="There are 12 reports matching your query."),
    )
    assert out["answer"] == (
        "There are 12 reports matching your query.\n\n"
        "Rooftop solar grew 1.2 GW in 2023 [1]."
    )
    assert out["used_chunks"] == 1
    assert out["numeric_mismatch"] is False  # numbers checked against content only


def test_assemble_no_prefix_is_content_only():
    out = pipe._assemble("Rooftop solar grew 1.2 GW in 2023 [1].", _gen(db_prefix=""))
    assert out["answer"] == "Rooftop solar grew 1.2 GW in 2023 [1]."


# --------------------------------------------------------------------------- #
# Empty-retrieval catalog fallback: asked only when the catalog hasn't already
# answered nothing for this query.
# --------------------------------------------------------------------------- #

_LISTING = {"answer": "- Solar in India (http://a)", "citations": [], "intent": "structured",
            "used_chunks": 1, "conflict": False, "cached": False}


def _wire_prepare(monkeypatch, pq, *, blocks=(), fallback=_LISTING):
    """Stub everything _prepare reaches except the branch under test. Returns the
    call log for the catalog fallback."""
    calls: list = []

    def fake_fallback(question, *, analysis):
        calls.append(question)
        return dict(fallback) if fallback is not None else None

    monkeypatch.setattr(pipe, "process", lambda q, h: pq)
    monkeypatch.setattr(pipe, "retrieve", lambda *a, **k: list(blocks))
    monkeypatch.setattr("app.core.clients.embeddings.embed_query", lambda q: [0.1])
    monkeypatch.setattr("app.cache.semantic_cache.lookup", lambda *a, **k: None)
    monkeypatch.setattr(
        "app.retrieval.structured.answerer.catalog_fallback", fake_fallback
    )
    return calls


def _qa_pq():
    return _pq(
        [("qa", 0.9)], intent="qa",
        analysis=qp.QueryAnalysis(search_query="q", intent="qa", title_contains="Solar"),
    )


def test_empty_retrieval_offers_the_catalog_listing(monkeypatch):
    """A content question retrieval could not ground: the catalog places documents
    by title/facet, so offer those rather than a blanket refusal."""
    from app.generation.prompts import NO_CONTENT_WITH_CATALOG

    calls = _wire_prepare(monkeypatch, _qa_pq())
    result, generation = pipe._prepare(
        "q", history=None, top_k=None
    )
    assert generation is None
    assert len(calls) == 1
    assert result["answer"] == f"{NO_CONTENT_WITH_CATALOG}\n\n- Solar in India (http://a)"
    assert result["intent"] == "qa"  # not relabelled as structured


def test_empty_retrieval_refuses_when_the_catalog_has_nothing(monkeypatch):
    calls = _wire_prepare(monkeypatch, _qa_pq(), fallback=None)
    result, _ = pipe._prepare(
        "q", history=None, top_k=None
    )
    assert len(calls) == 1
    assert result["answer"] == pipe.REFUSAL


def test_catalog_error_degrades_to_the_refusal(monkeypatch):
    """This path is already refusing; a catalog failure must not turn it into a 500."""
    _wire_prepare(monkeypatch, _qa_pq())
    monkeypatch.setattr(
        "app.retrieval.structured.answerer.catalog_fallback",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("MySQL down")),
    )
    result, _ = pipe._prepare(
        "q", history=None, top_k=None
    )
    assert result["answer"] == pipe.REFUSAL


def test_combined_query_does_not_re_ask_the_catalog(monkeypatch):
    """`_db_section` already asked and got nothing; asking again would re-run the
    query that just came back empty."""
    pq = _pq(
        [("database", 0.9), ("qa", 0.8)], intent="structured",
        analysis=qp.QueryAnalysis(search_query="q", intent="structured",
                                  operation="count", title_contains="Solar"),
    )
    calls = _wire_prepare(monkeypatch, pq)
    monkeypatch.setattr(pipe, "_db_section", lambda *a, **k: "")
    result, _ = pipe._prepare(
        "q", history=None, top_k=None
    )
    assert calls == []  # the catalog was consulted once, upstream
    assert result["answer"] == pipe.REFUSAL


def test_structured_fallthrough_does_not_re_ask_the_catalog(monkeypatch):
    """answer_structured returned None — the catalog already had nothing."""
    pq = _pq(
        [("database", 0.9)], intent="structured",
        analysis=qp.QueryAnalysis(search_query="q", intent="structured",
                                  operation="count", title_contains="Solar"),
    )
    calls = _wire_prepare(monkeypatch, pq)
    monkeypatch.setattr(
        "app.retrieval.structured.tools.resolve_lookup_chain", lambda a, q: None
    )
    monkeypatch.setattr(
        "app.retrieval.structured.answerer.answer_structured",
        lambda q, h, *, analysis: None,
    )
    result, _ = pipe._prepare(
        "q", history=None, top_k=None
    )
    assert calls == []
    assert result["answer"] == pipe.REFUSAL


def test_grounded_answer_never_asks_the_catalog(monkeypatch):
    """The fallback costs nothing on the happy path."""
    blocks = [ContextBlock(n=1, text="Solar grew.", payload={"source_type": "website"})]
    calls = _wire_prepare(monkeypatch, _qa_pq(), blocks=blocks)
    result, generation = pipe._prepare(
        "q", history=None, top_k=None
    )
    assert result is None and generation is not None
    assert calls == []
