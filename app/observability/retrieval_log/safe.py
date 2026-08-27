"""Turning arbitrary runtime objects into JSON that is safe to keep.

Two jobs, and they are separate on purpose:

* **Serializable.** A trace holds Qdrant filters (pydantic models), MySQL rows
  (``datetime``, ``Decimal``), dataclasses and whatever a driver hands back.
  :func:`jsonable` reduces all of it to JSON primitives and never raises — a
  value it cannot convert becomes its ``repr``, because a trace with one ugly
  field is worth more than no trace.

* **Safe.** Nothing here may write a credential to disk. Redaction is by *key*
  rather than by value: a mapping key that looks like a secret has its value
  replaced, whatever the value is. That is deliberately blunt — the cost of
  redacting a harmless field named ``token`` is a missing debug detail, and the
  cost of the reverse is a password in a log file.

Bounded as well as safe: every string is clipped and every container is capped,
so one pathological document cannot turn a trace into a megabyte of JSON.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time as _time
from decimal import Decimal
from typing import Any

REDACTED = "***redacted***"
TRUNCATION_MARKER = "…[truncated]"

#: A mapping key whose *value* is replaced with :data:`REDACTED`. Substring
#: match, case-insensitive: ``azure_openai_api_key``, ``NEO4J_PASSWORD`` and
#: ``Authorization`` all have to be caught, and none of them is spelled the
#: same way twice across the drivers this passes through.
_SECRET_KEY = re.compile(
    r"pass|secret|token|api[_-]?key|apikey|credential|auth|bearer|cookie"
    r"|session[_-]?id|private[_-]?key|signature|dsn|connection[_-]?string",
    re.IGNORECASE,
)

#: How deep a structure is followed before it is summarized. Payloads are flat;
#: a filter tree is two or three levels. Ten is generous and terminates.
_MAX_DEPTH = 10

#: Cap on a mapping's keys and a sequence's items at any one level, so an
#: unexpected shape cannot become an unbounded write.
_MAX_KEYS = 200
_MAX_ITEMS = 200


def is_secret_key(key: str) -> bool:
    return bool(_SECRET_KEY.search(key))


def clip(value: Any, limit: int) -> str:
    """``value`` as a string of at most ``limit`` characters, marked if cut."""
    text = value if isinstance(value, str) else str(value)
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit] + TRUNCATION_MARKER


def jsonable(value: Any, *, limit: int = 2000, _depth: int = 0) -> Any:
    """``value`` reduced to JSON primitives, redacted and bounded. Never raises."""
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        # inf/nan are not JSON; keep them readable rather than crashing the dump.
        return value if -1e308 < value < 1e308 else str(value)
    if isinstance(value, str):
        return clip(value, limit)
    if isinstance(value, (datetime, date, _time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<{len(bytes(value))} bytes>"
    if _depth >= _MAX_DEPTH:
        return clip(repr(value), limit)

    # pydantic models (Qdrant filters, LLM schemas) and dataclasses describe
    # themselves; ask them before falling back to repr.
    dumped = _dump(value)
    if dumped is not None:
        return jsonable(dumped, limit=limit, _depth=_depth + 1)

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for i, (key, item) in enumerate(value.items()):
            if i >= _MAX_KEYS:
                out["…"] = f"{len(value) - _MAX_KEYS} more key(s)"
                break
            name = key if isinstance(key, str) else clip(repr(key), 80)
            out[name] = (
                REDACTED
                if is_secret_key(name)
                else jsonable(item, limit=limit, _depth=_depth + 1)
            )
        return out
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)
        cut = items[:_MAX_ITEMS]
        converted = [jsonable(v, limit=limit, _depth=_depth + 1) for v in cut]
        if len(items) > _MAX_ITEMS:
            converted.append(f"…{len(items) - _MAX_ITEMS} more item(s)")
        return converted
    return clip(repr(value), limit)


def _dump(value: Any) -> Any | None:
    """``value`` as a plain container if it knows how to describe itself."""
    for attr in ("model_dump", "dict", "_asdict"):
        method = getattr(value, attr, None)
        if callable(method):
            try:
                return method(exclude_none=True) if attr == "model_dump" else method()
            except Exception:
                try:
                    return method()
                except Exception:
                    return None
    if hasattr(value, "__dataclass_fields__"):
        try:
            return {f: getattr(value, f) for f in value.__dataclass_fields__}
        except Exception:
            return None
    return None
