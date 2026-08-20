"""Shared reporting types for every knowledge orchestrator.

Three callers run the same stages and have to describe what happened in the
same words: ``scripts.build_knowledge`` over the corpus,
``app.knowledge.document_pipeline`` over one document, and
``scripts.knowledge_document`` over one document by hand. They started as one
implementation and would drift into three the moment each grew a counter the
others lacked, so the model lives here and none of them owns it.

``Stage`` is deliberately unchanged from the version that shipped inside
``scripts.build_knowledge``: ``counts`` is what a reader wants, ``errors`` is
what an operator needs — an id per failure, never a bare total — and ``notes``
is for the qualifications that make a count honest ("this run used --limit, so
conflict coverage is partial").
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

logger = logging.getLogger(__name__)

# Outcome of a whole run. `partial` is its own value rather than a flavour of
# `failed` because it is the common case worth retrying: some stages wrote,
# some did not, and what landed is still valid.
STATUS_OK = "ok"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUSES = (STATUS_OK, STATUS_PARTIAL, STATUS_FAILED, STATUS_SKIPPED)

# Errors kept on a report row. An operator needs the first few ids to repeat the
# run; the thousandth is noise, and the column is not a log.
MAX_REPORTED_ERRORS = 20


@dataclass
class Stage:
    """What one stage did."""

    name: str
    counts: dict[str, int] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    skipped: bool = False
    seconds: float = 0.0

    def fail(self, identifier: str, error: Any) -> None:
        """Record one failure without ending the stage."""
        self.errors.append({"id": str(identifier), "error": str(error)})

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.name,
            "skipped": self.skipped,
            "seconds": round(self.seconds, 2),
            "counts": self.counts,
            "notes": self.notes,
            "errors": self.errors,
        }


@contextmanager
def stage_timer(
    stages: list[Stage], name: str, *, skip: bool = False, log: Any = logger
) -> Iterator[Stage]:
    """Append a stage to ``stages``, time it, and log a one-line summary.

    The stage is appended *before* the body runs, so a stage that raises still
    appears in the report rather than vanishing from it.
    """
    stage = Stage(name=name, skipped=skip)
    stages.append(stage)
    if skip:
        log.debug("%-14s skipped", name)
        yield stage
        return
    started = time.monotonic()
    try:
        yield stage
    finally:
        stage.seconds = time.monotonic() - started
        summary = " ".join(f"{k}={v}" for k, v in stage.counts.items())
        log.info(
            "%-14s %s%s", name, summary or "-",
            f"  ({len(stage.errors)} errors)" if stage.errors else "",
        )


def collect_errors(stages: list[Stage]) -> list[dict[str, str]]:
    """Every stage error, capped, each tagged with the stage that raised it."""
    out: list[dict[str, str]] = []
    for stage in stages:
        for error in stage.errors:
            out.append({"stage": stage.name, **error})
            if len(out) >= MAX_REPORTED_ERRORS:
                return out
    return out


def status_for(stages: list[Stage], *, fatal: bool = False) -> str:
    """The run's overall verdict.

    ``fatal`` is for a failure that stopped the run rather than one stage —
    an unreachable entity index, say, which makes everything after it
    meaningless. Anything else with errors is ``partial``: what landed is
    valid, and a retry resumes.
    """
    if fatal:
        return STATUS_FAILED
    if any(stage.errors for stage in stages):
        return STATUS_PARTIAL
    if stages and all(stage.skipped for stage in stages):
        return STATUS_SKIPPED
    return STATUS_OK


def print_stages(stages: list[dict[str, Any]], *, indent: str = "  ") -> None:
    """Human-readable stage lines, for the CLIs."""
    for stage in stages:
        if stage["skipped"]:
            print(f"{indent}{stage['stage']:14} skipped")
            continue
        counts = "  ".join(f"{k}={v}" for k, v in stage["counts"].items())
        print(f"{indent}{stage['stage']:14} {counts or '-'}   {stage['seconds']}s")
        for note in stage["notes"]:
            print(f"{indent}  note: {note}")
        for err in stage["errors"][:10]:
            print(f"{indent}  error: {err['id']}: {err['error']}")
        if len(stage["errors"]) > 10:
            print(f"{indent}  ... and {len(stage['errors']) - 10} more")
