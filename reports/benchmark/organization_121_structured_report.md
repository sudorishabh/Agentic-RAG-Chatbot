# Structured / list retrieval - root cause and fix

## 1. Root cause

The catalog can filter on a closed set of facets: content type (`bundle`), `theme`, `tag`, `author`, `title_contains`, and a date range. A question's topic is open vocabulary. When the two did not line up, the structured path answered anyway — and it failed in two different directions, both of which produce the same visible symptom.

### 1a. The topic was snapped onto the nearest theme, not dropped

This is the part the previous report got wrong. It is not that a topic filter was missing; it is that a *wrong* one was applied. Traced against the live taxonomy:

```
resolve_filters(theme='Sustainable Development Goals')
  -> theme='Resources & Sustainable Development'   # a far broader theme
resolve_filters(theme='Climate Change Adaptation')
  -> theme='Climate Change'                        # 'adaptation' silently dropped
```

Theme resolution is fuzzy by design, so that "climate" finds "Climate Change". Nothing checked the *direction* of the fuzziness. A question whose topic is narrower than any theme was widened onto the theme that contains it, and the list then returned the newest rows of that whole theme. For Q112 that meant an opinion piece on decentralised education, a children's science congress, and a BioE3 video — all genuinely inside 'Resources & Sustainable Development', none of them a publication on the SDGs.

### 1b. What no facet could express simply vanished

Q119 ("Which researchers work on AI and sustainability?") produced `lookup_record` with **every filter empty**. Neither "AI" nor "sustainability" nor "researchers" is a bundle, theme, tag, author or title, so all three were dropped and the tool returned the ten most recent documents in the corpus.

### 1c. Why unrelated questions shared a list head

Both paths end at `list_documents(...) ORDER BY published_at DESC LIMIT 10`. Once the constraint is wrong or absent, the only thing ordering the result is recency, so **any two questions landing in the same bucket return the same rows**. That is the byte-identical list the benchmark kept seeing. Q112 and Q119 resolved to different operations and still produced overlapping lists, because both ended up unconstrained over the whole catalog.

### 1d. Why Q110 worked all along

"What policy briefs has TERI recently published?" is *entirely* content type plus recency. Once `bundle=policy_brief` is chosen, there is no topic left over, so the ten most recent policy briefs are not a list head — they are the answer. Any fix therefore had to distinguish "nothing left to constrain" from "something left unconstrained", not simply add filters everywhere.

## 2. The fix

One rule, applied to list and lookup operations: **every topical word in the question must be accounted for** — by a facet that genuinely means it, or by an explicit constraint on the rows — or the structured path does not answer.

Four mechanisms implement it (`app/retrieval/structured/topic.py`):

1. **Directional faithfulness** (`faithful_theme`). A resolved theme is accepted only when it carries every word that was asked for. Naming part of a theme is fine ("climate" -> "Climate Change"); dropping part of the ask is not ("climate change adaptation" -> "Climate Change"). Word matching is approximate, so "enviroment" -> "Environment" still resolves — a *missing* word makes a substitution unfaithful, a misspelt one does not.
2. **Residual topic** (`residual_topic`). The question's subject words minus everything the applied facets already account for: the bundle's own vocabulary, collective nouns like "publications", recency words, and the words of any faithful theme/tag/author. What remains is what nothing is filtering on.
3. **Topic constraint in SQL** (`RecordFilters.topic_terms`). The residual becomes `title LIKE` conditions OR-ed together, with the rows ordered by **how many** terms matched before recency. OR rather than AND because a title rarely carries every word of a topic phrase; ordering by match count is what stops the newest one-word match leading a list whose best row matches everything.
4. **Object-type guard** (`wants_person`). A document catalog holds authorship, which is a different claim from "works on", so a question asking *for people* declines and lets semantic retrieval answer. Filtering *by* a named author is untouched.

Plus one completeness fix: a list truncated by `limit` now states its total, counted over exactly the same filters, so ten rows cannot be mistaken for the whole set.

**The fallback is the point.** When the constrained list comes back empty the tool returns `ok=False` and the pipeline falls through to semantic retrieval — it never retries without the constraint. Preferring "no trustworthy structured answer" to "a plausible but wrong list" is the behaviour that makes the rest safe.

## 3. Before and after, per question

Both arms are the **same build**, differing only in `structured_topic_constraint_enabled`, so nothing here is confounded by other changes. Three runs each; the majority verdict is shown.

| Question | Verdict before -> after | Coverage | Gold docs (runs of 3) | Structured runs |
| --- | --- | --- | --- | --- |
| Q025 | INCORRECT -> INCORRECT | 0.000 -> 0.125 | 0/3 -> 0/3 | 3/3 -> 3/3 |
| Q035 | INCORRECT -> INCORRECT | 0.058 -> 0.031 | 0/3 -> 0/3 | 0/3 -> 0/3 |
| Q109 | INCORRECT -> INCORRECT | 0.000 -> 0.000 | 3/3 -> 3/3 | 3/3 -> 3/3 |
| Q112 | PARTIALLY_CORRECT -> PARTIALLY_CORRECT | 0.090 -> 0.135 | 3/3 -> 3/3 | 3/3 -> 3/3 |
| Q119 | **INCORRECT -> NO_ANSWER** | 0.123 -> 0.083 | 3/3 -> 3/3 | 3/3 -> 3/3 |
| Q110 | CORRECT -> CORRECT | 0.513 -> 0.656 | 0/3 -> 0/3 | 3/3 -> 3/3 |

### What each list actually returned

**Q025 — What are TERI's ongoing projects?**

| | First three items |
| --- | --- |
| before | Compendium and Enforcement Framework for Energy Efficiency Regulations; Agroecological Region; Prevention of Paraffin Deposition in Oil Well Tubing |
| after | Compendium and Enforcement Framework for Energy Efficiency Regulations; Agroecological Region; Prevention of Paraffin Deposition in Oil Well Tubing |

**Q035 — What innovations and technologies are being demonstrated under ongoing projects?**

| | First three items |
| --- | --- |
| before | Compendium and Enforcement Framework for Energy Efficiency Regulations; Agroecological Region; Prevention of Paraffin Deposition in Oil Well Tubing |
| after | Innovations for Advancing Climate Action and Green Economy; Integrated development of school and community leading to learning and development through; Facilitating Green Economic Recovery: Improving the uptake of cleaner technologies among M |

**Q109 — Can you recommend reports on climate change adaptation?**

| | First three items |
| --- | --- |
| before | Navigating Discussions on Decarbonisation and Business Actions at COP28; White paper on National Action Plan on Climate Change |
| after | White paper on National Action Plan on Climate Change |

**Q112 — What publications are available on Sustainable Development Goals?**

| | First three items |
| --- | --- |
| before | Decentralise education, create jobs; WCEF2026 Accelerator Session: Circular Public Procurement and Ecolabels; Chandigarh University Hosts Punjab's State-Level Orientation Workshop for National Childre |
| after | Sustainable Development Goals and Multilateralism: Agenda 2030 and Beyond; Reconciling Value Trade-Offs in Advancing Sustainable Development Goals: Risks and Opportu; Stakeholders and Corporate Social Responsibility: Are They Interlinked and Contributing to |

**Q119 — Which researchers work on AI and sustainability?**

| | First three items |
| --- | --- |
| before | Decentralise education, create jobs; Mobius Foundation's ICSE 2026 to Bring Global Sustainability Leaders Together to Advance E; UNCCD COP17 Green Zone Finance Day Panel on “Digital MRV & Carbon Finance” |
| after | (not a list) |

**Q110 — What policy briefs has TERI recently published?**

| | First three items |
| --- | --- |
| before | Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward; SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION; Discussion Brief: Sustainable Land Futures for Utility Scale RE Expansion in States: Case |
| after | Battery Assembly and Container Testing: Safety, Global Best Practices and Way Forward; SOLAR THERMAL ENERGY FOR INDUSTRIAL DECARBONIZATION; Discussion Brief: Sustainable Land Futures for Utility Scale RE Expansion in States: Case |

## 4. Do unrelated questions still share a list head?

Collisions — distinct questions whose answers open with the same two items — **before: 1 group(s)**, **after: 0 group(s)**.

- before: Q025, Q035 all open with "Compendium and Enforcement Framework for Energy Efficiency R"
- after: none

