from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Agentic RAG Chatbot", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
