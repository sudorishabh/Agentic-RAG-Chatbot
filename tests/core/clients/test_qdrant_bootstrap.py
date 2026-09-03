"""A fresh deployment must come up fully indexed, not one-thirteenth indexed.

`ensure_collection` created the collection and exactly one payload index. The
other twelve — including the `chunk_text` text index the whole lexical path
depends on — existed only where someone had remembered to run a script, so a new
environment silently fell back to unindexed filters and a keyword leg that
matched nothing. `_ensure_keyword_index` was defined and never called.

It also never checked that an existing collection's vectors were the size this
deployment embeds to.

The Qdrant client is a fake; no server.
"""

from __future__ import annotations

import pytest

from app.core.clients import vector_store as vs


class _FakeQdrant:
    def __init__(self, *, exists: bool = False, indexed: set[str] | None = None,
                 dimension: int = 3072, fail_on: set[str] | None = None):
        self.exists = exists
        self.indexed = set(indexed or ())
        self.dimension = dimension
        self.fail_on = set(fail_on or ())
        self.created_collection: dict | None = None
        self.index_calls: list[tuple[str, object]] = []

    def collection_exists(self, collection_name):
        return self.exists

    def create_collection(self, collection_name, vectors_config):
        self.exists = True
        self.created_collection = {
            "name": collection_name, "size": vectors_config.size,
            "distance": vectors_config.distance,
        }

    def get_collection(self, collection_name):
        from types import SimpleNamespace

        return SimpleNamespace(
            payload_schema={f: object() for f in self.indexed},
            config=SimpleNamespace(
                params=SimpleNamespace(vectors=SimpleNamespace(size=self.dimension))
            ),
        )

    def create_payload_index(self, collection_name, field_name, field_schema, wait=False):
        self.index_calls.append((field_name, field_schema))
        if field_name in self.fail_on:
            raise RuntimeError(f"refused: {field_name}")
        self.indexed.add(field_name)


@pytest.fixture
def qdrant(monkeypatch):
    """A fake client, with the per-process 'already ensured' cache cleared."""
    def use(client: _FakeQdrant) -> _FakeQdrant:
        monkeypatch.setattr(vs, "get_qdrant_client", lambda: client)
        vs._ensured_collections.clear()
        return client

    yield use
    vs._ensured_collections.clear()


@pytest.fixture
def settings(monkeypatch):
    from app.config import get_settings

    live = get_settings()
    monkeypatch.setattr(live, "qdrant_collection", "documents")
    monkeypatch.setattr(live, "azure_openai_embedding_dimensions", 3072)
    return live


# --------------------------------------------------------------------------- #
# A fresh deployment.
# --------------------------------------------------------------------------- #

def test_a_new_collection_gets_every_index_the_app_filters_on(qdrant, settings):
    client = qdrant(_FakeQdrant(exists=False))

    vs.ensure_collection()

    assert client.indexed == set(vs.PAYLOAD_INDEXES)


def test_the_lexical_path_gets_its_text_index(qdrant, settings):
    """`keyword_leg_enabled` degrades to dense-only without this, and says
    nothing about it."""
    client = qdrant(_FakeQdrant(exists=False))

    vs.ensure_collection()

    schema = dict(client.index_calls)["chunk_text"]
    assert getattr(schema, "type", None) == "text"
    assert getattr(schema, "lowercase", None) is True


def test_the_collection_is_created_at_the_configured_dimension(qdrant, settings, monkeypatch):
    """From configuration, not from whatever the model answered first — and
    without spending an embedding call to find out."""
    monkeypatch.setattr(
        vs, "get_embeddings", lambda: pytest.fail("must not probe the model")
    )
    client = qdrant(_FakeQdrant(exists=False))

    vs.ensure_collection()

    assert client.created_collection["size"] == 3072


def test_an_unpinned_dimension_still_falls_back_to_a_probe(qdrant, settings, monkeypatch):
    """ada-002 takes no dimensions parameter, so there is nothing to read."""
    from types import SimpleNamespace

    monkeypatch.setattr(settings, "azure_openai_embedding_dimensions", None)
    monkeypatch.setattr(
        vs, "get_embeddings", lambda: SimpleNamespace(embed_query=lambda text: [0.0] * 1536)
    )
    client = qdrant(_FakeQdrant(exists=False))

    vs.ensure_collection()

    assert client.created_collection["size"] == 1536


# --------------------------------------------------------------------------- #
# An existing collection.
# --------------------------------------------------------------------------- #

def test_existing_indexes_are_left_alone(qdrant, settings):
    client = qdrant(_FakeQdrant(exists=True, indexed=set(vs.PAYLOAD_INDEXES)))

    vs.ensure_collection()

    assert client.index_calls == [], "idempotent: nothing to do, nothing done"


def test_a_collection_missing_indexes_gains_only_those(qdrant, settings):
    """The state a deployment is actually in: one index from the old
    ensure_collection, the rest never run."""
    client = qdrant(_FakeQdrant(exists=True, indexed={"effective_start_date"}))

    vs.ensure_collection()

    assert [f for f, _ in client.index_calls] == [
        f for f in vs.PAYLOAD_INDEXES if f != "effective_start_date"
    ]


def test_one_index_failing_does_not_stop_the_others(qdrant, settings):
    """Each index built is one filter that works; refusing to build the rest
    because of one is strictly worse."""
    client = qdrant(_FakeQdrant(exists=True, fail_on={"chunk_text"}))

    vs.ensure_collection()

    assert "chunk_text" not in client.indexed
    assert "document_id" in client.indexed and "is_parent" in client.indexed


def test_a_timed_out_index_that_landed_is_not_reported_as_missing(qdrant, settings):
    """A text index over a whole collection routinely outlives the client
    timeout while Qdrant carries on. The schema read-back is the honest test."""
    class _SlowButSuccessful(_FakeQdrant):
        def create_payload_index(self, collection_name, field_name, field_schema, wait=False):
            self.index_calls.append((field_name, field_schema))
            self.indexed.add(field_name)  # the server did build it
            if field_name == "chunk_text":
                raise TimeoutError("the client gave up waiting")

    client = qdrant(_SlowButSuccessful(exists=True))

    created = vs.ensure_payload_indexes(client, "documents")

    assert "chunk_text" in created


# --------------------------------------------------------------------------- #
# Dimension validation.
# --------------------------------------------------------------------------- #

def test_a_mismatched_collection_is_refused(qdrant, settings):
    """Repointing at another embedding model leaves vectors that cannot be
    compared with the ones this process produces. Qdrant rejects the writes one
    request at a time, with a message about vector sizes rather than about
    configuration."""
    client = qdrant(_FakeQdrant(exists=True, dimension=1536))

    with pytest.raises(vs.VectorDimensionMismatch) as excinfo:
        vs.ensure_collection()

    message = str(excinfo.value)
    assert "1536" in message and "3072" in message
    assert "AZURE_OPENAI_EMBEDDING_DIMENSIONS" in message


def test_a_matching_collection_passes(qdrant, settings):
    client = qdrant(_FakeQdrant(exists=True, dimension=3072))

    vs.ensure_collection()  # must not raise

    assert client.indexed == set(vs.PAYLOAD_INDEXES)


def test_an_unpinned_deployment_validates_nothing(qdrant, settings, monkeypatch):
    """Nothing to compare against is not a mismatch."""
    monkeypatch.setattr(settings, "azure_openai_embedding_dimensions", None)
    qdrant(_FakeQdrant(exists=True, dimension=1536))

    vs.ensure_collection()  # must not raise


def test_a_failure_is_not_cached_as_success(qdrant, settings):
    """The mismatch has to be raised on every call, not once."""
    qdrant(_FakeQdrant(exists=True, dimension=1536))

    for _ in range(2):
        with pytest.raises(vs.VectorDimensionMismatch):
            vs.ensure_collection()


# --------------------------------------------------------------------------- #
# What must stay out.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("field", ["term_ids", "theme_ids", "tenant_id", "acl"])
def test_retired_fields_are_not_indexed(field):
    """Taxonomy and access-control payloads were removed from the model.
    Indexing them would be reviving it by the back door."""
    assert field not in vs.PAYLOAD_INDEXES


def test_the_index_list_covers_what_retrieval_filters_on():
    """A guard against the list drifting from the filters it exists for."""
    for field in (
        "is_parent", "is_current", "source_type", "document_id",
        "categories", "tags", "effective_start_date", "chunk_text",
    ):
        assert field in vs.PAYLOAD_INDEXES, field
