"""Reconciliation must not delete real documents on a short live enumeration.

Deletes are inferred from absence, so an enumeration that merely came back
incomplete is indistinguishable from a bundle that was genuinely emptied — and
what follows is not reversible: points, catalog row and every facet row hanging
off it, with nothing to restore from. A fetch that *fails* already skips the
bundle; these tests cover the responses that arrive successfully and short.

Two halves. The first drives the real reconcile path with the catalog and the
live set set independently, and asserts on the DELETED records it emits. The
second pins the enumeration itself as deterministic and exhaustive, since every
guarantee here rests on that walk returning everything.

All in memory: no MySQL, no Qdrant, no HTTP.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from app.catalog.models import StateRecord
from app.ingestion.change_detection import ChangeStatus, drupal
from app.ingestion.extractors import drupal_extractor as de

BUNDLE = "news"
OTHER = "events"


def _row(uuid: str, bundle: str) -> StateRecord:
    return StateRecord(
        document_id=uuid, source_type="website",
        source_key=f"https://teriin.org/{uuid}", fingerprint="2026-08-01T00:00:00+00:00",
        content_hash="h", doc_version=1, bundle=bundle, entity_type="node",
        changed_mark=1785000000,
    )


def _node(uuid: str, bundle: str) -> SimpleNamespace:
    return SimpleNamespace(
        uuid=uuid, bundle=bundle, changed="2026-08-01T00:00:00+00:00",
        source=f"https://teriin.org/{uuid}",
        body="A node with enough body text to survive the block filter.", files=[],
    )


def _ids(prefix: str, n: int) -> list[str]:
    return [f"{prefix}-{i:04d}" for i in range(n)]


@pytest.fixture
def site(monkeypatch):
    """A crawl whose catalog and live enumeration are set independently."""
    state: dict = {"catalog": {}, "live": {}, "enumeration_error": False}
    settings = SimpleNamespace(
        drupal_max_retries=1,
        drupal_block_min_chars=200,
        ingest_reconcile_max_missing_ratio=0.10,
        ingest_reconcile_min_deletions=2,
    )
    state["settings"] = settings

    monkeypatch.setattr(drupal, "get_settings", lambda: settings)
    monkeypatch.setattr(
        drupal.state, "load",
        lambda source_type: (dict(state["catalog"]) if source_type == "website" else {}),
    )
    # Each delete candidate is confirmed against the catalog as it stands now,
    # to tell a document that moved bundles from one that is gone. See
    # tests/test_bundle_moves.py.
    monkeypatch.setattr(drupal.state, "get", lambda uuid: state["catalog"].get(uuid))
    monkeypatch.setattr(drupal.dead_links, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.dead_links, "load", dict)
    monkeypatch.setattr(drupal.retries, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.retries, "floors", dict)
    monkeypatch.setattr(de, "_build_session", lambda retries: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(
        de, "iter_bundle_records",
        lambda s, b, **kw: iter([_node(u, b) for u in state["live"].get(b, [])]),
    )

    def iter_node_uuids(session, bundle, **kw):
        if state["enumeration_error"]:
            raise RuntimeError("site down")
        return iter(state["live"].get(bundle, []))

    monkeypatch.setattr(de, "iter_node_uuids", iter_node_uuids)
    return state


def _reconcile(site, *, catalogued: int, live: int, bundle: str = BUNDLE) -> list[str]:
    """Catalogue `catalogued` documents, present `live` of them, return deletes."""
    ids = _ids(bundle, catalogued)
    site["catalog"].update({u: _row(u, bundle) for u in ids})
    site["live"][bundle] = ids[:live]
    records = list(drupal.detect_drupal_changes(bundles=[bundle], reconcile_deletes=True))
    return [r.document_id for r in records if r.status is ChangeStatus.DELETED]


# --------------------------------------------------------------------------- #
# A complete enumeration is believed; a short one is not.
# --------------------------------------------------------------------------- #

def test_a_complete_enumeration_reconciles(site, caplog):
    with caplog.at_level(logging.WARNING):
        assert _reconcile(site, catalogued=100, live=100) == []
    assert "Refusing to reconcile" not in caplog.text


def test_one_missing_document_is_deleted(site, caplog):
    """The feature still has to work: a single genuine deletion goes through."""
    with caplog.at_level(logging.WARNING):
        deleted = _reconcile(site, catalogued=100, live=99)

    assert deleted == [f"{BUNDLE}-0099"]
    assert "Refusing to reconcile" not in caplog.text


def test_a_tenth_of_the_bundle_missing_is_refused(site):
    assert _reconcile(site, catalogued=100, live=90) == []


def test_an_empty_enumeration_is_refused(site):
    assert _reconcile(site, catalogued=100, live=0) == []


def test_a_large_bundle_going_empty_deletes_nothing(site):
    """The case that motivated all of this: one empty-but-successful response
    against the biggest bundle in the corpus."""
    assert _reconcile(site, catalogued=1634, live=0) == []


def test_an_enumeration_error_deletes_nothing(site):
    site["enumeration_error"] = True
    assert _reconcile(site, catalogued=100, live=50) == []


# --------------------------------------------------------------------------- #
# A small bundle can still lose a document.
# --------------------------------------------------------------------------- #

def test_a_small_bundle_can_still_lose_one_document(site):
    """8 documents losing 1 is 12.5% — over the ratio, under the absolute
    allowance. Without that allowance no small bundle could ever reconcile."""
    assert _reconcile(site, catalogued=8, live=7) == [f"{BUNDLE}-0007"]


def test_a_small_bundle_losing_several_is_still_refused(site):
    assert _reconcile(site, catalogued=8, live=5) == []


# --------------------------------------------------------------------------- #
# One bad bundle must not cost the others.
# --------------------------------------------------------------------------- #

def test_an_unsafe_bundle_does_not_block_a_healthy_one(site):
    site["catalog"].update({u: _row(u, BUNDLE) for u in _ids(BUNDLE, 100)})
    site["live"][BUNDLE] = []                                   # unsafe
    site["catalog"].update({u: _row(u, OTHER) for u in _ids(OTHER, 100)})
    site["live"][OTHER] = _ids(OTHER, 99)                       # one real deletion

    records = list(
        drupal.detect_drupal_changes(bundles=[BUNDLE, OTHER], reconcile_deletes=True)
    )
    deleted = [r.document_id for r in records if r.status is ChangeStatus.DELETED]

    assert deleted == [f"{OTHER}-0099"], "the healthy bundle still reconciles"
    assert not any(d.startswith(BUNDLE) for d in deleted)


# --------------------------------------------------------------------------- #
# The threshold is a setting, not a constant.
# --------------------------------------------------------------------------- #

def test_raising_the_ratio_admits_a_drop_that_was_refused(site):
    site["settings"].ingest_reconcile_max_missing_ratio = 0.50
    assert len(_reconcile(site, catalogued=100, live=90)) == 10


def test_lowering_the_ratio_refuses_a_drop_that_was_allowed(site):
    site["settings"].ingest_reconcile_max_missing_ratio = 0.001
    site["settings"].ingest_reconcile_min_deletions = 0
    assert _reconcile(site, catalogued=100, live=99) == []


def test_the_absolute_allowance_is_configurable(site):
    site["settings"].ingest_reconcile_min_deletions = 5
    assert len(_reconcile(site, catalogued=8, live=5)) == 3


# --------------------------------------------------------------------------- #
# The refusal has to be readable by whoever finds it in a log.
# --------------------------------------------------------------------------- #

def test_the_refusal_names_the_bundle_and_the_numbers(site, caplog):
    with caplog.at_level(logging.WARNING):
        _reconcile(site, catalogued=100, live=90)

    message = caplog.text
    assert f"node/{BUNDLE}" in message, "which source"
    assert "Catalogued 100" in message and "live 90" in message, "the counts"
    assert "missing 10" in message
    assert "10.0%" in message, "the reason it tripped"
    assert "No documents were deleted" in message, "what happened as a result"


def test_an_empty_enumeration_says_so_plainly(site, caplog):
    with caplog.at_level(logging.WARNING):
        _reconcile(site, catalogued=100, live=0)

    assert "returned nothing at all" in caplog.text


# --------------------------------------------------------------------------- #
# The enumeration the whole guard rests on.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "entity_type, field",
    [
        ("node", "drupal_internal__nid"),
        ("block_content", "drupal_internal__id"),
        ("taxonomy_term", "drupal_internal__tid"),
    ],
)
def test_the_enumeration_sorts_on_the_entity_serial_id(monkeypatch, entity_type, field):
    """A unique key, so the ordering is total and paging cannot shuffle rows."""
    captured: dict = {}

    monkeypatch.setattr(
        de, "_iter_pages",
        lambda session, url, params, timeout: captured.update(params) or iter(()),
    )
    list(de.iter_node_uuids(None, "report", entity_type=entity_type))

    assert captured["sort"] == field
    assert captured[f"fields[{entity_type}--report]"] == field


def test_the_enumeration_carries_no_changed_window(monkeypatch):
    """Reconciliation needs the whole live set. An incremental filter here would
    read every document outside the window as deleted."""
    captured: dict = {}

    monkeypatch.setattr(
        de, "_iter_pages",
        lambda session, url, params, timeout: captured.update(params) or iter(()),
    )
    list(de.iter_node_uuids(None, "report"))

    assert not any("changed" in key for key in captured), captured
    assert captured["sort"] == "drupal_internal__nid"


def test_the_enumeration_returns_every_record_once_across_pages(monkeypatch):
    """The same tied-`changed` corpus that breaks a `changed` sort: ordering on
    the serial id leaves no ties to shuffle, so paging stays exhaustive."""
    nodes = [
        {"id": f"uuid-{i:03d}",
         "attributes": {"drupal_internal__nid": i, "changed": "2017-12-28T08:23:11+00:00"}}
        for i in range(30)
    ]
    page_size, requests_made = 10, {"n": 0}

    def iter_pages(session, url, params, timeout):
        field = params["sort"]
        ordered = sorted(nodes, key=lambda n: n["attributes"][field])
        for start in range(0, len(ordered), page_size):
            requests_made["n"] += 1
            yield ordered[start : start + page_size], {}

    monkeypatch.setattr(de, "_iter_pages", iter_pages)
    got = list(de.iter_node_uuids(None, "report"))

    assert requests_made["n"] == 3, "the corpus must span more than one page"
    assert len(got) == len(set(got)) == len(nodes)
    assert set(got) == {n["id"] for n in nodes}
