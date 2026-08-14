"""The assertion model, and the identity design behind ``claim_id``.

Claim identity — the part worth arguing about
---------------------------------------------
An earlier sketch hashed ``valid_from`` and ``valid_until`` into the id. That is
wrong here, and the reason is worth stating because it is easy to re-introduce.

Those fields are **model-derived interpretation**. Re-extracting the same
sentence with a better prompt can legitimately read "since 2019" where it
previously read nothing, and if validity is part of the identity the result is a
*second* claim asserting the same thing from the same evidence. The store then
holds two rows that no later pass can tell apart from two genuinely different
assertions. Retries stop being safe, which is the one property the deterministic
id exists to provide.

So identity is what the **source states**, and nothing about how it was read:

    claim_id = sha256( evidence_key | subject_id | predicate | object_key )

``evidence_key``  the chunk the assertion was read from, or the document and
                  field for a CMS-derived one. Two chunks asserting the same
                  fact deliberately produce two claims — they are independent
                  evidence, and collapsing them would lose a corroboration.
``object_key``    ``entity:<id>`` or ``literal:<normalized>``, so an entity
                  object and a literal that happen to share a string can never
                  collide.

Everything mutable is *state on* the claim, never part of it: validity, temporal
basis, confidence, status, the quote and its offsets, the extracting model and
version. Re-extraction therefore updates a row rather than forking it, and a
change of prompt is visible as a changed field rather than as a duplicate.

Evidence
--------
Two kinds, and both point at something real:

``chunk``      a chunk id, a verbatim quote, and chunk-relative offsets. The
               quote must appear at those offsets in the stored chunk text.
``cms_field``  a document id and the metadata field that stated it. No quote:
               there is no prose to quote, and inventing one would be worse than
               admitting the evidence is structural.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.knowledge.claims import predicates as vocab

# How an assertion was produced. Ordered by how much is being trusted.
EXTRACTION_METHODS = ("cms_field", "pattern", "llm")

# Where the evidence lives.
EVIDENCE_CHUNK = "chunk"
EVIDENCE_CMS_FIELD = "cms_field"
EVIDENCE_KINDS = (EVIDENCE_CHUNK, EVIDENCE_CMS_FIELD)

# Lifecycle state. Only `active` claims are eligible for later projection;
# nothing is ever deleted, so history survives a contradiction.
STATUS_ACTIVE = "active"
STATUS_SUPERSEDED = "superseded"
STATUS_DISPUTED = "disputed"
STATUS_RETRACTED = "retracted"
STATUSES = (STATUS_ACTIVE, STATUS_SUPERSEDED, STATUS_DISPUTED, STATUS_RETRACTED)

# How a validity window was established. `stated` means the text said so;
# `document` means it was inferred from the document's date and is deliberately
# recorded as the weaker basis rather than being silently upgraded.
BASIS_STATED = "stated"
BASIS_DOCUMENT = "document"
BASIS_UNKNOWN = "unknown"
TEMPORAL_BASES = (BASIS_STATED, BASIS_DOCUMENT, BASIS_UNKNOWN)

# Dates outside this range are extraction noise rather than facts about the
# world. Mirrors the bounds app.ingestion.date_llm already enforces.
MIN_YEAR = 1900
MAX_YEAR = date.today().year + 5

# A quote has to be long enough to be evidence and short enough not to be the
# whole chunk restated.
MIN_QUOTE_CHARS = 10
MAX_QUOTE_CHARS = 600

_WHITESPACE = re.compile(r"\s+")


def normalize_literal(value: str) -> str:
    """Fold a literal object for identity purposes only."""
    return _WHITESPACE.sub(" ", (value or "").strip()).casefold()


def object_key(object_entity_id: str | None, object_literal: str | None) -> str:
    """The object's contribution to claim identity.

    Prefixed by kind so an entity id and a literal that happen to share a string
    can never produce the same key.
    """
    if object_entity_id:
        return f"entity:{object_entity_id}"
    return f"literal:{normalize_literal(object_literal or '')}"


def evidence_key(
    *, evidence_kind: str, chunk_id: str | None,
    document_id: str, source_field: str | None,
) -> str:
    """The evidence's contribution to claim identity.

    Chunk-scoped for extracted claims, so re-reading the same chunk is the same
    claim. Document-and-field-scoped for CMS claims, because there is no chunk
    and the field is what makes two metadata facts about one document distinct.
    """
    if evidence_kind == EVIDENCE_CHUNK:
        return f"chunk:{chunk_id}"
    return f"cms:{document_id}:{source_field or ''}"


def make_claim_id(
    *, evidence: str, subject_entity_id: str, predicate: str, obj: str
) -> str:
    """The deterministic identity. See the module docstring for what is
    deliberately *not* in it."""
    joined = "\x1f".join((evidence, subject_entity_id, predicate, obj))
    return "claim_" + hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]


@dataclass
class Assertion:
    """One thing the corpus says, with where it says it.

    Constructed only through :func:`build`, which computes the id, so an
    assertion cannot exist with an identity that disagrees with its content.
    """

    # --- identity inputs (stable) ---
    subject_entity_id: str
    predicate: str
    document_id: str
    evidence_kind: str = EVIDENCE_CHUNK
    object_entity_id: str | None = None
    object_literal: str | None = None
    chunk_id: str | None = None
    source_field: str | None = None

    # --- evidence (mutable; re-extraction may improve it) ---
    quote: str | None = None
    quote_start: int | None = None
    quote_end: int | None = None

    # --- interpretation (mutable) ---
    valid_from: str | None = None
    valid_until: str | None = None
    temporal_basis: str = BASIS_UNKNOWN
    confidence: float = 0.0
    status: str = STATUS_ACTIVE

    # --- provenance of the extraction itself ---
    extraction_method: str = "cms_field"
    extractor_version: str = ""
    vocabulary_version: str = vocab.VOCABULARY_VERSION
    model: str | None = None
    prompt_version: str | None = None

    claim_id: str = ""
    notes: dict[str, Any] = field(default_factory=dict)

    @property
    def object_is_entity(self) -> bool:
        return self.object_entity_id is not None

    def recompute_id(self) -> str:
        self.claim_id = make_claim_id(
            evidence=evidence_key(
                evidence_kind=self.evidence_kind, chunk_id=self.chunk_id,
                document_id=self.document_id, source_field=self.source_field,
            ),
            subject_entity_id=self.subject_entity_id,
            predicate=self.predicate,
            obj=object_key(self.object_entity_id, self.object_literal),
        )
        return self.claim_id


def build(**kwargs: Any) -> Assertion:
    """Create an assertion with its identity computed."""
    assertion = Assertion(**kwargs)
    assertion.recompute_id()
    return assertion
