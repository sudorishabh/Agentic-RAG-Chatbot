"""Paging the Drupal crawl must return every record exactly once.

Thousands of records carry one identical ``changed`` value from the 2017 site
migration. Offset pagination over a sort that cannot break those ties has no
defined order among them, and the order the backend settles on differs between
page requests — so records drift across page boundaries and the walk silently
returns some twice and others never. Measured against the live JSON:API, a
plain ``changed`` sort never returned 137 of 1,167 completed_projects while
returning 126 others twice.

The resource below reproduces that: it re-orders each group of tied records on
every request. ``test_the_fake_still_loses_records_without_a_tie_breaker`` keeps
the fixture honest — a stub that quietly became stable would let the two
completeness tests pass for the wrong reason.

No network: the resource, its paging and its tie ordering are all local.
"""

from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qsl, urlencode, urlparse

import pytest

from app.ingestion.extractors import drupal_extractor as de

BASE = "https://example.org/jsonapi"
BUNDLE = "completed_projects"
URL = f"{BASE}/node/{BUNDLE}"
PAGE_SIZE = 10

# Most of the corpus shares the migration timestamp, the rest are distinct.
# Sized so the tie group spans every page boundary — one page of untied records
# would hide the bug entirely.
MIGRATED = "2017-12-28T08:23:11+00:00"
TIED = 24
DISTINCT = 6


def _corpus(id_field: str = "drupal_internal__nid") -> list[dict]:
    def node(index: int, changed: str) -> dict:
        return {
            "id": f"uuid-{index:03d}",
            "type": f"node--{BUNDLE}",
            "attributes": {id_field: index, "title": f"Record {index}", "changed": changed},
        }

    tied = [node(i, MIGRATED) for i in range(TIED)]
    distinct = [
        node(TIED + i, f"2026-08-{i + 1:02d}T00:00:00+00:00") for i in range(DISTINCT)
    ]
    return tied + distinct


class _Resource:
    """A paging JSON:API collection that orders tied records differently on
    every request, the way an unindexed tie-break does in practice."""

    def __init__(self, nodes: list[dict], page_size: int = PAGE_SIZE) -> None:
        self.nodes = nodes
        self.page_size = page_size
        self.requests = 0

    def _order(self, fields: list[str], descending: bool) -> list[dict]:
        self.requests += 1

        def key(node: dict) -> tuple:
            return tuple(node["attributes"].get(f) for f in fields)

        ordered = sorted(self.nodes, key=key, reverse=descending)

        # Rotate each tie group by the request number, so two pages of the same
        # walk disagree about which tied record comes first.
        out: list[dict] = []
        start = 0
        while start < len(ordered):
            end = start
            while end < len(ordered) and key(ordered[end]) == key(ordered[start]):
                end += 1
            group = ordered[start:end]
            if len(group) > 1:
                shift = self.requests % len(group)
                group = group[shift:] + group[:shift]
            out.extend(group)
            start = end
        return out

    def page(self, query: dict[str, str]) -> dict:
        sort = query.get("sort", "")
        fields = [f.lstrip("-") for f in sort.split(",") if f]
        ordered = self._order(fields, sort.startswith("-")) if fields else list(self.nodes)

        limit = int(query.get("page[limit]", self.page_size))
        offset = int(query.get("page[offset]", 0))

        links: dict = {}
        if offset + limit < len(ordered):
            following = dict(query, **{"page[offset]": offset + limit})
            links["next"] = {"href": f"{URL}?{urlencode(following)}"}
        return {"data": ordered[offset : offset + limit], "links": links}


class _Session:
    """Serves the resource. Paging follows ``links.next``, which carries the
    query in the URL, so params arrive either way round."""

    def __init__(self, resource: _Resource) -> None:
        self.resource = resource

    def get(self, url, params=None, timeout=None):
        query = dict(parse_qsl(urlparse(url).query))
        query.update({k: str(v) for k, v in (params or {}).items()})
        page = self.resource.page(query)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: page)

    def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def _drupal_settings(monkeypatch):
    monkeypatch.setattr(
        de,
        "get_settings",
        lambda: SimpleNamespace(
            drupal_jsonapi_base=BASE,
            drupal_page_size=PAGE_SIZE,
            drupal_request_timeout=30,
            drupal_ingest_external_pdfs=False,
        ),
    )
    # The include-field probe is a separate request against the live resource,
    # and not what these tests are about.
    monkeypatch.setattr(de, "_discover_relationship_fields", lambda *a, **k: [])


def _walk(resource: _Resource, *, ascending: bool, entity_type: str = "node") -> list[str]:
    return [
        record.uuid
        for record in de.iter_bundle_records(
            _Session(resource), BUNDLE, entity_type=entity_type, ascending=ascending
        )
    ]


def _assert_exactly_once(walked: list[str], nodes: list[dict]) -> None:
    expected = [n["id"] for n in nodes]
    duplicated = sorted({u for u in walked if walked.count(u) > 1})
    missing = sorted(set(expected) - set(walked))

    assert not duplicated, f"returned on more than one page: {duplicated}"
    assert not missing, f"never returned by the walk: {missing}"
    assert sorted(walked) == sorted(expected)


# --------------------------------------------------------------------------- #
# Every record, exactly once, in both directions.
# --------------------------------------------------------------------------- #

def test_ascending_walk_returns_every_record_exactly_once():
    resource = _Resource(_corpus())
    _assert_exactly_once(_walk(resource, ascending=True), resource.nodes)
    assert resource.requests > 1, "the corpus must span more than one page"


def test_descending_walk_returns_every_record_exactly_once():
    resource = _Resource(_corpus())
    _assert_exactly_once(_walk(resource, ascending=False), resource.nodes)


def test_a_block_content_walk_is_exhaustive_too():
    """Blocks number their serial id differently, and the tie-break has to name
    the field the resource actually has or the sort is rejected outright."""
    resource = _Resource(_corpus(id_field="drupal_internal__id"))
    walked = _walk(resource, ascending=True, entity_type="block_content")
    _assert_exactly_once(walked, resource.nodes)


# --------------------------------------------------------------------------- #
# The fixture has to be able to catch the bug it was written for.
# --------------------------------------------------------------------------- #

def test_the_fake_still_loses_records_without_a_tie_breaker(monkeypatch):
    """The same walk under the old sort: records duplicated, records skipped."""
    monkeypatch.setattr(de, "_sort_key", lambda entity_type, *, ascending: "changed")
    resource = _Resource(_corpus())

    walked = _walk(resource, ascending=True)
    expected = {n["id"] for n in resource.nodes}

    assert len(walked) != len(set(walked)), "expected an untied sort to duplicate records"
    assert expected - set(walked), "expected an untied sort to skip records"


# --------------------------------------------------------------------------- #
# The tie-breaker names a field the resource has.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "entity_type, ascending, expected",
    [
        ("node", True, "changed,drupal_internal__nid"),
        ("node", False, "-changed,-drupal_internal__nid"),
        ("block_content", True, "changed,drupal_internal__id"),
        ("block_content", False, "-changed,-drupal_internal__id"),
        ("taxonomy_term", True, "changed,drupal_internal__tid"),
        ("taxonomy_term", False, "-changed,-drupal_internal__tid"),
        # Unknown entity: a sort field the resource does not have answers 400,
        # and the crawl logs that as a skipped bundle — worse than the ties.
        ("unrecognised", True, "changed"),
        ("unrecognised", False, "-changed"),
    ],
)
def test_sort_key_names_the_field_the_resource_has(entity_type, ascending, expected):
    assert de._sort_key(entity_type, ascending=ascending) == expected
