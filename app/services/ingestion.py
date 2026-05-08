import tempfile
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.services.vector_store import get_vector_store


def load_documents(filename: str, content: bytes) -> list[Document]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            documents = PyPDFLoader(tmp_path).load()
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        for document in documents:
            document.metadata["source"] = filename
        return documents
    text = content.decode("utf-8", errors="ignore")
    return [Document(page_content=text, metadata={"source": filename})]


def ingest_file(filename: str, content: bytes) -> int:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(load_documents(filename, content))
    if chunks:
        get_vector_store().add_documents(chunks)
    return len(chunks)
