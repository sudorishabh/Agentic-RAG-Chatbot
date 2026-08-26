"""Unit tests for the volatile-topic lexicon that widens the relevance band."""

from __future__ import annotations

import pytest

from app.retrieval.volatility import is_volatile


@pytest.mark.parametrize("query", [
    "what changed in the v3 API?",
    "current pricing for the rooftop programme",
    "which regulations apply to biomass co-firing?",
    "summarize the new solar policy",
    "what were the emission targets announced last month?",
    "latest annual report findings",
    "what is the most recent guidance on EV subsidies?",
    "has the tariff been updated?",
    "press release about the hydrogen mission",
    "what are the compliance deadlines?",
])
def test_volatile_queries_are_detected(query):
    assert is_volatile(query)


@pytest.mark.parametrize("query", [
    "how does anaerobic digestion work?",
    "what is the chemical composition of fly ash?",
    "explain the methodology used in the household survey",
    "who wrote the chapter on groundwater depletion?",
    "describe the geography of the Sundarbans",
])
def test_stable_queries_are_not(query):
    assert not is_volatile(query)


def test_matching_is_case_insensitive():
    assert is_volatile("LATEST API Pricing")


def test_terms_must_be_whole_words():
    """'apinventory' or 'lawn' must not read as 'api' or 'law' — a stray
    substring should not widen the band."""
    assert not is_volatile("apinventory of lawn species")


def test_an_empty_query_is_not_volatile():
    assert not is_volatile("")
