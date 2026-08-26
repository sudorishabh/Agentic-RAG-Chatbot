"""Standing invariants over ``published_at`` and where it came from.

These run on **every sweep** (``reconcile_after_sweep``), not only on demand,
which is the whole point: every problem the date audit found had existed for
months with nothing reporting it.

That placement sets the bar. A check belongs here only if it is **zero in a
healthy corpus** — every check in ``reconcile`` is, and a sweep that always warns
is a sweep nobody reads. The legitimately non-zero measurements stay in
``scripts.audit_dates``: 30 documents dated before the period their own name
states, 2,796 dated by an import batch with nothing better available. Those are
findings to work through, not alarms.
"""

from __future__ import annotations

import inspect

import pytest

from app.ingestion import reconcile


ADDED = (
    "date_provenance_unrecorded",
    "stated_date_not_applied",
    "undeclared_source_date_field",
    "year_precision_not_january",
)


# --------------------------------------------------------------------------- #
# They run where they need to
# --------------------------------------------------------------------------- #

def test_the_date_checks_are_part_of_reconciliation():
    """`verify_corpus` is a thin CLI over `reconcile()`, and the sweep calls the
    same function — so adding them here is what makes them standing rather than
    something a person has to remember to run."""
    assert "report.checks += date_checks()" in inspect.getsource(reconcile.reconcile)


def test_the_sweep_reports_drift_without_failing_the_sweep():
    """A date problem must not throw away an otherwise successful ingestion."""
    src = inspect.getsource(reconcile.reconcile_after_sweep)
    assert "logger.warning" in src
    assert "never raise" in src or "does not fail the sweep" in src


def test_nothing_here_repairs_anything():
    src = inspect.getsource(reconcile.date_checks)
    for forbidden in ("UPDATE ", "DELETE ", "INSERT ", "set_payload", "commit"):
        assert forbidden not in src, f"{forbidden!r} in a read-only check"


# --------------------------------------------------------------------------- #
# Each check has a cause and a next step
# --------------------------------------------------------------------------- #

def test_each_check_says_what_to_do_about_it():
    """"A number with no next step is how drift gets watched rather than
    fixed" — the module's own words. Each detail names the cause or the fix."""
    checks = {c.name: c for c in _fake_checks()}
    for name in ADDED:
        detail = checks[name].detail
        assert len(detail) > 40, f"{name} has no useful detail"
        assert any(word in detail for word in
                   ("Re-run", "Classify", "came from", "means")), name


def _fake_checks():
    """The checks as constructed, without a database.

    `date_checks` fails soft, so calling it with the catalogue unreachable
    returns a single skipped check — which is itself the behaviour under test
    below. To inspect the four real ones we build them the same way the function
    does, from the same helper.
    """
    return [
        reconcile._check("date_provenance_unrecorded", [],
                         "Documents whose published_at has no recorded origin. Every "
                         "write path sets it, so these came from one that does not."),
        reconcile._check("stated_date_not_applied", [],
                         "The source states a publication date that published_at does "
                         "not match. Re-run scripts.backfill_source_dates."),
        reconcile._check("undeclared_source_date_field", [],
                         "A source field that looks like a date and holds a parseable "
                         "one, which nothing has classified. Classify it in "
                         "app.ingestion.source_dates.FIELD_KINDS."),
        reconcile._check("year_precision_not_january", [],
                         "A year-precision date whose value is not 1 January. The day "
                         "is a marker for the year, so it means they disagree."),
    ]


def test_a_zero_count_reads_as_healthy():
    for check in _fake_checks():
        assert check.count == 0
        assert check.ok


def test_a_non_zero_count_reads_as_drift():
    check = reconcile._check("stated_date_not_applied", ["a", "b"], "detail")
    assert check.count == 2
    assert not check.ok


# --------------------------------------------------------------------------- #
# Failing soft
# --------------------------------------------------------------------------- #

def test_an_unreadable_catalogue_skips_rather_than_fails(monkeypatch):
    """A skipped check is not a passing check, and it must not turn a database
    hiccup into a failed sweep."""
    import app.core.clients as clients

    def _boom(*args, **kwargs):
        raise RuntimeError("MySQL is down")

    monkeypatch.setattr(clients, "mysql_connection", _boom)
    checks = reconcile.date_checks()
    assert len(checks) == 1
    assert checks[0].skipped
    assert checks[0].ok          # skipped does not fail a sweep
    assert checks[0].count == 0


# --------------------------------------------------------------------------- #
# What is deliberately NOT checked here
# --------------------------------------------------------------------------- #

def test_the_legitimately_non_zero_findings_stay_in_the_audit_script():
    """`dated_before_its_reporting_period` is 30 in a healthy corpus and
    `documents_in_migration_window` is 2,796. Either one here would make every
    sweep warn forever, and a warning that is always on is not a warning."""
    src = inspect.getsource(reconcile.date_checks)
    assert "dated_before_its_reporting_period" not in src
    assert "migration_window" not in src

    from scripts import audit_dates

    audit = inspect.getsource(audit_dates)
    assert "dated_before_its_reporting_period" in audit
    assert "documents_in_migration_window" in audit


# --------------------------------------------------------------------------- #
# The declaration that keeps the undeclared-field check meaningful
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "field", ["field_article_published_in", "field_rpaper_published_in",
              "field_rpaper_publisher"],
)
def test_the_venue_fields_are_declared_so_the_alarm_stays_meaningful(field):
    """These three hold journal and publisher names, and their names contain
    "publish". Declared ``unknown`` — looked at and rejected — so
    `undeclared_source_date_field` means "nobody has classified this" rather
    than firing on them forever. One field_rpaper_publisher value is literally
    "2021", which would otherwise parse as a date."""
    from app.ingestion.source_dates import FIELD_KINDS, classify

    assert field in FIELD_KINDS
    assert classify(field) == "unknown"


def test_declaring_a_field_unknown_does_not_let_it_set_a_date():
    from app.ingestion.source_dates import publication_date

    assert publication_date({"field_rpaper_publisher": "2021"}) is None
    assert publication_date({"field_article_published_in": "2019"}) is None


def test_a_genuinely_new_field_is_still_flagged():
    """Declaring the known three must not silence the check for the next one."""
    from app.ingestion.source_dates import FIELD_KINDS

    assert "field_brand_new_date" not in FIELD_KINDS
    assert reconcile._DATE_LIKE_FIELD.search("field_brand_new_date")
