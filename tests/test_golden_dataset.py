"""Schema validation for the eval golden dataset.

Keeps scripts/eval/golden.jsonl well-formed as it grows: parseable JSONL,
unique ids, known classes, and the class-specific expectation keys the runner
depends on. No services needed.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

GOLDEN = Path(__file__).resolve().parent.parent / "scripts" / "eval" / "golden.jsonl"

_CLASSES = {"routing", "analytics", "retrieval", "generation", "unanswerable"}
_SQL_FNS = {"count_documents", "distribution", "list_documents"}
_ROUTING_KEYS = {
    "intent", "operation", "bundle", "group_by", "answer_format", "source_type",
    "date_from", "date_to", "theme_contains", "author_contains", "title_contains_ci",
}


def _items():
    lines = GOLDEN.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_golden_parses_with_unique_ids_and_classes():
    items = _items()
    assert len(items) >= 30
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids))
    assert all(i["class"] in _CLASSES for i in items)
    assert all(i["question"].strip() for i in items)
    assert all(isinstance(i["expect"], dict) for i in items)
    # every class is represented
    assert {i["class"] for i in items} == _CLASSES


def test_golden_class_expectations_have_required_keys():
    for item in _items():
        expect, cls = item["expect"], item["class"]
        if cls == "routing":
            assert set(expect) <= _ROUTING_KEYS, item["id"]
            assert expect, item["id"]
        elif cls == "analytics":
            check = expect["sql_check"]
            assert check["fn"] in _SQL_FNS, item["id"]
            assert isinstance(check["kwargs"], dict), item["id"]
        elif cls == "retrieval":
            ids = expect["relevant_document_ids"]
            assert ids and all(isinstance(d, str) and d for d in ids), item["id"]
        elif cls == "generation":
            assert isinstance(expect["must_contain"], list), item["id"]
            assert isinstance(expect["must_not_contain"], list), item["id"]
        else:  # unanswerable
            assert expect == {"refusal": True}, item["id"]


def test_golden_dates_are_iso():
    for item in _items():
        expect = item["expect"]
        candidates = [expect.get("date_from"), expect.get("date_to")]
        kwargs = expect.get("sql_check", {}).get("kwargs", {})
        candidates += [kwargs.get("published_from"), kwargs.get("published_to")]
        for value in candidates:
            if value is not None:
                date.fromisoformat(value)  # raises on non-ISO
