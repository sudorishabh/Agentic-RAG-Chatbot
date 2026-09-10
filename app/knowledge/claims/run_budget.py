"""The corpus-level ceiling on claim-extraction model calls.

``claim_llm_max_calls_per_run`` has existed in configuration since the claim
extractor was written, documented as the thing that stops "an accidental
full-corpus pass" spending without bound. It was never read. The per-document
ceiling (``knowledge_llm_max_calls_per_document``) was, so no single document
could run away — but nothing bounded the *run*, and 12,003 documents at eight
calls each is a ceiling of 96,024 calls that no setting expressed.

This module is that ceiling. It is separate from :class:`StageOptions` because
the two have different lifetimes: options are rebuilt for every document, while
this has to be the *same* counter across every document in one ingestion run.

Scope
-----
A "run" is one ``ingest_drupal()`` call, which is the only run identity the
system actually has — it is the ``run_id`` written to ``ingest_log`` and carried
on ``DocumentInput``. ``reprocess()`` drives several passes and each is its own
run with its own fresh allowance, which is the useful behaviour: a pass that
exhausts its budget stops there, and the next pass resumes rather than being
permanently capped.

Thread safety
-------------
``ingest_drupal`` ingests on ``ingest_workers`` threads, so several documents
can ask for an allowance at the same instant. :meth:`RunBudget.try_consume`
therefore checks and increments under a lock and returns whether the caller may
proceed — a separate "is there room" property would be a race, because the room
could be gone by the time the caller acted on the answer.
"""
from __future__ import annotations

import threading
from collections import OrderedDict

__all__ = ["RunBudget", "for_run", "reset"]


class RunBudget:
    """A shared allowance of model calls, consumed atomically.

    ``max_calls`` of 0 means the extractor is off, matching the setting's
    documented "0 disables the extractor" — it is not read as "unlimited".
    A negative ceiling is treated the same way, since there is no sensible
    reading of it that permits a call.
    """

    __slots__ = ("max_calls", "_used", "_lock")

    def __init__(self, max_calls: int) -> None:
        self.max_calls = int(max_calls)
        self._used = 0
        self._lock = threading.Lock()

    def try_consume(self) -> bool:
        """Claim one call. True when the caller may proceed.

        The check and the increment are one atomic step on purpose: this is
        what makes the ceiling hold under concurrent ingestion instead of
        being overshot by however many threads looked at the same moment.
        """
        if self.max_calls <= 0:
            return False
        with self._lock:
            if self._used >= self.max_calls:
                return False
            self._used += 1
            return True

    @property
    def used(self) -> int:
        with self._lock:
            return self._used

    @property
    def remaining(self) -> int:
        with self._lock:
            return max(0, self.max_calls - self._used)

    @property
    def exhausted(self) -> bool:
        """Whether the allowance is spent, for reporting rather than gating.

        Callers must gate on :meth:`try_consume`, not on this: between reading
        this and acting on it another thread may have taken the last call.
        """
        if self.max_calls <= 0:
            return True
        with self._lock:
            return self._used >= self.max_calls

    def __repr__(self) -> str:  # pragma: no cover - diagnostics
        return f"RunBudget(used={self.used}/{self.max_calls})"


# One budget per run id. Bounded because a long-lived worker process handles
# many runs and this must not accumulate one entry per run forever; the cap is
# generous next to the number of runs that can overlap, which is one in
# ordinary operation and a handful under `reprocess`'s passes.
_MAX_TRACKED_RUNS = 16
_budgets: "OrderedDict[str, RunBudget]" = OrderedDict()
_registry_lock = threading.Lock()

#: Stands in for a run that carries no id — a single-document CLI invocation,
#: or a test. Such callers still get a real ceiling rather than a free pass.
_UNSCOPED = "__unscoped__"


def for_run(run_id: str | None, max_calls: int) -> RunBudget:
    """The budget shared by every document in ``run_id``.

    The same run id always gets the same object, which is what makes the
    ceiling run-wide rather than per-document. A new run id gets a fresh
    allowance, so the budget resets naturally at a run boundary and no caller
    has to remember to reset it.
    """
    key = run_id or _UNSCOPED
    with _registry_lock:
        budget = _budgets.get(key)
        if budget is None or budget.max_calls != int(max_calls):
            # A changed ceiling means reconfiguration between runs; honour the
            # new number rather than the allowance this key was created with.
            budget = RunBudget(max_calls)
            _budgets[key] = budget
        _budgets.move_to_end(key)
        while len(_budgets) > _MAX_TRACKED_RUNS:
            _budgets.popitem(last=False)
        return budget


def reset(run_id: str | None = None) -> None:
    """Forget one run's budget, or all of them.

    For tests, and for an operator who deliberately wants a run to continue
    past its ceiling after deciding the spend is acceptable.
    """
    with _registry_lock:
        if run_id is None:
            _budgets.clear()
        else:
            _budgets.pop(run_id or _UNSCOPED, None)
