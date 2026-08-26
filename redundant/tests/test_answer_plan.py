"""Unit tests for the evidence-coverage plan (app.generation.answer_plan).

Regression cover for Q001: retrieval found the authoritative Mission and Goals
page and the answer still omitted the twelve stated goals and all six values,
both present on the same page — retrieval succeeded and generation
under-delivered. The fix computed here is a per-question checklist: decompose
the question into its distinct asked-for parts, check each one against the
actual retrieved text (lexical, deterministic, no LLM), and only then hand
generation an explicit per-item directive.

The LLM call (``extract_requirements``) is mocked throughout — these tests
pin the deterministic half of the mechanism: coverage checking and directive
rendering, both of which must never invent a fact or a match that is not
actually in the text.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.generation import answer_plan as ap


def _block(n, text):
    return SimpleNamespace(n=n, text=text)


# --------------------------------------------------------------------------- #
# 1. The single-requirement no-op — the ordinary case, and why it must be one.
# --------------------------------------------------------------------------- #

def test_a_single_requirement_produces_no_directive():
    """The overwhelming majority of questions ask for one thing. Emitting a
    directive here would be pure prompt noise on every one of them, so this
    must be silent — the base prompt already handles a single-part question."""
    plan = ap.build_plan(["mission"], [_block(1, "TERI's mission is to usher...")])
    assert plan.supported == ["mission"]
    assert plan.unsupported == []
    assert ap.plan_directive(plan) == ""


def test_zero_requirements_produces_no_directive():
    plan = ap.build_plan([], [_block(1, "some text")])
    assert ap.plan_directive(plan) == ""


# --------------------------------------------------------------------------- #
# 2. Multi-part coverage: supported vs unsupported, decided lexically.
# --------------------------------------------------------------------------- #

def test_q001_shaped_question_flags_the_unstated_vision():
    """The pinned regression: "mission and vision" with a page that states the
    mission and never uses the word "vision" at all."""
    blocks = [_block(1, "TERI's mission is to usher in a cleaner and "
                        "sustainable future through conservation and "
                        "efficient use of energy and other resources.")]
    plan = ap.build_plan(["mission", "vision"], blocks)
    assert plan.supported == ["mission"]
    assert plan.unsupported == ["vision"]


def test_every_requirement_supported_still_gets_a_directive_when_there_are_two():
    """Two supported parts is still worth an explicit "cover both" push — the
    single-item exemption is specifically about length, not about accuracy."""
    blocks = [_block(1, "TERI's mission is X. TERI's vision is Y.")]
    plan = ap.build_plan(["mission", "vision"], blocks)
    assert plan.supported == ["mission", "vision"]
    assert plan.unsupported == []
    directive = ap.plan_directive(plan)
    assert "mission" in directive and "vision" in directive
    assert "does not specify" not in directive


def test_multi_word_requirements_match_on_any_content_word():
    """Deliberately permissive: one content word is enough to count as
    supported, because the failure mode of a bad match must be "the directive
    says nothing" (harmless — identical to before this module existed), never
    "the directive wrongly tells the model to disclaim something the text
    actually covers"."""
    blocks = [_block(1, "The green building rating system was jointly developed.")]
    plan = ap.build_plan(["mission", "green building rating"], blocks)
    assert "green building rating" in plan.supported


def test_a_requirement_with_no_matchable_words_is_unsupported():
    blocks = [_block(1, "completely unrelated content about something else")]
    plan = ap.build_plan(["mission", "zzzznotarealword"], blocks)
    assert "zzzznotarealword" in plan.unsupported


# --------------------------------------------------------------------------- #
# 3. The directive text: what it says, and what it must never say.
# --------------------------------------------------------------------------- #

def test_the_directive_names_every_requirement():
    plan = ap.AnswerPlan(
        requirements=["mission", "vision", "goals"],
        supported=["mission", "goals"], unsupported=["vision"],
    )
    directive = ap.plan_directive(plan)
    for word in ("mission", "vision", "goals"):
        assert word in directive


def test_the_directive_never_asserts_a_fact_only_names_dimensions():
    """No block text is ever quoted into the directive — it can only name which
    dimensions are supported or not, never repeat or paraphrase what the
    evidence says. That is what makes it impossible for this mechanism to
    introduce a fact generation did not already have in the numbered context."""
    plan = ap.build_plan(
        ["mission", "vision"],
        [_block(1, "TERI's mission is to usher in a cleaner future through "
                   "conservation of energy and resources for everyone alive.")],
    )
    directive = ap.plan_directive(plan)
    # The block's own sentence must not appear verbatim in the directive.
    assert "usher in a cleaner future" not in directive


def test_unsupported_items_are_told_to_be_disclaimed_not_invented():
    plan = ap.AnswerPlan(requirements=["mission", "vision"],
                         supported=["mission"], unsupported=["vision"])
    directive = ap.plan_directive(plan)
    assert "vision" in directive
    assert "invent" in directive.lower()


def test_a_partly_supported_plan_discourages_a_blanket_refusal():
    """Phase 5's principle operationalised: at least one supported part is
    explicit license not to refuse the whole question."""
    plan = ap.AnswerPlan(requirements=["mission", "vision"],
                         supported=["mission"], unsupported=["vision"])
    directive = ap.plan_directive(plan)
    assert "do not refuse the whole question" in directive.lower()


def test_when_nothing_is_supported_there_is_no_false_reassurance():
    """If every part is unsupported there is no "at least one part is
    answered" line — that would be a fabricated claim about the evidence."""
    plan = ap.AnswerPlan(requirements=["a", "b"], supported=[], unsupported=["a", "b"])
    directive = ap.plan_directive(plan)
    assert "at least one part" not in directive.lower()


# --------------------------------------------------------------------------- #
# 4. extract_requirements: fails open, never fabricates a requirement count.
# --------------------------------------------------------------------------- #

def test_extraction_failure_fails_open_to_empty(monkeypatch):
    """A broken LLM call must degrade to exactly today's behaviour: no plan,
    no directive, generation unaffected."""
    import app.core.clients.llm as llm_mod

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(llm_mod, "get_structured_llm", boom)
    assert ap.extract_requirements("What is TERI's mission and vision?") == []


def test_a_blank_question_extracts_nothing():
    assert ap.extract_requirements("") == []
    assert ap.extract_requirements("   ") == []


def test_extraction_is_capped_so_a_bad_llm_answer_cannot_bloat_the_prompt(monkeypatch):
    class _Result:
        requirements = [f"item{i}" for i in range(20)]

    class _Model:
        def with_structured_output(self, cls):
            return self

        def invoke(self, messages):
            return _Result()

    import app.core.clients.llm as llm_mod

    monkeypatch.setattr(llm_mod, "get_structured_llm", lambda: _Model())
    result = ap.extract_requirements("some compound question")
    assert len(result) <= 6


# --------------------------------------------------------------------------- #
# 5. Determinism: build_plan and plan_directive are pure functions.
# --------------------------------------------------------------------------- #

def test_build_plan_and_directive_are_deterministic():
    blocks = [_block(1, "TERI's mission is to usher in a cleaner future.")]
    results = {
        ap.plan_directive(ap.build_plan(["mission", "vision"], blocks))
        for _ in range(10)
    }
    assert len(results) == 1
