"""An attachment outlives the deletion of one parent, but not of its last.

A PDF is a document in its own right, and one PDF is often reachable from
several pages — 84 of them are, up to eight parents each. Deleting a page must
therefore end only that page's claim on its attachments, never the attachments
themselves; they go when the last claim does. `documents_attachment` records
every claim, and the deleted parent's rows cascade away with it, so an id left
with no rows has no parent left.

Without this an attachment survives every page that ever referenced it and stays
searchable indefinitely: nothing else deletes one, because the crawl can only
reach an attachment through a parent it no longer has.

The catalog below is a stand-in for the two tables involved, with the same
cascade the foreign key provides. No MySQL, no Qdrant.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ingestion import pipeline
from app.ingestion.change_detection import ChangeRecord, ChangeStatus


class _Catalog:
    """`documents` and `documents_attachment`, and the FK cascade between them."""

    def __init__(self) -> None:
        self.documents: dict[str, str] = {}          # document_id -> source_type
        self.links: set[tuple[str, str]] = set()     # (file_uuid, parent document_id)
        self.deleted_points: list[str] = []

    # --- fixture setup ---------------------------------------------------- #

    def add_page(self, page: str, *attachments: str) -> None:
        self.documents[page] = "website"
        for attachment in attachments:
            self.documents[attachment] = "pdf_attachment"
            self.links.add((attachment, page))

    def add_link_only(self, file_uuid: str, page: str) -> None:
        """A file that was linked but never successfully ingested — a link row
        with no document of its own. 91 of these exist today."""
        self.links.add((file_uuid, page))

    # --- the catalog API the pipeline calls -------------------------------- #

    def attachment_ids_for(self, document_id: str) -> list[str]:
        return sorted(f for f, parent in self.links if parent == document_id)

    def orphaned_attachments(self, file_uuids) -> list[str]:
        still_linked = {f for f, _ in self.links}
        return [
            f for f in dict.fromkeys(file_uuids)
            if f not in still_linked and self.documents.get(f) == "pdf_attachment"
        ]

    def delete(self, ids) -> None:
        for document_id in ids:
            self.documents.pop(document_id, None)
            # ON DELETE CASCADE: a parent takes its own link rows with it.
            self.links = {(f, p) for f, p in self.links if p != document_id}

    def delete_points(self, document_id, keep_ids=None) -> None:
        self.deleted_points.append(document_id)


@pytest.fixture
def catalog(monkeypatch):
    site = _Catalog()
    logged: list[tuple[str, str]] = []

    monkeypatch.setattr(pipeline, "delete_document", site.delete_points)
    monkeypatch.setattr(pipeline.state, "delete", site.delete)
    monkeypatch.setattr(pipeline.state, "attachment_ids_for", site.attachment_ids_for)
    monkeypatch.setattr(pipeline.state, "orphaned_attachments", site.orphaned_attachments)
    monkeypatch.setattr(
        pipeline, "_log",
        lambda run_id, record, status, **kw: logged.append((record.document_id, status)),
    )
    site.logged = logged
    return site


def _delete(page: str) -> str:
    record = ChangeRecord(
        status=ChangeStatus.DELETED, document_id=page, source_type="website",
        source_key=f"https://teriin.org/{page}", bundle="report", entity_type="node",
    )
    return pipeline._handle(record, build_doc=lambda r: None)


# --------------------------------------------------------------------------- #
# The last parent takes the attachment with it.
# --------------------------------------------------------------------------- #

def test_an_attachment_with_one_parent_goes_with_it(catalog):
    catalog.add_page("page-a", "pdf-1")

    assert _delete("page-a") == "deleted"

    assert "pdf-1" not in catalog.documents, "the attachment's catalog row must go"
    assert catalog.deleted_points == ["page-a", "pdf-1"], "and its vectors, after the parent's"


def test_deleting_the_attachment_removes_its_qdrant_points(catalog):
    catalog.add_page("page-a", "pdf-1")
    _delete("page-a")

    assert "pdf-1" in catalog.deleted_points


def test_every_orphaned_attachment_on_a_page_is_removed(catalog):
    catalog.add_page("page-a", "pdf-1", "pdf-2", "pdf-3")

    _delete("page-a")

    assert catalog.documents == {}
    assert catalog.deleted_points == ["page-a", "pdf-1", "pdf-2", "pdf-3"]


# --------------------------------------------------------------------------- #
# A shared attachment survives losing one parent.
# --------------------------------------------------------------------------- #

def test_a_shared_attachment_survives_losing_one_parent(catalog):
    catalog.add_page("page-a", "pdf-1")
    catalog.add_page("page-b", "pdf-1")

    _delete("page-a")

    assert catalog.documents.get("pdf-1") == "pdf_attachment"
    assert catalog.links == {("pdf-1", "page-b")}
    assert catalog.deleted_points == ["page-a"], "the attachment keeps its vectors"


def test_the_shared_attachment_goes_when_its_last_parent_does(catalog):
    catalog.add_page("page-a", "pdf-1")
    catalog.add_page("page-b", "pdf-1")

    _delete("page-a")
    assert "pdf-1" in catalog.documents, "still held by page-b"

    _delete("page-b")

    assert "pdf-1" not in catalog.documents
    assert catalog.deleted_points == ["page-a", "page-b", "pdf-1"]


def test_one_parent_of_three_leaves_the_attachment_alone(catalog):
    for page in ("page-a", "page-b", "page-c"):
        catalog.add_page(page, "pdf-1")

    _delete("page-b")

    assert catalog.documents.get("pdf-1") == "pdf_attachment"
    assert catalog.links == {("pdf-1", "page-a"), ("pdf-1", "page-c")}
    assert "pdf-1" not in catalog.deleted_points


def test_a_page_keeps_its_own_attachment_while_releasing_a_shared_one(catalog):
    """The mixed case: one attachment is exclusive to the deleted page, the
    other is not. Only the exclusive one may go."""
    catalog.add_page("page-a", "pdf-own", "pdf-shared")
    catalog.add_page("page-b", "pdf-shared")

    _delete("page-a")

    assert "pdf-own" not in catalog.documents
    assert catalog.documents.get("pdf-shared") == "pdf_attachment"
    assert catalog.deleted_points == ["page-a", "pdf-own"]


# --------------------------------------------------------------------------- #
# Everything else about deletion stays as it was.
# --------------------------------------------------------------------------- #

def test_a_page_with_no_attachments_deletes_exactly_as_before(catalog):
    catalog.add_page("page-a")

    assert _delete("page-a") == "deleted"

    assert catalog.deleted_points == ["page-a"]
    assert catalog.documents == {}
    assert catalog.logged == [("page-a", "deleted")]


def test_a_linked_file_that_was_never_ingested_costs_no_delete(catalog):
    """A link row with no document behind it — 91 of those exist. There is
    nothing to delete, so nothing should be attempted."""
    catalog.add_page("page-a")
    catalog.add_link_only("pdf-never-ingested", "page-a")

    _delete("page-a")

    assert catalog.deleted_points == ["page-a"]


def test_each_orphan_is_recorded_in_the_audit_log(catalog):
    catalog.add_page("page-a", "pdf-1", "pdf-2")

    _delete("page-a")

    assert catalog.logged == [
        ("page-a", "deleted"), ("pdf-1", "deleted"), ("pdf-2", "deleted")
    ]


def test_a_failed_orphan_check_leaves_the_attachments_alone(catalog, monkeypatch):
    """Fails open: the parent delete already succeeded, and an attachment that
    survives is the behaviour that predates this cleanup."""
    catalog.add_page("page-a", "pdf-1")

    def boom(file_uuids):
        raise RuntimeError("catalog unreachable")

    monkeypatch.setattr(pipeline.state, "orphaned_attachments", boom)

    assert _delete("page-a") == "deleted"
    assert catalog.deleted_points == ["page-a"]
    assert "pdf-1" in catalog.documents
