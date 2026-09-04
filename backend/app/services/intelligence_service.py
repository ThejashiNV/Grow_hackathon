"""Orchestrates historical market intelligence analysis."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

import numpy as np

from app.repositories import intelligence_repository
from app.schemas.intelligence import StockIntelligence
from app.services.historical_analysis import (
    analyze_regime,
    compute_expected_vs_actual,
    compute_horizons,
    detect_anomalous_moves,
    detect_patterns,
    find_rare_events,
)
from app.services.market_data import MarketDataProvider, get_market_data_provider
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
            return cached

    if provider is None:
        provider = get_market_data_provider()

    history = await provider.get_history(symbol, period="5y")
    quote = await provider.get_quote(symbol)

    if not history.points or len(history.points) < 30:
        return StockIntelligence(
            symbol=symbol,
            company_name=quote.company_name,
            sector=get_sector(symbol) or quote.sector,
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

    result = await asyncio.to_thread(_run_analysis, symbol, dates, closes, volumes)

    result.company_name = quote.company_name
    result.sector = get_sector(symbol) or quote.sector
    result.current_price = quote.price
    result.generated_at = datetime.now(UTC).isoformat()
    result.data_source = "yfinance"

    await intelligence_repository.cache_intelligence(symbol, result)
    return result


def _run_analysis(
    symbol: str,
    dates: list[str],
    closes: np.ndarray,
    volumes: np.ndarray,
) -> StockIntelligence:
    horizons = compute_horizons(dates, closes, volumes)
    anomalous = detect_anomalous_moves(dates, closes, volumes)
    patterns = detect_patterns(dates, closes, volumes)
    regime = analyze_regime(closes, volumes)
    rare = find_rare_events(dates, closes)
    expected_actual = compute_expected_vs_actual(anomalous, closes)

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
        confidence_note=(
            f"Analysis based on {len(closes)} trading days ({n_years:.1f} years) "
            f"of historical data. Patterns are observational, not predictive. "
            f"Past behavior does not guarantee future results."
        ),
    )
