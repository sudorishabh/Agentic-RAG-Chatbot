"""The migration that re-dates what is already ingested.

Ingestion code alone fixes nothing historical: a sweep that finds a document
unchanged returns before the document is rebuilt, so an existing row keeps the
date the old rule gave it. These tests cover the parts that decide *what* moves
and *what must not* — the database round-trips are exercised by running it.

The properties that matter:

* it re-derives from the metadata, never from the current value, so running it
  twice cannot compound;
* an attachment takes its page's new date, and a file dated from its own text
  does not;
* the pre-flight refuses a run that would write something the mapping does not
  sanction.
"""

from __future__ import annotations

import pytest

from app.ingestion.bundle_dates import resolve
from scripts.backfill_bundle_dates import (
    Move,
    attachment_moves,
    preflight,
    report,
)

CREATED = "2018-01-11T06:29:59+00:00"


def _move(**kwargs) -> Move:
    base = dict(
        document_id="d1", source_type="website", bundle="news",
        url="https://teriin.org/news/x", old_value=CREATED,
        new_value="2015-08-27T00:00:00+00:00", precision="day",
        source="cms_field", rule="bundle_date_field", field="field_news_date",
    )
    base.update(kwargs)
    return Move(**base)


# --------------------------------------------------------------------------- #
# The move
# --------------------------------------------------------------------------- #

def test_a_move_reports_how_far_the_stored_date_was_out():
    assert _move().days > 0, "the stored date was later than the truth"
    assert _move(old_value="2010-01-01T00:00:00+00:00").days < 0


def test_a_move_is_immutable():
    """It is reported, pre-flighted and then written; a mutable one could be
    reviewed as one thing and applied as another."""
    with pytest.raises(Exception):
        _move().new_value = "2001-01-01T00:00:00+00:00"


# --------------------------------------------------------------------------- #
# Pre-flight
# --------------------------------------------------------------------------- #

def test_a_clean_set_of_moves_passes():
    assert preflight([_move()], expect=-1) == []


def test_a_drifted_corpus_stops_the_run():
    """The reviewed dry run is the authority. A different set must not be
    rewritten silently because the corpus changed since."""
    problems = preflight([_move()], expect=99)
    assert problems and "expected 99" in problems[0]


def test_a_field_outside_the_mapping_is_refused():
    """The mapping is what sanctions a write. A value from anywhere else means
    something re-implemented the rule."""
    problems = preflight([_move(field="field_something_else")], expect=-1)
    assert any("not in the bundle mapping" in p for p in problems)


def test_an_unexpected_provenance_is_refused():
    problems = preflight([_move(source="guesswork")], expect=-1)
    assert any("unexpected provenance" in p for p in problems)


def test_a_year_precision_value_that_is_not_january_is_refused():
    """A year-precision date is 1 January standing in for a year. Any other day
    means the value and its precision disagree about what is known."""
    problems = preflight(
        [_move(precision="year", new_value="2016-06-01T00:00:00+00:00")], expect=-1)
    assert any("1 January" in p for p in problems)


def test_a_real_year_precision_value_passes():
    assert preflight([_move(precision="year", field="field_rpaper_year",
                            new_value="2016-01-01T00:00:00+00:00")],
                     expect=-1) == []


def test_a_value_with_no_timezone_is_refused():
    """`state._to_datetime` normalises to naive UTC; an offset-less value would
    shift the calendar date every consumer reads."""
    problems = preflight([_move(new_value="2015-08-27T00:00:00")], expect=-1)
    assert any("timezone" in p for p in problems)


def test_an_attachment_move_passes_the_same_gate():
    assert preflight([_move(source_type="pdf_attachment", source="parent_page",
                            rule="inherited_from_parent", parent_id="p1")],
                     expect=-1) == []


# --------------------------------------------------------------------------- #
# Attachment inheritance
# --------------------------------------------------------------------------- #

class _Cursor:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, *_a, **_k):
        return None

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False


class _Conn:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self):
        return _Cursor(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False


@pytest.fixture
def rows(monkeypatch):
    """Patch the one query `attachment_moves` makes."""
    captured: list = []

    def _install(value):
        captured.clear()
        captured.extend(value)

    import scripts.backfill_bundle_dates as script

    monkeypatch.setattr(script, "attachment_moves",
                        script.attachment_moves)  # keep the real function
    monkeypatch.setattr("app.catalog.db.state_table", lambda: "documents")
    monkeypatch.setattr("app.core.clients.mysql_connection",
                        lambda *a, **k: _Conn(captured))
    return _install


def _paper_page():
    return {"p1": resolve("research_papers", CREATED, {"field_rpaper_year": 2016})}


def _row(**kwargs):
    base = {"parent_id": "p1", "document_id": "f1",
            "published_at": CREATED, "published_at_precision": "day",
            "published_at_source": "parent_page",
            "url": "https://teriin.org/a.pdf", "bundle": "research_papers"}
    base.update(kwargs)
    return base


def test_an_attachment_takes_its_pages_new_date(rows):
    rows([_row()])
    moves = attachment_moves(_paper_page())
    assert len(moves) == 1
    assert moves[0].new_value == "2016-01-01T00:00:00+00:00"
    assert moves[0].precision == "year"
    assert moves[0].source == "parent_page"
    assert moves[0].parent_id == "p1"


def test_an_attachment_already_on_its_pages_date_does_not_move(rows):
    rows([_row(published_at="2016-01-01T00:00:00+00:00",
               published_at_precision="year")])
    assert attachment_moves(_paper_page()) == []


def test_a_precision_change_alone_is_still_a_move(rows):
    """The value is right and the marker is not: a reader would render 1 January
    as a real day."""
    rows([_row(published_at="2016-01-01T00:00:00+00:00",
               published_at_precision="day")])
    assert len(attachment_moves(_paper_page())) == 1


def test_a_file_dated_from_its_own_text_is_left_alone(rows):
    """The one override the design grants, and it outranks inheritance."""
    rows([_row(published_at_source="document_text")])
    assert attachment_moves(_paper_page()) == []


def test_an_attachment_whose_page_is_not_in_the_catalog_is_skipped(rows):
    rows([_row(parent_id="missing")])
    assert attachment_moves(_paper_page()) == []


def test_an_attachment_reachable_from_two_pages_moves_once(rows):
    """84 files hang off more than one page. Ordered by (file, page) so the same
    parent wins on every run."""
    rows([_row(parent_id="p1"), _row(parent_id="p2")])
    resolutions = _paper_page()
    resolutions["p2"] = resolve("article", "2020-05-05T00:00:00+00:00", {})
    moves = attachment_moves(resolutions)
    assert len(moves) == 1 and moves[0].parent_id == "p1"


def test_every_file_on_one_page_takes_the_same_date(rows):
    rows([_row(document_id=f"f{i}") for i in range(5)])
    moves = attachment_moves(_paper_page())
    assert len(moves) == 5
    assert {m.new_value for m in moves} == {"2016-01-01T00:00:00+00:00"}


def test_a_page_that_resolved_to_nothing_moves_none_of_its_files(rows):
    rows([_row()])
    assert attachment_moves({"p1": resolve("article", None, {})}) == []


# --------------------------------------------------------------------------- #
# The report is what a reviewer approves
# --------------------------------------------------------------------------- #

def test_the_report_survives_an_empty_run(capsys):
    report([], [])
    assert "0" in capsys.readouterr().out


def test_the_report_separates_pages_from_attachments(capsys):
    report([_move(),
            _move(document_id="f1", source_type="pdf_attachment",
                  source="parent_page", rule="inherited_from_parent")], [])
    printed = capsys.readouterr().out
    assert "1 pages, 1 attachments" in printed


def test_the_report_names_documents_it_could_not_re_derive(capsys):
    """Skipped, not guessed: without the original creation stamp the fallback
    rungs have nothing to fall back to."""
    report([], ["lost-1", "lost-2"])
    printed = capsys.readouterr().out
    assert "not recoverable" in printed
    assert "lost-1" in printed


def test_an_undated_document_does_not_break_the_report(capsys):
    report([_move(old_value="")], [])
    assert "attachments" in capsys.readouterr().out
