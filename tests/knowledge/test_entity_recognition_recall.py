"""Recognition recall: can a question's words reach the right entity at all?

The gap these tests close was invisible to every existing test, because every
existing test starts from a ``Mention``. Resolution was never the bottleneck —
``normalize_person`` has always folded "Dr Banwari Lal" and "Banwari Lal" onto
one key — but the gazetteer matches **surfaces**, and:

* every one of the 102 claim-eligible people is stored as "Dr X" / "Mr X" /
  "Ms X", while questions say "X"; and
* 50 of those 102 had no surface at all, because they are ``pi_attested``
  identities minted from ``field_completed_pi_name``, which was not a gazetteer
  source — the corpus trusted that field enough to create a canonical person
  from it, but not enough to recognise that person's name in text; and
* 395 of 847 project titles were rejected for being longer than ten words, a
  prose heuristic misapplied to a column that holds titles by construction.

So the mention was never produced and the resolver was never called.

Nothing here relaxes a resolution guard. Every test in the second half asserts
that a guard still holds: generic titles, bare surnames, initials, lowercase
prose and unknown names must still fail to produce a canonical identity, and a
provisional person must still be non-claim-eligible.
"""
from __future__ import annotations

import pytest

from app.knowledge.gazetteer import (
    _eligible,
    build_gazetteer,
    surface_pattern,
    surface_variants,
)
from app.knowledge.normalize import (
    is_honorific,
    normalize_person,
    normalize_project,
    strip_honorifics,
)


def _gaz(rows):
    return build_gazetteer(rows)


def _mentions(text, gazetteer):
    from app.knowledge.extract import extract_mentions

    return extract_mentions(
        text, chunk_id="c", document_id="d", gazetteer=gazetteer
    )


def _surfaces(gazetteer, entity_type=None):
    return {
        e.surface for e in gazetteer.linkable
        if entity_type is None or e.entity_type == entity_type
    }


# =========================================================================== #
# Normalization: titles, honorifics, punctuation, whitespace
# =========================================================================== #


@pytest.mark.parametrize(
    "written,expected",
    [
        ("Dr Banwari Lal", "banwari lal"),
        ("Dr. Banwari Lal", "banwari lal"),
        ("DR BANWARI LAL", "banwari lal"),
        ("Banwari Lal", "banwari lal"),
        ("Banwari Lal, PhD", "banwari lal"),
        ("  Banwari   Lal  ", "banwari lal"),
        ("Prof. Vibha Dhawan", "vibha dhawan"),
        ("Shri Ajay Shankar", "ajay shankar"),
        ("Ms Suruchi Bhadwal", "suruchi bhadwal"),
    ],
)
def test_one_person_normalizes_one_way(written, expected):
    """Already true before this work, and the reason the fix belongs upstream:
    resolution never had an honorific problem."""
    assert normalize_person(written) == expected


@pytest.mark.parametrize(
    "written,expected",
    [
        ("Dr Banwari Lal", "Banwari Lal"),
        ("Dr. Banwari Lal", "Banwari Lal"),
        ("Prof Vibha Dhawan", "Vibha Dhawan"),
        ("Shri Ajay Shankar", "Ajay Shankar"),
        ("Banwari Lal", "Banwari Lal"),
        ("Mr T Senthil Kumar", "T Senthil Kumar"),
    ],
)
def test_stripping_a_title_keeps_the_casing(written, expected):
    """Casing has to survive: short surfaces are matched case-sensitively, and
    a lower-cased variant would silently disarm that guard."""
    assert strip_honorifics(written) == expected


def test_a_name_that_is_only_titles_strips_to_nothing():
    assert strip_honorifics("Dr Prof") == ""
    assert strip_honorifics("") == ""


def test_is_honorific_ignores_case_and_periods():
    for token in ("Dr", "dr", "DR", "Dr.", "Ms.", "Prof", "Shri"):
        assert is_honorific(token), token
    for token in ("Banwari", "Lal", "Drought", "Doctor"):
        assert not is_honorific(token), token


def test_a_title_inside_an_organization_name_is_not_stripped():
    """"Dr Reddy's Laboratories" is an organization whose name begins with one.
    ``surface_variants`` is type-aware for exactly this reason."""
    assert surface_variants("Dr Reddy's Laboratories", "ORGANIZATION") == []
    assert surface_variants("Dr Reddy's Laboratories", "PROJECT") == []


# =========================================================================== #
# Surface variants
# =========================================================================== #


def test_a_titled_person_also_gets_a_bare_surface():
    assert surface_variants("Dr Banwari Lal", "PERSON") == ["Banwari Lal"]


def test_an_untitled_person_gets_no_variant():
    assert surface_variants("Banwari Lal", "PERSON") == []


def test_a_variant_carries_the_same_normalized_key_as_its_parent():
    """The property that makes this safe: the variant reaches the same
    candidates, the same vetoes and the same decision. It only widens what text
    can become a mention."""
    gazetteer = _gaz([("Dr Banwari Lal", "PERSON", "field_completed_pi_name")])
    entries = gazetteer.lookup("banwari lal")
    assert {e.surface for e in entries} == {"Dr Banwari Lal", "Banwari Lal"}
    assert {e.normalized for e in entries} == {"banwari lal"}


def test_a_variant_that_would_be_ineligible_alone_is_dropped():
    """"Dr Neha" strips to a single given name, which is not enough to
    recognise anyone. The variant goes through `_eligible` exactly as a primary
    surface does."""
    gazetteer = _gaz([("Dr Neha", "PERSON", "field_authors")])
    assert "Neha" not in _surfaces(gazetteer)


def test_a_variant_of_an_initials_only_name_is_dropped():
    gazetteer = _gaz([("Dr A K", "PERSON", "field_authors")])
    assert _surfaces(gazetteer, "PERSON") == set()


def test_recognizing_a_person_without_their_title():
    gazetteer = _gaz([("Dr Banwari Lal", "PERSON", "field_completed_pi_name")])
    found = _mentions("The study was led by Banwari Lal at the centre.", gazetteer)
    assert [(m.surface_text, m.entity_type) for m in found] == [
        ("Banwari Lal", "PERSON")
    ]
    # And it lands on the same identity key the titled form does.
    assert found[0].normalized_text == "banwari lal"


def test_recognizing_the_same_person_with_their_title():
    gazetteer = _gaz([("Dr Banwari Lal", "PERSON", "field_completed_pi_name")])
    found = _mentions("The study was led by Dr Banwari Lal.", gazetteer)
    assert found[0].surface_text == "Dr Banwari Lal"
    assert found[0].normalized_text == "banwari lal"


def test_a_bare_name_in_lower_case_prose_is_still_not_recognized():
    """The case-sensitivity guard for short surfaces must survive the variant.
    Losing it would turn every ordinary word that happens to be a name into a
    mention."""
    gazetteer = _gaz([("Dr Banwari Lal", "PERSON", "field_completed_pi_name")])
    assert _mentions("the banwari lal problem is well known", gazetteer) == []


# =========================================================================== #
# PI name fields as a recognition source
# =========================================================================== #


def test_the_pi_name_fields_are_a_gazetteer_source():
    """They already mint canonical people via `pi_promotion`; leaving them out
    of recognition meant 50 of 102 claim-eligible people had no surface at all.
    """
    from app.knowledge.gazetteer import _META_SOURCES

    person_fields = {f for f, t in _META_SOURCES if t == "PERSON"}
    assert "field_completed_pi_name" in person_fields
    assert "field_ongoing_pi_name" in person_fields


def test_a_pi_only_name_becomes_recognizable():
    gazetteer = _gaz([("Ms Sonia Rani", "PERSON", "field_completed_pi_name")])
    assert _mentions("Work carried out by Sonia Rani.", gazetteer)
    assert _mentions("Work carried out by Ms Sonia Rani.", gazetteer)


# =========================================================================== #
# Long project titles
# =========================================================================== #

_LONG_TITLE = (
    "Ecological footprint: establishing a tool to measure and manage urban "
    "energy use in India and China"
)


def test_a_long_project_title_is_recognizable():
    """16 words. Rejected before as "prose", which is a rule for free-text CMS
    fields and a category error for the title column of a project node."""
    gazetteer = _gaz([(_LONG_TITLE, "PROJECT", "project_title")])
    found = _mentions(f"The report covers {_LONG_TITLE} in detail.", gazetteer)
    assert [m.entity_type for m in found] == ["PROJECT"]
    assert found[0].surface_text == _LONG_TITLE


def test_the_length_rule_is_type_aware():
    """A long *organization* value is still prose; a long project title is not.
    """
    long_org = " ".join(f"Word{i}" for i in range(15))
    assert not _eligible(long_org, "x " * 15, "ORGANIZATION")
    assert _eligible(_LONG_TITLE, normalize_project(_LONG_TITLE), "PROJECT")


def test_a_title_with_a_finite_verb_is_still_refused():
    """Length is no longer evidence of prose for a title; grammar still is."""
    descriptive = "Oil is not well for the poor and the environment today"
    assert not _eligible(descriptive, normalize_project(descriptive), "PROJECT")


def test_a_pathological_title_is_still_bounded():
    absurd = " ".join(f"Token{i}" for i in range(60))
    assert not _eligible(absurd, normalize_project(absurd), "PROJECT")


def test_a_long_title_beats_an_organization_buried_inside_it():
    """The measured false merge this fixed.

    "Consultancy to Oil and Natural Gas Corporation Limited for setting up wind
    power project" is 14 words. With the title unrecognisable, the extractor
    matched the *organization* inside it and the question "who funded this
    project" was answered with that organization's funding relationships —
    a different question, answered confidently.
    """
    title = ("Consultancy to Oil and Natural Gas Corporation Limited for "
             "setting up wind power project")
    gazetteer = _gaz([
        (title, "PROJECT", "project_title"),
        ("Oil and Natural Gas Corporation Limited", "ORGANIZATION",
         "field_completed_sponsors"),
    ])
    found = _mentions(f"Who funded {title}?", gazetteer)
    assert [m.entity_type for m in found] == ["PROJECT"]
    assert found[0].surface_text == title


# =========================================================================== #
# The guards, all still holding
# =========================================================================== #


@pytest.mark.parametrize(
    "title", ["Steel", "Summary", "Download", "Environment", "Study"]
)
def test_a_generic_project_title_is_still_not_recognizable(title):
    gazetteer = _gaz([(title, "PROJECT", "project_title")])
    assert _surfaces(gazetteer, "PROJECT") == set()


def test_a_shortened_generic_fragment_of_a_real_title_does_not_match():
    """Only the whole surface matches, so a distinctive title cannot be reached
    by a generic piece of itself."""
    gazetteer = _gaz([(_LONG_TITLE, "PROJECT", "project_title")])
    for fragment in ("Ecological footprint", "urban energy use", "India and China"):
        assert _mentions(f"A study of {fragment} was published.", gazetteer) == [], fragment


@pytest.mark.parametrize("name", ["Sharma", "Kumar", "Singh", "Neha"])
def test_a_single_token_person_name_is_still_not_recognizable(name):
    gazetteer = _gaz([(name, "PERSON", "documents_author")])
    assert _surfaces(gazetteer, "PERSON") == set()


@pytest.mark.parametrize("name", ["A K", "R K", "S S", "A. K."])
def test_an_initials_only_name_is_still_not_recognizable(name):
    gazetteer = _gaz([(name, "PERSON", "documents_author")])
    assert _surfaces(gazetteer, "PERSON") == set()


def test_a_name_attested_for_two_types_still_stops_autolinking():
    """Data-driven ambiguity, unchanged: one normalized form attested for two
    entity types disarms every entry under it, variants included."""
    gazetteer = _gaz([
        ("Green Ventures", "PERSON", "documents_author"),
        ("Green Ventures", "ORGANIZATION", "field_completed_sponsors"),
    ])
    assert all(e.is_ambiguous for bucket in gazetteer.entries.values() for e in bucket)
    assert gazetteer.linkable == []


def test_type_aware_normalization_keeps_a_titled_organization_apart():
    """"Dr Reddy" is two different things depending on the type, and the
    normalizers already say so: the personal form drops the title, the
    organization form keeps it. So they do *not* collide, and the organization
    keeps linking — which is the behaviour type-aware normalization exists for.
    """
    from app.knowledge.normalize import normalize_org

    assert normalize_person("Dr Reddy") == "reddy"
    assert normalize_org("Dr Reddy's Laboratories") == "dr reddy s laboratories"

    gazetteer = _gaz([
        ("Dr Reddy's Laboratories", "ORGANIZATION", "field_completed_sponsors"),
    ])
    found = _mentions("Funded by Dr Reddy's Laboratories.", gazetteer)
    assert [m.entity_type for m in found] == ["ORGANIZATION"]


def test_a_surface_variant_cannot_outlive_its_parents_ambiguity():
    gazetteer = _gaz([
        ("Dr Suraj Prakash", "PERSON", "field_authors"),
        ("Suraj Prakash", "ORGANIZATION", "field_news_source"),
    ])
    # Both the parent and its bare variant share "suraj prakash", which is now
    # attested for two types, so nothing under that key links.
    assert _mentions("A note by Suraj Prakash appeared.", gazetteer) == []


def test_word_boundaries_still_hold_for_a_variant():
    gazetteer = _gaz([("Dr Ram Kumar", "PERSON", "field_completed_pi_name")])
    assert _mentions("The Ram Kumarasamy Trust met today.", gazetteer) == []


def test_the_variant_surface_is_matched_case_sensitively_when_short():
    pattern = surface_pattern("Banwari Lal")
    assert pattern.search("led by Banwari Lal today")
    assert not pattern.search("led by banwari lal today")


# =========================================================================== #
# Resolution safety, end to end
# =========================================================================== #


def _index(rows):
    """A minimal entity index over ``(entity_id, type, canonical, trust,
    claim_eligible)`` rows."""
    from app.knowledge.candidates import EntityIndex
    from app.knowledge.normalize import normalize_for

    entities = {
        entity_id: {
            "entity_id": entity_id, "entity_type": entity_type,
            "canonical_name": name,
            "normalized_name": normalize_for(entity_type, name),
            "trust": trust, "claim_eligible": 1 if eligible else 0,
            "cms_uuid": None, "source": "test", "status": "active",
        }
        for entity_id, entity_type, name, trust, eligible in rows
    }
    return EntityIndex({"entities": entities, "identifiers": {}, "aliases": []})


def _resolve(text, gazetteer, index, *, cms_authors=()):
    from app.knowledge.candidates import ResolutionContext
    from app.knowledge.normalize import normalize_for
    from app.knowledge.resolver import resolve_mention

    found = _mentions(text, gazetteer)
    assert found, f"no mention extracted from {text!r}"
    context = ResolutionContext(document_id="d")
    for author in cms_authors:
        context.cms_names["PERSON"].add(normalize_for("PERSON", author))
    return resolve_mention(found[0], index, context)


def test_a_bare_name_resolves_to_the_titled_canonical_entity():
    """The headline case, end to end: recognition, candidates, resolution."""
    gazetteer = _gaz([("Dr Banwari Lal", "PERSON", "field_completed_pi_name")])
    index = _index([
        ("person_000000000001", "PERSON", "Dr Banwari Lal", "pi_attested", True),
    ])
    decision = _resolve(
        "The work was led by Banwari Lal.", gazetteer, index,
        cms_authors=["Dr Banwari Lal"],
    )
    assert decision.canonical
    assert decision.entity_id == "person_000000000001"
    assert decision.claim_eligible


def test_a_bare_name_without_corroboration_still_does_not_link():
    """Recognition changed; the PERSON corroboration requirement did not."""
    gazetteer = _gaz([("Dr Banwari Lal", "PERSON", "field_completed_pi_name")])
    index = _index([
        ("person_000000000001", "PERSON", "Dr Banwari Lal", "pi_attested", True),
    ])
    decision = _resolve("The work was led by Banwari Lal.", gazetteer, index)
    assert not decision.canonical
    assert decision.decision == "AMBIGUOUS"


def test_a_bare_name_contradicted_by_the_document_is_still_vetoed():
    gazetteer = _gaz([("Dr Banwari Lal", "PERSON", "field_completed_pi_name")])
    index = _index([
        ("person_000000000001", "PERSON", "Dr Banwari Lal", "pi_attested", True),
    ])
    decision = _resolve(
        "The work was led by Banwari Lal.", gazetteer, index,
        cms_authors=["Dr Someone Else Entirely"],
    )
    assert not decision.canonical
    assert decision.decision == "UNRESOLVED"


def test_a_provisional_person_reached_by_a_bare_name_stays_non_eligible():
    """The canonical-leak guard. Widening recognition must not turn a name into
    an identity."""
    gazetteer = _gaz([("Dr Arun Kumar", "PERSON", "documents_author")])
    index = _index([
        ("person_000000000002", "PERSON", "Dr Arun Kumar", "provisional", False),
    ])
    decision = _resolve(
        "A note by Arun Kumar was filed.", gazetteer, index,
        cms_authors=["Dr Arun Kumar"],
    )
    assert decision.decision == "PROVISIONAL"
    assert not decision.canonical
    assert not decision.claim_eligible


def test_two_people_reachable_by_one_bare_name_do_not_link():
    """The false-merge guard, exercised through the new surface.

    Two distinct entities share the normalized key, so the margin collapses and
    neither is chosen — exactly as it would through the titled surface.
    """
    gazetteer = _gaz([("Dr Ritu Sharma", "PERSON", "field_completed_pi_name")])
    index = _index([
        ("person_000000000003", "PERSON", "Dr Ritu Sharma", "pi_attested", True),
        ("person_000000000004", "PERSON", "Ritu Sharma", "provisional", False),
    ])
    decision = _resolve(
        "Reported by Ritu Sharma.", gazetteer, index,
        cms_authors=["Dr Ritu Sharma"],
    )
    assert not decision.canonical


def test_the_candidate_cap_still_refuses_a_crowded_surface():
    from app.knowledge.candidates import MAX_CANDIDATES, generate

    gazetteer = _gaz([("Dr Common Name", "PERSON", "field_completed_pi_name")])
    index = _index([
        (f"person_{i:012d}", "PERSON", "Dr Common Name", "provisional", False)
        for i in range(MAX_CANDIDATES + 5)
    ])
    found = _mentions("Filed by Common Name today.", gazetteer)
    assert found
    assert generate(found[0], index).truncated


def test_a_name_order_variant_does_not_become_a_canonical_identity():
    """Deliberately unchanged, and worth pinning.

    "Adholeya Alok" and "Dr Alok Adholeya" are two rows in the store. Reversing
    word order to merge them would assert an identity from token order alone,
    which is not evidence. The reversed form resolves to the *provisional* row —
    grouping the sightings by name, asserting nothing — and cannot carry claims.
    """
    gazetteer = _gaz([
        ("Dr Alok Adholeya", "PERSON", "field_completed_pi_name"),
        ("Adholeya Alok", "PERSON", "documents_author"),
    ])
    index = _index([
        ("person_000000000005", "PERSON", "Dr Alok Adholeya", "pi_attested", True),
        ("person_000000000006", "PERSON", "Adholeya Alok", "provisional", False),
    ])
    decision = _resolve(
        "Compiled by Adholeya Alok.", gazetteer, index,
        cms_authors=["Adholeya Alok"],
    )
    assert decision.entity_id == "person_000000000006"
    assert not decision.canonical
    assert not decision.claim_eligible
