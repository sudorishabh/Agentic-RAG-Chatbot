"""Answer generation over retrieved context.

The grounded LLM call (buffered and streaming) plus the chit-chat reply. Faith-
fulness verification and the query pipeline that drives these live in
:mod:`app.generation.faithfulness` and :mod:`app.pipeline` respectively; this
module only turns a question + context blocks into answer text.
"""
from __future__ import annotations

import logging
from typing import Iterator

from app.core.clients.llm import get_llm
from app.core.models.context import ContextBlock
from app.generation.prompts import (
    CHITCHAT_SYSTEM_PROMPT,
    GROUNDED_SYSTEM_PROMPT,
    REFUSAL,
    format_context_blocks,
    format_directive,
)

logger = logging.getLogger(__name__)


def chitchat(question: str, history: list[dict[str, str]] | None) -> str:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [("system", CHITCHAT_SYSTEM_PROMPT), ("human", "{question}")]
    )
    chain = prompt | get_llm() | StrOutputParser()
    return chain.invoke({"question": question}).strip()


def _build_system(answer_format: str | None, correction: str | None) -> str:
    system = GROUNDED_SYSTEM_PROMPT
    directive = format_directive(answer_format)
    if directive:
        system += f"\n\n{directive}"
    if correction:
        system += f"\n\n{correction}"
    return system


def generate_answer(
    question: str,
    blocks: list[ContextBlock],
    *,
    correction: str | None = None,
    answer_format: str | None = None,
) -> str:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    if not blocks:
        return REFUSAL

    system = _build_system(answer_format, correction)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Numbered context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | get_llm() | StrOutputParser()
    return chain.invoke(
        {"context": format_context_blocks(blocks), "question": question}
    ).strip()


def generate_stream(
    question: str, blocks: list[ContextBlock], *, answer_format: str | None = None
) -> Iterator[str]:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _build_system(answer_format, None)),
            ("human", "Numbered context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | get_llm(streaming=True) | StrOutputParser()
    yield from chain.stream(
        {"context": format_context_blocks(blocks), "question": question}
    )
