from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

from app.core.config import get_settings
from app.services.vector_store import get_vector_store

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using only the provided context. "
    "If the context does not contain the answer, say you do not know. "
    "Cite the source filename when possible."
)


@lru_cache
def get_llm() -> AzureChatOpenAI:
    settings = get_settings()
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_chat_deployment,
        temperature=0,
    )


def format_docs(documents: list[Document]) -> str:
    return "\n\n".join(
        f"[{doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in documents
    )


def answer_query(question: str) -> dict:
    settings = get_settings()
    retriever = get_vector_store().as_retriever(
        search_kwargs={"k": settings.retrieval_top_k}
    )
    documents = retriever.invoke(question)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | get_llm() | StrOutputParser()
    answer = chain.invoke(
        {"context": format_docs(documents), "question": question}
    )
    sources = [
        {
            "source": doc.metadata.get("source", "unknown"),
            "content": doc.page_content,
        }
        for doc in documents
    ]
    return {"answer": answer, "sources": sources}
