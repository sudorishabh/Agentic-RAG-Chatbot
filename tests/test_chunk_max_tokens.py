"""`child_max_tokens` is a hard limit, not a target.

Three independent paths used to push a child past the configured cap: coalescing
merged windows that did not fit, overlap prepended its carry after every size
check, and `pack` sizes windows by summing atom counts while the emitted text is
the joined string. These tests pin the limit at each path and on the final child.
"""

from __future__ import annotations

from app.ingestion.chunking.packer import coalesce_windows, get_encoder
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
