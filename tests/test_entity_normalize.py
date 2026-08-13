"""Unit tests for knowledge-layer name normalization.

Pure string work; no DB, no network. Normalization is a comparison key, so the
tests come in pairs: variants of one name must agree, and different names must
not — the second half is what keeps a false merge from starting here.
"""

from __future__ import annotations

from app.knowledge import normalize as n


# --------------------------------------------------------------------------- #
# Shared folding
# --------------------------------------------------------------------------- #

def test_case_whitespace_and_accents_fold():
    assert n.normalize("  Deutsche   Gesellschaft  ") == "deutsche gesellschaft"
    assert n.normalize("Zusammenarbeit für Energie") == "zusammenarbeit fur energie"


def test_hyphen_and_space_reach_the_same_key():
    """"Asia-Pacific" and "Asia Pacific" are one name written two ways; joining
    them into "asiapacific" instead would also join genuinely separate words."""
    assert n.normalize("Asia-Pacific") == n.normalize("Asia Pacific") == "asia pacific"


def test_empty_and_punctuation_only_normalize_to_empty():
    for junk in ("", "   ", "...", "-- , --", "()"):
        assert n.normalize(junk) == ""


# --------------------------------------------------------------------------- #
# PERSON — the open-world, high-risk case
# --------------------------------------------------------------------------- #

def test_honorifics_are_stripped():
    for surface in ("Dr R K Pachauri", "Dr. R K Pachauri", "Shri R K Pachauri"):
        assert n.normalize_person(surface) == "r k pachauri"


def test_initials_agree_across_punctuation():
    """The corpus writes the same author three ways; all must block together."""
    assert (
        n.normalize_person("R.K. Pachauri")
        == n.normalize_person("R K Pachauri")
        == n.normalize_person("R. K. Pachauri")
        == "r k pachauri"
    )


def test_different_initials_stay_different():
    """The other half of the pair: folding must not make two people one."""
    assert n.normalize_person("R K Pachauri") != n.normalize_person("S K Pachauri")


def test_post_nominals_are_stripped():
    assert n.normalize_person("Leena Srivastava, PhD") == "leena srivastava"


def test_trailing_digit_artifact_is_dropped():
    """`field_authors` really contains "Asha Ram Sihag2"."""
    assert n.normalize_person("Asha Ram Sihag2") == "asha ram sihag"


def test_double_spacing_artifact_folds():
    """`documents_author` really contains "Adholeya  Alok"."""
    assert n.normalize_person("Adholeya  Alok") == "adholeya alok"


def test_initials_only_is_detectable():
    """"A." and "A. K." are in the author facet and name nobody in particular."""
    assert n.is_initials_only(n.normalize_person("A."))
    assert n.is_initials_only(n.normalize_person("A. K."))
    assert not n.is_initials_only(n.normalize_person("A K Sharma"))


def test_initials_of_is_a_blocking_key_not_a_match():
    assert n.initials_of("rajendra kumar pachauri") == "rkp"
    assert n.initials_of("r k pachauri") == "rkp"


# --------------------------------------------------------------------------- #
# ORGANIZATION
# --------------------------------------------------------------------------- #

def test_legal_forms_regularise():
    assert n.normalize_org("ACC Ltd") == n.normalize_org("ACC Limited")


def test_ampersand_spells_out():
    assert n.normalize_org("Growth & Commercialization") == (
        "growth and commercialization"
    )


def test_org_keeps_a_leading_honorific():
    """"Dr Reddy's Laboratories" is an organization whose name starts with one —
    stripping it, as PERSON does, would rename the company."""
    assert n.normalize_org("Dr Reddy's Laboratories").startswith("dr reddy")


def test_org_and_person_normalizers_differ_on_the_same_string():
    assert n.normalize_org("Dr Reddy") != n.normalize_person("Dr Reddy")


# --------------------------------------------------------------------------- #
# PROJECT
# --------------------------------------------------------------------------- #

def test_leading_article_is_dropped():
    assert n.normalize_project("The Solar Mission") == n.normalize_project(
        "Solar Mission"
    )


def test_normalize_for_dispatches_by_type():
    assert n.normalize_for("PERSON", "Dr Neha") == "neha"
    assert n.normalize_for("ORGANIZATION", "ACC Ltd") == "acc limited"
    assert n.normalize_for("PROJECT", "The Solar Mission") == "solar mission"
    # An unknown type falls back to the generic fold rather than raising.
    assert n.normalize_for("UNKNOWN", "Dr Neha") == "dr neha"
