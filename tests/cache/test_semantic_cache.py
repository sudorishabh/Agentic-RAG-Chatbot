"""Unit tests for semantic-cache facet hardening.

Covers the facet fingerprint builder (normalization, compactness, passthrough)
and the lookup post-filter: a stored fingerprint must equal the query's, and
legacy entries without one count as mismatches. Qdrant and the partition key
are stubbed; no network.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.cache import semantic_cache as sc
from app.retrieval.understanding import query_processor as qp


@pytest.fixture(autouse=True)
def _enable_cache(monkeypatch):
    """These tests exercise the enabled cache path (store/lookup/facets). The
    cache short-circuits to a no-op when disabled, so pin it on regardless of
    the ambient .env (SEMANTIC_CACHE_ENABLED is false in some local setups)."""
    monkeypatch.setattr(sc.get_settings(), "semantic_cache_enabled", True)


def _pq(**analysis_kw):
    analysis = qp.QueryAnalysis(search_query="x", **analysis_kw)
    return qp.ProcessedQuery(
        original="q", search_query="x", intent=analysis.intent,
        source_type=analysis.source_type, language=analysis.language,
        analysis=analysis,
    )


class _FakeClient:
    def __init__(self, payload=None):
        self.payload = payload
        self.upserts: list = []

    def collection_exists(self, name):
        return True

    def query_points(self, **kw):
        points = [] if self.payload is None else [SimpleNamespace(payload=self.payload)]
        return SimpleNamespace(points=points)

    def upsert(self, collection_name, points):
        self.upserts.extend(points)


def _wire(monkeypatch, client):
    monkeypatch.setattr(sc, "_client", lambda: client)
    monkeypatch.setattr(sc, "semantic_partition", lambda *a: "scope-key")


def _lookup(fingerprint):
    return sc.lookup(
        [0.1], top_k=6,
        fingerprint=fingerprint,
    )


# --------------------------------------------------------------------------- #
# Fingerprint builder.
# --------------------------------------------------------------------------- #

def test_fingerprint_normalizes_and_compacts():
    pq = _pq(source_type="pdf", theme=" Climate Change ", author="Dr Sharma",
             date_from="2024-01-01", tags=["Solar", "biofuels"])
    assert sc.facet_fingerprint(pq) == {
        "source_type": "pdf",
        "theme": "climate change",
        "author": "dr sharma",
        "date_from": "2024-01-01",
        "tags": ["biofuels", "solar"],
    }


def test_fingerprint_empty_for_unfaceted_and_passthrough():
    assert sc.facet_fingerprint(_pq()) == {}
    passthrough = qp.ProcessedQuery(original="q", search_query="q")
    assert sc.facet_fingerprint(passthrough) == {}


# --------------------------------------------------------------------------- #
# Lookup post-filter.
# --------------------------------------------------------------------------- #

def test_lookup_returns_result_on_fingerprint_match(monkeypatch):
    payload = {"result": {"answer": "cached"}, "facets": {"theme": "climate change"}}
    _wire(monkeypatch, _FakeClient(payload))
    assert _lookup({"theme": "climate change"}) == {"answer": "cached"}


def test_lookup_rejects_fingerprint_mismatch(monkeypatch):
    payload = {"result": {"answer": "cached"}, "facets": {"date_from": "2023-01-01"}}
    _wire(monkeypatch, _FakeClient(payload))
    assert _lookup({"date_from": "2024-01-01"}) is None  # different year
    assert _lookup({}) is None  # cached was faceted, query is not


def test_lookup_treats_legacy_entries_as_mismatch(monkeypatch):
    payload = {"result": {"answer": "old"}}  # stored before fingerprints existed
    _wire(monkeypatch, _FakeClient(payload))
    assert _lookup({}) is None


def test_lookup_unfaceted_match(monkeypatch):
    payload = {"result": {"answer": "cached"}, "facets": {}}
    _wire(monkeypatch, _FakeClient(payload))
    assert _lookup(None) == {"answer": "cached"}


# --------------------------------------------------------------------------- #
# Store persists the fingerprint.
# --------------------------------------------------------------------------- #

def test_store_persists_facets(monkeypatch):
    client = _FakeClient()
    _wire(monkeypatch, client)
    monkeypatch.setattr(sc, "_ensure_collection", lambda c, dim: True)
    monkeypatch.setattr(sc, "_maybe_prune", lambda c, name: None)

    sc.store(
        [0.1], {"answer": "a"},
        top_k=6, fingerprint={"theme": "energy"},
    )
    assert client.upserts[0].payload["facets"] == {"theme": "energy"}

    sc.store(
        [0.1], {"answer": "a"}, top_k=6,
    )
    assert client.upserts[1].payload["facets"] == {}
