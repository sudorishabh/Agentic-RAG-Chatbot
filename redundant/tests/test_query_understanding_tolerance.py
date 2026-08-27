"""Natural phrasing must reach the right data, without loosening any guard.

Three query-understanding defects, each measured on the live corpus before being
fixed here:

* a date range on a *relationship* was read as a document publication scope, and
  a scope no graph template expresses makes graph routing fail closed — so the
  one path that answers a validity question by interval overlap was the path the
  misreading switched off;
* ``chitchat`` is decided by a single stochastic sample and has no way back, so
  ordinary questions intermittently got "I'm here to help…" instead of an answer;
* a short but authoritative project title could not be resolved even from an
  exact reviewed alias, because the resolver's specificity veto is written for
  prose.
"""
from __future__ import annotations

import pytest

from app.retrieval.query_processor import QueryAnalysis
from app.retrieval.understanding.filters import _facet_filters, _is_relationship_time


def _keys(analysis):
    return [getattr(c, "key", "?") for c in _facet_filters(analysis)]


def _dated(question, **kw):
    return QueryAnalysis(
        search_query=question, intent="qa",
        date_from=kw.get("date_from", "2005-01-01"),
        date_to=kw.get("date_to", "2011-01-01"),
    )


# --------------------------------------------------------------------------- #
# Relationship validity vs document publication date
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "question",
    [
        "What did the Department of Biotechnology fund between 2005 and 2010?",
        "What did the Department of Biotechnology fund in 2011?",
        "What did the Department of Biotechnology fund after 2010?",
        "What did DBT fund since 2010?",
        "What did DBT fund before 2005?",
        "Who led Project X in 2015?",
        "Who led Project X until 2018?",
        "Which organisations sponsored the project between 2005 and 2010?",
        "Who has partnered with TERI since 2010?",
    ],
)
def test_a_date_on_a_relationship_is_not_a_publication_scope(question):
    """The dates bound the relationship, so no `published_at` condition is built
    and the graph keeps its temporal templates."""
    assert _is_relationship_time(_dated(question)) is True
    assert "published_at" not in _keys(_dated(question))


@pytest.mark.parametrize(
    "question",
    [
        "Which documents were published between 2005 and 2010?",
        "Which reports from 2005 to 2010 discuss biofuel?",
        "Show me papers published in 2011",
        "What was issued between 2005 and 2010?",
        "Which articles from 2008 mention solar?",
        "Anything released after 2010?",
    ],
)
def test_a_publication_date_scope_is_preserved_exactly(question):
    """The existing behaviour, untouched. This is the half that must not regress:
    "documents published between 2005 and 2010" really is a `published_at` query."""
    assert _is_relationship_time(_dated(question)) is False
    assert "published_at" in _keys(_dated(question))


def test_publication_language_wins_when_a_question_says_both():
    """"papers published in 2011 funded by DBT" names a predicate *and* a
    publication date. The conservative reading keeps the document scope."""
    question = "Which papers published in 2011 were funded by DBT?"
    assert _is_relationship_time(_dated(question)) is False
    assert "published_at" in _keys(_dated(question))


def test_a_date_with_no_relationship_named_keeps_the_document_scope():
    """No predicate means there is no relationship for the dates to modify, so
    the default stands rather than the filter being dropped on a guess."""
    question = "What happened between 2005 and 2010?"
    assert _is_relationship_time(_dated(question)) is False
    assert "published_at" in _keys(_dated(question))


def test_a_relational_question_with_no_dates_builds_no_date_condition():
    analysis = QueryAnalysis(
        search_query="What did DBT fund?", intent="qa",
        date_from=None, date_to=None,
    )
    assert _keys(analysis) == []


def test_the_other_facets_are_unaffected_by_the_temporal_split():
    """Dropping the date condition must not drop theme, tags, source or language."""
    analysis = QueryAnalysis(
        search_query="What did DBT fund between 2005 and 2010?", intent="qa",
        date_from="2005-01-01", date_to="2011-01-01",
        theme="Water", tags=["Ground water"], source_type="website",
        language="en",
    )
    keys = _keys(analysis)
    assert "published_at" not in keys
    assert "source_type" in keys and "language" in keys and "tags" in keys


def test_an_empty_question_is_never_read_as_relationship_time():
    assert _is_relationship_time(_dated("")) is False


# --------------------------------------------------------------------------- #
# The chitchat override
# --------------------------------------------------------------------------- #

def _probe(monkeypatch, *, relational, matched):
    """Stub the two halves of the shape probe."""
    import app.retrieval.understanding.approved_aliases as aa
    import app.retrieval.understanding.relational as rel

    class _Intent:
        is_relational = relational

    class _Index:
        def match(self, question):
            return [("x",)] if matched else []

    monkeypatch.setattr(rel, "read_relational", lambda q: _Intent())
    monkeypatch.setattr(aa, "get_index", lambda: _Index())


def test_a_relational_question_about_a_known_entity_is_not_chitchat(monkeypatch):
    from app.retrieval import query_processor as qp

    _probe(monkeypatch, relational=True, matched=True)
    assert qp._corrected_intent("Who led Green Jobs?", "chitchat") == "qa"


@pytest.mark.parametrize(
    "relational, matched",
    [(False, False), (True, False), (False, True)],
)
def test_both_halves_are_required_to_overrule_chitchat(monkeypatch, relational, matched):
    """A greeting names neither. "Thanks for the funding update" names a cue but
    no entity. "Tell me about TERI" names an entity but no relationship. None of
    them is a relational question, and none is overridden."""
    from app.retrieval import query_processor as qp

    _probe(monkeypatch, relational=relational, matched=matched)
    assert qp._corrected_intent("something", "chitchat") == "chitchat"


@pytest.mark.parametrize("intent", ["qa", "structured", "scoped_summary"])
def test_the_override_only_ever_reads_chitchat(monkeypatch, intent):
    """One-directional by construction: it can rescue a misfiled question and can
    never send a real one to the canned reply."""
    from app.retrieval import query_processor as qp

    _probe(monkeypatch, relational=True, matched=True)
    assert qp._corrected_intent("Who led Green Jobs?", intent) == intent


def test_the_probe_never_raises(monkeypatch):
    from app.retrieval import query_processor as qp
    import app.retrieval.understanding.relational as rel

    monkeypatch.setattr(
        rel, "read_relational",
        lambda q: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert qp._names_entity_and_relationship("anything") is False
    assert qp._corrected_intent("anything", "chitchat") == "chitchat"


def test_intent_classification_does_not_reach_into_graph_retrieval():
    """The probe deliberately asks recognition and the cue vocabulary rather than
    the router: knowing a question is not small talk needs far less evidence than
    answering it, and graph retrieval keeps its single doorway."""
    import inspect

    from app.retrieval import query_processor as qp

    source = inspect.getsource(qp)
    assert "app.retrieval.graph" not in source


# --------------------------------------------------------------------------- #
# The router's query-side acceptance for short authoritative project titles
# --------------------------------------------------------------------------- #

class _Decision:
    def __init__(self, **kw):
        self.entity_type = kw.get("entity_type", "PROJECT")
        self.claim_eligible = kw.get("claim_eligible", True)
        self.candidate_audit = kw.get("candidate_audit", [])
        self.surface_text = kw.get("surface_text", "Green Jobs")
        self.score = kw.get("score", 0.0)


class _Mention:
    def __init__(self, version="approved-alias-v1"):
        self.extractor_version = version


def _candidate(**kw):
    return {
        "entity_id": kw.get("entity_id", "project_1"),
        "trust": kw.get("trust", "authoritative"),
        "vetoes": kw.get("vetoes", ["v_project_name_not_specific"]),
    }


def test_an_exact_reviewed_alias_can_carry_a_short_project_title():
    """The four projects the specificity veto made unreachable — WEO 2007,
    HI-AWARE, Green Jobs, Water4Crops — are authoritative CMS project nodes with
    reviewed, unambiguous, autolinkable title aliases."""
    from app.retrieval.graph import router

    accepted = router._accept_approved_project(
        _Decision(candidate_audit=[_candidate()]), _Mention()
    )
    assert accepted is not None
    assert accepted.entity_id == "project_1"


@pytest.mark.parametrize(
    "kwargs, mention, reason",
    [
        ({"candidate_audit": [_candidate(vetoes=["v_ambiguous_alias"])]},
         _Mention(), "another veto"),
        ({"candidate_audit": [_candidate(
            vetoes=["v_project_name_not_specific", "v_ambiguous_alias"])]},
         _Mention(), "a second veto alongside it"),
        ({"candidate_audit": [_candidate(), _candidate(entity_id="project_2")]},
         _Mention(), "two candidates"),
        ({"candidate_audit": [_candidate(vetoes=[])]},
         _Mention(), "no veto at all — the normal path owns that"),
        ({"candidate_audit": [_candidate(trust="derived")]},
         _Mention(), "not authoritative"),
        ({"claim_eligible": False, "candidate_audit": [_candidate()]},
         _Mention(), "not claim-eligible"),
        ({"entity_type": "PERSON", "candidate_audit": [_candidate()]},
         _Mention(), "not a project"),
        ({"candidate_audit": [_candidate()]},
         _Mention(version="gazetteer"), "not from the approved-alias pass"),
        ({"candidate_audit": []}, _Mention(), "no candidates"),
    ],
)
def test_every_condition_on_that_acceptance_is_load_bearing(kwargs, mention, reason):
    from app.retrieval.graph import router

    assert router._accept_approved_project(_Decision(**kwargs), mention) is None, reason


def test_the_specificity_veto_itself_is_untouched():
    """The veto is shared with ingestion, where a wrong link becomes permanent.
    The query-side acceptance reads its audit trail; it does not relax the rule."""
    from app.knowledge import scoring

    assert scoring.is_specific_project_name("green jobs") is False
    assert scoring.is_specific_project_name("conserving mycorrhizal diversity") is True
