"""Unit tests for the async answer-quality monitor.

Covers enqueue gating (flag off, blank answers), silent drop on a full queue,
exception safety, the worker's judging path (coverage always, faithfulness
judge sampled), and the _persist hook wiring. Judges and caches are stubbed;
no threads, no network.
"""

from __future__ import annotations

import queue
from types import SimpleNamespace

import app.rag as rag
from app.cache import redis_cache, semantic_cache
from app.generation import faithfulness as fa
from app.observability import quality_monitor as qm
from app.retrieval.query_processor import ProcessedQuery


def _wire(monkeypatch, *, enabled=True, sample=1.0, maxsize=8):
    fresh: "queue.Queue[qm._Item]" = queue.Queue(maxsize=maxsize)
    monkeypatch.setattr(qm, "_queue", fresh)
    monkeypatch.setattr(qm, "_ensure_worker", lambda: None)  # no real thread
    monkeypatch.setattr(
        qm, "get_settings",
        lambda: SimpleNamespace(quality_monitor_enabled=enabled,
                                quality_judge_sample=sample),
    )
    return fresh


def _enqueue(**kw):
    kw.setdefault("question", "q")
    kw.setdefault("answer", "answer [1]")
    kw.setdefault("block_texts", ["block"])
    kw.setdefault("citations", [{"n": 1}])
    qm.enqueue(**kw)


# --------------------------------------------------------------------------- #
# Enqueue gating and drop behavior.
# --------------------------------------------------------------------------- #

def test_enqueue_queues_item_when_enabled(monkeypatch):
    q = _wire(monkeypatch)
    _enqueue()
    item = q.get_nowait()
    assert item.answer == "answer [1]" and item.block_texts == ["block"]


def test_enqueue_disabled_or_blank_skips(monkeypatch):
    q = _wire(monkeypatch, enabled=False)
    _enqueue()
    assert q.empty()

    q = _wire(monkeypatch, enabled=True)
    _enqueue(answer="   ")
    assert q.empty()


def test_enqueue_full_queue_drops_silently(monkeypatch):
    q = _wire(monkeypatch, maxsize=1)
    _enqueue()
    _enqueue()  # queue full — must neither block nor raise
    assert q.qsize() == 1


def test_enqueue_never_raises(monkeypatch):
    def boom():
        raise RuntimeError("settings unavailable")

    monkeypatch.setattr(qm, "get_settings", boom)
    _enqueue()  # swallowed


# --------------------------------------------------------------------------- #
# Worker processing.
# --------------------------------------------------------------------------- #

def _item(**kw):
    kw.setdefault("question", "q")
    kw.setdefault("answer", "Grew 40% [1]. Unsourced line.")
    kw.setdefault("block_texts", ["capacity rose by 40%"])
    kw.setdefault("citations", [{"n": 1}])
    return qm._Item(**kw)


def test_process_logs_coverage_and_judge_verdict(monkeypatch, caplog):
    _wire(monkeypatch, sample=1.0)
    monkeypatch.setattr(
        qm, "_judge",
        lambda item: fa.FaithfulnessReport(faithful=False, unsupported=["Unsourced line"]),
    )
    with caplog.at_level("INFO", logger="app.observability.quality_monitor"):
        qm._process(_item())

    line = next(r.getMessage() for r in caplog.records if "quality_metrics" in r.getMessage())
    assert "'citation_coverage': 0.5" in line
    assert "'faithful': False" in line and "'unsupported_claims': 1" in line
    assert "'q'" not in line  # lengths only; no query text in logs


def test_process_sample_zero_skips_judge(monkeypatch, caplog):
    _wire(monkeypatch, sample=0.0)

    def no_judge(item):
        raise AssertionError("judge must not run at sample=0")

    monkeypatch.setattr(qm, "_judge", no_judge)
    with caplog.at_level("INFO", logger="app.observability.quality_monitor"):
        qm._process(_item())
    line = next(r.getMessage() for r in caplog.records if "quality_metrics" in r.getMessage())
    assert "citation_coverage" in line and "faithful" not in line


def test_judge_builds_blocks_and_fails_open(monkeypatch):
    seen: dict = {}

    def fake_verify(answer, blocks):
        seen["blocks"] = [(b.n, b.text) for b in blocks]
        return fa.FaithfulnessReport(faithful=True)

    monkeypatch.setattr(fa, "verify", fake_verify)
    report = qm._judge(_item(block_texts=["one", "two"]))
    assert report.faithful is True
    assert seen["blocks"] == [(1, "one"), (2, "two")]

    def boom(answer, blocks):
        raise RuntimeError("judge down")

    monkeypatch.setattr(fa, "verify", boom)
    assert qm._judge(_item()) is None


# --------------------------------------------------------------------------- #
# _persist hook wiring.
# --------------------------------------------------------------------------- #

def test_persist_enqueues_fresh_answer(monkeypatch):
    monkeypatch.setattr(redis_cache, "set_response", lambda sig, result: None)
    monkeypatch.setattr(semantic_cache, "store", lambda *a, **kw: None)
    captured: dict = {}
    monkeypatch.setattr(qm, "enqueue", lambda **kw: captured.update(kw))

    from app.retrieval.context_builder import ContextBlock

    gen = rag._Generation(
        pq=ProcessedQuery(original="the question", search_query="q"),
        blocks=[ContextBlock(n=1, text="block text")],
        query_vector=[0.1], signature="sig", tenant_id="default",
        user_groups=["public"], top_k=6,
    )
    result = {"answer": "a [1]", "citations": [{"n": 1}]}
    rag._persist(gen, result)

    assert captured["question"] == "the question"
    assert captured["answer"] == "a [1]"
    assert captured["block_texts"] == ["block text"]
    assert captured["citations"] == [{"n": 1}]
