import logging

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None
_status = "not_configured"


async def connect_redis() -> None:
    global _client, _status
    settings = get_settings()
    try:
        _client = redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=3)
        await _client.ping()
        _status = "ok"
        logger.info("Redis connected")
    except Exception as exc:  # noqa: BLE001
        _status = "unavailable"
        logger.warning("Redis unavailable: %s", exc)


async def close_redis() -> None:
    if _client is not None:
        await _client.close()


def get_redis() -> redis.Redis | None:
    return _client if _status == "ok" else None


def redis_status() -> str:
    return _status
