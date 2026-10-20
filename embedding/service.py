from __future__ import annotations

import logging
import uuid
from pathlib import Path

from pgvector import Vector

from db import connect
from embedding.chunking import content_hash, split_markdown
from embedding.embedder import embed_text

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def _title_from_markdown(body: str, fallback: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or fallback
    return fallback


def _load_sources(source_key: str | None) -> list[tuple[str, str, str]]:
    """Return list of (source_key, title, raw_markdown)."""
    if not KNOWLEDGE_DIR.is_dir():
        logger.warning("Knowledge directory missing: %s", KNOWLEDGE_DIR)
        return []

    files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    sources: list[tuple[str, str, str]] = []
    for path in files:
        key = path.stem.lower()
        if source_key and key != source_key.lower():
            continue
        body = path.read_text(encoding="utf-8")
        title = _title_from_markdown(body, fallback=key.replace("-", " ").title())
        sources.append((key, title, body))
    return sources


def run_embed(source_key: str | None = None) -> None:
    sources = _load_sources(source_key)
    if not sources:
        logger.info("No knowledge sources to embed (sourceKey=%s)", source_key)
        return

    with connect() as conn:
        for key, title, body in sources:
            chunks = split_markdown(body)
            if not chunks:
                logger.info("Skip empty sourceKey=%s", key)
                continue

            conn.execute(
                'DELETE FROM "KnowledgeChunks" WHERE "SourceKey" = %s',
                (key,),
            )

            for index, chunk in enumerate(chunks):
                labeled = f"Section: {title}\n\n{chunk}"
                digest = content_hash(labeled)
                vector = embed_text(labeled)
                conn.execute(
                    """
                    INSERT INTO "KnowledgeChunks" (
                        "Id", "SourceKey", "Title", "ChunkIndex",
                        "Content", "Embedding", "ContentHash", "UpdatedAt"
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                    """,
                    (
                        str(uuid.uuid4()),
                        key,
                        title,
                        index,
                        labeled,
                        Vector(vector),
                        digest,
                    ),
                )

            logger.info(
                "Embedded sourceKey=%s title=%s chunks=%s",
                key,
                title,
                len(chunks),
            )

        conn.commit()
