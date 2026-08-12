"""Taxonomy is metadata on a document, never a document of its own.

A term's uuid already travels in the payload of every content chunk that
references it (`term_ids` / `theme_ids`), and that is what theme and tag
filtering match on. Crawling the term as well records the same fact a second
time as a near-empty document — most vocabularies carry no description at all —
and puts it in front of retrieval, where it can be returned instead of the
content it was only meant to label.

Leaving taxonomy out of the default source list is not enough to prevent that:
`--bundle` and `POST /ingest/run` both accept an arbitrary "entity_type:bundle"
spec. So the rule is enforced on the one path that reaches chunking and Qdrant,
and these tests hold it there.

Both halves are covered — no taxonomy source can be crawled, and a content
node's taxonomy references survive untouched. The extractor, the catalog and the
network are stubbed; no MySQL, no Qdrant, no HTTP.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from app.core.models import EntityRef
from app.ingestion.change_detection import drupal
from app.ingestion.extractors import drupal_extractor as de

# Every vocabulary the live site publishes, as measured against the JSON:API.
TAXONOMY_BUNDLES = [
    "tags", "partners", "region", "related_terms", "division_areas", "themes",
    "division", "stakeholders", "extra_pages", "programs_units",
    "regional_centre", "language",
]


def _node(uuid: str = "n-1", *, bundle: str = "report", refs=()) -> SimpleNamespace:
    return SimpleNamespace(
        uuid=uuid,
        bundle=bundle,
        nid=1,
        title="Air quality in Indian cities",
        url=f"https://teriin.org/{uuid}",
        body="A node with enough body text to survive the block filter.",
        created="2024-01-01T00:00:00+00:00",
        changed="2026-08-01T00:00:00+00:00",
        source=f"https://teriin.org/{uuid}",
        metadata={},
        refs=list(refs),
        files=[],
    )


class _Session:
    def close(self) -> None:
        pass


@pytest.fixture
def fetched(monkeypatch):
    """Records which (entity_type, bundle) sources the crawl actually fetches."""
    seen: list[tuple[str, str]] = []

    monkeypatch.setattr(
        drupal, "get_settings",
        lambda: SimpleNamespace(drupal_max_retries=1, drupal_block_min_chars=200),
    )
    monkeypatch.setattr(drupal.state, "load", lambda source_type: {})
    monkeypatch.setattr(drupal.dead_links, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.dead_links, "load", dict)
    monkeypatch.setattr(drupal.retries, "ensure_table", lambda: None)
    monkeypatch.setattr(drupal.retries, "floors", dict)
    monkeypatch.setattr(de, "_build_session", lambda retries: _Session())

    def iter_bundle_records(session, bundle, *, entity_type="node", **kw):
        seen.append((entity_type, bundle))
        return iter([_node(f"{entity_type}-{bundle}", bundle=bundle)])

    monkeypatch.setattr(de, "iter_bundle_records", iter_bundle_records)
    return seen


def _crawl(bundles=None) -> list:
    return list(drupal.detect_drupal_changes(bundles=bundles))


# --------------------------------------------------------------------------- #
# No taxonomy source can reach the crawl.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("bundle", TAXONOMY_BUNDLES)
def test_a_taxonomy_bundle_is_never_crawled(fetched, bundle):
    """Asked for by name, one vocabulary at a time — the way --bundle or the
    ingest API would ask."""
    records = _crawl([f"taxonomy_term:{bundle}"])

    assert fetched == [], f"taxonomy_term/{bundle} was fetched"
    assert records == [], f"taxonomy_term/{bundle} produced a document"


def test_the_default_crawl_holds_no_taxonomy_and_no_carousel(fetched):
    _crawl()

    entity_types = {entity for entity, _ in fetched}
    assert entity_types <= de.SEARCHABLE_ENTITY_TYPES
    assert "taxonomy_term" not in entity_types
    assert "carousel" not in {bundle for _, bundle in fetched}
    assert fetched, "the default crawl must still fetch something"


def test_carousel_is_not_a_default_bundle():
    assert "carousel" not in de.DEFAULT_BUNDLES


def test_a_refused_taxonomy_spec_does_not_stop_the_content_beside_it(fetched):
    """One bad spec in a list must not cost the run its real sources."""
    _crawl(["report", "taxonomy_term:themes", "block_content:basic"])

    assert fetched == [("node", "report"), ("block_content", "basic")]


def test_block_content_is_still_admitted(fetched):
    _crawl(["block_content:basic"])
    assert fetched == [("block_content", "basic")]


def test_an_unknown_entity_type_is_refused_too(fetched):
    """The allowlist is the point: a source is crawled because it was admitted,
    not because nobody thought to exclude it."""
    _crawl(["media:image", "paragraph:hero"])
    assert fetched == []


def test_a_refused_source_says_why(fetched, caplog):
    with caplog.at_level(logging.WARNING):
        _crawl(["taxonomy_term:themes"])

    message = caplog.text
    assert "taxonomy_term/themes" in message
    assert "metadata" in message


# --------------------------------------------------------------------------- #
# The other half: content keeps its taxonomy.
# --------------------------------------------------------------------------- #

def test_a_crawled_node_keeps_its_taxonomy_references(monkeypatch, fetched):
    """Refusing taxonomy *sources* must not touch the taxonomy *metadata* a
    content node carries — that is the whole point of the distinction."""
    refs = [
        EntityRef("field_theme", "t-energy", "taxonomy_term--themes", "Energy"),
        EntityRef("field_tags", "t-solar", "taxonomy_term--tags", "Solar"),
    ]

    def iter_bundle_records(session, bundle, *, entity_type="node", **kw):
        return iter([_node("n-1", bundle=bundle, refs=refs)])

    monkeypatch.setattr(de, "iter_bundle_records", iter_bundle_records)

    record = next(r for r in _crawl(["report"]) if r.source_type == "website")
    assert [r.uuid for r in record.payload.refs] == ["t-energy", "t-solar"]


def test_taxonomy_uuids_survive_into_the_chunk_payload(monkeypatch, fetched):
    """All the way to what Qdrant stores: theme and tag filtering match on these
    ids, so they must outlive the decision to stop crawling the terms."""
    from app.ingestion.canonical import from_drupal_record
    from app.ingestion.chunking import chunk_canonical

    refs = [
        EntityRef("field_theme", "t-energy", "taxonomy_term--themes", "Energy"),
        EntityRef("field_tags", "t-solar", "taxonomy_term--tags", "Solar"),
    ]

    def iter_bundle_records(session, bundle, *, entity_type="node", **kw):
        return iter([_node("n-1", bundle=bundle, refs=refs)])

    monkeypatch.setattr(de, "iter_bundle_records", iter_bundle_records)

    record = next(r for r in _crawl(["report"]) if r.source_type == "website")
    doc = from_drupal_record(record.payload)
    payload = next(c for c in chunk_canonical(doc) if not c.is_parent).to_payload()

    assert payload["term_ids"] == ["t-energy", "t-solar"], "every vocabulary"
    assert payload["theme_ids"] == ["t-energy"], "themes only, for theme filters"
    assert "Energy" in payload["categories"]
