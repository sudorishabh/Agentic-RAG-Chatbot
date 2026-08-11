"""`child_max_tokens` is a hard limit, not a target.

Three independent paths used to push a child past the configured cap: coalescing
merged windows that did not fit, overlap prepended its carry after every size
check, and `pack` sizes windows by summing atom counts while the emitted text is
the joined string. These tests pin the limit at each path and on the final child.
"""

from __future__ import annotations

from app.ingestion.chunking.packer import apply_overlap, coalesce_windows, get_encoder
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
