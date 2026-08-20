"""What the knowledge layer was, when it processed a document.

The counterpart of :mod:`app.ingestion.version`, and it exists for the same
reason. Each stage already carries its own version constant — ``EXTRACTOR_VERSION``,
``RESOLVER_VERSION``, ``VOCABULARY_VERSION``, ``DETECTOR_VERSION`` — and each is
recorded on the rows that stage writes, so a single row can be traced to the
rules that produced it. What no row could answer was the question an operator
actually asks after changing a rule:

    which documents were processed under which knowledge rules?

That needs one value per document, covering every version that materially
changes what the layer would produce. This module composes it.

Deliberately **not** claim identity
-----------------------------------
``claim_id`` covers what the source states and nothing about how it was read
(see :mod:`app.knowledge.claims.types`). Folding a rules fingerprint into it
would fork every claim on every rule change, which is precisely the failure that
module's identity design exists to prevent. This fingerprint is state *on* a
run, never part of anything's identity.

Composition
-----------
Hashed rather than concatenated because the parts total well over the column's
128 characters, and a truncated fingerprint would silently collide. The
component list is kept readable through :func:`components`, so "what changed?"
is answerable without reversing a hash.
"""
from __future__ import annotations

import hashlib
from typing import Any

#: Bumped when the *composition* changes — a component added or removed — so an
#: old fingerprint is not mistaken for a new one computed differently.
FINGERPRINT_VERSION = "kv1"


def components(*, gazetteer_fingerprint: str | None = None) -> dict[str, str]:
    """Every version that materially affects what the knowledge layer produces.

    ``gazetteer_fingerprint`` is passed in rather than computed here: building
    the gazetteer is expensive and a caller that skipped mention extraction has
    no reason to pay for it. Absent, it is recorded as ``"-"``, which is honest
    — that run's output did not depend on the name index.
    """
    from app.knowledge.claims import predicates as vocab
    from app.knowledge.claims import conflicts as cf
    from app.knowledge.claims import extract_cms, extract_llm
    from app.knowledge.extract import EXTRACTOR_VERSION as ENTITY_EXTRACTOR
    from app.knowledge.graph.project import PROJECTOR_VERSION
    from app.knowledge.resolver import RESOLVER_VERSION

    return {
        "entity_extract": ENTITY_EXTRACTOR,
        "resolver": RESOLVER_VERSION,
        "claims_cms": extract_cms.EXTRACTOR_VERSION,
        "claims_llm": extract_llm.EXTRACTOR_VERSION,
        "vocabulary": vocab.VOCABULARY_VERSION,
        "conflicts": cf.DETECTOR_VERSION,
        "projector": PROJECTOR_VERSION,
        "gazetteer": gazetteer_fingerprint or "-",
    }


def knowledge_version(*, gazetteer_fingerprint: str | None = None) -> str:
    """The one-value fingerprint stored on a knowledge run."""
    parts = components(gazetteer_fingerprint=gazetteer_fingerprint)
    joined = "\x1f".join(f"{k}={v}" for k, v in sorted(parts.items()))
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]
    return f"{FINGERPRINT_VERSION}:{digest}"


def describe(*, gazetteer_fingerprint: str | None = None) -> dict[str, Any]:
    """The fingerprint and the components behind it, for an operator view."""
    return {
        "knowledge_version": knowledge_version(
            gazetteer_fingerprint=gazetteer_fingerprint
        ),
        "components": components(gazetteer_fingerprint=gazetteer_fingerprint),
    }


__all__ = ["FINGERPRINT_VERSION", "components", "knowledge_version", "describe"]
