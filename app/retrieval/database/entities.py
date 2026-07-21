"""Entity registry for the Database capability.

An "entity" is a Drupal content bundle (news, research_papers, events, ...) — all
`source_type='website', entity_type='node'` rows in the catalog. There are no
per-entity tables and no per-entity tools: the bundle is a query parameter, so
registering a content type is a data change here.

This module is the canonical home for the bundle synonyms and display labels
(summarizer and the catalog tools resolve entities through here). See
docs/database-tool-registry.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES

# Free-text content types (from the LLM or the user) that plural/singular matching
# won't map to a known bundle.
_BUNDLE_SYNONYMS: dict[str, str] = {
    "person": "people",
    "paper": "research_papers",
    "policy": "policy_brief",
    "brief": "policy_brief",
    "news_article": "news",
    "press": "press_release",
}

# Display (singular, plural) forms for count/list answers. Bundle names are
# inconsistently pluralized, so map the known ones; anything else is humanized.
_BUNDLE_LABELS: dict[str, tuple[str, str]] = {
    "news": ("news item", "news items"),
    "events": ("event", "events"),
    "feature_articles": ("feature article", "feature articles"),
    "completed_projects": ("completed project", "completed projects"),
    "ongoing_projects": ("ongoing project", "ongoing projects"),
    "press_release": ("press release", "press releases"),
    "research_papers": ("research paper", "research papers"),
    "policy_brief": ("policy brief", "policy briefs"),
    "videos": ("video", "videos"),
    "infographics": ("infographic", "infographics"),
    "services": ("service", "services"),
    "people": ("person", "people"),
    "article": ("article", "articles"),
    "report": ("report", "reports"),
    "page": ("page", "pages"),
    "carousel": ("carousel", "carousels"),
    "items": ("item", "items"),
}


def entity_label(scope: str, n: int) -> str:
    """Singular/plural display label for a bundle (or any scope word), e.g.
    ('news', 1) -> 'news item'. Unknown scopes are humanized best-effort."""
    forms = _BUNDLE_LABELS.get(scope)
    if forms:
        return forms[0] if n == 1 else forms[1]
    human = scope.replace("_", " ")
    if n == 1:
        return human[:-1] if human.endswith("s") else human
    return human if human.endswith("s") else f"{human}s"


@dataclass(frozen=True)
class Entity:
    """How a catalog entity is queried. Every entity today is a website node; the
    source_type/entity_type binding lets a future non-Drupal source register with
    a different backing without touching the tools."""

    name: str
    source_type: str = "website"
    entity_type: str | None = "node"

    def label(self, n: int) -> str:
        return entity_label(self.name, n)


# Registered content entities, keyed by canonical bundle name.
_REGISTRY: dict[str, Entity] = {bundle: Entity(name=bundle) for bundle in DEFAULT_BUNDLES}


def normalize_entity(raw: str | None) -> str | None:
    """Map a free-text content type ('event', 'press release', 'person') to a
    canonical bundle name, or None for empty input. An unrecognized type returns
    its cleaned key (callers validate with `is_known` — a bad entity must count as
    zero, not as everything)."""
    if not raw:
        return None
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in _REGISTRY:
        return key
    for variant in (f"{key}s", key.rstrip("s")):
        if variant in _REGISTRY:
            return variant
    return _BUNDLE_SYNONYMS.get(key) or _BUNDLE_SYNONYMS.get(key.rstrip("s"), key)


def is_known(name: str | None) -> bool:
    """True when `name` (already normalized) is a registered content entity."""
    return bool(name) and name in _REGISTRY


def get_entity(name: str | None) -> Entity | None:
    """Resolve a (possibly free-text) entity name to a registered Entity, or None
    when it is empty or unrecognized."""
    canonical = normalize_entity(name)
    return _REGISTRY.get(canonical) if canonical else None
