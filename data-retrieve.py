import requests

BASE = "https://teriin.org/jsonapi"
H = {"Accept": "application/vnd.api+json"}

def include_fields(resource: str) -> list[str]:
    doc = requests.get(f"{BASE}/{resource}?page[limit]=1", headers=H, timeout=60).json()
    rels = doc["data"][0]["relationships"]
    return [k for k in rels if k.startswith("field_")]

resultIncludes = include_fields("node/feature_articles")
print(f"Fields to include for node/feature_articles: {resultIncludes}")

def fetch_with_relations(resource: str):
    inc = ",".join(include_fields(resource))
    url = f"{BASE}/{resource}?include={inc}&page[limit]=50"

    nodes, included = [], {}
    while url:
        doc = requests.get(url, headers=H, timeout=60).json()
        nodes += doc.get("data", [])
        for item in doc.get("included", []):
            included[(item["type"], item["id"])] = item
        url = doc.get("links", {}).get("next", {}).get("href")
    return nodes, included

def resolve_metadata(node: dict, included: dict) -> dict:
    meta = {}
    for field, rel in node["relationships"].items():
        data = rel.get("data")
        if not data:
            continue
        refs = data if isinstance(data, list) else [data]
        labels = []
        for ref in refs:
            ent = included.get((ref["type"], ref["id"]))
            if ent:
                a = ent["attributes"]
                labels.append(a.get("name") or a.get("display_name") or a.get("title"))
        if labels:
            meta[field] = labels
    return meta

nodes, included = fetch_with_relations("node/feature_articles")

print(resolve_metadata(nodes[0], included))
