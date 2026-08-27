"""Documents that failed before retry markers existed must still come back.

A document that errored or was skipped in the early runs left no catalog row —
so it contributes no `changed_mark` and the incremental cursor sits above it —
and no retry marker, because the feature landed later. Ninety-one attachments
are in exactly that state, invisible to everything except the append-only log.

The repair reuses the existing floor: write ordinary retry markers, let the next
ordinary sweep do the work. The subtlety is *which* document each marker names —
see `test_an_attachment_is_recovered_through_the_page_that_links_it`.

The catalog and the log are in memory; no MySQL.
"""

from __future__ import annotations

import pytest

from app.catalog.models import StateRecord
from app.ingestion import recovery
from app.ingestion.recovery import Stranded

PARENT_MARK = 1515666501
OLDER_MARK = 1509000000


class _Retries:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}

    def ensure_table(self) -> None:
        pass

    def record(self, document_id, *, source_type, bundle, changed_mark, outcome, error=None):
        self.items[document_id] = {
            "source_type": source_type, "bundle": bundle,
            "changed_mark": changed_mark, "outcome": outcome, "error": error,
        }

    def clear(self, document_ids) -> int:
        return sum(bool(self.items.pop(d, None)) for d in document_ids)

    def floors(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self.items.values():
            bundle, mark = item["bundle"], item["changed_mark"]
            if bundle is None or mark is None:
                continue
            out[bundle] = min(out.get(bundle, mark), mark)
        return out


@pytest.fixture
def world(monkeypatch):
    """Scripted `stranded()` output plus in-memory catalog and retry tables."""
    import app.catalog.retries as retries_module
    import app.catalog.state as state_module

    state = {
        "n-parent": StateRecord(
            document_id="n-parent", source_type="website",
            source_key="https://teriin.org/parent", fingerprint="f",
            bundle="news", changed_mark=PARENT_MARK,
        ),
        "n-older": StateRecord(
            document_id="n-older", source_type="website",
            source_key="https://teriin.org/older", fingerprint="f",
            bundle="news", changed_mark=OLDER_MARK,
        ),
    }
    retries = _Retries()
    monkeypatch.setattr(state_module, "get", state.get)
    for attribute in ("ensure_table", "record", "clear", "floors"):
        monkeypatch.setattr(retries_module, attribute, getattr(retries, attribute))

    holder = {"retries": retries, "state": state}

    def use(items: list[Stranded]):
        monkeypatch.setattr(recovery, "stranded", lambda: items)
        return items

    holder["use"] = use
    return holder


def _attachment(document_id="inbody:abc", **kwargs) -> Stranded:
    defaults = dict(
        document_id=document_id,
        source_type="pdf_attachment",
        status="skipped",
        source_url="https://teriin.org/files/Receipts_&amp;_Payments.pdf",
        parent_id="n-parent",
        bundle="news",
        changed_mark=PARENT_MARK,
    )
    defaults.update(kwargs)
    return Stranded(**defaults)


# --------------------------------------------------------------------------- #
# Which document the marker names.
# --------------------------------------------------------------------------- #

def test_an_attachment_is_recovered_through_the_page_that_links_it(world):
    """A marker on the attachment's own id would never resolve.

    Most of these are in-body PDFs whose id is a hash of the URL, and most were
    stranded *because* that URL was malformed. Once the extractor decodes it the
    same link yields a different id — so the old id is never crawled again, the
    marker never clears, and its floor holds the bundle's window open forever.
    The parent's id is stable and re-yields whatever it links to today.
    """
    world["use"]([_attachment()])

    report = recovery.recover()

    assert list(report.markers) == ["n-parent"]
    assert "inbody:abc" not in world["retries"].items
    marker = world["retries"].items["n-parent"]
    assert marker["bundle"] == "news" and marker["changed_mark"] == PARENT_MARK


def test_the_marker_is_taken_from_the_catalogued_parent_not_the_log(world):
    """The log's bundle is whatever was written at the time; the catalog row is
    what the crawl actually compares against."""
    world["use"]([_attachment(bundle="stale-guess", changed_mark=1)])

    recovery.recover()

    marker = world["retries"].items["n-parent"]
    assert marker["bundle"] == "news"
    assert marker["changed_mark"] == PARENT_MARK
    assert marker["source_type"] == "website"


def test_several_attachments_on_one_page_share_one_marker(world):
    """91 stranded attachments resolve to 47 pages; one crawl recovers each
    page's whole set."""
    world["use"]([
        _attachment("inbody:a"), _attachment("inbody:b"), _attachment("inbody:c"),
    ])

    report = recovery.recover()

    assert len(world["retries"].items) == 1
    assert sorted(report.markers["n-parent"]) == ["inbody:a", "inbody:b", "inbody:c"]


def test_the_marker_says_what_it_is_for(world):
    world["use"]([_attachment("inbody:a"), _attachment("inbody:b")])

    recovery.recover()

    error = world["retries"].items["n-parent"]["error"]
    assert "recover 2 document(s)" in error
    assert "inbody:a" in error


def test_a_recovery_marker_is_not_an_error_marker(world):
    """The document did not fail this run; an operator triaging the queue needs
    to be able to tell a fresh failure from a historical one."""
    world["use"]([_attachment()])

    recovery.recover()

    assert world["retries"].items["n-parent"]["outcome"] == recovery.RECOVER_OUTCOME
    assert world["retries"].items["n-parent"]["outcome"] != "error"


# --------------------------------------------------------------------------- #
# What cannot be recovered, and how that is reported.
# --------------------------------------------------------------------------- #

def test_an_attachment_with_no_linking_page_is_reported_not_invented(world):
    """No parent, no bundle, nothing to crawl. The one thing that must not
    happen is a marker on a made-up id."""
    orphan = _attachment("inbody:lost", parent_id=None, bundle=None, changed_mark=None)
    world["use"]([orphan])

    report = recovery.recover()

    assert world["retries"].items == {}
    assert [s.document_id for s in report.unrecoverable] == ["inbody:lost"]
    assert "no linking page" in orphan.blocked


def test_a_node_with_a_bundle_but_no_position_is_marked_and_flagged(world):
    """It can be marked — its id is stable — but the marker cannot widen a
    window, so it returns only when its bundle is crawled in full. Saying so
    beats implying it will come back on the next sweep."""
    node = Stranded(
        document_id="n-failed", source_type="website", status="error",
        bundle="feature_articles", changed_mark=None,
    )
    world["use"]([node])

    report = recovery.recover()

    assert "n-failed" in world["retries"].items
    assert [s.document_id for s in report.unfloorable] == ["n-failed"]
    assert "cannot be widened" in node.blocked


def test_a_dry_run_writes_nothing(world):
    world["use"]([_attachment()])

    report = recovery.recover(dry_run=True)

    assert world["retries"].items == {}
    assert report.markers == {"n-parent": ["inbody:abc"]}, "but it still reports"


def test_the_earliest_parent_wins_when_a_file_hangs_off_several_pages(world):
    """The furthest-back position widens the window most, and one widened window
    reaches the later pages too."""
    from app.ingestion.recovery import _earlier

    late = _attachment(parent_id="n-parent", changed_mark=PARENT_MARK)
    early = _attachment(parent_id="n-older", changed_mark=OLDER_MARK)

    assert _earlier(early, late) is True
    assert _earlier(late, early) is False


def test_a_route_with_a_position_beats_one_without(world):
    from app.ingestion.recovery import _earlier

    positioned = _attachment(changed_mark=PARENT_MARK)
    unpositioned = _attachment(changed_mark=None)

    assert _earlier(positioned, unpositioned) is True
    assert _earlier(unpositioned, positioned) is False


# --------------------------------------------------------------------------- #
# The lifecycle: marker -> widened window -> re-ingest -> marker gone.
# --------------------------------------------------------------------------- #

def test_the_marker_widens_the_crawl_window_to_the_parent(world):
    world["use"]([_attachment()])

    recovery.recover()

    assert world["retries"].floors() == {"news": PARENT_MARK}


def test_a_successful_re_ingest_clears_the_marker(world, monkeypatch):
    """The floor lifts on its own — the parent resolves, its marker goes, and
    the bundle stops being scanned from 2018 on every sweep."""
    from app.ingestion import pipeline
    from app.ingestion.change_detection import ChangeRecord, ChangeStatus

    world["use"]([_attachment()])
    recovery.recover()
    monkeypatch.setattr(pipeline, "retries", world["retries"])

    record = ChangeRecord(
        status=ChangeStatus.CHANGED, document_id="n-parent", source_type="website",
        source_key="https://teriin.org/parent", fingerprint="f2", bundle="news",
        changed_mark=PARENT_MARK,
    )
    pipeline._track_retry(record, "indexed", frozenset({"n-parent"}))

    assert world["retries"].items == {}
    assert world["retries"].floors() == {}


def test_a_failed_re_ingest_keeps_the_marker(world, monkeypatch):
    """Still stranded, still reachable next sweep — with the reason attached."""
    from app.ingestion import pipeline
    from app.ingestion.change_detection import ChangeRecord, ChangeStatus

    world["use"]([_attachment()])
    recovery.recover()
    monkeypatch.setattr(pipeline, "retries", world["retries"])

    record = ChangeRecord(
        status=ChangeStatus.CHANGED, document_id="n-parent", source_type="website",
        source_key="https://teriin.org/parent", fingerprint="f2", bundle="news",
        changed_mark=PARENT_MARK,
    )
    pipeline._track_retry(record, "error", frozenset({"n-parent"}), error="download failed")

    assert world["retries"].items["n-parent"]["outcome"] == "error"
    assert world["retries"].items["n-parent"]["error"] == "download failed"
    assert world["retries"].floors() == {"news": PARENT_MARK}
