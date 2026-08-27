"""Unit tests for the Neo4j foundation: client seams and schema DDL.

No live Neo4j. The driver is monkeypatched at ``app.core.clients.graph``, and
the schema is asserted on the *emitted statements* — which is what makes the
safety properties structural rather than aspirational: a statement that
interpolated a label, or a template that wrote from the read path, would fail
here rather than in review.
"""

from __future__ import annotations

import pytest

from app.knowledge.graph import schema


class _FakeSession:
    """Records statements instead of running them."""

    def __init__(self) -> None:
        self.statements: list[str] = []

    def run(self, statement, **params):
        self.statements.append(statement)
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# --------------------------------------------------------------------------- #
# Statement set
# --------------------------------------------------------------------------- #

def test_every_statement_is_idempotent():
    """Applied on every process start, like catalog.schema.ensure_*, so a second
    call must be a no-op rather than an error."""
    for statement in schema.statements():
        assert "IF NOT EXISTS" in statement, statement


def test_constraints_precede_indexes():
    """A uniqueness constraint creates its own backing index; creating an
    equivalent index first would leave a redundant one behind."""
    kinds = [
        "constraint" if s.startswith("CREATE CONSTRAINT") else "index"
        for s in schema.statements()
    ]
    assert kinds == sorted(kinds, key=lambda k: k != "constraint")


def test_statement_names_are_unique():
    """Two statements sharing a name silently overwrite each other's intent."""
    names = [
        s.split()[2] if not s.startswith("CREATE FULLTEXT") else s.split()[3]
        for s in schema.statements()
    ]
    assert len(names) == len(set(names))


def test_no_enterprise_only_ddl():
    """The deployed server is Community, which rejects NODE KEY and existence
    constraints. Both are designed around (alias_key, REQUIRED_PROPERTIES); a
    statement using either would fail at runtime, not here, so pin it."""
    for statement in schema.statements():
        assert "NODE KEY" not in statement, statement
        assert "IS NOT NULL" not in statement, statement


def test_schema_carries_no_access_control_or_taxonomy():
    """The corpus is public and read whole; taxonomy is not part of this model.
    A tenant, acl or term property appearing here would reintroduce a concept
    the rest of the system has removed."""
    ddl = " ".join(schema.statements()).lower()
    for banned in ("tenant", "acl", "taxonomy", "term_ids", "theme_ids"):
        assert banned not in ddl, banned


def test_identity_constraints_cover_every_merge_key():
    """Projection is idempotent only because each writer MERGEs on a key that is
    unique. A model key without a constraint is a duplicate waiting to happen."""
    ddl = " ".join(schema.CONSTRAINTS)
    for key in (
        "n.entity_id", "n.claim_id", "n.chunk_id", "n.document_id",
        "n.name", "n.alias_key", "n.cms_uuid",
    ):
        assert f"REQUIRE {key} IS UNIQUE" in ddl, key


# --------------------------------------------------------------------------- #
# Application
# --------------------------------------------------------------------------- #

def test_ensure_graph_schema_runs_every_statement():
    session = _FakeSession()
    count = schema.ensure_graph_schema(session=session)
    assert count == len(schema.statements())
    assert session.statements == list(schema.statements())


def test_ensure_graph_schema_opens_a_write_session(monkeypatch):
    """Schema work must not run on a read session — and the read/write split is
    the whole of the access boundary on Community."""
    session = _FakeSession()
    opened: list[str] = []

    def fake_write_session(**kw):
        opened.append("write")
        return session

    monkeypatch.setattr("app.core.clients.graph.write_session", fake_write_session)
    schema.ensure_graph_schema()
    assert opened == ["write"]
    assert len(session.statements) == len(schema.statements())


def test_drop_graph_schema_drops_everything_it_creates():
    """The graph is a rebuildable projection, so a model change is applied by
    dropping and recreating. Anything left behind survives that reset."""
    session = _FakeSession()
    schema.drop_graph_schema(session=session)
    dropped = " ".join(session.statements)
    for statement in schema.statements():
        name = (
            statement.split()[3] if statement.startswith("CREATE FULLTEXT")
            else statement.split()[2]
        )
        assert name in dropped, name
    assert all(s.startswith("DROP ") for s in session.statements)


# --------------------------------------------------------------------------- #
# Vocabulary allow-lists
# --------------------------------------------------------------------------- #

def test_labels_and_relationships_are_identifier_safe():
    """Cypher cannot parameterize a label or relationship type, so these are
    interpolated by construction. Restricting them to a code-owned allow-list of
    plain identifiers is the injection control."""
    for name in schema.ENTITY_LABELS + schema.PROVENANCE_RELATIONSHIPS:
        assert name.replace("_", "").isalnum()
        assert not name.startswith("_")


def test_alias_key_is_deterministic():
    """Stands in for the NODE KEY constraint Community rejects, so it has to be
    reproducible from its parts."""
    key = schema.alias_key("person_00001", "raj sharma", "full_name")
    assert key == schema.alias_key("person_00001", "raj sharma", "full_name")
    assert schema.alias_key("person_00002", "raj sharma", "full_name") != key


def test_alias_key_cannot_collide_across_field_boundaries():
    """This key *is* the uniqueness constraint, so an ambiguous encoding merges
    two different aliases onto one node. With a printable delimiter,
    ("a", "b|c", "d") and ("a|b", "c", "d") produce the same string."""
    assert schema.alias_key("a", "b|c", "d") != schema.alias_key("a|b", "c", "d")
    assert schema.alias_key("a", "", "b") != schema.alias_key("a", "b", "")


def test_required_properties_are_declared_for_every_node_type():
    """Community cannot enforce existence, so writers check this map instead.
    A node type missing from it is a type nobody is validating."""
    assert set(schema.REQUIRED_PROPERTIES) == {
        "Entity", "Alias", "Claim", "Chunk", "Document", "Predicate",
    }
    for label, props in schema.REQUIRED_PROPERTIES.items():
        assert props, label


# --------------------------------------------------------------------------- #
# Client seam
# --------------------------------------------------------------------------- #

def test_graph_available_is_false_rather_than_raising(monkeypatch):
    """Every knowledge-layer caller degrades rather than fails, so reachability
    is a value. An exception here would propagate into a health probe."""
    from app.core.clients import graph

    class _Boom:
        def verify_connectivity(self):
            raise RuntimeError("unreachable")

    monkeypatch.setattr(graph, "get_graph_driver", lambda: _Boom())
    assert graph.graph_available() is False


def test_reset_does_not_build_a_driver_just_to_close_it():
    """Resetting a process that never touched Neo4j must not connect to it —
    which is what calling get_graph_driver() to close it would do."""
    from app.core.clients import graph

    graph.get_graph_driver.cache_clear()
    assert graph.get_graph_driver.cache_info().currsize == 0
    graph.reset_graph_driver()  # no driver cached: must be a no-op, not a connect
    assert graph.get_graph_driver.cache_info().currsize == 0


def test_reset_closes_and_forgets_a_built_driver(monkeypatch):
    from app.core.clients import graph

    closed: list[str] = []

    class _Driver:
        def close(self):
            closed.append("closed")

    graph.get_graph_driver.cache_clear()
    monkeypatch.setattr(
        "neo4j.GraphDatabase.driver", lambda *a, **kw: _Driver()
    )
    graph.get_graph_driver()
    assert graph.get_graph_driver.cache_info().currsize == 1

    graph.reset_graph_driver()
    assert closed == ["closed"]
    assert graph.get_graph_driver.cache_info().currsize == 0


@pytest.mark.parametrize(
    "flag",
    [
        "knowledge_enabled",
        "graph_retrieval_enabled",
        "knowledge_process_after_index",
    ],
)
def test_knowledge_flags_default_off(flag):
    """Every new capability in this codebase launches OFF.

    Asserted against the **field default**, not a loaded ``Settings()``.
    ``Settings()`` reads ``.env``, so the previous form conflated two different
    claims — "this ships off" and "this machine has it off" — and could only
    ever fail on a developer box that had deliberately enabled the feature.
    It did, constantly, for anyone running the knowledge layer locally; the
    failure carried no information and cost a diagnostic detour every run.

    ``.env`` is gitignored and cannot be shipped, so the loaded value was never
    the thing worth guarding. The shipped default is, and that is what this now
    reads.
    """
    from app.config import Settings

    assert Settings.model_fields[flag].default is False
