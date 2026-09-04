from datetime import UTC, datetime

from app.core.database import get_db
from app.schemas.watchlist import Watchlist, WatchlistStock


async def get_watchlist(user_id: str) -> Watchlist:
    db = get_db()
    if db is None:
        return Watchlist(user_id=user_id, stocks=[], updated_at=datetime.now(UTC))

    doc = await db.watchlists.find_one({"user_id": user_id})
    if not doc:
        return Watchlist(user_id=user_id, stocks=[], updated_at=datetime.now(UTC))
    return Watchlist(**doc)


async def add_stock(user_id: str, symbol: str) -> Watchlist:
    db = get_db()
    now = datetime.now(UTC)
    if db is None:
        return Watchlist(user_id=user_id, stocks=[WatchlistStock(symbol=symbol, added_at=now)], updated_at=now)

    existing = await get_watchlist(user_id)
    if any(s.symbol == symbol for s in existing.stocks):
        return existing

    await db.watchlists.update_one(
        {"user_id": user_id},
        {
            "$push": {"stocks": {"symbol": symbol, "added_at": now}},
            "$set": {"updated_at": now, "user_id": user_id},
        },
        upsert=True,
    )
    return await get_watchlist(user_id)


async def remove_stock(user_id: str, symbol: str) -> Watchlist:
    db = get_db()
    now = datetime.now(UTC)
    if db is None:
        return Watchlist(user_id=user_id, stocks=[], updated_at=now)

    await db.watchlists.update_one(
        {"user_id": user_id},
        {"$pull": {"stocks": {"symbol": symbol}}, "$set": {"updated_at": now}},
    )
    return await get_watchlist(user_id)
