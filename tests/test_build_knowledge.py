"""Orchestration tests for scripts/build_knowledge.

The stages themselves are already covered by the knowledge-layer suites; what
is untested until now is the *wiring*: that the stages run in the order their
dependencies require, that a dry run touches no store, that ``--limit`` is
never presented as a corpus-wide verdict, and that the eligibility gates are
reached rather than bypassed.

Every library call is stubbed by patching the real modules' attributes, so the
call sites under test are the real ones. Nothing here needs MySQL, Qdrant,
Neo4j or an LLM, and several tests assert that no writer is reached at all.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from app.catalog import assertions as assertion_store
from app.catalog import entities as entity_store
from app.knowledge import pi_promotion, seed
from app.knowledge.claims import conflicts, extract_cms, validate
from scripts import build_knowledge as bk


@dataclass
class _SeedEntity:
    entity_id: str = "e1"
    aliases: list = field(default_factory=lambda: [("TERI", "acronym", "cms")])


@dataclass
class _Assertion:
    """Enough of an assertion for the orchestrator to move it around."""

    claim_id: str
    subject_entity_id: str = "org-1"
    object_entity_id: str | None = "org-2"
    predicate: str = "FUNDED_BY"
    status: str = "active"
    claim_eligible: bool = True


class _Recorder:
    """Records every write the run attempts, so a dry run can be asserted empty."""

    def __init__(self):
        self.calls: list[str] = []
        self.staged: list = []

    def writer(self, name, result=1):
        def _call(*args, **kwargs):
            self.calls.append(name)
            if name == "stage" and args:
                self.staged.extend(args[0])
            return result
        return _call


@pytest.fixture
def wired(monkeypatch):
    rec = _Recorder()

    # 1-4. entities
    monkeypatch.setattr(seed, "build_seed_entities",
                        lambda: [_SeedEntity(), _SeedEntity("e2")])
    monkeypatch.setattr(seed, "mine_acronym_aliases", lambda: [("e1", "TERI", 4)])
    monkeypatch.setattr(
        entity_store, "save_entities",
        rec.writer("save_entities", {"entities": 3, "aliases": 2,
                                     "identifiers": 1, "identifier_conflicts": 0}),
    )
    monkeypatch.setattr(entity_store, "mark_ambiguous_aliases",
                        rec.writer("mark_ambiguous_aliases"))
    monkeypatch.setattr(bk, "_write_acronym_aliases", rec.writer("acronym_aliases"))
    monkeypatch.setattr(pi_promotion, "evaluate_promotions",
                        lambda: [SimpleNamespace(promote=True),
                                 SimpleNamespace(promote=False)])
    monkeypatch.setattr(pi_promotion, "apply_promotions", rec.writer("apply_promotions"))
    monkeypatch.setattr(bk.Build, "index",
                        lambda self, refresh=False: SimpleNamespace(entities={}))

    # 7-10. claims
    monkeypatch.setattr(extract_cms, "extract_cms_claims",
                        lambda index, limit=None: [_Assertion("c1"), _Assertion("c2")])
    monkeypatch.setattr(
        validate, "validate",
        lambda assertions, **kw: validate.ValidationResult(list(assertions), []),
    )
    monkeypatch.setattr(validate, "dedupe", lambda assertions: list(assertions))
    monkeypatch.setattr(assertion_store, "stage", rec.writer("stage", 2))
    monkeypatch.setattr(assertion_store, "record_rejections",
                        rec.writer("record_rejections", 0))
    monkeypatch.setattr(assertion_store, "total", lambda: 2)
    monkeypatch.setattr(
        conflicts, "detect",
        lambda assertions: conflicts.ConflictReport(
            links=[], status_changes={}, examined=len(assertions), groups=1
        ),
    )
    monkeypatch.setattr(assertion_store, "save_links", rec.writer("save_links", 0))
    monkeypatch.setattr(assertion_store, "apply_status", rec.writer("apply_status", 0))
    return rec


def _run(**options):
    build = bk.Build(bk.Options(**options))
    return build, build.run()


def _stage(build, name):
    return [s for s in build.stages if s.name == name][0]


# --------------------------------------------------------------------------- #
# Dry run writes nothing.
# --------------------------------------------------------------------------- #

def test_dry_run_writes_nothing(wired):
    _, code = _run(dry_run=True, skip_project=True)
    assert wired.calls == []
    assert code == bk.EXIT_OK


def test_dry_run_still_runs_every_stage(wired):
    """A rehearsal that skipped the work would prove nothing."""
    build, _ = _run(dry_run=True, skip_project=True)
    assert [s.name for s in build.stages if not s.skipped] == [
        "seed", "acronyms", "ambiguity", "pi-promotion", "claims", "conflicts",
    ]
    assert _stage(build, "seed").counts["entities"] == 2
    assert _stage(build, "claims").counts["built"] == 2
    assert _stage(build, "claims").counts["accepted"] == 2
    assert "staged" not in _stage(build, "claims").counts


def test_dry_run_does_not_project(wired):
    build, _ = _run(dry_run=True)
    project = _stage(build, "project")
    assert not project.skipped and any("dry-run" in n for n in project.notes)


# --------------------------------------------------------------------------- #
# A real run writes, in dependency order.
# --------------------------------------------------------------------------- #

def test_write_run_calls_the_writers_in_order(wired):
    _, code = _run(skip_project=True)
    assert wired.calls == [
        "save_entities", "acronym_aliases", "mark_ambiguous_aliases",
        "apply_promotions", "stage", "record_rejections",
        "save_links", "apply_status",
    ]
    assert code == bk.EXIT_OK


def test_stage_order_is_fixed(wired):
    build, _ = _run(skip_project=True)
    assert [s.name for s in build.stages] == [
        "seed", "acronyms", "ambiguity", "pi-promotion", "claims", "conflicts",
        "project",
    ]


def test_skips_are_honoured(wired):
    build, _ = _run(skip_seed=True, skip_acronyms=True, skip_promotion=True,
                    skip_project=True)
    assert "save_entities" not in wired.calls
    assert {s.name for s in build.stages if s.skipped} == {
        "seed", "acronyms", "pi-promotion", "project"
    }


# --------------------------------------------------------------------------- #
# --limit is a pilot control, never a corpus verdict.
# --------------------------------------------------------------------------- #

def test_limit_is_passed_to_claim_extraction(wired, monkeypatch):
    seen: list = []
    monkeypatch.setattr(
        extract_cms, "extract_cms_claims",
        lambda index, limit=None: seen.append(limit) or [_Assertion("c1")],
    )
    _run(limit=500, skip_project=True)
    assert seen == [500]


def test_limited_run_reports_conflicts_as_partial(wired):
    build, _ = _run(limit=500, skip_project=True)
    stage = _stage(build, "conflicts")
    assert stage.counts["partial"] == 1
    assert bk.PARTIAL_CONFLICTS in stage.notes
    assert "--limit" in bk.PARTIAL_CONFLICTS


def test_full_run_is_not_marked_partial(wired):
    build, _ = _run(skip_project=True)
    stage = _stage(build, "conflicts")
    assert "partial" not in stage.counts
    assert stage.notes == []


def test_full_run_flags_claims_it_did_not_examine(wired, monkeypatch):
    """A corpus-wide verdict has to cover the whole table; if it cannot, that is
    an error rather than a quiet partial pass."""
    monkeypatch.setattr(assertion_store, "total", lambda: 9)
    build, code = _run(skip_project=True)
    stage = _stage(build, "conflicts")
    assert stage.counts["unexamined"] == 7
    assert any("not examined" in n for n in stage.notes)
    assert code == bk.EXIT_ERRORS


def test_limited_run_does_not_run_the_coverage_check(wired, monkeypatch):
    """Under --limit the batch is knowingly partial, so comparing it with the
    table would report an error for the expected case."""
    monkeypatch.setattr(assertion_store, "total", lambda: 9)
    build, code = _run(limit=500, skip_project=True)
    assert "unexamined" not in _stage(build, "conflicts").counts
    assert code == bk.EXIT_OK


# --------------------------------------------------------------------------- #
# Eligibility is enforced by validation, and the orchestrator cannot skip it.
# --------------------------------------------------------------------------- #

def test_provisional_entities_never_reach_staging(wired, monkeypatch):
    """A provisional PERSON is refused as `object_not_claim_eligible`. Only the
    accepted assertions may be staged."""
    good = _Assertion("keep")
    bad = _Assertion("drop", object_entity_id="person-provisional")
    monkeypatch.setattr(extract_cms, "extract_cms_claims",
                        lambda index, limit=None: [good, bad])
    monkeypatch.setattr(
        validate, "validate",
        lambda assertions, **kw: validate.ValidationResult(
            [a for a in assertions if a.claim_id != "drop"],
            [validate.Rejection("object_not_claim_eligible", "provisional", bad)],
        ),
    )
    build, _ = _run(skip_project=True)

    assert [a.claim_id for a in wired.staged] == ["keep"]
    stage = _stage(build, "claims")
    assert stage.counts["rejected"] == 1
    assert stage.counts["rejected_object_not_claim_eligible"] == 1


def test_validation_receives_the_configured_confidence_floor(wired, monkeypatch):
    from app.config import get_settings

    seen: dict = {}
    monkeypatch.setattr(
        validate, "validate",
        lambda assertions, **kw: seen.update(kw) or validate.ValidationResult(
            list(assertions), []
        ),
    )
    _run(skip_project=True)
    assert seen["min_confidence"] == get_settings().claim_min_confidence


def test_no_claims_leaves_conflicts_empty(wired, monkeypatch):
    monkeypatch.setattr(extract_cms, "extract_cms_claims", lambda index, limit=None: [])
    build, code = _run(skip_project=True)
    assert "stage" not in wired.calls
    assert _stage(build, "conflicts").notes == ["no claims to examine"]
    assert code == bk.EXIT_OK


# --------------------------------------------------------------------------- #
# Re-running, and failure isolation.
# --------------------------------------------------------------------------- #

def test_running_twice_repeats_the_same_writes(wired):
    """The orchestrator adds no bookkeeping: a second run offers the same rows,
    and the writers' own upsert/IGNORE semantics absorb them."""
    _run(skip_project=True)
    first = list(wired.calls)
    wired.calls.clear()
    _run(skip_project=True)
    assert wired.calls == first


def test_a_later_stage_failing_leaves_earlier_writes_intact(wired, monkeypatch):
    """Claims are staged before conflict detection runs. If detection blows up,
    the staged claims stay staged — the run reports fatal, it does not roll back
    work that already succeeded."""
    def boom(assertions):
        raise RuntimeError("detector exploded")

    monkeypatch.setattr(conflicts, "detect", boom)
    build = bk.Build(bk.Options(skip_project=True))
    with pytest.raises(RuntimeError):
        build.run()
    assert "stage" in wired.calls
    assert [a.claim_id for a in wired.staged] == ["c1", "c2"]


# --------------------------------------------------------------------------- #
# Fatal conditions and the CLI surface.
# --------------------------------------------------------------------------- #

def test_no_seed_entities_is_fatal(wired, monkeypatch):
    monkeypatch.setattr(seed, "build_seed_entities", lambda: [])
    assert bk.main(["--skip-project"]) == bk.EXIT_FATAL


def test_unexpected_failure_is_fatal_not_silent(wired, monkeypatch):
    def boom():
        raise RuntimeError("mysql down")

    monkeypatch.setattr(seed, "build_seed_entities", boom)
    assert bk.main(["--skip-project"]) == bk.EXIT_FATAL


def test_cli_dry_run_reports_json(wired, capsys):
    assert bk.main(["--limit", "500", "--dry-run", "--skip-project", "--json"]) == bk.EXIT_OK
    report = json.loads(capsys.readouterr().out)
    assert report["limit"] == 500
    assert report["dry_run"] is True
    assert report["with_mentions"] is False
    notes = [n for s in report["stages"] for n in s["notes"]]
    assert bk.PARTIAL_CONFLICTS in notes


def test_cli_text_report_shows_the_partial_warning(wired, capsys):
    bk.main(["--limit", "500", "--dry-run", "--skip-project"])
    assert "conflict detection is partial" in capsys.readouterr().out
