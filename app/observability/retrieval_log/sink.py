"""Where a finished trace goes on disk.

    logs/
    |-- 2026-08-27/
    |   |-- tell me about carbon sequestration - 2026-08-27 10-51-10 IST/
    |   |   |-- trace.json              the record, for parsing
    |   |   +-- report.md               the same trace explained, for reading
    |   +-- ...
    |-- errors/
    |   +-- 2026-08-27/
    |       +-- <same name>/            a copy of any query that had a failure
    +-- summary/
        +-- 2026-08-27.jsonl            one flat line per query

One directory per query, because a query produces more than one artifact and
guessing which files belong together from a flat listing is work a directory
does for free. It is named after the question and the local time it was asked
(see :mod:`app.observability.retrieval_log.naming`), so the right trace can be
found by looking; the file names inside are fixed, so ``logs/*/*/trace.json``
is a stable glob and ``report.md`` is always next to the data it describes.

Three properties this file exists to guarantee:

**A logging failure is never the caller's problem.** Every public function here
catches everything. A full disk, a locked file, a path that cannot be created —
each costs the trace and nothing else. The warning is emitted once per process
so a persistent failure cannot flood the application log it shares.

**Concurrent queries cannot overwrite each other.** The directory name is for
reading and promises nothing, so uniqueness is enforced by *creating* it: a
plain ``mkdir`` is atomic, the winner owns the name and a loser takes the next
one (see :func:`_reserve`). Each file is then written to a per-process temporary
name and moved into place with ``os.replace``, so a reader never sees a
half-written one. The append-only digest is the single shared file, guarded by a
lock and written one whole line at a time.

**Paths are ``pathlib`` throughout.** The default lives beside the repository
rather than the working directory, because a service started from elsewhere
should still log to the same place.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import threading
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

#: One warning per process. A trace that cannot be written is worth knowing
#: about; a trace that cannot be written on every query is worth knowing about
#: once.
_warned = False
_summary_lock = threading.Lock()

#: The repository root: app/observability/retrieval_log/sink.py -> up four.
_ROOT = pathlib.Path(__file__).resolve().parents[3]


def log_root() -> pathlib.Path:
    """The configured log directory, or ``<repo>/logs`` when none is set."""
    configured = (get_settings().retrieval_log_dir or "").strip()
    if configured:
        return pathlib.Path(configured).expanduser()
    return _ROOT / "logs"


def _warn(message: str) -> None:
    global _warned
    if _warned:
        logger.debug(message, exc_info=True)
        return
    _warned = True
    logger.warning(
        "%s Retrieval logging is best-effort; the query itself is unaffected. "
        "Further failures are logged at DEBUG.",
        message,
        exc_info=True,
    )


def _atomic_write(path: pathlib.Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically.

    The temporary name carries the pid and thread id so two writers cannot
    collide on it even when they are writing the same directory.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


#: How many times a name is nudged before falling back to the request id. Two
#: identical questions in the same second is plausible (a retry, a load test);
#: fifty is not, and an unbounded loop on a filesystem that keeps saying "exists"
#: would hang the request thread.
_MAX_NAME_ATTEMPTS = 50


def _reserve(parent: pathlib.Path, name: str, request_id: str) -> pathlib.Path:
    """Create a directory called ``name`` under ``parent``, or the next free
    variant of it, and return it.

    ``mkdir`` without ``exist_ok`` is the whole mechanism: creation is atomic, so
    the process that creates the directory owns it and a loser simply tries the
    next name. That is what keeps two concurrent queries with the *same*
    question and the same second from writing into one directory — the folder
    name is for reading and makes no promise of uniqueness, so uniqueness is
    enforced here instead.
    """
    parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(_MAX_NAME_ATTEMPTS):
        candidate = parent / (name if attempt == 0 else f"{name} ({attempt + 1})")
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    # Fifty collisions means the name is not discriminating; the request id
    # always is.
    final = parent / f"{name} ({request_id[:8]})"
    final.mkdir(exist_ok=True)
    return final


def _dump(
    parent: pathlib.Path,
    name: str,
    request_id: str,
    payload: dict[str, Any],
    report: str | None,
) -> pathlib.Path:
    """Write one query's directory: the record, and the explanation beside it."""
    directory = _reserve(parent, name, request_id)
    _atomic_write(
        directory / "trace.json",
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
    )
    if report:
        _atomic_write(directory / "report.md", report)
    return directory


def write(log: Any) -> pathlib.Path | None:
    """Persist one finished :class:`~.models.QueryLog`. Returns its directory, or None.

    Never raises: this runs in a ``finally`` on the request path, where an
    exception would replace the user's answer with a logging error.
    """
    try:
        payload = log.to_dict()
    except Exception:
        _warn("Could not serialize a retrieval trace.")
        return None

    # The report is rendered from the payload, so the two files describe exactly
    # the same record — and a failure to render one costs only the prose.
    report: str | None = None
    if get_settings().retrieval_log_report:
        try:
            from app.observability.retrieval_log import markdown

            report = markdown.render(payload)
        except Exception:
            _warn("Could not render the report for a retrieval trace.")

    root = None
    path = None
    name = f"query_{log.request_id}"
    try:
        root = log_root()
        name = log.folder
        path = _dump(root / log.day, name, log.request_id, payload, report)
    except Exception:
        _warn("Could not write a retrieval trace.")
        path = None

    if root is not None and log.failed:
        try:
            _dump(root / "errors" / log.day, name, log.request_id, payload, report)
        except Exception:
            _warn("Could not write the errors/ copy of a retrieval trace.")

    if root is not None and get_settings().retrieval_log_summary:
        try:
            _append_summary(root, log)
        except Exception:
            _warn("Could not append to the retrieval-log summary.")
    return path


def _append_summary(root: pathlib.Path, log: Any) -> None:
    """Add one line to the day's digest.

    Append mode plus a whole line per write, under a lock: a reader (or pandas)
    sees complete lines only, and concurrent queries queue rather than interleave.
    """
    line = json.dumps(log.summary(), ensure_ascii=False, default=str)
    target = root / "summary" / f"{log.day}.jsonl"
    with _summary_lock:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
