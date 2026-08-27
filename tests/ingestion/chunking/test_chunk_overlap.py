"""Tests for sentence-aware overlap carry between child chunks."""

from __future__ import annotations

from app.ingestion.chunking.packer import apply_overlap, get_encoder, overlap_carry

ENC = get_encoder("cl100k_base")


def test_overlap_starts_at_sentence_boundary():
    prev = "reducing emissions is hard. The introduction of new low carbon tech is required."
    carry = overlap_carry(prev, 60, ENC)
    assert carry.startswith("The introduction")  # leading partial sentence dropped


def test_apply_overlap_child_starts_cleanly():
    prev = "Some earlier prose. This sentence completes the prior chunk."
    nxt = "Next chunk body begins here."
    out = apply_overlap([prev, nxt], 60, ENC, max_tokens=560)
    assert out[1].startswith("This sentence completes")


def test_abbreviation_is_not_a_boundary():
    prev = "costs (Hall et. al, 2020) varied across the routes considered here."
    carry = overlap_carry(prev, 60, ENC)
    assert carry.startswith("costs")  # "et. al," must not split the sentence


def test_overlap_without_boundary_returns_tail():
    prev = "onelongfragmentwithnoboundary"
    assert overlap_carry(prev, 60, ENC) == "onelongfragmentwithnoboundary"
