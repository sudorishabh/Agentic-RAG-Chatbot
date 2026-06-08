import os
import shutil
import uuid
from dotenv import load_dotenv
from openai import AzureOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, Filter, FieldCondition, FieldCondition, MatchValue

load_dotenv()

# text-embedding-3-large is 3072-dim by default; we request 1536 via the
# `dimensions` arg so it matches the collection's vector size below.
EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIM = 1536

# shutil.rmtree(host="localhost", port=6333)
shutil.rmtree("./qdrant_storage", ignore_errors=True)

# client = QdrantClient(host="localhost", port=6333)
client = QdrantClient(path="./qdrant_storage")
client.create_collection(
    collection_name="languages",
    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
)

# For Azure, `azure_endpoint` is the base resource URL (e.g.
# https://terillm.openai.azure.com/) and the deployment name is passed as
# `model` on each request — not the full /openai/deployments/... REST URL.
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_EMBEDDING_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION"),
)

interpreted_languages = ['Python', 'JavaScript', 'Java', 'Ruby', 'PHP', 'Perl', 'Lua', 'R', 'MATLAB', 'Bash']
compiled_languages = ['C', 'C++', 'Go', 'Rust', 'Swift', 'Kotlin', 'Zig', 'Fortran', 'Haskell']


def embed(texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIM,
    )
    return [item.embedding for item in response.data]


interpreted_embeddings = embed(interpreted_languages)
compiled_embeddings = embed(compiled_languages)

print("Interpreted language embeddings:")
for lang, vector in zip(interpreted_languages, interpreted_embeddings):
    print(f"{lang}: {vector[:5]}...")

print("Compiled language embeddings:")
for lang, vector in zip(compiled_languages, compiled_embeddings):
    print(f"{lang}: {vector[:5]}...")

# points = 

# point_id = 1

# for lang, vector in zip(interpreted_languages, interpreted_embeddings):
#     points.append(PointStruct(id=point_id, vector=vector, payload={"language": lang, "type": "interpreted"}))
#     point_id += 1
# for lang, vector in zip(compiled_languages, compiled_embeddings):
#     points.append(PointStruct(id=point_id, vector=vector, payload={"language": lang, "type": "compiled"}))
#     point_id += 1

client.upsert(
    collection_name="languages",
    wait=True,
    points=[PointStruct(
        id=uuid.uuid4(),
        vector=interpreted_embeddings[i], 
        payload={"language": interpreted_languages[i], "type": "interpreted"}) for i in range(len(interpreted_languages))
        ]  
)

client.upsert(
    collection_name="languages",
    wait=True,
    points=[PointStruct(
        id=uuid.uuid4(),
        vector=compiled_embeddings[i], 
        payload={"language": compiled_languages[i], "type": "compiled"}) for i in range(len(compiled_languages))
    ]  
)



# query_vector = embed(["C#"])[0]
query_vector = embed(["C"])[0]
results = client.query_points(
    collection_name="languages",
    query=query_vector,
    with_payload=True,
    limit=2,
    query_filter=Filter(
        must = FieldCondition(key="type", match=MatchValue(value="interpreted")
    ))
).points

print(results)
