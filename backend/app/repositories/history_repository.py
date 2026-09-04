from datetime import UTC, datetime

from app.core.database import get_db
from app.schemas.history import HistoryEntry
from app.schemas.scoring import ChangeBundle


def _bundle_to_entry(user_id: str, bundle: ChangeBundle) -> dict:
    date_key = bundle.as_of.strftime("%Y-%m-%d")
    top_event = max(bundle.events, key=lambda e: e.impact_score, default=None)
    return {
        "user_id": user_id,
        "symbol": bundle.symbol,
        "company_name": bundle.company_name,
        "date_key": date_key,
        "detected_at": bundle.as_of,
        "seen_at": None,
        "price": bundle.price,
        "change_pct": bundle.change_pct,
        "attention_score": bundle.attention_score,
        "surprise_score": bundle.surprise_score,
        "impact_score": bundle.impact_score,
        "explain_chips": [c.model_dump() for c in bundle.explain_chips],
        "top_headline": top_event.title if top_event else None,
        "top_event_type": top_event.event_type if top_event else None,
        "why_this": bundle.why_this,
        "why_now": bundle.why_now,
        "demo_label": bundle.demo_label,
    }


async def record_meaningful_changes(user_id: str, bundles: list[ChangeBundle]) -> int:
    """Insert history entries for meaningful bundles not yet recorded today. Returns count inserted."""
    db = get_db()
    if db is None:
        return 0

    meaningful = [b for b in bundles if b.is_meaningful and b.data_ok]
    if not meaningful:
        return 0

    inserted = 0
    for bundle in meaningful:
        doc = _bundle_to_entry(user_id, bundle)
        try:
            await db.change_history.update_one(
                {"user_id": user_id, "symbol": bundle.symbol, "date_key": doc["date_key"]},
                {"$setOnInsert": doc},
                upsert=True,
            )
            inserted += 1
        except Exception:  # noqa: BLE001
            pass
    return inserted


async def mark_seen(user_id: str, symbol: str) -> None:
    db = get_db()
    if db is None:
        return

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    await db.change_history.update_many(
        {"user_id": user_id, "symbol": symbol, "date_key": today, "seen_at": None},
        {"$set": {"seen_at": datetime.now(UTC)}},
    )


async def get_history(
    user_id: str,
    filter_mode: str = "all",
    limit: int = 50,
) -> list[HistoryEntry]:
    db = get_db()
    if db is None:
        return []

    query: dict = {"user_id": user_id}

    if filter_mode == "today":
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        query["date_key"] = today
    elif filter_mode == "seen":
        query["seen_at"] = {"$ne": None}
    elif filter_mode == "unseen":
        query["seen_at"] = None

    cursor = db.change_history.find(query).sort("detected_at", -1).limit(limit)
    return [HistoryEntry(**doc) async for doc in cursor]


async def count_history(user_id: str) -> int:
    db = get_db()
    if db is None:
        return 0
    return await db.change_history.count_documents({"user_id": user_id})
