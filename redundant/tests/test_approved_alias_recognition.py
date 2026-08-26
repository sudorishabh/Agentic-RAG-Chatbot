"""Query-time recognition from the approved alias model.

The gazetteer is built from raw CMS metadata and needs conservative heuristics
against prose. Those heuristics silently dropped whole classes of ordinary
phrasing in a *question* — acronyms, lower case, short authoritative titles,
punctuation variants of a stored name — so entity resolution was never reached.

Every test here pins one of the two halves that had to stay separate: what may be
admitted to the index (review said this alias links) and what may be matched in
the text (this string really is being used as that name). No live MySQL: the
index is built from literal rows, which is what makes the guards assertable.
"""
from __future__ import annotations

import pytest

from app.retrieval.understanding import approved_aliases as aa


def _alias(
    entity_id, normalized, surface, alias_type, canonical_name,
    *, entity_type="ORGANIZATION", autolink=1, is_ambiguous=0,
    normalized_name=None,
):
    return {
        "entity_id": entity_id, "normalized": normalized, "surface": surface,
        "alias_type": alias_type, "autolink": autolink,
        "is_ambiguous": is_ambiguous, "entity_type": entity_type,
        "canonical_name": canonical_name,
        "normalized_name": normalized_name or canonical_name.lower(),
    }


ADB = _alias("org_1", "adb", "ADB", "acronym", "Asian Development Bank",
             normalized_name="asian development bank")
# The live catalog's known-bad glossary mapping.
MOEFCC = _alias("org_2", "moefcc", "MOEFCC", "acronym",
                "Central Pollution Control Board",
                normalized_name="central pollution control board")
# `oil` is a real approved acronym alias, and a question about oil is not a
# question about the company.
OIL = _alias("org_3", "oil", "OIL", "acronym", "Oil India Limited",
             normalized_name="oil india limited")
PERSON = _alias("person_1", "alok adholeya", "Dr Alok Adholeya", "full_name",
                "Dr Alok Adholeya", entity_type="PERSON",
                normalized_name="alok adholeya")
GREEN_JOBS = _alias("project_1", "green jobs", "Green Jobs", "title",
                    "Green Jobs", entity_type="PROJECT",
                    normalized_name="green jobs")
WATER4CROPS = _alias("project_2", "water4crops", "Water4Crops", "title",
                     "Water4Crops", entity_type="PROJECT",
                     normalized_name="water4crops")
CODE = _alias("project_3", "2012mc03", "2012MC03", "code",
              "Eco-city Project- Phase I", entity_type="PROJECT",
              normalized_name="eco city project phase i")
ECO_TITLE = _alias("project_3", "eco city project phase i",
                   "Eco-city Project- Phase I", "title",
                   "Eco-city Project- Phase I", entity_type="PROJECT",
                   normalized_name="eco city project phase i")
# A TERI division whose name is also an ordinary noun phrase.
DIVISION = _alias("org_4", "water resources", "Water Resources", "full_name",
                  "Water Resources", normalized_name="water resources")

ALL = [ADB, MOEFCC, OIL, PERSON, GREEN_JOBS, WATER4CROPS, CODE, ECO_TITLE,
       DIVISION]


def _index(rows=None, organizations=()):
    return aa.ApprovedAliasIndex.build(
        ALL if rows is None else rows, organizations
    )


def _matched(index, question):
    return [(text, alias.entity_id) for text, alias in (
        (question[s:e], a) for s, e, a in index.match(question)
    )]


# --------------------------------------------------------------------------- #
# Admission: which aliases may be linked at all
# --------------------------------------------------------------------------- #

def test_an_acronym_must_be_derivable_from_the_name_it_abbreviates():
    """The guard that catches the live catalog's wrong glossary mapping.

    `MOEFCC -> Central Pollution Control Board` is wrong and is flagged
    `is_ambiguous = 0`, so the review flags alone would have admitted it. CPCB is
    not MOEFCC, and that is the whole test.
    """
    index = _index()
    assert index.get("adb") is not None
    assert index.get("moefcc") is None


@pytest.mark.parametrize(
    "acronym, name, expected",
    [
        ("ADB", "Asian Development Bank", True),
        ("CPCB", "Central Pollution Control Board", True),
        # "Limited" adds a letter the acronym drops.
        ("ONGC", "Oil and Natural Gas Corporation Limited", True),
        # Joining words are skipped, so MNRE not MONARE.
        ("MNRE", "Ministry of New and Renewable Energy", True),
        ("MOEFCC", "Central Pollution Control Board", False),
        ("XYZ", "Asian Development Bank", False),
        ("ADB", "", False),
        ("", "Asian Development Bank", False),
    ],
)
def test_acronym_initials_consistency(acronym, name, expected):
    assert aa.acronym_matches_name(acronym, name) is expected


def test_a_recorded_ambiguity_vetoes_the_surface_for_everyone():
    """Two entities claiming one normalized form: neither links. Checked over
    every row for the form, so a form recorded ambiguous anywhere cannot become
    unambiguous because one of its rows happens to pass the flags."""
    mpcb_a = _alias("org_a", "mpcb", "MPCB", "acronym",
                    "Maharashtra Pollution Control Board", is_ambiguous=1,
                    autolink=0)
    mpcb_b = _alias("org_b", "mpcb", "MPCB", "acronym",
                    "Madhya Pradesh Pollution Control Board", is_ambiguous=1,
                    autolink=0)
    assert _index([mpcb_a, mpcb_b]).get("mpcb") is None
    # And even if one row were flagged clean, the second owner still vetoes.
    mpcb_b_clean = dict(mpcb_b, is_ambiguous=0, autolink=1)
    assert _index([mpcb_a, mpcb_b_clean]).get("mpcb") is None


def test_a_non_autolinkable_alias_is_not_admitted():
    assert _index([dict(ADB, autolink=0)]).get("adb") is None


def test_only_active_claim_eligible_entities_are_loaded():
    """The filter is in the SQL, so this pins the statement rather than a branch:
    an ineligible entity must never reach the index in the first place."""
    import inspect

    source = inspect.getsource(aa.ApprovedAliasIndex.load)
    assert "status = 'active'" in source
    assert "claim_eligible = 1" in source


# --------------------------------------------------------------------------- #
# Matching: whether this occurrence really uses that name
# --------------------------------------------------------------------------- #

def test_an_acronym_needs_upper_case_in_the_question():
    """Case is the signal, and it is the only thing separating a question about
    oil from a question about Oil India Limited."""
    index = _index()
    assert _matched(index, "What did OIL fund?") == [("OIL", "org_3")]
    assert _matched(index, "What about oil prices?") == []
    assert _matched(index, "What did ADB fund?") == [("ADB", "org_1")]
    assert _matched(index, "what did adb fund?") == []


@pytest.mark.parametrize(
    "question",
    [
        "Which projects did Dr Alok Adholeya lead?",
        "Which projects did dr alok adholeya lead?",
        "Which projects did DR ALOK ADHOLEYA lead?",
        "Which projects did dR aLoK aDhOlEyA lead?",
    ],
)
def test_a_person_name_resolves_in_any_casing(question):
    """A person's name is not a common noun, so lower case is not evidence of
    anything. This is the case half of the reported failure."""
    assert _matched(_index(), question) == [
        (question.split("did ")[1].split(" lead")[0], "person_1")
    ]


def test_a_single_token_person_surface_is_still_refused():
    """"Neha" really appears in field_authors; one token is not a person."""
    solo = _alias("person_9", "neha", "Neha", "full_name", "Neha",
                  entity_type="PERSON", normalized_name="neha")
    assert _matched(_index([solo]), "Who is Neha?") == []


def test_a_short_organization_name_needs_a_capital():
    """"Water Resources" is a real TERI division *and* an ordinary noun phrase.
    Only the writer's capitalisation tells them apart, which is the same rule
    the gazetteer applies to short surfaces.

    The matched span may be wider than the name itself — the normalizers fold a
    leading article away, so "the Water Resources" reaches the same key — which
    is why the entity is asserted rather than the exact span boundary.
    """
    index = _index()
    (matched,) = _matched(index, "Ask the Water Resources division")
    text, entity_id = matched
    assert entity_id == "org_4"
    assert "Water Resources" in text
    assert _matched(index, "projects about water resources") == []


def test_a_short_project_title_needs_a_capital_too():
    index = _index()
    assert _matched(index, "Who led Green Jobs?") == [("Green Jobs", "project_1")]
    assert _matched(index, "how many green jobs were created?") == []


def test_a_one_token_title_needs_a_distinctive_shape_not_a_capital():
    """A capital proves nothing about a single word at the start of a sentence, so
    admission rests on shape: a digit or an internal capital. "Water4Crops" has
    both; "Environment" has neither."""
    index = _index()
    assert _matched(index, "What is Water4Crops?") == [
        ("Water4Crops", "project_2")
    ]
    generic = _alias("project_9", "environment", "Environment", "title",
                     "Environment", entity_type="PROJECT",
                     normalized_name="environment")
    assert _matched(_index([generic]), "Tell me about Environment") == []


def test_a_project_code_matches_regardless_of_shape_rules():
    """A code is distinctive by construction, and it is the escape hatch the
    resolver's own specificity veto already documents."""
    index = _index()
    assert _matched(index, "Who led project 2012MC03?") == [
        ("2012MC03", "project_3")
    ]
    assert _matched(index, "who led project 2012mc03?") == [
        ("2012mc03", "project_3")
    ]


@pytest.mark.parametrize(
    "question",
    [
        "Who led the Eco-city Project- Phase I?",
        "Who led the Eco-city Project - Phase I?",
        "Who led the Eco-city Project – Phase I?",   # en dash
        "Who led the Eco-city Project — Phase I?",   # em dash
        "Who led the Eco-city Project (Phase I)?",
        "Who led the Eco-city Project Phase I?",
        "who led the eco-city project phase i?",
    ],
)
def test_punctuation_and_casing_variants_of_a_stored_name_all_match(question):
    """The stored title is "Eco-city Project- Phase I", with that exact hyphen.
    The normalizers already fold every variant onto one key — this pins that they
    are the *same* normalizers that wrote the alias table, so exact matching
    against the store is what happens rather than a similarity guess."""
    matches = _index().match(question)
    assert [a.entity_id for _, _, a in matches] == ["project_3"]


def test_longest_match_wins_and_matches_do_not_overlap():
    index = _index()
    matches = index.match(
        "Did ADB fund the Eco-city Project- Phase I with Water Resources?"
    )
    assert [a.entity_id for _, _, a in matches] == ["org_1", "project_3", "org_4"]
    spans = [(s, e) for s, e, _ in matches]
    assert all(spans[i][1] <= spans[i + 1][0] for i in range(len(spans) - 1))


def test_an_unknown_acronym_matches_nothing():
    assert _matched(_index(), "What did QQQ fund?") == []
    assert _matched(_index(), "What did DBT fund?") == []


# --------------------------------------------------------------------------- #
# Acronyms derived from an organization's own authoritative name
# --------------------------------------------------------------------------- #

def _org(entity_id, name):
    return {"entity_id": entity_id, "canonical_name": name,
            "normalized_name": name.lower()}


def test_an_acronym_derived_from_one_organization_name_is_usable():
    """Not new data: a deterministic function of `canonical_name`, and the
    inverse of the admission guard. MNRE has no alias row in the live catalog."""
    index = _index([], [_org("org_m", "Ministry of New and Renewable Energy")])
    assert _matched(index, "What projects did MNRE fund?") == [("MNRE", "org_m")]


def test_a_derived_acronym_two_organizations_share_is_refused():
    index = _index([], [
        _org("org_x", "Haryana Urban Development Authority"),
        _org("org_y", "Hyderabad Urban Development Authority"),
    ])
    assert _matched(index, "What did HUDA fund?") == []


def test_a_derived_acronym_the_alias_table_calls_ambiguous_is_refused():
    """A recorded ambiguity beats a derived guess: the alias table is the
    reviewed model, and deriving a form it already vetoed would override review."""
    vetoed = _alias("org_p", "mpcb", "MPCB", "acronym",
                    "Madhya Pradesh Pollution Control Board", is_ambiguous=1,
                    autolink=0)
    index = _index([vetoed], [_org("org_q", "Maharashtra Pollution Control Board")])
    assert _matched(index, "What did MPCB fund?") == []


def test_a_derived_acronym_still_needs_upper_case():
    index = _index([], [_org("org_m", "Ministry of New and Renewable Energy")])
    assert _matched(index, "what projects did mnre fund?") == []


# --------------------------------------------------------------------------- #
# Mentions handed to the unchanged resolver
# --------------------------------------------------------------------------- #

def test_a_mention_carries_the_entitys_key_not_the_aliases():
    """The bug this pins cost the whole acronym fix: a mention stamped with the
    *alias's* normalized form ("mnre") sent the resolver looking for an entity
    named "mnre", which found nothing, so recognition worked and resolution
    silently failed."""
    index = _index([ADB])
    (mention,) = aa.lookup_mentions("What did ADB fund?", index=index)
    assert mention.surface_text == "Asian Development Bank"
    assert mention.normalized_text == "asian development bank"
    assert mention.entity_type == "ORGANIZATION"


def test_a_mentions_span_points_at_what_the_user_typed():
    """The surface is the canonical name so the resolver can find it, but the
    span has to stay on the user's words or entity masking in the router blanks
    the wrong part of the question."""
    question = "What did ADB fund?"
    (mention,) = aa.lookup_mentions(question, index=_index([ADB]))
    assert question[mention.start_offset:mention.end_offset] == "ADB"


def test_a_code_match_is_stamped_as_an_identifier():
    """Which is what routes it through the resolver's Tier 0, before scoring."""
    (mention,) = aa.lookup_mentions("Who led 2012MC03?", index=_index([CODE]))
    assert mention.extraction_method == "identifier"
    (other,) = aa.lookup_mentions("Who led Green Jobs?", index=_index([GREEN_JOBS]))
    assert other.extraction_method == "gazetteer"


def test_every_mention_is_stamped_with_this_passs_version():
    """The router's query-side project acceptance keys on this stamp, so it is
    load-bearing rather than decorative."""
    mentions = aa.lookup_mentions(
        "Did ADB fund Green Jobs?", index=_index([ADB, GREEN_JOBS])
    )
    assert mentions
    assert {m.extractor_version for m in mentions} == {"approved-alias-v1"}


def test_a_broken_index_never_breaks_a_query(monkeypatch):
    monkeypatch.setattr(
        aa, "get_index", lambda: (_ for _ in ()).throw(RuntimeError("no mysql"))
    )
    assert aa.lookup_mentions("What did ADB fund?") == []


def test_an_empty_question_matches_nothing():
    assert _index().match("") == []
    assert _index().match("   ") == []
