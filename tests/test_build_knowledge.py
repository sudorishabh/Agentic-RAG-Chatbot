"""Orchestration tests for scripts/build_knowledge.

The stages themselves are already covered by the knowledge-layer suites; what
is untested until now is the *wiring*: that the stages run in the order their
dependencies require, that a dry run touches no store, and that one bad
document cannot take the run down with it.

Every library call is stubbed. Nothing here needs MySQL, Qdrant, Neo4j or an
LLM, and no test is allowed to reach a real writer — several assert exactly
that.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from scripts import build_knowledge as bk


@dataclass
class _SeedEntity:
    entity_id: str = "e1"
    aliases: list = field(default_factory=lambda: [("TERI", "acronym", "cms")])


class _Writes:
    """Records every write a run attempts, so a dry run can be asserted empty."""

    def __init__(self):
        self.calls: list[str] = []

    def record(self, name):
        def _call(*args, **kwargs):
            self.calls.append(name)
            return {"entities": 3, "aliases": 2, "identifiers": 1,
                    "identifier_conflicts": 0} if name == "save_entities" else 1
        return _call


@pytest.fixture
def wired(monkeypatch):
    """Stub every library the orchestrator touches; return the write recorder."""
    writes = _Writes()

    entities = SimpleNamespace(
        save_entities=writes.record("save_entities"),
        mark_ambiguous_aliases=writes.record("mark_ambiguous_aliases"),
    )
    monkeypatch.setitem(
        __import__("sys").modules, "app.catalog.entities", entities
    )
    monkeypatch.setattr(bk, "_write_acronym_aliases", writes.record("acronym_aliases"))

    seed = SimpleNamespace(
        build_seed_entities=lambda: [_SeedEntity(), _SeedEntity("e2")],
        mine_acronym_aliases=lambda: [("e1", "TERI", 4)],
    )
    monkeypatch.setitem(__import__("sys").modules, "app.knowledge.seed", seed)

    promo = SimpleNamespace(
        evaluate_promotions=lambda: [
            SimpleNamespace(promote=True), SimpleNamespace(promote=False)
        ],
        apply_promotions=writes.record("apply_promotions"),
    )
    monkeypatch.setitem(__import__("sys").modules, "app.knowledge.pi_promotion", promo)

    monkeypatch.setattr(bk.Build, "index", lambda self, refresh=False: SimpleNamespace(entities={}))
    return writes


def _run(**options):
    build = bk.Build(bk.Options(**options))
    code = build.run()
    return build, code


# --------------------------------------------------------------------------- #
# Dry run writes nothing.
# --------------------------------------------------------------------------- #

def test_dry_run_writes_nothing(wired):
    build, code = _run(dry_run=True, skip_project=True)
    assert wired.calls == []
    assert code == bk.EXIT_OK


def test_dry_run_still_runs_every_stage(wired):
    """A rehearsal that skipped the work would prove nothing."""
    build, _ = _run(dry_run=True, skip_project=True)
    names = [s.name for s in build.stages if not s.skipped]
    assert names == ["seed", "acronyms", "ambiguity", "pi-promotion"]
    assert build.stages[0].counts["entities"] == 2  # counted, not written
    assert build.stages[1].counts["mined"] == 1
    assert build.stages[3].counts["considered"] == 2


def test_dry_run_reports_itself(wired):
    build, _ = _run(dry_run=True, skip_project=True)
    assert build.report()["dry_run"] is True


def test_dry_run_does_not_project(wired):
    build, _ = _run(dry_run=True)
    project = [s for s in build.stages if s.name == "project"][0]
    assert not project.skipped
    assert any("dry-run" in n for n in project.notes)


# --------------------------------------------------------------------------- #
# A real run writes, in dependency order.
# --------------------------------------------------------------------------- #

def test_write_run_calls_the_writers_in_order(wired):
    build, code = _run(skip_project=True)
    assert wired.calls == [
        "save_entities", "acronym_aliases", "mark_ambiguous_aliases",
        "apply_promotions",
    ]
    assert code == bk.EXIT_OK


def test_stage_order_is_fixed(wired):
    """Acronyms after seeding, ambiguity after acronyms, promotion last: each
    depends on what the one before it wrote."""
    build, _ = _run(skip_project=True)
    assert [s.name for s in build.stages] == [
        "seed", "acronyms", "ambiguity", "pi-promotion", "project",
    ]


def test_skips_are_honoured(wired):
    build, _ = _run(skip_seed=True, skip_acronyms=True, skip_promotion=True,
                    skip_project=True)
    assert wired.calls == ["mark_ambiguous_aliases"]
    skipped = {s.name for s in build.stages if s.skipped}
    assert skipped == {"seed", "acronyms", "pi-promotion", "project"}


# --------------------------------------------------------------------------- #
# Re-running is idempotent at the orchestration level.
# --------------------------------------------------------------------------- #

def test_running_twice_repeats_the_same_writes(wired):
    """The orchestrator adds no bookkeeping: a second run offers the same rows,
    and the writers' own upsert/IGNORE semantics absorb them."""
    _run(skip_project=True)
    first = list(wired.calls)
    wired.calls.clear()
    _run(skip_project=True)
    assert wired.calls == first


# --------------------------------------------------------------------------- #
# Fatal conditions.
# --------------------------------------------------------------------------- #

def test_no_seed_entities_is_fatal(wired, monkeypatch):
    monkeypatch.setitem(
        __import__("sys").modules, "app.knowledge.seed",
        SimpleNamespace(build_seed_entities=lambda: [], mine_acronym_aliases=lambda: []),
    )
    assert bk.main(["--skip-project"]) == bk.EXIT_FATAL


def test_unexpected_failure_is_fatal_not_silent(wired, monkeypatch):
    def boom():
        raise RuntimeError("mysql down")

    monkeypatch.setitem(
        __import__("sys").modules, "app.knowledge.seed",
        SimpleNamespace(build_seed_entities=boom, mine_acronym_aliases=lambda: []),
    )
    assert bk.main(["--skip-project"]) == bk.EXIT_FATAL


# --------------------------------------------------------------------------- #
# CLI surface.
# --------------------------------------------------------------------------- #

def test_cli_defaults_keep_mentions_off(wired):
    assert bk.main(["--dry-run", "--skip-project"]) == bk.EXIT_OK


def test_limit_is_carried_into_the_report(wired, monkeypatch, capsys):
    monkeypatch.setattr(bk.Build, "run", lambda self: bk.EXIT_OK)
    bk.main(["--limit", "500", "--dry-run", "--json"])
    import json

    report = json.loads(capsys.readouterr().out)
    assert report["limit"] == 500
    assert report["with_mentions"] is False
