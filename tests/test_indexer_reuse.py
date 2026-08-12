"""Unchanged chunks reuse their stored vector instead of being re-embedded.

Chunk ids are derived from owned content (see tests/test_chunk_identity.py), so
an unchanged chunk keeps its id across a re-index. `index_chunks` now reads the
stored vectors for those ids and skips the embedding call when `embed_hash`
still matches — the hash covers the exact string the embedder was handed, carry
and "title › heading" breadcrumb included, so anything that moves that string is
re-embedded rather than reusing a stale vector.

The store and the embedder are stubbed; no network. Embedding calls are counted
as *texts embedded*, which is what the Azure bill tracks.
"""

from __future__ import annotations

import pytest

from app.core import clients as core_clients
from app.ingestion import indexer
from app.ingestion.chunking import DocumentMeta, chunk_document
from app.ingestion.chunking.config import ChunkingConfig

# Sized so each paragraph owns one child: packing then stays put when a
# paragraph is inserted, which is what makes the insertion case meaningful.
CONFIG = ChunkingConfig(
    child_target_tokens=20, child_max_tokens=40, child_min_tokens=5,
    child_overlap_tokens=5, parent_target_tokens=100_000, parent_max_tokens=100_000,
)

A = "Alpha reports coastal erosion along the northern shoreline of the district."
B = "Bravo records groundwater salinity rising across the eastern wards each year."
C = "Charlie notes sewerage capacity unchanged despite steady population growth."
D = "Delta tracks tourist arrivals peaking through the winter festival season."

META = DocumentMeta(document_id="doc-1", source_type="pdf", title="T")


class _Store:
    """Minimal stand-in for the points collection, persistent across upserts."""

    def __init__(self) -> None:
        self.points: dict[str, object] = {}

    def retrieve(self, collection_name, ids, with_payload=None, with_vectors=False):
        return [self.points[str(i)] for i in ids if str(i) in self.points]

    def upsert(self, collection_name, points):
        for point in points:
            self.points[str(point.id)] = point


class _Embedder:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def embed_documents(self, batch):
        self.texts.extend(batch)
        # Deterministic 4-dim vector so reuse is observable.
        return [[float(len(t)), 1.0, 2.0, 3.0] for t in batch]

    def embed_query(self, text):
        return [0.0, 1.0, 2.0, 3.0]


@pytest.fixture
def store(monkeypatch):
    fake, embedder = _Store(), _Embedder()
    monkeypatch.setattr(core_clients, "ensure_collection", lambda: None)
    monkeypatch.setattr(core_clients, "get_qdrant_client", lambda: fake)
    monkeypatch.setattr(core_clients, "get_embeddings", lambda: embedder)
    fake.embedder = embedder
    return fake


def _index(text: str) -> int:
    return indexer.index_chunks(chunk_document(text, META, config=CONFIG))


def _doc(*paragraphs: str) -> str:
    return "\n\n".join(paragraphs)


def _embedded(store) -> int:
    return len(store.embedder.texts)


def _reset(store) -> None:
    store.embedder.texts.clear()


# --- Test 1: unchanged document --------------------------------------------- #

def test_first_index_embeds_every_child(store):
    _index(_doc(A, B, C, D))
    children = [c for c in chunk_document(_doc(A, B, C, D), META, config=CONFIG)
                if not c.is_parent]
    assert _embedded(store) == len(children)


def test_reindexing_an_unchanged_document_embeds_nothing(store):
    _index(_doc(A, B, C, D))
    _reset(store)
    _index(_doc(A, B, C, D))
    assert _embedded(store) == 0


def test_reused_vectors_are_the_stored_ones(store):
    _index(_doc(A, B, C, D))
    before = {pid: list(p.vector) for pid, p in store.points.items()}
    _reset(store)
    _index(_doc(A, B, C, D))
    assert {pid: list(p.vector) for pid, p in store.points.items()} == before


# --- Test 2: one chunk changed ---------------------------------------------- #

def test_editing_one_chunk_embeds_only_what_changed(store):
    _index(_doc(A, B, C, D))
    _reset(store)
    _index(_doc(A, B, C, D.replace("tourist", "visitor")))
    assert _embedded(store) == 1
    assert "visitor" in store.embedder.texts[0]


def test_unchanged_children_keep_their_points(store):
    _index(_doc(A, B, C, D))
    first = set(store.points)
    _reset(store)
    _index(_doc(A, B, C, D.replace("tourist", "visitor")))
    assert len(set(store.points) & first) >= len(first) - 2


# --- Test 3: insertion ------------------------------------------------------ #

def test_inserting_a_paragraph_embeds_it_and_only_its_neighbour(store):
    """The insertion itself, plus the chunk after it — whose overlap carry now
    comes from the new text. Everything else is reused.

    This holds while packing lands the same way. An insertion that repacks the
    surrounding windows changes their *owned* content, and those chunks are then
    legitimately new — content anchoring cannot preserve an identity whose
    content moved.
    """
    _index(_doc(A, B, C))
    _reset(store)
    _index(_doc(A, "Echo describes mangrove cover declining near the estuary mouth.", B, C))
    assert _embedded(store) == 2
    embedded = " ".join(store.embedder.texts)
    assert "Echo describes" in embedded
    assert "Charlie notes" not in embedded, "the untouched tail must be reused"


# --- Test 7: a changed carry must not reuse a stale vector ------------------ #

def test_a_chunk_whose_carry_changed_is_re_embedded(store):
    """Its id is stable, but its stored text differs, so the vector must not be
    reused — that is exactly what content_hash guards."""
    _index(_doc(A, B, C, D))
    stored = {pid: p.payload["content_hash"] for pid, p in store.points.items()}
    _reset(store)
    _index(_doc(A, B, C.replace("sewerage", "drainage"), D))
    for pid, point in store.points.items():
        if pid in stored and point.payload["content_hash"] != stored[pid]:
            assert any(point.payload["chunk_text"][:30] in t for t in store.embedder.texts), (
                "a chunk whose stored text changed was not re-embedded"
            )


def test_reuse_requires_a_matching_hash(store):
    _index(_doc(A, B, C, D))
    # Corrupt one stored reuse key: that point must be re-embedded next time.
    victim = next(pid for pid, p in store.points.items() if not p.payload["is_parent"])
    store.points[victim].payload["embed_hash"] = "stale"
    _reset(store)
    _index(_doc(A, B, C, D))
    assert _embedded(store) == 1


# --- Test 9: parent text changing must not re-embed children ---------------- #

def test_a_child_is_not_re_embedded_because_its_parent_changed(store):
    _index(_doc(A, B, C, D))
    _reset(store)
    # Editing D changes the parent's text (it spans the section) but leaves
    # A/B/C untouched; only the edited child may be embedded.
    _index(_doc(A, B, C, D.replace("winter", "summer")))
    assert _embedded(store) == 1


# --- fail-open -------------------------------------------------------------- #

def test_a_store_failure_falls_back_to_embedding_everything(store, monkeypatch):
    _index(_doc(A, B, C, D))
    _reset(store)

    def boom(*a, **k):
        raise RuntimeError("store down")

    monkeypatch.setattr(store, "retrieve", boom)
    _index(_doc(A, B, C, D))
    children = [c for c in chunk_document(_doc(A, B, C, D), META, config=CONFIG)
                if not c.is_parent]
    assert _embedded(store) == len(children)


# --- the breadcrumb is part of what gets embedded --------------------------- #
#
# A child's id and its `content_hash` both cover its own text only, so a title
# or heading edit leaves them byte-identical while changing the string the
# embedder is handed. Keying reuse on `content_hash` therefore kept a vector
# built from the old title — silently, since the payload title was refreshed.
# Each test below asserts the ids did NOT churn, so the re-embed can only be
# the reuse key doing its job.

OLD_TITLE = "Coastal Erosion Report 2019"
NEW_TITLE = "Marine Sediment Loss Study 2024"


def _meta(title: str) -> DocumentMeta:
    """Same document, different title — ids stay put, the breadcrumb moves."""
    return DocumentMeta(document_id="doc-1", source_type="pdf", title=title)


def _index_as(text: str, *, title: str) -> int:
    return indexer.index_chunks(chunk_document(text, _meta(title), config=CONFIG))


def _children_of(text: str, title: str) -> list:
    return [c for c in chunk_document(text, _meta(title), config=CONFIG) if not c.is_parent]


def _child_ids(store) -> set[str]:
    return {pid for pid, p in store.points.items() if not p.payload["is_parent"]}


def test_an_unchanged_document_and_title_reuses_every_vector(store):
    _index_as(_doc(A, B, C), title=OLD_TITLE)
    _reset(store)
    _index_as(_doc(A, B, C), title=OLD_TITLE)
    assert _embedded(store) == 0


def test_a_body_edit_re_embeds_that_chunk_with_the_title_held_still(store):
    _index_as(_doc(A, B, C), title=OLD_TITLE)
    _reset(store)
    _index_as(_doc(A, B, C.replace("sewerage", "drainage")), title=OLD_TITLE)

    assert _embedded(store) == 1
    assert "drainage" in store.embedder.texts[0]


def test_a_title_edit_re_embeds_every_child(store):
    _index_as(_doc(A, B, C), title=OLD_TITLE)
    before = _child_ids(store)
    _reset(store)
    _index_as(_doc(A, B, C), title=NEW_TITLE)

    assert _embedded(store) == len(_children_of(_doc(A, B, C), NEW_TITLE))
    assert all(NEW_TITLE in text for text in store.embedder.texts)
    assert _child_ids(store) == before, "the ids must not churn; only the input did"


def test_a_heading_edit_re_embeds_the_children_under_it(store):
    before_text = _doc("# Groundwater Salinity", A, B, C)
    after_text = _doc("# Aquifer Contamination", A, B, C)

    _index_as(before_text, title=OLD_TITLE)
    before = _child_ids(store)
    _reset(store)
    _index_as(after_text, title=OLD_TITLE)

    assert _embedded(store) == len(_children_of(after_text, OLD_TITLE))
    assert all("Aquifer Contamination" in text for text in store.embedder.texts)
    assert _child_ids(store) == before, "the ids must not churn; only the input did"


def test_repeated_identical_paragraphs_each_keep_reusing(store):
    """The same text twice in one document is two chunks, ordinal-separated.
    Both must reuse, and neither may collapse onto the other's point."""
    text = _doc(A, B, A, C)
    _index_as(text, title=OLD_TITLE)
    before = _child_ids(store)
    assert len(before) == len(_children_of(text, OLD_TITLE))

    _reset(store)
    _index_as(text, title=OLD_TITLE)

    assert _embedded(store) == 0
    assert _child_ids(store) == before


def test_a_child_records_the_hash_of_what_was_embedded(store):
    _index_as(_doc(A, B, C), title=OLD_TITLE)
    child = next(p for p in store.points.values() if not p.payload["is_parent"])

    assert child.payload["embed_hash"] != child.payload["content_hash"], (
        "text behind a breadcrumb embeds something other than the text itself"
    )


def test_parents_carry_no_embedding_hash(store):
    """They hold zero vectors and are never embedded, so there is no input to
    fingerprint — a hash there would describe a call that never happened."""
    _index_as(_doc(A, B, C), title=OLD_TITLE)
    parents = [p for p in store.points.values() if p.payload["is_parent"]]

    assert parents, "the fixture must produce a parent for this to mean anything"
    assert all("embed_hash" not in p.payload for p in parents)


# --- stale cleanup ---------------------------------------------------------- #

def test_upserted_ids_are_exactly_the_new_chunk_ids(store):
    """`delete_document(keep_ids=...)` removes everything else, so the upserted
    id set defines what survives — a deleted paragraph leaves no stale point."""
    chunks = chunk_document(_doc(A, B, C), META, config=CONFIG)
    indexer.index_chunks(chunks)
    assert set(store.points) == {c.chunk_id for c in chunks}

    smaller = chunk_document(_doc(A, C), META, config=CONFIG)
    keep = {c.chunk_id for c in smaller}
    indexer.index_chunks(smaller)
    stale = set(store.points) - keep
    assert all("Bravo" not in store.points[pid].payload.get("chunk_text", "") for pid in keep)
    assert stale, "the fixture must leave B behind for delete_document to remove"
