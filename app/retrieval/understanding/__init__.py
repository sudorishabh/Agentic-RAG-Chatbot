"""Query understanding: a question -> what to retrieve and how to filter it.

The first stage of the read path. Nothing here touches Qdrant.

* :mod:`.query_processor` — the entry point and the data contracts
  (``QueryAnalysis``, ``QueryUnderstanding``): the LLM call, sample voting/merge
  and the legacy derivation.
* :mod:`.prompts` — the understanding prompt text, split out to keep
  ``query_processor`` focused on control flow.
* :mod:`.filters` — turns an analysis into a Qdrant facet filter.
* :mod:`.relational` — relational/comparative question shapes.
* :mod:`.approved_aliases` — vetted surface forms for entities the corpus names
  inconsistently.
* :mod:`.annual_report_editions` — which edition of a recurring series a
  question means.
* :mod:`.catalog_prompt` — the corpus description (bundles, themes) injected
  into understanding and structured planning prompts.
"""
