"""Phase 4b: combined (database + content) answers.

Covers the capability read, the deterministic catalog section, and the sectioned
composition in _assemble. The full _prepare/stream integration hits Qdrant/LLM
and is out of scope here; these test the composition seams. No network.
"""

from __future__ import annotations

from app import rag
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
    return rag._Generation(
        pq=_pq(intent="qa"), blocks=blocks, query_vector=[0.0],
        tenant_id="default", user_groups=["public"], top_k=6, db_prefix=db_prefix,
    )


# --------------------------------------------------------------------------- #
# _capabilities
# --------------------------------------------------------------------------- #

def test_capabilities_reads_understanding():
    pq = _pq([("database", 0.9), ("qa", 0.8)], intent="structured")
    assert rag._capabilities(pq) == {"database", "qa"}


def test_capabilities_empty_on_passthrough():
    assert rag._capabilities(_pq(labels=None)) == set()


# --------------------------------------------------------------------------- #
# _db_section
# --------------------------------------------------------------------------- #

def test_db_section_uses_analysis_slots(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.drupal_router.answer_structured",
        lambda q, h, *, analysis: {"answer": "There are 12 reports matching your query."},
    )
    pq = _pq(
        [("database", 0.9), ("qa", 0.8)],
        analysis=qp.QueryAnalysis(search_query="q", operation="count", bundle="report"),
    )
    assert rag._db_section(pq, "q", None) == "There are 12 reports matching your query."


def test_db_section_empty_without_operation():
    pq = _pq([("qa", 0.9)], analysis=qp.QueryAnalysis(search_query="q"))
    assert rag._db_section(pq, "q", None) == ""


def test_db_section_empty_when_structured_fails(monkeypatch):
    monkeypatch.setattr(
        "app.retrieval.drupal_router.answer_structured", lambda q, h, *, analysis: None
    )
    pq = _pq(
        [("database", 0.9)],
        analysis=qp.QueryAnalysis(search_query="q", operation="count", bundle="report"),
    )
    assert rag._db_section(pq, "q", None) == ""


# --------------------------------------------------------------------------- #
# _assemble composition
# --------------------------------------------------------------------------- #

def test_assemble_prefixes_db_section():
    out = rag._assemble(
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
    out = rag._assemble("Rooftop solar grew 1.2 GW in 2023 [1].", _gen(db_prefix=""))
    assert out["answer"] == "Rooftop solar grew 1.2 GW in 2023 [1]."
