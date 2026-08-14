"""Source-level claims: what the corpus *says* about entities.

The Python type is ``Assertion``, not ``Claim``. Two other things in this
codebase already own that word: ``app.generation.faithfulness._Claim`` is an
*answer*-level statement checked against its citations, and ``Claim`` is
reserved for the Neo4j node label. Keeping the names apart stops three unrelated
ideas colliding in review.

This package stages assertions in MySQL and nothing more. Projection to Neo4j,
current-state relationships and graph retrieval are later phases; an assertion
staged here is durable and re-projectable, so nothing is lost by them not
existing yet.
"""
