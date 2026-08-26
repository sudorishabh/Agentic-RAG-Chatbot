"""Tests for the canonical resolver: :func:`app.ingestion.date_resolution.resolve`.

These cover the orchestration — routing, the re-check after reading the PDF, the
mapping of a model verdict onto a date, and the fail-closed guarantee. The rules
themselves are covered by ``tests/test_date_resolution.py``.

The property every test here defends: ``published_at`` moves only on an
override, and everything else lands on the page's own date.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ingestion import date_resolution
from app.ingestion.date_llm import DateInterpretation
from app.ingestion.date_resolution import build_evidence, resolve

NODE_DATE = "2020-01-10T00:00:00+00:00"


def _node(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        uuid=kwargs.pop("uuid", "node-1"),
        title=kwargs.pop("title", "A page"),
        url=kwargs.pop("url", "https://teriin.org/page"),
        created=kwargs.pop("created", NODE_DATE),
        bundle=kwargs.pop("bundle", "page"),
        files=kwargs.pop("files", []),
        **kwargs,
    )


def _file(**kwargs) -> SimpleNamespace:
    return SimpleNamespace(
        uuid=kwargs.pop("uuid", "f1"),
        url=kwargs.pop("url", "https://teriin.org/a.pdf"),
        filename=kwargs.pop("filename", "a.pdf"),
        description=kwargs.pop("description", None),
        origin=kwargs.pop("origin", "attachment"),
        created=kwargs.pop("created", None),
        **kwargs,
    )


def _evidence(node=None, file=None, count=None):
    return build_evidence(document_id="d1", node=node or _node(),
                          file=file or _file(), page_pdf_count=count)


# --------------------------------------------------------------------------- #
# Evidence adaptation
# --------------------------------------------------------------------------- #

def test_page_pdf_count_defaults_to_the_nodes_file_count():
    node = _node(files=[_file(), _file(uuid="f2"), _file(uuid="f3")])
    assert _evidence(node=node).page.pdf_count == 3


def test_a_node_with_no_files_still_counts_as_one_pdf():
    assert _evidence(node=_node(files=[])).page.pdf_count == 1


def test_the_file_description_is_carried_as_anchor_text():
    evidence = _evidence(file=_file(description="Annual Report 2021-2022"))
    assert evidence.edition == "2021-22"


# --------------------------------------------------------------------------- #
# The default: the page's date
# --------------------------------------------------------------------------- #

def test_a_single_pdf_page_keeps_the_page_date_without_reading_the_pdf(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("the PDF must not be read for a settled case")

    monkeypatch.setattr(date_resolution, "_read_pdf_signals", _boom)
    got = resolve(_evidence(), content=b"%PDF-")
    assert got.published_at == NODE_DATE
    assert got.overridden is False
    assert got.decision.rule == "single_pdf_page"
    assert "llm" not in got.used


def test_a_late_upload_does_not_move_the_date(monkeypatch):
    """Routed for a look. Even if the model claims a publication date, an empty
    document cannot ground it, so the page date stands.

    The routed path deliberately still asks when the text is unreadable — the
    validated run made 315 calls against 122 fetch failures — because grounding,
    not routing, is what prevents the override.
    """
    monkeypatch.setattr(date_resolution, "_read_pdf_signals", lambda *_a, **_k: None)
    verdict = DateInterpretation(
        candidate_date="2024-06-01", date_type="publication",
        publication_statement="Published on 1 June 2024",
        confidence=0.99, recommended_action="override")
    verdict.set_grounded(False, False)          # nothing readable to ground against
    monkeypatch.setattr("app.ingestion.date_llm.interpret", lambda _e: verdict)
    node = _node(files=[_file(), _file(uuid="f2")])
    file = _file(created="2024-06-01T00:00:00+00:00")
    got = resolve(_evidence(node=node, file=file), content=b"%PDF-")
    assert got.published_at == NODE_DATE
    assert got.overridden is False
    assert got.needs_review is True


# --------------------------------------------------------------------------- #
# Overrides: only a surviving verdict moves the date
# --------------------------------------------------------------------------- #

def _route_to_llm(monkeypatch, head_text: str, verdict: DateInterpretation | None):
    """Force the routed path with a given PDF text and model verdict."""
    def _fill(evidence, _content):
        evidence.head_text = head_text
        evidence.pdf_created = "2024-01-01T00:00:00+00:00"

    monkeypatch.setattr(date_resolution, "_read_pdf_signals", _fill)
    if verdict is not None:
        verdict.set_grounded(
            *_grounding(verdict, head_text)
        )
    monkeypatch.setattr("app.ingestion.date_llm.interpret", lambda _e: verdict)


def _grounding(verdict: DateInterpretation, text: str) -> tuple[bool, bool]:
    from app.ingestion.date_llm import date_is_in_text, statement_is_in_text

    return (date_is_in_text(verdict.candidate_date, text),
            statement_is_in_text(verdict.publication_statement, text))


def _routed_evidence():
    """A multi-PDF page whose file date diverges — the routed shape."""
    node = _node(files=[_file(), _file(uuid="f2"), _file(uuid="f3")])
    return _evidence(node=node, file=_file(created="2024-06-01T00:00:00+00:00"))


def test_a_grounded_publication_statement_moves_the_date(monkeypatch):
    text = "Press Release New Delhi, 31 March 2025 TERI announces findings"
    _route_to_llm(monkeypatch, text, DateInterpretation(
        candidate_date="2025-03-31", date_type="publication",
        publication_statement="New Delhi, 31 March 2025",
        confidence=0.95, recommended_action="override"))
    got = resolve(_routed_evidence(), content=b"%PDF-")
    assert got.published_at == "2025-03-31"
    assert got.overridden is True
    assert got.decision.source == "llm_publication"
    assert "llm" in got.used


def test_a_reconstructed_statement_does_not_move_the_date(monkeypatch):
    """The Pioneer failure: the date is in the text, the statement is not."""
    _route_to_llm(monkeypatch, "12/24/13 The Pioneer", DateInterpretation(
        candidate_date="2013-12-24", date_type="publication",
        publication_statement="The Pioneer, Tuesday, December 24, 2013",
        confidence=0.95, recommended_action="override"))
    got = resolve(_routed_evidence(), content=b"%PDF-")
    assert got.published_at == NODE_DATE
    assert got.overridden is False
    assert got.needs_review is True


def test_a_notification_verdict_does_not_move_the_date(monkeypatch):
    _route_to_llm(monkeypatch, "Notified on 18.05.2023 by the Ministry.",
                  DateInterpretation(
                      candidate_date="2023-05-18", date_type="notification",
                      publication_statement="Notified on 18.05.2023",
                      confidence=0.99, recommended_action="override"))
    got = resolve(_routed_evidence(), content=b"%PDF-")
    assert got.published_at == NODE_DATE
    assert got.decision.date_type == "notification"


def test_an_edition_verdict_yields_a_label_and_keeps_the_date(monkeypatch):
    _route_to_llm(monkeypatch, "ANNUAL REPORT 2024/25 Vision", DateInterpretation(
        candidate_date=None, date_type="edition", edition_label="2024-2025",
        confidence=0.99, recommended_action="keep_page_date"))
    got = resolve(_routed_evidence(), content=b"%PDF-")
    assert got.published_at == NODE_DATE
    assert got.edition_label == "2024-2025"
    assert got.overridden is False


def test_a_model_outage_keeps_the_page_date(monkeypatch):
    _route_to_llm(monkeypatch, "some readable text 2024", None)
    got = resolve(_routed_evidence(), content=b"%PDF-")
    assert got.published_at == NODE_DATE
    assert got.decision.rule == "llm_unavailable"


def test_the_raw_verdict_is_returned_for_the_audit_trail(monkeypatch):
    text = "Published on 12 September 2024 by TERI"
    _route_to_llm(monkeypatch, text, DateInterpretation(
        candidate_date="2024-09-12", date_type="publication",
        publication_statement="Published on 12 September 2024",
        confidence=0.96, recommended_action="override"))
    got = resolve(_routed_evidence(), content=b"%PDF-")
    assert got.llm_raw and got.llm_raw["candidate_date"] == "2024-09-12"


# --------------------------------------------------------------------------- #
# Fail-closed
# --------------------------------------------------------------------------- #

def test_an_unreadable_pdf_cannot_produce_an_override(monkeypatch):
    """Real bytes that PyMuPDF cannot parse: head text stays empty, so grounding
    fails and no date can move — even against a maximally confident verdict.

    The stub stands in for the model so the unit suite stays offline; the
    grounding it is checked against is the production one.
    """
    seen: list[str] = []

    def _stub(evidence):
        from app.ingestion.date_llm import date_is_in_text, statement_is_in_text

        seen.append(evidence.head_text)
        verdict = DateInterpretation(
            candidate_date="2024-06-01", date_type="publication",
            publication_statement="Published on 1 June 2024",
            confidence=0.99, recommended_action="override")
        verdict.set_grounded(
            date_is_in_text(verdict.candidate_date, evidence.head_text),
            statement_is_in_text(verdict.publication_statement, evidence.head_text),
        )
        return verdict

    monkeypatch.setattr("app.ingestion.date_llm.interpret", _stub)
    got = resolve(_routed_evidence(), content=b"not a pdf")
    assert seen == [""], "the model must be shown no text for an unreadable PDF"
    assert got.published_at == NODE_DATE
    assert got.overridden is False


def test_missing_content_keeps_the_page_date(monkeypatch):
    """No bytes at all — the routed case still asks, and still cannot ground."""
    verdict = DateInterpretation(
        candidate_date="2024-06-01", date_type="publication",
        publication_statement="Published on 1 June 2024",
        confidence=0.99, recommended_action="override")
    verdict.set_grounded(False, False)
    monkeypatch.setattr("app.ingestion.date_llm.interpret", lambda _e: verdict)
    got = resolve(_routed_evidence(), content=None)
    assert got.published_at == NODE_DATE
    assert got.overridden is False


def test_an_unexpected_error_keeps_the_page_date(monkeypatch):
    def _explode(_evidence):
        raise RuntimeError("boom")

    monkeypatch.setattr(date_resolution, "decide", _explode)
    got = resolve(_evidence(), content=b"%PDF-")
    assert got.published_at == NODE_DATE
    assert got.overridden is False


def test_a_node_without_a_date_never_invents_one():
    got = resolve(_evidence(node=_node(created=None)), content=b"%PDF-")
    assert got.published_at is None
    assert got.overridden is False


# --------------------------------------------------------------------------- #
# The production path: build_attachment_doc must carry the decision through
# --------------------------------------------------------------------------- #

class _FakePage:
    page_number = 1
    text = "PDF body text."


class _FakePdfResult:
    source = "a.pdf"
    pages = [_FakePage()]


def _build_doc(monkeypatch, *, node, file, resolved):
    """Run build_attachment_doc with the resolver stubbed and no I/O."""
    from app.ingestion.extractors import attachment, pdf_extractor

    monkeypatch.setattr(attachment, "fetch_attachment",
                        lambda s, url, t: (b"%PDF-", url))
    monkeypatch.setattr(pdf_extractor, "extract_pdf",
                        lambda content, name: _FakePdfResult())
    recorded: list = []
    monkeypatch.setattr("app.catalog.date_decisions.ensure_table", lambda: None)
    monkeypatch.setattr("app.catalog.date_decisions.record", recorded.append)
    monkeypatch.setattr(attachment, "_resolve_date",
                        lambda record, n, f, content: resolved)
    record = SimpleNamespace(document_id="f1", source_type="pdf_attachment",
                             payload=(node, file), fingerprint="fp")
    return attachment.build_attachment_doc(record, session=None), recorded


def test_an_override_reaches_the_document(monkeypatch):
    from app.ingestion.date_resolution import ResolvedDate
    from app.ingestion.date_rules import DateDecision

    resolved = ResolvedDate(
        published_at="2025-03-31",
        decision=DateDecision(document_id="f1", action="propose_override",
                              candidate_date="2025-03-31", date_type="publication",
                              source="llm_publication", confidence=0.95,
                              rule="llm_interpreted", decided_by="llm"),
    )
    node = _node(metadata={}, refs=[], files=[_file()])
    doc, recorded = _build_doc(monkeypatch, node=node, file=_file(), resolved=resolved)
    assert doc.published_at == "2025-03-31"
    assert len(recorded) == 1 and recorded[0].action == "propose_override"


def test_an_edition_label_lands_in_extra_without_moving_the_date(monkeypatch):
    from app.ingestion.date_resolution import ResolvedDate
    from app.ingestion.date_rules import DateDecision

    resolved = ResolvedDate(
        published_at=NODE_DATE, edition_label="2024-2025",
        decision=DateDecision(document_id="f1", action="keep_page_date",
                              candidate_date=NODE_DATE, date_type="edition",
                              edition_label="2024-2025", rule="llm_interpreted",
                              decided_by="llm"),
    )
    node = _node(metadata={}, refs=[], files=[_file()])
    doc, _ = _build_doc(monkeypatch, node=node, file=_file(), resolved=resolved)
    assert doc.published_at == NODE_DATE
    assert doc.extra["edition_label"] == "2024-2025"
    assert doc.extra["bundle"] == "page"


def test_no_edition_label_means_no_key_in_extra(monkeypatch):
    from app.ingestion.date_resolution import ResolvedDate

    resolved = ResolvedDate(published_at=NODE_DATE)
    node = _node(metadata={}, refs=[], files=[_file()])
    doc, _ = _build_doc(monkeypatch, node=node, file=_file(), resolved=resolved)
    assert "edition_label" not in doc.extra


def test_the_feature_flag_falls_back_to_the_node_date(monkeypatch):
    """With resolution off, a PDF inherits its node's date, as it did before."""
    from app.config import get_settings
    from app.ingestion.extractors import attachment

    settings = get_settings()
    monkeypatch.setattr(settings, "date_resolution_enabled", False)
    monkeypatch.setattr("app.ingestion.date_resolution.resolve",
                        lambda *_a, **_k: pytest.fail("resolver must not run"))
    node = _node(files=[_file()])
    got = attachment._resolve_date(
        SimpleNamespace(document_id="f1"), node, _file(), b"%PDF-")
    assert got.published_at == NODE_DATE
    assert got.decision is None
