"""Recording where each existing ``effective_start_date`` came from.

Every value this writes has to be *derived*, not assumed — the whole reason the
column was left NULL rather than blanket-stamped ``created`` is that ``created``
is false for the four PDFs dated from a publication statement quoted out of the
document. So the tests below are about the derivation: which rows each class
claims, which it must not, and that it cannot move a date.
"""

from __future__ import annotations

import inspect

from scripts import backfill_date_provenance as backfill
from scripts.backfill_date_provenance import CLASSES


def _clause(source: str, fragment: str) -> str:
    for src, _precision, _description, clause in CLASSES:
        if src == source and fragment in clause:
            return clause
    raise AssertionError(f"no {source!r} class whose clause mentions {fragment!r}")


# --------------------------------------------------------------------------- #
# What the classes claim
# --------------------------------------------------------------------------- #

def test_the_three_classes_cover_the_three_possible_origins():
    assert [src for src, *_ in CLASSES] == ["created", "document_text", "created"]


def test_every_class_writes_a_documented_source_value():
    """The column is VARCHAR(16) and the schema comment names three values."""
    for source, _precision, _description, _clause in CLASSES:
        assert source in ("created", "cms_field", "document_text")
        assert len(source) <= 16


def test_every_class_writes_a_documented_precision():
    for _source, precision, _description, _clause in CLASSES:
        assert precision in ("year", "month", "day")
        assert len(precision) <= 8


def test_no_class_can_overwrite_a_recorded_value():
    """Every clause requires NULL, so the 1,047 rows already stamped
    ``cms_field`` are untouchable and the script is a safe no-op on re-run."""
    for _source, _precision, _description, clause in CLASSES:
        assert "date_source IS NULL" in clause


def test_the_website_class_cannot_reach_an_attachment():
    assert "d.source_type = 'website'" in _clause("created", "website")


def test_the_attachment_classes_cannot_reach_a_website_document():
    assert "d.source_type <> 'website'" in _clause("document_text", "propose_override")
    assert "d.source_type <> 'website'" in _clause("created", "dd.action <> ")


def test_document_text_is_claimed_only_for_a_verified_override():
    """`propose_override` is granted only for a publication statement quoted
    from the PDF and verified against its own text. Anything looser here would
    put a claim on a date that was never made."""
    clause = _clause("document_text", "propose_override")
    assert "dd.action = 'propose_override'" in clause


def test_an_attachment_that_kept_its_page_date_is_created_not_document_text():
    clause = _clause("created", "dd.action <> ")
    assert "dd.action <> 'propose_override'" in clause
    assert "dd.document_id IS NOT NULL" in clause


def test_an_attachment_with_no_decision_row_is_claimed_by_nothing():
    """Its origin is genuinely unknown, so it stays NULL. Both attachment
    clauses require a decision row; neither can pick it up."""
    for source, fragment in (("document_text", "propose_override"),
                             ("created", "dd.action <> ")):
        clause = _clause(source, fragment)
        assert "dd." in clause, "an attachment class must depend on the decision row"


def test_the_classes_are_mutually_exclusive_on_action():
    """A PDF cannot satisfy both attachment clauses, so no row is stamped twice
    with different values depending on execution order."""
    override = _clause("document_text", "propose_override")
    kept = _clause("created", "dd.action <> ")
    assert "= 'propose_override'" in override
    assert "<> 'propose_override'" in kept


# --------------------------------------------------------------------------- #
# It must not move a date
# --------------------------------------------------------------------------- #

def test_no_class_touches_effective_start_date():
    src = inspect.getsource(backfill.main)
    assert "SET d.date_source" in src
    assert "SET d.effective_start_date =" not in src
    assert "effective_start_date = %s" not in src


def test_the_date_checksum_is_asserted_over_the_whole_corpus():
    """Not just the rows touched — a date moving anywhere would be a bug in a
    script whose whole claim is that it moves none."""
    src = inspect.getsource(backfill._date_checksum)
    assert "ORDER BY document_id" in src
    assert "WHERE" not in src.upper().split("SELECT")[1].split("ORDER BY")[0]


def test_a_changed_checksum_fails_the_run():
    src = inspect.getsource(backfill.main)
    assert "A date moved" in src
    assert "return 1" in src


def test_updated_at_is_not_moved():
    """No fact about the document changed — only what we recorded about our own
    knowledge of it. Moving updated_at would misreport that as an edit."""
    code = "\n".join(line for line in inspect.getsource(backfill.main).splitlines()
                     if not line.lstrip().startswith("#"))
    assert "updated_at" not in code


def test_nothing_is_written_to_qdrant():
    """Provenance is deliberately not a payload field — putting it there would
    be a PAYLOAD version bump and a full corpus reprocess."""
    src = inspect.getsource(backfill)
    assert "set_payload" not in src
    assert "qdrant" not in src.lower().replace("no qdrant", "")


def test_the_cache_is_left_alone():
    """No date and no payload changed, so no cached answer can be stale — unlike
    the source-date backfill, which must drop it."""
    src = inspect.getsource(backfill.main)
    assert "delete_collection" not in src
    assert "semantic cache is left alone" in src


# --------------------------------------------------------------------------- #
# Labels that disagree with what ingestion would write
# --------------------------------------------------------------------------- #

def test_the_relabel_pass_asks_the_same_function_ingestion_asks():
    """It cannot be a SQL clause: whether the source states a date depends on a
    field inside the raw_meta JSON, on an Asia/Kolkata conversion, and on the
    year-precision rule. Re-deriving any of that here would be a fourth copy of
    a decision that has already drifted twice."""
    src = inspect.getsource(backfill.stale_labels)
    assert "resolve_effective_dates" in src
    assert "publication_date" not in src


def test_a_row_is_only_relabelled_when_the_date_does_not_move():
    """The safety property the whole run rests on. A row whose *date* disagrees
    is the source-date backfill's job, so this leaves it alone — one script
    cannot quietly do the other's work."""
    src = inspect.getsource(backfill.stale_labels)
    assert 'value[:10] != stored.date().isoformat()' in src
    assert "continue" in src


def test_the_relabel_pass_skips_rows_already_correct():
    """Idempotence: a second run must find nothing."""
    src = inspect.getsource(backfill.stale_labels)
    assert '(row["date_source"], row["start_precision"]) == (source, precision)' \
        in src


def test_only_website_rows_are_considered():
    """An attachment's provenance comes from its decision row, not from a CMS
    field it does not have."""
    src = inspect.getsource(backfill.stale_labels)
    assert "source_type = 'website'" in src


def test_the_relabel_writes_only_the_two_provenance_columns():
    src = inspect.getsource(backfill.main)
    assert "SET date_source = %s, " in src
    assert "start_precision = %s WHERE document_id = %s" in src


def test_the_relabel_is_covered_by_the_date_checksum():
    """It runs inside the same transaction the checksum brackets, so a date
    moving during it fails the run like any other."""
    src = inspect.getsource(backfill.main)
    before_commit = src.split("conn.commit()")[0]
    assert "stale" in before_commit
    assert "_date_checksum" in src.split("stale = ")[0] or "_date_checksum" in src


# --------------------------------------------------------------------------- #
# Dry run
# --------------------------------------------------------------------------- #

def test_the_dry_run_returns_before_any_update():
    src = inspect.getsource(backfill.main)
    before_updates = src.split("for source, precision, _description, clause in CLASSES")[0]
    assert "No changes written" in before_updates
    assert "return 0" in before_updates
