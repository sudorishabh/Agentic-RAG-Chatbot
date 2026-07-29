"""Shared text for the three prompts that describe the document catalog's
database slots to an LLM: the intent classifier
(`app.retrieval.understanding.prompts`), the slot-extraction fallback
(`app.retrieval.structured.answerer`), and the v2 tool-calling planner
(`app.retrieval.structured.planner`). Kept in one place so the bundle list, the
vocabulary mapping, and the collective-word warning don't drift across three
independently-edited strings, each previously hand-duplicating its own version.

Each block is a self-contained sentence/paragraph meant to be appended as its
own line wherever it applies — not designed to be spliced mid-sentence. See
docs/database-retrieval-redesign.md §10.
"""

from __future__ import annotations

from app.ingestion.extractors.drupal_extractor import DEFAULT_BUNDLES

BUNDLE_LIST = ", ".join(DEFAULT_BUNDLES)

VOCABULARY = (
    "Vocabulary: \"articles\", \"items\", \"stories\", \"pieces\", and \"entries\" "
    "all mean a catalog record in general — none of them names a specific content "
    "type. A bundle's own name (e.g. \"events\", \"reports\", \"press releases\") "
    "does name one; users never say the word \"bundle\" itself."
)

COLLECTIVE_WORD_WARNING = (
    "A generic collective word (\"publications\", \"works\", \"output\", "
    "\"everything\") means every content type, not one — leave the content type "
    "null for these rather than collapsing onto a single bundle (do not map "
    "\"publications\" to research_papers)."
)

# resolve_entity is not advertised for tags — see
# docs/database-retrieval-redesign.md §3/§4.1: a dev-DB sample found ~237
# freeform tag terms over ~224 tagged documents, the shape of long-tail CMS
# tagging rather than a curated vocabulary fuzzy matching could usefully rank.
RESOLVE_FIRST = (
    "Resolve first: before filtering by author, bundle, or theme, call "
    "resolve_entity if the name is a proper noun, a partial name, or possibly "
    "misspelled (\"rishab negi\", \"climate\", \"env theme\"). Skip it for an "
    "exact, already-known bundle name and for a date-only or tag-only filter — "
    "a tag is set directly and is never resolved through resolve_entity."
)

OPERATIONS = (
    "count_records answers \"how many\" of one thing. aggregate_records answers "
    "\"how many per X\" or \"which X does Y appear in\" — always ONE call, never "
    "one call per value. list_records is for when the user wants to see rows or "
    "metadata, not just a number."
)

BEHAVIOR = (
    "Themes: a specific theme is a normal filter; \"how many themes are there?\" "
    "means list_themes, which lists Main themes first and Other themes in a "
    "separate section.\n"
    "Ambiguity: if resolve_entity returns more than one close match, ask the "
    "user to pick — never silently choose the top candidate.\n"
    "No fabrication: if a filter does not resolve to anything, say so explicitly "
    "(e.g. \"no author matching 'X' found\") rather than treating it as zero.\n"
    "Always name the resolved entities in the final answer, so the user can "
    "catch a wrong match."
)

FEW_SHOTS = (
    "Examples (the tool call sequence, not just the answer):\n"
    "1. \"How many posts are there from Rishabh Negi?\" -> "
    "resolve_entity(\"Rishabh Negi\", \"author\") -> count_records(filters={author}).\n"
    "2. \"How many events are there?\" -> count_records(entity=\"events\") — "
    "exact bundle name, no resolve step.\n"
    "3. \"How many themes are there?\" -> list_themes().\n"
    "4. \"How many events are under Climate Change?\" -> "
    "resolve_entity(\"Climate Change\", \"theme\") -> "
    "count_records(entity=\"events\", filters={theme}).\n"
    "5. \"How many posts from Rishabh Negi under Environment?\" -> two "
    "resolve_entity calls (author, theme) -> one count_records.\n"
    "6. \"Which bundles does Rishabh Negi post in?\" -> "
    "resolve_entity(\"Rishabh Negi\", \"author\") -> "
    "aggregate_records(group_by=\"content_type\", filters={author}).\n"
    "7. \"Latest 5 reports under Climate Change with their source links\" -> "
    "resolve_entity(\"Climate Change\", \"theme\") -> "
    "list_records(entity=\"report\", limit=5, filters={theme}).\n"
    "8. \"How many posts are tagged 'policy'?\" -> "
    "count_records(filters={tag=\"policy\"}) — no resolve step; an unresolved "
    "tag is a terminal miss, not a guess.\n"
    "Ambiguous: \"how many posts by rishab?\" -> resolve_entity(\"rishab\", "
    "\"author\") returns two close matches (Rishabh Negi, Rishab Nigam) -> ask "
    "which one, do not guess.\n"
    "Miss: \"posts by Zzz\" -> resolve_entity(\"Zzz\", \"author\") finds nothing "
    "-> answer \"no author matching 'Zzz' found\", not a fallback count."
)
