"""The knowledge layer: canonical entities, source-level claims, and the graph.

Deliberately a new package rather than an extension of an existing one. Two
names in this codebase already mean something else:

* ``app.retrieval.structured.entities`` — an "entity" there is a Drupal content
  *bundle* (news, people), not a real-world entity.
* ``app.generation.faithfulness._Claim`` — an *answer*-level statement checked
  against its citations, unrelated to a source-level assertion extracted from
  the corpus.

To keep those apart, the Python type for a source-level assertion is
``Assertion``; ``Claim`` is used only as the Neo4j node label, where there is no
collision.
"""
