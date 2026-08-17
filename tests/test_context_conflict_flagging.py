"""Regression tests: `conflict` must mean two sources might disagree.

``_flag_conflicts`` flagged any pair of blocks whose payloads shared an
identity — and ``_ids`` includes ``document_id``, so two different *sections of
one document* were reported as contradicting each other. Because ``_admit``
deduplicates by parent rather than by document, that is the ordinary case: live
traffic came back ``conflict: True`` on roughly 60% of answers, which reaches the
API response and the prompt's "prefer the later published date" handling.

The invariant enforced here: a conflict is a disagreement *between sources*, so
it needs two distinct documents. One document cannot contradict itself, and a
website node paired with its own attached PDF is one source in two formats — the
case that was already excused, including under the pre-rename ``article`` alias.
"""

from __future__ import annotations

import pytest

from app.core.models.context import ContextBlock
from app.retrieval.context_builder import _flag_conflicts


def _block(n, document_id, source_type="pdf_attachment", **extra):
    payload = {"document_id": document_id, "source_type": source_type}
    payload.update(extra)
    return ContextBlock(n=n, text=f"block {n}", payload=payload)


def _flag(*blocks):
    _flag_conflicts(list(blocks))
    return [b.conflict for b in blocks]


# --------------------------------------------------------------------------- #
# The false positive: one document, several sections.
# --------------------------------------------------------------------------- #

def test_two_sections_of_one_document_do_not_conflict():
    assert _flag(
        _block(1, "file-1", pdf_id="file-1"),
        _block(2, "file-1", pdf_id="file-1"),
    ) == [False, False]


def test_three_sections_of_one_document_do_not_conflict():
    assert _flag(
        _block(1, "file-1"), _block(2, "file-1"), _block(3, "file-1")
    ) == [False, False, False]


def test_one_document_reached_by_two_identities_does_not_conflict():
    """``_ids`` unions document_id / pdf_id / article_uuid; an overlap on any of
    them means the same source, not two of them."""
    assert _flag(
        _block(1, "node-1", source_type="website", article_uuid="node-1"),
        _block(2, "other-id", source_type="website", article_uuid="node-1"),
    ) == [False, False]


def test_website_sections_of_one_page_do_not_conflict():
    assert _flag(
        _block(1, "node-1", source_type="website"),
        _block(2, "node-1", source_type="website"),
    ) == [False, False]


# --------------------------------------------------------------------------- #
# The excusals that already existed stay excused.
# --------------------------------------------------------------------------- #

def test_website_and_its_own_attachment_do_not_conflict():
    assert _flag(
        _block(1, "node-1", source_type="website", linked_pdf_id="file-9"),
        _block(2, "file-9", source_type="pdf_attachment"),
    ) == [False, False]


def test_attachment_pointing_back_at_its_node_does_not_conflict():
    assert _flag(
        _block(1, "file-9", source_type="pdf_attachment", linked_article_uuid="node-1"),
        _block(2, "node-1", source_type="website"),
    ) == [False, False]


def test_legacy_article_alias_is_still_one_source_in_two_formats():
    """Points indexed before the rename carry ``article``. The pair is the same
    source in two formats whichever name storage happens to use."""
    assert _flag(
        _block(1, "node-1", source_type="article", linked_pdf_id="file-9"),
        _block(2, "file-9", source_type="pdf_attachment"),
    ) == [False, False]


# --------------------------------------------------------------------------- #
# Unrelated documents were never flagged, and still are not.
# --------------------------------------------------------------------------- #

def test_unrelated_documents_do_not_conflict():
    assert _flag(_block(1, "doc-A"), _block(2, "doc-B")) == [False, False]


def test_unrelated_website_and_pdf_do_not_conflict():
    assert _flag(
        _block(1, "node-1", source_type="website"),
        _block(2, "file-9", source_type="pdf_attachment"),
    ) == [False, False]


# --------------------------------------------------------------------------- #
# The check still works: a cross-linked pair of like-kind documents flags.
# --------------------------------------------------------------------------- #

def test_two_distinct_cross_linked_documents_of_one_kind_still_conflict():
    """Two distinct documents, linked to each other, not the website/own-PDF
    pair — the shape the flag exists for. Pins that the mechanism still fires
    rather than having been hardwired off."""
    assert _flag(
        _block(1, "node-1", source_type="website", linked_article_uuid="node-2"),
        _block(2, "node-2", source_type="website"),
    ) == [True, True]


def test_a_flagged_pair_marks_only_that_pair():
    a, b, c = (
        _block(1, "node-1", source_type="website", linked_article_uuid="node-2"),
        _block(2, "node-2", source_type="website"),
        _block(3, "file-unrelated"),
    )
    assert _flag(a, b, c) == [True, True, False]


# --------------------------------------------------------------------------- #
# Editions: two attachments hanging off one node.
# --------------------------------------------------------------------------- #

def test_two_attachments_of_one_node_conflict():
    """The case the "prefer the later published date" rule exists for. Annual
    report editions share a single Drupal node, so they reach retrieval as two
    attachment documents whose only common ground is the node they hang off."""
    assert _flag(
        _block(1, "file-2022", linked_article_uuid="node-1"),
        _block(2, "file-2023", linked_article_uuid="node-1"),
    ) == [True, True]


def test_three_editions_all_flag():
    assert _flag(
        _block(1, "file-2021", linked_article_uuid="node-1"),
        _block(2, "file-2022", linked_article_uuid="node-1"),
        _block(3, "file-2023", linked_article_uuid="node-1"),
    ) == [True, True, True]


def test_attachments_of_different_nodes_do_not_conflict():
    assert _flag(
        _block(1, "file-a", linked_article_uuid="node-1"),
        _block(2, "file-b", linked_article_uuid="node-2"),
    ) == [False, False]


def test_two_pages_sharing_one_attachment_conflict():
    """The symmetric shape: distinct documents whose only common ground is the
    document they both point at."""
    assert _flag(
        _block(1, "node-1", source_type="website", linked_pdf_id="file-9"),
        _block(2, "node-2", source_type="website", linked_pdf_id="file-9"),
    ) == [True, True]


def test_an_edition_and_its_own_node_are_still_one_source():
    """A node beside one of its attachments stays the two-formats case; only
    attachment-vs-attachment is an edition disagreement."""
    assert _flag(
        _block(1, "node-1", source_type="website", linked_pdf_id="file-2023"),
        _block(2, "file-2023", linked_article_uuid="node-1"),
    ) == [False, False]


def test_editions_flag_without_disturbing_an_unrelated_block():
    a, b, c = (
        _block(1, "file-2022", linked_article_uuid="node-1"),
        _block(2, "file-2023", linked_article_uuid="node-1"),
        _block(3, "file-other", linked_article_uuid="node-9"),
    )
    assert _flag(a, b, c) == [True, True, False]


def test_sections_of_one_edition_still_do_not_conflict():
    """Two chunks of the *same* attachment share both a document id and a parent
    node; identity wins, so they are one source, not two editions."""
    assert _flag(
        _block(1, "file-2023", linked_article_uuid="node-1"),
        _block(2, "file-2023", linked_article_uuid="node-1"),
    ) == [False, False]


# --------------------------------------------------------------------------- #
# The realistic mixed context: nothing spurious.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("n_sections", [2, 3, 4])
def test_a_segregated_context_of_one_pdf_plus_a_page_is_clean(n_sections):
    """What production actually retrieves: a website page and several sections of
    one report. Previously every such answer reported a conflict."""
    blocks = [_block(1, "node-1", source_type="website")]
    blocks += [
        _block(i + 2, "file-1", pdf_id="file-1") for i in range(n_sections)
    ]
    _flag_conflicts(blocks)
    assert not any(b.conflict for b in blocks)
