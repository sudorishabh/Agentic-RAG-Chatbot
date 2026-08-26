"""The graph supplements retrieval; it no longer replaces it.

`retrieve` used to return a graph answer verbatim, which is right when the rows
are the whole answer and wrong the moment they are only part of it. Measured on
the live corpus: "a brief history of TERI" routes to `entity_timeline`, the graph
answers with eleven funding and partnership rows, and the evidence is the project
pages those claims came from — none of which says when TERI was founded. The
Annual Report chunk beginning "TERI was established in 1974" sat at 0.77
similarity and was never fetched, so the answer was the refusal.
"""
from __future__ import annotations

import pytest

from app.core.models.context import ContextBlock
from app.retrieval.retriever import (
    SEMANTIC_MIN_SLOTS,
    _block_key,
    _merge_graph_and_retrieval,
)

BUDGET = 100_000


def _facts(text="verified relationships"):
    return ContextBlock(n=1, text=text, payload={"kind": "graph_facts"})


def _block(name, *, text=None, parent=None, chunk=None, document=None):
    return ContextBlock(
        n=0, text=text or f"text of {name}",
        payload={
            "title": name, "source_type": "website",
            "parent_chunk_id": parent, "chunk_id": chunk or name,
            "document_id": document or name,
        },
    )


def _titles(blocks):
    return [
        "GRAPH" if b.payload.get("kind") == "graph_facts" else b.payload.get("title")
        for b in blocks
    ]


def test_the_facts_block_leads_and_prose_still_gets_in():
    """The shape the TERI question needed: the graph's answer, its provenance,
    and the About page that actually describes the institute."""
    graph = [_facts(), _block("g1"), _block("g2"), _block("g3"), _block("g4")]
    semantic = [_block("Mission and Goals"), _block("Annual Report"), _block("s3")]
    merged = _merge_graph_and_retrieval(graph, semantic, limit=6, token_budget=BUDGET)

    assert len(merged) == 6
    assert merged[0].payload.get("kind") == "graph_facts"
    assert "Mission and Goals" in _titles(merged)
    assert "Annual Report" in _titles(merged)


def test_prose_keeps_its_reserved_slots_however_much_evidence_the_graph_has():
    graph = [_facts()] + [_block(f"g{i}") for i in range(20)]
    semantic = [_block(f"s{i}") for i in range(20)]
    merged = _merge_graph_and_retrieval(graph, semantic, limit=6, token_budget=BUDGET)

    kept = [t for t in _titles(merged) if str(t).startswith("s")]
    assert len(kept) >= SEMANTIC_MIN_SLOTS
    assert len(merged) == 6


def test_the_graph_takes_the_slots_prose_cannot_fill():
    """Reserving for prose that does not exist would waste the context."""
    graph = [_facts()] + [_block(f"g{i}") for i in range(10)]
    merged = _merge_graph_and_retrieval(graph, [], limit=6, token_budget=BUDGET)
    assert len(merged) == 6
    assert _titles(merged) == ["GRAPH", "g0", "g1", "g2", "g3", "g4"]


def test_a_graph_answer_with_no_evidence_still_leads():
    graph = [_facts()]
    semantic = [_block("s1"), _block("s2"), _block("s3")]
    merged = _merge_graph_and_retrieval(graph, semantic, limit=6, token_budget=BUDGET)
    assert _titles(merged) == ["GRAPH", "s1", "s2", "s3"]


def test_a_graph_leg_that_answered_nothing_leaves_retrieval_untouched():
    semantic = [_block("s1"), _block("s2")]
    assert _merge_graph_and_retrieval([], semantic, limit=6, token_budget=BUDGET) == semantic


def test_the_same_passage_is_not_printed_twice():
    """The graph hydrates a chunk the semantic pull may also admit."""
    shared = _block("shared", chunk="c-1")
    graph = [_facts(), shared]
    semantic = [_block("shared copy", chunk="c-1"), _block("other", chunk="c-2")]
    merged = _merge_graph_and_retrieval(graph, semantic, limit=6, token_budget=BUDGET)
    assert _titles(merged) == ["GRAPH", "shared", "other"]


def test_de_duplication_prefers_the_parent_because_admission_does():
    """Two different children of one parent are one passage after expansion."""
    graph = [_facts(), _block("g-child", parent="p-1", chunk="c-1")]
    semantic = [_block("s-child", parent="p-1", chunk="c-2")]
    merged = _merge_graph_and_retrieval(graph, semantic, limit=6, token_budget=BUDGET)
    assert _titles(merged) == ["GRAPH", "g-child"]


def test_blocks_are_renumbered_contiguously_from_one():
    graph = [_facts(), _block("g1")]
    semantic = [_block("s1"), _block("s2")]
    merged = _merge_graph_and_retrieval(graph, semantic, limit=6, token_budget=BUDGET)
    assert [b.n for b in merged] == list(range(1, len(merged) + 1))


def test_one_shared_token_budget_rather_than_two():
    """The facts block used to be appended after `build_context` had already
    spent its allowance, so a graph answer could exceed the budget by a whole
    context. Both legs are now paid for out of the same purse."""
    graph = [_facts("g " * 400), _block("g1", text="a " * 400)]
    semantic = [_block("s1", text="b " * 400), _block("s2", text="c " * 400)]
    merged = _merge_graph_and_retrieval(graph, semantic, limit=6, token_budget=500)

    from app.retrieval.context.builder import _count_tokens

    assert len(merged) < 4
    # The first block is admitted whatever it costs; every later one fits.
    assert sum(_count_tokens(b.text) for b in merged[1:]) <= 500


def test_a_context_is_never_empty_just_because_the_first_block_is_large():
    graph = [_facts("g " * 5000)]
    merged = _merge_graph_and_retrieval(graph, [_block("s1")], limit=6, token_budget=10)
    assert merged and merged[0].payload.get("kind") == "graph_facts"


def test_the_limit_is_never_exceeded():
    graph = [_facts()] + [_block(f"g{i}") for i in range(10)]
    semantic = [_block(f"s{i}") for i in range(10)]
    for limit in (1, 2, 3, 6, 9):
        merged = _merge_graph_and_retrieval(
            graph, semantic, limit=limit, token_budget=BUDGET
        )
        assert len(merged) == limit


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"parent_chunk_id": "p", "chunk_id": "c", "document_id": "d"}, "p"),
        ({"chunk_id": "c", "document_id": "d"}, "c"),
        ({"document_id": "d"}, "d"),
    ],
)
def test_the_dedup_key_prefers_parent_then_chunk_then_document(payload, expected):
    assert _block_key(ContextBlock(n=1, text="t", payload=payload)) == expected


def test_retrieve_no_longer_short_circuits_on_a_graph_answer(monkeypatch):
    """The regression in one line: the semantic legs must still run."""
    from app.retrieval import retriever

    ran = {"search": 0}
    facts = _facts()
    monkeypatch.setattr(
        retriever, "graph_blocks_for",
        lambda q, *, n, filters=None, source_type=None: [facts],
    )
    monkeypatch.setattr(retriever, "embed_query", lambda *a, **kw: [0.0])

    def _search(*a, **kw):
        ran["search"] += 1
        return []

    monkeypatch.setattr(retriever, "search", _search)
    monkeypatch.setattr(retriever, "dual_search", _search)
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "graph_routing_enabled", True, raising=False)
    retriever.retrieve("Can you give a brief history of TERI?", n=6)
    assert ran["search"] >= 1, "the corpus must still be searched"
