"""`child_max_tokens` is a hard limit, not a target.

Three independent paths used to push a child past the configured cap: coalescing
merged windows that did not fit, overlap prepended its carry after every size
check, and `pack` sizes windows by summing atom counts while the emitted text is
the joined string. These tests pin the limit at each path and on the final child.
"""

from __future__ import annotations

import pytest

from app.ingestion.chunking import DocumentMeta, chunk_document, chunk_pages
from app.ingestion.chunking.config import ChunkingConfig, config_for
from app.ingestion.chunking.packer import (
    apply_overlap,
    coalesce_windows,
    get_encoder,
    window_texts,
)
from app.ingestion.chunking.segmenter import Block, join_blocks

ENC = get_encoder("cl100k_base")

MAX = 560
MIN = 120


def _block(tokens: int, kind: str = "text") -> Block:
    filler = "Sea level rise assessment methodology and vulnerability scoring. " * 60
    return Block(kind, ENC.head(filler, tokens), 0, 21)


def _sizes(windows) -> list[int]:
    return [ENC.count(join_blocks(w)) for w in windows]


def test_coalesce_refuses_a_merge_that_would_exceed_the_maximum():
    """The reported case: ~545 + ~100 must not become a ~645-token child."""
    windows = [[_block(545, "table")], [_block(100)]]
    before = _sizes(windows)
    # The premise: the small window is undersized, so coalescing wants to merge
    # it, but the merged result would not fit.
    assert before[1] < MIN and sum(before) > MAX, before

    out = coalesce_windows(windows, MIN, MAX, ENC)

    assert all(size <= MAX for size in _sizes(out)), _sizes(out)
    assert len(out) == 2, "the undersized window must stay separate, not merge over cap"


def test_coalesce_leaves_a_window_short_rather_than_overflowing():
    """An undersized window is acceptable; an oversized one is not."""
    out = coalesce_windows([[_block(540)], [_block(60)]], MIN, MAX, ENC)
    assert min(_sizes(out)) < MIN
    assert max(_sizes(out)) <= MAX


def test_coalesce_still_merges_when_the_result_fits():
    """The fix must not disable coalescing where there is room."""
    out = coalesce_windows([[_block(100)], [_block(200)]], MIN, MAX, ENC)
    assert len(out) == 1
    assert MIN <= _sizes(out)[0] <= MAX


def test_coalesce_picks_the_neighbour_that_fits():
    """Given one neighbour that fits and one that does not, merge with the former."""
    windows = [[_block(500)], [_block(60)], [_block(200)]]
    out = coalesce_windows(windows, MIN, MAX, ENC)
    assert all(size <= MAX for size in _sizes(out)), _sizes(out)
    assert len(out) == 2, "60 should join the 200 window, not the 500 one"


def test_a_lone_undersized_window_is_kept():
    out = coalesce_windows([[_block(30)]], MIN, MAX, ENC)
    assert len(out) == 1
    assert _sizes(out) == [30]


# --- overlap must not push a child over the cap ----------------------------- #

# Sentences, so `overlap_carry` has boundaries to advance to.
PROSE = "Coastal infrastructure needs sustained adaptation investment now. " * 60


def _text(tokens: int) -> str:
    return ENC.head(PROSE, tokens)


def test_overlap_is_trimmed_to_fit_the_maximum():
    """A ~520-token child plus a 60-token carry must not reach 580."""
    first, second = _text(300), _text(520)
    out = apply_overlap([first, second], 60, ENC, max_tokens=MAX)
    assert ENC.count(out[1]) <= MAX, ENC.count(out[1])
    # Trimmed, not dropped: some carry still precedes the chunk.
    assert len(out[1]) > len(second)


def test_overlap_is_untouched_when_there_is_room():
    """A 400-token child with a 60-token carry keeps its normal overlap."""
    first, second = _text(400), _text(400)
    capped = apply_overlap([first, second], 60, ENC, max_tokens=MAX)
    uncapped = apply_overlap([first, second], 60, ENC, max_tokens=100_000)
    assert capped == uncapped
    assert ENC.count(capped[1]) <= MAX
    assert len(capped[1]) > len(second)


def test_overlap_never_cuts_the_chunk_itself():
    """The carry gives way, never the chunk: a child filling the cap keeps all
    of its own text, and the result still respects the maximum."""
    second = _text(MAX)
    out = apply_overlap([_text(300), second], 60, ENC, max_tokens=MAX)
    assert ENC.count(out[1]) <= MAX, ENC.count(out[1])
    assert out[1].endswith(second.strip())


def test_overlap_is_dropped_when_no_carry_can_fit():
    """A child at the cap with no room at all is returned untouched."""
    second = _text(MAX)
    out = apply_overlap([_text(300), second], 60, ENC, max_tokens=ENC.count(second))
    assert out[1] == second


def test_first_child_is_never_given_a_carry():
    first = _text(400)
    out = apply_overlap([first, _text(400)], 60, ENC, max_tokens=MAX)
    assert out[0] == first


def test_overlap_still_starts_on_a_sentence_boundary_when_trimmed():
    out = apply_overlap([_text(300), _text(515)], 60, ENC, max_tokens=MAX)
    carry = out[1][: len(out[1]) - len(_text(515))]
    assert carry.strip().startswith("Coastal"), carry


# --- the invariant on the final emitted children ---------------------------- #
#
# Coalescing and overlap are both capped above, but `pack` sizes a window by
# summing atom counts while the emitted text is the joined string. These tests
# go through the whole path and assert on real Chunk objects.


def _children(chunks):
    return [c for c in chunks if not c.is_parent]


def _assert_within_cap(chunks, config) -> None:
    children = _children(chunks)
    assert children
    worst = max(c.token_count for c in children)
    assert worst <= config.child_max_tokens, (
        f"largest child {worst} tokens exceeds child_max_tokens "
        f"{config.child_max_tokens}"
    )
    # token_count must describe the text that is actually stored.
    for child in children:
        assert child.token_count == ENC.count(child.text)


def test_window_texts_splits_a_window_that_exceeds_the_cap():
    """`pack` can hand over an oversized window; the enforcement point splits it
    on existing boundaries instead of truncating."""
    text = "\n\n".join(_text(300) for _ in range(4))  # ~1200 tokens as one window
    out = window_texts([[Block("text", text, 0, 1)]], overlap=60, max_tokens=MAX, enc=ENC)
    assert len(out) > 1
    assert all(ENC.count(t) <= MAX for _, t in out), [ENC.count(t) for _, t in out]
    # Nothing dropped: every word of the source survives somewhere.
    joined = " ".join(t for _, t in out)
    assert all(word in joined for word in set(text.split()))


def test_split_pieces_keep_their_window_blocks():
    """Page and table metadata come from blocks, so pieces must keep them."""
    block = Block("table", "\n\n".join(_text(300) for _ in range(3)), 0, 21)
    out = window_texts([[block]], overlap=0, max_tokens=MAX, enc=ENC)
    assert len(out) > 1
    assert all(blocks == [block] for blocks, _ in out)


@pytest.mark.parametrize("preset", ["pdf", "article", "report", "policy", "small_pdf"])
def test_no_emitted_child_exceeds_the_cap_for_any_preset(preset):
    config = config_for(preset)
    meta = DocumentMeta(document_id="d", source_type="pdf", title="Panaji Case Study")
    body = "Coastal infrastructure needs sustained adaptation investment now. " * 400
    text = f"1. Introduction\n\n{body}\n\n2. Methodology\n\n{body}"
    _assert_within_cap(chunk_document(text, meta, config=config), config)


def test_no_emitted_child_exceeds_the_cap_with_a_table_at_the_limit():
    """The reported shape: a table atom packed to the cap beside a short note."""
    config = config_for("pdf")
    meta = DocumentMeta(document_id="d", source_type="pdf", title="T")
    rows = "\n".join(f"| Zone {i} | Water Supply | {i * 7} |" for i in range(120))
    text = f"3.1 Zone Vulnerabilities\n\n{rows}\n\nA short trailing note.\n"
    _assert_within_cap(chunk_pages([(21, text)], meta, config=config), config)


_WORDS = (
    "supply", "zone", "assessment", "sewerage", "transport", "altinho",
    "flood", "prone", "elevation", "heritage", "khazan", "mangrove",
)


def _uneven_paragraphs(n: int) -> str:
    """Many short paragraphs of uneven token length — the shape that makes
    `pack`'s sum-of-atoms sizing drift from the joined text's real count."""
    return "\n\n".join(
        " ".join(_WORDS[(i * 7 + j) % len(_WORDS)] for j in range(1 + i % 5))
        for i in range(n)
    )


def test_no_emitted_child_exceeds_the_cap_when_target_equals_max():
    """With no headroom, `pack`'s sum-based sizing drifts past the cap: summing
    atom counts is not the same as counting the joined window. Without the
    enforcement point this document emits children of ~690 tokens."""
    config = ChunkingConfig(
        child_target_tokens=MAX, child_max_tokens=MAX, child_min_tokens=MIN,
        child_overlap_tokens=60,
    )
    meta = DocumentMeta(document_id="d", source_type="pdf", title="T")
    _assert_within_cap(chunk_document(_uneven_paragraphs(700), meta, config=config), config)
