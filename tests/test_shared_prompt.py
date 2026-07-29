"""Unit tests for the shared DB-slot prompt text (app.retrieval.structured.prompt)
and its use by the three prompts that previously hand-duplicated it: the intent
classifier, the slot-extraction fallback, and the v2 tool-calling planner.
No LLM, no network — these check the composed prompt strings only.
"""

from __future__ import annotations

from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES
from app.retrieval.structured import prompt
from app.retrieval.structured import answerer
from app.retrieval.structured import planner
from app.retrieval.understanding import prompts as understanding_prompts


# --------------------------------------------------------------------------- #
# The blocks themselves.
# --------------------------------------------------------------------------- #

def test_bundle_list_matches_default_bundles():
    assert prompt.BUNDLE_LIST == ", ".join(DEFAULT_BUNDLES)


def test_vocabulary_names_synonyms_and_the_bundle_word():
    assert "articles" in prompt.VOCABULARY and "items" in prompt.VOCABULARY
    assert "bundle" in prompt.VOCABULARY


def test_collective_word_warning_names_publications():
    assert "publications" in prompt.COLLECTIVE_WORD_WARNING
    assert "research_papers" in prompt.COLLECTIVE_WORD_WARNING


def test_resolve_first_excepts_tag():
    assert "resolve_entity" in prompt.RESOLVE_FIRST
    assert "tag" in prompt.RESOLVE_FIRST


def test_behavior_covers_ambiguity_and_no_fabrication():
    assert "Ambiguity" in prompt.BEHAVIOR
    assert "No fabrication" in prompt.BEHAVIOR
    assert "Main themes" in prompt.BEHAVIOR


def test_few_shots_cover_every_worked_example():
    for marker in (
        "Rishabh Negi", "How many events are there", "How many themes",
        "Climate Change", "content_type", "source links", "tagged 'policy'",
        "Ambiguous:", "Miss:",
    ):
        assert marker in prompt.FEW_SHOTS, marker


# --------------------------------------------------------------------------- #
# planner._PLANNER_SYSTEM — the only prompt that should gain resolve_entity.
# --------------------------------------------------------------------------- #

def test_planner_system_advertises_resolve_entity_tool():
    assert "- resolve_entity:" in planner._PLANNER_SYSTEM


def test_planner_system_includes_every_shared_block():
    for block in (
        prompt.BUNDLE_LIST, prompt.VOCABULARY, prompt.RESOLVE_FIRST,
        prompt.OPERATIONS, prompt.BEHAVIOR, prompt.COLLECTIVE_WORD_WARNING,
        prompt.FEW_SHOTS,
    ):
        assert block in planner._PLANNER_SYSTEM


# --------------------------------------------------------------------------- #
# answerer._PARSE_SYSTEM and understanding._SYSTEM — reuse the vocabulary/
# bundle-list blocks only; neither does multi-step tool calling, so neither
# gains resolve_entity or the few-shots.
# --------------------------------------------------------------------------- #

def test_parse_system_reuses_shared_bundle_and_vocabulary_blocks():
    assert prompt.BUNDLE_LIST in answerer._PARSE_SYSTEM
    assert prompt.COLLECTIVE_WORD_WARNING in answerer._PARSE_SYSTEM
    assert prompt.VOCABULARY in answerer._PARSE_SYSTEM
    assert "resolve_entity" not in answerer._PARSE_SYSTEM


def test_understanding_system_reuses_shared_bundle_block():
    assert prompt.BUNDLE_LIST in understanding_prompts.UNDERSTANDING_SYSTEM
    assert prompt.COLLECTIVE_WORD_WARNING in understanding_prompts.UNDERSTANDING_SYSTEM
    assert "resolve_entity" not in understanding_prompts.UNDERSTANDING_SYSTEM


def test_bundle_list_is_not_duplicated_by_hand_in_any_consumer():
    """Regression guard for the drift this module exists to prevent: none of
    the three consumers should hand-build ", ".join(DEFAULT_BUNDLES) anymore."""
    import inspect

    for module in (answerer, planner, understanding_prompts):
        source = inspect.getsource(module)
        assert "DEFAULT_BUNDLES" not in source
