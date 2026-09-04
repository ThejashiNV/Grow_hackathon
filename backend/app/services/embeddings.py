"""Sentence-transformer embeddings, loaded once and reused.

Used for headline novelty scoring and news deduplication (Part 16/PART 5).
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

_model = None
_load_lock = asyncio.Lock()


async def get_embedding_model():
    global _model
    if _model is None:
        async with _load_lock:
            if _model is None:
                _model = await asyncio.to_thread(_load_model)
    return _model


def _load_model():
    from sentence_transformers import SentenceTransformer

    logger.info("Loading sentence-transformers/all-MiniLM-L6-v2 ...")
    return SentenceTransformer("all-MiniLM-L6-v2")


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = await get_embedding_model()
    vectors = await asyncio.to_thread(model.encode, texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]
