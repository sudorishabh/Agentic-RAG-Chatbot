"""Unit tests for the fuzzy scoring engine behind entity resolution
(app.retrieval.structured.resolve). Pure functions — no DB, no LLM.

Score assertions use the exact values the implementation produces (verified
by running the real module, not hand-computed) so a future change to the
scoring formula that shifts these numbers is caught; band assertions are the
behavioral contract that actually matters downstream.
"""

from __future__ import annotations

import pytest

from app.retrieval.structured import resolve

AUTHORS = ["Rishabh Negi", "Rishab Nigam", "A K Sharma", "Meena Sehgal", "TERI Web Desk"]
THEMES = ["Climate Change", "Environment", "Environment and Public Health", "Energy",
          "Sustainable Agriculture", "Green Shipping"]
BUNDLES = ["events", "news", "research_papers", "policy_brief", "report"]


def _rank(query: str, pool: list[str]) -> tuple[float, str, float]:
    ranked = sorted(((resolve.score(query, c), c) for c in pool), reverse=True)
    top_score, top_name = ranked[0]
    runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
    return top_score, top_name, runner_up


# --------------------------------------------------------------------------- #
# score() — similarity in [0, 1].
# --------------------------------------------------------------------------- #

def test_exact_match_is_perfect():
    assert resolve.score("Rishabh Negi", "Rishabh Negi") == 1.0


def test_exact_match_is_case_and_punctuation_insensitive():
    assert resolve.score("RISHABH-NEGI", "Rishabh Negi") == 1.0
    assert resolve.score("environment", "Environment") == 1.0


def test_word_order_does_not_matter():
    assert resolve.score("negi rishabh", "Rishabh Negi") == 1.0


def test_misspelling_scores_highly():
    # missing the second "h" in "Rishabh" — a real fuzzy-match case from §2.
    assert resolve.score("rishab negi", "Rishabh Negi") == pytest.approx(0.9565, abs=1e-3)


def test_unrelated_strings_score_low():
    assert resolve.score("zzznonexistent", "Rishabh Negi") == pytest.approx(0.3077, abs=1e-3)


def test_empty_query_or_candidate_never_matches():
    assert resolve.score("", "Rishabh Negi") == 0.0
    assert resolve.score("Rishabh Negi", "") == 0.0
    assert resolve.score("", "") == 0.0


def test_filler_words_are_stripped_before_scoring():
    """"env theme" reduces to "env" before comparison — the generic descriptor
    word must not dilute the match against the word that names the entity."""
    assert resolve.score("env theme", "Environment") == resolve.score("env", "Environment")
    assert resolve.score("events bundle", "events") == resolve.score("events", "events")


def test_only_curated_filler_words_are_stripped():
    """Common English words ("the", "of") are not filler words — stripping
    them is out of scope, so this still scores via the substring boost rather
    than an exact "waste"-alone match."""
    assert resolve.score("the theme of waste", "Waste") == pytest.approx(0.7083, abs=1e-3)
    assert resolve.score("the theme of waste", "Waste") != resolve.score("waste", "Waste")


def test_all_filler_query_is_not_stripped_to_nothing():
    # "theme" alone has no content word left after stripping; falls back to
    # comparing the original token rather than an empty string.
    assert resolve._content_tokens(["theme"]) == ["theme"]
    assert resolve.score("theme", "theme") == 1.0
    assert resolve.score("theme", "Environment") > 0.0


def test_single_token_prefix_match_discounted_by_candidate_length():
    """An exact hit on a candidate's only word beats an exact hit on one word
    of a much longer candidate — otherwise "environment" would tie "Environment"
    against "Environment and Public Health" instead of preferring the exact
    name."""
    exact = resolve.score("environment", "Environment")
    partial = resolve.score("environment", "Environment and Public Health")
    assert exact == 1.0
    assert partial < exact
    assert partial == pytest.approx(0.6897, abs=1e-3)


def test_prefix_bonus_does_not_apply_to_multi_token_queries():
    """A single strong token match must not carry a multi-token query — two
    different people can share a first name, and one aligned token says
    nothing about whether the rest of the name also corresponds."""
    # "rishab" alone matches "Rishab Nigam"'s first name exactly, but
    # "rishab negi" must not inherit that strength against the wrong person.
    assert resolve.score("rishab negi", "Rishab Nigam") == pytest.approx(0.7826, abs=1e-3)
    assert resolve.score("rishab negi", "Rishabh Negi") > resolve.score(
        "rishab negi", "Rishab Nigam"
    )


# --------------------------------------------------------------------------- #
# classify_band() — ACCEPT / AMBIGUOUS / MISS from top + runner-up scores.
# --------------------------------------------------------------------------- #

def test_clear_misspelling_accepts():
    top, _, runner_up = _rank("rishab negi", AUTHORS)
    assert resolve.classify_band(top, runner_up) == resolve.ACCEPT


def test_exact_full_name_accepts():
    top, _, runner_up = _rank("rishabh negi", AUTHORS)
    assert resolve.classify_band(top, runner_up) == resolve.ACCEPT


def test_genuine_tie_is_ambiguous_not_a_silent_guess():
    """"rishab" matches two different real people almost identically — must
    ask, never silently pick one (§4)."""
    top, _, runner_up = _rank("rishab", AUTHORS)
    assert top == runner_up == 0.75
    assert resolve.classify_band(top, runner_up) == resolve.AMBIGUOUS


def test_dominant_partial_match_accepts_despite_moderate_absolute_score():
    """"climate" only scores 0.75 against "Climate Change" in absolute terms,
    but nothing else comes close — a moderate score with no real competition
    should still resolve confidently, not force an unnecessary clarification."""
    top, name, runner_up = _rank("climate", THEMES)
    assert name == "Climate Change"
    assert resolve.classify_band(top, runner_up) == resolve.ACCEPT


def test_close_partial_matches_are_ambiguous():
    """"env theme" is genuinely close between two real, different themes —
    must ask rather than guess which "environment" theme is meant."""
    top, _, runner_up = _rank("env theme", THEMES)
    assert resolve.classify_band(top, runner_up) == resolve.AMBIGUOUS


def test_unrelated_query_misses():
    top, _, runner_up = _rank("zzznonexistent", AUTHORS)
    assert resolve.classify_band(top, runner_up) == resolve.MISS


def test_no_runner_up_defaults_to_zero():
    assert resolve.classify_band(1.0) == resolve.ACCEPT
    assert resolve.classify_band(0.0) == resolve.MISS
