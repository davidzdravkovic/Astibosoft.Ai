from __future__ import annotations

import hashlib
import re

_MAX_CHARS = 900
_MIN_CHARS = 120


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_markdown(text: str) -> list[str]:
    """Split on blank lines / headings; pack into ~900 char chunks."""
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    blocks = re.split(r"\n{2,}", normalized)
    chunks: list[str] = []
    buf = ""

    for block in blocks:
        piece = block.strip()
        if not piece:
            continue
        candidate = f"{buf}\n\n{piece}".strip() if buf else piece
        if len(candidate) <= _MAX_CHARS:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        if len(piece) <= _MAX_CHARS:
            buf = piece
        else:
            for start in range(0, len(piece), _MAX_CHARS):
                part = piece[start : start + _MAX_CHARS].strip()
                if part:
                    chunks.append(part)
            buf = ""

    if buf:
        chunks.append(buf)

    return [c for c in chunks if len(c) >= _MIN_CHARS or len(chunks) == 1]
