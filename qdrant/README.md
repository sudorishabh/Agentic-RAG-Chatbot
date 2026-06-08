# `qdrant/main.py` — Embeddings + Qdrant walkthrough

A self-contained learning script that demonstrates the full vector-search loop:
**generate embeddings → store them in Qdrant → run a filtered similarity search.**

It is intentionally separate from the production `app/` package — think of it as a
scratchpad for understanding how Azure OpenAI embeddings and Qdrant fit together
before that logic gets wired into the real services
([app/services/embeddings.py](../app/services/embeddings.py),
[app/services/vector_store.py](../app/services/vector_store.py)).

The example dataset is a list of programming languages split into two groups,
*interpreted* vs *compiled*, which gives us labelled points to search and filter on.

---

## What it does, end to end

1. Loads configuration from `.env`.
2. Wipes any previous local Qdrant data and creates a fresh `languages` collection.
3. Connects to Azure OpenAI for embeddings.
4. Embeds two lists of language names.
5. Prints a preview of each embedding vector.
6. Stores every language as a point (vector + metadata) in Qdrant.
7. Embeds a query (`"C"`), searches the collection, and prints the matches.

---

## Prerequisites

This script uses its **own** environment variable names, which differ from the
main app's [.env.example](../.env.example). Make sure these are set:

| Variable | Purpose |
|---|---|
| `AZURE_OPENAI_EMBEDDING_KEY` | API key for the Azure OpenAI resource |
| `AZURE_OPENAI_ENDPOINT` | Base resource URL, e.g. `https://terillm.openai.azure.com/` |
| `AZURE_OPENAI_EMBEDDING_API_VERSION` | API version, e.g. `2024-06-01` |
| `AZURE_OPENAI_EMBEDDING_MODEL` | Deployment name (defaults to `text-embedding-3-large`) |

> **Note:** for Azure, `azure_endpoint` is just the base resource URL. The
> deployment name is passed as the `model` argument on each request — you do *not*
> build the full `/openai/deployments/.../embeddings` REST path yourself.

No Docker is required: the script runs Qdrant in **embedded / on-disk mode**
(`path="./qdrant_storage"`), so a local folder is used instead of a server.

Run it with:

```bash
python qdrant/main.py
```

---

## Code walkthrough

### 1. Configuration

```python
EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIM = 1536
```

`text-embedding-3-large` produces **3072-dimensional** vectors by default. The
script deliberately requests **1536** dimensions (via the `dimensions` argument in
`embed()`) so the vectors match the size declared on the collection. These two
numbers — the requested embedding dimension and the collection's `size` — must
always agree, or upserts will be rejected.

### 2. Reset + create the collection

```python
shutil.rmtree("./qdrant_storage", ignore_errors=True)

client = QdrantClient(path="./qdrant_storage")
client.create_collection(
    collection_name="languages",
    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
)
```

- `shutil.rmtree(...)` deletes the local storage folder so every run starts from a
  clean slate. `ignore_errors=True` means it's a no-op the first time, when the
  folder doesn't exist yet.
- `QdrantClient(path=...)` opens Qdrant in embedded mode against that folder. The
  commented-out `QdrantClient(host="localhost", port=6333)` line shows the
  alternative: talking to a running Qdrant server (e.g. the one in
  [docker-compose.yml](../docker-compose.yml)).
- `VectorParams(size=1536, distance=Distance.COSINE)` says each vector has 1536
  components and similarity is measured by **cosine distance** — the standard
  choice for text embeddings.

### 3. Azure OpenAI client

```python
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_EMBEDDING_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION"),
)
```

A standard Azure OpenAI client, configured purely from environment variables.

### 4. The dataset

```python
interpreted_languages = ['Python', 'JavaScript', 'Java', 'Ruby', 'PHP', 'Perl', 'Lua', 'R', 'MATLAB', 'Bash']
compiled_languages    = ['C', 'C++', 'Go', 'Rust', 'Swift', 'Kotlin', 'Zig', 'Fortran', 'Haskell']
```

Two labelled groups. The label (`interpreted` / `compiled`) becomes payload
metadata on each point, which is later used to filter searches.

### 5. The `embed` helper

```python
def embed(texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIM,
    )
    return [item.embedding for item in response.data]
```

Takes a list of strings and returns a list of vectors (one per input). Batching all
texts into a single call is cheaper and faster than embedding them one at a time.
`dimensions=EMBEDDING_DIM` is what truncates the output to 1536 components.

### 6. Embed + preview

```python
interpreted_embeddings = embed(interpreted_languages)
compiled_embeddings    = embed(compiled_languages)

for lang, vector in zip(interpreted_languages, interpreted_embeddings):
    print(f"{lang}: {vector[:5]}...")
```

Two batch calls produce the vectors, then the script prints the first 5 numbers of
each vector as a sanity check (the full 1536-number vectors would be unreadable).

### 7. Store the points

```python
client.upsert(
    collection_name="languages",
    wait=True,
    points=[PointStruct(
        id=uuid.uuid4(),
        vector=interpreted_embeddings[i],
        payload={"language": interpreted_languages[i], "type": "interpreted"})
        for i in range(len(interpreted_languages))],
)
```

Each language becomes a `PointStruct` with three parts:

- **`id`** — a random `uuid.uuid4()`, so every point is unique.
- **`vector`** — the embedding, used for similarity search.
- **`payload`** — arbitrary JSON metadata (`language` and `type`) returned with
  results and usable in filters.

`wait=True` blocks until the write is durably applied before continuing. A second,
identical `upsert` stores the compiled languages with `type: "compiled"`.

### 8. Search with a filter

```python
query_vector = embed(["C"])[0]
results = client.query_points(
    collection_name="languages",
    query=query_vector,
    with_payload=True,
    limit=2,
    query_filter=Filter(
        must=FieldCondition(key="type", match=MatchValue(value="interpreted"))
    ),
).points
print(results)
```

- The query word `"C"` is embedded the same way as the stored data — you always
  search a vector store with a vector, never raw text.
- `limit=2` asks for the two nearest points; `with_payload=True` returns their
  metadata.
- `query_filter` restricts the search to points where `type == "interpreted"`.
  So even though `"C"` is itself a compiled language, the results come from the
  *interpreted* group — this demonstrates how metadata filtering narrows a
  similarity search to a subset of the collection.

---

## Things to be aware of

- **Every run wipes the data.** The `shutil.rmtree` at the top means this script is
  not incremental — it rebuilds the collection from scratch each time.
- **The filter's `must` should be a list.** Qdrant's `Filter(must=...)` expects a
  *list* of conditions, e.g. `must=[FieldCondition(...)]`. Passing a single
  `FieldCondition` works on some client versions but is fragile — wrap it in a list
  to be safe:

  ```python
  query_filter=Filter(must=[FieldCondition(key="type", match=MatchValue(value="interpreted"))])
  ```
- **Dimensions must stay in sync.** If you change `EMBEDDING_DIM`, the collection's
  `VectorParams(size=...)` changes with it automatically (same constant) — but if
  you ever hard-code one without the other, upserts will fail.
- **Minor cleanups:** `FieldCondition` is imported twice on the import line, and the
  commented `shutil.rmtree(host=..., port=...)` line isn't valid (`rmtree` takes a
  path, not host/port) — it's just a leftover note hinting at server mode.

---

## How this maps to the real app

| Concept here | Production equivalent |
|---|---|
| `embed()` helper | [app/services/embeddings.py](../app/services/embeddings.py) |
| `create_collection` / `upsert` / `query_points` | [app/services/vector_store.py](../app/services/vector_store.py) |
| Embedded `path=` Qdrant | Server Qdrant via [docker-compose.yml](../docker-compose.yml) |
| `languages` toy collection | `documents` collection (`QDRANT_COLLECTION`) |
| `type` payload + filter | Document/source metadata used during retrieval |