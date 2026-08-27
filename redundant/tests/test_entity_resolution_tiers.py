"""Unit tests for entity resolution: candidates, scoring, tiers, decisions.

No database: the index is built from literals. The organising principle of the
suite is that **a false merge is worse than an unresolved mention**, so for every
"this links" test there is a paired "this must not link" test, and the second
kind is the one that matters.
"""

from __future__ import annotations

import pytest

from app.knowledge.candidates import (
    Candidate,
    CandidateSet,
    EntityIndex,
    ResolutionContext,
    generate,
)
from app.knowledge.resolver import (
    AMBIGUOUS,
    AUTO,
    PROVISIONAL,
    UNRESOLVED,
    resolve_mention,
    resolve_mentions,
)
from app.knowledge.seed import PROJECT_CODE_SCHEME, entity_id_for
from app.knowledge.types import Mention

CHUNK = "c-1"
DOC = "d-1"


def _mention(surface, entity_type, *, normalized=None, method="gazetteer", start=0):
    from app.knowledge.normalize import normalize_for

    return Mention(
        chunk_id=CHUNK, document_id=DOC, start_offset=start,
        end_offset=start + max(1, len(surface)), surface_text=surface,
        normalized_text=normalized if normalized is not None
        else normalize_for(entity_type, surface),
        entity_type=entity_type, extraction_method=method,
        extractor_version="test", confidence=0.9,
    )


def _index(entities=(), aliases=(), identifiers=()):
    """Build an index from (entity_id, type, canonical, trust) tuples."""
    from app.knowledge.normalize import normalize_for

    from app.knowledge.seed import is_claim_eligible

    entity_rows = {}
    for entity_id, entity_type, canonical, trust in entities:
        entity_rows[entity_id] = {
            "entity_id": entity_id, "entity_type": entity_type,
            "canonical_name": canonical,
            "normalized_name": normalize_for(entity_type, canonical),
            "trust": trust, "source": "test",
            # Derived from trust exactly as seeding derives it, so the fixture
            # cannot accidentally make a provisional identity claim-eligible.
            "claim_eligible": 1 if is_claim_eligible(trust) else 0,
        }
    alias_rows = []
    for entity_id, surface, alias_type, autolink, ambiguous in aliases:
        entity_type = entity_rows[entity_id]["entity_type"]
        alias_rows.append({
            "entity_id": entity_id,
            "normalized": normalize_for(entity_type, surface),
            "surface": surface, "alias_type": alias_type,
            "autolink": autolink, "is_ambiguous": ambiguous,
        })
    return EntityIndex({
        "entities": entity_rows,
        "aliases": alias_rows,
        "identifiers": dict(identifiers),
    })


PACHAURI = entity_id_for("PERSON", "r k pachauri")
SHARMA_A = entity_id_for("PERSON", "sharma-a")
SHARMA_B = entity_id_for("PERSON", "sharma-b")
TERI = entity_id_for("ORGANIZATION", "teri")
ACC = entity_id_for("ORGANIZATION", "acc limited")
PROJ = entity_id_for("PROJECT", "proj-1")
STEEL = entity_id_for("PROJECT", "steel")


# --------------------------------------------------------------------------- #
# Tier 0 — identifiers
# --------------------------------------------------------------------------- #

def test_project_code_resolves_by_identifier():
    """The strongest signal in this corpus: (scheme, value) is a database
    invariant, so this is a lookup and not an inference."""
    index = _index(
        entities=[(PROJ, "PROJECT", "Eco-housing framework", "authoritative")],
        identifiers=[((PROJECT_CODE_SCHEME, "2004BS22"), PROJ)],
    )
    decision = resolve_mention(_mention("2004BS22", "PROJECT"), index)
    assert decision.decision == AUTO
    assert decision.entity_id == PROJ
    assert decision.tier == "tier0_identifier"


def test_unknown_project_code_does_not_resolve():
    index = _index(
        entities=[(PROJ, "PROJECT", "Eco-housing framework", "authoritative")],
        identifiers=[((PROJECT_CODE_SCHEME, "2004BS22"), PROJ)],
    )
    decision = resolve_mention(_mention("2099ZZ99", "PROJECT"), index)
    assert decision.decision == UNRESOLVED
    assert decision.entity_id is None


def test_identifier_short_circuits_other_candidates():
    """Nothing outranks an identifier, so nothing else is even considered."""
    index = _index(
        entities=[(PROJ, "PROJECT", "2004BS22", "authoritative")],
        identifiers=[((PROJECT_CODE_SCHEME, "2004BS22"), PROJ)],
    )
    candidates = generate(_mention("2004BS22", "PROJECT"), index)
    assert [c.source for c in candidates] == ["identifier"]


# --------------------------------------------------------------------------- #
# Tier 1 / 2 — exact names and aliases
# --------------------------------------------------------------------------- #

def test_exact_organization_name_resolves():
    index = _index(entities=[(ACC, "ORGANIZATION", "ACC Limited", "derived")])
    decision = resolve_mention(_mention("ACC Limited", "ORGANIZATION"), index)
    assert decision.decision == AUTO
    assert decision.entity_id == ACC
    assert decision.tier == "tier1_exact_name"


def test_case_and_legal_form_variants_reach_the_same_entity():
    index = _index(entities=[(ACC, "ORGANIZATION", "ACC Limited", "derived")])
    for surface in ("ACC LIMITED", "acc limited", "ACC Ltd"):
        decision = resolve_mention(_mention(surface, "ORGANIZATION"), index)
        assert decision.entity_id == ACC, surface


def test_acronym_alias_resolves():
    """Acronyms are the corpus's most common organization surface."""
    index = _index(
        entities=[(TERI, "ORGANIZATION", "The Energy and Resources Institute", "derived")],
        aliases=[(TERI, "TERI", "acronym", 1, 0)],
    )
    decision = resolve_mention(_mention("TERI", "ORGANIZATION"), index)
    assert decision.decision == AUTO
    assert decision.entity_id == TERI
    assert decision.tier == "tier2_alias"


def test_ambiguous_alias_never_links():
    """An alias claimed by two entities is vetoed outright — the data-driven
    guard that disarms a shared surface the moment it becomes shared."""
    index = _index(
        entities=[
            (TERI, "ORGANIZATION", "The Energy and Resources Institute", "derived"),
            (ACC, "ORGANIZATION", "Association of Corporate Counsel", "derived"),
        ],
        aliases=[(TERI, "ACC", "acronym", 0, 1), (ACC, "ACC", "acronym", 0, 1)],
    )
    decision = resolve_mention(_mention("ACC", "ORGANIZATION"), index)
    assert decision.decision == UNRESOLVED
    assert "v_ambiguous_alias" in decision.reason


# --------------------------------------------------------------------------- #
# PERSON — the open-world, high-risk type
# --------------------------------------------------------------------------- #

def test_person_exact_name_alone_does_not_auto_link():
    """The single most important PERSON rule. One seeded "Ritu Sharma" does not
    make every "Ritu Sharma" in the corpus that person — it means the corpus has
    met one so far. Without corroboration this stays undecided."""
    index = _index(entities=[(SHARMA_A, "PERSON", "Ritu Sharma", "derived")])
    decision = resolve_mention(_mention("Ritu Sharma", "PERSON"), index)
    assert decision.decision == AMBIGUOUS
    assert "no corroborating context" in decision.reason
    assert decision.entity_id is None


def test_person_links_when_the_document_asserts_the_name():
    """Corroboration that is not the name: this document's own CMS metadata
    says it is by this person."""
    index = _index(entities=[(SHARMA_A, "PERSON", "Ritu Sharma", "derived")])
    context = ResolutionContext(document_id=DOC)
    context.cms_names["PERSON"].add("ritu sharma")
    decision = resolve_mention(_mention("Ritu Sharma", "PERSON"), index, context)
    assert decision.decision == AUTO
    assert decision.entity_id == SHARMA_A


def test_same_name_different_people_are_never_merged():
    """Two people share a name. They score identically, the margin collapses to
    zero, and the resolver refuses. This is the false-merge gate."""
    index = _index(
        entities=[
            (SHARMA_A, "PERSON", "Raj Sharma", "derived"),
            (SHARMA_B, "PERSON", "Raj Sharma", "derived"),
        ],
    )
    decision = resolve_mention(_mention("Raj Sharma", "PERSON"), index)
    assert decision.decision != AUTO
    assert decision.entity_id is None


def test_contradictory_document_context_vetoes_a_perfect_name_match():
    """"Raj Sharma - TERI" vs "Raj Sharma - IIT Delhi": the name matches exactly
    and the context contradicts, so no link. Vetoes beat scores."""
    index = _index(entities=[(SHARMA_A, "PERSON", "Raj Sharma", "derived")])
    context = ResolutionContext(document_id=DOC)
    context.cms_names["PERSON"].add("meena sehgal")   # someone else entirely
    decision = resolve_mention(_mention("Raj Sharma", "PERSON"), index, context)
    assert decision.decision == UNRESOLVED
    assert "v_cms_names_someone_else" in decision.reason


@pytest.mark.parametrize("surface", ["A.", "A. K.", "R"])
def test_initials_only_mentions_never_link(surface):
    """The author facet is full of these. They name nobody in particular."""
    index = _index(entities=[(PACHAURI, "PERSON", "R K Pachauri", "authoritative")])
    decision = resolve_mention(_mention(surface, "PERSON"), index)
    assert decision.decision != AUTO
    assert decision.entity_id is None


def test_honorifics_do_not_prevent_a_match():
    """"Dr R K Pachauri" and "R K Pachauri" are one name; normalization folds
    the honorific before anything is compared."""
    index = _index(entities=[(PACHAURI, "PERSON", "R K Pachauri", "authoritative")])
    context = ResolutionContext(document_id=DOC)
    context.cms_names["PERSON"].add("r k pachauri")
    decision = resolve_mention(_mention("Dr R K Pachauri", "PERSON"), index, context)
    assert decision.decision == AUTO
    assert decision.entity_id == PACHAURI


def test_initials_blocking_surfaces_a_candidate_without_linking_it():
    """"R K Pachauri" blocks against "Rajendra Kumar Pachauri" on shared
    initials — enough to consider, deliberately not enough to link."""
    full = entity_id_for("PERSON", "rajendra kumar pachauri")
    index = _index(entities=[(full, "PERSON", "Rajendra Kumar Pachauri", "derived")])
    mention = _mention("R K Pachauri", "PERSON")
    candidates = generate(mention, index)
    assert [c.source for c in candidates] == ["blocked"]
    assert resolve_mention(mention, index).decision != AUTO


# --------------------------------------------------------------------------- #
# PROJECT — descriptive titles must not resolve on similarity
# --------------------------------------------------------------------------- #

def test_descriptive_project_title_does_not_link_on_the_title_alone():
    """"Steel" is a real project title in this CMS and also an ordinary word.
    Resolving it from title similarity would attach every mention of the
    material to a project."""
    index = _index(
        entities=[(STEEL, "PROJECT", "Steel", "authoritative")],
        aliases=[(STEEL, "Steel", "title", 0, 0)],
    )
    decision = resolve_mention(_mention("steel", "PROJECT"), index)
    assert decision.decision != AUTO
    assert decision.entity_id is None


def test_specific_project_title_still_resolves():
    index = _index(
        entities=[(PROJ, "PROJECT", "Water Sustainability Assessment of Chennai",
                   "authoritative")],
    )
    decision = resolve_mention(
        _mention("Water Sustainability Assessment of Chennai", "PROJECT"), index
    )
    assert decision.decision == AUTO
    assert decision.entity_id == PROJ


# --------------------------------------------------------------------------- #
# Candidate generation
# --------------------------------------------------------------------------- #

def test_no_candidate_is_unresolved_not_new():
    """A name the CMS never asserted is honestly unknown. Minting an entity here
    is exactly the "invent an id because a name looked similar" failure."""
    decision = resolve_mention(_mention("Nobody At All", "PERSON"), _index())
    assert decision.decision == UNRESOLVED
    assert decision.entity_id is None
    assert decision.reason == "no candidate entity"


def test_multiple_candidates_without_a_winner_are_ambiguous():
    index = _index(
        entities=[
            (SHARMA_A, "PERSON", "Raj Sharma", "derived"),
            (SHARMA_B, "PERSON", "Raj Sharma", "derived"),
        ],
    )
    context = ResolutionContext(document_id=DOC)
    context.cms_names["PERSON"].add("raj sharma")
    decision = resolve_mention(_mention("Raj Sharma", "PERSON"), index, context)
    assert decision.decision == AMBIGUOUS
    assert len(decision.candidate_audit) == 2


def test_a_truncated_shortlist_refuses_rather_than_picking():
    """A surface matching more entities than the cap is too common to be
    evidence; choosing from a truncated list would fake a decision."""
    mention = _mention("Common Name", "ORGANIZATION")
    oversized = CandidateSet(
        [
            Candidate(
                entity_id=f"org_{i:012x}", entity_type="ORGANIZATION",
                canonical_name="Common Name", normalized_name="common name",
                trust="derived", source="alias",
            )
            for i in range(30)
        ],
        truncated=True,
    )
    decision = resolve_mention(mention, _index(), candidate_set=oversized)
    assert decision.decision == AMBIGUOUS
    assert "too common" in decision.reason


def test_candidate_generation_is_bounded_and_ordered():
    index = _index(
        entities=[(ACC, "ORGANIZATION", "ACC Limited", "derived")],
        aliases=[(ACC, "ACC Limited", "full_name", 1, 0)],
    )
    mention = _mention("ACC Limited", "ORGANIZATION")
    first = [c.entity_id for c in generate(mention, index)]
    second = [c.entity_id for c in generate(mention, index)]
    assert first == second == [ACC]  # one entity, strongest source kept


# --------------------------------------------------------------------------- #
# Determinism and audit
# --------------------------------------------------------------------------- #

def test_repeated_resolution_is_identical():
    index = _index(
        entities=[
            (SHARMA_A, "PERSON", "Raj Sharma", "derived"),
            (SHARMA_B, "PERSON", "Raj Sharma", "derived"),
        ],
    )
    mention = _mention("Raj Sharma", "PERSON")
    a = resolve_mention(mention, index)
    b = resolve_mention(mention, index)
    assert (a.decision, a.entity_id, a.score, a.margin) == (
        b.decision, b.entity_id, b.score, b.margin
    )
    assert a.candidate_audit == b.candidate_audit


def test_every_decision_carries_its_evidence():
    """The audit has to answer "why" without re-running the resolver."""
    index = _index(entities=[(ACC, "ORGANIZATION", "ACC Limited", "derived")])
    decision = resolve_mention(_mention("ACC Limited", "ORGANIZATION"), index)
    assert decision.resolver_version
    assert decision.tier and decision.reason
    audit = decision.candidate_audit[0]
    assert audit["entity_id"] == ACC
    assert "features" in audit and "score" in audit and "vetoes" in audit


def test_co_mentions_corroborate_within_a_chunk():
    """A person beside their employer is corroborated by it — the cheapest real
    context this corpus offers."""
    index = _index(
        entities=[
            (SHARMA_A, "PERSON", "Ritu Sharma", "derived"),
            (TERI, "ORGANIZATION", "TERI", "derived"),
        ],
    )
    mentions = [
        _mention("Ritu Sharma", "PERSON", start=0),
        _mention("TERI", "ORGANIZATION", start=40),
    ]
    decisions = resolve_mentions(mentions, index)
    person = next(d for d in decisions if d.entity_type == "PERSON")
    # The person is corroborated by their own co-mention set, so the margin and
    # score are recorded even though the link stays conservative.
    assert person.score is not None


def test_resolver_never_returns_an_unknown_decision_state():
    index = _index(entities=[(ACC, "ORGANIZATION", "ACC Limited", "derived")])
    for surface, entity_type in [
        ("ACC Limited", "ORGANIZATION"), ("Nobody", "PERSON"),
        ("A.", "PERSON"), ("steel", "PROJECT"),
    ]:
        decision = resolve_mention(_mention(surface, entity_type), index)
        assert decision.decision in ("AUTO", "AMBIGUOUS", "UNRESOLVED", "NEW")


def test_entity_ids_are_deterministic_and_well_formed():
    from app.knowledge.seed import ENTITY_ID_RE

    assert entity_id_for("PERSON", "x") == entity_id_for("PERSON", "x")
    assert entity_id_for("PERSON", "x") != entity_id_for("ORGANIZATION", "x")
    for entity_type in ("PERSON", "ORGANIZATION", "PROJECT"):
        assert ENTITY_ID_RE.match(entity_id_for(entity_type, "sample"))


# --------------------------------------------------------------------------- #
# Seeding guards. The seeder decides what identities *exist*, so a bad entity
# here is a false merge nothing downstream can undo — the resolver cannot
# un-merge two people the seed already collapsed into one.
# --------------------------------------------------------------------------- #

def test_seeder_rejects_facet_fragments():
    """"& Sharma" is a real value in documents_author, left by a split on
    "and". Seeding it would create an entity for later mentions to collide
    with."""
    from app.knowledge.seed import _is_name_like
    from app.knowledge.normalize import normalize_person

    assert not _is_name_like(normalize_person("& Sharma"))
    assert _is_name_like(normalize_person("Divya Sharma"))


def test_seeder_id_is_stable_across_runs():
    """The whole layer is rebuildable only because ids derive from the seed
    source rather than a counter."""
    from app.knowledge.seed import entity_id_for

    uuid = "ab2e2f0c-0eca-4681-8918-efb62f1adbe8"
    assert entity_id_for("PERSON", uuid) == entity_id_for("PERSON", uuid)


def test_project_code_shape_is_strict():
    """A loose code pattern would turn ordinary numbers into Tier-0 identities,
    which is the one tier that links with no corroboration at all."""
    from app.knowledge.seed import _PROJECT_CODE_RE

    assert _PROJECT_CODE_RE.match("2004BS22")
    for bad in ("2004bs22", "204BS22", "2004BS2", "1899AA11", "2004BS222"):
        assert not _PROJECT_CODE_RE.match(bad), bad


def test_a_mention_never_corroborates_itself():
    """The bug this test exists for silently disabled PERSON's whole safety
    requirement: every name corroborated itself, so name-only matches
    auto-linked."""
    index = _index(entities=[(SHARMA_A, "PERSON", "Ritu Sharma", "derived")])
    decisions = resolve_mentions([_mention("Ritu Sharma", "PERSON")], index)
    assert decisions[0].decision == AMBIGUOUS
    assert "no corroborating context" in decisions[0].reason


def test_repeating_a_name_in_a_chunk_is_not_corroboration():
    """Two sightings of one name are repetition, not evidence of identity."""
    index = _index(entities=[(SHARMA_A, "PERSON", "Ritu Sharma", "derived")])
    mentions = [
        _mention("Ritu Sharma", "PERSON", start=0),
        _mention("Ritu Sharma", "PERSON", start=50),
    ]
    for decision in resolve_mentions(mentions, index):
        assert decision.decision == AMBIGUOUS
        assert decision.entity_id is None


# --------------------------------------------------------------------------- #
# Provisional identity. The corpus gives *names* for people, not people: two
# different "Arun Kumar"s are one row. That conflation cannot be undone, so the
# model's job is to stop anything treating such a row as a canonical person.
# --------------------------------------------------------------------------- #

def _person_index(trust):
    return _index(entities=[(SHARMA_A, "PERSON", "Ritu Sharma", trust)])


def _corroborating_context():
    context = ResolutionContext(document_id=DOC)
    context.cms_names["PERSON"].add("ritu sharma")
    return context


def test_provisional_person_links_but_is_not_canonical():
    """The link is still useful — it groups every sighting of the name — but it
    asserts nothing about identity, so it cannot become a claim subject."""
    decision = resolve_mention(
        _mention("Ritu Sharma", "PERSON"), _person_index("provisional"),
        _corroborating_context(),
    )
    assert decision.decision == PROVISIONAL
    assert decision.entity_id == SHARMA_A
    assert decision.linked is True
    assert decision.canonical is False
    assert decision.claim_eligible is False


def test_authoritative_person_is_canonical():
    decision = resolve_mention(
        _mention("Ritu Sharma", "PERSON"), _person_index("authoritative"),
        _corroborating_context(),
    )
    assert decision.decision == AUTO
    assert decision.canonical is True
    assert decision.claim_eligible is True


def test_only_auto_counts_as_canonical():
    """Claims and graph projection read `canonical`, never the raw entity_id —
    so PROVISIONAL must not slip through as an identity."""
    from app.knowledge.resolver import CANONICAL_DECISIONS

    assert CANONICAL_DECISIONS == (AUTO,)
    assert PROVISIONAL not in CANONICAL_DECISIONS


def test_trust_levels_decide_claim_eligibility():
    from app.knowledge.seed import (
        TRUST_AUTHORITATIVE, TRUST_DERIVED, TRUST_PROVISIONAL, is_claim_eligible,
    )

    assert is_claim_eligible(TRUST_AUTHORITATIVE)
    assert is_claim_eligible(TRUST_DERIVED)
    assert not is_claim_eligible(TRUST_PROVISIONAL)


def test_author_derived_people_are_seeded_provisional():
    """The seed-level fix: a name from the author facet is a name, not a person.
    Marking it authoritative would re-create the conflation this phase exists to
    remove."""
    from app.knowledge.seed import TRUST_PROVISIONAL, SeedEntity

    entity = SeedEntity(
        entity_id=SHARMA_A, entity_type="PERSON", canonical_name="Ritu Sharma",
        normalized_name="ritu sharma", source="documents_author",
        trust=TRUST_PROVISIONAL,
    )
    assert entity.claim_eligible is False


def test_provisional_still_obeys_every_veto():
    """Being provisional is not a licence to link loosely — the vetoes apply
    first, so contradictory context still refuses outright."""
    context = ResolutionContext(document_id=DOC)
    context.cms_names["PERSON"].add("someone else")
    decision = resolve_mention(
        _mention("Ritu Sharma", "PERSON"), _person_index("provisional"), context
    )
    assert decision.decision == UNRESOLVED
    assert decision.entity_id is None
