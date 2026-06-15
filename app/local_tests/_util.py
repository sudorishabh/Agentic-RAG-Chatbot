"""Shared helpers for the local test runners.

Each runner builds a human-readable report and writes it to
``app/local_tests/outputs/<name>.txt`` so you can eyeball what the pipeline
produced. Nothing here touches the network.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `import app...` work when a runner is executed directly
# (``python app/local_tests/test_chunking.py``) as well as via ``-m``.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Reports contain text lifted straight from PDFs/HTML (em dashes, non-breaking
# hyphens, …). The default Windows console is cp1252 and chokes on those when we
# echo the report, so switch stdout to UTF-8 with a safe fallback.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
    pass

HERE = Path(__file__).resolve().parent
SAMPLES = HERE / "samples"
OUTPUTS = HERE / "outputs"


class Reporter:
    """Accumulates report lines and prints them both to stdout and a .txt file."""

    def __init__(self, title: str, out_name: str) -> None:
        self.out_path = OUTPUTS / out_name
        self._lines: list[str] = []
        self.rule("=", title)

    def line(self, text: str = "") -> None:
        self._lines.append(text)

    def kv(self, key: str, value: object) -> None:
        self._lines.append(f"{key:>16}: {value}")

    def rule(self, char: str = "-", title: str | None = None) -> None:
        bar = char * 78
        self._lines.append(bar)
        if title:
            self._lines.append(title)
            self._lines.append(bar)

    def preview(self, text: str, limit: int = 600) -> None:
        snippet = (text or "").strip()
        if len(snippet) > limit:
            snippet = snippet[:limit] + f"\n… [+{len(snippet) - limit} more chars]"
        self._lines.append(snippet)

    def write(self) -> Path:
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        body = "\n".join(self._lines) + "\n"
        self.out_path.write_text(body, encoding="utf-8")
        print(body)
        print(f"--> wrote {self.out_path}")
        return self.out_path
