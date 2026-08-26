"""Rebuilding the corpus after a code change, driven by the catalog.

The incremental crawl cannot reach this work: its window is
``changed >= MAX(changed_mark)`` per bundle, and a chunker fix moves nothing in
Drupal, so a document last edited in 2018 stays outside every window forever.
The selection therefore comes from the catalog — which documents are not on the
current `pipeline_version` — and the crawl window is widened to reach them.

Covered here: the census and the window it derives, the pass loop and its stop
conditions (complete, limit, no progress), resumability, the batch controls, and
that nothing about this can delete a document.

The catalog, the crawl and the pipeline are all stubbed; no MySQL, Qdrant or
network.
"""

from __future__ import annotations

import pytest

from app.catalog.models import StateRecord
from app.ingestion import reprocess as rp
from app.ingestion.change_detection import ChangeStatus
from app.ingestion.change_detection.base import compute_status
from app.ingestion.version import PIPELINE_VERSION

OLD = "c0.i0.p0.e0"


# --------------------------------------------------------------------------- #
# The crawl-level rule the whole mechanism rests on.
# --------------------------------------------------------------------------- #

def _row(**kwargs) -> StateRecord:
    defaults = dict(
        document_id="doc-1",
        source_type="website",
        source_key="https://example.org/brief",
        fingerprint="2026-01-01",
        content_hash="h",
        pipeline_version=PIPELINE_VERSION,
    )
    defaults.update(kwargs)
    return StateRecord(**defaults)


def test_a_stale_version_makes_an_otherwise_unchanged_record_changed():
    """Without this the version check is unreachable for exactly the documents
    it exists for: an UNCHANGED record is never built, so nothing downstream
    ever compares its stored version to anything."""
    assert compute_status(_row(pipeline_version=OLD), "2026-01-01") is ChangeStatus.CHANGED


def test_an_unstamped_row_is_changed_too():
    assert compute_status(_row(pipeline_version=None), "2026-01-01") is ChangeStatus.CHANGED


def test_a_current_row_with_an_unchanged_fingerprint_stays_unchanged():
    """The healthy sweep must stay cheap: no version churn means no re-ingest."""
    assert compute_status(_row(), "2026-01-01") is ChangeStatus.UNCHANGED


# --------------------------------------------------------------------------- #
# The census.
# --------------------------------------------------------------------------- #

class _FakeCursor:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.calls.append((" ".join(sql.split()), params))
        return 1

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _census_rows(*rows):
    return [
        {"bundle": b, "documents": n, "floor": f, "without_position": w}
        for b, n, f, w in rows
    ]


@pytest.fixture
def catalog(monkeypatch):
    """A scripted census result; the fixture returns the cursor for assertions."""
    holder = {}

    def use(rows):
        cursor = _FakeCursor(rows)
        monkeypatch.setattr(rp, "mysql_connection", lambda: _FakeConn(cursor))
        monkeypatch.setattr(rp, "_table", lambda: "documents")
        holder["cursor"] = cursor
        return cursor

    holder["use"] = use
    return holder


def test_the_census_counts_only_documents_off_the_current_version(catalog):
    cursor = catalog["use"](_census_rows(("news", 40, 1515666501, 0)))

    report = rp.census()

    sql, params = cursor.calls[0]
    assert "pipeline_version IS NULL OR pipeline_version <> %s" in sql
    assert params[0] == PIPELINE_VERSION
    assert report.documents == 40


def test_the_census_reports_the_window_each_bundle_needs(catalog):
    catalog["use"](
        _census_rows(("news", 40, 1515666501, 0), ("report", 12, 1600000000, 2))
    )

    report = rp.census()

    assert rp.floors_for(report) == {"news": 1515666501, "report": 1600000000}
    assert report.without_position == 2


def test_a_bundle_with_no_crawl_position_cannot_widen_a_window(catalog):
    """A row with no changed_mark cannot position the cursor. It is reported
    rather than silently dropped, because it is only reached when its source is
    fetched in full."""
    catalog["use"](_census_rows((None, 3, None, 3)))

    report = rp.census()

    assert rp.floors_for(report) == {}
    assert report.without_position == 3


def test_selected_bundles_narrow_the_query(catalog):
    cursor = catalog["use"](_census_rows(("news", 5, 1, 0)))

    rp.census(bundles=["news"])

    sql, params = cursor.calls[0]
    assert "bundle IN (%s)" in sql
    assert params[1] == "news"


# --------------------------------------------------------------------------- #
# The pass loop.
# --------------------------------------------------------------------------- #

class _Corpus:
    """A shrinking stale set, and every crawl the reprocessor asked for."""

    def __init__(self, stale: list[int], per_pass: int = 10) -> None:
        self.remaining = list(stale)
        self.per_pass = per_pass
        self.crawls: list[dict] = []

    def census(self, *, version=PIPELINE_VERSION, bundles=None):
        by_bundle = rp.Census(
            version=version,
            bundles=(
                [rp.BundleStale("news", len(self.remaining), min(self.remaining), 0)]
                if self.remaining
                else []
            ),
        )
        return by_bundle

    def run(self, bundles=None, *, published_only=True, extra_floors=None, **kw):
        self.crawls.append(
            {"bundles": bundles, "extra_floors": extra_floors, "kwargs": kw}
        )
        rebuilt = self.remaining[: self.per_pass]
        self.remaining = self.remaining[self.per_pass :]
        return {"indexed": len(rebuilt)}


@pytest.fixture
def corpus(monkeypatch):
    # The reprocessor ensures the schema before asking its question — the column
    # has to exist for the census to be answerable. Stubbed so this module stays
    # a unit test and touches no database.
    import app.catalog.state as state_module

    monkeypatch.setattr(state_module, "ensure_table", lambda: None)

    def build(stale, per_pass=10):
        site = _Corpus(stale, per_pass)
        monkeypatch.setattr(rp, "census", site.census)
        return site

    return build


def test_it_keeps_going_until_nothing_is_stale(corpus):
    site = corpus(list(range(1000, 1025)), per_pass=10)

    report = rp.reprocess(run=site.run, progress=lambda msg: None)

    assert report.stale_before == 25 and report.stale_after == 0
    assert report.rebuilt == 25
    assert report.stopped_because == "complete"
    assert len(site.crawls) == 3, "25 documents at 10 a pass"


def test_each_pass_asks_for_the_window_the_remaining_work_needs(corpus):
    """The floor rises as the oldest documents are rebuilt, so later passes scan
    less — the crawl is not re-walking the whole corpus every time."""
    site = corpus([1000, 1001, 1002, 2000, 2001, 2002], per_pass=3)

    rp.reprocess(run=site.run, progress=lambda msg: None)

    asked = [c["extra_floors"]["news"] for c in site.crawls]
    assert asked == [1000, 2000]


def test_a_limit_stops_the_run_and_leaves_the_rest_for_next_time(corpus):
    site = corpus(list(range(1000, 1030)), per_pass=10)

    report = rp.reprocess(limit=10, run=site.run, progress=lambda msg: None)

    assert report.rebuilt == 10
    assert report.stale_after == 20
    assert report.stopped_because == "limit reached"
    assert len(site.crawls) == 1


def test_it_is_resumable_because_progress_lives_in_the_catalog(corpus):
    """Two capped invocations finish what one uncapped one would have."""
    site = corpus(list(range(1000, 1020)), per_pass=10)

    first = rp.reprocess(limit=10, run=site.run, progress=lambda msg: None)
    second = rp.reprocess(run=site.run, progress=lambda msg: None)

    assert first.stale_after == 10
    assert second.stale_before == 10 and second.stale_after == 0


def test_a_pass_that_rebuilds_nothing_stops_the_run(corpus):
    """A document that fails to rebuild stays stale. Without this guard the loop
    would re-attempt it forever."""
    site = corpus([1000, 1001], per_pass=0)

    report = rp.reprocess(run=site.run, progress=lambda msg: None)

    assert report.stopped_because == "no progress"
    assert len(site.crawls) == 1, "it stops rather than trying again"


def test_max_passes_bounds_one_invocation(corpus):
    site = corpus(list(range(1000, 1100)), per_pass=1)

    report = rp.reprocess(max_passes=3, run=site.run, progress=lambda msg: None)

    assert len(site.crawls) == 3
    assert report.stopped_because == "max passes"


def test_nothing_stale_means_nothing_crawled(corpus):
    site = corpus([])

    report = rp.reprocess(run=site.run, progress=lambda msg: None)

    assert site.crawls == []
    assert report.rebuilt == 0 and report.stopped_because == "complete"


def test_the_schema_is_ensured_before_the_catalog_is_asked(monkeypatch):
    """The census reads a column that a deployment may not have yet, so the
    tool has to make it exist before it can report anything — including under
    --dry-run, where the alternative is an unexplained SQL error."""
    import app.catalog.state as state_module

    order: list[str] = []
    monkeypatch.setattr(state_module, "ensure_table", lambda: order.append("ensure"))
    monkeypatch.setattr(
        rp, "census",
        lambda **kw: order.append("census") or rp.Census(version=PIPELINE_VERSION),
    )

    rp.reprocess(dry_run=True, progress=lambda msg: None)

    assert order == ["ensure", "census"]


# --------------------------------------------------------------------------- #
# Safety and controls.
# --------------------------------------------------------------------------- #

def test_a_dry_run_crawls_nothing(corpus):
    site = corpus(list(range(1000, 1010)))
    lines: list[str] = []

    report = rp.reprocess(dry_run=True, run=site.run, progress=lines.append)

    assert site.crawls == [], "no crawl, no indexing, no deletion"
    assert report.stale_after == report.stale_before == 10
    assert report.stopped_because == "dry run"
    assert any("Dry run" in line for line in lines)


def test_reconciliation_is_never_enabled(corpus):
    """A version bump says nothing about a document having been removed at
    source, and a delete is the one thing a reprocess must never do."""
    site = corpus([1000], per_pass=1)

    rp.reprocess(run=site.run, progress=lambda msg: None)

    assert "reconcile_deletes" not in site.crawls[0]["kwargs"]
    assert all("reconcile" not in str(c["kwargs"]) for c in site.crawls)


def test_the_batch_controls_apply_only_for_the_run(corpus, monkeypatch):
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "ingest_batch_size", 7)
    monkeypatch.setattr(settings, "ingest_batch_pause_seconds", 0.0)
    seen: list[tuple[int, float, int]] = []

    site = corpus([1000], per_pass=1)
    original_run = site.run

    def run(*args, **kwargs):
        seen.append(
            (
                settings.ingest_batch_size,
                settings.ingest_batch_pause_seconds,
                settings.ingest_max_docs_per_run,
            )
        )
        return original_run(*args, **kwargs)

    rp.reprocess(
        limit=5, batch_size=25, pause=1.5, run=run, progress=lambda msg: None
    )

    assert seen == [(25, 1.5, 5)], "the crawl ran under this run's controls"
    assert settings.ingest_batch_size == 7, "and the deployment's are restored"
    assert settings.ingest_batch_pause_seconds == 0.0


def test_selected_bundles_reach_the_crawl(corpus):
    site = corpus([1000], per_pass=1)

    rp.reprocess(["news"], run=site.run, progress=lambda msg: None)

    assert site.crawls[0]["bundles"] == ["news"]


def test_the_report_records_every_pass(corpus):
    site = corpus(list(range(1000, 1015)), per_pass=10)

    report = rp.reprocess(run=site.run, progress=lambda msg: None).as_dict()

    assert [p["pass"] for p in report["passes"]] == [1, 2]
    assert report["passes"][0]["rebuilt"] == 10
    assert report["passes"][1]["stale_after"] == 0
    assert report["rebuilt"] == 15
