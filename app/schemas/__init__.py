"""HTTP wire contracts: the request and response bodies of the API.

Pydantic models, one module per router (:mod:`.query` for the retrieval API,
:mod:`.ingest` for the ingestion control plane). They exist to validate and
serialise what crosses the network boundary, and nothing below :mod:`app.api`
should import them.

**Not to be confused with :mod:`app.core.models`.** The distinction is which
boundary the type describes:

* ``app.schemas`` — the *external* boundary. Pydantic, versioned by the API's
  compatibility promises, shaped for JSON. Changing one is a public change.
* ``app.core.models`` — *internal* contracts shared between packages
  (``CanonicalDocument``, ``ContextBlock``). Plain dataclasses, shaped for the
  code that passes them around. Changing one is an internal refactor.

A type that is both — sent over the wire *and* passed between layers — is a sign
the two boundaries have been conflated; give each side its own model and convert
at the router.
"""
from app.schemas.ingest import (
    ArticleIngestRequest,
    ArticleIngestResponse,
    ReindexRequest,
    ReindexResponse,
)
from app.schemas.query import (
    ChatTurn,
    Citation,
    DetectedIntent,
    QueryRequest,
    SearchBlock,
    SearchRequest,
    SearchResponse,
)

__all__ = [
    "ArticleIngestRequest",
    "ArticleIngestResponse",
    "ReindexRequest",
    "ReindexResponse",
    "ChatTurn",
    "Citation",
    "DetectedIntent",
    "QueryRequest",
    "SearchBlock",
    "SearchRequest",
    "SearchResponse",
]
