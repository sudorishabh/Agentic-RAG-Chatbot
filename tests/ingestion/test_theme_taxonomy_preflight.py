"""The theme-map preflight on the write paths that rewrite theme rows.

``theme_taxonomy.require_taxonomy`` existed for a while without a single
production caller, which made it documentation rather than a guard. These tests
pin the wiring, not the function — ``test_theme_rows.py`` already covers what
``require_taxonomy`` does in isolation.

Why it has to be a preflight and not a per-document check: classifying against
an unreadable map does not raise. It succeeds, and returns every theme as
unmapped — no parent, no group, no path. A run in that state does not fail
noisily; it quietly rewrites the hierarchy of every document it touches. The
trigger can be as small as the data file going missing, which has happened. So
the run refuses before it writes anything, while per-document classification
stays tolerant so a mid-run problem costs one document rather than the ingest.
"""

from __future__ import annotations

import pytest

from app.catalog import theme_taxonomy
from app.ingestion import backfill, pipeline


@pytest.fixture
def unreadable_map(monkeypatch, tmp_path):
    """Point the taxonomy at a file that is not there and drop the cache."""
    monkeypatch.setattr(theme_taxonomy, "TAXONOMY_PATH", tmp_path / "gone.json")
    theme_taxonomy.reload_taxonomy()
    yield
    theme_taxonomy.reload_taxonomy()


def test_an_ingest_run_refuses_to_start_without_a_theme_map(
    monkeypatch, unreadable_map
):
    touched: list[str] = []
    monkeypatch.setattr(
        pipeline.state, "ensure_table", lambda: touched.append("ensure_table")
    )
    monkeypatch.setattr(
        pipeline, "_handle", lambda *a, **k: touched.append("handle") or "indexed"
    )

    with pytest.raises(theme_taxonomy.TaxonomyUnavailable):
        pipeline._run(iter(()), build_doc=lambda r: None)

    # Before anything, including the table setup: nothing was written, so
    # nothing has to be repaired.
    assert touched == []


def test_the_facet_backfill_refuses_too(monkeypatch, unreadable_map):
    """It rewrites theme rows for every document it finds a payload for, so it
    can do the same corpus-wide damage as an ingest run."""
    monkeypatch.setattr(
        backfill, "collect", lambda: pytest.fail("collect ran before the guard")
    )

    with pytest.raises(theme_taxonomy.TaxonomyUnavailable):
        backfill.backfill_catalog()


def test_reclassifying_rows_refuses_too(monkeypatch, unreadable_map):
    """The sharpest case: this exists to *repair* rows whose hierarchy is
    missing, and against an empty map it would write exactly the damage it is
    meant to undo."""
    from app.catalog import state

    monkeypatch.setattr(
        state,
        "mysql_connection",
        lambda: pytest.fail("opened a connection before the guard"),
    )

    with pytest.raises(theme_taxonomy.TaxonomyUnavailable):
        state.reclassify_theme_rows()


def test_an_ingest_run_proceeds_with_the_shipped_map(monkeypatch):
    """The guard must not be a new way for ingestion to fail: with the real map
    in place the run starts as before."""
    theme_taxonomy.reload_taxonomy()
    started: list[str] = []
    monkeypatch.setattr(
        pipeline.state, "ensure_table", lambda: started.append("ensure_table")
    )
    monkeypatch.setattr(pipeline.ingest_log, "ensure_table", lambda: None)
    monkeypatch.setattr(pipeline, "_pending_retries", frozenset)
    monkeypatch.setattr(pipeline, "_prewarm_clients", lambda settings: None)

    pipeline._run(iter(()), build_doc=lambda r: None)

    assert started == ["ensure_table"]


def test_the_shipped_map_is_where_configuration_says_it_is():
    """The path is resolved from `theme_taxonomy_path`, defaulting to the file
    beside the app package. A default that does not exist is the whole outage
    this module guards against, so it is asserted directly."""
    theme_taxonomy.reload_taxonomy()
    assert theme_taxonomy.TAXONOMY_PATH.exists(), (
        f"{theme_taxonomy.TAXONOMY_PATH} is missing; ingestion will refuse to run."
    )
    assert theme_taxonomy.is_loaded()


def test_the_configured_path_overrides_the_default(monkeypatch, tmp_path):
    """A deployment must be able to relocate the map without a code edit — the
    reason there is a setting at all rather than a bare path expression."""
    elsewhere = tmp_path / "custom" / "themes.json"
    elsewhere.parent.mkdir()
    elsewhere.write_text("[]", encoding="utf-8")

    from app.config import get_settings

    class _Settings:
        theme_taxonomy_path = str(elsewhere)

    monkeypatch.setattr(theme_taxonomy, "get_settings", lambda: _Settings())
    assert theme_taxonomy._configured_path() == elsewhere

    # Unset falls back to the shipped file next to the app package.
    class _Unset:
        theme_taxonomy_path = ""

    monkeypatch.setattr(theme_taxonomy, "get_settings", lambda: _Unset())
    assert theme_taxonomy._configured_path().name == "theme_structure.json"
    assert get_settings().theme_taxonomy_path == ""
