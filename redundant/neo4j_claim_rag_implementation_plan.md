# Implementation Plan — Entity Resolution + Claim Layer + Neo4j Knowledge Graph + Hybrid Retrieval

## 0. Mission

You are modifying an existing production RAG application.

This is an implementation task, not a theoretical exercise.

Use the repository as the ultimate source of truth for current implementation details. Use this document as the product/architecture specification, but verify every repository-specific assumption before editing code.

The goal is to extend the existing RAG system with:

- canonical entity extraction and resolution
- a source-level claim/assertion layer
- temporal and conflict-aware claims
- provenance/evidence tracking
- Neo4j knowledge graph projection
- graph-aware retrieval
- lexical/BM25 retrieval
- hybrid retrieval combining semantic, lexical, and graph signals
- evidence hydration back into Qdrant
- safe rollout, evaluation, observability, and rollback

The existing application must continue working throughout the rollout.

Do not replace Qdrant with Neo4j.

Do not replace MySQL with Neo4j.

Do not let the LLM directly write Cypher or directly mutate the graph.

---

# 1. Objective

## 1.1 Primary objective

Turn the existing document-centric RAG system into a knowledge-aware RAG system that can reason about:

- people
- organizations
- projects
- locations
- services/programs
- relationships between entities
- historical changes
- conflicting assertions
- evidence supporting every claim

while preserving the existing document/semantic retrieval pipeline.

The intended user experience is that users can ask both:

### Semantic/document questions

> “What are the environmental impacts of solar energy?”

### Exact/lexical questions

> “What does the 2024 report say about SDG 7?”

### Entity/relationship questions

> “Who leads projects funded by TERI?”

### Temporal questions

> “Who led Project Phoenix in 2024?”

### Evidence-oriented questions

> “Why does the system say Alice leads Project Phoenix?”

The system should answer using structured knowledge where appropriate, while still grounding final answers in the original source text.

---

# 2. High-level target architecture

```text
                         Drupal / CMS
                   authoritative source
                           │
                           ▼
                       Documents
                           │
                           ▼
                         Chunks
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Entity extraction             Index/search
             │                           │
             ▼                           ├── Dense vectors
      Entity resolution                  └── Sparse/BM25
             │                                 │
             ▼                                 ▼
           MySQL                           Qdrant
   audit/state/staging                 semantic + lexical
             │                                 │
             ▼                                 │
       Claim extraction                         │
             │                                 │
             ▼                                 │
       Claim validation                         │
       temporal handling                        │
       conflict detection                       │
             │                                 │
             ▼                                 │
        Neo4j graph                             │
             │                                   │
             └────────────────┬──────────────────┘
                              ▼
                    Multi-signal retrieval
                     ┌────────┼────────┐
                     ▼        ▼        ▼
                   Graph    Dense    BM25
                   Neo4j    Qdrant   Qdrant
                     │        │        │
                     └────┬───┴────────┘
                          ▼
                        Fusion
                          ▼
                       Reranker
                          ▼
                   Evidence hydration
                          ▼
                     Context blocks
                          ▼
                         LLM
                          ▼
                  Answer + citations
                  + claim provenance
```

---

# 3. Core architectural principles

These are non-negotiable unless repository inspection proves an explicit conflict.

## 3.1 CMS remains the upstream source

Drupal/CMS remains the authoritative origin for:

- original content
- source records
- authoritative CMS identities
- CMS UUIDs

Do not replace the existing ingestion mechanism.

---

## 3.2 MySQL remains operational/audit storage

Keep MySQL for:

- document catalog
- ingestion state
- entity mentions
- entity resolution decisions
- review queues
- merge logs
- assertion/claim staging
- extraction caches
- identifier uniqueness
- operational state

Do not move millions of append-heavy mention rows into Neo4j just because Neo4j is being added.

---

## 3.3 Qdrant remains the text retrieval/evidence store

Qdrant must continue to own:

- chunk embeddings
- chunk text payload
- dense semantic retrieval
- lexical/BM25 retrieval once implemented
- exact chunk retrieval by `chunk_id`

The current system already uses `chunk_id` as the Qdrant point ID. Preserve that cross-store key.

---

## 3.4 Neo4j owns relationship-oriented knowledge

Neo4j should contain:

- canonical entity nodes
- aliases
- claims
- predicate vocabulary
- provenance edges
- claim/document/chunk references needed for graph traversal
- temporal/conflict metadata
- derived current-state relationships

Neo4j should not become a duplicate text store.

Do not store full chunk text or embeddings in Neo4j unless repository inspection proves a specific requirement.

---

## 3.5 Neo4j is rebuildable

Neo4j must remain a rebuildable projection.

Intended invariant:

```text
MySQL + Qdrant
     ↓
rebuild
     ↓
Neo4j
```

If Neo4j becomes unavailable or corrupted:

- ingestion must continue
- staged claims must remain durable
- retrieval must degrade safely
- Neo4j must be rebuildable without re-downloading/re-crawling the corpus where avoidable

Do not create an architecture requiring a distributed transaction between MySQL and Neo4j.

---

# 4. Current repository context — verify before editing

The current architecture was previously inspected. Treat the repository as authoritative and verify all details before changing anything.

## 4.1 Servers

The application currently has separate retrieval/public and ingestion/private surfaces.

Likely existing modules include:

```text
app/main.py
app/ingest_main.py
app/app_factory.py
app/workers/scheduler.py
```

The ingestion server is intended to remain private/network-isolated.

---

## 4.2 Existing ingestion pipeline

The current per-document path is centered around the ingestion pipeline and approximately performs:

```text
change detection
→ document construction
→ content hash
→ enrichment
→ chunking
→ embedding/upsert
→ persistence
→ logging
```

Verify the implementation and preserve existing semantics.

---

## 4.3 Chunking

The current chunk model includes fields such as:

- `chunk_id`
- text
- document ID
- version
- content hash
- section metadata
- page information
- parent/child information

The current `chunk_id` behavior is version-scoped and tied to document content/version lifecycle.

Do not break:

- parent/child semantics
- chunk ID rules
- document reindex behavior
- ACL metadata
- citation behavior

---

## 4.4 Qdrant

The current application uses Qdrant for dense document retrieval.

Verify:

- Qdrant server version
- Python client version
- collection configuration
- vector dimensions
- distance metric
- payload indexes
- current keyword/sparse retrieval behavior, if any

The important existing design property is:

```text
Qdrant point ID == chunk_id
```

Preserve it.

---

## 4.5 Existing retrieval

Inspect:

```text
app/pipeline/query_pipeline.py
app/retrieval/retriever.py
app/retrieval/hybrid_search.py
app/retrieval/scoped_retrieval.py
app/retrieval/fusion.py
```

The existing pipeline may already have semantic search plus a keyword leg and RRF-style fusion.

Do not assume the existing keyword leg is BM25.

Determine exactly what it is.

Reuse it or upgrade it if appropriate rather than adding duplicate retrieval machinery.

---

## 4.6 Existing LLM and embedding abstractions

Inspect and reuse:

```text
app/core/clients/llm.py
app/core/clients/embeddings.py
```

Reuse existing structured-output/Pydantic conventions.

Do not introduce a second LLM abstraction unnecessarily.

---

## 4.7 Existing faithfulness claim machinery

Inspect `app/generation/faithfulness.py`.

Existing answer-level claims are different from new source-level knowledge assertions.

Avoid naming collisions.

Use a distinct Python-side name such as `Assertion` for the source-level extracted object if that remains the cleanest option after repository inspection.

---

## 4.8 Existing entity terminology

The existing structured retrieval layer may already use `Entity` for CMS content bundles rather than real-world entities.

Do not blindly reuse existing names.

Use an appropriate `app/knowledge/` namespace or the repository-equivalent.

---

## 4.9 Existing conventions

Prefer existing repository conventions for:

- configuration
- raw MySQL SQL
- idempotent DDL
- feature flags
- pytest
- monkeypatching
- retry/state handling
- scheduler/background work
- logging and metrics
- Docker/Compose
- deployment

Do not introduce a new queue/task framework unless repository inspection proves the current architecture has changed and requires one.

---

# 5. Entity model

Entities are canonical real-world objects such as:

```text
Person
Organization
Project
Location
Service
Program
Department
```

Do not finalize the exact type vocabulary until the actual corpus/source schema confirms it.

Start with the smallest vocabulary supported by evidence, likely:

- PERSON
- ORGANIZATION
- PROJECT

Then add others when Phase 0 validates them.

Avoid artificial distinctions such as `INSTITUTION` vs `ORGANIZATION` unless the corpus proves the distinction is useful.

---

# 6. Mention vs entity

A mention is a text occurrence:

```text
"Dr. Raj Sharma"
```

The canonical entity is something like:

```text
person_00192
```

A single entity can have many mentions.

Store mention-level audit information in MySQL.

Do not create one Neo4j entity node per mention.

---

# 7. Entity extraction

Implement extraction in increasingly expensive stages:

```text
1. CMS-derived mentions
2. cache lookup
3. gazetteer/alias lookup
4. deterministic patterns
5. LLM extraction only when necessary
```

Use child chunks where the existing chunk model indicates parents duplicate child content.

Cache extraction using chunk content/version information.

Do not call an LLM when deterministic logic can safely produce the required result.

Record exact character spans for extracted mentions.

---

# 8. Entity resolution

Entity resolution asks:

> Which canonical entity does this mention refer to?

Use conservative tiers:

```text
Tier 0: exact authoritative identifier
Tier 1: unique safe alias
Tier 2: name + corroboration
Tier 3: scored candidate + margin
Tier 4: LLM adjudication for genuinely ambiguous cases
Tier 5: provisional entity or unresolved
```

Core safety rule:

> False merge is worse than unresolved.

Do not merge because of name similarity alone when strong contradictory context exists.

---

## 8.1 Resolution bands

Use configurable bands such as:

```text
AUTO
REVIEW
AMBIGUOUS
NEW
UNRESOLVED
```

Use the earlier proposed thresholds only as starting hypotheses.

Calibrate against real corpus data before production.

Potential initial candidate:

```text
AUTO:
score >= 0.90
margin >= 0.15
at least one corroborating feature
no veto
```

Do not treat these numbers as proven truth.

---

## 8.2 Resolution vetoes

Strong vetoes override similarity:

- identifier conflict
- type conflict
- incompatible organization context
- impossible temporal context
- other evidence-backed contradictions

---

## 8.3 Merge/unmerge

Entity merges must be reversible.

Record exact mention IDs and decision metadata.

Prefer tombstone/`merged_into` semantics over destructive deletion.

Unmerge must be able to restore prior assignments without reprocessing the entire corpus.

---

# 9. Claim/assertion layer

A source-level claim is a structured representation of what text says.

Example:

Source:

> “Bob is currently leading Project Phoenix.”

Structured assertion:

```text
subject = project_123
predicate = LED_BY
object = person_456
```

Claims must additionally support:

- confidence
- evidence
- source document
- source chunk
- evidence span/quote
- temporal validity
- extraction method
- model/version
- status
- conflict/supersession information

---

# 10. Three knowledge levels

Keep these distinct.

## Level 1 — source text

Stored in Qdrant:

```text
chunk_id
chunk_text
```

Immutable for that document/chunk version.

## Level 2 — normalized assertion

Staged in MySQL and represented in Neo4j:

```text
Project Phoenix
LED_BY
Bob
```

plus metadata/provenance.

## Level 3 — current graph state

Derived traversal relationship:

```text
(:Project)-[:LED_BY]->(:Person)
```

Level 3 is derived from Level 2.

Nothing should independently write current-state semantic edges as separate truth.

---

# 11. Claim representation: hybrid node + projected relationship

Use this as the default architecture.

## 11.1 Authoritative claim node

```text
(:Claim)
```

with:

```text
(:Claim)-[:SUBJECT]->(:Entity)
(:Claim)-[:OBJECT]->(:Entity)
(:Claim)-[:USES_PREDICATE]->(:Predicate)
(:Claim)-[:SUPPORTED_BY]->(:Chunk)
```

and where applicable:

```text
(:Claim)-[:CONTRADICTS]->(:Claim)
(:Claim)-[:SUPERSEDES]->(:Claim)
```

## 11.2 Derived traversal edge

Project approved/current claims into fast relationships:

```text
(:Project)-[:LED_BY]->(:Person)
(:Project)-[:FUNDED_BY]->(:Organization)
```

Every projected edge must include enough metadata to find its authoritative claim, including:

```text
claim_id
confidence
valid_from
valid_until
current
projection_version
```

The projection must be:

- deterministic
- idempotent
- versioned
- rebuildable
- disposable

Disputed claims must not create confident current-state relationships.

---

# 12. Why claims are nodes

Do not reduce every fact to a simple edge.

Claims need:

- multiple evidence sources
- per-evidence metadata
- temporal validity
- historical preservation
- conflicts
- supersession
- model/extractor metadata
- auditability

Explicit claim nodes solve these requirements.

---

# 13. Deterministic claim IDs

Use a deterministic claim ID based on stable inputs such as:

```text
chunk_id
subject_entity_id
predicate
object_entity_id or normalized literal
valid_from
valid_until
```

The same source chunk processed twice must produce the same claim ID.

Different chunks asserting the same fact should produce distinct claims because they are independent evidence.

This is the basis for safe retries and idempotent `MERGE`.

---

# 14. Predicate vocabulary

Use a closed and versioned vocabulary.

Each predicate should define:

- name
- description
- subject/domain types
- object/range types
- functional/non-functional behavior
- temporal semantics
- literal-object support, if applicable

Potential initial predicates:

```text
LED_BY
WORKS_AT
MEMBER_OF
FUNDED_BY
PARTNER
LOCATED_IN
PART_OF_PROGRAM
PARENT_OF
AUTHORED
```

Do not allow the LLM to invent predicates directly.

Unknown predicates go to a review/vocabulary-extension path.

Keep predicate direction canonical:

```text
Project --LED_BY--> Person
Project --FUNDED_BY--> Organization
Person --WORKS_AT--> Organization
```

Do not mix equivalent predicate directions unnecessarily.

---

# 15. Temporal claims

Support:

```text
valid_from
valid_until
asserted_at
created_at
temporal_basis
```

Distinguish:

- `valid_from` / `valid_until`: when the fact was true in the world
- `asserted_at`: when the system received/learned the assertion
- `created_at`: when the record was written
- `temporal_basis`: how validity was established

Do not silently infer fact validity solely from document publication date.

---

# 16. Conflict handling

For functional predicates:

```text
same subject
+
same predicate
+
overlapping validity
+
different object
=
potential conflict
```

Handle deterministically.

Example:

```text
Bob:
2024-01 → 2026-03

Alice:
2026-03 → present
```

is not a contradiction.

But:

```text
Bob:
2026-01 → present

Alice:
2026-02 → present
```

is a conflict for a functional `LED_BY` predicate.

If no safe adjudication exists:

```text
both claims = disputed
no current-state projection
review case created
```

Preserve historical claims.

Never silently delete history.

---

# 17. Evidence and provenance

Every claim must be traceable:

```text
Claim
 ↓
Chunk
 ↓
Document
```

Retain:

- document ID
- chunk ID
- exact quote where possible
- character offsets
- extraction method
- extraction model/version
- prompt version

The application must independently verify the LLM quote exists verbatim in the chunk and recompute offsets.

Never trust model-generated offsets without validation.

---

# 18. Neo4j ↔ Qdrant evidence bridge

This is mandatory.

When a claim is extracted from `chunk_8217`, persist that provenance in Neo4j.

Conceptually:

```text
Claim_123
   |
   └── SUPPORTED_BY → Chunk(chunk_8217)
```

or an equivalent model.

Later:

```text
Neo4j
 ↓
claim_123
 ↓
chunk_8217
 ↓
Qdrant exact lookup
 ↓
original chunk text
```

Important distinction:

### Qdrant semantic search

```text
query
 ↓
similarity search
 ↓
candidate chunks
```

### Qdrant evidence lookup

```text
chunk_id
 ↓
exact point lookup
 ↓
actual chunk text
```

Do not confuse those operations.

Use batched exact lookups for multiple chunk IDs.

---

# 19. Qdrant responsibilities

Qdrant should support three conceptual roles:

## 19.1 Dense semantic retrieval

Find text with similar meaning.

## 19.2 Sparse/BM25 lexical retrieval

Find text containing important exact terms, identifiers, acronyms, names, etc.

## 19.3 Exact evidence hydration

Given a `chunk_id`, return the actual text/payload for that chunk.

---

# 20. BM25 / sparse lexical search

Before changing Qdrant:

1. Inspect the current keyword retrieval implementation.
2. Determine whether BM25 already exists.
3. Check the installed Qdrant server/client version.
4. Verify sparse-vector support.
5. Determine whether existing collections can be extended safely.
6. Determine whether re-indexing is required.
7. Measure the value of lexical search on the actual corpus.

Preferred architecture:

```text
Same Qdrant document collection
+
dense vector
+
sparse/BM25 representation
```

Do not introduce Elasticsearch/OpenSearch merely to get BM25 unless the evaluation demonstrates a need that Qdrant cannot meet.

---

# 21. Retrieval evaluation for BM25

Create a real query benchmark.

Include categories:

```text
semantic
exact-term
identifier
acronym
entity/name
project name
relational
multi-hop
temporal
mixed
```

Compare:

```text
dense-only
BM25-only
dense + BM25
graph + dense
graph + dense + BM25
```

Measure retrieval and answer-level impact.

Do not assume BM25 must become default simply because hybrid search is popular.

Adopt it as a default only if it improves the real workload without unacceptable cost/latency/complexity.

---

# 22. Multi-signal retrieval

Use three retrieval signals:

```text
Dense semantic
Lexical/BM25
Graph relational
```

Interpret them as:

```text
Dense:
"What text means something similar?"

BM25:
"What text contains these important exact terms?"

Graph:
"How are entities and claims related?"
```

---

# 23. Query routing

Route queries according to their nature.

Examples:

### Semantic

> “Explain TERI's approach to renewable energy.”

Dense should dominate.

### Exact lexical

> “What documents mention SDG 7?”

BM25 should dominate.

### Graph

> “Who leads projects funded by TERI?”

Graph should dominate.

### Mixed

> “What projects funded by TERI did Alice lead, and what does the 2024 report say about them?”

Use graph + dense + BM25.

Do not force all queries through every backend if unnecessary.

---

# 24. Retrieval fusion

Prefer rank-based fusion such as existing RRF.

Do not naïvely add raw BM25 and cosine scores because their scales differ.

Start with:

```text
Dense
+
BM25
+
Graph candidates
↓
rank fusion
```

Then existing reranker.

Only introduce weighted RRF or learned weighting after there is enough evaluation data to justify it.

Reuse existing `fusion.py` if possible.

---

# 25. Reranking

Preferred pipeline:

```text
Dense + BM25 + Graph
        ↓
candidate generation
        ↓
RRF/fusion
        ↓
existing reranker
        ↓
final evidence candidates
        ↓
LLM
```

Reuse the current reranker.

Do not introduce a second reranker without measurable need.

---

# 26. Graph-first retrieval

For graph-shaped questions:

```text
User question
 ↓
query/entity analysis
 ↓
entity resolution
 ↓
safe Cypher template
 ↓
Neo4j traversal
 ↓
entity IDs + claim IDs + chunk IDs
 ↓
batched Qdrant exact lookup
 ↓
evidence
 ↓
rerank/context
 ↓
LLM
```

Neo4j returns structured knowledge and provenance pointers, not necessarily full source text.

---

# 27. Vector-first retrieval

For open-ended questions:

```text
question
 ↓
dense Qdrant search
 ↓
relevant chunks
 ↓
optional graph enrichment
 ↓
claims/entities related to those chunks
 ↓
context
 ↓
LLM
```

Preserve existing vector-first behavior whenever new graph features are disabled.

---

# 28. BM25-first retrieval

For exact terminology:

```text
question
 ↓
BM25/Qdrant sparse search
 ↓
candidate chunks
 ↓
optional dense/graph enrichment
 ↓
rerank
 ↓
LLM
```

---

# 29. Hybrid retrieval

Target architecture:

```text
                         Query
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
            Dense          BM25        Graph
           Qdrant         Qdrant       Neo4j
              │            │            │
              └──────┬─────┘            │
                     ▼                  │
                    RRF                 │
                     │                  │
                     └────────┬─────────┘
                              ▼
                        Candidate set
                              │
                              ▼
                           Reranker
                              │
                              ▼
                     Evidence hydration
                              │
                              ▼
                            Context
                              │
                              ▼
                             LLM
```

---

# 30. Neo4j graph model

Use a graph model broadly along these lines, after verifying the exact Neo4j version and constraints supported by the installed edition.

## Entity labels

```text
(:Entity:Person)
(:Entity:Organization)
(:Entity:Project)
(:Entity:Location)
(:Entity:Service)
(:Entity:Program)
(:Entity:Department)
```

Common fields:

```text
entity_id
canonical_name
normalized_name
entity_type
source
cms_uuid
trust
status
merged_into
first_seen_at
updated_at
```

---

## 30.1 Alias

```text
(:Alias)
```

with:

```text
normalized
surface
alias_type
autolink
is_ambiguous
valid_from
valid_until
source
confidence
```

Relationship:

```text
(:Entity)-[:HAS_ALIAS]->(:Alias)
```

---

## 30.2 Claim

```text
(:Claim)
```

with:

```text
claim_id
predicate
subject_id
object_id
object_literal
object_type
valid_from
valid_until
temporal_basis
asserted_at
created_at
confidence
status
extraction_method
extraction_model
extractor_version
prompt_version
```

---

## 30.3 Chunk stub

```text
(:Chunk)
```

with only graph/provenance fields such as:

```text
chunk_id
document_id
doc_version
chunk_index
page_number
section_heading
content_hash
```

No full text.

---

## 30.4 Document stub

```text
(:Document)
```

with graph-useful metadata and no full body.

---

# 31. Neo4j provenance relationships

Evaluate at least:

```text
(:Claim)-[:SUBJECT]->(:Entity)
(:Claim)-[:OBJECT]->(:Entity)
(:Claim)-[:USES_PREDICATE]->(:Predicate)
(:Claim)-[:SUPPORTED_BY]->(:Chunk)
(:Chunk)-[:PART_OF]->(:Document)
(:Claim)-[:CONTRADICTS]->(:Claim)
(:Claim)-[:SUPERSEDES]->(:Claim)
```

Where required:

```text
(:Entity)-[:HAS_ALIAS]->(:Alias)
(:Entity)-[:SAME_AS_CMS]->(:Document)
```

---

# 32. Current-state graph relationships

Project approved current knowledge into:

```text
(:Project)-[:LED_BY]->(:Person)
(:Person)-[:WORKS_AT]->(:Organization)
(:Person)-[:MEMBER_OF]->(:Department)
(:Project)-[:FUNDED_BY]->(:Organization)
(:Project)-[:PARTNER]->(:Organization)
(:Project)-[:LOCATED_IN]->(:Location)
(:Project)-[:PART_OF_PROGRAM]->(:Program)
(:Organization)-[:PARENT_OF]->(:Organization)
(:Person)-[:AUTHORED]->(:Document)
```

These must be derived, not independently authored.

---

# 33. Neo4j constraints and indexes

Create only those required for correctness and observed query patterns.

At minimum investigate uniqueness for:

```text
entity_id
claim_id
chunk_id
document_id
predicate
cms_uuid
```

Hot-path indexes may include:

```text
alias normalized form
entity type + normalized name
entity status
entity trust
claim status
claim predicate
claim subject
claim object
chunk document/version
```

Verify exact syntax against the installed Neo4j edition/version.

---

# 34. Security

## LLM never generates arbitrary Cypher

The model may choose:

```text
template_id
typed parameters
```

The application supplies the actual reviewed Cypher template.

## Parameterized queries

Never interpolate user/model data into query strings.

## Relationship/label allow-list

Dynamic labels and relationship types must originate only from code-side allow-lists.

## Read-only retrieval account

Prefer:

```text
ingestion → read/write Neo4j
retrieval → read-only Neo4j
```

## Bounded queries

Every graph template must have:

- bounded depth
- reasonable limit
- timeout/p95 budget

Do not expose arbitrary variable-length traversal.

---

# 35. Access control

Preserve current tenant/ACL behavior.

When graph results provide chunk IDs:

```text
Neo4j → chunk_id → Qdrant
```

reapply authoritative ACL/tenant checks before exposing the text.

A raw chunk ID must never bypass access control.

---

# 36. Prompt injection protection

Document text is untrusted data.

Protect extraction with:

1. structured output
2. closed entity list
3. closed predicate vocabulary
4. quote must exist verbatim in source chunk
5. deterministic validation
6. confidence/review gate
7. disputed claims never projected as current knowledge

The LLM must never write directly to the database.

---

# 37. Ingestion pipeline

Target behavior:

```text
existing document sweep
    ↓
change detection
    ↓
build canonical document
    ↓
content hash
    ↓
existing chunking
    ↓
existing dense indexing
    ↓
entity extraction
    ↓
entity resolution
    ↓
claim extraction
    ↓
claim validation
    ↓
MySQL staging
    ↓
Neo4j projection
    ↓
conflict detection
    ↓
current-state projection
```

All new work should be fail-open where consistent with existing ingestion semantics.

---

# 38. Separate staging from projection

Do not require the ingestion request to successfully commit both MySQL and Neo4j.

Preferred:

```text
ingestion
→ MySQL staging
→ separate Neo4j projection
```

Benefits:

- Neo4j outage does not break ingestion
- no distributed transaction
- batching is possible
- projection is retryable
- extraction is not repeated merely because Neo4j was unavailable

---

# 39. Background work

Reuse the existing scheduler/state-based background work model.

Do not add Celery/RQ or another queue unless repository inspection proves the application now has a justified requirement for one.

Use durable “missing work” state and attempt counters where the existing architecture already uses that pattern.

Expensive claim extraction/backfill should be explicitly budgeted.

---

# 40. Error handling

## Entity extraction failure

- log
- record attempt
- do not create invalid claims
- preserve document indexing

## Entity resolution ambiguity

- no unsafe merge
- queue/mark unresolved
- allow later re-resolution

## Claim extraction failure

- no claim
- stage nothing invalid
- retry through durable work list

## Neo4j unavailable

- do not fail ingestion
- keep MySQL staging
- graph catches up later

## Qdrant hydration failure

- do not fabricate evidence
- fall back or omit unsupported graph claim according to current RAG behavior

## BM25 unavailable

- dense retrieval remains available where safe

## Graph query timeout

- bounded timeout
- fallback to existing retrieval where possible
- record metrics

---

# 41. Idempotency

The system must safely handle repeated:

- extraction
- resolution
- claim staging
- graph projection
- backfill runs
- scheduler runs

Use deterministic IDs and `MERGE`.

Never create duplicates from retries.

---

# 42. Document lifecycle

## Unchanged document

Do not unnecessarily re-extract.

## Changed document

Generate new applicable chunk/claim state according to existing versioning.

## Deleted document

Remove its evidence/claims from active knowledge appropriately, but do not delete canonical entities solely because one document disappeared.

## Entity merge

Update/reconcile affected claims and projection.

## Merge reversal

Restore previous assignments from the merge log.

---

# 43. Feature flags

All new behavior should default to OFF.

Verify existing names first.

Potential flags:

```text
knowledge_enabled
entity_extraction_enabled
claim_extraction_enabled
neo4j_projection_enabled
bm25_enabled
graph_retrieval_enabled
hybrid_retrieval_enabled
```

Do not conflict with existing configuration.

With all new flags off, behavior should remain effectively equivalent to today's behavior.

---

# 44. Backfill

This is a new knowledge layer over an existing corpus, not a destructive migration.

Use resumable operations:

```text
1. create MySQL knowledge tables
2. create Neo4j schema
3. seed CMS entities
4. extract mentions
5. resolve mentions
6. validate gold/evaluation quality
7. extract claims
8. validate/normalize/conflict-detect
9. project entities
10. project claims/evidence
11. build current-state projection
12. evaluate retrieval
13. progressively enable features
```

Do not run expensive LLM backfill without an explicit operator-controlled budget.

---

# 45. Performance

Measure:

- documents
- chunks
- mentions/chunk
- entity count
- alias count
- assertions/chunk
- claims
- graph node count
- graph relationship count
- graph query p95
- Qdrant dense p95
- Qdrant BM25 p95
- fusion latency
- reranker latency
- evidence hydration latency
- LLM extraction calls/cost

Optimize after measuring.

Do not assume exact corpus sizes.

Batch:

- MySQL writes
- Neo4j projection
- Qdrant hydration
- retrieval queries where practical

---

# 46. Caching

Use versioned caches.

## Entity extraction

```text
chunk_content_hash
+
extractor_version
```

## Claim extraction

```text
chunk_content_hash
+
resolved entity set
+
extractor_version
```

## Adjudication

```text
normalized mention
+
candidate IDs
+
prompt/model version
```

## Gazetteer

Process-local cache with explicit reload/version handling.

Do not add graph-result caching initially unless evaluation proves it is needed.

---

# 47. Observability

Add spans/metrics following existing conventions.

Recommended logical operations:

```text
ingest.entities
ingest.resolve
ingest.entity_llm
ingest.claims
ingest.claim_llm
graph.project
rag.graph
rag.bm25
rag.dense
rag.fusion
rag.graph_hydrate
rag.rerank
```

Track:

```text
entity_mentions
entity_auto
entity_review
entity_ambiguous
entity_new
entity_cache_hit
entity_llm_calls
claims_extracted
claims_rejected
claims_pending_review
claim_cache_hit
claim_llm_calls
graph_nodes_merged
graph_rels_merged
conflicts_detected
bm25_hits
dense_hits
graph_hits
fusion_candidates
evidence_hydration_failures
```

Never expose entity names or source text in public metrics.

---

# 48. Explainability tools

Provide operator/dev paths for:

```text
explain claim
explain entity
explain mention
review unresolved cases
review disputed claims
report false-merge sources
report predicate accuracy
```

A key diagnostic question must be answerable:

> “Why does the system believe this?”

---

# 49. Testing

## 49.1 Baseline

Before modifications:

- run full current test suite
- record result
- run representative retrieval queries
- record current answers/latency

## 49.2 Unit tests

Cover:

- normalization
- extraction
- resolution
- vetoes
- score bands
- merge/unmerge
- claim extraction
- quote validation
- predicate validation
- temporal parsing
- conflict handling
- deterministic IDs
- graph projection
- rebuild
- BM25
- fusion
- exact Qdrant hydration
- ACL filtering

## 49.3 Integration tests

Test:

```text
document
→ chunks
→ entities
→ claims
→ MySQL staging
→ Neo4j
→ graph query
→ chunk IDs
→ Qdrant hydration
→ source evidence
```

Also test service outages and partial failures.

## 49.4 End-to-end tests

Include at least:

> Who leads projects funded by TERI?

> Who led Project Phoenix in 2024?

> What documents mention SDG 7?

> What are the environmental impacts of solar energy?

> What projects funded by TERI did Alice lead, and what does the 2024 report say about them?

Verify:

- route selection
- retrieval
- evidence
- citations
- ACL
- final answer
- no regression

---

# 50. Evaluation gates

Use initial targets, but calibrate them against real data.

## Entity

```text
false merge rate < 1% for AUTO
same-name different entities separated = 100%
```

## Claim

```text
claim precision >= 0.85
predicate accuracy >= 0.90
conflict classification >= 0.90
```

## Graph

```text
graph query correctness >= 0.95
evidence correctness >= 0.95
```

## Retrieval

Measure:

- Recall@K
- MRR
- nDCG where applicable
- latency
- final answer quality

Compare all relevant retrieval combinations.

## Final system

There must be:

- no existing RAG quality regression
- no ACL leakage
- no unsafe graph writes
- no duplicate knowledge due to retries

---

# 51. Rollout

Roll out progressively:

```text
Infrastructure
    ↓
Entity extraction shadow
    ↓
Entity resolution shadow
    ↓
Entity graph
    ↓
Claim extraction/staging
    ↓
Claim validation
    ↓
Claim graph
    ↓
BM25 evaluation
    ↓
Hybrid retrieval testing
    ↓
Graph retrieval flag
    ↓
Production enablement
```

At each phase:

- run tests
- inspect logs/metrics
- inspect diff
- verify rollback

---

# 52. Rollback

Rollback must never require recovering lost source data from Neo4j.

Expected rollback mechanisms:

```text
graph_retrieval_enabled = false
bm25_enabled = false
hybrid_retrieval_enabled = false
```

If graph projection is corrupt:

```text
drop/rebuild graph
```

If a bad projection version is deployed:

```text
restore prior projection or rebuild from durable inputs
```

Existing RAG behavior must remain available when the graph is disabled.

---

# 53. Likely affected code areas

These are candidates only. Verify exact paths first.

Potential areas:

```text
app/config.py

app/core/clients/
app/catalog/
app/knowledge/
app/knowledge/claims/
app/knowledge/graph/
app/retrieval/
app/retrieval/graph/
app/pipeline/
app/observability/
app/api/
app/schemas/
app/workers/
tests/
docker-compose.yml
.env.example
```

Do not create files merely because this document names them.

Map responsibilities to the repository's actual structure.

---

# 54. Implementation discipline

For each phase:

1. Inspect the repository.
2. Explain the existing implementation briefly.
3. Identify exact files.
4. Make the smallest clean change.
5. Run focused tests.
6. Run relevant regression tests.
7. Inspect the diff.
8. Fix problems.
9. Continue only after the phase is healthy.

Never:

- silently replace existing behavior
- add placeholder implementations
- use fake production data
- add unnecessary dependencies
- make broad rewrites
- skip tests because the code compiles

---

# 55. Final acceptance checklist

## Existing behavior

- [ ] Existing ingestion passes.
- [ ] `/chat` passes.
- [ ] `/search` passes.
- [ ] Existing citations pass.
- [ ] Existing ACL behavior passes.
- [ ] Existing behavior remains intact with new flags off.

## Entity layer

- [ ] Entity extraction works.
- [ ] CMS identity is reused.
- [ ] Resolution is conservative.
- [ ] False merge gate passes.
- [ ] Same-name different entities stay separate.
- [ ] Merge/unmerge works.
- [ ] Decisions are auditable.

## Claim layer

- [ ] Claims only reference valid entities.
- [ ] Predicate vocabulary is closed.
- [ ] Quotes are source-verifiable.
- [ ] Temporal validity works.
- [ ] Conflicts are deterministic.
- [ ] Historical claims remain available.
- [ ] Disputed claims are not projected.
- [ ] Claim IDs are deterministic.

## Neo4j

- [ ] Schema creation is idempotent.
- [ ] Constraints work.
- [ ] Projection is idempotent.
- [ ] Rebuild works.
- [ ] Graph queries are bounded.
- [ ] Retrieval credentials are read-only.
- [ ] LLM cannot execute arbitrary Cypher.

## Qdrant

- [ ] Dense retrieval still works.
- [ ] BM25 has been experimentally evaluated.
- [ ] BM25 is enabled only if useful.
- [ ] Sparse indexing works if enabled.
- [ ] Exact chunk hydration works.
- [ ] Batched hydration works.
- [ ] ACL/tenant checks are preserved.

## Hybrid retrieval

- [ ] Graph-first works.
- [ ] Vector-first works.
- [ ] BM25-first works where appropriate.
- [ ] Dense + BM25 fusion works.
- [ ] Graph + dense works.
- [ ] Graph + dense + BM25 works where appropriate.
- [ ] Reranker integration works.
- [ ] Evidence is grounded.
- [ ] No inaccessible text is returned.

## Reliability

- [ ] Neo4j outage does not break ingestion.
- [ ] Neo4j outage safely degrades retrieval.
- [ ] Qdrant failure is handled safely.
- [ ] LLM failure does not create invalid knowledge.
- [ ] Retries are idempotent.
- [ ] Partial projection is resumable.
- [ ] Graph can be rebuilt.
- [ ] Feature flags restore existing behavior.

## Evaluation

- [ ] Unit tests pass.
- [ ] Integration tests pass.
- [ ] End-to-end tests pass.
- [ ] Existing regression suite passes.
- [ ] Retrieval benchmark is complete.
- [ ] Claim/entity quality gates pass.
- [ ] Evidence correctness passes.
- [ ] Answer quality does not regress.
- [ ] Security tests pass.
- [ ] Performance is within measured budgets.

---

# 56. Final implementation report

At completion, provide:

## Summary

What changed.

## Files changed

Exact files and purpose.

## Database changes

- MySQL tables/indexes
- Neo4j constraints/indexes/schema
- Qdrant collection/vector changes

## Tests run

Exact commands and results.

## Retrieval evaluation

Compare:

```text
dense
BM25
dense + BM25
graph + dense
graph + dense + BM25
```

## Rollout state

Which feature flags are enabled.

## Limitations

What remains imperfect.

## Decisions

Any unresolved architecture/product choices.

---

# 57. Final architecture to preserve

The final mental model is:

```text
CMS
=
source of original information

MySQL
=
operational state + audit + staging

Qdrant
=
text + dense semantic search + BM25/lexical search + exact chunk lookup

Neo4j
=
entities + claims + relationships + provenance + graph traversal

LLM
=
language interpretation/synthesis, never unrestricted database authority
```

And graph evidence must work like:

```text
Source document
    ↓
Chunk
    ↓
Claim
    ↓
Neo4j
    ↓
query returns claim_id + chunk_id
    ↓
application uses chunk_id
    ↓
Qdrant exact lookup
    ↓
original source text
    ↓
LLM
    ↓
answer + citation
```

The most important retrieval mental model is:

```text
                         QUERY
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
           Dense           BM25         Graph
          Qdrant          Qdrant        Neo4j
             │             │             │
             └──────┬──────┘             │
                    ▼                    │
                  Fusion                 │
                    │                    │
                    └────────┬───────────┘
                             ▼
                           Rerank
                             ▼
                      Evidence hydration
                             ▼
                            LLM
                             ▼
                    Answer + provenance
```

Do not add components simply because they are fashionable.

Use measurement from the actual corpus to decide whether BM25, graph retrieval, additional reranking, or other retrieval improvements are worth their complexity.

Begin by inspecting the current repository and establishing the baseline. Do not modify production behavior until the current code paths, tests, and data contracts are understood.
