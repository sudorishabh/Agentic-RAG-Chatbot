"""``document_published_at`` is the date a document states about itself.

``published_at`` keeps its meaning unchanged: the source/web-page publication
date, and the field every chronology, filter and ranking path uses. The new
column is NULL unless the document itself states a date — never derived from an
edition label, a PDF CreationDate, a cover month-year, an upload time or a URL
path.

All ten TERI annual reports are NULL because an audit of their front and back
matter found no publication statement in any of them
(``reports/phase0/annual_report_date_audit.md``).
"""

from __future__ import annotations

import pytest

from app.catalog.models import StateRecord
from app.core.models import CanonicalDocument
from app.core.models.context import ContextBlock
from app.generation.date_claims import verify_date_claims
from app.generation.prompts import _source_hint
from app.ingestion.chunking.models import DocumentMeta
from app.ingestion.chunking.payload import build_payload
from app.ingestion.date_resolution import ResolvedDate

PAGE_DATE = "2022-02-09T06:59:06+00:00"
STATED = "2024-09-12T00:00:00+00:00"


def _annual_payload(document_published_at: str | None = None) -> dict:
    return {
        "source_type": "pdf_attachment",
        "title": "Annual Report 2024-2025",
        "edition_label": "2024-25",
        "published_at": PAGE_DATE,
        "document_published_at": document_published_at,
        "page_number": 3,
    }


# --------------------------------------------------------------------------- #
# 1. The annual reports: page date kept, document date NULL
# --------------------------------------------------------------------------- #

def test_an_annual_report_keeps_its_page_date_and_states_no_document_date():
    record = StateRecord(
        document_id="inbody:592d62f0", source_type="pdf_attachment",
        source_key="https://teriin.org/files/TERI-Annual-Report-2024-25.pdf",
        fingerprint="fp", published_at=PAGE_DATE, document_published_at=None,
        title="Annual Report 2024-2025",
    )
    assert record.published_at == PAGE_DATE
    assert record.document_published_at is None


def test_the_field_defaults_to_none_everywhere_it_is_carried():
    """Nothing populates it by accident: every carrier defaults to NULL."""
    assert CanonicalDocument(document_id="d", source_type="website").document_published_at is None
    assert DocumentMeta(document_id="d", source_type="website").document_published_at is None
    assert StateRecord(document_id="d", source_type="s", source_key="k",
                       fingerprint="f").document_published_at is None
    assert ResolvedDate(published_at=PAGE_DATE).document_published_at is None


def test_the_annual_report_header_reports_the_distinction():
    header = _source_hint(_annual_payload())
    assert "page published 2022-02-09" in header
    assert "document published: not stated" in header


def test_a_null_document_date_never_renders_as_a_date():
    header = _source_hint(_annual_payload(None))
    assert "document published: not stated" in header
    # The edition must not be smuggled in as the document date.
    assert "document published: 2024" not in header


# --------------------------------------------------------------------------- #
# 2. A future document that does state its publication date
# --------------------------------------------------------------------------- #

def test_a_stated_publication_date_populates_the_new_field_only():
    """The capability this column exists for, with `published_at` untouched."""
    doc = CanonicalDocument(
        document_id="d1", source_type="pdf_attachment",
        published_at=PAGE_DATE, document_published_at=STATED)
    assert doc.published_at == PAGE_DATE
    assert doc.document_published_at == STATED


def test_a_stated_date_reaches_the_chunk_payload():
    meta = DocumentMeta(document_id="d1", source_type="pdf_attachment",
                        published_at=PAGE_DATE, document_published_at=STATED)
    from app.ingestion.chunking.models import Chunk

    payload = build_payload(
        Chunk(chunk_id="c1", text="x", is_parent=False, meta=meta))
    assert payload["published_at"] == PAGE_DATE
    assert payload["document_published_at"] == STATED


def test_a_stated_date_shows_in_the_header_beside_the_page_date():
    header = _source_hint(_annual_payload("2025-11-21T00:00:00+00:00"))
    assert "page published 2022-02-09" in header
    assert "document published: 2025-11-21" in header


def test_the_resolver_can_carry_a_stated_date_without_touching_the_page_date():
    resolved = ResolvedDate(published_at=PAGE_DATE, document_published_at=STATED,
                            edition_label="2024-25")
    assert resolved.published_at == PAGE_DATE
    assert resolved.document_published_at == STATED


# --------------------------------------------------------------------------- #
# 3. A missing resolver value must not erase a stored one
# --------------------------------------------------------------------------- #

def test_the_upsert_coalesces_the_document_date():
    """A path that does not resolve a document date passes NULL. The statement
    must keep the stored value rather than overwriting it — unlike
    ``published_at``, which is authoritative on every write."""
    import inspect

    from app.catalog import state

    sql = inspect.getsource(state.upsert)
    assert "document_published_at = COALESCE(VALUES(document_published_at)," in sql
    # published_at deliberately does NOT coalesce; the contrast is the point.
    assert "published_at = VALUES(published_at)," in sql


def test_the_backfill_allowlist_cannot_reach_the_new_column():
    """`backfill.collect` lifts payload fields back into the catalog. Omitting
    the column from its allowlist is what stops it reverting a stored value."""
    from app.ingestion.backfill import _PAYLOAD_FIELDS

    assert "published_at" in _PAYLOAD_FIELDS
    assert "document_published_at" not in _PAYLOAD_FIELDS


def test_backfill_facets_writes_a_fixed_column_list():
    """The other revert path: a fixed UPDATE, so an absent column is untouched."""
    import inspect

    from app.catalog import state

    sql = inspect.getsource(state.backfill_facets)
    assert "SET published_at = %s" in sql
    assert "document_published_at" not in sql


def test_reconcile_does_not_scroll_the_new_column():
    """Nothing to compare means no spurious drift report."""
    from app.ingestion.reconcile import _SCROLL_FIELDS

    assert "published_at" in _SCROLL_FIELDS
    assert "document_published_at" not in _SCROLL_FIELDS


# --------------------------------------------------------------------------- #
# 4. The guard stays anchored to the page date
# --------------------------------------------------------------------------- #

def _blocks(document_published_at: str | None = None) -> list[ContextBlock]:
    return [ContextBlock(n=3, text="", payload=_annual_payload(document_published_at))]


def test_the_page_date_is_still_the_forbidden_one():
    answer = "The 2024-25 annual report was published on 2022-02-09 [3]."
    assert not verify_date_claims(answer, _blocks()).clean


def test_a_stated_document_date_is_permitted_as_the_publication_date():
    """The inversion this must never make: the document date is the legitimate
    answer, so quoting it must not be flagged."""
    blocks = _blocks("2025-11-21T00:00:00+00:00")
    answer = "The 2024-25 annual report was published on 2025-11-21 [3]."
    assert verify_date_claims(answer, blocks).clean


def test_the_page_date_stays_forbidden_even_when_a_document_date_exists():
    blocks = _blocks("2025-11-21T00:00:00+00:00")
    answer = "The 2024-25 annual report was published on 9 February 2022 [3]."
    report = verify_date_claims(answer, blocks)
    assert not report.clean
    assert report.offenders[0].claimed_date.isoformat() == "2022-02-09"


def test_the_guard_reads_only_the_page_date_field():
    """A block with a document date and NO page date yields nothing to forbid."""
    blocks = [ContextBlock(n=3, text="", payload={
        "source_type": "pdf_attachment", "title": "Annual Report 2024-2025",
        "edition_label": "2024-25", "published_at": None,
        "document_published_at": "2025-11-21T00:00:00+00:00",
    })]
    answer = "The report was published on 2025-11-21 [3]."
    assert verify_date_claims(answer, blocks).clean


# --------------------------------------------------------------------------- #
# 5. Non-annual-report behaviour is unchanged
# --------------------------------------------------------------------------- #

def test_a_website_page_header_is_byte_identical_to_before():
    header = _source_hint({
        "source_type": "website", "title": "TERI launches report",
        "published_at": "2024-05-01T00:00:00",
    })
    assert header == "website · TERI launches report · page published 2024-05-01T00:00:00"


def test_a_pdf_without_an_edition_gains_no_document_date_line():
    header = _source_hint({
        "source_type": "pdf_attachment", "title": "Some report",
        "published_at": "2020-01-01T00:00:00", "page_number": 2,
    })
    assert "document published" not in header
    assert "page published 2020-01-01" in header


def test_a_payload_without_the_field_still_builds():
    """Existing chunks predate the column; their payloads must not break."""
    meta = DocumentMeta(document_id="d1", source_type="pdf_attachment",
                        published_at="2020-01-01T00:00:00")
    from app.ingestion.chunking.models import Chunk

    payload = build_payload(
        Chunk(chunk_id="c1", text="x", is_parent=False, meta=meta))
    # build_payload drops empty values, so a NULL document date is simply absent.
    assert payload["published_at"] == "2020-01-01T00:00:00"
    assert "document_published_at" not in payload


@pytest.mark.parametrize(
    "payload",
    [
        {"source_type": "website", "title": "News", "published_at": "2023-01-01T00:00:00"},
        {"source_type": "pdf_attachment", "title": "Brief",
         "published_at": "2019-06-01T00:00:00"},
    ],
)
def test_documents_with_no_edition_are_untouched_by_the_guard(payload):
    blocks = [ContextBlock(n=1, text="", payload=payload)]
    date = str(payload["published_at"])[:10]
    assert verify_date_claims(f"The report was published on {date} [1].", blocks).clean
