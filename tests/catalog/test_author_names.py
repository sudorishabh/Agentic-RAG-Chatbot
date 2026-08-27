"""Formatting normalization of author names — and the line it must not cross.

The rule this file defends: **normalize formatting when we can prove it is
formatting; never infer that two names denote one person.** Drupal gives authors
as free text with no id, email or reference, so the only evidence available is
the string itself. Collapsing spacing or a courtesy title changes how a name is
written; reordering its tokens changes which name is written, and that is an
identity claim the catalog is not entitled to make.
"""
from __future__ import annotations

import pytest

from app.catalog.author_names import TITLES, normalize


# --------------------------------------------------------------------------- #
# Formatting — safe
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "a,b",
    [
        ("Puri  Munish", "Puri Munish"),              # double space
        ("  Yang Wenrong  ", "Yang Wenrong"),          # edge whitespace
        ("Barrow Colin J.", "Barrow Colin J"),         # trailing period
        ("Corcoran  Alina A.", "Corcoran Alina A"),    # both
        ("Dr. Jayanta Mitra", "Dr Jayanta Mitra"),     # abbreviating period
        ("MEENA SEHGAL", "Meena Sehgal"),              # case
        ("Ram  N K", "Ram N K"),
    ],
)
def test_formatting_differences_collapse(a, b):
    assert normalize(a) == normalize(b)


def test_unicode_compatibility_forms_collapse():
    """A non-breaking space renders identically and compares differently."""
    assert normalize("Meena Sehgal") == normalize("Meena Sehgal")


@pytest.mark.parametrize("title", TITLES)
def test_a_courtesy_title_is_not_part_of_the_name(title):
    assert normalize(f"{title} Meena Sehgal") == normalize("Meena Sehgal")
    assert normalize(f"{title}. Meena Sehgal") == normalize("Meena Sehgal")


def test_different_titles_on_one_name_collapse():
    """'Dr Jitendra Vir Sharma' and 'Mr Jitendra Vir Sharma' are one name."""
    assert normalize("Dr Jitendra Vir Sharma") == normalize("Mr Jitendra Vir Sharma")


def test_stacked_titles_are_removed():
    assert normalize("Dr Prof Alok Adholeya") == normalize("Alok Adholeya")


# --------------------------------------------------------------------------- #
# The guard — a title word that is really a name
# --------------------------------------------------------------------------- #


def test_a_title_word_used_as_a_given_name_survives():
    """"Shri" is both a courtesy title and a common given name. Stripping it
    unguarded turns 'Mr Shri Prakash' — a real person with 22 documents — into
    'prakash', losing the given name and merging him with anyone surnamed
    Prakash. The guard keeps a title only when two tokens would not survive it.
    """
    assert normalize("Mr Shri Prakash") == "shri prakash"
    assert normalize("Shri Prakash") == "shri prakash"
    assert normalize("Dr Shri Krishan") == "shri krishan"


def test_a_lone_name_that_looks_like_a_title_is_untouched():
    assert normalize("Prakash") == "prakash"
    assert normalize("Shri") == "shri"


# --------------------------------------------------------------------------- #
# Inference — refused
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "a,b",
    [
        ("Sehgal Meena", "Meena Sehgal"),
        ("Datta Debajit", "Debajit Datta"),
        ("Sharma Jitendra Vir", "Jitendra Vir Sharma"),
        ("Ram Mohan M P", "M P Ram Mohan"),
    ],
)
def test_name_order_variants_stay_separate(a, b):
    """Surname-first and given-name-first are left as two names.

    Deciding they are one person is an inference about naming convention, and
    the investigation behind this module found nothing in the corpus that could
    settle it — no author id, no email, no reference, and the graph's person
    entities for authors are all provisional. There is also no safe general
    rule: token permutation would merge any two people whose names are
    anagrams.
    """
    assert normalize(a) != normalize(b)


def test_normalization_never_reorders_tokens():
    for raw in ("Sehgal Meena", "Dr Jitendra Vir Sharma", "Mr Shri Prakash"):
        assert normalize(raw).split() == [
            t for t in normalize(raw).split()
        ]
        # the surviving tokens appear in their original relative order
        original = [t.strip(".,;").casefold() for t in raw.split()]
        assert [t for t in normalize(raw).split() if t in original] == [
            t for t in original if t in normalize(raw).split()
        ]


def test_distinct_people_sharing_a_name_are_not_separated_or_merged():
    """Two people called "Arun Kumar" were already one string; normalization
    neither fixes that nor makes it worse. It groups names, not people."""
    assert normalize("Arun Kumar") == normalize("Mr Arun Kumar")


# --------------------------------------------------------------------------- #
# Contract
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "raw",
    ["Dr Jayanta Mitra", "Mr Shri Prakash", "Sehgal Meena", "Barrow Colin J.",
     "  Puri  Munish ", "TERI Web Desk", "Prakash"],
)
def test_idempotent(raw):
    once = normalize(raw)
    assert normalize(once) == once


@pytest.mark.parametrize("raw", [None, "", "   ", ".", ",,"])
def test_empty_input_yields_empty_output(raw):
    assert normalize(raw) == ""


def test_deterministic():
    assert len({normalize("Dr.  Meena   Sehgal") for _ in range(50)}) == 1


def test_an_organisation_stored_as_an_author_is_left_alone():
    """Two rows in the author facet are institutions, not people. Normalization
    has no opinion about that — it is a formatting rule, and the data-entry
    error is fixed at the source, not modelled around."""
    assert normalize("Tampere University, Finland") == "tampere university finland"
