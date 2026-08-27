"""Readiness has to mean "this process can do its job".

`/ready` probed Qdrant and nothing else, so the ingestion server reported ready
while MySQL — its system of record, holding the crawl cursor, the retry floor
and every write it makes — was unreachable.

Which stores are *required* differs by process, and that difference is the point:
the retrieval server answers from Qdrant, so a catalog blip degrades structured
answers rather than ending the service, and taking it out of a load balancer for
that would turn a degraded feature into an outage.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import health
from app.config import get_settings


@pytest.fixture(autouse=True)
def _clean_requirements(monkeypatch):
    """Requirements are process-wide; keep each test's to itself."""
    monkeypatch.setattr(health, "_REQUIRED_STORES", set())


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(health.router)
    return TestClient(app)


@pytest.fixture
def probes(monkeypatch):
    """Control what each store answers."""
    state = {"qdrant": True, "mysql": True}

    def qdrant():
        if not state["qdrant"]:
            raise RuntimeError("qdrant refused the connection")
        return {"reachable": True, "collection": "documents", "points": 10}

    def mysql():
        if not state["mysql"]:
            raise RuntimeError("mysql refused the connection")
        return {"reachable": True, "database": "arc_db"}

    monkeypatch.setattr(health, "_qdrant_status", qdrant)
    monkeypatch.setattr(health, "_mysql_status", mysql)
    monkeypatch.setattr(health, "_redis_status", lambda: {"configured": False})
    monkeypatch.setattr(health, "_neo4j_status", lambda: {"enabled": False})
    return state


def test_everything_up_is_ready(client, probes):
    assert client.get("/ready").status_code == 200


def test_qdrant_down_is_never_ready(client, probes):
    """Required everywhere: without it there is nothing to retrieve from."""
    probes["qdrant"] = False

    assert client.get("/ready").status_code == 503


def test_mysql_down_is_not_ready_where_it_is_required(client, probes):
    """The ingestion server declares this (app.ingest_main)."""
    health.require_for_readiness("mysql")
    probes["mysql"] = False

    assert client.get("/ready").status_code == 503


def test_mysql_down_still_serves_where_it_is_not_required(client, probes):
    """The retrieval server's dense path does not touch MySQL; a catalog blip
    must not pull the whole API out of rotation."""
    probes["mysql"] = False

    assert client.get("/ready").status_code == 200


def test_the_ingestion_server_requires_mysql():
    """Asserted against the app itself, not a fixture, so the wiring is what is
    being tested."""
    import app.ingest_main  # noqa: F401  (importing is what registers it)

    assert "mysql" in health._REQUIRED_STORES


def test_the_body_stays_bare_unless_ops_detail_is_on(client, probes, monkeypatch):
    """Error strings and point counts fingerprint a deployment; the status code
    is the contract."""
    monkeypatch.setattr(get_settings(), "ops_detail_enabled", False)
    probes["qdrant"] = False

    body = client.get("/ready").json()

    assert body == {"status": "not_ready"}


def test_detail_names_the_store_that_failed(client, probes, monkeypatch):
    monkeypatch.setattr(get_settings(), "ops_detail_enabled", True)
    health.require_for_readiness("mysql")
    probes["mysql"] = False

    body = client.get("/ready").json()

    assert body["status"] == "not_ready"
    assert body["mysql"]["reachable"] is False
    assert "refused" in body["mysql"]["error"]
    assert body["qdrant"]["reachable"] is True, "and which one was fine"


def test_a_healthy_detail_body_reports_every_store(client, probes, monkeypatch):
    monkeypatch.setattr(get_settings(), "ops_detail_enabled", True)

    body = client.get("/ready").json()

    assert body["status"] == "ready"
    for store in ("qdrant", "mysql", "redis", "neo4j"):
        assert store in body


def test_an_unrequired_store_is_not_probed_when_nobody_will_read_it(
    client, probes, monkeypatch
):
    """A probe is a request per health check; don't spend one on a value the
    response will not carry and readiness does not depend on."""
    monkeypatch.setattr(get_settings(), "ops_detail_enabled", False)
    called: list[str] = []
    monkeypatch.setattr(
        health, "_mysql_status",
        lambda: called.append("mysql") or {"reachable": True},
    )

    assert client.get("/ready").status_code == 200
    assert called == []
