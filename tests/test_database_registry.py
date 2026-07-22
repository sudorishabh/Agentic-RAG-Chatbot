"""Phase 1 infrastructure: entity registry + scope resolver. No DB / network."""

from __future__ import annotations

from datetime import datetime

from app.retrieval import structured as db
from app.retrieval.structured import entities, filters


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
# Scope resolver.
# --------------------------------------------------------------------------- #

def test_resolve_theme_prefers_term_uuids(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.terms.resolve_terms",
        lambda name, vocabulary=None: [{"term_uuid": "u1", "name": "Climate"}],
    )
    assert filters.resolve_theme("Climate") == {"term_uuids": ["u1"]}


def test_resolve_theme_falls_back_to_category(monkeypatch):
    monkeypatch.setattr("app.catalog.terms.resolve_terms", lambda *a, **k: [])
    assert filters.resolve_theme("Nonexistent") == {"category": "Nonexistent"}


def test_resolve_theme_degrades_on_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.catalog.terms.resolve_terms", boom)
    assert filters.resolve_theme("Climate") == {"category": "Climate"}


def test_resolve_filters_resolved_theme(monkeypatch):
    monkeypatch.setattr(
        "app.catalog.terms.resolve_terms",
        lambda *a, **k: [{"term_uuid": "u1", "name": "Climate"}],
    )
    scope = filters.resolve_filters(
        db.RecordFilters(
            theme="Climate", author="Sharma", title_contains="grid",
            date_from="2024-01-01", date_to="2025-01-01",
        )
    )
    assert scope.term_uuids == ["u1"]
    assert scope.theme_requested is True and scope.theme_resolved is True
    assert scope.published_from == datetime(2024, 1, 1)
    assert scope.published_to == datetime(2025, 1, 1)
    # as_kwargs carries author + theme + dates, but NOT title_contains
    kwargs = scope.as_kwargs()
    assert kwargs == {
        "author": "Sharma",
        "term_uuids": ["u1"],
        "published_from": datetime(2024, 1, 1),
        "published_to": datetime(2025, 1, 1),
    }
    assert scope.title_contains == "grid"  # passed separately by list/lookup


def test_resolve_filters_unresolved_theme_uses_category(monkeypatch):
    monkeypatch.setattr("app.catalog.terms.resolve_terms", lambda *a, **k: [])
    scope = filters.resolve_filters(db.RecordFilters(theme="Mystery"))
    assert scope.term_uuids is None
    assert scope.category == "Mystery"
    assert scope.theme_requested is True and scope.theme_resolved is False
    assert scope.as_kwargs() == {"category": "Mystery"}


def test_resolve_filters_empty_is_empty():
    scope = filters.resolve_filters(db.RecordFilters())
    assert scope.as_kwargs() == {}
    assert scope.theme_requested is False and scope.theme_resolved is False


def test_bad_date_is_ignored(monkeypatch):
    scope = filters.resolve_filters(db.RecordFilters(date_from="not-a-date"))
    assert scope.published_from is None
