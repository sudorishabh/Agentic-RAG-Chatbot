"""The AUTHORED predicate: PERSON -> the document the claim came from.

A document is not one of this model's entity types (PERSON, ORGANIZATION,
PROJECT), so AUTHORED is literal-valued and the authoritative link to the
document is the claim's own provenance. Every CMS claim projects as
``Claim-[:SUPPORTED_BY]->Document``, so the graph path

    Person <-[:SUBJECT]- Claim -[:SUPPORTED_BY]-> Document

*is* the PERSON -AUTHORED-> DOCUMENT edge, reified exactly like every other
relationship in this graph rather than as a special case.
"""
from __future__ import annotations

from app.knowledge.claims import predicates as vocab


def test_authored_is_declared():
    assert vocab.is_known("AUTHORED")
    assert "AUTHORED" in vocab.PREDICATE_NAMES


def test_the_subject_is_a_person_and_only_a_person():
    p = vocab.get("AUTHORED")
    assert p.domain == ("PERSON",)
    assert vocab.accepts("AUTHORED", "PERSON", None)
    for wrong in ("ORGANIZATION", "PROJECT"):
        assert not vocab.accepts("AUTHORED", wrong, None), wrong


def test_the_object_is_text_not_an_entity():
    """Literal-valued on purpose: a DOCUMENT entity type does not exist, and
    inventing one to hold the object would be a far larger change than the
    relationship warrants."""
    p = vocab.get("AUTHORED")
    assert p.object_kind == vocab.OBJECT_TEXT
    assert p.entity_valued is False
    assert p.range == ()
    # So an entity object must not type-check.
    for t in ("PERSON", "ORGANIZATION", "PROJECT"):
        assert not vocab.accepts("AUTHORED", "PERSON", t), t


def test_it_is_not_functional():
    """A document has several authors and a person writes many documents, so
    neither side is exclusive. Marking it functional would make co-authors
    contradict each other in conflict detection."""
    assert vocab.get("AUTHORED").functional is False


def test_it_has_a_description_stating_the_direction():
    d = vocab.get("AUTHORED").description
    assert "person" in d.lower() and "document" in d.lower()


def test_the_existing_vocabulary_is_untouched():
    """Adding a predicate must not perturb the ones the graph already uses."""
    for name, domain, rng, functional in (
        ("FUNDED_BY", ("PROJECT",), ("ORGANIZATION",), False),
        ("PARTNER_OF", ("PROJECT",), ("ORGANIZATION",), False),
        ("LED_BY", ("PROJECT",), ("PERSON",), True),
        ("WORKS_AT", ("PERSON",), ("ORGANIZATION",), True),
        ("MEMBER_OF", ("PERSON",), ("ORGANIZATION",), False),
    ):
        p = vocab.get(name)
        assert (p.domain, p.range, p.functional) == (domain, rng, functional), name
    role = vocab.get("HAS_ROLE")
    assert role.object_kind == vocab.OBJECT_TEXT and role.domain == ("PERSON",)


def test_the_model_may_not_propose_authorship():
    """Authorship is stated outright in the CMS author fields, so there is
    nothing to infer and a guessed author would be a false statement about a
    real person. The extractor's disabled set is what keeps the CMS the only
    writer of this predicate."""
    from app.knowledge.document_pipeline import _DISABLED_PREDICATES

    assert "AUTHORED" in _DISABLED_PREDICATES
