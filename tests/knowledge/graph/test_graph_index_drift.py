"""Index drift: the failure `CREATE INDEX ... IF NOT EXISTS` cannot correct.

The bug these close, measured on the deployed graph: `document_published` was
declared on `published_at`, the date model renamed that property to
`effective_start_date`, and the DDL was updated — but `IF NOT EXISTS` matches on
the index **name**, so the server kept the old index, reported success, and left
1,044 Document nodes indexed on a property none of them carried. Every
date-filtered Document query was a full label scan and nothing said so.
"""
from __future__ import annotations

from app.knowledge.graph import schema


class _FakeSession:
    """Records statements and answers SHOW INDEXES from a supplied table."""

    def __init__(self, stored):
        # stored: name -> (label, (properties,)) ; None means a LOOKUP index
        self.stored = dict(stored)
        self.statements: list[str] = []

    def run(self, statement, **kwargs):
        self.statements.append(statement)
        if statement.startswith("SHOW INDEXES"):
            rows = []
            for name, value in self.stored.items():
                if value is None:
                    rows.append({"name": name, "labelsOrTypes": None,
                                 "properties": None, "type": "LOOKUP"})
                else:
                    label, props = value
                    rows.append({"name": name, "labelsOrTypes": [label],
                                 "properties": list(props), "type": "RANGE"})
            return rows
        return []


def _declared():
    return schema.declared_indexes()


# --------------------------------------------------------------------------- #
# The parser the migration depends on
# --------------------------------------------------------------------------- #

def test_every_declared_index_is_parsed_from_its_own_ddl():
    """Derived from INDEXES rather than repeated, so the two cannot disagree —
    a hand-maintained copy is exactly how the original drift went unnoticed."""
    declared = _declared()
    assert len(declared) == len(schema.INDEXES)
    for name, (label, props) in declared.items():
        assert name and label and props
        assert all(not p.startswith("n.") for p in props), "the alias is stripped"


def test_the_document_date_index_is_declared_on_the_canonical_field():
    label, props = _declared()["document_effective_start_date"]
    assert (label, props) == ("Document", ("effective_start_date",))


def test_the_obsolete_index_name_is_no_longer_declared():
    assert "document_published" not in _declared()
    assert "document_published" in schema.OBSOLETE_INDEXES


def test_a_composite_index_keeps_both_properties_in_order():
    assert _declared()["claim_validity"][1] == ("valid_from", "valid_until")


# --------------------------------------------------------------------------- #
# The migration
# --------------------------------------------------------------------------- #

def test_an_obsolete_index_is_dropped():
    session = _FakeSession({"document_published": ("Document", ("published_at",))})
    dropped = schema.migrate_index_drift(session)
    assert dropped == ["document_published"]
    assert "DROP INDEX document_published IF EXISTS" in session.statements


def test_an_index_whose_property_drifted_is_dropped_so_it_can_be_rebuilt():
    """The general case, not just the one name we happened to catch."""
    session = _FakeSession({"claim_status": ("Claim", ("state",))})
    dropped = schema.migrate_index_drift(session)
    assert dropped == ["claim_status"]
    assert "DROP INDEX claim_status IF EXISTS" in session.statements


def test_an_index_that_already_matches_is_left_alone():
    session = _FakeSession({
        "claim_status": ("Claim", ("status",)),
        "claim_validity": ("Claim", ("valid_from", "valid_until")),
    })
    assert schema.migrate_index_drift(session) == []
    assert not [s for s in session.statements if s.startswith("DROP")]


def test_a_lookup_index_owning_no_property_is_ignored():
    """Neo4j's own token-lookup indexes carry no label or property and are not
    ours to reason about; reading them as drift would drop them every start."""
    session = _FakeSession({"index_1b9dcc97": None})
    assert schema.migrate_index_drift(session) == []
    assert not [s for s in session.statements if s.startswith("DROP")]


def test_an_index_that_does_not_exist_yet_is_not_dropped():
    assert schema.migrate_index_drift(_FakeSession({})) == []


def test_ensure_reconciles_drift_before_it_creates():
    """Order is the whole point: a CREATE ... IF NOT EXISTS issued while the
    stale index still exists is the no-op that hid this for so long."""
    session = _FakeSession({"document_published": ("Document", ("published_at",))})
    schema.ensure_graph_schema(session=session)

    drop = session.statements.index("DROP INDEX document_published IF EXISTS")
    create = next(i for i, s in enumerate(session.statements)
                  if s.startswith("CREATE INDEX document_effective_start_date"))
    assert drop < create
    # And the schema was still applied in full.
    assert len([s for s in session.statements if s.startswith("CREATE")]) == \
        len(schema.statements())


def test_teardown_also_removes_the_obsolete_index():
    """A drop-then-rebuild that left the old index behind would defeat itself."""
    session = _FakeSession({})
    schema.drop_graph_schema(session=session)
    assert "DROP INDEX document_published IF EXISTS" in session.statements
