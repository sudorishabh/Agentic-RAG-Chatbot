"""Unit tests for the stage-timing metrics system.

Covers the aggregate registry (counts, totals, percentiles, ordering), the
tracing.span() hook that feeds it, the per-request breakdown collector —
including a generator resumed in a foreign context, the shape the chat SSE
driver produces — and the /metrics/timings endpoint gate.
"""

from __future__ import annotations

import contextvars

import pytest

from app.observability import metrics
from app.observability.tracing import span


@pytest.fixture(autouse=True)
def _clean_registry():
    metrics.reset()
    yield
    metrics.reset()


def test_record_stage_aggregates():
    for ms in (10.0, 20.0, 30.0):
        metrics.record_stage("rag.search", ms)
    metrics.record_stage("rag.generate", 100.0)

    snap = metrics.snapshot()
    by_name = {s["stage"]: s for s in snap["stages"]}

    search = by_name["rag.search"]
    assert search["count"] == 3
    assert search["total_ms"] == 60.0
    assert search["avg_ms"] == 20.0
    assert search["p50_ms"] == 20.0
    assert search["max_ms"] == 30.0

    # sorted by total time, biggest first
    assert snap["stages"][0]["stage"] == "rag.generate"


def test_component_totals_groups_and_excludes_parents():
    stages = {
        "rag.search": 200.0,          # qdrant
        "rag.semantic_cache": 30.0,   # qdrant
        "rag.generate": 1500.0,       # llm
        "rag.embed_query": 80.0,      # embedding
        "rag.context_build": 5.0,     # other (unmapped)
        "rag.stream_answer": 1900.0,  # parent — excluded
    }
    totals = metrics.component_totals(stages)
    assert totals == {
        "llm": 1500.0,
        "qdrant": 230.0,
        "embedding": 80.0,
        "other": 5.0,
    }
    assert list(totals) == ["llm", "qdrant", "embedding", "other"]  # sorted desc


def test_snapshot_reports_components():
    metrics.record_stage("rag.search", 300.0)
    metrics.record_stage("rag.generate", 700.0)
    metrics.record_stage("rag.stream_answer", 1050.0)  # parent, not attributed

    snap = metrics.snapshot()
    by_component = {c["component"]: c for c in snap["components"]}
    assert set(by_component) == {"qdrant", "llm"}
    assert by_component["llm"]["total_ms"] == 700.0
    assert by_component["llm"]["share_pct"] == 70.0
    assert by_component["qdrant"]["share_pct"] == 30.0

    by_stage = {s["stage"]: s for s in snap["stages"]}
    assert by_stage["rag.search"]["component"] == "qdrant"
    assert by_stage["rag.stream_answer"]["component"] == "total"


def test_span_feeds_registry():
    with span("test.stage"):
        pass
    by_name = {s["stage"]: s for s in metrics.snapshot()["stages"]}
    assert by_name["test.stage"]["count"] == 1


def test_collect_into_gathers_breakdown():
    breakdown: dict[str, float] = {}
    with metrics.collect_into(breakdown):
        metrics.record_stage("rag.search", 12.0)
        metrics.record_stage("rag.search", 8.0)
        metrics.record_stage("rag.rerank", 5.0)
    metrics.record_stage("rag.rerank", 99.0)  # outside: aggregate only

    assert breakdown == {"rag.search": 20.0, "rag.rerank": 5.0}
    by_name = {s["stage"]: s for s in metrics.snapshot()["stages"]}
    assert by_name["rag.rerank"]["count"] == 2


def test_collect_into_survives_foreign_context_resume():
    """Mimic app.api.chat._sse: each next() runs in a fresh context copy."""
    breakdown: dict[str, float] = {}

    def gen():
        with metrics.collect_into(breakdown):
            metrics.record_stage("rag.search", 7.0)
            yield "token"
            metrics.record_stage("rag.semantic_cache_store", 3.0)

    events = gen()
    parent = contextvars.copy_context()
    assert parent.run(next, events) == "token"
    with pytest.raises(StopIteration):
        contextvars.copy_context().run(next, events)

    # The pre-yield stage made it into the request dict; the post-yield one
    # only reached the global registry — and nothing raised.
    assert breakdown == {"rag.search": 7.0}
    by_name = {s["stage"]: s for s in metrics.snapshot()["stages"]}
    assert by_name["rag.semantic_cache_store"]["count"] == 1


def test_timings_endpoint_gated_by_ops_detail(monkeypatch):
    from fastapi.testclient import TestClient

    from app import app_factory
    from app.api.health import router
    from app.config import get_settings

    app = app_factory.FastAPI()
    app.include_router(router)
    client = TestClient(app)

    settings = get_settings()
    monkeypatch.setattr(settings, "ops_detail_enabled", False)
    assert client.get("/metrics/timings").status_code == 404

    monkeypatch.setattr(settings, "ops_detail_enabled", True)
    metrics.record_stage("rag.search", 42.0)
    body = client.get("/metrics/timings").json()
    assert body["stages"][0]["stage"] == "rag.search"
    assert body["stages"][0]["total_ms"] == 42.0
    assert body["components"][0]["component"] == "qdrant"


def test_timings_endpoint_admin_group_grant(monkeypatch):
    import time

    jwt = pytest.importorskip("jwt")  # PyJWT ships with the auth feature
    from fastapi.testclient import TestClient

    from app import app_factory
    from app.api.health import router
    from app.config import get_settings

    app = app_factory.FastAPI()
    app.include_router(router)
    client = TestClient(app)

    settings = get_settings()
    monkeypatch.setattr(settings, "ops_detail_enabled", False)
    monkeypatch.setattr(settings, "ops_admin_group", "admin")
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "jwt_secret", "test-secret")

    def token(groups):
        return jwt.encode(
            {"groups": groups, "exp": int(time.time()) + 60},
            "test-secret",
            algorithm="HS256",
        )

    def get(tok=None):
        headers = {"Authorization": f"Bearer {tok}"} if tok else {}
        return client.get("/metrics/timings", headers=headers)

    metrics.record_stage("rag.generate", 10.0)
    assert get(token(["admin"])).status_code == 200
    assert get(token(["public"])).status_code == 404  # wrong group
    assert get().status_code == 404                    # no token: hidden, not 401
    assert get("garbage").status_code == 404           # bad token: hidden too

    # group grant is meaningless without verified identities
    monkeypatch.setattr(settings, "auth_enabled", False)
    assert get(token(["admin"])).status_code == 404
