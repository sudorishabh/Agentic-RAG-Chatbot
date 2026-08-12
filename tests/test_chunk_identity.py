"""A chunk's id is its own content within its document.

Ids used to be `uuid5(document_id | version | running-index)`, so a version bump
alone gave every chunk a new id and re-embedded the whole document — 36 of 36
children on a real corpus document, for a one-word edit.

Identity is now anchored on the chunk's *owned* text, deliberately independent
of version, position, page and overlap carry. Identity is not the re-embed test:
`content_hash` still covers the exact stored text (carry included), so a chunk
whose carry changed keeps its id but is still correctly re-embedded.
"""

from __future__ import annotations

from app.ingestion.chunking import DocumentMeta, chunk_document, chunk_pages
from app.ingestion.chunking.config import ChunkingConfig

CONFIG = ChunkingConfig(
    child_target_tokens=40, child_max_tokens=60, child_min_tokens=10,
    child_overlap_tokens=10, parent_target_tokens=100_000, parent_max_tokens=100_000,
)

A = "Alpha reports coastal erosion along the northern shoreline of the district."
B = "Bravo records groundwater salinity rising across the eastern wards each year."
C = "Charlie notes sewerage capacity unchanged despite steady population growth."
D = "Delta tracks tourist arrivals peaking through the winter festival season."
NEW = "Echo describes mangrove cover declining near the estuary mouth this decade."


def _meta(version: int = 1, document_id: str = "doc-1") -> DocumentMeta:
    return DocumentMeta(
        document_id=document_id, source_type="pdf", title="T", doc_version=version
    )


def _ids(text: str, *, version: int = 1) -> dict[str, str]:
    """{chunk text -> chunk id} for the children of a one-section document."""
    chunks = chunk_document(text, _meta(version), config=CONFIG)
    return {c.text: c.chunk_id for c in chunks if not c.is_parent}


def _doc(*paragraphs: str) -> str:
    return "\n\n".join(paragraphs)


# --- Case A: unchanged content ---------------------------------------------- #

def test_reindexing_an_unchanged_document_keeps_every_id():
    first = _ids(_doc(A, B, C, D))
    second = _ids(_doc(A, B, C, D))
    assert first == second


def test_a_version_bump_alone_changes_nothing():
    """The defect this fixes: v1 -> v2 with identical content used to churn 100%."""
    v1 = _ids(_doc(A, B, C, D), version=1)
    v2 = _ids(_doc(A, B, C, D), version=7)
    assert v1 == v2


# --- Case B: one chunk edited ------------------------------------------------ #

def test_editing_one_chunk_leaves_the_others_stable():
    v1 = _ids(_doc(A, B, C, D))
    v2 = _ids(_doc(A, B.replace("rising", "falling"), C, D))
    stable = set(v1.values()) & set(v2.values())
    assert len(v2) - len(stable) == 1, "only the edited chunk should be new"
    changed = [t for t in v2 if v2[t] not in stable]
    assert "falling" in changed[0]


# --- Case C: insertion before existing chunks ------------------------------- #

def test_inserting_a_paragraph_does_not_shift_later_ids():
    """The positional scheme changed every downstream id; content anchoring does not."""
    v1 = _ids(_doc(A, B, C))
    v2 = _ids(_doc(A, NEW, B, C))
    for text, chunk_id in v1.items():
        if text in v2:
            assert v2[text] == chunk_id, f"id shifted for {text[:30]!r}"


# --- Case D/E: split and merge ---------------------------------------------- #

def test_a_split_produces_new_ids_and_retires_the_old_one():
    v1 = _ids(_doc(f"{A} {B}"))
    v2 = _ids(_doc(A, B))
    assert not (set(v1.values()) & set(v2.values())), "no id may be forced onto both halves"
    assert len(set(v2.values())) == len(v2), "split halves must not collide"


def test_a_merge_produces_one_new_id():
    v1 = _ids(_doc(A, B))
    v2 = _ids(_doc(f"{A} {B}"))
    assert not (set(v1.values()) & set(v2.values()))


# --- Case F: overlap is not part of identity -------------------------------- #

def test_changing_the_overlap_setting_does_not_change_ids():
    text = _doc(A, B, C, D)
    meta = _meta()
    wide = ChunkingConfig(
        child_target_tokens=40, child_max_tokens=80, child_min_tokens=10,
        child_overlap_tokens=30, parent_target_tokens=100_000, parent_max_tokens=100_000,
    )
    narrow = ChunkingConfig(
        child_target_tokens=40, child_max_tokens=80, child_min_tokens=10,
        child_overlap_tokens=0, parent_target_tokens=100_000, parent_max_tokens=100_000,
    )
    a = [c.chunk_id for c in chunk_document(text, meta, config=wide) if not c.is_parent]
    b = [c.chunk_id for c in chunk_document(text, meta, config=narrow) if not c.is_parent]
    assert a == b
    # ...but the stored text differs, so content_hash must differ and drive a re-embed.
    ha = [c.content_hash for c in chunk_document(text, meta, config=wide) if not c.is_parent]
    hb = [c.content_hash for c in chunk_document(text, meta, config=narrow) if not c.is_parent]
    assert ha != hb


def test_a_shared_id_always_agrees_with_its_content_hash():
    """The safety property behind reuse: for any id present in both versions,
    equal `content_hash` implies byte-identical stored text. A chunk whose carry
    shifted keeps its id but reports a different hash, so it is re-embedded
    rather than reusing a stale vector."""
    meta = _meta()
    v1 = chunk_document(_doc(A, B, C, D), meta, config=CONFIG)
    v2 = chunk_document(_doc(A, B, C, D.replace("tourist", "visitor")), meta, config=CONFIG)
    kids1 = {c.chunk_id: c for c in v1 if not c.is_parent}
    kids2 = {c.chunk_id: c for c in v2 if not c.is_parent}
    shared = set(kids1) & set(kids2)
    assert shared, "unchanged paragraphs must keep their ids"
    for cid in shared:
        same_hash = kids1[cid].content_hash == kids2[cid].content_hash
        same_text = kids1[cid].text == kids2[cid].text
        assert same_hash == same_text, f"hash and text disagree for {cid}"


# --- Case G: page numbers are not part of identity -------------------------- #

def test_repagination_does_not_change_ids():
    """A cover page inserted ahead of the content is not a content edit."""
    meta = _meta()
    before = chunk_pages([(1, _doc(A, B)), (2, _doc(C, D))], meta, config=CONFIG)
    after = chunk_pages(
        [(1, "Cover"), (2, _doc(A, B)), (3, _doc(C, D))], meta, config=CONFIG
    )
    ids_before = {c.text: c.chunk_id for c in before if not c.is_parent}
    ids_after = {c.text: c.chunk_id for c in after if not c.is_parent}
    common = set(ids_before) & set(ids_after)
    assert common
    for text in common:
        assert ids_before[text] == ids_after[text]


def test_page_number_still_recorded_even_though_it_is_not_in_the_identity():
    meta = _meta()
    child = next(
        c for c in chunk_pages([(7, _doc(A, B))], meta, config=CONFIG) if not c.is_parent
    )
    assert child.page_number == 7


# --- duplicates must not collapse ------------------------------------------- #

def test_identical_text_in_two_places_gets_two_ids():
    repeated = "Not applicable."
    text = _doc(A, repeated, B, repeated, C)
    chunks = [c for c in chunk_document(text, _meta(), config=CONFIG) if not c.is_parent]
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "duplicate content must not collapse onto one id"


def test_duplicate_ordinals_are_stable_across_reindexing():
    repeated = "Not applicable."
    text = _doc(A, repeated, B, repeated, C)
    first = [c.chunk_id for c in chunk_document(text, _meta(), config=CONFIG)]
    second = [c.chunk_id for c in chunk_document(text, _meta(2), config=CONFIG)]
    assert first == second


# --- scoping ----------------------------------------------------------------- #

def test_the_same_text_in_two_documents_gets_different_ids():
    a = _ids(_doc(A, B))
    chunks = chunk_document(_doc(A, B), _meta(document_id="doc-2"), config=CONFIG)
    b = {c.text: c.chunk_id for c in chunks if not c.is_parent}
    assert set(a.values()).isdisjoint(b.values())


def test_parents_and_children_never_share_an_id():
    chunks = chunk_document(_doc(A, B, C, D), _meta(), config=CONFIG)
    parents = {c.chunk_id for c in chunks if c.is_parent}
    children = {c.chunk_id for c in chunks if not c.is_parent}
    assert parents and children
    assert parents.isdisjoint(children)


def test_children_reference_the_emitted_parent_id():
    chunks = chunk_document(_doc(A, B, C, D), _meta(), config=CONFIG)
    parents = {c.chunk_id for c in chunks if c.is_parent}
    for child in (c for c in chunks if not c.is_parent):
        if child.parent_chunk_id:
            assert child.parent_chunk_id in parents
