"""Unit tests for keeping dead attachment links out of the Drupal crawl.

Covers the read side of the marker: a URL the site answered 4xx for is left out
of the run while the fingerprint that failed is still current, comes back when
that fingerprint moves, and never blocks the crawl if the marker table cannot
be read. The extractor, the catalog and the network are all stubbed.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.catalog.dead_links import DeadLink
from app.ingestion.change_detection import drupal
from app.ingestion.extractors import drupal_extractor

CHANGED = "2026-08-04T10:00:00+00:00"
INBODY_UUID = "inbody:fe59431e"
FILE_UUID = "9c1e-attached-file"


def _file(uuid=INBODY_UUID, origin="inbody"):
    return SimpleNamespace(
        uuid=uuid,
        url="https://teriin.org/sites/default/files/files/gone.pdf",
        filename="gone.pdf",
        origin=origin,
    )


def _node(files):
    return SimpleNamespace(
        uuid="node-1",
        body="A node with enough body text to survive the block filter.",
        files=files,
        changed=CHANGED,
        source="https://teriin.org/node/1",
    )


def _patch(monkeypatch, *, files, markers, load_raises=False):
    """Drive detect_drupal_changes over exactly one node with these files."""
    monkeypatch.setattr(
        drupal, "get_settings",
        lambda: SimpleNamespace(drupal_max_retries=1, drupal_block_min_chars=200),
    )
    monkeypatch.setattr(drupal.state, "load", lambda source_type: {})
    monkeypatch.setattr(drupal_extractor, "_build_session", lambda retries: _Session())
    monkeypatch.setattr(
        drupal_extractor, "iter_bundle_records",
        lambda session, bundle, **kw: iter([_node(files)]),
    )

    def _load():
        if load_raises:
            raise RuntimeError("catalog unreachable")
        return markers

    monkeypatch.setattr(drupal.dead_links, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.dead_links, "load", _load)


class _Session:
    def close(self):
        pass


def _attachment_ids(records) -> list[str]:
    return [r.document_id for r in records if r.source_type == "pdf_attachment"]


# --------------------------------------------------------------------------- #
# A current marker keeps the attachment out of the run.
# --------------------------------------------------------------------------- #

def test_a_marked_attachment_is_left_out_of_the_run(monkeypatch):
    """The whole point: no ChangeRecord means no download and no skip, so the
    404 stops repeating every sweep."""
    _patch(
        monkeypatch,
        files=[_file()],
        # An in-body PDF is fingerprinted on its own URL-derived uuid.
        markers={INBODY_UUID: DeadLink(INBODY_UUID, fingerprint=INBODY_UUID, status=404)},
    )
    records = list(drupal.detect_drupal_changes(bundles=["report"]))

    assert _attachment_ids(records) == []
    # The node itself is unaffected — only its dead link is suppressed.
    assert [r.document_id for r in records] == ["node-1"]


def test_an_unmarked_attachment_still_yields(monkeypatch):
    _patch(monkeypatch, files=[_file()], markers={})
    records = list(drupal.detect_drupal_changes(bundles=["report"]))

    assert _attachment_ids(records) == [INBODY_UUID]


# --------------------------------------------------------------------------- #
# The marker expires when the fingerprint it recorded moves.
# --------------------------------------------------------------------------- #

def test_a_marked_attachment_returns_when_its_fingerprint_moves(monkeypatch):
    """A real attachment is fingerprinted on its node's changed mark, so editing
    the node — the way a replaced file reaches the site — revives the download."""
    _patch(
        monkeypatch,
        files=[_file(uuid=FILE_UUID, origin="attachment")],
        markers={FILE_UUID: DeadLink(FILE_UUID, fingerprint="2026-01-01T00:00:00+00:00")},
    )
    records = list(drupal.detect_drupal_changes(bundles=["report"]))

    assert _attachment_ids(records) == [FILE_UUID]


def test_a_marked_attachment_stays_out_while_its_node_is_untouched(monkeypatch):
    _patch(
        monkeypatch,
        files=[_file(uuid=FILE_UUID, origin="attachment")],
        markers={FILE_UUID: DeadLink(FILE_UUID, fingerprint=CHANGED)},
    )
    records = list(drupal.detect_drupal_changes(bundles=["report"]))

    assert _attachment_ids(records) == []


# --------------------------------------------------------------------------- #
# The skip list is an optimization, never a dependency.
# --------------------------------------------------------------------------- #

def test_an_unreadable_marker_table_retries_everything(monkeypatch):
    _patch(monkeypatch, files=[_file()], markers={}, load_raises=True)
    records = list(drupal.detect_drupal_changes(bundles=["report"]))

    assert _attachment_ids(records) == [INBODY_UUID]
