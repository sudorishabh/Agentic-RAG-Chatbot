"""Unit tests for entity candidate sourcing and the resolve_entity orchestrator
(app.retrieval.structured.resolve). Candidate sources are stubbed; no DB.
Scoring behavior itself is covered by test_entity_resolution_scoring.py.
"""

from __future__ import annotations

import pytest

from app.retrieval.structured import resolve


@pytest.fixture(autouse=True)
def _clear_author_cache():
    """The author name list is process-cached (lru_cache) — clear it around
    every test so one test's monkeypatched DB never leaks into another's."""
    resolve.reload_authors()
    yield
    resolve.reload_authors()


# --------------------------------------------------------------------------- #
# _bundle_candidates — in-memory, no DB.
# --------------------------------------------------------------------------- #

def test_bundle_exact_synonym_returns_single_confident_candidate():
    """A known synonym ("policy" -> policy_brief) is a sure thing — no need to
    also fuzzy-rank the other 15 bundles against it."""
    candidates = resolve._bundle_candidates("policy")
    assert len(candidates) == 1
    assert candidates[0].id == "policy_brief"
    assert candidates[0].type == resolve.BUNDLE
    assert candidates[0].score == 1.0


def test_bundle_unknown_query_scores_against_every_bundle():
    candidates = resolve._bundle_candidates("evnts")
    names = {c.id for c in candidates}
    assert "events" in names
    assert len(candidates) == 16  # every DEFAULT_BUNDLES entry is scored
    top = max(candidates, key=lambda c: c.score)
    assert top.id == "events"


# --------------------------------------------------------------------------- #
# _theme_candidates — the documents_theme vocabulary.
# --------------------------------------------------------------------------- #

def test_theme_candidates_read_the_theme_vocabulary(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: [
            {"theme": "Climate Change", "theme_type": "primary", "parent": None,
             "theme_group": "main", "documents": 3},
            {"theme": "Environment", "theme_type": "primary", "parent": None,
             "theme_group": "main", "documents": 5},
        ],
    )
    candidates = resolve._theme_candidates("climate")
    # The catalog keys themes by name, so id and canonical_name are the same.
    assert {c.id for c in candidates} == {"Climate Change", "Environment"}
    top = max(candidates, key=lambda c: c.score)
    assert top.id == top.canonical_name == "Climate Change"


def test_theme_candidates_empty_vocabulary_yields_nothing(monkeypatch):
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: [])
    assert resolve._theme_candidates("climate") == []


def test_theme_candidates_degrade_to_empty_on_query_failure(monkeypatch):
    def boom(**kw):
        raise RuntimeError("mysql down")

    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", boom)
    assert resolve._theme_candidates("climate") == []


# --------------------------------------------------------------------------- #
# _author_candidates — cached distinct-author list.
# --------------------------------------------------------------------------- #

def test_author_candidates_scored_against_every_distinct_author(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.distinct_authors", lambda **kw: ["Rishabh Negi", "A K Sharma"]
    )
    candidates = resolve._author_candidates("rishab negi")
    assert {c.id for c in candidates} == {"Rishabh Negi", "A K Sharma"}
    top = max(candidates, key=lambda c: c.score)
    assert top.id == "Rishabh Negi"


def test_author_name_list_is_cached_across_calls(monkeypatch):
    calls = []

    def fake_distinct_authors(**kw):
        calls.append(1)
        return ["Rishabh Negi"]

    monkeypatch.setattr("app.catalog.queries.distinct_authors", fake_distinct_authors)
    resolve._author_candidates("rishabh")
    resolve._author_candidates("negi")
    assert len(calls) == 1  # second call served from the cache


def test_reload_authors_clears_the_cache(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.distinct_authors", lambda **kw: ["Rishabh Negi"]
    )
    resolve._author_candidates("rishabh")
    monkeypatch.setattr(
        "app.catalog.queries.distinct_authors", lambda **kw: ["A K Sharma"]
    )
    resolve.reload_authors()
    candidates = resolve._author_candidates("sharma")
    assert {c.id for c in candidates} == {"A K Sharma"}


def test_author_candidates_degrade_to_empty_on_query_failure(monkeypatch):
    def boom(**kw):
        raise RuntimeError("mysql down")

    monkeypatch.setattr("app.catalog.queries.distinct_authors", boom)
    assert resolve._author_candidates("rishab") == []


# --------------------------------------------------------------------------- #
# resolve_entity — the merging/ranking orchestrator.
# --------------------------------------------------------------------------- #

def test_resolve_entity_narrows_to_one_type(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.distinct_authors", lambda **kw: ["Rishabh Negi", "Rishab Nigam"]
    )
    candidates = resolve.resolve_entity("rishab", type="author")
    assert candidates and all(c.type == resolve.AUTHOR for c in candidates)


def test_resolve_entity_merges_all_types_when_type_omitted(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary",
        lambda **kw: [{"theme": "Climate Change", "theme_type": "primary",
                       "parent": None, "theme_group": "main", "documents": 3}],
    )
    monkeypatch.setattr("app.catalog.queries.distinct_authors", lambda **kw: ["Rishabh Negi"])
    candidates = resolve.resolve_entity("climate")
    types_present = {c.type for c in candidates}
    # A real answer for "climate" only needs the theme; bundle/author candidates
    # merely need to have been considered and ranked below it.
    assert resolve.THEME in types_present
    assert candidates[0].canonical_name == "Climate Change"


def test_resolve_entity_ranks_highest_score_first(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.distinct_authors",
        lambda **kw: ["Zzz Nonexistent", "Rishabh Negi"],
    )
    candidates = resolve.resolve_entity("rishabh negi", type="author")
    assert [c.id for c in candidates] == ["Rishabh Negi", "Zzz Nonexistent"]


def test_resolve_entity_clamps_to_limit(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.distinct_authors",
        lambda **kw: [f"Author {i}" for i in range(10)],
    )
    candidates = resolve.resolve_entity("author", type="author", limit=3)
    assert len(candidates) == 3


def test_resolve_entity_empty_query_returns_no_candidates():
    assert resolve.resolve_entity("") == []
    assert resolve.resolve_entity("   ") == []


def test_resolve_entity_rejects_unadvertised_type():
    """tag is a filter, not an advertised resolve_entity type (§3) — a caller
    asking for it gets a clear error, not a silent fall-through to merging
    every type."""
    with pytest.raises(ValueError):
        resolve.resolve_entity("policy", type="tag")
