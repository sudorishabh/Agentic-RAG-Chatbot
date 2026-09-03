"""Unit tests for shadow-mode attachment date candidates (Phase 0).

The fixtures are real rows from the teriin.org corpus, so a regression here is
readable as "this document would be dated wrongly" rather than as an abstract
rule change. The load-bearing test is
:func:`test_shadow_mode_does_not_change_effective_start_date` — Phase 0 measures and
must never move a document.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ingestion.date_candidates import (
    DateCandidates,
    parse_pdf_date,
    read_pdf_docinfo,
    resolve,
)

# Real corpus rows (see the Phase 0 investigation).
NODE_AGREE = "2018-10-17T00:00:00+00:00"      # FLOW press release - Indore.pdf
FILE_AGREE = "2018-10-17T00:00:00+00:00"

NODE_MIGRATED = "2018-01-11T06:29:59+00:00"   # dsds2015_day1.pdf: a 2015 deck
FILE_MIGRATED = "2018-01-11T06:29:59+00:00"   # imported in the Dec17-Feb18 batch
PDF_MIGRATED = "2015-02-04T00:00:00+00:00"

NODE_LATE = "2023-08-07T00:00:00+00:00"       # Tandoor pilot handout: a genuine
FILE_LATE = "2024-08-22T00:00:00+00:00"       # upload onto an older page

NODE_STRAGGLER = "2012-06-23T00:00:00+00:00"  # mining-policy-brief_june2012.pdf:
FILE_STRAGGLER = "2018-05-01T00:00:00+00:00"  # a migration straggler, NOT late


def _resolve(**kwargs) -> DateCandidates:
    kwargs.setdefault("document_id", "doc-1")
    kwargs.setdefault("origin", "attachment")
    return resolve(**kwargs)


# --------------------------------------------------------------------------- #
# parse_pdf_date
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "raw, expected_prefix",
    [
        ("D:20240812103321+05'30'", "2024-08-12"),
        ("D:20160722", "2016-07-22"),
        ("D:2016", "2016-01-01"),
    ],
)
def test_pdf_dates_are_parsed_to_iso(raw, expected_prefix):
    assert parse_pdf_date(raw).startswith(expected_prefix)


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "not a date",
        "D:00000000000000",       # the empty-DocInfo default
        "D:19700101000000",       # epoch: a dead clock, not a publication date
        "D:29990101000000",       # far future
        "D:20241332000000",       # month 13
    ],
)
def test_unusable_pdf_dates_are_rejected(raw):
    assert parse_pdf_date(raw) is None


def test_a_sixty_second_timestamp_is_clamped_not_discarded():
    # Some producers emit :60; the date is still good.
    assert parse_pdf_date("D:20200101120060").startswith("2020-01-01")


def test_unreadable_bytes_yield_no_docinfo():
    assert read_pdf_docinfo(b"not a pdf at all") == (None, None)
    assert read_pdf_docinfo(b"") == (None, None)


# --------------------------------------------------------------------------- #
# resolve: the agreeing majority must not move
# --------------------------------------------------------------------------- #

def test_matching_node_and_file_dates_are_left_alone():
    got = _resolve(node_created=NODE_AGREE, file_created=FILE_AGREE)
    assert got.proposed == NODE_AGREE
    assert got.source == "node_created"
    assert got.rule == "default"
    assert got.would_move is False


def test_a_pdf_authored_just_before_upload_does_not_move_the_date():
    # The common case: a PDF written a few weeks before its article went up.
    got = _resolve(node_created=NODE_AGREE, pdf_created="2018-09-20T00:00:00+00:00")
    assert got.would_move is False
    assert got.rule == "default"


def test_a_pdf_attached_weeks_after_its_node_does_not_move_the_date():
    got = _resolve(node_created=NODE_AGREE, file_created="2018-11-05T00:00:00+00:00")
    assert got.would_move is False


# --------------------------------------------------------------------------- #
# resolve: correction 1, the migration era
# --------------------------------------------------------------------------- #

def test_a_migration_era_document_is_dated_from_the_pdf_itself():
    got = _resolve(
        node_created=NODE_MIGRATED,
        file_created=FILE_MIGRATED,
        pdf_created=PDF_MIGRATED,
    )
    assert got.proposed == PDF_MIGRATED
    assert got.source == "pdf_docinfo"
    assert got.rule == "migration_era"
    assert got.would_move is True
    assert got.delta_days is not None and got.delta_days < 0


def test_the_migration_correction_wins_over_the_late_upload_one():
    # A back-catalogue document uploaded years later is better described by when
    # it was written than by when someone got round to posting it.
    got = _resolve(
        node_created=NODE_LATE,
        file_created=FILE_LATE,
        pdf_created="2014-03-01T00:00:00+00:00",
    )
    assert got.rule == "migration_era"
    assert got.source == "pdf_docinfo"


# --------------------------------------------------------------------------- #
# resolve: correction 2, genuine late uploads
# --------------------------------------------------------------------------- #

def test_a_late_upload_onto_an_older_page_is_dated_from_the_file():
    got = _resolve(node_created=NODE_LATE, file_created=FILE_LATE)
    assert got.proposed == FILE_LATE
    assert got.source == "file_created"
    assert got.rule == "late_upload"
    assert got.delta_days == 381


def test_a_migration_straggler_is_not_mistaken_for_a_late_upload():
    """mining-policy-brief_june2012.pdf: node 2012, file 2018-05-01.

    The gap clears a year, but the file date is inside the migration, so it
    describes the import and not an upload — the node's own date stands.
    """
    got = _resolve(node_created=NODE_STRAGGLER, file_created=FILE_STRAGGLER)
    assert got.proposed == NODE_STRAGGLER
    assert got.rule == "default"
    assert got.would_move is False


def test_in_body_pdfs_have_no_file_date_and_fall_through():
    got = _resolve(node_created=NODE_LATE, origin="inbody", file_created=None)
    assert got.origin == "inbody"
    assert got.would_move is False


def test_without_a_node_date_the_pdf_date_is_the_only_candidate():
    got = _resolve(node_created=None, pdf_created=PDF_MIGRATED)
    assert got.proposed == PDF_MIGRATED
    assert got.rule == "no_node_date"


def test_without_any_date_nothing_is_proposed():
    got = _resolve(node_created=None)
    assert got.proposed is None
    assert got.would_move is False


# --------------------------------------------------------------------------- #
# The Phase 0 guarantee
# --------------------------------------------------------------------------- #

class _FakePage:
    page_number = 1
    text = "PDF body text."


class _FakePdfResult:
    source = "a.pdf"
    pages = [_FakePage()]


def test_a_docinfo_only_date_does_not_re_date_the_document(monkeypatch):
    """The production guarantee for the migration-era shape.

    Node and file both stamped 2018 by the import; the PDF's own metadata says
    2015. A DocInfo date is authoring evidence and can never move a date on its
    own, so the document keeps the node's date. (This replaces the Phase 0
    assertion that *nothing* could move a date — production can now, but only on
    a grounded publication statement, which this PDF has not got.)
    """
    from app.ingestion.extractors import attachment, pdf_extractor

    monkeypatch.setattr(attachment, "fetch_attachment", lambda s, url, t: (b"%PDF-", url))
    monkeypatch.setattr(pdf_extractor, "extract_pdf", lambda content, name: _FakePdfResult())
    monkeypatch.setattr(
        "app.ingestion.date_candidates.read_pdf_docinfo",
        lambda content: (PDF_MIGRATED, PDF_MIGRATED),
    )
    recorded: list = []
    monkeypatch.setattr("app.catalog.date_decisions.ensure_table", lambda: None)
    monkeypatch.setattr("app.catalog.date_decisions.record", recorded.append)

    node = SimpleNamespace(
        uuid="node-1", title="A report", url="https://example.org/report",
        created=NODE_MIGRATED, bundle="report", metadata={}, refs=[],
    )
    file = SimpleNamespace(
        uuid="f1", url="https://example.org/a.pdf", filename="a.pdf",
        description=None, origin="attachment", created=FILE_MIGRATED,
    )
    record = SimpleNamespace(
        document_id="f1", source_type="pdf_attachment", payload=(node, file),
        fingerprint="fp",
    )

    doc = attachment.build_attachment_doc(record, session=None)

    assert doc.effective_start_date == NODE_MIGRATED, "a DocInfo date must not re-date a PDF"
    assert len(recorded) == 1, "the decision and its evidence must be recorded"
    stored = recorded[0]
    assert stored.action == "keep_page_date"
    assert stored.current_start_date == NODE_MIGRATED


def test_a_failed_decision_write_never_fails_the_ingestion(monkeypatch):
    from app.ingestion.extractors import attachment, pdf_extractor

    monkeypatch.setattr(attachment, "fetch_attachment", lambda s, url, t: (b"%PDF-", url))
    monkeypatch.setattr(pdf_extractor, "extract_pdf", lambda content, name: _FakePdfResult())

    def _boom() -> None:
        raise RuntimeError("no database")

    monkeypatch.setattr("app.catalog.date_decisions.ensure_table", _boom)

    node = SimpleNamespace(
        uuid="node-1", title="A report", url="https://example.org/report",
        created=NODE_AGREE, bundle="report", metadata={}, refs=[],
    )
    file = SimpleNamespace(
        uuid="f1", url="https://example.org/a.pdf", filename="a.pdf",
        description=None, origin="attachment", created=FILE_AGREE,
    )
    record = SimpleNamespace(
        document_id="f1", source_type="pdf_attachment", payload=(node, file),
        fingerprint="fp",
    )

    doc = attachment.build_attachment_doc(record, session=None)
    assert doc is not None and doc.effective_start_date == NODE_AGREE
