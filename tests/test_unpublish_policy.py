"""The searchable index holds what the site currently publishes.

Unpublishing is not a separate signal the crawl could read. This site's JSON:API
serves an anonymous client only published content — `filter[status]=0` returns
nothing, and an unfiltered walk returns exactly the published set — so an
unpublished document is simply absent from the enumeration, indistinguishable
from one that was deleted. Both therefore leave the index, which is the intended
policy.

What must NOT happen is treating that as permanent. Nothing records the document
as gone-for-good: its catalog row is removed and its retry marker cleared, so
republishing brings it back through the ordinary crawl as a new document. These
tests hold that round trip, and hold it against the completeness guard, so a
failed fetch can never be mistaken for a site-wide unpublish.

Catalog, index and JSON:API are all in memory here.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.catalog.models import StateRecord
from app.ingestion import pipeline
from app.ingestion.change_detection import ChangeStatus, drupal
from app.ingestion.extractors import drupal_extractor as de

BUNDLE = "news"


class _Site:
    """A Drupal bundle, the catalog built from it, and the index behind that."""

    def __init__(self) -> None:
        self.published: dict[str, list[str]] = {}
        self.catalog: dict[str, StateRecord] = {}
        self.points: set[str] = set()
        self.enumeration_fails = False
        self.enumeration_empty = False

    # --- the site ---------------------------------------------------------- #

    def publish(self, *document_ids: str, bundle: str = BUNDLE) -> None:
        live = self.published.setdefault(bundle, [])
        live.extend(d for d in document_ids if d not in live)

    def unpublish(self, *document_ids: str, bundle: str = BUNDLE) -> None:
        """Exactly what the API does: the document stops being returned."""
        self.published[bundle] = [
            d for d in self.published.get(bundle, []) if d not in document_ids
        ]

    def live(self, bundle: str) -> list[str]:
        if self.enumeration_fails:
            raise RuntimeError("site unreachable")
        return [] if self.enumeration_empty else list(self.published.get(bundle, []))

    # --- the catalog it produces ------------------------------------------- #

    def index(self, document_id: str, bundle: str = BUNDLE) -> None:
        self.catalog[document_id] = StateRecord(
            document_id=document_id, source_type="website",
            source_key=f"https://teriin.org/{document_id}",
            fingerprint="2026-08-01T00:00:00+00:00", content_hash="h", doc_version=1,
            bundle=bundle, entity_type="node", changed_mark=1785000000,
        )
        self.points.add(document_id)

    def searchable(self) -> set[str]:
        return {d for d in self.catalog if d in self.points}


@pytest.fixture
def site(monkeypatch):
    world = _Site()
    settings = SimpleNamespace(
        drupal_max_retries=1, drupal_block_min_chars=200,
        ingest_reconcile_max_missing_ratio=0.10, ingest_reconcile_min_deletions=2,
    )
    world.settings = settings

    monkeypatch.setattr(drupal, "get_settings", lambda: settings)
    monkeypatch.setattr(
        drupal.state, "load",
        lambda source_type: (dict(world.catalog) if source_type == "website" else {}),
    )
    monkeypatch.setattr(drupal.dead_links, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.dead_links, "load", dict)
    monkeypatch.setattr(drupal.retries, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.retries, "floors", dict)
    monkeypatch.setattr(de, "_build_session", lambda retries: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(
        de, "iter_bundle_records",
        lambda s, b, **kw: iter([
            SimpleNamespace(
                uuid=d, bundle=b, changed="2026-08-01T00:00:00+00:00",
                source=f"https://teriin.org/{d}", body="Body text, long enough.", files=[],
            )
            for d in world.live(b)
        ]),
    )
    monkeypatch.setattr(de, "iter_node_uuids", lambda s, b, **kw: iter(world.live(b)))

    # The delete half of the pipeline, applied to the same in-memory world.
    monkeypatch.setattr(pipeline, "delete_document", lambda doc_id, keep_ids=None: world.points.discard(doc_id))
    monkeypatch.setattr(pipeline.state, "delete", lambda ids: [world.catalog.pop(i, None) for i in ids])
    monkeypatch.setattr(pipeline.state, "attachment_ids_for", lambda doc_id: [])
    monkeypatch.setattr(pipeline, "_log", lambda *a, **k: None)
    return world


def _crawl(site) -> list:
    return list(drupal.detect_drupal_changes(bundles=[BUNDLE], reconcile_deletes=True))


def _reconcile(site) -> list[str]:
    """Crawl and apply every deletion it decides on. Returns what was removed."""
    removed = []
    for record in _crawl(site):
        if record.status is ChangeStatus.DELETED:
            pipeline._handle(record, build_doc=lambda r: None)
            removed.append(record.document_id)
    return removed


# --------------------------------------------------------------------------- #
# Published content stays; unpublished content goes.
# --------------------------------------------------------------------------- #

def test_published_documents_stay_searchable(site):
    site.publish("n-1", "n-2", "n-3")
    for doc in ("n-1", "n-2", "n-3"):
        site.index(doc)

    assert _reconcile(site) == []
    assert site.searchable() == {"n-1", "n-2", "n-3"}


def test_an_unpublished_document_leaves_the_index(site):
    site.publish("n-1", "n-2", "n-3")
    for doc in ("n-1", "n-2", "n-3"):
        site.index(doc)

    site.unpublish("n-2")

    assert _reconcile(site) == ["n-2"]
    assert site.searchable() == {"n-1", "n-3"}
    assert "n-2" not in site.catalog, "its catalog row goes too"
    assert "n-2" not in site.points, "and its vectors"


def test_unpublishing_one_document_leaves_the_rest_alone(site):
    site.publish(*[f"n-{i}" for i in range(20)])
    for i in range(20):
        site.index(f"n-{i}")

    site.unpublish("n-7")

    assert _reconcile(site) == ["n-7"]
    assert len(site.searchable()) == 19


# --------------------------------------------------------------------------- #
# Removal is not permanent.
# --------------------------------------------------------------------------- #

def test_a_republished_document_is_crawled_again_as_new(site):
    site.publish("n-1", "n-2")
    site.index("n-1")
    site.index("n-2")

    site.unpublish("n-2")
    assert _reconcile(site) == ["n-2"]

    site.publish("n-2")                       # the editor puts it back
    statuses = {r.document_id: r.status for r in _crawl(site)}

    assert statuses["n-2"] is ChangeStatus.NEW, (
        "nothing may record it as permanently deleted; it must ingest afresh"
    )
    assert statuses["n-1"] is ChangeStatus.UNCHANGED, "its neighbour is untouched"


def test_a_republished_document_can_be_indexed_and_stays(site):
    site.publish("n-1", "n-2", "n-3")
    for doc in ("n-1", "n-2", "n-3"):
        site.index(doc)

    site.unpublish("n-1")
    _reconcile(site)
    assert site.searchable() == {"n-2", "n-3"}

    site.publish("n-1")
    site.index("n-1")                          # the crawl re-ingests it

    assert _reconcile(site) == [], "it is live again, so nothing deletes it"
    assert site.searchable() == {"n-1", "n-2", "n-3"}


def test_a_bundle_cannot_be_emptied_by_unpublishing_its_last_document(site):
    """The guard owns this case, and it wins: a bundle whose live set goes to
    zero is a broken fetch as far as reconciliation can tell, so the document
    stays until someone confirms it."""
    site.publish("n-1")
    site.index("n-1")

    site.unpublish("n-1")

    assert _reconcile(site) == []
    assert site.searchable() == {"n-1"}


# --------------------------------------------------------------------------- #
# A failure must never read as a mass unpublish.
# --------------------------------------------------------------------------- #

def test_an_unreachable_site_deletes_nothing(site):
    site.publish(*[f"n-{i}" for i in range(100)])
    for i in range(100):
        site.index(f"n-{i}")

    site.enumeration_fails = True

    assert _reconcile(site) == []
    assert len(site.searchable()) == 100


def test_an_empty_response_is_not_a_site_wide_unpublish(site):
    """The completeness guard still owns this: everything vanishing at once is a
    broken fetch, not an editorial decision."""
    site.publish(*[f"n-{i}" for i in range(100)])
    for i in range(100):
        site.index(f"n-{i}")

    site.enumeration_empty = True

    assert _reconcile(site) == []
    assert len(site.searchable()) == 100


def test_a_bulk_unpublish_beyond_the_threshold_is_held_back(site):
    """A real bulk unpublish looks exactly like a truncated response, so it is
    refused too — deliberately. Raising the threshold is the way through."""
    site.publish(*[f"n-{i}" for i in range(100)])
    for i in range(100):
        site.index(f"n-{i}")

    site.unpublish(*[f"n-{i}" for i in range(20)])

    assert _reconcile(site) == [], "20% at once is held for a human"
    assert len(site.searchable()) == 100

    site.settings.ingest_reconcile_max_missing_ratio = 0.50
    assert len(_reconcile(site)) == 20, "once confirmed, it goes through"
    assert len(site.searchable()) == 80
