"""A dry run decides everything a real reconciliation decides, and acts on none of it.

It runs the same crawl, the same enumeration, the same completeness guard, the
same per-candidate bundle-move confirmation and the same query that works out
which attachments an eviction would orphan — then stops, because nothing is ever
handed to `_handle`, and `_handle` is where every write lives.

The tests below hold both halves: that the report matches what a real run would
actually do, and that running it leaves the catalog, the index, the retry markers
and the high-water mark exactly as they were. Every write seam is wired to a spy
that fails the test if it is called.

No MySQL, no Qdrant, no HTTP.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.catalog.models import StateRecord
from app.ingestion import pipeline
from app.ingestion.change_detection import ChangeStatus, drupal
from app.ingestion.extractors import drupal_extractor as de


class _World:
    def __init__(self) -> None:
        self.live: dict[str, list[str]] = {}
        self.catalog: dict[str, StateRecord] = {}
        self.points: set[str] = set()
        self.links: set[tuple[str, str]] = set()      # (file_uuid, parent)
        self.writes: list[str] = []                   # anything that mutates state
        self.enumeration_empty = False

    # --- setup ------------------------------------------------------------- #

    def page(self, bundle: str, uuid: str, *attachments: str, live: bool = True) -> None:
        self.catalog[uuid] = StateRecord(
            document_id=uuid, source_type="website", source_key=f"/{uuid}",
            fingerprint="2026-08-02T00:00:00+00:00", content_hash="h", doc_version=1,
            bundle=bundle, entity_type="node", changed_mark=1785000000,
        )
        self.points.add(uuid)
        if live:
            self.live.setdefault(bundle, []).append(uuid)
        for attachment in attachments:
            self.catalog[attachment] = StateRecord(
                document_id=attachment, source_type="pdf_attachment",
                source_key=f"/{attachment}.pdf", fingerprint="fp", content_hash="h",
                doc_version=1, bundle=bundle,
            )
            self.points.add(attachment)
            self.links.add((attachment, uuid))

    def publish_only(self, bundle: str, uuid: str) -> None:
        """Live on the site but not catalogued — e.g. a document that moved here."""
        self.live.setdefault(bundle, []).append(uuid)

    # --- the read side the dry run uses ------------------------------------ #

    def live_in(self, bundle: str) -> list[str]:
        return [] if self.enumeration_empty else list(self.live.get(bundle, []))

    def attachment_ids_for(self, document_id: str) -> list[str]:
        return sorted(f for f, parent in self.links if parent == document_id)

    def orphaned_attachments(self, file_uuids, *, ignoring_parents=()) -> list[str]:
        gone = set(ignoring_parents)
        keeps = {f for f, parent in self.links if parent not in gone}
        return [
            f for f in dict.fromkeys(file_uuids)
            if f not in keeps
            and getattr(self.catalog.get(f), "source_type", None) == "pdf_attachment"
        ]


@pytest.fixture
def world(monkeypatch):
    site = _World()
    settings = SimpleNamespace(
        drupal_max_retries=1, drupal_block_min_chars=200,
        ingest_reconcile_max_missing_ratio=0.10, ingest_reconcile_min_deletions=2,
        ingest_max_docs_per_run=0, ingest_batch_size=0, ingest_batch_pause_seconds=0.0,
        ingest_workers=1, enrichment_enabled=False,
    )
    site.settings = settings

    monkeypatch.setattr(drupal, "get_settings", lambda: settings)
    monkeypatch.setattr(
        drupal.state, "load",
        lambda source_type: {
            k: v for k, v in site.catalog.items() if v.source_type == source_type
        } if source_type in ("website", "pdf_attachment") else {},
    )
    monkeypatch.setattr(drupal.state, "get", lambda uuid: site.catalog.get(uuid))
    monkeypatch.setattr(drupal.dead_links, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.dead_links, "load", dict)
    monkeypatch.setattr(drupal.retries, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.retries, "floors", dict)
    monkeypatch.setattr(de, "_build_session", lambda retries: SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(
        de, "iter_bundle_records",
        lambda s, b, **kw: iter([
            SimpleNamespace(
                uuid=u, bundle=b, changed="2026-08-02T00:00:00+00:00", source=f"/{u}",
                body="Body text, long enough to survive the filter.", files=[],
            )
            for u in site.live_in(b)
        ]),
    )
    monkeypatch.setattr(de, "iter_node_uuids", lambda s, b, **kw: iter(site.live_in(b)))

    monkeypatch.setattr(pipeline.state, "attachment_ids_for", site.attachment_ids_for)
    monkeypatch.setattr(pipeline.state, "orphaned_attachments", site.orphaned_attachments)

    # Every seam that changes persistent state fails the test if it is reached.
    def forbidden(name):
        def _spy(*args, **kwargs):
            site.writes.append(name)
            raise AssertionError(f"a dry run must not call {name}")
        return _spy

    monkeypatch.setattr(pipeline, "delete_document", forbidden("delete_document"))
    monkeypatch.setattr(pipeline.state, "delete", forbidden("state.delete"))
    monkeypatch.setattr(pipeline.state, "upsert", forbidden("state.upsert"))
    monkeypatch.setattr(pipeline, "_save_state", forbidden("_save_state"))
    monkeypatch.setattr(pipeline, "_log", forbidden("ingest_log.record"))
    monkeypatch.setattr(pipeline.retries, "record", forbidden("retries.record"))
    monkeypatch.setattr(pipeline.retries, "clear", forbidden("retries.clear"))
    monkeypatch.setattr(pipeline, "index_chunks", forbidden("index_chunks"))
    return site


def _dry_run(world, bundles):
    return pipeline.reconcile_dry_run(bundles)


# --------------------------------------------------------------------------- #
# What it reports.
# --------------------------------------------------------------------------- #

def test_a_missing_document_is_reported(world):
    world.page("news", "n-1")
    world.page("news", "n-2")
    world.page("news", "gone", live=False)

    report = _dry_run(world, ["news"])

    assert [d["document_id"] for d in report["documents"]] == ["gone"]
    assert report["by_bundle"] == {"news": 1}
    assert report["dry_run"] is True


def test_an_unsafe_bundle_yields_no_candidates(world):
    for i in range(20):
        world.page("news", f"n-{i}")
    world.enumeration_empty = True

    report = _dry_run(world, ["news"])

    assert report["documents"] == []
    assert report["attachments"] == []


def test_a_bundle_move_is_not_reported_as_a_deletion(world):
    world.page("news", "n-1")
    world.page("news", "n-2")
    world.page("news", "mover", live=False)      # catalogued under news…
    world.page("events", "e-1")
    world.page("events", "e-2")
    world.publish_only("events", "mover")        # …but live under events

    report = _dry_run(world, ["news", "events"])

    assert report["documents"] == [], "a move is not a deletion"
    assert report["moved"] == [
        {"document_id": "mover", "from_bundle": "news", "to_bundle": "events"}
    ]


def test_an_attachment_that_would_be_orphaned_is_reported(world):
    world.page("news", "n-1")
    world.page("news", "n-2")
    world.page("news", "gone", "pdf-only", live=False)

    report = _dry_run(world, ["news"])

    assert report["attachments"] == ["pdf-only"]
    assert report["linked_attachments_surviving"] == 0


def test_a_shared_attachment_is_not_reported(world):
    world.page("news", "n-1")
    world.page("news", "n-2")
    world.page("news", "gone", "pdf-shared", live=False)
    world.page("news", "keeper")                 # a live page holding the same PDF
    world.links.add(("pdf-shared", "keeper"))

    report = _dry_run(world, ["news"])

    assert [d["document_id"] for d in report["documents"]] == ["gone"]
    assert report["attachments"] == [], "another page still claims it"
    assert report["linked_attachments_surviving"] == 1


# --------------------------------------------------------------------------- #
# What it must not touch. The fixture makes every write seam raise, so these
# pass only if the dry run never reaches one.
# --------------------------------------------------------------------------- #

def test_a_dry_run_writes_nothing_at_all(world):
    world.page("news", "n-1")
    world.page("news", "n-2")
    world.page("news", "gone", "pdf-only", live=False)
    before_catalog = dict(world.catalog)
    before_points = set(world.points)
    before_links = set(world.links)

    report = _dry_run(world, ["news"])

    assert report["documents"], "the fixture must produce something to delete"
    assert world.writes == [], "no write seam was reached"
    assert world.catalog == before_catalog, "no catalog write"
    assert world.points == before_points, "no Qdrant deletion"
    assert world.links == before_links


def test_a_dry_run_leaves_retry_markers_and_the_high_water_mark_alone(world):
    """The mark is derived from `changed_mark` on catalog rows, so an untouched
    catalog is an untouched cursor; the retry seams raise if reached."""
    world.page("news", "n-1")
    world.page("news", "gone", live=False)
    marks_before = {d: r.changed_mark for d, r in world.catalog.items()}

    _dry_run(world, ["news"])

    assert {d: r.changed_mark for d, r in world.catalog.items()} == marks_before
    assert world.writes == []


# --------------------------------------------------------------------------- #
# The report has to match what would really happen.
# --------------------------------------------------------------------------- #

def test_the_dry_run_and_the_real_run_agree_on_the_candidates(world, monkeypatch):
    """Same fixture, same decisions: whatever the dry run lists is exactly what
    reconciliation emits when it is allowed to act."""
    world.page("news", "n-1")
    world.page("news", "n-2")
    world.page("news", "gone-1", live=False)
    world.page("news", "gone-2", live=False)

    report = _dry_run(world, ["news"])
    dry = sorted(d["document_id"] for d in report["documents"])

    emitted = sorted(
        r.document_id
        for r in drupal.detect_drupal_changes(bundles=["news"], reconcile_deletes=True)
        if r.status is ChangeStatus.DELETED
    )

    assert dry == emitted == ["gone-1", "gone-2"]


def test_the_dry_run_agrees_when_the_guard_refuses_too(world):
    for i in range(20):
        world.page("news", f"n-{i}")
    world.enumeration_empty = True

    report = _dry_run(world, ["news"])
    emitted = [
        r.document_id
        for r in drupal.detect_drupal_changes(bundles=["news"], reconcile_deletes=True)
        if r.status is ChangeStatus.DELETED
    ]

    assert [d["document_id"] for d in report["documents"]] == emitted == []


def test_the_report_is_marked_as_a_dry_run(world, caplog):
    import logging

    world.page("news", "n-1")
    world.page("news", "gone", live=False)

    with caplog.at_level(logging.WARNING):
        _dry_run(world, ["news"])

    assert "DRY RUN" in caplog.text
    assert "nothing was deleted" in caplog.text
