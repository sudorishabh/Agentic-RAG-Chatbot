"""The corpus-level model-call ceiling, at the level of the counter itself.

`claim_llm_max_calls_per_run` was declared and never read, so nothing bounded a
full-corpus pass. These cover the counter's own contract; the pipeline tests
cover what the claims stage does when it comes back empty.
"""
from __future__ import annotations

import threading

from app.knowledge.claims import run_budget as rb


def setup_function() -> None:
    rb.reset()


def test_the_allowance_is_spent_one_call_at_a_time():
    budget = rb.RunBudget(3)
    assert [budget.try_consume() for _ in range(5)] == [True, True, True, False, False]
    assert budget.used == 3
    assert budget.remaining == 0
    assert budget.exhausted


def test_call_201_is_never_started_when_the_limit_is_200():
    """The requirement, at the number the setting actually ships with."""
    budget = rb.RunBudget(200)
    granted = sum(1 for _ in range(500) if budget.try_consume())
    assert granted == 200, "exactly the ceiling, not one more"
    assert budget.used == 200
    assert budget.try_consume() is False, "call 201 is refused"


def test_a_zero_ceiling_disables_the_extractor_rather_than_unbounding_it():
    """The setting documents "0 disables the extractor". Read as "unlimited" it
    would do the exact opposite of what it says, on the default-off path."""
    budget = rb.RunBudget(0)
    assert budget.try_consume() is False
    assert budget.exhausted
    assert budget.remaining == 0


def test_a_negative_ceiling_permits_nothing():
    assert rb.RunBudget(-5).try_consume() is False


def test_the_ceiling_holds_when_documents_are_ingested_concurrently():
    """`ingest_drupal` runs on `ingest_workers` threads, so the check and the
    increment have to be one step. Were they separate, several threads would
    read the same remaining count and every one of them would proceed."""
    budget = rb.RunBudget(50)
    granted: list[bool] = []
    lock = threading.Lock()

    def worker() -> None:
        for _ in range(20):
            ok = budget.try_consume()
            with lock:
                granted.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(granted) == 50, "320 attempts, 50 allowed, no overshoot"
    assert budget.used == 50


# --------------------------------------------------------------------------- #
# Run scoping
# --------------------------------------------------------------------------- #

def test_every_document_in_one_run_shares_the_same_allowance():
    """The whole point. A per-document counter already existed; what was
    missing was one that spans the documents of a run."""
    first = rb.for_run("run-a", 10)
    second = rb.for_run("run-a", 10)
    assert first is second
    for _ in range(10):
        assert first.try_consume()
    assert second.try_consume() is False, "the second document sees it spent"


def test_a_new_run_starts_with_a_fresh_allowance():
    spent = rb.for_run("run-a", 2)
    assert spent.try_consume() and spent.try_consume()
    assert spent.try_consume() is False

    nxt = rb.for_run("run-b", 2)
    assert nxt is not spent
    assert nxt.try_consume(), "a later pass is not permanently capped"


def test_a_run_without_an_id_still_gets_a_real_ceiling():
    """A single-document CLI invocation carries no run id. Treating that as
    unscoped-and-therefore-unlimited would leave the documented ceiling off on
    exactly the path a person runs by hand."""
    budget = rb.for_run(None, 1)
    assert budget.try_consume()
    assert rb.for_run(None, 1).try_consume() is False


def test_reconfiguring_the_ceiling_between_runs_is_honoured():
    rb.for_run("run-a", 5).try_consume()
    assert rb.for_run("run-a", 9).max_calls == 9, "the new number wins"


def test_the_registry_does_not_grow_without_bound():
    """A long-lived worker handles many runs; one entry per run forever is a
    leak. The most recent are the ones that can still be spending."""
    for n in range(rb._MAX_TRACKED_RUNS * 3):
        rb.for_run(f"run-{n}", 4)
    assert len(rb._budgets) <= rb._MAX_TRACKED_RUNS


def test_reset_forgets_one_run_or_all_of_them():
    a, b = rb.for_run("run-a", 1), rb.for_run("run-b", 1)
    assert a.try_consume() and b.try_consume()

    rb.reset("run-a")
    assert rb.for_run("run-a", 1).try_consume(), "run-a starts over"
    assert rb.for_run("run-b", 1).try_consume() is False, "run-b is untouched"

    rb.reset()
    assert rb.for_run("run-b", 1).try_consume()
