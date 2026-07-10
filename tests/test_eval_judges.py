"""Unit tests for the decomposed eval judges.

Covers deterministic citation coverage, claim-evidence selection, the
faithfulness composition (rate math, fail-open on extraction/check errors),
and relevance clamping. All LLM calls are stubbed; no network.
"""

from __future__ import annotations

from scripts.eval import judges


class _FakeStructured:
    """Stands in for get_structured_llm().with_structured_output(schema)."""

    def __init__(self, responses):
        self.responses = dict(responses)

    def with_structured_output(self, schema):
        outer = self

        class _Bound:
            def invoke(self, messages):
                value = outer.responses[schema.__name__]
                if isinstance(value, Exception):
                    raise value
                return value

        return _Bound()


def _stub(monkeypatch, **responses):
    import app.generation.llm_client as llm_client

    monkeypatch.setattr(
        llm_client, "get_structured_llm", lambda: _FakeStructured(responses)
    )


# --------------------------------------------------------------------------- #
# citation_coverage — deterministic.
# --------------------------------------------------------------------------- #

def test_citation_coverage_fractions():
    assert judges.citation_coverage("Solar grew 40% [1]. Wind fell [2].") == 1.0
    assert judges.citation_coverage("Solar grew 40% [1]. Wind fell.") == 0.5
    assert judges.citation_coverage("No citations here. None at all.") == 0.0
    assert judges.citation_coverage("") == 0.0


def test_citation_coverage_counts_bullet_lines():
    answer = "- point one [1]\n- point two\n- point three [2]"
    assert abs(judges.citation_coverage(answer) - 2 / 3) < 1e-9


# --------------------------------------------------------------------------- #
# Claim evidence selection.
# --------------------------------------------------------------------------- #

def test_text_for_claim_uses_cited_blocks():
    blocks = ["block one", "block two", "block three"]
    claim = judges.Claim(text="x", citations=[2])
    assert judges._text_for_claim(claim, blocks) == "block two"
    both = judges.Claim(text="x", citations=[1, 3])
    assert judges._text_for_claim(both, blocks) == "block one\n\nblock three"


def test_text_for_claim_falls_back_to_all_blocks():
    blocks = ["a", "b"]
    uncited = judges.Claim(text="x", citations=[])
    out_of_range = judges.Claim(text="x", citations=[9])
    assert judges._text_for_claim(uncited, blocks) == "a\n\nb"
    assert judges._text_for_claim(out_of_range, blocks) == "a\n\nb"


# --------------------------------------------------------------------------- #
# judge_faithfulness — composition and fail-open.
# --------------------------------------------------------------------------- #

def test_judge_faithfulness_rate_math(monkeypatch):
    claims = [
        judges.Claim(text="supported claim", citations=[1]),
        judges.Claim(text="unsupported claim", citations=[1]),
    ]
    monkeypatch.setattr(judges, "extract_claims", lambda answer: claims)
    monkeypatch.setattr(
        judges, "claim_supported", lambda text, block: text == "supported claim"
    )

    report = judges.judge_faithfulness("answer", ["block"])

    assert report["total"] == 2 and report["supported"] == 1
    assert report["rate"] == 0.5 and report["faithful"] is False
    assert [c["supported"] for c in report["claims"]] == [True, False]


def test_judge_faithfulness_no_claims_is_faithful(monkeypatch):
    monkeypatch.setattr(judges, "extract_claims", lambda answer: [])
    report = judges.judge_faithfulness("Thanks for asking!", ["block"])
    assert report == {"claims": [], "total": 0, "supported": 0, "rate": 1.0,
                      "faithful": True}


def test_judge_faithfulness_fails_open(monkeypatch):
    def boom(answer):
        raise RuntimeError("llm down")

    monkeypatch.setattr(judges, "extract_claims", boom)
    assert judges.judge_faithfulness("answer", ["block"]) is None

    # All per-claim checks erroring -> None, not a fake 0% rate.
    monkeypatch.setattr(
        judges, "extract_claims", lambda a: [judges.Claim(text="c", citations=[])]
    )
    monkeypatch.setattr(judges, "claim_supported", lambda t, b: None)
    assert judges.judge_faithfulness("answer", ["block"]) is None

    assert judges.judge_faithfulness("answer", []) is None  # nothing to check


def test_claim_supported_verdict_and_error(monkeypatch):
    _stub(monkeypatch, SupportVerdict=judges.SupportVerdict(supported=True))
    assert judges.claim_supported("c", "b") is True

    _stub(monkeypatch, SupportVerdict=RuntimeError("down"))
    assert judges.claim_supported("c", "b") is None


# --------------------------------------------------------------------------- #
# extract_claims / judge_relevance via the stubbed LLM.
# --------------------------------------------------------------------------- #

def test_extract_claims_drops_blank_text(monkeypatch):
    _stub(monkeypatch, ClaimList=judges.ClaimList(claims=[
        judges.Claim(text="real claim", citations=[1]),
        judges.Claim(text="   ", citations=[2]),
    ]))
    claims = judges.extract_claims("answer")
    assert [c.text for c in claims] == ["real claim"]


def test_judge_relevance_clamps_and_fails_open(monkeypatch):
    _stub(monkeypatch, RelevanceScore=judges.RelevanceScore(score=9))
    assert judges.judge_relevance("q", "a") == 5

    _stub(monkeypatch, RelevanceScore=judges.RelevanceScore(score=-2))
    assert judges.judge_relevance("q", "a") == 1

    _stub(monkeypatch, RelevanceScore=RuntimeError("down"))
    assert judges.judge_relevance("q", "a") is None
