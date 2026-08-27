"""Unit tests for PI-name promotion.

No database: evidence objects are built from literals. The suite is organised
around the one thing promotion must not do — make a name canonical because it
appeared in a PI field — so the refusal tests carry more weight than the
acceptance ones.
"""

from __future__ import annotations

import pytest

from app.knowledge import pi_promotion as pi
from app.knowledge.seed import CLAIM_ELIGIBLE_TRUST, TRUST_PROVISIONAL, is_claim_eligible


def _evidence(normalized, surface=None, *, projects=1, codes=1,
              divisions=("Energy Group",), starts=("2019-01-01",)):
    return pi.PiEvidence(
        normalized=normalized,
        surface=surface or normalized.title(),
        project_ids={f"doc-{i}" for i in range(projects)},
        project_codes={f"2019XX{i:02d}" for i in range(codes)},
        divisions=set(divisions),
        start_dates=list(starts),
    )


def _decide(evidence, *, surnames=None, ambiguous=frozenset()):
    return pi.decide(
        evidence, surnames=surnames or {}, ambiguous=set(ambiguous)
    )


# --------------------------------------------------------------------------- #
# The rule admits well-evidenced names
# --------------------------------------------------------------------------- #

def test_a_well_evidenced_pi_name_is_promoted():
    """The shape the corpus actually produces: several coded projects inside one
    division over a plausible span."""
    decision = _decide(_evidence(
        "shailly kedia", projects=13, codes=9,
        starts=("2010-01-01", "2022-01-01"),
    ))
    assert decision.promote
    assert "13 project" in decision.reason


def test_a_single_coded_project_is_enough_when_nothing_contradicts():
    assert _decide(_evidence("aishwarya raj")).promote


def test_a_three_token_name_survives_a_crowded_surname():
    """Length is itself discriminating: "Alak Chandra Deka" is specific in a way
    "Amit Kumar" is not, so the surname guard applies only to two-token names."""
    decision = _decide(
        _evidence("alak chandra deka"), surnames={"deka": 30}
    )
    assert decision.promote


# --------------------------------------------------------------------------- #
# The rule refuses everything it cannot distinguish
# --------------------------------------------------------------------------- #

def test_pi_membership_alone_is_not_enough():
    """The brief's rule 2. A PI field earns consideration, never eligibility:
    strip the corroborating evidence and the same name is refused."""
    assert not _decide(_evidence("someone somebody", codes=0)).promote


def test_a_crowded_surname_refuses_a_two_token_name():
    """The "Arun Kumar" guard. 23 other Kumars make the name a poor identity
    however good the project evidence is."""
    decision = _decide(_evidence("amit kumar", projects=8, codes=8),
                       surnames={"kumar": 24})
    assert not decision.promote
    assert "surname shared with 23" in decision.reason


def test_a_surname_just_below_the_threshold_is_allowed():
    decision = _decide(_evidence("rare surname"),
                       surnames={"surname": pi.MAX_SHARED_SURNAME})
    assert decision.promote


@pytest.mark.parametrize("name", ["a k", "r k s", "m"])
def test_initials_are_never_promoted(name):
    """Initials identify nobody, PI field or not."""
    assert not _decide(_evidence(name)).promote


def test_a_single_token_name_is_refused():
    assert not _decide(_evidence("neha")).promote


def test_a_name_marked_ambiguous_is_refused():
    """Already known to denote more than one thing."""
    decision = _decide(_evidence("shared name"), ambiguous={"shared name"})
    assert not decision.promote
    assert "ambiguous" in decision.reason


def test_a_pi_without_any_coded_project_is_refused():
    """Project codes are the authoritative project identifier; a PI anchored to
    no coded project has no authoritative anchor."""
    decision = _decide(_evidence("uncoded person", codes=0))
    assert not decision.promote
    assert "project code" in decision.reason


def test_spanning_several_divisions_is_refused():
    """One senior person or two unrelated ones — the corpus cannot say, so the
    name stays provisional."""
    decision = _decide(_evidence(
        "alok adholeya", divisions=("Biotechnology", "Earth Science")
    ))
    assert not decision.promote
    assert "division areas" in decision.reason


def test_an_implausible_career_span_is_refused():
    decision = _decide(_evidence(
        "long career", starts=("1960-01-01", "2020-01-01")
    ))
    assert not decision.promote
    assert "career span" in decision.reason


# --------------------------------------------------------------------------- #
# Trust model
# --------------------------------------------------------------------------- #

def test_pi_attested_is_claim_eligible_but_not_authoritative():
    """Promotion must not erase why it happened: `pi_attested` is its own level,
    so it stays auditable and reversible."""
    assert is_claim_eligible(pi.TRUST_PI_ATTESTED)
    assert pi.TRUST_PI_ATTESTED in CLAIM_ELIGIBLE_TRUST
    assert pi.TRUST_PI_ATTESTED != "authoritative"


def test_provisional_remains_ineligible():
    assert not is_claim_eligible(TRUST_PROVISIONAL)


def test_promotion_only_ever_raises_provisional_people():
    """The SQL is restricted to trust='provisional', so an authoritative
    identity is left alone and nothing is ever demoted by this pass."""
    import inspect

    source = inspect.getsource(pi.apply_promotions)
    assert "trust='provisional'" in source
    assert "claim_eligible=1" in source


def test_a_decision_records_its_evidence():
    """A promotion has to be explainable after the fact."""
    decision = _decide(_evidence("someone else", projects=4, codes=4))
    assert decision.evidence["projects"] == 4
    assert decision.evidence["project_codes"]
    assert "career_years" in decision.evidence


def test_refusals_carry_a_specific_reason():
    """"Refused" without a reason is undiagnosable, and each reason names the
    single failing test rather than an arbitrary one."""
    reasons = {
        _decide(_evidence("a k")).reason,
        _decide(_evidence("no codes", codes=0)).reason,
        _decide(_evidence("wide", divisions=("A", "B"))).reason,
    }
    assert len(reasons) == 3
    assert all(reason for reason in reasons)


def test_surname_frequency_ignores_single_token_names():
    counts = pi.surname_frequency(["amit kumar", "arun kumar", "neha"])
    assert counts["kumar"] == 2
    assert "neha" not in counts
