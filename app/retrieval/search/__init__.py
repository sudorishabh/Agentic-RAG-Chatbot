"""Candidate search: fetch a candidate set from Qdrant and order it.

One cluster rather than separate "fetch" and "rank" packages, because
:class:`.hybrid_search.Candidate` is the type every module here passes around —
splitting them would put that type on one side of a boundary and half its users
on the other.

Reading order, cheapest first:

* :mod:`.hybrid_search` — the primitive: ``Candidate``, ``build_filter``,
  ``search``. Everything else in this package sits on top of it.
* :mod:`.fusion` — reciprocal-rank fusion across legs.
* :mod:`.strategies` — recall expansion over the primitive: website-biased dual
  pull, keyword full-text leg, multi-query paraphrasing, one-shot corrective
  requery.
* :mod:`.scoped_retrieval` — search restricted to named documents.
* :mod:`.title_leg` — the title-anchored leg, for pages whose text is a list of
  link labels no embedding matches.
* :mod:`.reranker` — cross-encoder / heuristic reordering and the authority,
  recency and substance bands.
* :mod:`.volatility` — whether a question's answer decays with time (read by the
  reranker's recency band).
* :mod:`.temporal_gate` — drops candidates a temporal question excludes.
"""
