"""Persistent market data storage in MongoDB.

Stores OHLCV history, avoids re-downloading the same data.
Supports incremental updates (only fetch new days since last stored date).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from app.core.database import get_db

logger = logging.getLogger(__name__)


async def get_stored_history(symbol: str) -> dict | None:
    """Get the stored price history metadata for a symbol."""
    db = get_db()
    if db is None:
        return None
    try:
        return await db.price_history_meta.find_one({"symbol": symbol})
    except Exception:
        logger.warning("Failed to read price history meta for %s", symbol, exc_info=True)
        return None


async def get_stored_prices(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Read stored daily prices from MongoDB."""
    db = get_db()
    if db is None:
        return []
    try:
        query: dict = {"symbol": symbol}
        if start_date:
            query.setdefault("date", {})["$gte"] = start_date
        if end_date:
            query.setdefault("date", {})["$lte"] = end_date

        cursor = db.daily_prices.find(query).sort("date", 1)
        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(doc)
        return results
    except Exception:
        logger.warning("Failed to read prices for %s", symbol, exc_info=True)
        return []


async def store_daily_prices(symbol: str, prices: list[dict]) -> int:
    """Upsert daily price records. Returns count of records written."""
    db = get_db()
    if db is None:
        return 0
    try:
        count = 0
        for p in prices:
            p["symbol"] = symbol
            await db.daily_prices.update_one(
                {"symbol": symbol, "date": p["date"]},
                {"$set": p},
                upsert=True,
            )
            count += 1

        if prices:
            dates = [p["date"] for p in prices]
            await db.price_history_meta.replace_one(
                {"symbol": symbol},
                {
                    "symbol": symbol,
                    "first_date": min(dates),
                    "last_date": max(dates),
                    "total_records": await db.daily_prices.count_documents({"symbol": symbol}),
                    "updated_at": datetime.now(UTC),
                },
                upsert=True,
            )
        return count
    except Exception:
        logger.warning("Failed to store prices for %s", symbol, exc_info=True)
        return 0


async def needs_refresh(symbol: str, max_age_hours: int = 6) -> bool:
    """Check if stored data is stale and needs refresh."""
    meta = await get_stored_history(symbol)
    if meta is None:
        return True
    updated = meta.get("updated_at")
    if updated is None:
        return True
    age = datetime.now(UTC) - updated
    return age > timedelta(hours=max_age_hours)


async def store_benchmark_data(index_symbol: str, prices: list[dict]) -> int:
    """Store benchmark/index daily prices."""
    db = get_db()
    if db is None:
        return 0
    try:
        count = 0
        for p in prices:
            p["symbol"] = index_symbol
            p["is_benchmark"] = True
            await db.benchmark_prices.update_one(
                {"symbol": index_symbol, "date": p["date"]},
                {"$set": p},
                upsert=True,
            )
            count += 1
        return count
    except Exception:
        logger.warning("Failed to store benchmark data for %s", index_symbol, exc_info=True)
        return 0


async def get_benchmark_prices(
    index_symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Read benchmark/index prices."""
    db = get_db()
    if db is None:
        return []
    try:
        query: dict = {"symbol": index_symbol}
        if start_date:
            query.setdefault("date", {})["$gte"] = start_date
        if end_date:
            query.setdefault("date", {})["$lte"] = end_date
        cursor = db.benchmark_prices.find(query).sort("date", 1)
        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(doc)
        return results
    except Exception:
        logger.warning("Failed to read benchmark for %s", index_symbol, exc_info=True)
        return []
