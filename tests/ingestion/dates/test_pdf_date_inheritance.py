"""An attached file carries its page's date. One file or twelve.

The bug this closes: the attachment path read ``node.created`` while the page's
own builder applied the bundle's configured field, so a research paper's page and
the PDF hanging off it were dated differently by construction. The page's
*resolved* date is now the one answer, resolved once and propagated.

What must stay impossible, and is tested here one signal at a time: the file's
Drupal upload stamp, its ``/files/YYYY-MM/`` path, its PDF ``CreationDate`` and
``ModDate``, a year in its filename and the ingestion clock may none of them set
a date. They are evidence about a file; the page states the date.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ingestion import date_resolution
from app.ingestion.bundle_dates import resolve_effective_dates
from app.ingestion.date_resolution import build_evidence
from app.ingestion.date_resolution import resolve as resolve_pdf

NODE_CREATED = "2018-01-11T06:29:59+00:00"
PAPER_YEAR = "2016-01-01T00:00:00+00:00"
PROJECT_START = "2020-01-02T00:00:00+00:00"
PROJECT_END = "2022-12-31T00:00:00+00:00"


def _project(**kwargs):
    """A completed_projects node — a bundle whose mapping declares both ends.

    The raw values are IST-midnight encoded, as the live CMS stores them, so the
    resolved dates are the next calendar day.
    """
    return _node(
        bundle="completed_projects",
        metadata={"field_completed_start_date": "2020-01-01T18:30:00+00:00",
                  "field_completed_end_date": "2022-12-30T18:30:00+00:00"},
        **kwargs,
    )


def _file(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        uuid=kwargs.pop("uuid", "f1"),
        url=kwargs.pop("url", "https://teriin.org/sites/default/files/a.pdf"),
        filename=kwargs.pop("filename", "a.pdf"),
        description=kwargs.pop("description", None),
        origin=kwargs.pop("origin", "attachment"),
        created=kwargs.pop("created", None),
        **kwargs,
    )


def _node(bundle="research_papers", metadata=None, files=None, **kwargs):
    return SimpleNamespace(
        uuid=kwargs.pop("uuid", "node-1"),
        title=kwargs.pop("title", "A research paper"),
        url=kwargs.pop("url", "https://teriin.org/research/x"),
        created=kwargs.pop("created", NODE_CREATED),
        bundle=bundle,
        metadata=metadata if metadata is not None else {"field_rpaper_year": 2016},
        files=files if files is not None else [_file()],
        refs=[],
        **kwargs,
    )


def _resolve_for(node, file, content=b"%PDF-"):
    parent = resolve_effective_dates(node.bundle, node.created, node.metadata)
    evidence = build_evidence(document_id=file.uuid, node=node, file=file,
                              parent_date=parent)
    return resolve_pdf(evidence, content)


# --------------------------------------------------------------------------- #
# Inheritance
# --------------------------------------------------------------------------- #

def test_a_page_with_one_pdf_hands_it_the_bundles_resolved_date():
    got = _resolve_for(_node(), _file())
    assert got.start_value == PAPER_YEAR
    assert got.start_value != NODE_CREATED, "the creation stamp is not the answer"


def test_a_page_with_no_pdf_is_simply_a_page():
    """Nothing to inherit; the page's own resolution is the whole story."""
    node = _node(files=[])
    assert resolve_effective_dates(node.bundle, node.created, node.metadata).start_value == PAPER_YEAR


@pytest.mark.parametrize("count", [2, 3, 12])
def test_every_pdf_on_a_page_gets_the_same_date(count):
    files = [_file(uuid=f"f{i}", filename=f"part-{i}.pdf") for i in range(count)]
    node = _node(files=files)
    dates = {_resolve_for(node, f).start_value for f in files}
    assert dates == {PAPER_YEAR}


def test_each_pdf_is_still_its_own_document_linked_to_the_parent():
    """Shared date, separate documents: the evidence keeps per-file identity and
    the page's identity alongside it."""
    files = [_file(uuid="fa", filename="a.pdf"), _file(uuid="fb", filename="b.pdf")]
    node = _node(files=files)
    evidence = [build_evidence(document_id=f.uuid, node=node, file=f) for f in files]
    assert [e.document_id for e in evidence] == ["fa", "fb"]
    assert [e.filename for e in evidence] == ["a.pdf", "b.pdf"]
    assert {e.page.node_uuid for e in evidence} == {"node-1"}
    assert {e.page.pdf_count for e in evidence} == {2}


def test_the_precision_is_inherited_too():
    """A file on a year-precision page is year-precision. Without this a reader
    renders its 1 January as a day and invents a January publication."""
    assert _resolve_for(_node(), _file()).start_precision == "year"


def test_a_page_falling_back_to_its_creation_stamp_hands_that_over():
    node = _node(bundle="article", metadata={})
    got = _resolve_for(node, _file())
    assert got.start_value == NODE_CREATED
    assert got.start_precision == "day"


def test_an_undated_page_hands_over_nothing_rather_than_inventing_a_date():
    node = _node(bundle="article", metadata={}, created=None)
    got = _resolve_for(node, _file())
    assert got.start_value is None


# --------------------------------------------------------------------------- #
# Ranges are inherited whole
# --------------------------------------------------------------------------- #

def test_a_pdf_on_a_range_page_inherits_both_ends():
    got = _resolve_for(_project(), _file())
    assert got.start_value == PROJECT_START
    assert got.end_value == PROJECT_END


@pytest.mark.parametrize("count", [1, 2, 3, 12])
def test_every_pdf_on_a_range_page_inherits_the_same_period(count):
    files = [_file(uuid=f"f{i}") for i in range(count)]
    node = _project(files=files)
    resolved = [_resolve_for(node, f) for f in files]
    assert {r.start_value for r in resolved} == {PROJECT_START}
    assert {r.end_value for r in resolved} == {PROJECT_END}


def test_a_pdf_on_a_single_date_page_gets_no_end():
    """Never manufactured: a research paper has no period, so neither does a
    file hanging off one."""
    got = _resolve_for(_node(), _file())
    assert got.end_value is None
    assert got.end_precision is None


def test_the_page_evidence_names_the_end_field_separately():
    evidence = build_evidence(document_id="f1", node=_project(), file=_file())
    assert evidence.page.date_field == "field_completed_start_date"
    assert evidence.page.end_date_field == "field_completed_end_date"
    assert evidence.page.node_end_date == PROJECT_END
    assert evidence.page.effective_end == PROJECT_END


def test_a_page_with_no_end_hands_over_no_end_rather_than_its_creation_stamp():
    """A creation stamp is a point, not a period."""
    evidence = build_evidence(document_id="f1", node=_node(), file=_file())
    assert evidence.page.effective_end is None


def test_an_inverted_page_range_hands_over_only_the_start():
    node = _node(
        bundle="completed_projects",
        metadata={"field_completed_start_date": "2022-12-30T18:30:00+00:00",
                  "field_completed_end_date": "2020-01-01T18:30:00+00:00"})
    got = _resolve_for(node, _file())
    assert got.start_value == PROJECT_END
    assert got.end_value is None


# --------------------------------------------------------------------------- #
# What must never set a date
# --------------------------------------------------------------------------- #

def test_a_late_upload_stamp_does_not_move_the_date():
    got = _resolve_for(_node(), _file(created="2024-06-01T00:00:00+00:00"))
    assert got.start_value == PAPER_YEAR


def test_an_upload_month_in_the_url_does_not_move_the_date():
    url = "https://teriin.org/sites/default/files/2024-06/a.pdf"
    got = _resolve_for(_node(), _file(url=url))
    assert got.start_value == PAPER_YEAR


def test_a_year_in_the_filename_does_not_move_the_date():
    got = _resolve_for(_node(), _file(filename="annual-review-2024.pdf"))
    assert got.start_value == PAPER_YEAR


def test_pdf_metadata_is_not_even_read_when_the_page_states_its_date(monkeypatch):
    """Not merely ignored — never fetched. DocInfo and the head text cost a parse,
    and there is nothing they could contribute to a settled case."""
    def _boom(*_a, **_k):
        raise AssertionError("PDF metadata must not be read")

    monkeypatch.setattr(date_resolution, "_read_pdf_signals", _boom)
    files = [_file(uuid=f"f{i}") for i in range(4)]
    node = _node(files=files)
    for file in files:
        assert _resolve_for(node, file).start_value == PAPER_YEAR


def test_the_model_is_never_asked_when_the_page_states_its_date(monkeypatch):
    monkeypatch.setattr("app.ingestion.date_llm.interpret",
                        lambda _e: pytest.fail("the model must not be called"))
    files = [_file(uuid=f"f{i}", created="2024-06-01T00:00:00+00:00")
             for i in range(3)]
    node = _node(files=files)
    for file in files:
        got = _resolve_for(node, file)
        assert got.start_value == PAPER_YEAR
        assert "llm" not in got.used


def test_the_upload_gap_is_measured_against_the_creation_stamp_not_the_date():
    """A completed project's page states 2004 and was typed in in 2017. Reading
    the effective date as the page's age would make every attachment look 13
    years late and route the whole bundle to the model."""
    node = _node(bundle="completed_projects",
                 metadata={"field_completed_start_date": "2004-06-28T18:30:00+00:00"})
    evidence = build_evidence(document_id="f1", node=node, file=_file())
    assert evidence.page.node_created == NODE_CREATED
    assert evidence.page.node_start_date.startswith("2004-06-29")
    assert evidence.page.effective_date.startswith("2004-06-29")


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #

def test_the_decision_records_the_chain_back_to_the_field():
    """"Why does this PDF have the date 2016?" has to be answerable from the
    stored row: because it hangs on this research_papers page, whose
    field_rpaper_year is 2016."""
    got = _resolve_for(_node(), _file())
    assert got.decision.rule == "parent_bundle_date_field"
    for expected in ("research_papers", "field_rpaper_year", "2016"):
        assert expected in got.decision.evidence


def test_the_decision_says_the_file_signals_were_not_read():
    got = _resolve_for(_node(), _file(created="2024-06-01T00:00:00+00:00"))
    assert "not read" in got.decision.supporting_evidence


def test_the_candidate_start_date_on_the_decision_is_the_date_actually_assigned():
    """The audit row would otherwise read "would have been <creation stamp>",
    which is not what was ever on the table."""
    got = _resolve_for(_node(), _file())
    assert got.decision.candidate_start_date == got.start_value


def test_the_evidence_carries_the_page_identity_for_the_audit_row():
    evidence = build_evidence(document_id="f1", node=_node(), file=_file())
    assert evidence.page.bundle == "research_papers"
    assert evidence.page.date_field == "field_rpaper_year"
    assert evidence.page.date_field_value == 2016
    assert evidence.page.date_source == "cms_field"
    assert evidence.page.date_from_bundle_field


def test_a_page_on_its_creation_stamp_is_not_claimed_as_a_field_date():
    evidence = build_evidence(document_id="f1",
                              node=_node(bundle="article", metadata={}),
                              file=_file())
    assert not evidence.page.date_from_bundle_field
    assert evidence.page.date_source == "created"


# --------------------------------------------------------------------------- #
# Through the real builder
# --------------------------------------------------------------------------- #

class _FakePage:
    page_number = 1
    text = "PDF body text."


class _FakePdfResult:
    source = "a.pdf"
    pages = [_FakePage()]


def _build(monkeypatch, node, file):
    from app.ingestion.extractors import attachment, pdf_extractor

    monkeypatch.setattr(attachment, "fetch_attachment",
                        lambda s, url, t: (b"%PDF-", url))
    monkeypatch.setattr(pdf_extractor, "extract_pdf",
                        lambda content, name: _FakePdfResult())
    recorded: list = []
    monkeypatch.setattr("app.catalog.date_decisions.ensure_table", lambda: None)
    monkeypatch.setattr("app.catalog.date_decisions.record", recorded.append)
    record = SimpleNamespace(document_id=file.uuid, source_type="pdf_attachment",
                             payload=(node, file), fingerprint="fp")
    return attachment.build_attachment_doc(record, session=None), recorded


def test_the_built_document_carries_the_page_date_and_says_so(monkeypatch):
    doc, _ = _build(monkeypatch, _node(), _file())
    assert doc.effective_start_date == PAPER_YEAR
    assert doc.date_source == "parent_page"
    assert doc.start_precision == "year"
    assert doc.effective_end_date is None


def test_the_built_document_carries_the_inherited_period(monkeypatch):
    doc, recorded = _build(monkeypatch, _project(), _file())
    assert doc.effective_start_date == PROJECT_START
    assert doc.effective_end_date == PROJECT_END
    assert doc.end_precision == "day"
    assert doc.date_source == "parent_page"
    assert recorded[0].candidate_end_date == PROJECT_END


def test_the_audit_row_names_both_fields_and_both_values(monkeypatch):
    """Not collapsed into one ambiguous string: "why does this run to 2022?" is
    a different question from "why does it start in 2020"."""
    _, recorded = _build(monkeypatch, _project(), _file())
    evidence = recorded[0].evidence
    assert "field_completed_start_date" in evidence
    assert "field_completed_end_date" in evidence
    assert "2022-12-31" in evidence


def test_the_built_document_links_back_to_its_page(monkeypatch):
    node = _node()
    doc, _ = _build(monkeypatch, node, _file())
    assert doc.linked_article_uuid == node.uuid
    assert doc.source_url == node.url
    assert doc.extra["bundle"] == "research_papers"


def test_every_pdf_on_a_page_is_built_with_the_same_date(monkeypatch):
    files = [_file(uuid="fa", filename="a.pdf"),
             _file(uuid="fb", filename="b.pdf", created="2024-06-01T00:00:00+00:00"),
             _file(uuid="fc", filename="c-2024.pdf")]
    node = _node(files=files)
    docs = [_build(monkeypatch, node, f)[0] for f in files]
    assert {d.effective_start_date for d in docs} == {PAPER_YEAR}
    assert {d.document_id for d in docs} == {"fa", "fb", "fc"}


def test_the_audit_row_explains_the_inheritance(monkeypatch):
    node = _node()
    _, recorded = _build(monkeypatch, node, _file())
    assert len(recorded) == 1
    evidence = recorded[0].evidence
    assert "Inherited from" in evidence
    assert node.title in evidence and node.url in evidence
    assert "field_rpaper_year" in evidence and "2016" in evidence
    assert recorded[0].current_start_date == PAPER_YEAR


def test_the_document_carries_the_evidence_for_the_catalog(monkeypatch):
    doc, _ = _build(monkeypatch, _node(), _file())
    assert doc.date_evidence.source == "parent_page"
    assert doc.date_evidence.start_field == "field_rpaper_year"
    assert doc.date_evidence.bundle == "research_papers"


def test_turning_the_resolver_off_degrades_to_plain_inheritance(monkeypatch):
    """Not to the creation stamp: with the feature off a file still carries its
    page's date, which is now the resolved one."""
    from app.config import get_settings
    from app.ingestion.extractors import attachment

    monkeypatch.setattr(get_settings(), "date_resolution_enabled", False)
    monkeypatch.setattr("app.ingestion.date_resolution.resolve",
                        lambda *_a, **_k: pytest.fail("resolver must not run"))
    node = _node()
    got = attachment._resolve_date(
        SimpleNamespace(document_id="f1"), node, _file(), b"%PDF-",
        attachment.resolve_parent_date(node))
    assert got.start_value == PAPER_YEAR
    assert got.start_precision == "year"
