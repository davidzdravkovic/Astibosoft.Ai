from __future__ import annotations

import os
from functools import lru_cache

from fastembed import TextEmbedding

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
VECTOR_DIM = 768


@lru_cache(maxsize=1)
def _get_model() -> TextEmbedding:
    return TextEmbedding(model_name=MODEL_NAME)


def embed_text(text: str) -> list[float]:
    model = _get_model()
    vectors = list(model.embed([text]))
    if not vectors:
        raise RuntimeError("Embedding model returned no vectors")
    vector = vectors[0]
    return vector.tolist() if hasattr(vector, "tolist") else list(vector)
