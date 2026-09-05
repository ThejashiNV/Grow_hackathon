"""Benchmark/index data service.

Fetches and caches NIFTY 50, sector indices, and provides
relative performance calculations.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import numpy as np

from app.core.database import get_db
from app.repositories import market_data_repository

logger = logging.getLogger(__name__)

BENCHMARKS = {
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANKNIFTY": "^NSEBANK",
    "NIFTYIT": "^CNXIT",
    "NIFTYPHARMA": "^CNXPHARMA",
    "NIFTYAUTO": "^CNXAUTO",
    "NIFTYFMCG": "^CNXFMCG",
    "NIFTYENERGY": "^CNXENERGY",
    "NIFTYMETAL": "^CNXMETAL",
}

SECTOR_TO_INDEX = {
    "IT": "^CNXIT",
    "BANKING": "^NSEBANK",
    "AUTO": "^CNXAUTO",
    "PHARMA": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "ENERGY": "^CNXENERGY",
    "METALS": "^CNXMETAL",
}

CACHE_TTL_HOURS = 6


async def get_benchmark_closes(
    index_symbol: str,
    period: str = "5y",
) -> np.ndarray | None:
    """Get benchmark close prices as numpy array, fetching/caching as needed."""
    db = get_db()
    if db is not None:
        stored = await market_data_repository.get_benchmark_prices(index_symbol)
        if stored and len(stored) > 50:
            meta = await db.benchmark_meta.find_one({"symbol": index_symbol})
            if meta:
                updated = meta.get("updated_at", datetime.min)
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=UTC)
                age = datetime.now(UTC) - updated
                if age < timedelta(hours=CACHE_TTL_HOURS):
                    return np.array([p["close"] for p in stored], dtype=np.float64)

    prices = await asyncio.to_thread(_fetch_benchmark, index_symbol, period)
    if not prices:
        stored = await market_data_repository.get_benchmark_prices(index_symbol)
        if stored:
            return np.array([p["close"] for p in stored], dtype=np.float64)
        return None

    if db is not None:
        await market_data_repository.store_benchmark_data(index_symbol, prices)
        try:
            await db.benchmark_meta.replace_one(
                {"symbol": index_symbol},
                {"symbol": index_symbol, "updated_at": datetime.now(UTC)},
                upsert=True,
            )
        except Exception:
            pass

    return np.array([p["close"] for p in prices], dtype=np.float64)


def _fetch_benchmark(index_symbol: str, period: str) -> list[dict]:
    try:
        import yfinance as yf
        ticker = yf.Ticker(index_symbol)
        hist = ticker.history(period=period, interval="1d", auto_adjust=False)
        if hist.empty:
            return []
        return [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else 0,
            }
            for idx, row in hist.iterrows()
            if row["Close"] == row["Close"]
        ]
    except Exception as exc:
        logger.warning("Failed to fetch benchmark %s: %s", index_symbol, exc)
        return []


async def get_sector_index(sector: str) -> str | None:
    return SECTOR_TO_INDEX.get(sector)


async def get_market_index() -> str:
    return "^NSEI"


def compute_relative_returns(
    stock_closes: np.ndarray,
    benchmark_closes: np.ndarray,
) -> dict:
    """Compute relative performance metrics between stock and benchmark."""
    min_len = min(len(stock_closes), len(benchmark_closes))
    if min_len < 10:
        return {}

    sc = stock_closes[-min_len:]
    bc = benchmark_closes[-min_len:]

    stock_ret = np.diff(sc) / sc[:-1]
    bench_ret = np.diff(bc) / bc[:-1]

    relative_ret = stock_ret - bench_ret

    total_stock = (sc[-1] / sc[0] - 1) * 100
    total_bench = (bc[-1] / bc[0] - 1) * 100

    correlation = float(np.corrcoef(stock_ret, bench_ret)[0, 1]) if len(stock_ret) > 10 else None

    beta = None
    if len(stock_ret) > 20:
        cov = np.cov(stock_ret, bench_ret)
        if cov[1, 1] > 1e-15:
            beta = float(cov[0, 1] / cov[1, 1])

    return {
        "stock_return_pct": round(total_stock, 2),
        "benchmark_return_pct": round(total_bench, 2),
        "outperformance_pct": round(total_stock - total_bench, 2),
        "correlation": round(correlation, 3) if correlation is not None else None,
        "beta": round(beta, 3) if beta is not None else None,
        "avg_daily_relative_pct": round(float(np.mean(relative_ret)) * 100, 4),
        "trading_days": min_len,
    }
