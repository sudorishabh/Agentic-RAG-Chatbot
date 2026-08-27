"""What the corpus is made of: the content types both paths have to agree about.

This exists for the same reason :mod:`app.core.editions` does. The bundle list is
*ingestion's* configuration — it decides what to crawl — but the read path needs
the identical list for three different jobs:

* :mod:`app.retrieval.understanding.catalog_prompt` describes the corpus to the
  model, and a bundle missing from that description is a bundle the model will
  not ask for;
* :mod:`app.retrieval.structured.entities` registers one queryable entity per
  bundle, so the structured planner can count and list them;
* :mod:`app.pipeline.summarize` decides whether a scope name is a bundle.

Those three used to import ``DEFAULT_BUNDLES`` from
``app.ingestion.extractors.drupal_extractor`` — the read path reaching into a
write-path *extractor* for a list of names. That is backwards, and it is the kind
of import that quietly makes retrieval depend on how the crawler happens to be
implemented.

So the vocabulary lives in the neutral core layer and both paths read it from
here. Ingestion still owns the *decision* of what to crawl: it re-exports this
list under its own name and adds the crawl-only settings (block types, the
searchable-entity allowlist) that no reader has any use for.
"""
from __future__ import annotations

__all__ = ["DEFAULT_BUNDLES"]

#: The Drupal node bundles that make up the corpus.
#:
#: ``carousel`` is deliberately absent: those nodes are homepage promo slides
#: carrying a title and no body, so they chunk to nothing, and both of the live
#: ones name subjects already covered by real news and event content.
#:
#: This is the list ingestion *attempts*. A bundle that exists here but has no
#: rows in a given deployment is a bundle that was configured and never
#: populated, which is why the read path checks it against the catalog rather
#: than trusting it (see ``catalog_prompt.describe_corpus``).
DEFAULT_BUNDLES: tuple[str, ...] = (
    "article",
    "page",
    "research_papers",
    "completed_projects",
    "feature_articles",
    "ongoing_projects",
    "news",
    "events",
    "press_release",
    "policy_brief",
    "videos",
    "infographics",
    "services",
    "report",
    "people",
)
