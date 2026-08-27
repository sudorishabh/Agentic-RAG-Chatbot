"""Console + file reporting for the local ingestion test.

Everything emitted goes to the console and to every active file sink, so a
run can mirror its output into a run-level report file and a per-document
file at the same time. Plain-ASCII output so results render identically in
Windows and Unix terminals.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence, TextIO

WIDTH = 78

_sinks: list[TextIO] = []
_console_enabled = True


def emit(text: str = "") -> None:
    """Write one line to the console (unless quieted) and every file sink."""
    if _console_enabled:
        print(text)
    for handle in _sinks:
        print(text, file=handle)


@contextmanager
def quiet_console() -> Iterator[None]:
    """Suppress console output while active; file sinks still receive it.
    Used to keep large per-document dumps in files without flooding the terminal."""
    global _console_enabled
    previous = _console_enabled
    _console_enabled = False
    try:
        yield
    finally:
        _console_enabled = previous


@contextmanager
def sink(path: Path) -> Iterator[None]:
    """Mirror emitted output into ``path`` while active. Sinks nest, so a
    per-document file can be active inside the run-level report file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("w", encoding="utf-8")
    _sinks.append(handle)
    try:
        yield
    finally:
        _sinks.remove(handle)
        handle.close()


def header(title: str) -> None:
    """Top-level banner, one per document or run phase."""
    emit()
    emit("=" * WIDTH)
    emit(f" {title}")
    emit("=" * WIDTH)


def section(title: str) -> None:
    """Stage divider inside a document report (extraction, chunking, ...)."""
    emit()
    emit(f"--- {title} " + "-" * max(0, WIDTH - len(title) - 5))


def kv(label: str, value: Any, indent: int = 2) -> None:
    """One aligned 'label: value' line."""
    emit(f"{' ' * indent}{label + ':':<26} {fmt(value)}")


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


def block(text: str | None, indent: int = 4) -> None:
    """Emit a multi-line text blob verbatim (no truncation), each line indented."""
    pad = " " * indent
    if not text:
        emit(f"{pad}(empty)")
        return
    for line in str(text).splitlines() or [""]:
        emit(pad + line)


def table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str], indent: int = 2) -> None:
    """Fixed-width table of dict rows; long cells are clipped, missing keys show '-'."""
    if not rows:
        emit(f"{' ' * indent}(no rows)")
        return
    cells = [[snippet(fmt(row.get(col)), 40) for col in columns] for row in rows]
    widths = [
        max(len(col), *(len(row[i]) for row in cells)) for i, col in enumerate(columns)
    ]
    pad = " " * indent
    emit(pad + "  ".join(col.ljust(widths[i]) for i, col in enumerate(columns)))
    emit(pad + "  ".join("-" * w for w in widths))
    for row in cells:
        emit(pad + "  ".join(row[i].ljust(widths[i]) for i in range(len(columns))))


class Checks:
    """Collects named PASS/FAIL results and renders a run summary."""

    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def add(self, name: str, ok: bool, detail: str = "") -> bool:
        self.results.append({"name": name, "ok": bool(ok), "detail": detail})
        line = f"  [{'PASS' if ok else 'FAIL'}] {name}"
        if detail:
            line += f"  ({detail})"
        emit(line)
        return ok

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r["ok"])

    @property
    def total(self) -> int:
        return len(self.results)

    def summary(self) -> str:
        return f"{self.total - self.failed}/{self.total} checks passed"
