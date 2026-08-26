"""The planner-to-query-function mapping, asserted end to end without a database.

The claim this file defends is narrow and total: **a structured question reaches
exactly one authoritative catalog function, chosen deterministically from typed
slots.** No SQL is generated from natural language, no function is selected by
name from model output, and a slot value the code does not recognise stops the
query rather than steering it somewhere plausible.

Each test drives `planner.plan(...)` and then `planner.execute(...)` with the
catalog readers replaced by recorders, so what is asserted is the function that
*would* have been called and the arguments it would have received. Numerical
correctness is a separate concern, checked against independently written SQL by
`scripts/verify_catalog_counts.py`.
"""
from __future__ import annotations

import typing
from types import SimpleNamespace

import pytest

from app.retrieval.structured import planner, tools
from app.retrieval.structured.types import RecordFilters, ToolResult


def _slots(**kw):
    base = dict(
        operation=None, bundle=None, theme=None, author=None, title_contains=None,
        group_by=None, secondary_group_by=None, count_of="records",
        date_from=None, date_to=None, tags=None, limit=10,
    )
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.fixture
def calls(monkeypatch):
    """Record which catalog reader the plan reaches, and with what."""
    seen: list[tuple[str, dict]] = []

    def _record(name, result):
        def _fn(*args, **kwargs):
            seen.append((name, {"args": args, **kwargs}))
            return result
        return _fn

    monkeypatch.setattr(tools.state, "count_documents", _record("count_documents", 7))
    monkeypatch.setattr(
        tools.state, "count_distinct_values", _record("count_distinct_values", 5)
    )
    monkeypatch.setattr(
        tools.state, "distribution", _record("distribution", [("Energy", 3)])
    )
    monkeypatch.setattr(
        tools.state, "cross_distribution",
        _record("cross_distribution", [("Sharma", "Energy", 2)]),
    )
    # Resolution would otherwise hit MySQL to canonicalize names.
    monkeypatch.setattr(
        tools, "resolve_filters",
        lambda f: SimpleNamespace(
            author=f.author, theme=f.theme, tag=f.tag, theme_group=f.theme_group,
            title_contains=f.title_contains, published_from=None, published_to=None,
            effective=f, ambiguous=None,
            author_missed=False, theme_missed=False, tag_missed=False,
            as_kwargs=lambda: {
                k: v for k, v in {
                    "author": f.author, "theme": f.theme,
                    "theme_group": f.theme_group, "tag": f.tag,
                }.items() if v is not None
            },
        ),
    )
    return seen


def _run(seen, question=None, **slot_kw):
    planner.execute(planner.plan(_slots(**slot_kw), question=question),
                    question=question)
    return seen


# --------------------------------------------------------------------------- #
# 1. The mapping, one test per supported shape
# --------------------------------------------------------------------------- #


def test_count_with_records_maps_to_count_documents(calls):
    seen = _run(calls, operation="count", bundle="article", count_of="records")
    assert [name for name, _ in seen] == ["count_documents"]


def test_count_with_author_maps_to_count_distinct_values(calls):
    seen = _run(calls, operation="count", bundle="article", count_of="author")
    name, kwargs = seen[0]
    assert name == "count_distinct_values"
    assert kwargs["args"][0] == "author"


def test_count_with_theme_maps_to_count_distinct_values(calls):
    seen = _run(calls, operation="count", bundle="article", count_of="theme")
    name, kwargs = seen[0]
    assert name == "count_distinct_values"
    assert kwargs["args"][0] == "theme"


def test_count_with_content_type_maps_to_the_bundle_column(calls):
    """The slot is user-facing ("content type"); the column is `bundle`."""
    seen = _run(calls, operation="count", count_of="content_type")
    name, kwargs = seen[0]
    assert name == "count_distinct_values" and kwargs["args"][0] == "bundle"


def test_distribution_by_author_maps_to_distribution(calls):
    seen = _run(calls, operation="distribution", bundle="article", group_by="author")
    name, kwargs = seen[0]
    assert name == "distribution" and kwargs["args"][0] == "author"


def test_distribution_by_theme_maps_to_distribution(calls):
    seen = _run(calls, operation="distribution", bundle="article", group_by="theme")
    name, kwargs = seen[0]
    assert name == "distribution" and kwargs["args"][0] == "theme"


def test_two_dimensions_map_to_cross_distribution(calls):
    seen = _run(calls, operation="distribution", bundle="article",
                group_by="author", secondary_group_by="theme")
    name, kwargs = seen[0]
    assert name == "cross_distribution"
    assert kwargs["args"][:2] == ("author", "theme")


def test_the_dimension_order_reaches_the_query_unchanged(calls):
    """`theme x author` must not silently become `author x theme`: the pair is
    transposable, the *labelling* is not."""
    seen = _run(calls, operation="distribution", group_by="theme",
                secondary_group_by="author")
    assert seen[0][1]["args"][:2] == ("theme", "author")


def test_exactly_one_query_function_runs_per_plan(calls):
    for kw in (
        dict(operation="count"),
        dict(operation="count", count_of="author"),
        dict(operation="distribution", group_by="theme"),
        dict(operation="distribution", group_by="author", secondary_group_by="theme"),
    ):
        calls.clear()
        _run(calls, **kw)
        assert len(calls) == 1, kw


# --------------------------------------------------------------------------- #
# 3. Counting documents is not counting entities
# --------------------------------------------------------------------------- #


def test_documents_and_entities_are_different_queries(calls):
    """The distinction the whole feature rests on. Same filters, same scope —
    different function, and therefore a different noun in the answer."""
    _run(calls, operation="count", bundle="article", theme="Energy")
    docs = calls[-1]
    calls.clear()
    _run(calls, operation="count", bundle="article", theme="Energy",
         count_of="author")
    authors = calls[-1]

    assert docs[0] == "count_documents"
    assert authors[0] == "count_distinct_values"
    # Identical scope; only the counted thing differs.
    assert docs[1]["theme"] == authors[1]["theme"] == "Energy"
    assert docs[1]["bundle"] == authors[1]["bundle"] == "article"


def test_counting_themes_for_an_author_is_a_distinct_count(calls):
    seen = _run(calls, operation="count", author="Sharma", count_of="theme")
    name, kwargs = seen[0]
    assert name == "count_distinct_values"
    assert kwargs["args"][0] == "theme" and kwargs["author"] == "Sharma"


# --------------------------------------------------------------------------- #
# 4. The vocabularies are finite, agree with each other, and fail closed
# --------------------------------------------------------------------------- #


def test_every_declaration_of_the_vocabulary_agrees():
    """The same allow-list is written out in five places — two Literals for the
    two slot models, one for the LLM planner, and two lookup tables. They must
    not drift: a dimension added to one and missed in another is a slot the
    model can set and the tool then refuses."""
    from app.retrieval import query_processor as qp
    from app.retrieval.structured import types as T
    from app.retrieval.structured.answerer import StructuredQuery

    count_of_sets = [
        set(typing.get_args(T.CountOf)),
        set(typing.get_args(qp.CountOf)),
        set(typing.get_args(StructuredQuery.model_fields["count_of"].annotation)),
        set(typing.get_args(
            planner._PlannedCall.model_fields["count_of"].annotation)),
        set(tools.VALID_COUNT_OF),
    ]
    assert all(s == count_of_sets[0] for s in count_of_sets), count_of_sets

    group_by_sets = [
        set(typing.get_args(T.GroupBy)),
        set(typing.get_args(qp.GroupBy)),
        set(tools.VALID_DIMENSIONS),
        set(tools._COUNT_OF_NOUNS),
    ]
    assert all(s == group_by_sets[0] for s in group_by_sets), group_by_sets


def test_count_of_is_the_dimensions_plus_records():
    assert tools.VALID_COUNT_OF == tools.VALID_DIMENSIONS | {tools.COUNT_RECORDS}


@pytest.mark.parametrize(
    "bad", ["document", "documents", "banana", "Author", "authors", "tag", "themes"]
)
def test_an_unsupported_count_of_refuses_rather_than_counting_documents(bad, calls):
    """Found in review: these all silently produced a *document* count, so "how
    many authors work on Energy" answered "62 articles" — a right number under a
    wrong noun. "document" is the worst of them, being the obvious spelling for
    someone who has not read the enum."""
    result = tools.count_records("article", RecordFilters(), count_of=bad)
    assert result.ok is False
    assert "unsupported count_of" in result.error
    assert calls == [], "nothing may reach the database"


@pytest.mark.parametrize("bad", ["banana", "Author", "tag", "records"])
def test_an_unsupported_group_by_refuses(bad, calls):
    """`group_by='Author'` used to return a *theme* breakdown."""
    result = tools.aggregate_records("article", bad, RecordFilters())
    assert result.ok is False
    assert "unsupported group_by" in result.error
    assert calls == []


@pytest.mark.parametrize("unset", [None, ""])
def test_an_unset_count_of_still_means_documents(unset, calls):
    result = tools.count_records("article", RecordFilters(), count_of=unset)
    assert result.ok is True
    assert calls[0][0] == "count_documents"


def test_an_unset_group_by_still_means_theme(calls):
    tools.aggregate_records("article", None, RecordFilters())
    assert calls[0][1]["args"][0] == "theme"


def test_an_unsupported_secondary_degrades_to_one_dimension(calls):
    """The secondary is optional, so dropping it yields a narrower *correct*
    answer rather than a wrong one — but the reported dimensions must say so."""
    result = tools.aggregate_records(
        "article", "author", RecordFilters(), secondary_group_by="banana"
    )
    assert result.ok is True
    assert calls[0][0] == "distribution"
    assert result.data["dimensions"] == ["author"]


def test_a_repeated_dimension_is_the_single_dimension_question(calls):
    result = tools.aggregate_records(
        "article", "author", RecordFilters(), secondary_group_by="author"
    )
    assert calls[0][0] == "distribution"
    assert result.data["dimensions"] == ["author"]


def test_reported_dimensions_match_the_row_shape(calls):
    """A caller reads `dimensions` to know how to unpack `groups`; the two
    disagreeing is how a pair gets read backwards or a scalar as a pair."""
    single = tools.aggregate_records("article", "author", RecordFilters())
    assert len(single.data["dimensions"]) == len(single.data["groups"][0]) - 1

    paired = tools.aggregate_records(
        "article", "author", RecordFilters(), secondary_group_by="theme"
    )
    assert len(paired.data["dimensions"]) == len(paired.data["groups"][0]) - 1


# --------------------------------------------------------------------------- #
# 6. Main/Other survives every shape
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "kw",
    [
        dict(operation="count", count_of="theme"),
        dict(operation="distribution", group_by="theme"),
        dict(operation="distribution", group_by="author", secondary_group_by="theme"),
    ],
)
def test_a_theme_shaped_question_stays_main_scoped(kw, calls):
    """Whenever themes are a dimension of the answer, the Main default holds —
    even if the wording never says "theme"."""
    seen = _run(calls, question="How many are there?", **kw)
    assert seen[0][1].get("theme_group") == "main", kw


@pytest.mark.parametrize(
    "kw",
    [
        dict(operation="count"),
        dict(operation="count", count_of="author"),
        dict(operation="distribution", group_by="author"),
        dict(operation="distribution", group_by="content_type"),
    ],
)
def test_a_question_with_no_theme_dimension_is_not_theme_scoped(kw, calls):
    """Regression: the Main restriction used to be applied to *every* count.

    It is a join against `documents_theme`, so a document carrying no theme
    silently vanished — "how many authors are there?" answered 876 instead of
    955, and a plain document count lost 2,620 untagged documents. A theme
    restriction belongs only on a query that concerns themes.
    """
    seen = _run(calls, question="How many are there?", **kw)
    assert seen[0][1].get("theme_group") is None, kw


@pytest.mark.parametrize(
    "question,expected",
    [
        ("How many articles are under the main themes?", "main"),
        ("How many authors work on other themes?", "other"),
        ("How many authors work across all themes?", None),
        # No mention of themes at all: no restriction, not a Main default.
        ("How many articles are there?", None),
        ("How many authors are there?", None),
    ],
)
def test_the_question_decides_the_theme_group(question, expected, calls):
    seen = _run(calls, question=question, operation="count", count_of="author")
    assert seen[0][1].get("theme_group") == expected


def test_a_named_theme_lifts_the_group_restriction():
    """"How many authors work on Green Shipping" must answer even though Green
    Shipping is an Other theme."""
    from app.retrieval.structured.filters import resolve_filters

    call = planner.plan(
        _slots(operation="count", count_of="author", theme="Green Shipping"),
        question="How many authors work on Green Shipping?",
    ).calls[0]
    assert resolve_filters(call.filters).theme_group is None


# --------------------------------------------------------------------------- #
# 9 & 10. Failing safe, and leaving the old shapes alone
# --------------------------------------------------------------------------- #


def test_no_catalog_function_is_selected_by_name_from_model_output():
    """The dispatch is a chain of `if` on a closed `ToolName` literal; there is
    no lookup from a model-supplied string to a callable."""
    import inspect

    source = inspect.getsource(planner.execute) + inspect.getsource(planner._run)
    assert "getattr(" not in source
    assert "eval(" not in source and "exec(" not in source


def test_the_llm_planner_cannot_invent_a_tool():
    """`ToolName` is a closed Literal, so an unknown tool fails validation before
    it can reach `_run`."""
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        planner._PlannedCall(tool="drop_everything")


def test_an_unknown_tool_on_a_hand_built_call_is_refused():
    from app.retrieval.structured.types import DatabasePlan, ToolCall

    result = planner.execute(
        DatabasePlan(calls=[ToolCall(tool="nonexistent_tool")])  # type: ignore[arg-type]
    )
    assert result[0].ok is False and "unknown tool" in result[0].error


def test_slots_lacking_the_new_fields_plan_exactly_as_before(calls):
    """Backward compatibility: the pre-Step-4 slot object has neither field."""
    old = SimpleNamespace(
        operation="count", bundle="article", theme=None, author=None,
        title_contains=None, group_by=None, date_from=None, date_to=None, limit=10,
    )
    planner.execute(planner.plan(old))
    assert calls[0][0] == "count_documents"

    calls.clear()
    old.operation, old.group_by = "distribution", "theme"
    planner.execute(planner.plan(old))
    assert calls[0][0] == "distribution"
