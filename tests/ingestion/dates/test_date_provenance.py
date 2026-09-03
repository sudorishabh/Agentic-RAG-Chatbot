"""``date_source`` and ``start_precision``: where the date came
from, and how precise it is.

Everything ranks, filters and orders on ``effective_start_date``, and until these
columns existed a bare value could not be told apart from a placeholder — an
import timestamp shared by 646 documents read exactly like a date the publisher
stated. These record the difference.

The invariant that shapes every test below: **provenance must never outlive the
value it describes.** A stale ``date_source`` is worse than none,
because it reads as evidence for a date it was never about. So every path that
overwrites ``effective_start_date`` must either carry the provenance with it or clear it.
"""

from __future__ import annotations

import inspect

import pytest

from app.catalog.models import StateRecord
from app.core.models import CanonicalDocument


# --------------------------------------------------------------------------- #
# 1. The carriers default to "not recorded"
# --------------------------------------------------------------------------- #

def test_nothing_populates_the_columns_by_accident():
    """NULL means *not recorded*, and every carrier has to start there — a
    default of "created" would be a claim, and for the four PDFs dated from a
    verified publication statement it would be a false one."""
    doc = CanonicalDocument(document_id="d", source_type="website")
    assert doc.date_source is None
    assert doc.start_precision is None

    record = StateRecord(document_id="d", source_type="s", source_key="k",
                         fingerprint="f")
    assert record.date_source is None
    assert record.start_precision is None


def test_the_columns_can_carry_a_value_through_both_models():
    doc = CanonicalDocument(
        document_id="d", source_type="website",
        effective_start_date="2012-04-18T00:00:00", date_source="cms_field",
        start_precision="day",
    )
    assert (doc.date_source, doc.start_precision) == ("cms_field", "day")


# --------------------------------------------------------------------------- #
# 2. Provenance is written with its value, not coalesced
# --------------------------------------------------------------------------- #

def test_the_upsert_overwrites_provenance_rather_than_coalescing_it():
    """Provenance is written with the value it describes, never coalesced.

    ``date_source``, ``start_precision`` and ``end_precision`` all describe
    ``effective_start_date`` / ``effective_end_date``, which are themselves
    overwritten outright on every write. Coalescing any of them would let a new
    date inherit an old date's provenance — evidence for a value it was never
    about, which is worse than no evidence at all.
    """
    from app.catalog import state

    sql = inspect.getsource(state.upsert)
    for clause in (
        "effective_start_date = VALUES(effective_start_date),",
        "date_source    = VALUES(date_source),",
        "start_precision = VALUES(start_precision),",
        "effective_end_date           = VALUES(effective_end_date),",
        "end_precision = VALUES(end_precision),",
    ):
        assert clause in sql, clause
    assert "COALESCE(VALUES(effective_start_date)" not in sql
    assert "COALESCE(VALUES(date_source)" not in sql


def test_the_insert_and_the_placeholders_agree():
    """A column list and a %s count that disagree is a runtime error on the
    first real write, not a test failure — so it is counted here."""
    from app.catalog import state

    sql = inspect.getsource(state.upsert)
    insert = sql.split("INSERT INTO", 1)[1].split("ON DUPLICATE KEY", 1)[0]
    columns = insert.split("(", 1)[1].split(")", 1)[0]
    names = [c.strip() for c in columns.replace("\n", " ").split(",") if c.strip()]
    placeholders = insert.split("VALUES", 1)[1].count("%s")
    assert "date_source" in names
    assert "start_precision" in names
    assert len(names) == placeholders, f"{len(names)} columns vs {placeholders} params"


def test_the_pipeline_passes_provenance_into_the_catalog_row():
    from app.ingestion import pipeline

    sql = inspect.getsource(pipeline._save_state)
    assert "date_source=doc.date_source" in sql
    assert "start_precision=doc.start_precision" in sql


def test_the_reader_returns_provenance_from_a_row():
    from app.catalog.state import _row_to_record

    record = _row_to_record({
        "document_id": "d", "source_type": "website", "source_key": "k",
        "fingerprint": "f", "date_source": "cms_field",
        "start_precision": "year",
    })
    assert record.date_source == "cms_field"
    assert record.start_precision == "year"


def test_the_reader_tolerates_a_row_from_before_the_columns_existed():
    """`load()` selects *, so a legacy row simply lacks the keys."""
    from app.catalog.state import _row_to_record

    record = _row_to_record({
        "document_id": "d", "source_type": "website", "source_key": "k",
        "fingerprint": "f",
    })
    assert record.date_source is None
    assert record.start_precision is None


# --------------------------------------------------------------------------- #
# 3. The revert paths — the ones that would desync value from provenance
# --------------------------------------------------------------------------- #

def test_the_payload_lift_clears_provenance_when_it_overwrites_the_date():
    """`backfill.collect` reads ``effective_start_date`` out of chunk payloads and
    `backfill_facets` writes it with a bare SET. The payload carries the value
    and not its origin, so the honest record afterwards is "unknown"."""
    from app.catalog import state

    sql = inspect.getsource(state.backfill_facets)
    assert "SET effective_start_date = %s" in sql
    assert "date_source = NULL" in sql
    assert "start_precision = NULL" in sql


def test_the_payload_lift_cannot_read_provenance_back_in():
    """The columns are not payload fields, so nothing can restore them from
    Qdrant — which is why clearing them is the only correct option above."""
    from app.ingestion.backfill import _PAYLOAD_FIELDS

    assert "effective_start_date" in _PAYLOAD_FIELDS
    assert "date_source" not in _PAYLOAD_FIELDS
    assert "start_precision" not in _PAYLOAD_FIELDS


def test_the_columns_stay_out_of_the_chunk_payload():
    """Provenance is an audit fact, not something retrieval reads, so it stays
    in MySQL. A payload key is replicated once per chunk.

    PAYLOAD is 2 because the date keys were *renamed* — old points carry keys no
    reader consults — not because anything was added. Adding `date_source` here
    would be a third reason, and an unnecessary one."""
    from app.ingestion.chunking.models import Chunk, DocumentMeta
    from app.ingestion.chunking.payload import build_payload

    meta = DocumentMeta(document_id="d", source_type="website",
                        effective_start_date="2012-04-18T00:00:00")
    payload = build_payload(Chunk(chunk_id="c", text="x", is_parent=False, meta=meta))
    assert payload["effective_start_date"] == "2012-04-18T00:00:00"
    assert "date_source" not in payload
    assert "start_precision" not in payload


def test_reconcile_does_not_scroll_the_new_columns():
    from app.ingestion.reconcile import _SCROLL_FIELDS

    assert "effective_start_date" in _SCROLL_FIELDS
    assert "date_source" not in _SCROLL_FIELDS
    assert "start_precision" not in _SCROLL_FIELDS


# --------------------------------------------------------------------------- #
# 4. The vocabulary the columns accept
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("source", ["created", "cms_field", "document_text"])
def test_the_documented_sources_fit_the_column(source):
    """VARCHAR(16); a value that would be silently truncated is a wrong value."""
    assert len(source) <= 16


@pytest.mark.parametrize("precision", ["year", "month", "day"])
def test_the_documented_precisions_fit_the_column(precision):
    assert len(precision) <= 8


def test_the_precisions_match_what_the_classifier_emits():
    """The classifier is the only producer of these values, so its vocabulary
    and the column's have to be the same set."""
    from app.ingestion.source_dates import FIELD_ROLES

    emitted = {precision for _, precision in FIELD_ROLES.values()}
    assert emitted <= {"year", "month", "day"}
