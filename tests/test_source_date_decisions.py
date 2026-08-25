"""The date audit trail covers website documents, not only PDFs.

``{state}_date_decision`` is both the audit trail ("why does this document carry
this date?") and the review queue. It held PDF rows only, so the question was
unanswerable for the 8,507 documents where the date was simply the CMS record's
creation stamp — which is where the large errors are.

Two shaping constraints, both tested below:

**A row is written only when the source offered a publication date.** ~6,000
records state nothing; a row saying so for each would cost an INSERT and a
commit to answer what ``documents.published_at_source`` already answers.

**The review queue must not be swamped.** 617 records carry a year and nothing
finer. Those are *deferred*, not *reviewed* — the queue is for cases a person
has to settle, and burying 23 real ones under 617 known deferrals would empty it
of meaning.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.catalog.date_decisions import from_source_record
from app.ingestion.source_dates import SourceDate, publication_date

CREATED = "2018-01-11T06:29:59+00:00"


def _row(metadata: dict, applied: str | None = None, created: str = CREATED):
    stated = publication_date(metadata)
    return from_source_record(
        document_id="uuid-1", bundle="news", url="https://teriin.org/news/x",
        created=created, applied=applied if applied is not None else created,
        stated=stated,
    )


# --------------------------------------------------------------------------- #
# When nothing is written
# --------------------------------------------------------------------------- #

def test_a_record_stating_no_publication_date_gets_no_row():
    assert _row({}) is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("field_event_start_date", "2017-11-05T18:30:00+00:00"),
        ("field_completed_start_date", "2004-06-28T18:30:00+00:00"),
        ("field_ongoing_start_date", "2019-10-24T10:35:27+00:00"),
        ("field_enddate_forlatestfirst", "2020-05-08T22:00:00+05:30"),
    ],
)
def test_an_event_or_period_date_is_not_something_to_audit(field, value):
    """It was never a candidate, so there is no decision to explain."""
    assert _row({field: value}) is None


def test_an_undeclared_field_gets_no_row():
    assert _row({"field_mystery_date": "2011-01-01T00:00:00+00:00"}) is None


def test_an_implausible_value_gets_no_row():
    assert _row({"field_news_date": "1970-01-01T00:00:00+00:00"}) is None


# --------------------------------------------------------------------------- #
# The date moved
# --------------------------------------------------------------------------- #

def test_a_corrected_date_is_recorded_as_an_override():
    row = _row({"field_news_date": "2015-08-26T18:30:00+00:00"},
               applied="2015-08-27T00:00:00+00:00")
    assert row is not None
    assert row.action == "propose_override"
    assert row.rule == "cms_publication_field"
    assert row.candidate_source == "field_news_date"
    assert row.decided_by == "deterministic"
    assert row.confidence == 1.0


def test_the_row_preserves_what_the_date_would_have_been():
    """The whole value of the audit trail: "would have been X, assigned Y"."""
    row = _row({"field_news_date": "2015-08-26T18:30:00+00:00"},
               applied="2015-08-27T00:00:00+00:00")
    assert row.current_published_at == CREATED
    assert row.candidate_date == "2015-08-27T00:00:00+00:00"


def test_the_evidence_names_the_field_and_both_dates():
    row = _row({"field_pressrelease_date": "2012-04-17T18:30:00+00:00"},
               applied="2012-04-18T00:00:00+00:00")
    assert "field_pressrelease_date" in row.evidence
    assert "2012-04-18" in row.evidence
    assert "2018-01-11" in row.evidence


# --------------------------------------------------------------------------- #
# The source agreed already
# --------------------------------------------------------------------------- #

def test_a_field_that_matches_the_created_stamp_is_recorded_as_a_keep():
    """1,334 records are in this state. Worth a row — it is evidence the date is
    corroborated rather than merely unchallenged — but not an override."""
    row = _row({"field_news_date": "2018-01-11T06:29:59+00:00"})
    assert row.action == "keep_page_date"
    assert row.rule == "cms_field_matches_created"
    assert row.candidate_source == "node_created"


# --------------------------------------------------------------------------- #
# Year precision is deferred, not reviewed
# --------------------------------------------------------------------------- #

def test_a_year_only_source_is_deferred_rather_than_applied():
    row = _row({"field_rpaper_year": "2016"})
    assert row is not None
    assert row.action == "keep_page_date"
    assert row.rule == "year_precision_deferred"
    assert row.candidate_date == CREATED


def test_a_deferral_never_reaches_the_review_queue():
    """`WHERE action='needs_manual_review'` is the queue. 617 deferrals landing
    in it would bury the 23 cases that need a person."""
    row = _row({"field_rpaper_year": "2016"})
    assert row.action != "needs_manual_review"


def test_the_deferral_is_findable_as_the_phase_two_worklist():
    row = _row({"field_rpaper_year": "2016"})
    assert row.rule == "year_precision_deferred"
    assert "year" in row.evidence


# --------------------------------------------------------------------------- #
# Row shape: it has to fit the columns and the existing reports
# --------------------------------------------------------------------------- #

def test_the_row_marks_itself_as_a_website_document():
    row = _row({"field_news_date": "2015-08-26T18:30:00+00:00"},
               applied="2015-08-27T00:00:00+00:00")
    assert row.origin == "website"


def test_a_source_record_is_its_own_page():
    """Reports join node_uuid back to the catalogue; a NULL would dangle."""
    row = _row({"field_news_date": "2015-08-26T18:30:00+00:00"})
    assert row.node_uuid == row.document_id


def test_every_value_fits_its_column():
    """Silently truncated values are wrong values. Widths from schema.py."""
    widths = {"origin": 16, "candidate_source": 32, "action": 24, "rule": 48,
              "decided_by": 16, "date_type": 16}
    for metadata, applied in (
        ({"field_news_date": "2015-08-26T18:30:00+00:00"}, "2015-08-27T00:00:00+00:00"),
        ({"field_pressrelease_date": "2012-04-17T18:30:00+00:00"}, "2012-04-18T00:00:00+00:00"),
        ({"field_rpaper_year": "2016"}, None),
        ({"field_news_date": "2018-01-11T06:29:59+00:00"}, None),
    ):
        row = _row(metadata, applied=applied)
        for attribute, width in widths.items():
            value = getattr(row, attribute)
            assert value is None or len(str(value)) <= width, \
                f"{attribute}={value!r} exceeds {width}"


def test_the_vocabularies_match_the_pdf_path():
    """One table, one set of values, so a report does not need to know which
    source type wrote a row."""
    from app.ingestion.date_rules import Action, DateType
    from typing import get_args

    actions, types = set(get_args(Action)), set(get_args(DateType))
    for metadata, applied in (
        ({"field_news_date": "2015-08-26T18:30:00+00:00"}, "2015-08-27T00:00:00+00:00"),
        ({"field_rpaper_year": "2016"}, None),
        ({"field_news_date": "2018-01-11T06:29:59+00:00"}, None),
    ):
        row = _row(metadata, applied=applied)
        assert row.action in actions
        assert row.date_type in types
        assert row.decided_by in ("deterministic", "llm")


def test_no_llm_fields_are_claimed():
    """Nothing here consulted a model, and a prompt_version would imply one."""
    row = _row({"field_news_date": "2015-08-26T18:30:00+00:00"})
    assert row.llm_raw is None
    assert row.prompt_version is None


# --------------------------------------------------------------------------- #
# The call site
# --------------------------------------------------------------------------- #

def test_only_website_records_are_recorded_here():
    """Attachments record their own decision inside `build_attachment_doc`;
    recording them again here would double every PDF row."""
    import inspect

    from app.ingestion import pipeline

    src = inspect.getsource(pipeline._record_source_date_decision)
    assert 'if record.source_type != "website":' in src
    assert "return" in src


def test_the_write_fails_open(monkeypatch):
    """An unreachable database must cost a warning, never a document."""
    from app.catalog import date_decisions
    from app.ingestion import pipeline

    def _boom(*args, **kwargs):
        raise RuntimeError("MySQL is down")

    monkeypatch.setattr(date_decisions, "ensure_table", _boom)

    class _Rec:
        source_type = "website"
        document_id = "uuid-1"
        bundle = "news"
        payload = type("P", (), {"created": CREATED})()

    class _Doc:
        source_url = "https://teriin.org/news/x"
        published_at = "2015-08-27T00:00:00+00:00"
        raw_meta = {"field_news_date": "2015-08-26T18:30:00+00:00"}

    pipeline._record_source_date_decision(_Rec(), _Doc())  # must not raise


def test_the_row_uses_the_value_the_write_path_applied():
    """`applied` is passed in rather than re-derived, so the audit row cannot
    disagree with the date actually stored."""
    row = from_source_record(
        document_id="d", bundle="news", url=None, created=CREATED,
        applied="2015-08-27T00:00:00+00:00",
        stated=SourceDate(value=date(2015, 8, 27), field="field_news_date",
                          kind="publication", precision="day"),
    )
    assert row.candidate_date == "2015-08-27T00:00:00+00:00"
