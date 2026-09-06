"""Orchestrates the full market intelligence pipeline.

Phases:
1. Company profile lookup (entity mapping, aliases)
2. Market data fetch (with persistent caching, incremental updates)
3. Benchmark data fetch (NIFTY, sector index)
4. News fetch (multi-provider, deduplication, persistence)
5. Historical analysis (horizons, anomalous moves, patterns, regime)
6. ML anomaly detection (ensemble multi-signal)
7. Benchmark comparison (relative performance)
8. Cache result in MongoDB
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import numpy as np

from app.repositories import intelligence_repository
from app.schemas.intelligence import (
    AnomalySignalOut,
    BenchmarkComparison,
    CompanyProfile,
    DataFreshness,
    EventClusterOut,
    EventImpactOut,
    HistoricalSimilarOut,
    MLAnomalyOut,
    NewsItemOut,
    ReactionWindowOut,
    StockBaselineOut,
    StockIntelligence,
)
from app.services.event_classifier import EVENT_CATEGORY
from app.services.event_clustering import cluster_events
from app.services.event_impact import build_event_impact
from app.services.event_stock_linker import enrich_clusters_with_stock_links
from app.services.benchmark_service import (
    SECTOR_TO_INDEX,
    compute_relative_returns,
    get_benchmark_closes,
    get_market_index,
    get_sector_index,
)
from app.services.company_intel import get_company_profile, get_search_terms
from app.services.historical_analysis import (
    analyze_regime,
    compute_expected_vs_actual,
    compute_horizons,
    detect_anomalous_moves,
    detect_patterns,
    find_rare_events,
)
from app.services.market_data import MarketDataProvider, get_market_data_provider
from app.services.ml_anomaly import detect_anomalies_ml
from app.services.news_provider import fetch_and_store_news
from app.utils.sector_map import get_sector

logger = logging.getLogger(__name__)


async def get_stock_intelligence(
    symbol: str,
    provider: MarketDataProvider | None = None,
    skip_cache: bool = False,
) -> StockIntelligence:
    if not skip_cache:
        cached = await intelligence_repository.get_cached(symbol)
        if cached is not None:
            if cached.freshness:
                cached.freshness.cache_hit = True
            return cached

    if provider is None:
        provider = get_market_data_provider()

    profile_task = get_company_profile(symbol)
    history_task = provider.get_history(symbol, period="5y")
    quote_task = provider.get_quote(symbol)

    profile, history, quote = await asyncio.gather(
        profile_task, history_task, quote_task
    )

    if not history.points or len(history.points) < 30:
        return StockIntelligence(
            symbol=symbol,
            company_name=quote.company_name or profile.get("name"),
            sector=get_sector(symbol) or quote.sector or profile.get("sector"),
            total_trading_days=len(history.points),
            generated_at=datetime.now(UTC).isoformat(),
            confidence_note=(
                "Insufficient historical data for meaningful analysis "
                "(need at least 30 trading days)."
            ),
        )

    dates = [p.date.strftime("%Y-%m-%d") for p in history.points]
    closes = np.array([p.close for p in history.points], dtype=np.float64)
    volumes = np.array([p.volume for p in history.points], dtype=np.float64)

    sector = get_sector(symbol) or quote.sector or profile.get("sector")

    sector_index = SECTOR_TO_INDEX.get(sector) if sector else None
    market_index = await get_market_index()

    benchmark_tasks = []
    benchmark_tasks.append(
        get_benchmark_closes(market_index, period="5y") if market_index else _null_future()
    )
    benchmark_tasks.append(
        get_benchmark_closes(sector_index, period="5y") if sector_index else _null_future()
    )

    search_terms = get_search_terms(profile)
    news_task = fetch_and_store_news(symbol, search_terms)

    market_closes, sector_closes, news_items = await asyncio.gather(
        benchmark_tasks[0], benchmark_tasks[1], news_task,
        return_exceptions=True,
    )

    if isinstance(market_closes, Exception):
        logger.warning("Market benchmark fetch failed: %s", market_closes)
        market_closes = None
    if isinstance(sector_closes, Exception):
        logger.warning("Sector benchmark fetch failed: %s", sector_closes)
        sector_closes = None
    if isinstance(news_items, Exception):
        logger.warning("News fetch failed: %s", news_items)
        news_items = []

    result = await asyncio.to_thread(
        _run_analysis, symbol, dates, closes, volumes,
        sector_closes=sector_closes,
        market_closes=market_closes,
    )

    result.company_name = quote.company_name or profile.get("name")
    result.sector = sector
    result.industry = profile.get("industry")
    result.current_price = quote.price
    result.change_pct = quote.change_pct
    result.generated_at = datetime.now(UTC).isoformat()
    result.data_source = "yfinance"

    result.company_profile = CompanyProfile(
        name=profile.get("name", symbol),
        sector=sector,
        industry=profile.get("industry"),
        exchange=profile.get("exchange", ""),
        market_cap=profile.get("market_cap"),
        aliases=profile.get("aliases", []),
        subsidiaries=profile.get("subsidiaries", []),
        segments=profile.get("segments", []),
        commodities=profile.get("commodities", []),
        macro_factors=profile.get("macro_factors", []),
        competitors=profile.get("competitors", []),
    )

    result.freshness = DataFreshness(
        price_data="live" if not quote.is_delayed else "delayed",
        price_updated_at=quote.as_of.isoformat() if quote.as_of else None,
        news_data="live" if news_items else "unavailable",
        news_updated_at=datetime.now(UTC).isoformat() if news_items else None,
        benchmark_data="available" if market_closes is not None else "unavailable",
        intelligence_generated_at=datetime.now(UTC).isoformat(),
        cache_hit=False,
    )

    if isinstance(news_items, list) and news_items:
        result.news = [
            NewsItemOut(
                news_id=n.get("news_id", ""),
                title=n.get("title", ""),
                summary=n.get("summary", ""),
                publisher=n.get("publisher"),
                link=n.get("link"),
                published_at=n.get("published_at"),
                source=n.get("source", ""),
                event_type=n.get("event_type", "other"),
                impact_score=n.get("impact_score", 0),
            )
            for n in news_items[:30]
        ]

        try:
            logger.info("Starting event clustering for %s with %d news items", symbol, len(news_items[:30]))
            clusters, _ = await cluster_events(symbol, news_items[:30])
            logger.info("Event clustering produced %d clusters for %s", len(clusters), symbol)
            clusters = enrich_clusters_with_stock_links(clusters)

            anomalous_dicts = [m.model_dump() for m in result.anomalous_moves]
            rare_dicts = [r.model_dump() for r in result.rare_events]

            cluster_outs: list[EventClusterOut] = []
            for c in clusters:
                event_date_str = c.first_seen.strftime("%Y-%m-%d") if c.first_seen else None
                try:
                    impact_result = build_event_impact(
                        c.event_type, c.canonical_title, event_date_str,
                        dates, closes, volumes, market_closes,
                        anomalous_dicts, rare_dicts,
                    )
                    impact_out = EventImpactOut(
                        event_type=impact_result.event_type,
                        event_date=impact_result.event_date,
                        reactions=[
                            ReactionWindowOut(
                                window=r.window, days=r.days,
                                stock_return_pct=r.stock_return_pct,
                                market_return_pct=r.market_return_pct,
                                abnormal_return_pct=r.abnormal_return_pct,
                                volume_ratio=r.volume_ratio,
                            ) for r in impact_result.reactions
                        ],
                        historical_avg_reaction_5d=impact_result.historical_avg_reaction_5d,
                        historical_avg_reaction_20d=impact_result.historical_avg_reaction_20d,
                        similar_events=[
                            HistoricalSimilarOut(
                                date=s.date, event_description=s.event_description,
                                stock_return_5d_pct=s.stock_return_5d_pct,
                                stock_return_20d_pct=s.stock_return_20d_pct,
                                severity=s.severity,
                            ) for s in impact_result.similar_events
                        ],
                        historical_event_count=impact_result.historical_event_count,
                    )
                except Exception:
                    impact_out = None

                cluster_outs.append(EventClusterOut(
                    cluster_id=c.cluster_id,
                    canonical_title=c.canonical_title,
                    event_type=c.event_type.value,
                    category=EVENT_CATEGORY.get(c.event_type, "other"),
                    article_count=c.article_count,
                    sources=c.sources,
                    first_seen=c.first_seen.isoformat() if c.first_seen else None,
                    last_seen=c.last_seen.isoformat() if c.last_seen else None,
                    impact_score=c.impact_score,
                    severity=c.severity,
                    affected_symbols=c.affected_symbols,
                    summary=c.summary,
                    event_impact=impact_out,
                ))
            result.event_clusters = cluster_outs
        except Exception:
            logger.warning("Event clustering failed for %s", symbol, exc_info=True)

    if market_closes is not None:
        rel = compute_relative_returns(closes, market_closes)
        if rel:
            result.benchmark_comparison.append(BenchmarkComparison(
                benchmark_name="NIFTY 50",
                benchmark_symbol="^NSEI",
                stock_return_pct=rel["stock_return_pct"],
                benchmark_return_pct=rel["benchmark_return_pct"],
                outperformance_pct=rel["outperformance_pct"],
                correlation=rel.get("correlation"),
                beta=rel.get("beta"),
            ))

    if sector_closes is not None and sector_index:
        sector_name = next(
            (k for k, v in SECTOR_TO_INDEX.items() if v == sector_index),
            "Sector"
        )
        rel = compute_relative_returns(closes, sector_closes)
        if rel:
            result.benchmark_comparison.append(BenchmarkComparison(
                benchmark_name=f"NIFTY {sector_name}",
                benchmark_symbol=sector_index,
                stock_return_pct=rel["stock_return_pct"],
                benchmark_return_pct=rel["benchmark_return_pct"],
                outperformance_pct=rel["outperformance_pct"],
                correlation=rel.get("correlation"),
                beta=rel.get("beta"),
            ))

    await intelligence_repository.cache_intelligence(symbol, result)
    return result


def _run_analysis(
    symbol: str,
    dates: list[str],
    closes: np.ndarray,
    volumes: np.ndarray,
    sector_closes: np.ndarray | None = None,
    market_closes: np.ndarray | None = None,
) -> StockIntelligence:
    horizons = compute_horizons(dates, closes, volumes)
    anomalous = detect_anomalous_moves(dates, closes, volumes)
    patterns = detect_patterns(dates, closes, volumes)
    regime = analyze_regime(closes, volumes)
    rare = find_rare_events(dates, closes)
    expected_actual = compute_expected_vs_actual(anomalous, closes)

    ml_results = detect_anomalies_ml(
        dates, closes, volumes,
        sector_closes=sector_closes,
        market_closes=market_closes,
        lookback=10,
    )

    ml_anomalies_out = [
        MLAnomalyOut(
            date=r.date,
            composite_score=r.composite_score,
            is_anomalous=r.is_anomalous,
            explanation=r.explanation,
            signals=[
                AnomalySignalOut(
                    name=s.name,
                    score=s.score,
                    z_score=s.z_score,
                    description=s.description,
                )
                for s in r.signals if s.score >= 10
            ],
        )
        for r in ml_results
    ]

    _enrich_horizons_with_benchmarks(horizons, closes, sector_closes, market_closes)

    _enrich_anomalous_with_benchmarks(anomalous, dates, closes, sector_closes, market_closes)

    from app.services.stock_baselines import compute_stock_baseline
    baseline = compute_stock_baseline(symbol, closes, volumes)
    baseline_out = None
    if baseline:
        baseline_out = StockBaselineOut(
            normal_daily_vol_ann=baseline.normal_daily_vol_ann,
            normal_volume_median=baseline.normal_volume_median,
            normal_daily_range_pct=baseline.normal_daily_range_pct,
            normal_daily_range_p95=baseline.normal_daily_range_p95,
            volume_clustering_score=baseline.volume_clustering_score,
            return_persistence=baseline.return_persistence,
            gap_frequency=baseline.gap_frequency,
            regime_label=baseline.regime_label,
            volatility_percentile=baseline.volatility_percentile,
        )

    n_years = len(closes) / 252

    return StockIntelligence(
        symbol=symbol,
        data_start=dates[0],
        data_end=dates[-1],
        total_trading_days=len(closes),
        horizons=horizons,
        anomalous_moves=anomalous,
        patterns=patterns,
        regime_changes=regime,
        rare_events=rare,
        expected_vs_actual=expected_actual,
        ml_anomalies=ml_anomalies_out,
        stock_baseline=baseline_out,
        confidence_note=(
            f"Analysis based on {len(closes)} trading days ({n_years:.1f} years) "
            f"of historical data. Patterns are observational, not predictive. "
            f"Past behavior does not guarantee future results."
        ),
    )


def _enrich_horizons_with_benchmarks(
    horizons,
    closes: np.ndarray,
    sector_closes: np.ndarray | None,
    market_closes: np.ndarray | None,
) -> None:
    from app.services.historical_analysis import HORIZON_SPECS

    for h in horizons:
        spec_days = next((d for label, d in HORIZON_SPECS if label == h.period), None)
        if spec_days is None:
            continue

        if market_closes is not None and len(market_closes) >= spec_days:
            mc = market_closes[-spec_days:]
            h.market_return_pct = round((mc[-1] / mc[0] - 1) * 100, 2)
            h.relative_performance_pct = round(h.return_pct - h.market_return_pct, 2)

        if sector_closes is not None and len(sector_closes) >= spec_days:
            sc = sector_closes[-spec_days:]
            h.sector_return_pct = round((sc[-1] / sc[0] - 1) * 100, 2)


def _enrich_anomalous_with_benchmarks(
    anomalous,
    dates: list[str],
    closes: np.ndarray,
    sector_closes: np.ndarray | None,
    market_closes: np.ndarray | None,
) -> None:
    for move in anomalous:
        try:
            idx = dates.index(move.date)
        except ValueError:
            continue

        if idx < 1:
            continue

        if sector_closes is not None and len(sector_closes) > idx:
            sr = (sector_closes[idx] / sector_closes[idx - 1] - 1) * 100
            move.sector_return_pct = round(sr, 2)
            move.abnormal_return_pct = round(move.change_pct - sr, 2)

        if market_closes is not None and len(market_closes) > idx:
            mr = (market_closes[idx] / market_closes[idx - 1] - 1) * 100
            move.market_return_pct = round(mr, 2)
            if move.abnormal_return_pct is None:
                move.abnormal_return_pct = round(move.change_pct - mr, 2)


async def _null_future():
    return None
