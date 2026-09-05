"""Market intelligence API routes."""

import asyncio

from fastapi import APIRouter, Query

from app.repositories import watchlist_repository
from app.services.intelligence_service import get_stock_intelligence

router = APIRouter(tags=["intelligence"])


@router.get("/intelligence/{symbol}")
async def get_intelligence(
    symbol: str,
    refresh: bool = Query(False, description="Force refresh (bypass cache)"),
):
    return await get_stock_intelligence(symbol, skip_cache=refresh)


@router.get("/intelligence-summary")
async def get_watchlist_intelligence_summary(
    user_id: str = Query("default", description="User ID"),
):
    """Compact intelligence summary for each watched stock."""
    watchlist = await watchlist_repository.get_watchlist(user_id)
    symbols = [s.symbol for s in watchlist.stocks]

    if not symbols:
        return {"items": [], "generated_at": None}

    tasks = [get_stock_intelligence(sym) for sym in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    items = []
    for sym, result in zip(symbols, results):
        if isinstance(result, Exception):
            items.append({
                "symbol": sym,
                "status": "error",
                "error": str(result),
            })
            continue

        top_anomaly = max(
            (a.composite_score for a in result.ml_anomalies),
            default=0,
        )

        regime_alerts = [r.metric for r in result.regime_changes if r.ratio > 1.5 or r.ratio < 0.5]
        news_count = len(result.news)
        high_impact_news = sum(1 for n in result.news if n.impact_score >= 50)

        if top_anomaly >= 70:
            status = "high_anomaly"
        elif top_anomaly >= 50 or regime_alerts or high_impact_news >= 2:
            status = "event_detected"
        else:
            status = "normal"

        summary_signals = []
        if top_anomaly >= 40:
            summary_signals.append(f"Anomaly {top_anomaly:.0f}/100")
        if regime_alerts:
            summary_signals.append(f"Regime: {', '.join(regime_alerts)}")
        if high_impact_news:
            summary_signals.append(f"{high_impact_news} high-impact news")
        if result.change_pct is not None and abs(result.change_pct) > 2:
            summary_signals.append(f"Price {result.change_pct:+.1f}%")

        items.append({
            "symbol": sym,
            "company_name": result.company_name,
            "sector": result.sector,
            "current_price": result.current_price,
            "change_pct": result.change_pct,
            "status": status,
            "anomaly_score": round(top_anomaly, 1),
            "regime_alerts": regime_alerts,
            "news_count": news_count,
            "high_impact_news": high_impact_news,
            "signals": summary_signals,
            "freshness": result.freshness.model_dump() if result.freshness else None,
        })

    items.sort(key=lambda x: x.get("anomaly_score", 0), reverse=True)

    return {"items": items}
