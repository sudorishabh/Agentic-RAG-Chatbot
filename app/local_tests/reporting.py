"""Console reporting helpers for the local ingestion test.

Plain-ASCII output so results render identically in Windows and Unix
terminals and stay readable when redirected to a file.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

WIDTH = 78


def header(title: str) -> None:
    """Top-level banner, one per document or run phase."""
    print()
    print("=" * WIDTH)
    print(f" {title}")
    print("=" * WIDTH)


def section(title: str) -> None:
    """Stage divider inside a document report (extraction, chunking, ...)."""
    print()
    print(f"--- {title} " + "-" * max(0, WIDTH - len(title) - 5))


def kv(label: str, value: Any, indent: int = 2) -> None:
    """One aligned 'label: value' line."""
    print(f"{' ' * indent}{label + ':':<26} {fmt(value)}")


def fmt(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, (list, tuple, set)):
        items = [str(v) for v in value]
        return ", ".join(items) if items else "-"
    return str(value)


def snippet(text: str | None, limit: int = 160) -> str:
    """Single-line preview of a text blob."""
    flat = " ".join((text or "").split())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


def table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str], indent: int = 2) -> None:
    """Fixed-width table of dict rows; long cells are clipped, missing keys show '-'."""
    if not rows:
        print(f"{' ' * indent}(no rows)")
        return
    cells = [[snippet(fmt(row.get(col)), 40) for col in columns] for row in rows]
    widths = [
        max(len(col), *(len(row[i]) for row in cells)) for i, col in enumerate(columns)
    ]
    pad = " " * indent
    print(pad + "  ".join(col.ljust(widths[i]) for i, col in enumerate(columns)))
    print(pad + "  ".join("-" * w for w in widths))
    for row in cells:
        print(pad + "  ".join(row[i].ljust(widths[i]) for i in range(len(columns))))


class Checks:
    """Collects named PASS/FAIL results and renders a run summary."""

    def __init__(self) -> None:
        self._results: list[bool] = []

    def add(self, name: str, ok: bool, detail: str = "") -> bool:
        self._results.append(ok)
        line = f"  [{'PASS' if ok else 'FAIL'}] {name}"
        if detail:
            line += f"  ({detail})"
        print(line)
        return ok

    @property
    def failed(self) -> int:
        return self._results.count(False)

    @property
    def total(self) -> int:
        return len(self._results)

    def summary(self) -> str:
        return f"{self.total - self.failed}/{self.total} checks passed"
