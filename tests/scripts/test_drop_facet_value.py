"""scripts.drop_facet_value: payload-only removal of one stale facet value.

The audited case: ``categories = ['Transport', 'True']`` on 5,598 points. The
script must drop exactly the stale value, keep every other category in order,
delete the key rather than write an empty list, and touch nothing else.
"""
from __future__ import annotations

from types import SimpleNamespace

from scripts import drop_facet_value as dfv


def test_only_the_stale_value_is_removed_and_order_is_kept():
    assert dfv.without_value(["Transport", "True"], "True") == ["Transport"]
    assert dfv.without_value(["True", "Marine and Coastal", "True"], "True") == ["Marine and Coastal"]
    assert dfv.without_value(["True"], "True") == []
    assert dfv.without_value(None, "True") == []
    # A legitimate value that merely contains the text is untouched.
    assert dfv.without_value(["True North Initiative", "True"], "True") == ["True North Initiative"]


class _FakeClient:
    """Enough of QdrantClient for plan()/apply(): one scroll page, recorded writes."""

    def __init__(self, points):
        self._points = points
        self.set_calls: list[dict] = []
        self.delete_calls: list[dict] = []

    def scroll(self, *, collection_name, scroll_filter, limit, with_payload, with_vectors, offset):
        assert with_vectors is False
        return list(self._points), None

    def set_payload(self, *, collection_name, payload, points):
        self.set_calls.append({"payload": payload, "points": list(points)})

    def delete_payload(self, *, collection_name, keys, points):
        self.delete_calls.append({"keys": keys, "points": list(points)})


def _point(pid, categories):
    return SimpleNamespace(id=pid, payload={"document_id": "d", "categories": categories})


def test_plan_groups_points_by_their_resulting_list():
    client = _FakeClient([
        _point("p1", ["Transport", "True"]),
        _point("p2", ["Transport", "True"]),
        _point("p3", ["Marine and Coastal", "True"]),
        _point("p4", ["True"]),
    ])
    groups = dfv.plan(client, "documents", "categories", "True")
    assert groups[("Transport",)] == ["p1", "p2"]
    assert groups[("Marine and Coastal",)] == ["p3"]
    assert groups[()] == ["p4"]


def test_apply_rewrites_the_list_and_deletes_the_key_when_empty():
    client = _FakeClient([])
    groups = {("Transport",): ["p1", "p2"], (): ["p4"]}
    written = dfv.apply(client, "documents", "categories", groups)
    assert written == 3
    assert client.set_calls == [{"payload": {"categories": ["Transport"]}, "points": ["p1", "p2"]}]
    assert client.delete_calls == [{"keys": ["categories"], "points": ["p4"]}]


def test_apply_never_writes_any_other_payload_key():
    client = _FakeClient([])
    dfv.apply(client, "documents", "categories", {("Transport",): ["p1"]})
    assert all(set(call["payload"]) == {"categories"} for call in client.set_calls)
