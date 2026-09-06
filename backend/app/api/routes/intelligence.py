"""Market intelligence API routes."""

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.session import get_current_user_id
from app.repositories import watchlist_repository
from app.services.intelligence_service import get_stock_intelligence
from app.services.refresh_pipeline import force_refresh, get_refresh_status

router = APIRouter(tags=["intelligence"])


async def _get_user_last_seen(db, user_id: str, symbols: list[str]) -> dict[str, datetime | None]:
    if db is None or not symbols:
        return {s: None for s in symbols}
    cursor = db.stock_states.find(
        {"user_id": user_id, "symbol": {"$in": symbols}},
        {"symbol": 1, "last_seen_at": 1},
    )
    found: dict[str, datetime | None] = {}
    async for doc in cursor:
        ts = doc.get("last_seen_at")
        if ts and ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        found[doc["symbol"]] = ts
    return {s: found.get(s) for s in symbols}


async def _get_changes_since(db, symbol: str, since: datetime | None) -> list[dict]:
    if db is None or since is None:
        return []
    cursor = db.intel_snapshots.find(
        {"symbol": symbol, "timestamp": {"$gt": since}},
        sort=[("timestamp", -1)],
        limit=20,
    )
    changes: list[dict] = []
    async for snap in cursor:
        for c in snap.get("changes", []):
            changes.append({
                "timestamp": snap["timestamp"].isoformat() if snap.get("timestamp") else None,
                **c,
            })
    return changes


@router.get("/intelligence/{symbol}")
async def get_intelligence(
    symbol: str,
    refresh: bool = Query(False, description="Force refresh (bypass cache)"),
):
    return await get_stock_intelligence(symbol, skip_cache=refresh)


@router.get("/intelligence-summary")
async def get_watchlist_intelligence_summary(
    user_id: str = Depends(get_current_user_id),
):
    """Compact intelligence summary for each watched stock, with changes since last check."""
    watchlist = await watchlist_repository.get_watchlist(user_id)
    symbols = [s.symbol for s in watchlist.stocks]

    if not symbols:
        return {"items": [], "generated_at": None, "total_new_changes": 0}

    db = get_db()
    intel_tasks = [get_stock_intelligence(sym) for sym in symbols]
    results = await asyncio.gather(*intel_tasks, return_exceptions=True)

    last_seen_map = await _get_user_last_seen(db, user_id, symbols)

    items = []
    total_new_changes = 0
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

        hi_clusters = [c for c in result.event_clusters if c.impact_score >= 50]
        for c in hi_clusters[:2]:
            summary_signals.append(f"Event: {c.canonical_title[:40]}")

        changes_since = await _get_changes_since(db, sym, last_seen_map.get(sym))
        never_seen = last_seen_map.get(sym) is None
        total_new_changes += len(changes_since) + (1 if never_seen else 0)

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
            "changes_since_last_check": changes_since,
            "never_seen": never_seen,
            "last_seen_at": last_seen_map.get(sym).isoformat() if last_seen_map.get(sym) else None,
            "event_clusters": [c.model_dump() for c in result.event_clusters[:5]],
        })

    items.sort(key=lambda x: x.get("anomaly_score", 0), reverse=True)

    return {"items": items, "total_new_changes": total_new_changes}


@router.post("/intel-seen")
async def mark_intel_seen(user_id: str = Depends(get_current_user_id)):
    """Record that the user has reviewed their watchlist intelligence."""
    watchlist = await watchlist_repository.get_watchlist(user_id)
    symbols = [s.symbol for s in watchlist.stocks]
    if not symbols:
        return {"marked": 0}

    db = get_db()
    if db is None:
        return {"marked": 0}

    now = datetime.now(UTC)
    for sym in symbols:
        await db.stock_states.update_one(
            {"user_id": user_id, "symbol": sym},
            {"$set": {"user_id": user_id, "symbol": sym, "last_seen_at": now}},
            upsert=True,
        )
    return {"marked": len(symbols), "seen_at": now.isoformat()}


@router.get("/refresh-status")
async def refresh_status():
    return await get_refresh_status()


@router.post("/refresh/{symbol}")
async def trigger_refresh(symbol: str):
    return await force_refresh(symbol.upper())


@router.get("/daily-feed")
async def daily_feed(user_id: str = Depends(get_current_user_id)):
    """Today's Market Intelligence daily feed — aggregated across all watchlist stocks."""
    watchlist = await watchlist_repository.get_watchlist(user_id)
    symbols = [s.symbol for s in watchlist.stocks]
    if not symbols:
        return {"alerts": [], "movers": [], "news_digest": [], "sector_summary": {}, "refresh_status": None}

    tasks = [get_stock_intelligence(sym) for sym in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    alerts = []
    movers = []
    all_news = []
    sector_data: dict[str, list] = {}

    for sym, result in zip(symbols, results):
        if isinstance(result, Exception):
            continue

        top_anomaly = max((a.composite_score for a in result.ml_anomalies), default=0)
        regime_alerts = [r for r in result.regime_changes if r.ratio > 1.5 or r.ratio < 0.5]

        if top_anomaly >= 60:
            alerts.append({
                "type": "anomaly",
                "symbol": sym,
                "company_name": result.company_name,
                "score": round(top_anomaly, 1),
                "detail": next((a.explanation for a in result.ml_anomalies if a.composite_score >= 60), ""),
                "severity": "critical" if top_anomaly >= 80 else "high",
            })

        for r in regime_alerts:
            alerts.append({
                "type": "regime_change",
                "symbol": sym,
                "company_name": result.company_name,
                "score": round(r.ratio * 40, 1),
                "detail": r.description,
                "severity": "high" if r.ratio > 2 or r.ratio < 0.3 else "medium",
            })

        for cluster in result.event_clusters:
            if cluster.impact_score >= 60:
                alerts.append({
                    "type": "event_cluster",
                    "symbol": sym,
                    "company_name": result.company_name,
                    "score": cluster.impact_score,
                    "detail": f"{cluster.canonical_title} ({cluster.article_count} articles, {cluster.category})",
                    "severity": cluster.severity,
                    "event_type": cluster.event_type,
                    "category": cluster.category,
                    "article_count": cluster.article_count,
                })

        hi_news = [n for n in result.news if n.impact_score >= 50]
        if len(hi_news) >= 2 and not result.event_clusters:
            alerts.append({
                "type": "news_cluster",
                "symbol": sym,
                "company_name": result.company_name,
                "score": sum(n.impact_score for n in hi_news) / len(hi_news),
                "detail": f"{len(hi_news)} high-impact articles",
                "severity": "medium",
            })

        if result.change_pct is not None and abs(result.change_pct) > 1:
            movers.append({
                "symbol": sym,
                "company_name": result.company_name,
                "change_pct": result.change_pct,
                "current_price": result.current_price,
                "anomaly_score": round(top_anomaly, 1),
                "direction": "up" if result.change_pct > 0 else "down",
            })

        for n in result.news[:5]:
            all_news.append({
                "symbol": sym,
                "title": n.title,
                "publisher": n.publisher,
                "published_at": n.published_at,
                "impact_score": n.impact_score,
                "event_type": n.event_type,
                "link": n.link,
            })

        s = result.sector or "Other"
        if s not in sector_data:
            sector_data[s] = []
        sector_data[s].append({
            "symbol": sym,
            "change_pct": result.change_pct,
            "anomaly_score": round(top_anomaly, 1),
        })

    alerts.sort(key=lambda x: x["score"], reverse=True)
    movers.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    all_news.sort(key=lambda x: x["impact_score"], reverse=True)

    sector_summary = {}
    for s, stocks in sector_data.items():
        changes = [st["change_pct"] for st in stocks if st["change_pct"] is not None]
        sector_summary[s] = {
            "stocks": stocks,
            "avg_change_pct": round(sum(changes) / len(changes), 2) if changes else None,
            "max_anomaly": max((st["anomaly_score"] for st in stocks), default=0),
        }

    db = get_db()
    recent_changes = []
    if db is not None:
        cursor = db.intel_snapshots.find(
            {"symbol": {"$in": symbols}},
            sort=[("timestamp", -1)],
            limit=50,
        )
        async for snap in cursor:
            for c in snap.get("changes", []):
                recent_changes.append({
                    "symbol": snap["symbol"],
                    "timestamp": snap["timestamp"].isoformat() if snap.get("timestamp") else None,
                    **c,
                })

    ref_status = await get_refresh_status()

    all_clusters = []
    for sym, result in zip(symbols, results):
        if isinstance(result, Exception):
            continue
        for c in result.event_clusters:
            all_clusters.append({
                "symbol": sym,
                "cluster_id": c.cluster_id,
                "canonical_title": c.canonical_title,
                "event_type": c.event_type,
                "category": c.category,
                "article_count": c.article_count,
                "impact_score": c.impact_score,
                "severity": c.severity,
                "affected_symbols": c.affected_symbols,
                "first_seen": c.first_seen,
                "last_seen": c.last_seen,
            })
    all_clusters.sort(key=lambda x: x["impact_score"], reverse=True)

    return {
        "alerts": alerts[:20],
        "movers": movers[:20],
        "news_digest": all_news[:30],
        "event_clusters": all_clusters[:20],
        "sector_summary": sector_summary,
        "recent_changes": recent_changes[:20],
        "refresh_status": ref_status,
        "generated_at": datetime.now(UTC).isoformat(),
    }
