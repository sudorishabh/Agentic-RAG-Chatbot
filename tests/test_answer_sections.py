"""The two-block answer structure.

Covers the prompt contract, the parsing the frontend and the verification passes
share, and the sources footer that has to agree with the blocks above it. The
tags come from a model, so the malformed cases matter as much as the happy path.
No network.
"""

from __future__ import annotations

from app.core.models.context import ContextBlock
from app.generation import answerer
from app.generation.faithfulness import FaithfulnessReport
from app.generation.prompts import (
    GROUNDED_SYSTEM_PROMPT,
    PDF_LEAD,
    PDF_TAG,
    SINGLE_SOURCE_SYSTEM_PROMPT,
    WEBSITE_TAG,
    format_directive,
    grounded_system_prompt,
    has_mixed_sources,
)
from app.generation.sections import (
    PDF,
    PLAIN,
    WEBSITE,
    split_sections,
    strip_tags,
)
from app.pipeline import query_pipeline as pipe
from app.retrieval import query_processor as qp


def _web(body):
    return f"<{WEBSITE_TAG}>\n{body}\n</{WEBSITE_TAG}>"


def _pdf(body):
    return f"<{PDF_TAG}>\n{PDF_LEAD}\n{body}\n</{PDF_TAG}>"


def _kinds(answer):
    return [s.kind for s in split_sections(answer)]


# --------------------------------------------------------------------------- #
# split_sections — the shapes the prompt asks for.


def test_both_blocks_parse_in_order():
    sections = split_sections(_web("Grew 1.2 GW [1].") + "\n" + _pdf("60% commercial [2]."))
    assert [s.kind for s in sections] == [WEBSITE, PDF]
    assert sections[0].text == "Grew 1.2 GW [1]."
    assert sections[1].text == f"{PDF_LEAD}\n60% commercial [2]."


def test_website_only_yields_one_section():
    assert _kinds(_web("Grew 1.2 GW [1].")) == [WEBSITE]


def test_pdf_only_yields_one_section():
    assert _kinds(_pdf("60% commercial [2].")) == [PDF]


def test_untagged_answer_is_a_single_plain_section():
    sections = split_sections("I don't have information on that.")
    assert [s.kind for s in sections] == [PLAIN]
    assert sections[0].text == "I don't have information on that."


def test_empty_answer_yields_no_sections():
    assert split_sections("") == []
    assert split_sections("   \n\n  ") == []


# --------------------------------------------------------------------------- #
# split_sections — model non-compliance and truncated streams.


def test_pdf_block_emitted_first_is_reordered_behind_website():
    # The prompt forbids this ordering; the parser enforces it regardless.
    assert _kinds(_pdf("60% commercial [2].") + _web("Grew 1.2 GW [1].")) == [
        WEBSITE,
        PDF,
    ]


def test_repeated_blocks_of_one_kind_merge():
    sections = split_sections(_web("First [1].") + _web("Second [2]."))
    assert [s.kind for s in sections] == [WEBSITE]
    assert sections[0].text == "First [1].\n\nSecond [2]."


def test_unterminated_block_runs_to_the_end():
    sections = split_sections(f"<{WEBSITE_TAG}>\nGrew 1.2 GW [1].")
    assert [s.kind for s in sections] == [WEBSITE]
    assert sections[0].text == "Grew 1.2 GW [1]."


def test_empty_block_is_dropped_rather_than_rendered():
    assert _kinds(_web("Grew 1.2 GW [1].") + f"<{PDF_TAG}>\n\n</{PDF_TAG}>") == [WEBSITE]


def test_unpaired_close_tag_never_reaches_the_output():
    sections = split_sections(f"Plain text.</{PDF_TAG}>")
    assert [s.kind for s in sections] == [PLAIN]
    assert sections[0].text == "Plain text."


def test_tag_casing_and_inner_whitespace_are_tolerated():
    answer = f"<{WEBSITE_TAG.upper()} >\nGrew 1.2 GW [1].\n</{WEBSITE_TAG} >"
    assert _kinds(answer) == [WEBSITE]


# --------------------------------------------------------------------------- #
# split_sections — untagged text keeps its position around the blocks.


def test_catalog_prefix_stays_above_the_blocks():
    answer = "We hold 4 reports.\n\n" + _web("Grew 1.2 GW [1].")
    sections = split_sections(answer)
    assert [s.kind for s in sections] == [PLAIN, WEBSITE]
    assert sections[0].text == "We hold 4 reports."


def test_trailing_remark_stays_below_the_blocks():
    sections = split_sections(_web("Grew 1.2 GW [1].") + "\nAsk me for more.")
    assert [s.kind for s in sections] == [WEBSITE, PLAIN]
    assert sections[-1].text == "Ask me for more."


# --------------------------------------------------------------------------- #
# strip_tags — what the faithfulness and numeric checks see.


def test_strip_tags_removes_wrappers_and_keeps_content():
    stripped = strip_tags(_web("Grew 1.2 GW [1].") + "\n" + _pdf("60% commercial [2]."))
    assert WEBSITE_TAG not in stripped
    assert PDF_TAG not in stripped
    assert "Grew 1.2 GW [1]." in stripped
    assert "60% commercial [2]." in stripped


def test_strip_tags_collapses_the_gaps_left_by_removal():
    assert "\n\n\n" not in strip_tags(_web("A [1].") + "\n\n" + _pdf("B [2]."))


def test_strip_tags_leaves_an_untagged_answer_alone():
    assert strip_tags("I don't have information on that.") == (
        "I don't have information on that."
    )


# --------------------------------------------------------------------------- #
# The prompt contract. Asserted structurally rather than by prose match, so
# rewording the rules stays free while the demonstrated shape stays pinned.


def _demonstrated_blocks(text, start_at=0):
    """The span from a website opening tag through the next PDF closing tag."""
    start = text.index(f"<{WEBSITE_TAG}>", start_at)
    close = f"</{PDF_TAG}>"
    return text[start : text.index(close, start) + len(close)]


def test_prompt_names_both_block_tags():
    assert f"<{WEBSITE_TAG}>" in GROUNDED_SYSTEM_PROMPT
    assert f"<{PDF_TAG}>" in GROUNDED_SYSTEM_PROMPT


def test_prompt_states_the_structure_before_demonstrating_it():
    assert GROUNDED_SYSTEM_PROMPT.index("Answer structure") < (
        GROUNDED_SYSTEM_PROMPT.index("Example:")
    )


def test_prompt_template_parses_as_the_two_blocks():
    # The shape the prompt specifies must be the shape the parser reads, or the
    # prompt teaches a format the frontend cannot render.
    sections = split_sections(_demonstrated_blocks(GROUNDED_SYSTEM_PROMPT))
    assert [s.kind for s in sections] == [WEBSITE, PDF]
    assert sections[1].text.startswith(PDF_LEAD)


def test_prompt_worked_example_parses_as_the_two_blocks():
    example_at = GROUNDED_SYSTEM_PROMPT.index("Example:")
    demonstrated = _demonstrated_blocks(GROUNDED_SYSTEM_PROMPT, example_at)
    assert [s.kind for s in split_sections(demonstrated)] == [WEBSITE, PDF]


def test_prompt_ends_by_demonstrating_the_dropped_pdf_block():
    # Omitting the PDF block is the rule a model most readily ignores, so the
    # prompt has to show it, not just describe it.
    tail = GROUNDED_SYSTEM_PROMPT[GROUNDED_SYSTEM_PROMPT.rindex(f"</{PDF_TAG}>") :]
    assert f"<{WEBSITE_TAG}>" in tail
    assert f"<{PDF_TAG}>" not in tail


def test_format_directives_are_scoped_inside_the_blocks():
    for fmt in ("list", "table", "summary", "detailed", "timeline"):
        assert WEBSITE_TAG in format_directive(fmt), fmt
    # The default path stays lean: no directive, so no scope note either.
    assert format_directive("default") == ""


# --------------------------------------------------------------------------- #
# The single-source prompt. A context of one source kind has nothing to split
# along, so the structure the mixed prompt teaches must be absent entirely —
# left in, it makes the model manufacture a block and restate the answer in it.


def test_single_source_prompt_never_mentions_the_block_structure():
    for token in (WEBSITE_TAG, PDF_TAG, PDF_LEAD):
        assert token not in SINGLE_SOURCE_SYSTEM_PROMPT, token


def test_single_source_prompt_asks_for_one_continuous_answer():
    assert "one continuous answer" in SINGLE_SOURCE_SYSTEM_PROMPT


def test_single_source_worked_example_parses_as_plain_text():
    # The demonstrated answer is what the model copies, so it has to read as an
    # untagged whole to the same parser the frontend mirrors.
    example = SINGLE_SOURCE_SYSTEM_PROMPT[
        SINGLE_SOURCE_SYSTEM_PROMPT.index("Example:") :
    ]
    assert _kinds(example) == [PLAIN]


def test_grounded_system_prompt_selects_by_context_composition():
    assert grounded_system_prompt(mixed=True) == GROUNDED_SYSTEM_PROMPT
    assert grounded_system_prompt(mixed=False) == SINGLE_SOURCE_SYSTEM_PROMPT


def test_both_prompt_variants_share_the_rule_numbering():
    # app.generation.answerer appends the history rule as "9.", so neither
    # variant may add or drop a numbered rule.
    for prompt in (GROUNDED_SYSTEM_PROMPT, SINGLE_SOURCE_SYSTEM_PROMPT):
        for n in range(1, 9):
            assert f"\n{n}. " in f"\n{prompt}", (n, prompt[:40])
        assert "\n9. " not in prompt


def test_single_source_format_directives_name_no_wrappers():
    for fmt in ("list", "table", "summary", "detailed", "timeline"):
        directive = format_directive(fmt, mixed=False)
        assert WEBSITE_TAG not in directive, fmt
        assert PDF_TAG not in directive, fmt
        assert "this shape wins" in directive, fmt


def test_format_directives_outrank_the_general_style_guidance():
    # A detected shape reads this user's explicit intent, so "summarize briefly"
    # must not lose to the always-on instruction to answer thoroughly.
    assert "this shape wins" in format_directive("summary")


def test_prompt_states_the_style_between_the_structure_and_the_example():
    structure = GROUNDED_SYSTEM_PROMPT.index("Answer structure")
    style = GROUNDED_SYSTEM_PROMPT.index("Answer style:")
    assert structure < style < GROUNDED_SYSTEM_PROMPT.index("Example:")


def test_prompt_guards_added_depth_against_padding():
    # Asking a grounded model for fuller answers invites padding; the guard that
    # ties every added sentence back to the context has to survive rewording.
    style = GROUNDED_SYSTEM_PROMPT[GROUNDED_SYSTEM_PROMPT.index("Answer style:") :]
    assert "never from padding" in style


# --------------------------------------------------------------------------- #
# Which structure a given context asks for. The retrieved blocks decide it —
# the model is never asked to infer the composition and suppress the split
# itself, which is what produced a duplicated PDF section on PDF-only pulls.


def _blocks(*source_types):
    return [
        ContextBlock(n=i, text=f"Passage {i}.", payload={"source_type": st})
        for i, st in enumerate(source_types, start=1)
    ]


def test_mixed_sources_needs_both_kinds_present():
    assert has_mixed_sources(_blocks("website", "pdf"))
    assert has_mixed_sources(_blocks("pdf", "website", "pdf_attachment"))
    assert not has_mixed_sources(_blocks("pdf", "pdf"))
    assert not has_mixed_sources(_blocks("website", "website"))
    # Every non-website kind counts as PDF, so these are single-source.
    assert not has_mixed_sources(_blocks("pdf", "pdf_attachment"))
    assert not has_mixed_sources([])


def test_pdf_only_context_is_answered_without_the_block_structure():
    system = answerer._build_system(
        None, None, mixed=has_mixed_sources(_blocks("pdf", "pdf_attachment"))
    )
    assert WEBSITE_TAG not in system
    assert PDF_TAG not in system
    assert PDF_LEAD not in system


def test_mixed_context_keeps_the_block_structure():
    system = answerer._build_system(
        None, None, mixed=has_mixed_sources(_blocks("website", "pdf"))
    )
    assert f"<{WEBSITE_TAG}>" in system
    assert f"<{PDF_TAG}>" in system


def test_correction_note_defers_to_the_structure_already_in_force():
    # A retry runs through the same prompt as the draft it replaces, so a note
    # that named the blocks itself would push a single-source rewrite back into
    # the split the prompt just forbade.
    note = FaithfulnessReport(faithful=False, unsupported=["1.2 GW"]).correction_note()
    for token in (WEBSITE_TAG, PDF_TAG, PDF_LEAD, "answer-block"):
        assert token not in note, token


def test_corrected_pdf_only_answer_is_still_asked_for_one_block():
    system = answerer._build_system(
        "table",
        FaithfulnessReport(faithful=False).correction_note(),
        mixed=has_mixed_sources(_blocks("pdf", "pdf")),
    )
    for token in (WEBSITE_TAG, PDF_TAG, PDF_LEAD):
        assert token not in system, token


def test_history_rule_continues_the_numbering_of_either_variant():
    for mixed in (True, False):
        system = answerer._build_system(None, None, mixed=mixed, has_history=True)
        assert "\n9. " in system
        assert "\n10. " not in system


# --------------------------------------------------------------------------- #
# The sources footer lists what the answer cited, not everything retrieved.


def _generation():
    blocks = [
        ContextBlock(
            n=1, text="The programme added 1.2 GW in 2023.",
            payload={"source_type": "website", "title": "Rooftop Push"},
        ),
        ContextBlock(
            n=2, text="Commercial installations were 60% of capacity.",
            payload={"source_type": "pdf", "title": "Annual Report"},
        ),
    ]
    return pipe._Generation(
        pq=qp.ProcessedQuery(
            understanding=None, original="q", search_query="q", intent="qa"
        ),
        blocks=blocks, query_vector=[0.0], tenant_id="default",
        user_groups=["public"], top_k=6,
    )


def _cited(answer):
    return [c["n"] for c in pipe._assemble(answer, _generation())["citations"]]


def test_footer_lists_both_sources_when_both_blocks_cite():
    assert _cited(_web("Added 1.2 GW [1].") + _pdf("60% commercial [2].")) == [1, 2]


def test_dropped_pdf_block_leaves_no_pdf_chip():
    # The rule that makes the footer agree with the answer: a PDF the model
    # rightly left out must not resurface as a source under it.
    out = pipe._assemble(_web("Added 1.2 GW [1]."), _generation())
    assert [c["type"] for c in out["citations"]] == ["website"]


def test_pdf_only_answer_lists_the_pdf_alone():
    assert _cited(_pdf("60% commercial [2].")) == [2]


def test_uncited_answer_keeps_every_source():
    assert _cited(_web("The programme added capacity.")) == [1, 2]


def test_used_chunks_still_counts_what_retrieval_supplied():
    out = pipe._assemble(_web("Added 1.2 GW [1]."), _generation())
    assert out["used_chunks"] == 2


def test_tags_do_not_register_as_unverified_figures():
    out = pipe._assemble(_web("Added 1.2 GW in 2023 [1]."), _generation())
    assert out["numeric_mismatch"] is False
