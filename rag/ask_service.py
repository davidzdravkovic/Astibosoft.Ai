from __future__ import annotations

import logging
import os

from db import connect
from rag.llm import LlmError, LlmNotConfiguredError, generate_answer
from rag.search import RetrievedChunk, search_similar

logger = logging.getLogger(__name__)

RAG_SERVICE_UNAVAILABLE_CODE = "rag-service-unavailable"
ASSISTANT_UNAVAILABLE_MESSAGE = (
    "I couldn't reach the assistant right now. Try again in a moment."
)

_MAX_DISTANCE = float(os.getenv("RAG_MAX_DISTANCE", "0.55"))


class AskServiceUnavailableError(Exception):
    """LLM or assistant configuration failed; mapped to HTTP 503 at the API edge."""


class AskSource:
    __slots__ = ("source_key", "title")

    def __init__(self, source_key: str, title: str) -> None:
        self.source_key = source_key
        self.title = title


class PreparedAsk:
    __slots__ = ("answer", "sources", "context", "chunks")

    def __init__(
        self,
        answer: str,
        sources: list[AskSource],
        context: str,
        chunks: list[RetrievedChunk],
    ) -> None:
        self.answer = answer
        self.sources = sources
        self.context = context
        self.chunks = chunks


def _filter_by_distance(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    kept: list[RetrievedChunk] = []
    for chunk in chunks:
        if chunk.distance is None or chunk.distance <= _MAX_DISTANCE:
            kept.append(chunk)
    return kept


def prepare_ask(question: str) -> PreparedAsk:
    with connect() as conn:
        chunks = search_similar(conn, question)

    chunks = _filter_by_distance(chunks)

    if not chunks:
        return PreparedAsk(
            answer=(
                "I don't have enough company knowledge for that yet. "
                "Use the contact form or email hello@astibosoft.com and the team can help."
            ),
            sources=[],
            context="",
            chunks=[],
        )

    sources = [AskSource(chunk.source_key, chunk.title) for chunk in chunks]
    context_blocks = [
        f"[{index + 1}] ({chunk.source_key} — {chunk.title})\n{chunk.chunk_text}"
        for index, chunk in enumerate(chunks)
    ]
    context = "\n\n".join(context_blocks)

    try:
        answer = generate_answer(question, context)
    except LlmNotConfiguredError as exc:
        logger.warning("LLM not configured: %s", exc)
        raise AskServiceUnavailableError from exc
    except LlmError as exc:
        logger.warning("LLM error: %s", exc)
        raise AskServiceUnavailableError from exc

    return PreparedAsk(
        answer=answer,
        sources=sources,
        context=context,
        chunks=chunks,
    )
