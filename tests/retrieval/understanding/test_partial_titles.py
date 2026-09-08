"""Recognising a project named by part of its title.

No DB: the index is built from literals, because what is under test is the two
guards, not the loader. The recurring assertion is the pair — a real partial
title is found, and a run of ordinary words that happens to be unique is not.
"""

from __future__ import annotations

import pytest

from app.retrieval.understanding import partial_titles as pt


def _index(titles: dict[str, str]) -> pt.PartialTitleIndex:
    """Build an index from ``entity_id -> canonical title`` without MySQL."""
    from app.knowledge.normalize import normalize_project

    index = pt.PartialTitleIndex()
    for entity_id, canonical in titles.items():
        normalized = normalize_project(canonical)
        tokens = normalized.split()
        if len(tokens) < pt.SHINGLE_TOKENS:
            continue
        index.projects[entity_id] = (canonical, normalized)
        for token in set(tokens):
            index.token_df[token] = index.token_df.get(token, 0) + 1
        for i in range(len(tokens) - pt.SHINGLE_TOKENS + 1):
            shingle = " ".join(tokens[i : i + pt.SHINGLE_TOKENS])
            index.owners.setdefault(shingle, set()).add(entity_id)
    return index


# Enough repetition of "project on solar" to be representative, though the
# distinctiveness floor is exercised separately: in a corpus this small every
# word is rare, so those tests state the real frequencies instead.
CORPUS = {
    "project_aaaaaaaaaaaa": "Heavy metal assessment of Yamuna River Water",
    "project_bbbbbbbbbbbb": "Films on Energy Efficiency for IREDA",
    "project_cccccccccccc": "A study on the role of Discoms in solar rooftop systems",
    "project_dddddddddddd": "Pilot project on solar PV based charging for e-bikes",
    "project_eeeeeeeeeeee": "A project on solar water pumps for farmers",
    "project_ffffffffffff": "Demonstration project on solar cold storage",
    "project_gggggggggggg": "Assessment of a project on solar street lighting",
    "project_hhhhhhhhhhhh": "Review of the project on rural electrification",
}


# --------------------------------------------------------------------------- #
# What it finds
# --------------------------------------------------------------------------- #

def test_a_project_named_by_part_of_its_title_is_found():
    """The whole point: the stored title is not what anybody types."""
    matches = _index(CORPUS).match("Who leads the Yamuna River Water project?")
    assert [m.entity_id for m in matches] == ["project_aaaaaaaaaaaa"]
    assert matches[0].canonical_name == "Heavy metal assessment of Yamuna River Water"


def test_the_span_covers_what_the_user_wrote_not_the_stored_title():
    """The router masks resolved spans before reading relational cues, so a span
    claiming more than the user wrote would blank out their own question."""
    question = "Who leads the Yamuna River Water project?"
    match = _index(CORPUS).match(question)[0]
    assert question[match.start : match.end] == "Yamuna River Water"


def test_the_longest_run_wins():
    question = "Who leads Heavy metal assessment of Yamuna River?"
    match = _index(CORPUS).match(question)[0]
    assert question[match.start : match.end] == "Heavy metal assessment of Yamuna River"


# --------------------------------------------------------------------------- #
# What it refuses — the two guards
# --------------------------------------------------------------------------- #

def test_a_phrase_two_projects_share_names_neither():
    """Uniqueness is the veto. Both solar titles contain "on solar", so a
    question using it identifies nothing and must not pick one."""
    corpus = {
        "project_1111": "A study of solar rooftop systems in Delhi",
        "project_2222": "A study of solar rooftop systems in Mumbai",
    }
    assert _index(corpus).match("Tell me about the study of solar rooftop systems") == []


def test_a_unique_run_of_ordinary_words_is_still_refused():
    """Uniqueness alone is not distinctiveness.

    "project on solar" really does occur in exactly one title, so the uniqueness
    guard admits it — and it names no project. Every token in it is corpus-wide
    filler, which is what the document-frequency floor is for.

    Frequencies are set to their measured values over the real 1,054 titles
    rather than emerging from a handful of literals: in a corpus this small
    every word is rare, so the guard could only ever be exercised by saying what
    the corpus actually looks like.
    """
    index = _index({"project_dddddddddddd": "Pilot project on solar PV based charging"})
    index.projects.update({f"project_{i:012d}": ("t", "t") for i in range(1054)})
    index.token_df.update({
        "pilot": 21, "project": 67, "on": 188, "solar": 38, "pv": 12,
        "based": 30, "charging": 9,
    })
    assert index._distinctive_max_df == 10
    assert index.match("Who leads the project on solar PV based systems?") == []


def test_a_rare_token_in_the_run_is_what_admits_it():
    """The other half of the same guard: identical shape, one rare word."""
    index = _index({"project_aaaaaaaaaaaa": "Heavy metal assessment of Yamuna River"})
    index.projects.update({f"project_{i:012d}": ("t", "t") for i in range(1054)})
    index.token_df.update({
        "heavy": 3, "metal": 1, "assessment": 45, "of": 495, "yamuna": 4,
        "river": 6,
    })
    matches = index.match("Who leads the assessment of Yamuna River?")
    assert [m.entity_id for m in matches] == ["project_aaaaaaaaaaaa"]


def test_a_run_shorter_than_the_floor_is_refused():
    assert _index(CORPUS).match("Tell me about IREDA") == []


def test_a_question_naming_no_project_finds_nothing():
    for question in (
        "What is the weather today?",
        "Tell me about climate change",
        "How many projects are there?",
    ):
        assert _index(CORPUS).match(question) == []


# --------------------------------------------------------------------------- #
# Mentions
# --------------------------------------------------------------------------- #

def test_the_mention_carries_the_canonical_name_and_its_own_provenance():
    """Surface is the stored title so the resolver's exact-name tier finds it;
    the version stamp is distinct from `approved-alias-v1` because this matched
    a *part* of a title rather than a whole reviewed alias."""
    mentions = pt.lookup_mentions(
        "Who leads the Yamuna River Water project?", index=_index(CORPUS)
    )
    assert len(mentions) == 1
    assert mentions[0].surface_text == "Heavy metal assessment of Yamuna River Water"
    assert mentions[0].entity_type == "PROJECT"
    assert mentions[0].extractor_version == pt.EXTRACTOR_VERSION


def test_lookup_never_raises_when_the_index_cannot_load(monkeypatch):
    """Recognition must never break a query, matching every other pass."""
    def _boom() -> None:
        raise RuntimeError("no database")

    monkeypatch.setattr(pt, "get_index", _boom)
    assert pt.lookup_mentions("Who leads the Yamuna River Water project?") == []


# --------------------------------------------------------------------------- #
# The distinctiveness floor itself
# --------------------------------------------------------------------------- #

def test_the_floor_scales_with_the_corpus_but_never_below_its_minimum():
    small = _index({"project_1111": "Heavy metal assessment of Yamuna River Water"})
    assert small._distinctive_max_df == pt.DISTINCTIVE_DF_FLOOR

    big = pt.PartialTitleIndex()
    big.projects = {f"project_{i:012d}": ("t", "t") for i in range(1000)}
    assert big._distinctive_max_df == int(1000 * pt.DISTINCTIVE_DF_SHARE)
