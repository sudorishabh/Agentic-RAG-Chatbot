"""Shared domain models.

Cross-boundary data contracts that more than one feature package depends on:
the canonical document produced by ingestion, and the context block passed from
retrieval to generation. Feature-internal models (e.g. ``Candidate``,
``ProcessedQuery``) stay in their owning package.
"""
from app.core.models.context import ContextBlock
from app.core.models.document import (
    CanonicalDocument,
    CanonicalSection,
    EntityRef,
    FileLink,
)

__all__ = [
    "CanonicalDocument",
    "CanonicalSection",
    "EntityRef",
    "FileLink",
    "ContextBlock",
]
