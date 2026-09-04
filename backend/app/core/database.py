import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None
_status = "not_configured"


async def connect_mongo() -> None:
    global _client, _db, _status
    settings = get_settings()
    try:
        _client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
        await _client.admin.command("ping")
        _db = _client[settings.mongodb_database]
        await _ensure_indexes(_db)
        _status = "ok"
        logger.info("MongoDB connected")
    except Exception as exc:  # noqa: BLE001
        _status = "unavailable"
        logger.warning("MongoDB unavailable: %s", exc)


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.watchlists.create_index("user_id", unique=True)
    await db.stock_states.create_index([("user_id", 1), ("symbol", 1)], unique=True)
    await db.change_events.create_index([("symbol", 1), ("timestamp", -1)])
    await db.change_events.create_index("event_id", unique=True)
    await db.change_bundles.create_index([("symbol", 1), ("timestamp", -1)])
    await db.market_snapshots.create_index("symbol", unique=True)


async def close_mongo() -> None:
    if _client is not None:
        _client.close()


def get_db() -> AsyncIOMotorDatabase | None:
    return _db


def mongo_status() -> str:
    return _status
