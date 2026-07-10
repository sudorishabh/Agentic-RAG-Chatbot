"""Unit tests for id-scoped Qdrant retrieval and lead-parent fetching.

Covers the document_id filter construction on the scoped search, the
child→parent hop (batched retrieve, child-payload fallback), id capping, and
fail-open behavior. All Qdrant traffic goes to duck-typed fakes; no network.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.retrieval import hybrid_search, scoped_retrieval as sr


def _point(id="c1", score=0.9, payload=None, vector=None):
    return SimpleNamespace(id=id, score=score, payload=payload or {}, vector=vector or [0.1])


class _FakeClient:
    def __init__(self, *, query_points_result=None, scroll_points=None, retrieve_records=None):
        self.query_points_result = SimpleNamespace(points=query_points_result or [])
        self.scroll_points = scroll_points or []
        self.retrieve_records = retrieve_records or []
        self.calls: dict[str, dict] = {}

    def collection_exists(self, name):
        return True

    def query_points(self, **kw):
        self.calls["query_points"] = kw
        return self.query_points_result

    def scroll(self, **kw):
        self.calls["scroll"] = kw
        return self.scroll_points, None

    def retrieve(self, **kw):
        self.calls["retrieve"] = kw
        return self.retrieve_records


def _conditions(qfilter):
    return {getattr(c, "key", None): c for c in qfilter.must}


# --------------------------------------------------------------------------- #
# search_within_documents — dense search inside an id set.
# --------------------------------------------------------------------------- #

def test_scoped_search_filters_by_document_ids(monkeypatch):
    fake = _FakeClient(query_points_result=[_point(payload={"document_id": "d1"})])
    monkeypatch.setattr(hybrid_search, "get_qdrant_client", lambda: fake)

    out = sr.search_within_documents([0.1, 0.2], ["d1", "d2"], limit=5)

    assert len(out) == 1 and out[0].payload["document_id"] == "d1"
    kw = fake.calls["query_points"]
    assert kw["limit"] == 5 and kw["query"] == [0.1, 0.2]
    conds = _conditions(kw["query_filter"])
    assert conds["document_id"].match.any == ["d1", "d2"]
    # Tenant/ACL mandatory filter still applies to scoped pulls.
    assert conds["is_parent"].match.value is False
    assert conds["tenant_id"].match.value == "default"


def test_scoped_search_empty_ids_skip_qdrant(monkeypatch):
    def no_client():
        raise AssertionError("client must not be created")

    monkeypatch.setattr(hybrid_search, "get_qdrant_client", no_client)
    assert sr.search_within_documents([0.1], [], limit=5) == []
    assert sr.search_within_documents([0.1], ["", None], limit=5) == []


def test_scoped_search_caps_id_set(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(hybrid_search, "get_qdrant_client", lambda: fake)

    sr.search_within_documents([0.1], [f"d{i}" for i in range(500)], limit=5)

    conds = _conditions(fake.calls["query_points"]["query_filter"])
    assert len(conds["document_id"].match.any) == sr._MAX_IDS


def test_scoped_search_fails_open(monkeypatch):
    def boom():
        raise RuntimeError("qdrant down")

    monkeypatch.setattr(hybrid_search, "get_qdrant_client", boom)
    assert sr.search_within_documents([0.1], ["d1"], limit=5) == []


# --------------------------------------------------------------------------- #
# lead_parents — first child -> parent payload per document.
# --------------------------------------------------------------------------- #

def test_lead_parents_hops_to_parent_with_child_fallback(monkeypatch):
    children = [
        _point(id="c1", payload={"document_id": "d1", "parent_chunk_id": "p1",
                                 "chunk_text": "child 1"}),
        _point(id="c2", payload={"document_id": "d2", "chunk_text": "only child"}),
    ]
    parents = [_point(id="p1", payload={"document_id": "d1", "chunk_text": "parent 1"})]
    fake = _FakeClient(scroll_points=children, retrieve_records=parents)
    monkeypatch.setattr(sr, "get_qdrant_client", lambda: fake)

    out = sr.lead_parents(["d1", "d2"])

    assert out["d1"]["chunk_text"] == "parent 1"
    assert out["d2"]["chunk_text"] == "only child"  # no parent -> child payload
    assert fake.calls["retrieve"]["ids"] == ["p1"]  # one batched retrieve
    conds = _conditions(fake.calls["scroll"]["scroll_filter"])
    assert conds["document_id"].match.any == ["d1", "d2"]
    assert conds["chunk_index"].match.value == 0


def test_lead_parents_retrieve_failure_degrades_to_children(monkeypatch):
    children = [_point(id="c1", payload={"document_id": "d1", "parent_chunk_id": "p1",
                                         "chunk_text": "child 1"})]
    fake = _FakeClient(scroll_points=children)

    def boom_retrieve(**kw):
        raise RuntimeError("retrieve down")

    fake.retrieve = boom_retrieve
    monkeypatch.setattr(sr, "get_qdrant_client", lambda: fake)

    out = sr.lead_parents(["d1"])
    assert out["d1"]["chunk_text"] == "child 1"


def test_lead_parents_scroll_failure_returns_empty(monkeypatch):
    fake = _FakeClient()

    def boom_scroll(**kw):
        raise RuntimeError("scroll down")

    fake.scroll = boom_scroll
    monkeypatch.setattr(sr, "get_qdrant_client", lambda: fake)
    assert sr.lead_parents(["d1"]) == {}


def test_lead_parents_empty_ids_skip_qdrant(monkeypatch):
    def no_client():
        raise AssertionError("client must not be created")

    monkeypatch.setattr(sr, "get_qdrant_client", no_client)
    assert sr.lead_parents([]) == {}
