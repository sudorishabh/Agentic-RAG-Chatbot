"""The retired field-keyed backfill must refuse rather than half-apply.

The behaviour worth protecting is narrow: a runbook, a cron entry or an
operator's shell history that still names this script has to land on an
explanation and a non-zero exit, not on a silent no-op and not on a traceback.
The replacement's own tests live in ``test_backfill_bundle_dates.py``.
"""

from __future__ import annotations

from scripts import backfill_source_dates


def test_running_it_fails_rather_than_doing_nothing():
    assert backfill_source_dates.main([]) != 0


def test_it_names_its_replacement(capsys):
    backfill_source_dates.main([])
    printed = capsys.readouterr().err
    assert "scripts.backfill_bundle_dates" in printed


def test_the_replacement_it_names_actually_exists():
    """A pointer to a module that does not import is worse than no pointer."""
    import importlib

    assert importlib.import_module(backfill_source_dates.REPLACEMENT) is not None


def test_it_no_longer_writes_anything():
    """No write path may survive in the module at all — the point of retiring it
    is that it cannot apply a rule ingestion has stopped following."""
    import inspect

    source = inspect.getsource(backfill_source_dates)
    for forbidden in ("UPDATE ", "set_payload", "mysql_connection", "commit"):
        assert forbidden not in source, f"{forbidden!r} survives in a retired script"
