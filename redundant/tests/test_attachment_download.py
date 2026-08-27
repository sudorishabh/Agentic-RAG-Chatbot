"""Unit tests for attached-PDF download failures.

Covers how a failed download is reported and remembered: a dead link (4xx) is
one quiet warning plus a marker that keeps the crawl from refetching it, while
a transient failure keeps its traceback and no marker. No network and no
catalog — the session and the marker store are stubs.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
import requests

from app.catalog import dead_links
from app.ingestion.extractors import attachment


def _http_error(status: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    return requests.HTTPError(f"{status} Error", response=response)


def _record(url="https://teriin.org/files/gone.pdf", fingerprint="inbody:abc"):
    node = SimpleNamespace(
        uuid="n1", title="A node", url="https://teriin.org/node/1", bundle="report",
        created=None, metadata={}, refs=[],
    )
    file = SimpleNamespace(url=url, filename="gone.pdf", description=None)
    return SimpleNamespace(
        payload=(node, file), document_id="inbody:abc", fingerprint=fingerprint
    )


class _FailingSession:
    def __init__(self, exc: Exception):
        self._exc = exc

    def get(self, url, timeout):  # noqa: ARG002 - signature parity with requests
        raise self._exc


@pytest.fixture(autouse=True)
def markers(monkeypatch) -> list[dict]:
    """Stub the marker store for every test here — the real one writes to MySQL,
    and a download failure reaches it on the 4xx path. Yields the calls made."""
    calls: list[dict] = []
    monkeypatch.setattr(
        dead_links, "record",
        lambda document_id, **kw: calls.append({"document_id": document_id, **kw}),
    )
    return calls


# --------------------------------------------------------------------------- #
# dead_link_status — only client errors count as permanently gone.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("status,expected", [(404, 404), (403, 403), (410, 410)])
def test_dead_link_status_reports_client_errors(status, expected):
    assert attachment.dead_link_status(_http_error(status)) == expected


@pytest.mark.parametrize("exc", [
    _http_error(500),
    _http_error(503),
    requests.ConnectTimeout("timed out"),
])
def test_dead_link_status_ignores_transient_failures(exc):
    assert attachment.dead_link_status(exc) is None


# --------------------------------------------------------------------------- #
# build_attachment_doc — the failure is logged at the level it deserves.
# --------------------------------------------------------------------------- #

def test_dead_link_logs_a_warning_without_traceback(caplog):
    session = _FailingSession(_http_error(404))
    with caplog.at_level(logging.WARNING, logger=attachment.logger.name):
        assert attachment.build_attachment_doc(_record(), session) is None

    record = caplog.records[-1]
    assert record.levelno == logging.WARNING
    assert record.exc_info is None
    assert "HTTP 404" in record.getMessage()


def test_transient_failure_stays_an_error_with_traceback(caplog):
    session = _FailingSession(requests.ConnectTimeout("timed out"))
    with caplog.at_level(logging.WARNING, logger=attachment.logger.name):
        assert attachment.build_attachment_doc(_record(), session) is None

    record = caplog.records[-1]
    assert record.levelno == logging.ERROR
    assert record.exc_info is not None


# --------------------------------------------------------------------------- #
# build_attachment_doc — a dead link is remembered so it stops being refetched.
# --------------------------------------------------------------------------- #

def test_a_dead_link_is_marked_at_the_records_fingerprint(markers):
    session = _FailingSession(_http_error(404))

    attachment.build_attachment_doc(_record(fingerprint="inbody:abc"), session)

    assert markers == [{
        "document_id": "inbody:abc",
        "fingerprint": "inbody:abc",
        "url": "https://teriin.org/files/gone.pdf",
        "status": 404,
    }]


def test_a_transient_failure_is_not_marked(markers):
    """A timeout says nothing about whether the file is there; marking it would
    strand a healthy attachment until its node happens to change."""
    session = _FailingSession(requests.ConnectTimeout("timed out"))

    attachment.build_attachment_doc(_record(), session)

    assert markers == []


def test_an_unwritable_marker_does_not_break_the_download_path(monkeypatch, caplog):
    def _boom(document_id, **kw):
        raise RuntimeError("catalog unreachable")

    monkeypatch.setattr(dead_links, "record", _boom)
    session = _FailingSession(_http_error(404))

    with caplog.at_level(logging.WARNING, logger=attachment.logger.name):
        assert attachment.build_attachment_doc(_record(), session) is None

    assert "will be retried" in caplog.records[-1].getMessage()
