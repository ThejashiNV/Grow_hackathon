import logging

import chromadb

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client = None
_headlines_collection = None
_status = "not_configured"


def connect_chroma() -> None:
    global _client, _headlines_collection, _status
    settings = get_settings()
    try:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
        _headlines_collection = _client.get_or_create_collection("headlines")
        _status = "ok"
        logger.info("ChromaDB connected")
    except Exception as exc:  # noqa: BLE001
        _status = "unavailable"
        logger.warning("ChromaDB unavailable: %s", exc)


def get_headlines_collection():
    return _headlines_collection if _status == "ok" else None


def chroma_status() -> str:
    return _status
