"""Turn anything the pipeline hands us into JSON-safe structures, losslessly
where it matters (text, ids, payloads) and summarised only for raw bytes and
vectors."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any


def to_jsonable(value: Any, _depth: int = 0) -> Any:
    if _depth > 12:
        return repr(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): to_jsonable(v, _depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_jsonable(v, _depth + 1) for v in value]
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: to_jsonable(getattr(value, f.name), _depth + 1)
            for f in dataclasses.fields(value)
        }
    if hasattr(value, "__dict__"):
        return {
            k: to_jsonable(v, _depth + 1)
            for k, v in vars(value).items()
            if not k.startswith("_")
        }
    return repr(value)


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_jsonable(value), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def vector_summary(vector: Any) -> dict[str, Any] | None:
    """Dimension, norm and a fingerprint; never the 3072 floats themselves."""
    if not isinstance(vector, list) or not vector:
        return None
    norm = sum(float(x) * float(x) for x in vector) ** 0.5
    digest = hashlib.sha256(
        ",".join(f"{float(x):.6f}" for x in vector).encode("utf-8")
    ).hexdigest()
    return {
        "dim": len(vector),
        "l2_norm": round(norm, 6),
        "is_zero": norm == 0.0,
        "sha256_of_rounded": digest,
        "head": [round(float(x), 6) for x in vector[:6]],
    }
