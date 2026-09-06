"""Background intelligence refresh pipeline.

Runs as an asyncio task during app lifespan. Periodically refreshes
intelligence for all watched stocks with incremental updates:
- Market data: every 15 min during market hours, 2h otherwise
- News: every 30 min
- Full intelligence rebuild: every 4h or when significant change detected
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.core.database import get_db

logger = logging.getLogger(__name__)

MARKET_REFRESH_MINUTES = 15
NEWS_REFRESH_MINUTES = 30
INTEL_REBUILD_HOURS = 4
LOOP_INTERVAL_SECONDS = 60

_task: asyncio.Task | None = None


async def start_refresh_loop() -> None:
    global _task
    if _task is not None:
        return
    _task = asyncio.create_task(_refresh_loop())
    logger.info("Background refresh pipeline started")


async def stop_refresh_loop() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
        logger.info("Background refresh pipeline stopped")


async def get_refresh_status() -> dict:
    db = get_db()
    if db is None:
        return {"running": _task is not None and not _task.done(), "last_run": None, "stocks_tracked": 0}

    meta = await db.refresh_meta.find_one({"_id": "pipeline"})
    return {
        "running": _task is not None and not _task.done(),
        "last_run": meta.get("last_run").isoformat() if meta and meta.get("last_run") else None,
        "last_duration_sec": meta.get("last_duration_sec") if meta else None,
        "stocks_tracked": meta.get("stocks_tracked", 0) if meta else 0,
        "last_errors": meta.get("last_errors", []) if meta else [],
        "total_refreshes": meta.get("total_refreshes", 0) if meta else 0,
    }


async def force_refresh(symbol: str) -> dict:
    """Force an immediate refresh for a single stock."""
    return await _refresh_one_stock(symbol, force=True)


async def _refresh_loop() -> None:
    await asyncio.sleep(10)

    while True:
        try:
            await _run_refresh_cycle()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Refresh cycle failed")

        await asyncio.sleep(LOOP_INTERVAL_SECONDS)


async def _run_refresh_cycle() -> None:
    db = get_db()
    if db is None:
        return

    symbols = await _get_all_watched_symbols(db)
    if not symbols:
        return

    now = datetime.now(UTC)
    errors = []
    refreshed = 0

    for symbol in symbols:
        try:
            needs = await _check_staleness(symbol, now)
            if not needs["any"]:
                continue
            result = await _refresh_one_stock(symbol, needs=needs)
            if result.get("refreshed"):
                refreshed += 1
            if result.get("error"):
                errors.append(f"{symbol}: {result['error']}")
        except Exception as exc:
            errors.append(f"{symbol}: {exc}")
            logger.warning("Refresh failed for %s: %s", symbol, exc)

    if refreshed > 0 or errors:
        duration = (datetime.now(UTC) - now).total_seconds()
        await db.refresh_meta.replace_one(
            {"_id": "pipeline"},
            {
                "_id": "pipeline",
                "last_run": now,
                "last_duration_sec": round(duration, 1),
                "stocks_tracked": len(symbols),
                "stocks_refreshed": refreshed,
                "last_errors": errors[-5:],
                "total_refreshes": await _inc_counter(db),
            },
            upsert=True,
        )
        logger.info(
            "Refresh cycle: %d/%d stocks updated in %.1fs, %d errors",
            refreshed, len(symbols), duration, len(errors),
        )


async def _inc_counter(db) -> int:
    doc = await db.refresh_meta.find_one({"_id": "pipeline"})
    return (doc.get("total_refreshes", 0) if doc else 0) + 1


async def _get_all_watched_symbols(db) -> list[str]:
    """Collect unique symbols across all users' watchlists."""
    symbols: set[str] = set()
    async for doc in db.watchlists.find({}, {"stocks.symbol": 1}):
        for s in doc.get("stocks", []):
            sym = s.get("symbol")
            if sym:
                symbols.add(sym)
    return list(symbols)


async def _check_staleness(symbol: str, now: datetime) -> dict:
    db = get_db()
    result = {"market": False, "news": False, "intelligence": False, "any": False}

    if db is None:
        result.update(market=True, news=True, intelligence=True, any=True)
        return result

    intel_doc = await db.market_intelligence.find_one({"symbol": symbol})
    if intel_doc is None:
        result.update(market=True, news=True, intelligence=True, any=True)
        return result

    cached_at = intel_doc.get("cached_at")
    if cached_at:
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=UTC)
        age_hours = (now - cached_at).total_seconds() / 3600
        if age_hours > INTEL_REBUILD_HOURS:
            result.update(market=True, news=True, intelligence=True, any=True)
            return result

    news_meta = await db.news_cache_meta.find_one({"symbol": symbol})
    if news_meta:
        nts = news_meta.get("fetched_at")
        if nts:
            if nts.tzinfo is None:
                nts = nts.replace(tzinfo=UTC)
            if (now - nts).total_seconds() > NEWS_REFRESH_MINUTES * 60:
                result["news"] = True
                result["any"] = True
    else:
        result["news"] = True
        result["any"] = True

    price_meta = await db.price_history_meta.find_one({"symbol": symbol})
    if price_meta:
        pts = price_meta.get("updated_at")
        if pts:
            if pts.tzinfo is None:
                pts = pts.replace(tzinfo=UTC)
            if (now - pts).total_seconds() > MARKET_REFRESH_MINUTES * 60:
                result["market"] = True
                result["any"] = True
    else:
        result["market"] = True
        result["any"] = True

    return result


async def _refresh_one_stock(symbol: str, force: bool = False, needs: dict | None = None) -> dict:
    from app.services.intelligence_service import get_stock_intelligence

    try:
        result = await get_stock_intelligence(symbol, skip_cache=True)

        db = get_db()
        if db is not None:
            await _store_change_snapshot(db, symbol, result)

        return {"refreshed": True, "symbol": symbol}
    except Exception as exc:
        logger.warning("Failed to refresh %s: %s", symbol, exc)
        return {"refreshed": False, "symbol": symbol, "error": str(exc)}


async def _store_change_snapshot(db, symbol: str, intel) -> None:
    """Store a snapshot diff so we can show 'what changed since last check'."""
    now = datetime.now(UTC)

    prev = await db.intel_snapshots.find_one(
        {"symbol": symbol}, sort=[("timestamp", -1)]
    )

    changes = []
    if prev:
        prev_score = prev.get("anomaly_score", 0)
        curr_score = max((a.composite_score for a in intel.ml_anomalies), default=0)
        if abs(curr_score - prev_score) > 10:
            changes.append({
                "type": "anomaly_change",
                "detail": f"Anomaly score changed from {prev_score:.0f} to {curr_score:.0f}",
                "severity": "high" if curr_score >= 70 else "medium",
            })

        prev_news = prev.get("news_count", 0)
        curr_news = len(intel.news)
        new_articles = curr_news - prev_news
        if new_articles > 0:
            changes.append({
                "type": "new_news",
                "detail": f"{new_articles} new article(s)",
                "severity": "medium" if new_articles >= 3 else "low",
            })

        prev_price = prev.get("price")
        if prev_price and intel.current_price:
            price_change = abs(intel.current_price / prev_price - 1) * 100
            if price_change > 2:
                changes.append({
                    "type": "price_move",
                    "detail": f"Price moved {price_change:.1f}% since last check",
                    "severity": "high" if price_change > 5 else "medium",
                })

        prev_regimes = set(prev.get("regime_alerts", []))
        curr_regimes = {r.metric for r in intel.regime_changes if r.ratio > 1.5 or r.ratio < 0.5}
        new_regimes = curr_regimes - prev_regimes
        if new_regimes:
            changes.append({
                "type": "regime_change",
                "detail": f"New regime alert: {', '.join(new_regimes)}",
                "severity": "high",
            })

    top_anomaly = max((a.composite_score for a in intel.ml_anomalies), default=0)

    snapshot = {
        "symbol": symbol,
        "timestamp": now,
        "price": intel.current_price,
        "change_pct": intel.change_pct,
        "anomaly_score": top_anomaly,
        "news_count": len(intel.news),
        "high_impact_news": sum(1 for n in intel.news if n.impact_score >= 50),
        "regime_alerts": [r.metric for r in intel.regime_changes if r.ratio > 1.5 or r.ratio < 0.5],
        "changes": changes,
        "sector": intel.sector,
    }

    await db.intel_snapshots.insert_one(snapshot)

    await db.intel_snapshots.delete_many({
        "symbol": symbol,
        "timestamp": {"$lt": now - timedelta(days=30)},
    })
