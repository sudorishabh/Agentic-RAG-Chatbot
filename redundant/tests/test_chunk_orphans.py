"""A parent is emitted only when it adds context beyond a single child.

The rule
--------
    one child     -> no parent record; context expansion falls back to the
                     child's own text, plus the heading it already carries
    many children -> one shared parent; context expands to the parent text

Why the single-child case is deliberate, not a defect
-----------------------------------------------------
An "orphan" child is the only child of its parent window, so that window holds
nothing the child lacks except the heading — and the heading already reaches the
reader through `section_heading` (rendered by `generation/prompts.py`). Parents
are never embedded and never searched (`indexer.py` gives them zero vectors;
`hybrid_search.build_filter` pins `is_parent=False`), so emitting them would add
a stored point per single-child section purely to restate the child.

Measured over the sample corpus (10 documents, 76 children) at the time of this
decision:

    orphan children ............ 8 / 76  (11%)
    parent's extra context ..... median 3 tokens, max 13, min 0

Those figures are evidence for the decision, not a runtime rule — nothing here
asserts them, and they will drift as the corpus changes.
"""

from __future__ import annotations

from app.ingestion.chunking import DocumentMeta, chunk_document
from app.ingestion.chunking.config import ChunkingConfig

META = DocumentMeta(document_id="d", source_type="pdf", title="Panaji Case Study")

# Small children so a section splits; parent_max high so the section stays one
# parent window and the split is purely a child-level one.
CONFIG = ChunkingConfig(
    child_target_tokens=60, child_max_tokens=80, child_min_tokens=20,
    child_overlap_tokens=20, parent_target_tokens=100_000, parent_max_tokens=100_000,
)

HEADING = "3.1 Interventions Proposed"


def _prose(n: int) -> str:
    return " ".join(
        f"Alpha sentence {i} about coastal infrastructure." for i in range(n)
    )


def _split(chunks):
    return [c for c in chunks if c.is_parent], [c for c in chunks if not c.is_parent]


# --- Test A: a single-child section intentionally has no parent -------------- #

def test_single_child_section_has_no_parent_record():
    parents, children = _split(
        chunk_document(f"{HEADING}\n\n{_prose(4)}", META, config=CONFIG)
    )
    assert len(children) == 1
    assert not parents
    assert children[0].parent_chunk_id is None


def test_the_orphan_child_is_still_a_normal_searchable_chunk():
    """No parent must not mean a degraded child."""
    _, children = _split(chunk_document(f"{HEADING}\n\n{_prose(4)}", META, config=CONFIG))
    child = children[0]
    assert child.is_parent is False           # searched; parents are filtered out
    assert child.text.strip()
    assert child.embed_text.strip()           # it is embedded
    assert child.section_heading == HEADING   # and it carries its heading
    assert child.token_count > 0
    payload = child.to_payload()
    assert payload["chunk_text"] == child.text
    assert "parent_chunk_id" not in payload   # omitted, not null


# --- Test C: a multi-child section still shares one parent ------------------ #

def test_multi_child_section_shares_exactly_one_parent():
    parents, children = _split(
        chunk_document(f"{HEADING}\n\n{_prose(40)}", META, config=CONFIG)
    )
    assert len(children) > 1
    assert len(parents) == 1
    assert {c.parent_chunk_id for c in children} == {parents[0].chunk_id}


# --- Test D: the parent only exists where it is actually more context ------- #

def test_a_shared_parent_is_materially_more_than_any_one_child():
    parents, children = _split(
        chunk_document(f"{HEADING}\n\n{_prose(40)}", META, config=CONFIG)
    )
    parent = parents[0]
    assert parent.token_count > max(c.token_count for c in children)
    # It spans content that no single child holds.
    assert parent.text.count("Alpha sentence") > max(
        c.text.count("Alpha sentence") for c in children
    )


def test_a_single_child_already_holds_its_whole_window():
    """So the skipped parent could only have added the heading."""
    body = _prose(4)
    _, children = _split(chunk_document(f"{HEADING}\n\n{body}", META, config=CONFIG))
    child = children[0]
    # Everything a parent would contain, minus the heading, is already here.
    assert body in child.text
    # ...and the heading reaches the reader through the child's own payload.
    assert child.to_payload()["section_heading"] == HEADING


# --- Test E: parent record counts are pinned -------------------------------- #

def test_parent_record_count_matches_the_rule():
    single = chunk_document(f"{HEADING}\n\n{_prose(4)}", META, config=CONFIG)
    many = chunk_document(f"{HEADING}\n\n{_prose(40)}", META, config=CONFIG)

    assert sum(c.is_parent for c in single) == 0
    assert sum(c.is_parent for c in many) == 1


def test_each_section_is_scored_independently():
    """One section with many children and one with a single child, together."""
    text = f"{HEADING}\n\n{_prose(40)}\n\n4. Conclusions\n\n{_prose(4)}"
    parents, children = _split(chunk_document(text, META, config=CONFIG))

    by_heading: dict[str, list] = {}
    for child in children:
        by_heading.setdefault(child.section_heading, []).append(child)
    assert set(by_heading) == {HEADING, "4. Conclusions"}

    # The big section gets its parent; the single-child one does not.
    assert len(parents) == 1
    assert parents[0].section_heading == HEADING
    assert all(c.parent_chunk_id == parents[0].chunk_id for c in by_heading[HEADING])
    assert all(c.parent_chunk_id is None for c in by_heading["4. Conclusions"])
