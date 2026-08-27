# Retrieval logging

One switch turns on a complete, per-query record of what retrieval did:

```env
is_retrieval_log=true
```

With it on, every question writes one JSON file describing the whole retrieval
pipeline — every Qdrant pull, every graph traversal, every SQL statement, what
each returned, how long each took, anything that failed, and the context that
finally reached the LLM. With it off (the default) nothing is built, serialized
or written: each instrumentation point is a boolean read.

It is for debugging, evaluation and analysis. It never changes an answer.

---

## 1. Turning it on

| Variable | Default | What it does |
|---|---|---|
| `is_retrieval_log` | `false` | The one switch. Everything below is inert without it. |
| `RETRIEVAL_LOG_DIR` | *(empty → `<repo>/logs`)* | Where traces are written. Empty resolves beside the repository, so the path does not depend on the working directory the server was started from. |
| `RETRIEVAL_LOG_DETAIL` | `compact` | `compact` writes one line per retrieved item and one line per filter; `full` writes the structured object with every payload field. See §3.1. |
| `RETRIEVAL_LOG_INCLUDE_TEXT` | `true` | Keep retrieved passage text. `false` keeps ids, scores, metadata and a character count — a safe reference to the content rather than the content. |
| `RETRIEVAL_LOG_MAX_TEXT_CHARS` | `1200` | Per-string ceiling (context text, SQL, an error message). Longer values are truncated with a marker. A compact hit's snippet is shorter still (160). |
| `RETRIEVAL_LOG_MAX_RESULTS` | `10` | Per-event ceiling on results captured — Qdrant hits, graph rows, SQL rows. The recorded counts are always the true totals. |
| `RETRIEVAL_LOG_REPORT` | `true` | Write `report.md` beside each `trace.json` — the same trace explained in prose. See §2. |
| `RETRIEVAL_LOG_SUMMARY` | `true` | Also append a one-line-per-query digest under `summary/`. |

Nothing is hard-coded: all of it is read from the environment through
`app/config.py` on every query, so a value can be changed without a code change.

## 2. Where the traces go

```text
logs/
├── 2026-08-26/
│   ├── query_5f3c1e9a.../
│   │   ├── trace.json              the record, for parsing
│   │   └── report.md               the same trace explained, for reading
│   └── query_a17b40d2.../
├── errors/
│   └── 2026-08-26/
│       └── query_a17b40d2.../      a copy of any query that had a failure
└── summary/
    └── 2026-08-26.jsonl            one flat line per query
```

One directory per query, named for its `request_id` (a uuid4) — which is also
the correlation key inside the files: every event belonging to one question
lives in one trace, and two concurrent queries can never contend for a path.
The names inside are fixed, so `logs/*/query_*/trace.json` is a stable glob and
`report.md` is always beside the data it describes. Both files are written to a
temporary name and moved into place, so a reader never sees a half-written one.
Directories are created on first write.

### `report.md`

The trace, written out for a person: what the question was taken to mean and
why, which retriever was asked what, **what each leg of retrieval is for**, the
passages that reached the LLM in the order it sees them (with the `[n]` that
matches the answer's citations), where the time went, and what failed. Rendered
from the same dictionary as `trace.json`, so the two cannot disagree — it adds
no data, only ordering, prose and the standing explanation of the pipeline.

Set `RETRIEVAL_LOG_REPORT=false` to write only the JSON. A report that fails to
render costs the prose and nothing else; `trace.json` is written either way.

`errors/` exists so a bad query can be found without reading every file, and
`summary/` so latency and failure trends can be loaded without parsing the
traces at all.

## 3. What a trace contains

```jsonc
{
  "schema_version": 1,
  "request_id": "5f3c1e9a...",          // correlates everything below
  "timestamp": "2026-08-26T12:04:11.183+00:00",
  "entrypoint": "chat.stream",          // or "search"
  "question": "how much rooftop solar was added in 2024?",
  "top_k": 6,

  "query": {                            // what query understanding decided
    "search_query": "rooftop solar capacity added 2024",
    "intent": "qa",
    "answer_format": "default",
    "filters": [ /* the Qdrant facet conditions, as sent */ ],
    "capabilities": ["qa"],
    "intents": [{"label": "qa", "confidence": 0.91, "rationale": "..."}]
  },

  "retrievers": {                        // which stores were invoked, and their cost
    "invoked": ["mysql", "qdrant"],
    "totals": {
      "qdrant": {"calls": 4, "results": 86, "latency_ms": 141.2, "errors": 0,
                 "stages": ["website_pull", "not_website_pull", "title_leg",
                            "parent_fetch"]},
      "mysql":  {"calls": 1, "results": 8507, "latency_ms": 526.5, "errors": 0,
                 "stages": ["catalog"]}
    }
  },

  "timings": {
    "started_at": "...", "finished_at": "...",
    "total_latency_ms": 2841.6,
    "retrieval_latency_ms": 667.7,      // summed across every retriever call
    "stages_ms": {"rag.search": 210.4, "rag.rerank": 88.1, "...": 0}
  },

  "events": [ /* one entry per retriever call — see below */ ],

  "context": {                           // what actually reached the LLM
    "block_count": 5,
    "total_chars": 20352,                // the real total, whatever was kept below
    "prompt_chars": 21167,               // the rendered context, headers included
    "blocks": [{"n": 1, "score": 0.81, "conflict": false,
                "text_chars": 7937,      // the real block size
                "source": "Scope and potential of coastal ecosystem… · pp.5-6 · pdf_attachment",
                "text": "Introduction Coastal ecosystems are…"}]   // clipped for the log
  },

  "outcome": {"intent": "qa", "cached": false, "answered": true,
              "used_chunks": 5, "citations": 3, "conflict": false,
              "numeric_mismatch": false, "answer_chars": 1284},

  "notes": { /* pipeline facts no single call can state: which legs ran,
                candidate counts, whether facets were relaxed, rerank survivors */ },
  "errors": [ /* failures that belong to the query rather than one retriever */ ]
}
```

### 3.1 Compact and full

A single question runs five Qdrant legs of up to forty hits each, plus the
catalog vocabularies it loads to resolve the question. Rendered as structured
objects that is **711 KB and 10,640 lines for one query** — technically complete
and practically unreadable. So the default rendering is one line per item:

```jsonc
"request": {
  "collection": "documents",
  "limit": 40,
  "filter": "is_parent=false AND is_current=true AND NOT (section_type in [toc, references, glossary] OR source_type=website)"
},
"result_count": 40,
"results_truncated": true,
"results": [
  " 1. 0.541  Scope and potential of coastal ecosystem… · p.6 · pdf_attachment · 2021-02-11 · 2069e93a | Figure 1: Allochthonous carbon…",
  " 2. 0.524  Seagrass Meadows – The Emerging Carbon Sink · website · 2025-03-01 · 6ebc7334 | Beneath the world's marine waters lies…"
]
```

Same query, same information, **34 KB and ~350 lines**. What compacts:

* **A retrieved hit** → `rank · score · title · page · source · date · document
  id | snippet`. The 20-field payload becomes the phrase that says where the
  passage came from.
* **A filter tree** → one line of `key=value AND …`. Every pull carries the same
  mandatory shape conditions, so the structured form repeated forty lines of
  identical tree on every leg of every query.
* **A graph or SQL row** → its own JSON on one line (still parseable, just not
  indented).
* **A bulk vocabulary load** (over 200 rows — the author gazetteer, the theme
  names, the entity index) → its count and its SQL, without a row sample. Five
  of 8,507 author names tell a reader nothing they can act on.
* **A short list** (ids, enabled classes) → one joined line.
* **Context blocks** keep their metadata as a `source` phrase and their text
  clipped to `RETRIEVAL_LOG_MAX_TEXT_CHARS`. Two numbers keep that honest:
  `text_chars` is the block's real size and `prompt_chars` the real size of the
  rendered context the model was sent, so a clipped sample can never be mistaken
  for the whole prompt. `RETRIEVAL_LOG_DETAIL=full` adds `prompt_text` — the
  exact string generation interpolated into the prompt, block headers and
  website/PDF group headings included, untruncated.

`RETRIEVAL_LOG_DETAIL=full` restores the structured objects — every payload
field, every row sampled, the filter as a tree — for analysis that needs them.
Counts, latencies and errors are identical in both.

### Events

Every event has the same shape, whichever store produced it:

```jsonc
{
  "retriever": "qdrant",            // "qdrant" | "graph" | "mysql" | anything added later
  "operation": "vector_search",
  "stage": "not_website_pull",       // which leg of the pipeline issued it
  "started_at": "2026-08-26T12:04:11.402+00:00",
  "latency_ms": 38.7,
  "request": { /* what the store was asked for */ },
  "result_count": 40,                // the true total
  "results": [ /* up to RETRIEVAL_LOG_MAX_RESULTS of them, in the order returned */ ],
  "results_truncated": true,
  "metrics": { /* anything measured that is not a result */ },
  "error": { "type": "...", "message": "...", "where": "..." }   // only when it failed
}
```

**Qdrant** — `request` carries the collection, the query text, the limit, the
filter (the mandatory shape conditions plus the query's facets) and the vector's
dimension; `results` carry rank, score, provenance and a snippet (compact) or
point id, score, full payload metadata and text (full). Stages seen today:
`website_pull`, `not_website_pull`, `keyword_leg`, `content_term_leg`,
`title_leg`, `multi_query_leg`, `corrective_pull`, `scoped_pull`,
`attachment_pull`, `lead_child_scroll`, `parent_fetch`,
`graph_chunk_hydration`, `graph_document_hydration`, `semantic_cache_lookup`.

**Graph** — two events per routed question. `graph_routing` records the decision:
the outcome (`answered`, `not_routed`, `zero_result`, `timed_out`, …), the
capability class, the template, the resolved entity, the query's scope and how
many blocks survived. `graph_traversal` records the query itself: the template
id, the Cypher, the validated parameters, the rows, and the entity / claim /
chunk / document identifiers they yielded.

**MySQL** — one event per statement: the SQL, its bound parameters, the tables it
read, its `rowcount` and the rows the caller fetched.

## 4. Reading the logs

One query, explained — open the report beside its trace:

```text
logs/2026-08-26/query_5f3c1e9a.../report.md
```

A day, folded into per-retriever latency, recall and failures:

```bash
python -m scripts.retrieval_log_report                    # today
python -m scripts.retrieval_log_report --all --slowest 20
python -m scripts.retrieval_log_report --errors-only
python -m scripts.retrieval_log_report --request-id 5f3c1e9a   # one trace, in full
```

```text
retriever  stage                       calls      p50      p95  total s  results  empty errors
--------------------------------------------------------------------------------------------
mysql      catalog                         1    524.2    524.2      0.5     8507      0      0
qdrant     website_pull                    2      0.0      0.1      0.0        4      0      0
qdrant     title_leg                       2      0.0      0.0      0.0        4      0      0
```

A day, as a dataframe:

```python
import pandas as pd
df = pd.read_json("logs/summary/2026-08-26.jsonl", lines=True)
df.groupby("intent")["total_latency_ms"].describe()
df[df.errors > 0][["request_id", "question", "retrievers"]]
```

Across the traces themselves — e.g. per-store latency, or which pulls returned
nothing:

```python
import json, pathlib
import pandas as pd

events = [
    {"request_id": t["request_id"], "question": t["question"], **e}
    for path in pathlib.Path("logs/2026-08-26").glob("query_*/trace.json")
    for t in [json.loads(path.read_text(encoding="utf-8"))]
    for e in t["events"]
]
ev = pd.DataFrame(events)
ev.groupby(["retriever", "stage"]).agg(
    calls=("latency_ms", "size"),
    p95_ms=("latency_ms", lambda s: s.quantile(0.95)),
    empty=("result_count", lambda s: (s == 0).sum()),
)
```

## 5. What the trace is, and is not

The three sections answer different questions and must not be read as each
other:

| Section | What it is |
|---|---|
| `events` | Every candidate each store *returned*. Six Qdrant legs of up to forty hits is ~200 candidates; fusion, reranking and context-building cut that to a handful. **Most of this never reaches the LLM.** |
| `context` | The blocks that *did*, in the order the model sees them (`n` is the `[1]`, `[2]` in the answer's citations), with each block's text clipped for the log and its true size recorded. |
| `outcome` | What the query returned: cached or fresh, answered or refused, how many chunks and citations, the answer's length. |

Not captured: the system prompt (a static template — it is the same string for
every query of a given answer format), and the deterministic catalog section
prefixed onto a combined answer (its size is in `notes.db_prefix_chars`).

## 6. Guarantees

* **Logging never changes retrieval.** Nothing in the trace is read back by the
  application, and every instrumentation point is a record-and-continue.
* **A logging failure is never a query failure.** Serialization, the directory,
  the write and the digest are each guarded; a failure costs the trace and is
  warned about once per process.
* **A retriever's failure is captured without being hidden.** The event records
  the exception and the original error continues to propagate (or to be handled
  exactly as it was before) — including the failures the retrievers swallow
  themselves, which a trace that showed them as *empty but fine* would conceal.
* **No secrets.** Connection settings are never read. Everything captured passes
  through a redactor that blanks any mapping value whose key looks like a
  credential (`password`, `api_key`, `token`, `authorization`, …), at any depth.
* **Bounded.** Every string is clipped and every collection capped, so one
  pathological document cannot produce a megabyte of JSON. Counts are always the
  true totals.
* **Concurrency-safe.** One file per `request_id`, written atomically; the shared
  digest is appended a whole line at a time under a lock. Traces follow a query
  onto its worker threads (the parallel search legs, the graph's executor).

## 7. How it is wired

The implementation is `app/observability/retrieval_log/` — a package at layer 1,
which is why it can be called from the client gateways, retrieval, the catalog
and the pipeline alike, and why it never imports any of them (see
`tests/test_architecture.py`). The retrieval code holds only the call:

```python
with retrieval_log.qdrant_call("vector_search", stage="dense_pull",
                               request=lambda: {"limit": limit}) as call:
    response = client.query_points(...)
    call.qdrant_results(response.points)
```

MySQL needs no call at all: `app/core/clients/database.py` hands out a tracing
proxy connection while a query is being traced, so the ~30 catalog query sites
are untouched.

Adding a retriever is one line — `retriever_call("elasticsearch", "search", …)`
— and nothing in the package changes: the summary, the roll-ups and the digest
all key off the name.

Tests: `tests/observability/test_retrieval_log.py` (the package, including
redaction, bounds, concurrency and the failure guarantees) and
`tests/pipeline/test_retrieval_log_integration.py` (the same trace produced
through the real retrieval path).
