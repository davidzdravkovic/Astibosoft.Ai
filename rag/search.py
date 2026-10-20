from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass

import psycopg
from pgvector import Vector

from embedding.embedder import embed_text

TOP_K = int(os.getenv("RAG_TOP_K", "6"))
MAX_PER_SOURCE = int(os.getenv("RAG_MAX_PER_SOURCE", "2"))


@dataclass(frozen=True)
class RetrievedChunk:
    source_key: str
    title: str
    chunk_text: str
    distance: float | None = None


def search_similar(conn: psycopg.Connection, question: str) -> list[RetrievedChunk]:
    query_vector = Vector(embed_text(question))
    # Over-fetch then diversify by SourceKey.
    fetch_limit = max(TOP_K * 3, TOP_K)
    rows = conn.execute(
        """
        SELECT "SourceKey", "Title", "Content",
               "Embedding" <=> %s::vector AS distance
        FROM "KnowledgeChunks"
        ORDER BY distance
        LIMIT %s
        """,
        (query_vector, fetch_limit),
    ).fetchall()

    per_source: dict[str, int] = defaultdict(int)
    selected: list[RetrievedChunk] = []

    for row in rows:
        source_key = row[0]
        if per_source[source_key] >= MAX_PER_SOURCE:
            continue
        selected.append(
            RetrievedChunk(
                source_key=source_key,
                title=row[1],
                chunk_text=row[2],
                distance=float(row[3]) if row[3] is not None else None,
            )
        )
        per_source[source_key] += 1
        if len(selected) >= TOP_K:
            break

    return selected
