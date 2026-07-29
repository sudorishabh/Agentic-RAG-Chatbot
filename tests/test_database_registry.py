"""Phase 1 infrastructure: entity registry + scope resolver. No DB / network."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.retrieval import structured as db
from app.retrieval.structured import entities, filters, resolve


# --------------------------------------------------------------------------- #
# Entity registry.
# --------------------------------------------------------------------------- #

def test_normalize_entity_canonicalizes_free_text():
    assert entities.normalize_entity("news") == "news"
    assert entities.normalize_entity("press release") == "press_release"  # spaces
    assert entities.normalize_entity("event") == "events"                 # plural variant
    assert entities.normalize_entity("person") == "people"                # synonym
    assert entities.normalize_entity("papers") == "research_papers"       # synonym via stem
    assert entities.normalize_entity(None) is None


def test_is_known_and_get_entity():
    assert entities.is_known("news") is True
    assert entities.is_known("tenders") is False        # not a Drupal bundle
    assert entities.is_known(entities.normalize_entity("widgets")) is False

    ent = entities.get_entity("press release")
    assert ent is not None
    assert ent.name == "press_release"
    assert ent.source_type == "website" and ent.entity_type == "node"
    assert entities.get_entity("nonsense") is None


def test_entity_label_singular_plural():
    assert entities.entity_label("news", 1) == "news item"
    assert entities.entity_label("news", 2) == "news items"
    assert entities.entity_label("report", 2) == "reports"
    assert entities.entity_label("widget", 1) == "widget"   # generic fallback
    assert entities.entity_label("widget", 2) == "widgets"


# --------------------------------------------------------------------------- #
# Scope resolver. Themes and tags are keyed by name — see
# tests/test_filter_resolution.py for the name-matching behaviour itself; this
# section covers what `resolve_filters` hands to the catalog readers.
# --------------------------------------------------------------------------- #

def _theme_vocab(*names):
    return [{"theme": n, "theme_type": "primary", "parent": None,
             "theme_group": "main", "documents": 3} for n in names]


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """No catalog behind these tests unless a case stubs one."""
    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", lambda **kw: [])
    monkeypatch.setattr("app.catalog.queries.find_tag", lambda name: None)
    monkeypatch.setattr("app.catalog.queries.distinct_authors", lambda **kw: [])
    resolve.reload_authors()
    yield
    resolve.reload_authors()


def test_resolve_theme_returns_the_canonical_name(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary", lambda **kw: _theme_vocab("Climate Change")
    )
    assert filters.resolve_theme("climate") == "Climate Change"


def test_resolve_theme_keeps_an_unmatched_name(monkeypatch):
    assert filters.resolve_theme("Nonexistent") == "Nonexistent"


def test_resolve_theme_blank_is_none():
    assert filters.resolve_theme(None) is None
    assert filters.resolve_theme("") is None


def test_resolve_theme_degrades_on_error(monkeypatch):
    def boom(**kw):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.catalog.queries.theme_vocabulary", boom)
    assert filters.resolve_theme("Climate") == "Climate"


def test_resolve_tag_matches_exactly_and_returns_stored_casing(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.find_tag",
        lambda name: "Waste management" if name.strip().lower() == "waste management" else None,
    )
    assert filters.resolve_tag("waste MANAGEMENT") == "Waste management"


def test_resolve_tag_keeps_an_unmatched_name(monkeypatch):
    assert filters.resolve_tag("nonexistent") == "nonexistent"


def test_resolve_tag_degrades_on_error(monkeypatch):
    def boom(name):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.catalog.queries.find_tag", boom)
    assert filters.resolve_tag("policy") == "policy"


def test_resolve_filters_passes_names_and_dates_to_the_readers(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary", lambda **kw: _theme_vocab("Climate Change")
    )
    monkeypatch.setattr("app.catalog.queries.distinct_authors", lambda **kw: ["A K Sharma"])
    resolve.reload_authors()
    scope = filters.resolve_filters(
        db.RecordFilters(
            theme="climate", author="Sharma", title_contains="grid",
            date_from="2024-01-01", date_to="2025-01-01",
        )
    )
    assert scope.published_from == datetime(2024, 1, 1)
    assert scope.published_to == datetime(2025, 1, 1)
    # as_kwargs carries author + theme + dates, but NOT title_contains
    assert scope.as_kwargs() == {
        "author": "A K Sharma",
        "theme": "Climate Change",
        "published_from": datetime(2024, 1, 1),
        "published_to": datetime(2025, 1, 1),
    }
    assert scope.title_contains == "grid"  # passed separately by list/lookup


def test_resolve_filters_carries_theme_and_tag_together(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.queries.theme_vocabulary", lambda **kw: _theme_vocab("Energy")
    )
    monkeypatch.setattr("app.catalog.queries.find_tag",
                        lambda name: "solar" if name.lower() == "solar" else None)
    scope = filters.resolve_filters(db.RecordFilters(theme="Energy", tag="solar"))
    assert scope.as_kwargs() == {"theme": "Energy", "tag": "solar"}


def test_resolve_filters_empty_is_empty():
    scope = filters.resolve_filters(db.RecordFilters())
    assert scope.as_kwargs() == {}
    assert scope.ambiguous is None
    assert not (scope.author_missed or scope.theme_missed or scope.tag_missed)


def test_bad_date_is_ignored():
    scope = filters.resolve_filters(db.RecordFilters(date_from="not-a-date"))
    assert scope.published_from is None
