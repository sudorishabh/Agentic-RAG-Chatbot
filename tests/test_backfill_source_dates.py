"""The date backfill's judgements and its refusals.

This is the only step in the date work that writes data, so the tests are almost
entirely about what stops it. The reviewed dry run showed 1,047 documents; a run
that would move a different number, or move a year-precision value, or store a
non-UTC string, has to fail before the first write rather than after a partial
one.
"""

from __future__ import annotations

import pytest

from scripts.backfill_source_dates import EXPECTED_MOVES, Move, _metadata, preflight, report


def _move(created: str, new_value: str, field: str = "field_news_date",
          precision: str = "day") -> Move:
    return Move(document_id="d", bundle="news", url="https://teriin.org/news/x",
                created=created, new_value=new_value, field=field, precision=precision)


# --------------------------------------------------------------------------- #
# How far the date moves
# --------------------------------------------------------------------------- #

def test_a_correction_backwards_reports_positive_days():
    move = _move("2018-01-11T06:29:59+00:00", "2012-04-18T00:00:00+00:00")
    assert move.days == 2094


def test_a_correction_forwards_reports_negative_days():
    """Ten documents move later. The sign is what makes them findable in the
    report, since they are the ones worth eyeballing individually."""
    move = _move("2022-11-16T05:47:22+00:00", "2022-11-18T00:00:00+00:00")
    assert move.days == -2


def test_a_single_day_shift_is_counted_as_one_day():
    """172 of the 1,047 are one day — the population where a timezone bug would
    be indistinguishable from a correction."""
    assert _move("2026-01-08T00:00:00+00:00", "2026-01-07T00:00:00+00:00").days == 1


def test_the_largest_observed_correction():
    """A white paper on a 2008 policy, recorded in 2020, dated 2009 by the CMS."""
    assert _move("2020-11-24T04:59:38+00:00", "2009-02-12T00:00:00+00:00").days == 4303


# --------------------------------------------------------------------------- #
# The refusals
# --------------------------------------------------------------------------- #

def test_a_clean_run_has_no_objections():
    moves = [_move("2018-01-11T06:29:59+00:00", "2012-04-18T00:00:00+00:00")]
    assert preflight(moves, expect=1) == []


def test_a_drifted_count_refuses():
    """The corpus changing between review and apply is the case this exists for:
    the reviewed diff would no longer be the diff being applied."""
    moves = [_move("2018-01-11T06:29:59+00:00", "2012-04-18T00:00:00+00:00")]
    problems = preflight(moves, expect=1047)
    assert len(problems) == 1
    assert "expected 1047" in problems[0]


def test_the_count_check_can_be_disabled_deliberately():
    moves = [_move("2018-01-11T06:29:59+00:00", "2012-04-18T00:00:00+00:00")]
    assert preflight(moves, expect=-1) == []


def test_a_year_precision_value_is_allowed_when_it_is_january_first():
    """A year-only source is applied as 1 January, marked year precision."""
    moves = [_move("2018-01-11T06:29:59+00:00", "2016-01-01T00:00:00+00:00",
                   field="field_rpaper_year", precision="year")]
    assert preflight(moves, expect=1) == []


def test_a_year_precision_value_on_another_day_refuses():
    """1 January is the marker the precision refers to. Any other day means the
    value and its precision disagree about what is known — the thing
    `reconcile.year_precision_not_january` watches for."""
    moves = [_move("2018-01-11T06:29:59+00:00", "2016-03-15T00:00:00+00:00",
                   field="field_rpaper_year", precision="year")]
    problems = preflight(moves, expect=1)
    assert any("not 1 January" in p for p in problems)


def test_an_unactionable_precision_refuses():
    """If a precision is staged out by narrowing ACTIONABLE_PRECISIONS, a move
    carrying it must not slip through a backfill written before the change."""
    moves = [_move("2018-01-11T06:29:59+00:00", "2016-01-01T00:00:00+00:00",
                   field="field_rpaper_year", precision="century")]
    problems = preflight(moves, expect=1)
    assert any("not actionable" in p for p in problems)


def test_a_non_publication_field_refuses():
    """An event or project date reaching the move list is the corruption this
    whole design exists to prevent."""
    moves = [_move("2018-01-11T06:29:59+00:00", "2004-06-28T00:00:00+00:00",
                   field="field_completed_start_date")]
    problems = preflight(moves, expect=1)
    assert any("field_completed_start_date" in p and "period" in p for p in problems)


def test_an_undeclared_field_refuses():
    moves = [_move("2018-01-11T06:29:59+00:00", "2012-04-18T00:00:00+00:00",
                   field="field_invented_date")]
    problems = preflight(moves, expect=1)
    assert any("unknown" in p for p in problems)


def test_a_non_utc_value_refuses():
    """`state._to_datetime` normalises to naive UTC, so an IST-offset string
    would land a day early — the exact error being corrected."""
    moves = [_move("2018-01-11T06:29:59+00:00", "2012-04-18T00:00:00+05:30")]
    problems = preflight(moves, expect=1)
    assert any("UTC" in p for p in problems)


def test_several_objections_are_all_reported():
    """A partial list would mean fixing one problem to discover the next."""
    moves = [
        _move("2018-01-11T06:29:59+00:00", "2016-03-15T00:00:00+00:00",
              field="field_rpaper_year", precision="year"),
        _move("2018-01-11T06:29:59+00:00", "2012-04-18T00:00:00+05:30",
              field="field_completed_start_date"),
    ]
    assert len(preflight(moves, expect=99)) >= 3


def test_the_expected_count_matches_the_reviewed_dry_run():
    assert EXPECTED_MOVES == 1047


# --------------------------------------------------------------------------- #
# Scoping: PDFs must be unreachable
# --------------------------------------------------------------------------- #

def test_the_candidate_query_excludes_pdfs_in_sql():
    """Scoped in the query rather than filtered afterwards, so a PDF cannot
    reach the write path even if the classifier changed."""
    import inspect

    from scripts import backfill_source_dates

    sql = inspect.getsource(backfill_source_dates.candidates)
    assert "source_type = 'website'" in sql


def test_the_candidate_order_is_deterministic():
    """`--limit` selects a prefix, so an unordered query would apply a different
    subset than the one reviewed — a scoped trial would be unverifiable."""
    import inspect

    from scripts import backfill_source_dates

    assert "ORDER BY document_id" in inspect.getsource(backfill_source_dates.candidates)


def test_the_invariants_watch_the_pdf_dates():
    import inspect

    from scripts import backfill_source_dates

    src = inspect.getsource(backfill_source_dates.invariants)
    assert "source_type <> 'website'" in src
    assert "non_website_date_checksum" in src


def test_indexed_at_is_not_touched_by_the_update():
    """`indexed_at` means "was re-chunked and re-indexed", which has not
    happened — and `corpus_revision` reads MAX(indexed_at), so claiming it would
    be false *and* a silent cache invalidation."""
    import inspect

    from scripts import backfill_source_dates

    # Comment lines stripped: the reason `indexed_at` is excluded is written out
    # in a comment, and the assertion is about the statement, not the prose.
    code = "\n".join(
        line for line in inspect.getsource(backfill_source_dates.apply).splitlines()
        if not line.lstrip().startswith("#")
    )
    assert "updated_at = NOW()" in code
    assert "indexed_at" not in code


def test_the_precision_marker_goes_into_the_payload_with_the_date():
    """The bug this exists for: the first run of the year-precision backfill set
    `published_at` alone, so 389 documents carried 1 January with nothing saying
    it was a marker — and the answer layer would have reported an invented
    January publication for every one of them."""
    import inspect

    from scripts import backfill_source_dates

    src = inspect.getsource(backfill_source_dates.apply)
    assert 'payload["published_at_precision"] = "year"' in src
    assert 'if move.precision == "year"' in src


def test_no_precision_key_is_written_for_a_full_date():
    """Absent means "a full date", which keeps every existing point valid and
    this off the PAYLOAD version."""
    import inspect

    from scripts import backfill_source_dates

    src = inspect.getsource(backfill_source_dates.apply)
    assert '"published_at_precision": "day"' not in src
    assert '"published_at_precision": move.precision' not in src


def test_both_stores_are_written():
    """MySQL alone would be reverted by `app.ingestion.backfill`, which lifts
    published_at out of the chunk payloads and writes it back."""
    import inspect

    from scripts import backfill_source_dates

    src = inspect.getsource(backfill_source_dates.apply)
    assert "set_payload" in src
    assert "UPDATE" in src


# --------------------------------------------------------------------------- #
# Odds and ends
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("raw", [None, "", "not json", "[1,2]", 7])
def test_unreadable_metadata_is_an_empty_dict(raw):
    assert _metadata(raw) == {}


def test_metadata_parses_a_json_string_and_passes_a_dict_through():
    assert _metadata('{"a": 1}') == {"a": 1}
    assert _metadata({"a": 1}) == {"a": 1}


def test_the_report_survives_an_empty_move_list(capsys):
    """A second run after a successful apply moves nothing; it must print that
    rather than divide by zero."""
    report([])
    assert "0" in capsys.readouterr().out
