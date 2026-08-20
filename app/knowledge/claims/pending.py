"""Pending relationship candidates: predicates the vocabulary cannot express.

Named ``pending`` rather than ``candidates`` because ``app.knowledge.candidates``
already means something else — the shortlist of canonical entities a *mention*
might denote. These are proposals about a *predicate*, and keeping the words
apart stops two unrelated ideas colliding in review.

Why this exists
---------------
The vocabulary in :mod:`app.knowledge.claims.predicates` is closed on purpose: a
model that can invent a relationship type can assert anything. That decision is
right and is not revisited here. But it had a side effect worth fixing — the
evidence was destroyed twice over. :mod:`app.knowledge.claims.extract_llm`
dropped an out-of-vocabulary proposal before it was ever recorded, and
:mod:`app.knowledge.claims.validate` rejected it with a code and no quote. So
the one question the vocabulary needs answered — *what relationship does this
corpus keep asserting that we cannot express?* — had no data behind it.

A candidate is evidence and nothing else
----------------------------------------
It is not a claim, it is not an edge, and no runtime path can turn it into
either:

* it is never staged, so :mod:`app.catalog.assertions` never sees it;
* it is never projected, and could not be — ``writer.safe_relationship``
  raises for any type outside the closed vocabulary;
* ``promoted`` status is set by a human *after* adding a ``Predicate`` to
  ``predicates.py`` and bumping ``VOCABULARY_VERSION``. Nothing here writes it.

It still carries the same verified quote a claim would, located by the same
:func:`app.knowledge.claims.validate.locate_quote`, so a reviewer reads the
sentence that proposed it rather than a bare predicate name. A proposal whose
quote is not in the chunk verbatim is discarded exactly as a claim's would be —
being unusable as a claim does not make fabricated evidence acceptable.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Sequence

from app.knowledge.claims import predicates as vocab
from app.knowledge.claims import types as t

logger = logging.getLogger(__name__)

# Lifecycle. `promoted` and `rejected` are operator verdicts; runtime only ever
# writes `pending`.
STATUS_PENDING = "pending"
STATUS_PROMOTED = "promoted"
STATUS_REJECTED = "rejected"
CANDIDATE_STATUSES = (STATUS_PENDING, STATUS_PROMOTED, STATUS_REJECTED)

# A surface longer than this is a sentence, not a relationship name.
MAX_SURFACE_CHARS = 128

_NON_WORD = re.compile(r"[^A-Za-z0-9]+")


def normalize_predicate(surface: str) -> str:
    """Fold a proposed predicate to the shape the vocabulary uses.

    ``collaborated with`` / ``Collaborated-With`` / ``COLLABORATED_WITH`` are one
    candidate, not three. Grouping is the whole value of this table, so the fold
    happens before identity is computed rather than in a reporting query.
    """
    folded = _NON_WORD.sub("_", (surface or "").strip()).strip("_").upper()
    return folded[:MAX_SURFACE_CHARS]


def make_candidate_id(
    *, evidence: str, subject_entity_id: str, predicate: str, obj: str
) -> str:
    """Deterministic identity, built by the same construction as ``claim_id``.

    Reused rather than reinvented so the argument in
    :mod:`app.knowledge.claims.types` holds here unchanged: identity is what the
    source states — this evidence, this subject, this predicate, this object —
    and everything mutable is state on the row. A retry therefore upserts, and
    a second reading of the same sentence is the same candidate.
    """
    return "cand_" + t.make_claim_id(
        evidence=evidence, subject_entity_id=subject_entity_id,
        predicate=predicate, obj=obj,
    )[len("claim_"):]


@dataclass
class PredicateCandidate:
    """One proposal for a relationship the vocabulary does not contain."""

    predicate_surface: str
    predicate_normalized: str
    subject_entity_id: str
    document_id: str
    evidence_kind: str = t.EVIDENCE_CHUNK
    object_entity_id: str | None = None
    object_literal: str | None = None
    chunk_id: str | None = None
    quote: str | None = None
    quote_start: int | None = None
    quote_end: int | None = None
    confidence: float = 0.0
    extraction_method: str = "llm"
    extractor_version: str = ""
    vocabulary_version: str = vocab.VOCABULARY_VERSION
    model: str | None = None
    prompt_version: str | None = None
    status: str = STATUS_PENDING
    candidate_id: str = ""

    def recompute_id(self) -> str:
        self.candidate_id = make_candidate_id(
            evidence=t.evidence_key(
                evidence_kind=self.evidence_kind, chunk_id=self.chunk_id,
                document_id=self.document_id, source_field=None,
            ),
            subject_entity_id=self.subject_entity_id,
            predicate=self.predicate_normalized,
            obj=t.object_key(self.object_entity_id, self.object_literal),
        )
        return self.candidate_id


def build(
    *, predicate_surface: str, subject_entity_id: str, document_id: str,
    chunk_id: str | None, chunk_text: str, quote: str | None,
    object_entity_id: str | None = None, object_literal: str | None = None,
    confidence: float = 0.0, extraction_method: str = "llm",
    extractor_version: str = "", model: str | None = None,
    prompt_version: str | None = None,
) -> PredicateCandidate | None:
    """A candidate, or None when the proposal is not worth recording.

    Refused, and each refusal is the same rule a claim would face:

    * an empty or unusable predicate surface — there is nothing to group on;
    * a predicate that is **already in the vocabulary** — that is a claim, and
      routing it here would hide a validation failure as a discovery;
    * no subject — an unanchored relationship string is not evidence of a
      relationship, only of a phrase;
    * a quote that is not in the chunk verbatim. Offsets are recomputed here
      from the located text and whatever the model reported is discarded, which
      is the same treatment :mod:`app.knowledge.claims.validate` gives a claim.
    """
    from app.knowledge.claims.validate import locate_quote

    normalized = normalize_predicate(predicate_surface)
    if not normalized or vocab.is_known(normalized):
        return None
    if not subject_entity_id or not document_id:
        return None

    candidate = PredicateCandidate(
        predicate_surface=(predicate_surface or "")[:MAX_SURFACE_CHARS],
        predicate_normalized=normalized,
        subject_entity_id=subject_entity_id,
        document_id=document_id,
        chunk_id=chunk_id,
        evidence_kind=t.EVIDENCE_CHUNK if chunk_id else t.EVIDENCE_CMS_FIELD,
        object_entity_id=object_entity_id or None,
        object_literal=(object_literal or None),
        confidence=max(0.0, min(1.0, float(confidence or 0.0))),
        extraction_method=extraction_method,
        extractor_version=extractor_version,
        model=model,
        prompt_version=prompt_version,
    )

    if candidate.evidence_kind == t.EVIDENCE_CHUNK:
        text = (quote or "").strip()
        if not (t.MIN_QUOTE_CHARS <= len(text) <= t.MAX_QUOTE_CHARS):
            return None
        located = locate_quote(chunk_text or "", text)
        if located is None:
            return None
        start, end = located
        candidate.quote = chunk_text[start:end]
        candidate.quote_start, candidate.quote_end = start, end
        if candidate.object_literal:
            candidate.object_literal = candidate.object_literal[:255]

    candidate.recompute_id()
    return candidate


def dedupe(candidates: Sequence[PredicateCandidate]) -> list[PredicateCandidate]:
    """One candidate per id, keeping the most confident."""
    best: dict[str, PredicateCandidate] = {}
    for candidate in candidates:
        current = best.get(candidate.candidate_id)
        if current is None or candidate.confidence > current.confidence:
            best[candidate.candidate_id] = candidate
    return sorted(best.values(), key=lambda c: c.candidate_id)


def summarize(candidates: Sequence[Any]) -> dict[str, int]:
    """Proposals per normalized predicate — what a vocabulary review reads."""
    out: dict[str, int] = {}
    for candidate in candidates:
        name = getattr(candidate, "predicate_normalized", None) or "?"
        out[name] = out.get(name, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))
