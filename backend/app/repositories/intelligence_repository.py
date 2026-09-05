"""MongoDB cache for market intelligence reports."""

import logging
from datetime import UTC, datetime, timedelta

from app.core.database import get_db
from app.schemas.intelligence import StockIntelligence

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 4


async def get_cached(symbol: str) -> StockIntelligence | None:
    db = get_db()
    if db is None:
        return None
    try:
        doc = await db.market_intelligence.find_one({"symbol": symbol})
        if doc is None:
            return None
        cached_at = doc.get("cached_at")
        if cached_at:
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=UTC)
        if cached_at and (datetime.now(UTC) - cached_at) > timedelta(hours=CACHE_TTL_HOURS):
            return None
        doc.pop("_id", None)
        doc.pop("cached_at", None)
        return StockIntelligence(**doc)
    except Exception:
        logger.warning("Failed to read intelligence cache for %s", symbol, exc_info=True)
        return None


async def cache_intelligence(symbol: str, report: StockIntelligence) -> None:
    db = get_db()
    if db is None:
        return
    try:
        doc = report.model_dump()
        doc["cached_at"] = datetime.now(UTC)
        await db.market_intelligence.replace_one(
            {"symbol": symbol}, doc, upsert=True,
        )
    except Exception:
        logger.warning("Failed to cache intelligence for %s", symbol, exc_info=True)


async def invalidate_cache(symbol: str) -> None:
    db = get_db()
    if db is None:
        return
    try:
        await db.market_intelligence.delete_one({"symbol": symbol})
    except Exception:
        logger.warning("Failed to invalidate intelligence cache for %s", symbol, exc_info=True)
