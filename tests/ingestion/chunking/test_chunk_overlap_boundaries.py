"""Overlap crosses packing boundaries but not semantic ones.

Overlap used to restart at every parent window. A parent boundary *inside* a
section exists only because the section outgrew `parent_max_tokens`, and those
splits land mid-sentence, so the first child after one lost its context. A
section boundary is a real break: carrying prose across it would pollute the next
heading's embedding (`Recommendations` -> `References`).
"""

from __future__ import annotations

from app.ingestion.chunking import DocumentMeta, chunk_document
from app.ingestion.chunking.config import ChunkingConfig

META = DocumentMeta(document_id="d", source_type="pdf", title="Panaji Case Study")

# Small children so overlap is forced; parent_max large enough that a section
# stays one parent unless a test deliberately overflows it.
ONE_PARENT = ChunkingConfig(
    child_target_tokens=60, child_max_tokens=80, child_min_tokens=20,
    child_overlap_tokens=20, parent_target_tokens=100_000, parent_max_tokens=100_000,
)
# parent_max small enough that a single section splits into several parents:
# a Type C boundary, created purely by packing.
MANY_PARENTS = ChunkingConfig(
    child_target_tokens=60, child_max_tokens=80, child_min_tokens=20,
    child_overlap_tokens=20, parent_target_tokens=150, parent_max_tokens=200,
)


def _prose(marker: str, n: int = 12) -> str:
    """Capitalised sentences, so `_SENTENCE_BOUNDARY` has boundaries to find."""
    return " ".join(
        f"{marker.capitalize()} sentence {i} about coastal infrastructure." for i in range(n)
    )


def _children(chunks):
    return [c for c in chunks if not c.is_parent]


def _carry(prev, cur) -> str:
    """The leading run of `cur.text` carried from the end of `prev.text`.

    The carry is by construction a suffix of the previous chunk and a prefix of
    this one, so the longest such run is the overlap. Short coincidental matches
    are ignored — a real carry is a sentence or more.
    """
    for n in range(min(len(prev.text), len(cur.text)), 12, -1):
        if prev.text.endswith(cur.text[:n]):
            return cur.text[:n]
    return ""


def test_same_section_children_still_overlap():
    """Test 1: the existing behaviour inside one section is unchanged."""
    children = _children(chunk_document(_prose("alpha", 30), META, config=ONE_PARENT))
    assert len(children) > 1
    carry = _carry(children[0], children[1])
    assert carry, "second child lost its overlap"
    assert children[0].text.endswith(carry)
    assert children[1].text.startswith(carry)


def test_overlap_does_not_cross_a_section_boundary():
    """Test 2: a real heading change must not inherit the previous section."""
    text = f"1. Introduction\n\n{_prose('alpha', 20)}\n\n2. Methodology\n\n{_prose('bravo', 20)}"
    children = _children(chunk_document(text, META, config=ONE_PARENT))
    first_of_b = next(c for c in children if c.section_heading == "2. Methodology")
    assert "Alpha" not in first_of_b.text
    prev = children[children.index(first_of_b) - 1]
    assert prev.section_heading == "1. Introduction"
    assert not _carry(prev, first_of_b)


def test_overlap_crosses_a_parent_boundary_inside_one_section():
    """Test 3: a parent split is a packing artifact, so context must continue."""
    text = f"1. Introduction\n\n{_prose('alpha', 60)}"
    chunks = chunk_document(text, META, config=MANY_PARENTS)
    parents = [c for c in chunks if c.is_parent]
    children = _children(chunks)
    assert len(parents) > 1, "fixture must split the section into several parents"
    assert len({c.section_heading for c in children}) == 1, "must stay one section"

    # The first child of a later parent still carries from the previous child.
    crossing = [
        (a, b) for a, b in zip(children, children[1:])
        if a.parent_chunk_id != b.parent_chunk_id
    ]
    assert crossing, "fixture must produce a parent boundary between children"
    for prev, cur in crossing:
        assert _carry(prev, cur), (
            f"child {cur.chunk_index} lost overlap across a parent boundary"
        )


def test_first_child_of_a_new_section_carries_nothing():
    """Test 4: assert the exact text, not merely that overlap is absent."""
    body_a, body_b = _prose("alpha", 20), _prose("bravo", 20)
    text = f"1. Introduction\n\n{body_a}\n\n2. Methodology\n\n{body_b}"
    children = _children(chunk_document(text, META, config=ONE_PARENT))
    first_of_b = next(c for c in children if c.section_heading == "2. Methodology")
    # Its text begins exactly where section B's own content begins.
    assert body_b.startswith(first_of_b.text[:40])
    assert first_of_b.overlap_page_range is None


def test_three_sections_carry_within_but_not_across():
    """Test 5: A -> B blocked, B's own children still overlap."""
    text = (
        f"1. Introduction\n\n{_prose('alpha', 20)}\n\n"
        f"2. Methodology\n\n{_prose('bravo', 20)}\n\n"
        f"3. Results\n\n{_prose('charlie', 20)}"
    )
    children = _children(chunk_document(text, META, config=ONE_PARENT))
    by_section: dict[str, list] = {}
    for child in children:
        by_section.setdefault(child.section_heading, []).append(child)
    assert len(by_section) == 3
    assert all(len(v) > 1 for v in by_section.values()), "each section needs 2+ children"

    for prev, cur in zip(children, children[1:]):
        same_section = prev.section_heading == cur.section_heading
        carried = bool(_carry(prev, cur))
        assert carried == same_section, (
            f"child {cur.chunk_index}: carried={carried} but "
            f"same_section={same_section}"
        )

    # No section's marker leaks into another section's chunks.
    for heading, marker in (
        ("1. Introduction", "Alpha"), ("2. Methodology", "Bravo"), ("3. Results", "Charlie")
    ):
        for other, kids in by_section.items():
            if other == heading:
                continue
            assert all(marker not in c.text for c in kids), f"{marker} leaked into {other}"


def test_widened_overlap_still_respects_the_token_cap():
    """P1-5 must hold for the newly carried overlap too."""
    chunks = chunk_document(f"1. Introduction\n\n{_prose('alpha', 60)}", META, config=MANY_PARENTS)
    children = _children(chunks)
    assert children
    assert max(c.token_count for c in children) <= MANY_PARENTS.child_max_tokens
