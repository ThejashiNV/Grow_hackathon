from datetime import UTC, datetime

from app.core.database import get_db
from app.schemas.user_state import StockState


async def get_state(user_id: str, symbol: str) -> StockState:
    db = get_db()
    if db is None:
        return StockState(user_id=user_id, symbol=symbol)

    doc = await db.stock_states.find_one({"user_id": user_id, "symbol": symbol})
    if not doc:
        return StockState(user_id=user_id, symbol=symbol)
    return StockState(**doc)


async def get_states_bulk(user_id: str, symbols: list[str]) -> dict[str, StockState]:
    db = get_db()
    if db is None or not symbols:
        return {s: StockState(user_id=user_id, symbol=s) for s in symbols}

    cursor = db.stock_states.find({"user_id": user_id, "symbol": {"$in": symbols}})
    found = {doc["symbol"]: StockState(**doc) async for doc in cursor}
    return {s: found.get(s, StockState(user_id=user_id, symbol=s)) for s in symbols}


async def mark_seen(
    user_id: str,
    symbol: str,
    price: float | None,
    volume: int | None,
    score: float | None,
    event_ids: list[str],
) -> StockState:
    db = get_db()
    now = datetime.now(UTC)
    state = StockState(
        user_id=user_id,
        symbol=symbol,
        last_seen_price=price,
        last_seen_volume=volume,
        last_seen_score=score,
        last_seen_event_ids=event_ids,
        last_seen_at=now,
    )
    if db is not None:
        await db.stock_states.update_one(
            {"user_id": user_id, "symbol": symbol},
            {"$set": state.model_dump()},
            upsert=True,
        )
    return state
